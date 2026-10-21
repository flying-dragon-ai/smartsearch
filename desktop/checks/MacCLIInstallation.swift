import Foundation

@main struct CLIInstallationCheck {
    @MainActor static func main() async throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1])
        let suite = "com.smartsearch.test.cli." + UUID().uuidString
        let preferences = UserDefaults(suiteName: suite)!
        defer { preferences.removePersistentDomain(forName: suite) }
        let first = root.appendingPathComponent("npm 1 & space"), second = root.appendingPathComponent("npm 2 & space")
        let search = first.appendingPathComponent("bin").path + ":" + second.appendingPathComponent("bin").path
        var now = Date(), checks = 0, shouldFail = false
        let load: () async throws -> String = {
            checks += 1
            if shouldFail { throw CheckFailure.failed("offline") }
            return "1.2.4"
        }
        let manager = CLIInstallationManager(searchPath: search, preferences: preferences, versionLoader: load, clock: { now })
        await manager.discover()
        try expect(manager.npm?.prefix == first.path && manager.selected?.compatible == false && manager.selected?.canManage == true, "Legacy npm installation must remain manageable without executing its Python wrapper")
        try expect(manager.installations.count == 2, "Every npm prefix must be detected")
        try expect(!FileManager.default.fileExists(atPath: root.appendingPathComponent("legacy-executed").path), "Legacy wrapper was executed")
        manager.setNpmPath(root.appendingPathComponent("missing/npm").path)
        await manager.discover()
        try expect(manager.npm == nil && manager.selected == nil, "Invalid manual npm must not fall back to a different installation")
        manager.setNpmPath(second.appendingPathComponent("bin/npm").path)
        await manager.discover()
        try expect(manager.selected?.compatible == true && manager.npm?.prefix == second.path, "Manual npm selection/protocol handshake failed")
        await manager.checkAutomatically(onLaunch: true)
        await manager.checkAutomatically(onLaunch: true)
        try expect(checks == 1 && manager.updateAvailable, "Startup check or update status failed")
        now.addTimeInterval(86399)
        await manager.checkAutomatically()
        try expect(checks == 1, "Checked before 24 hours")
        now.addTimeInterval(1)
        await manager.checkAutomatically()
        try expect(checks == 2, "Did not check at 24 hours")
        let successfulDate = manager.checkedAt
        shouldFail = true
        now.addTimeInterval(86400)
        await manager.checkAutomatically()
        await manager.checkAutomatically()
        try expect(checks == 3 && manager.checkedAt == successfulDate && !manager.checkError.isEmpty, "Failure must retain cache and throttle retries")
        manager.automaticallyChecks = false
        now.addTimeInterval(86400)
        await manager.checkAutomatically()
        try expect(checks == 3, "Disabled automatic checks still ran")
        shouldFail = false
        await manager.checkVersion()
        try await manager.installOrRepair(expectedVersion: "1.2.4")
        try expect(manager.selected?.version == "1.2.4" && manager.selected?.compatible == true, "Install must verify the resulting runtime")
        let restored = CLIInstallationManager(searchPath: search, preferences: preferences, versionLoader: load, clock: { now })
        await restored.discover()
        try expect(restored.manualNpmPath == manager.manualNpmPath && !restored.automaticallyChecks && restored.checkedAt == manager.checkedAt, "Preferences and successful check did not persist")
        try await manager.uninstall()
        let operations = try Data(contentsOf: second.appendingPathComponent("operations.json"))
        let args = try JSONDecoder().decode([String].self, from: operations)
        try expect(args == ["uninstall", "--global", "--prefix", second.path, "@konbakuyomu/smart-search"], "npm prefix/argument boundary changed")
        try expect(FileManager.default.fileExists(atPath: first.appendingPathComponent("lib/node_modules/@konbakuyomu/smart-search/package.json").path), "Another npm installation was changed")
        let oldGlobal = ProcessInfo.processInfo.environment["MISE_GLOBAL_CONFIG_FILE"]
        setenv("MISE_GLOBAL_CONFIG_FILE", root.appendingPathComponent("global.toml").path, 1)
        defer { if let oldGlobal { setenv("MISE_GLOBAL_CONFIG_FILE", oldGlobal, 1) } else { unsetenv("MISE_GLOBAL_CONFIG_FILE") } }
        preferences.removeObject(forKey: "SmartSearchDesktop.npmPath")
        preferences.removeObject(forKey: "SmartSearchDesktop.selectedCLI")
        preferences.set(root.appendingPathComponent("mise/installs/npm-konbakuyomu-smart-search/1.2.2/node_modules/@konbakuyomu/smart-search").path, forKey: "SmartSearchDesktop.selectedCLI")
        let upgraded = CLIInstallationManager(searchPath: root.appendingPathComponent("mise bin").path + ":" + search, preferences: preferences, versionLoader: load)
        await upgraded.discover()
        try expect(upgraded.selected?.source == "mise" && upgraded.selected?.version == "1.2.3" && upgraded.message.isEmpty, "Follow the active mise version after an upgrade outside the App")
        preferences.removeObject(forKey: "SmartSearchDesktop.selectedCLI")
        let mise = CLIInstallationManager(searchPath: root.appendingPathComponent("mise bin").path + ":" + search, preferences: preferences, versionLoader: load)
        await mise.discover()
        try expect(mise.selected?.source == "mise" && mise.selected?.compatible == true && mise.selected?.canManage == true, "Active mise tool outside npm prefix must be selected: " + mise.message)
        try expect(mise.selected?.managerOptions == ["--tool-option", "allow_low_downloads=\"true\""], "Preserve mise options")
        await mise.checkVersion()
        try await mise.installOrRepair(expectedVersion: "1.2.4")
        try expect(mise.selected?.version == "1.2.4" && mise.selected?.source == "mise", "Keep mise ownership after update")
        let use = try JSONDecoder().decode([String].self, from: Data(contentsOf: root.appendingPathComponent("mise-operations.json")))
        try expect(use == ["use", "--global", "--pin", "--tool-option", "allow_low_downloads=\"true\"", "npm:@konbakuyomu/smart-search@1.2.4"], "Update through original manager")
        mise.setCliPath(root.appendingPathComponent("missing/smart-search").path)
        await mise.discover()
        try expect(mise.selected == nil && !mise.canInstall && !mise.message.isEmpty, "Missing explicit CLI must not silently switch")
        try expect(CLIInstallationManager.miseOptions("version = \"1.2.3\"\npostinstall = \"custom\"", requested: "1.2.3") == nil, "Complex mise options stay read-only")
        try expect(CLIInstallationManager.miseOptions("version = \"^1\"", requested: "^1") == nil, "Mise version constraints stay intact")
        print("PASS: npm/mise discovery and ownership, manual selection, legacy isolation, scoped updates, startup/24h checks and persistence")
    }
    static func expect(_ condition: Bool, _ message: String) throws { if !condition { throw CheckFailure.failed(message) } }
}
enum CheckFailure: Error { case failed(String) }
extension Bundle { static var module: Bundle { .main } }
