using System.Text.Json;
using System.Xml.Linq;
using SmartSearch.Desktop;
using Velopack;
using Velopack.Locators;

if (args.Length != 7) throw new ArgumentException("Expected feed, isolated root, package ID, old/new version, architecture, result path.");
var (feed, root, id, oldVersion, version, architecture, result) = (args[0], Path.GetFullPath(args[1]), args[2], args[3], args[4], args[5], args[6]);
if (!id.StartsWith("com.smartsearch.test.", StringComparison.Ordinal) || !Uri.TryCreate(feed, UriKind.Absolute, out var uri) || uri.Host != "127.0.0.1")
    throw new ArgumentException("Only the isolated test identity and loopback feed are allowed.");
var current = Path.Combine(root, "current");
var locator = new TestVelopackLocator(id, oldVersion, Path.Combine(root, "packages"), current, root,
    Path.Combine(root, "Update.exe"), $"win-{architecture}-stable");
var manager = new UpdateManager(feed, new UpdateOptions { ExplicitChannel = $"win-{architecture}-stable", AllowVersionDowngrade = false }, locator);
var plan = await manager.CheckForUpdatesAsync();
if (plan is null || plan.TargetFullRelease.Version.ToString() != version || plan.DeltasToTarget.Length == 0)
    throw new InvalidOperationException("SDK did not select the expected delta update.");
var updater = new AppUpdater(manager);
await updater.CheckAsync();
if (!updater.Available || updater.LatestVersion != version) throw new InvalidOperationException("App adapter failed to find the update.");
// Cancel at the final progress notification, including the SDK-completed/UI-continuation boundary.
using (var cancel = new CancellationTokenSource())
{
    await updater.DownloadAsync(() => { if (updater.Progress == 100) cancel.Cancel(); }, cancel.Token);
    if (!cancel.IsCancellationRequested || updater.Ready || updater.Error.Length == 0)
        throw new InvalidOperationException("A cancelled download became ready to install.");
}
await updater.CheckAsync();
await updater.DownloadAsync(() => { }, CancellationToken.None);
if (!updater.Ready) throw new InvalidOperationException("App adapter did not download and verify: " + updater.Error);
// The actual updater applies the actual candidate package; the locator only confines it to this test installation.
manager.WaitExitThenApplyUpdates(manager.UpdatePendingRestart, silent: true, restart: false);
var timeout = DateTime.UtcNow.AddSeconds(90);
bool installed = false;
while (DateTime.UtcNow < timeout)
{
    try
    {
        installed = XDocument.Load(Path.Combine(current, "sq.version")).Descendants()
            .Any(x => x.Name.LocalName == "version" && x.Value == version);
        if (installed) break;
    }
    catch (IOException) { }
    await Task.Delay(200);
}
if (!installed) throw new InvalidOperationException("The updater did not install the target version.");
if (Directory.Exists(Path.Combine(current, "backend"))) throw new InvalidOperationException("The App must not contain a CLI.");
File.WriteAllText(result, JsonSerializer.Serialize(new { version, packageId = id, adapter = "AppUpdater", installed = true, deltaCount = plan.DeltasToTarget.Length }));
Console.WriteLine("Native candidate download, verification and application passed.");
