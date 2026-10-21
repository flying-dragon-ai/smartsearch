using static SmartSearch.Desktop.Localization;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SmartSearch.Desktop;

internal sealed class BackendClient : IAsyncDisposable
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    private readonly SemaphoreSlim _writeGate = new(1, 1);
    private readonly ConcurrentDictionary<int, TaskCompletionSource<JsonElement>> _pending = new();
    private readonly string? _configuredPath;
    private readonly IReadOnlyList<string> _configuredArguments;
    private Process? _process;
    private StreamWriter? _writer;
    private CancellationTokenSource? _readerCancellation;
    private int _nextId;
    private string? _generation;

    public BackendClient(string? configuredPath = null, IEnumerable<string>? configuredArguments = null)
    {
        _configuredPath = configuredPath;
        _configuredArguments = configuredArguments?.ToArray() ?? [];
    }

    public bool IsConnected => _process is { HasExited: false };
    public string? Generation => _generation;
    public string? BackendPath { get; private set; }
    internal CLIInstallation? Installation { get; set; }
    internal bool UsesExplicitBackend => !string.IsNullOrWhiteSpace(_configuredPath ?? Environment.GetEnvironmentVariable("SMART_SEARCH_BACKEND_PATH"));

    public event EventHandler<BackendEvent>? EventReceived;
    public event EventHandler<string>? Disconnected;

    public async Task<JsonElement> StartAsync(string? configDirectory, CancellationToken cancellationToken)
    {
        await StopAsync(sendShutdown: false);
        BackendPath = ResolveBackendPath();
        if (!File.Exists(BackendPath))
            throw new BackendDisconnectedException(L("找不到所选 CLI：{0}。请打开概览的本地环境，重新检测或选择已有 CLI。", BackendPath));

        var startInfo = new ProcessStartInfo
        {
            FileName = BackendPath,
            UseShellExecute = false,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            WindowStyle = ProcessWindowStyle.Hidden,
            StandardInputEncoding = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
            StandardOutputEncoding = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
            StandardErrorEncoding = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false)
        };
        foreach (var argument in UsesExplicitBackend ? _configuredArguments : Installation?.Arguments ?? [])
            startInfo.ArgumentList.Add(argument);
        startInfo.ArgumentList.Add("--desktop-backend");
        if (!UsesExplicitBackend && Installation is { } installed)
            foreach (var (key, value) in installed.Environment) startInfo.Environment[key] = value;

        var process = new Process { StartInfo = startInfo, EnableRaisingEvents = true };
        process.Exited += (_, _) => OnProcessExited(process);
        if (!process.Start())
            throw new BackendDisconnectedException(L("无法启动 Smart Search 后端。"));

        _process = process;
        _writer = process.StandardInput;
        _readerCancellation = new CancellationTokenSource();
        _ = ReadOutputAsync(process, _readerCancellation.Token);
        _ = DrainDiagnosticsAsync(process, _readerCancellation.Token);

        var result = await CallAsync("initialize", new
        {
            protocol_version = 1,
            lang = Localization.Language,
            config_dir = configDirectory,
            app_version = _configuredPath is null ? System.Reflection.Assembly.GetEntryAssembly()?.GetName().Version?.ToString(3) : "development",
            enable_update_checks = false,
            independent_cli = !UsesExplicitBackend
        }, cancellationToken);

        var protocol = GetInt(result, "protocol_version");
        if (protocol != 1)
            throw new BackendDisconnectedException(L("后端协议版本不兼容：{0}。需要版本 1。", protocol?.ToString() ?? L("未知")));

        _generation = GetString(result, "generation");
        if (string.IsNullOrWhiteSpace(_generation))
            throw new BackendDisconnectedException(L("后端未返回 generation，已拒绝继续通信。"));
        return result;
    }

    public async Task<JsonElement> CallAsync(string method, object? parameters, CancellationToken cancellationToken)
    {
        var process = _process;
        var writer = _writer;
        if (process is null || writer is null || process.HasExited)
            throw new BackendDisconnectedException(L("后端未连接。"));

        var id = Interlocked.Increment(ref _nextId);
        if (id <= 0)
            throw new BackendDisconnectedException(L("请求编号已耗尽，请重新启动应用。"));

        var response = new TaskCompletionSource<JsonElement>(TaskCreationOptions.RunContinuationsAsynchronously);
        if (!_pending.TryAdd(id, response))
            throw new BackendDisconnectedException(L("请求编号冲突。"));

        try
        {
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(30));
            var requestToken = timeout.Token;
            var line = JsonSerializer.Serialize(new { id, method, @params = parameters }, JsonOptions);
            await _writeGate.WaitAsync(requestToken);
            try
            {
                await writer.WriteLineAsync(line.AsMemory(), requestToken);
                await writer.FlushAsync(requestToken);
            }
            finally
            {
                _writeGate.Release();
            }
            return await response.Task.WaitAsync(requestToken);
        }
        finally
        {
            _pending.TryRemove(id, out _);
        }
    }

    public async Task StopAsync(bool sendShutdown = true)
    {
        var process = _process;
        if (process is null)
            return;

        if (sendShutdown && !process.HasExited)
        {
            try
            {
                using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(3));
                await CallAsync("shutdown", new { }, timeout.Token);
            }
            catch (Exception)
            {
                // Continue below so a timed-out private backend cannot become an orphan.
            }
        }

        if (!process.HasExited)
        {
            try
            {
                await process.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(3));
            }
            catch (TimeoutException)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync();
            }
        }
        ReleaseProcess(process);
    }

    private async Task ReadOutputAsync(Process process, CancellationToken cancellationToken)
    {
        try
        {
            while (!cancellationToken.IsCancellationRequested && await process.StandardOutput.ReadLineAsync(cancellationToken) is { } line)
            {
                if (!ReferenceEquals(_process, process) || string.IsNullOrWhiteSpace(line))
                    continue;
                HandleLine(line);
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (Exception)
        {
            OnProcessExited(process);
        }
    }

    private static async Task DrainDiagnosticsAsync(Process process, CancellationToken cancellationToken)
    {
        try
        {
            while (!cancellationToken.IsCancellationRequested && await process.StandardError.ReadLineAsync(cancellationToken) is not null)
            {
                // stderr is intentionally not rendered or persisted: it may contain upstream diagnostics.
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (Exception)
        {
            // stdout/exit state remains the source of the user-facing backend status.
        }
    }

    private void HandleLine(string line)
    {
        JsonElement root;
        try
        {
            using var document = JsonDocument.Parse(line);
            root = document.RootElement.Clone();
        }
        catch (JsonException)
        {
            return;
        }

        if (root.TryGetProperty("id", out var idProperty) && idProperty.TryGetInt32(out var id))
        {
            if (!_pending.TryGetValue(id, out var waiting))
                return;
            if (root.TryGetProperty("error", out var error))
            {
                waiting.TrySetException(new BackendRpcException(GetString(error, "code") ?? "unknown_error", GetString(error, "message")));
                return;
            }
            if (root.TryGetProperty("result", out var result))
                waiting.TrySetResult(result.Clone());
            else
                waiting.TrySetException(new BackendDisconnectedException(L("后端响应缺少 result。")));
            return;
        }

        if (!root.TryGetProperty("event", out var eventProperty) || eventProperty.ValueKind != JsonValueKind.String ||
            !root.TryGetProperty("data", out var data))
            return;

        var eventGeneration = GetString(data, "generation");
        if (!string.IsNullOrWhiteSpace(eventGeneration) && _generation is not null && eventGeneration != _generation)
            return;
        EventReceived?.Invoke(this, new BackendEvent(eventProperty.GetString()!, data.Clone()));
    }

    private void OnProcessExited(Process process)
    {
        if (!ReferenceEquals(_process, process))
            return;
        foreach (var pending in _pending.Values)
            pending.TrySetException(new BackendDisconnectedException(L("Smart Search 后端已退出。")));
        Disconnected?.Invoke(this, L("后端已退出；当前快照不再代表实时状态。"));
    }

    private void ReleaseProcess(Process process)
    {
        if (!ReferenceEquals(_process, process))
            return;
        _readerCancellation?.Cancel();
        _readerCancellation?.Dispose();
        _readerCancellation = null;
        _writer?.Dispose();
        _writer = null;
        _process = null;
        _generation = null;
        process.Dispose();
    }

    private string ResolveBackendPath()
    {
        var configured = _configuredPath ?? Environment.GetEnvironmentVariable("SMART_SEARCH_BACKEND_PATH");
        if (!string.IsNullOrWhiteSpace(configured))
            return Path.GetFullPath(configured);
        return Installation?.Executable ?? throw new BackendDisconnectedException(L("尚未选择 CLI"));
    }

    private static string? GetString(JsonElement value, string property) =>
        value.TryGetProperty(property, out var item) && item.ValueKind == JsonValueKind.String ? item.GetString() : null;

    private static int? GetInt(JsonElement value, string property) =>
        value.TryGetProperty(property, out var item) && item.TryGetInt32(out var result) ? result : null;

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
        _writeGate.Dispose();
    }
}
