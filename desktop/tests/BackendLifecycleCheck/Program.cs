using SmartSearch.Desktop;

Localization.Preference = "zh";
if (ActivityPresentation.ProviderModel("firecrawl", "") != "服务商：firecrawl" ||
    ActivityPresentation.ProviderModel("openai-compatible", "grok-test") != "服务商：openai-compatible · 模型：grok-test" ||
    ActivityPresentation.ProviderModel("", "") != "")
    throw new Exception("Activity captions must distinguish a model from a non-model provider.");

// Real wsl.exe: start a CLI inside a distribution from its launch argv, with a Linux config directory.
if (args.Length >= 4 && args[0] == "--wsl")
{
    var (distribution, linuxConfig) = (args[1], args[2]);
    var installation = new CLIInstallation("wsl://" + distribution, Path.Combine(Environment.SystemDirectory, "wsl.exe"),
        ["-d", distribution, "--cd", "~", "--exec", .. args[3..]], "", "wsl", true, [], "", new() { ["WSL_UTF8"] = "1" }, Distribution: distribution);
    await using var wslClient = new BackendClient { Installation = installation };
    for (var attempt = 0; attempt < 2; attempt++)
    {
        var state = await wslClient.StartAsync(linuxConfig, CancellationToken.None);
        if (state.GetProperty("config_dir").GetString() != linuxConfig) throw new Exception("WSL backend did not use the Linux config directory.");
        var pong = await wslClient.CallAsync("ping", new { }, CancellationToken.None);
        if (pong.GetProperty("protocol_version").GetInt32() != 1) throw new Exception("WSL reconnect failed.");
        await wslClient.StopAsync();
        if (wslClient.IsConnected) throw new Exception("Stopped WSL backend is still connected.");
    }
    Console.WriteLine("PASS: a CLI inside WSL " + distribution + " serves the private protocol through wsl.exe and reconnects.");
    return;
}

// The same real client must reconnect after stopping for a failed installer
// launch. No UI, installer, package manager, or provider is invoked here.
var standalone = args.Length == 3 && args[0] == "--standalone";
if (!standalone && args.Length != 2) throw new ArgumentException("Pass Python executable and an isolated config directory, or --standalone CLI config-directory.");
var configDirectory = Path.GetFullPath(args[^1]);
await using (var missing = new BackendClient(Path.Combine(configDirectory, "missing-smart-search.exe")))
{
    try
    {
        await missing.StartAsync(configDirectory, CancellationToken.None);
        throw new Exception("Missing executable should fail before starting a process.");
    }
    catch (BackendDisconnectedException error)
    {
        if (!error.Message.Contains("概览的本地环境")) throw new Exception("Missing CLI recovery must point to Overview.");
    }
}
await using var client = standalone ? new BackendClient() : new BackendClient(args[0], ["-m", "smart_search.desktop_entry"]);
if (standalone)
{
    var manager = new CLIInstallationManager(Path.Combine(configDirectory, "detection-state"), searchPath: "");
    manager.SetCliPath(Path.GetFullPath(args[1]));
    await manager.DiscoverAsync();
    if (manager.Selected is not { Compatible: true, Source: "manual", CanManage: false } selected)
        throw new Exception("Standalone discovery failed: " + manager.Message);
    // Isolate background Skill maintenance as well as provider configuration.
    selected.Environment["LOCALAPPDATA"] = Path.Combine(configDirectory, "local");
    selected.Environment["APPDATA"] = Path.Combine(configDirectory, "roaming");
    selected.Environment["USERPROFILE"] = configDirectory;
    selected.Environment["HOME"] = configDirectory;
    selected.Environment["SMART_SEARCH_ACTIVITY_ENABLED"] = "false";
    client.Installation = selected;
}
for (var attempt = 0; attempt < 2; attempt++)
{
    var state = await client.StartAsync(configDirectory, CancellationToken.None);
    if (state.GetProperty("protocol_version").GetInt32() != 1) throw new Exception("Handshake failed.");
    var pong = await client.CallAsync("ping", new { }, CancellationToken.None);
    if (pong.GetProperty("protocol_version").GetInt32() != 1) throw new Exception("Reconnect failed.");
    await client.StopAsync();
    if (client.IsConnected) throw new Exception("Stopped backend is still connected.");
}
Console.WriteLine("PASS: " + (standalone ? "standalone discovery without Node/npm and " : "") + "stop/reconnect preserve the private RPC client.");
