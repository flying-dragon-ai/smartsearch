using static SmartSearch.Desktop.Localization;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation;
using Microsoft.UI.Xaml.Controls;

namespace SmartSearch.Desktop;

public sealed partial class MainWindow
{
    private ListView? _activityList;
    private ContentControl? _activityDetail;
    private JsonElement? _activitySnapshot;
    private JsonElement? _selectedActivity;
    private JsonElement? _activityDetails;
    private string? _selectedActivityKey;
    private string? _activityLoadingKey;
    private int _activitySelectionVersion;
    private string _activityFilter = "all";
    private bool _updatingActivityList;
    private TextBlock? _activityReadError;
    private TextBlock? _activityDetailSummary;

    private UIElement BuildActivityPage()
    {
        var filter = new SelectorBar
        {
            MinHeight = 36, Padding = new Thickness(0), VerticalAlignment = VerticalAlignment.Center
        };
        foreach (var (value, label) in new[] { ("all", L("全部")), ("running", L("运行中")), ("failed", L("失败")) })
        {
            var item = new SelectorBarItem
            {
                Text = label, Tag = value, MinHeight = 36, Padding = new Thickness(12, 8, 12, 5)
            };
            filter.Items.Add(item);
            if (value == _activityFilter) filter.SelectedItem = item;
        }
        AutomationProperties.SetName(filter, L("筛选活动"));
        filter.SelectionChanged += (_, _) =>
        {
            _activityFilter = filter.SelectedItem?.Tag as string ?? "all";
            if (_activitySnapshot is { } snapshot) RenderActivity(snapshot);
        };
        var more = new MenuFlyout();
        var preferences = new MenuFlyoutItem { Text = L("观察设置…") };
        preferences.Click += async (_, _) => await ShowActivityPreferencesAsync();
        var clear = new MenuFlyoutItem { Text = L("清除已结束记录") };
        clear.Click += async (_, _) => await RunOperationAsync("activity-clear", ClearActivityAsync);
        more.Items.Add(preferences);
        more.Items.Add(clear);
        var toolbar = new Grid { ColumnSpacing = 16 };
        toolbar.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        toolbar.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        var filterLabel = Body(L("活动筛选"));
        filterLabel.VerticalAlignment = VerticalAlignment.Center;
        toolbar.Children.Add(new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12, Children = { filterLabel, filter } });
        var actions = ActionRow(
            ActionButton(L("刷新"), () => RefreshActivityAsync(silent: false), operationKey: "activity-refresh", busyText: L("刷新中…")),
            new Button { Content = L("更多"), Flyout = more });
        actions.VerticalAlignment = VerticalAlignment.Center;
        Grid.SetColumn(actions, 1);
        toolbar.Children.Add(actions);
        var toolbarSurface = new Border { Style = UiStyle("WorkspaceToolbarStyle"), Child = toolbar };
        _activityViews.Clear();
        _activityHint = Secondary(string.Empty);
        _activityHint.Visibility = Visibility.Collapsed;
        _activityHint.Margin = new Thickness(24, 8, 24, 16);
        _activityList = new ListView { SelectionMode = ListViewSelectionMode.Single,
            Padding = new Thickness(12, 0, 12, 12), HorizontalContentAlignment = HorizontalAlignment.Stretch };
        AutomationProperties.SetName(_activityList, L("活动记录"));
        _activityList.SelectionChanged += async (_, _) =>
        {
            if (_updatingActivityList || _activityList.SelectedItem is not ListViewItem { Tag: string key } || _activitySnapshot is not { } snapshot) return;
            var run = Items(snapshot, "runs").FirstOrDefault(run => ActivityKey(run) == key);
            if (run.ValueKind == JsonValueKind.Object) await ShowActivityDetailsAsync(run);
        };
        var listPane = new Grid();
        listPane.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        listPane.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        listPane.Children.Add(_activityHint);
        Grid.SetRow(_activityList, 1);
        listPane.Children.Add(_activityList);
        _activityDetail = new ContentControl { HorizontalContentAlignment = HorizontalAlignment.Stretch, VerticalContentAlignment = VerticalAlignment.Stretch };
        _activityReadError = Secondary(string.Empty);
        RenderActivityDetail();
        var split = SplitWorkspace("activity", listPane, _activityDetail, 280, 240, 340, 360);
        var layout = new Grid();
        layout.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        layout.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        layout.Children.Add(toolbarSurface);
        Grid.SetRow(split, 1);
        layout.Children.Add(split);
        if (_activitySnapshot is { } existing) RenderActivity(existing);
        _ = RefreshActivityAsync(silent: true);
        return layout;
    }

    private static string ActivityKey(JsonElement run) => Text(run, "config_dir") + "\n" + Text(run, "run_id");

    private bool MatchesActivityFilter(JsonElement run) => _activityFilter switch
    {
        "running" => !IsTerminal(Text(run, "status")),
        "failed" => Text(run, "status") is "failed" or "interrupted" || Text(run, "error_type").Length > 0,
        _ => true
    };

    private void RenderActivity(JsonElement result)
    {
        _activitySnapshot = result.Clone();
        if (_currentPage != "activity" || _activityList is null) return;
        if (_activityEnabledSwitch is not null)
        {
            _settingActivityEnabled = true;
            _activityEnabledSwitch.IsOn = Bool(result, "enabled", true);
            _settingActivityEnabled = false;
        }
        var runs = Items(result, "runs").Where(MatchesActivityFilter).OrderByDescending(run => Number(run, "started_at"))
            .ThenBy(ActivityKey, StringComparer.Ordinal).ToList();
        var keys = runs.Select(ActivityKey).ToHashSet();
        _updatingActivityList = true;
        foreach (var key in _activityViews.Keys.Where(key => !keys.Contains(key)).ToArray())
        {
            _activityList.Items.Remove(_activityViews[key].Row);
            _activityViews.Remove(key);
        }
        for (var index = 0; index < runs.Count; index++)
        {
            var run = runs[index];
            var key = ActivityKey(run);
            if (!_activityViews.TryGetValue(key, out var view)) _activityViews[key] = view = BuildActivityRow(run);
            view.Update(run);
            var position = _activityList.Items.IndexOf(view.Row);
            if (position == index) continue;
            if (position >= 0) _activityList.Items.RemoveAt(position);
            _activityList.Items.Insert(index, view.Row);
        }
        if (_selectedActivityKey is not null && keys.Contains(_selectedActivityKey))
        {
            _selectedActivity = runs.First(run => ActivityKey(run) == _selectedActivityKey);
            _activityList.SelectedItem = _activityViews[_selectedActivityKey].Row;
        }
        else if (_selectedActivityKey is not null)
        {
            _selectedActivity = _activityDetails = null;
            _selectedActivityKey = null;
            _activitySelectionVersion++;
            _activityLoadingKey = null;
            RenderActivityDetail();
        }
        _updatingActivityList = false;
        var messages = new List<string>();
        if (!Bool(result, "enabled", true)) messages.Add(L("活动记录已暂停"));
        if (Items(result, "errors").Any()) messages.Add(L("部分活动目录不可读取。请检查观察设置。"));
        if (runs.Count == 0) messages.Add(_activityFilter == "all" ? L("目前没有可见记录。旧 CLI、未启用观测或未添加的配置目录不会被伪造为“空闲”。") : L("没有符合筛选条件的记录。"));
        _activityHint!.Text = string.Join("\n", messages);
        _activityHint.Visibility = messages.Count == 0 ? Visibility.Collapsed : Visibility.Visible;
    }

    private ActivityRowView BuildActivityRow(JsonElement initial)
    {
        var title = Body(string.Empty);
        title.FontWeight = Microsoft.UI.Text.FontWeights.SemiBold;
        var summary = Secondary(string.Empty);
        var status = Secondary(string.Empty);
        var row = new ListViewItem
        {
            Tag = ActivityKey(initial), Padding = new Thickness(12, 10, 12, 10), HorizontalContentAlignment = HorizontalAlignment.Stretch,
            Content = new StackPanel { Spacing = 4, Children = { title, summary, status } }
        };
        return new ActivityRowView(row, run =>
        {
            title.Text = CommandLabel(Text(run, "command"));
            summary.Text = Timestamp(run, "started_at") + " · " + (Text(run, "origin") == "app" ? L("桌面 App") : L("终端 / AI"));
            status.Text = StatusLabel(Text(run, "status", "unknown")) + " · " + PhaseLabel(Text(run, "phase")) + " · " + Elapsed(run);
            AutomationProperties.SetName(row, title.Text + " · " + summary.Text + " · " + status.Text);
        });
    }

    private async Task ShowActivityDetailsAsync(JsonElement run)
    {
        var key = ActivityKey(run);
        if (_selectedActivityKey != key)
        {
            _selectedActivityKey = key;
            _selectedActivity = run.Clone();
            _activityDetails = null;
            _activitySelectionVersion++;
            _activityLoadingKey = null;
            RenderActivityDetail();
        }
        await RefreshSelectedActivityAsync(silent: false);
    }

    private async Task RefreshSelectedActivityAsync(bool silent)
    {
        if (_currentPage != "activity" || _selectedActivity is not { } run || _selectedActivityKey is not { } key || _activityLoadingKey == key) return;
        var runId = Text(run, "run_id");
        var directory = Text(run, "config_dir", Text(_state, "config_dir"));
        var selectionVersion = _activitySelectionVersion;
        _activityLoadingKey = key;
        try
        {
            var details = await _backend.CallAsync("activity.details", new { run_id = runId, config_dir = directory }, CancellationToken.None);
            if (_activitySelectionVersion != selectionVersion || _selectedActivityKey != key || _currentPage != "activity") return;
            if (!Bool(details, "ok"))
            {
                ShowActivityReadFailure(Text(details, "error", L("后端没有保存这条活动记录。")), silent);
                return;
            }
            var structureChanged = _activityDetails is not { } previous || ActivityStructure(previous) != ActivityStructure(details);
            _activityDetails = details.Clone();
            if (structureChanged) RenderActivityDetail();
            else if (_activityDetailSummary is not null) _activityDetailSummary.Text = ActivitySummary(Property(details, "run"));
            if (_activityReadError is not null) _activityReadError.Visibility = Visibility.Collapsed;
        }
        catch (Exception error)
        {
            if (_activitySelectionVersion == selectionVersion && _selectedActivityKey == key && _currentPage == "activity")
                ShowActivityReadFailure(SafeMessage(error), silent);
        }
        finally { if (_activitySelectionVersion == selectionVersion) _activityLoadingKey = null; }
    }

    private void ShowActivityReadFailure(string message, bool silent)
    {
        if (_activityReadError is not null)
        {
            _activityReadError.Text = message;
            _activityReadError.Visibility = Visibility.Visible;
        }
        if (!silent) ShowNotice(L("活动详情不可用"), message, InfoBarSeverity.Warning);
    }

    private static string ActivityStructure(JsonElement details)
    {
        var snapshot = JsonNode.Parse(details.GetRawText())!;
        if (snapshot["run"] is JsonObject run)
        {
            run.Remove("updated_at");
            run.Remove("elapsed_ms");
        }
        return snapshot.ToJsonString();
    }

    private static string ActivitySummary(JsonElement run) => L("{0} · {1} · 用时 {2}",
        Text(run, "origin") == "app" ? L("桌面 App") : L("终端 / AI"), PhaseLabel(Text(run, "phase")), Elapsed(run));

    private void RenderActivityDetail()
    {
        if (_activityDetail is null) return;
        if (_selectedActivity is not { } selected)
        {
            _activityDetail.Content = EmptyState(L("选择一条活动记录"), L("在左侧选择任务，查看状态、阶段事件和结果。"), Symbol.Clock);
            return;
        }
        var run = _activityDetails is { } details ? Property(details, "run") : selected;
        var runId = Text(run, "run_id", Text(selected, "run_id"));
        var panel = PagePanel();
        panel.Children.Add(HeadingWithStatus(CommandLabel(Text(run, "command")), StatusLabel(Text(run, "status", "unknown")), StatusTone(Text(run, "status"))));
        _activityDetailSummary = Secondary(ActivitySummary(run));
        panel.Children.Add(_activityDetailSummary);
        _activityReadError = Secondary(string.Empty);
        _activityReadError.Visibility = Visibility.Collapsed;
        panel.Children.Add(_activityReadError);
        var summary = new StackPanel { Spacing = 8 };
        summary.Children.Add(KeyValue(L("开始"), Timestamp(run, "started_at")));
        summary.Children.Add(KeyValue(L("配置目录"), Text(run, "config_dir", Text(selected, "config_dir"))));
        var providerModel = ActivityPresentation.ProviderModel(Text(run, "provider"), Text(run, "model"));
        if (Text(run, "provider").Length > 0 || Text(run, "model").Length > 0) summary.Children.Add(Body(providerModel));
        if (Text(run, "error_type").Length > 0) summary.Children.Add(Body(L("错误：{0}", ProviderCheckLabel(Text(run, "error_type")))));
        if (Text(run, "config_revision").Length > 0) summary.Children.Add(KeyValue(L("配置版本"), Text(run, "config_revision")));
        panel.Children.Add(Card(summary));
        if (_ownedRuns.Contains(runId))
            panel.Children.Add(IsTerminal(Text(run, "status"))
                ? ActionButton(L("查看结果"), () => ShowRunResultAsync(runId), operationKey: "result:" + runId)
                : ActionButton(L("取消任务"), () => CancelOwnedRunAsync(runId), operationKey: "cancel:" + runId, busyText: L("取消中…")));
        if (_activityDetails is { } current)
        {
            var events = new StackPanel { Spacing = 12 };
            foreach (var item in Items(current, "events"))
            {
                var text = Timestamp(item, "timestamp") + " · " + PhaseLabel(Text(item, "phase")) + " · " + StatusLabel(Text(item, "status", "unknown"));
                if (Text(item, "provider").Length > 0 || Text(item, "model").Length > 0) text += " · " + ActivityPresentation.ProviderModel(Text(item, "provider"), Text(item, "model"));
                if (Text(item, "error_type").Length > 0) text += " · " + ProviderCheckLabel(Text(item, "error_type"));
                events.Children.Add(Body(text));
            }
            if (events.Children.Count == 0) events.Children.Add(Secondary(L("没有可持久读取的事件；当前 App 自有任务仍可保留其内存状态。")));
            panel.Children.Add(SettingsSection(L("阶段事件"), Text(current, "note"), events));
            panel.Children.Add(DetailsButton(L("高级 JSON（仅活动元数据）"), () => ShowDetailsAsync(L("高级 JSON（仅活动元数据）"),
                DataText(JsonSerializer.Serialize(_activityDetails, new JsonSerializerOptions { WriteIndented = true })))));
        }
        else panel.Children.Add(Secondary(L("正在读取运行详情…")));
        _activityDetail.Content = PaneScroll(panel, "activity:detail:" + _selectedActivityKey);
    }

    private Task ShowActivityPreferencesAsync()
    {
        var content = new StackPanel { Spacing = 16 };
        _activityEnabledSwitch = CompactSwitch(L("记录活动"), Bool(_activitySnapshot, "enabled", Bool(Property(_state, "activity"), "enabled", true)));
        _activityEnabledSwitch.Toggled += async (_, _) =>
        {
            if (!_settingActivityEnabled) await RunOperationAsync("activity-setting", () => SetActivityEnabledAsync(_activityEnabledSwitch.IsOn));
        };
        content.Children.Add(SettingRow(L("记录活动"), L("关闭后保留已有历史。"), _activityEnabledSwitch));
        content.Children.Add(Divider());
        content.Children.Add(SectionHeading(L("活动观察范围")));
        content.Children.Add(Secondary(L("默认观察当前配置目录。可以添加其他目录，不会自动扫描你的文件。")));
        var directories = new StackPanel { Spacing = 8 };
        RenderExtraDirectories(directories);
        content.Children.Add(directories);
        if (ConnectedToWsl) content.Children.Add(Secondary(L("当前连接的是 WSL 中的 CLI，只观察它自己的配置目录。")));
        content.Children.Add(ActionButton(L("添加活动目录"), async () =>
        {
            var folder = await PickFolderAsync();
            if (folder is null || _extraActivityDirectories.Contains(folder.Path, StringComparer.OrdinalIgnoreCase)) return;
            _extraActivityDirectories.Add(folder.Path);
            SaveExtraDirectories();
            RenderExtraDirectories(directories);
            await RefreshActivityAsync(silent: true);
        }, enabled: () => !ConnectedToWsl));
        return ShowDetailsAsync(L("观察设置…"), content);
    }
}
