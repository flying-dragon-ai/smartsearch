import Foundation

// This standalone protocol probe compiles the production client directly.
// SwiftPM normally supplies this accessor for Localization.swift.
extension Bundle {
    static var module: Bundle { .main }
}

@main
struct MacBackendLifecycle {
    static func main() async throws {
        guard CommandLine.arguments.count == 4,
              let iterations = Int(CommandLine.arguments[3]), iterations > 0 else {
            throw failure("Expected backend path, isolated config directory and iteration count")
        }
        let executable = URL(fileURLWithPath: CommandLine.arguments[1])
        let directory = URL(fileURLWithPath: CommandLine.arguments[2])
        let client = BackendClient()

        for iteration in 1...iterations {
            let profile = directory.appendingPathComponent("profile-\(iteration)")
            try FileManager.default.createDirectory(at: profile, withIntermediateDirectories: true)
            let started = Date()
            var phase = "initialize"
            do {
                // Match the App's startup budget: a signed backend can be cold
                // on a busy runner. Keep the tighter IPC deadline once ready.
                await client.setTimeout(seconds: 30)
                try await client.start(backendURL: executable)
                let snapshot = try await client.initialize(
                    configDirectory: profile.path, enableUpdateChecks: false, language: "zh"
                )
                guard snapshot["protocol_version"]?.integerValue == 1,
                      snapshot["commands"]?.arrayValue?.isEmpty == false else {
                    throw failure("Initialize did not return the actual protocol and command catalog")
                }
                await client.setTimeout(seconds: 5)
                phase = "concurrent get_state"
                // Real get_state replies exceed a pipe chunk. Concurrent requests
                // also verify response IDs while unsolicited activity events arrive.
                try await withThrowingTaskGroup(of: Void.self) { group in
                    for _ in 0..<4 {
                        group.addTask {
                            let state = try await client.request(method: "get_state")
                            guard state["generation"] == snapshot["generation"],
                                  state["commands"] == snapshot["commands"] else {
                                throw failure("State response was lost, reordered or truncated")
                            }
                        }
                    }
                    try await group.waitForAll()
                }
                phase = "ping"
                let ping = try await client.request(method: "ping")
                guard ping["generation"] == snapshot["generation"] else {
                    throw failure("Ping was delivered to the wrong backend generation")
                }
                phase = "shutdown"
                await client.shutdown()
                guard await !client.isConnected() else { throw failure("Shutdown retained a connection") }
                print("Backend lifecycle \(iteration)/\(iterations) passed (\(String(format: "%.2f", Date().timeIntervalSince(started)))s)")
            } catch {
                let diagnostic = "Backend lifecycle \(iteration)/\(iterations) failed during \(phase): \(error)\n"
                FileHandle.standardError.write(Data(diagnostic.utf8))
                await client.shutdown()
                throw error
            }
        }
    }

    private static func failure(_ message: String) -> NSError {
        NSError(domain: "MacBackendLifecycle", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
    }
}
