import Foundation

enum BackendClientError: LocalizedError, Sendable {
    case backendNotFound(String)
    case notConnected
    case incompatibleProtocol
    case timedOut
    case disconnected
    case malformedMessage
    case backendRejected(String)

    var errorDescription: String? {
        switch self {
        case let .backendNotFound(path):
            return L("找不到所选 CLI：{0}。请打开概览的本地环境，重新检测或选择已有 CLI。", path)
        case .notConnected:
            return L("后端尚未连接。")
        case .incompatibleProtocol:
            return L("App 与所选 CLI 的协议不兼容，请更新 CLI 或 App。")
        case .timedOut:
            return L("后端未在设定时间内响应。")
        case .disconnected:
            return L("后端进程已断开。")
        case .malformedMessage:
            return L("后端返回了无法读取的协议消息。")
        case let .backendRejected(message):
            return message.isEmpty ? L("后端拒绝了该请求。请检查输入或查看脱敏诊断。") : message
        }
    }
}

struct BackendEvent: Sendable {
    let name: String
    let data: JSONValue
    let generation: String?
}

private struct RequestEnvelope: Encodable {
    let id: Int
    let method: String
    let params: JSONValue
}

private struct PendingRequest {
    let token: UUID
    let continuation: CheckedContinuation<JSONValue, Error>
}

actor BackendClient {
    static let protocolVersion = 1

    private var process: Process?
    private var inputHandle: FileHandle?
    private var outputHandle: FileHandle?
    private var errorHandle: FileHandle?
    private var processToken: UUID?
    private var generation: String?
    private var stdoutBuffer = Data()
    private var outputTask: Task<Void, Never>?
    private var outputContinuation: AsyncStream<Data>.Continuation?
    private var nextID = 1
    private var timeoutSeconds: TimeInterval = 30
    private var pending: [Int: PendingRequest] = [:]
    private var timeoutTasks: [Int: Task<Void, Never>] = [:]
    private var eventContinuation: AsyncStream<BackendEvent>.Continuation?
    private var eventStreamID: UUID?

    func eventStream() -> AsyncStream<BackendEvent> {
        let streamID = UUID()
        return AsyncStream { continuation in
            eventContinuation = continuation
            eventStreamID = streamID
            continuation.onTermination = { [weak self] _ in
                Task { await self?.clearEventContinuation(streamID) }
            }
        }
    }

    func setTimeout(seconds: TimeInterval) {
        timeoutSeconds = min(max(seconds, 5), 300)
    }

    func start(backendURL: URL, arguments: [String] = [], environment: [String: String] = [:]) async throws {
        await shutdown()
        guard FileManager.default.isExecutableFile(atPath: backendURL.path) else {
            throw BackendClientError.backendNotFound(backendURL.path)
        }

        let input = Pipe()
        let output = Pipe()
        let error = Pipe()
        let newProcess = Process()
        newProcess.executableURL = backendURL
        newProcess.arguments = arguments + ["--desktop-backend"]
        newProcess.environment = ProcessInfo.processInfo.environment.merging(environment) { _, value in value }
        newProcess.standardInput = input
        newProcess.standardOutput = output
        newProcess.standardError = error

        let token = UUID()
        newProcess.terminationHandler = { [weak self] finishedProcess in
            let status = finishedProcess.terminationStatus
            Task { await self?.processDidExit(token: token, status: status) }
        }

        do {
            try newProcess.run()
        } catch {
            throw BackendClientError.backendNotFound(backendURL.path)
        }

        process = newProcess
        inputHandle = input.fileHandleForWriting
        outputHandle = output.fileHandleForReading
        errorHandle = error.fileHandleForReading
        processToken = token
        generation = nil
        stdoutBuffer.removeAll(keepingCapacity: true)
        nextID = 1

        // Pipe callbacks arrive in order; separate Tasks do not. Feed one
        // consumer so a large JSON response cannot have its chunks reordered.
        let chunks = AsyncStream<Data> { continuation in
            outputContinuation = continuation
            output.fileHandleForReading.readabilityHandler = { handle in
                let data = handle.availableData
                if data.isEmpty {
                    handle.readabilityHandler = nil
                    continuation.finish()
                } else {
                    continuation.yield(data)
                }
            }
        }
        outputTask = Task { [weak self] in
            for await data in chunks {
                guard !Task.isCancelled else { break }
                await self?.consumeStdout(data, token: token)
            }
        }
        // stderr can contain diagnostics but must not become protocol or UI content.
        error.fileHandleForReading.readabilityHandler = { handle in
            _ = handle.availableData
        }
    }

    func initialize(configDirectory: String? = nil, enableUpdateChecks: Bool = true, language: String = "auto", independentCLI: Bool = false) async throws -> JSONValue {
        var params: [String: JSONValue] = ["protocol_version": .number(Double(Self.protocolVersion)),
            "app_version": .string(Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "development"),
            "enable_update_checks": .bool(enableUpdateChecks), "lang": .string(language),
            "include_config_secrets": .bool(true), "independent_cli": .bool(independentCLI)]
        if let configDirectory, !configDirectory.isEmpty {
            params["config_dir"] = .string(configDirectory)
        }
        let result = try await request(method: "initialize", params: .object(params))
        guard result["protocol_version"]?.integerValue == Self.protocolVersion else {
            throw BackendClientError.incompatibleProtocol
        }
        guard let reportedGeneration = result["generation"]?.stringValue, !reportedGeneration.isEmpty else {
            throw BackendClientError.malformedMessage
        }
        generation = reportedGeneration
        return result
    }

    func request(
        method: String,
        params: JSONValue = .object([:]),
        timeout: TimeInterval? = nil
    ) async throws -> JSONValue {
        guard let token = processToken, let inputHandle else {
            throw BackendClientError.notConnected
        }
        let id = nextID
        nextID += 1
        let envelope = RequestEnvelope(id: id, method: method, params: params)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.withoutEscapingSlashes]
        guard var line = try? encoder.encode(envelope) else {
            throw BackendClientError.malformedMessage
        }
        line.append(0x0A)

        return try await withCheckedThrowingContinuation { continuation in
            pending[id] = PendingRequest(token: token, continuation: continuation)
            let requestTimeout = timeout ?? timeoutSeconds
            timeoutTasks[id] = Task { [weak self] in
                do {
                    try await Task.sleep(nanoseconds: UInt64(requestTimeout * 1_000_000_000))
                } catch { return }
                await self?.expireRequest(id, token: token)
            }
            inputHandle.write(line)
        }
    }

    func shutdown() async {
        if processToken != nil {
            _ = try? await request(method: "shutdown", timeout: 5)
        }
        terminateOwnedProcess()
    }

    func isConnected() -> Bool {
        processToken != nil && process?.isRunning == true
    }

    private func consumeStdout(_ data: Data, token: UUID) {
        guard token == processToken else { return }
        stdoutBuffer.append(data)
        while let newline = stdoutBuffer.firstIndex(of: 0x0A) {
            let line = stdoutBuffer.prefix(upTo: newline)
            stdoutBuffer.removeSubrange(...newline)
            guard let text = String(data: line, encoding: .utf8) else {
                failAll(for: token, with: BackendClientError.malformedMessage)
                continue
            }
            consumeMessage(text, token: token)
        }
    }

    private func consumeMessage(_ line: String, token: UUID) {
        guard token == processToken else { return }
        guard let decoded = try? JSONDecoder().decode(JSONValue.self, from: Data(line.utf8)),
              let object = decoded.objectValue else {
            eventContinuation?.yield(BackendEvent(name: "backend.protocol-error", data: .object([:]), generation: nil))
            return
        }

        let messageGeneration = object.string("generation")
            ?? object.object("data").string("generation")
            ?? object.object("result").string("generation")
        if let generation, let messageGeneration, generation != messageGeneration {
            return
        }

        if let id = object["id"]?.integerValue {
            guard let request = pending.removeValue(forKey: id), request.token == token else { return }
            timeoutTasks.removeValue(forKey: id)?.cancel()
            if let result = object["result"] {
                request.continuation.resume(returning: result)
            } else if let error = object["error"]?.objectValue {
                // The private backend sanitizes this protocol field before emission.
                let message = error["message"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                request.continuation.resume(throwing: BackendClientError.backendRejected(message))
            } else {
                request.continuation.resume(throwing: BackendClientError.malformedMessage)
            }
            return
        }

        if let name = object.string("event") {
            eventContinuation?.yield(BackendEvent(name: name, data: object["data"] ?? .object([:]), generation: messageGeneration))
        }
    }

    private func expireRequest(_ id: Int, token: UUID) {
        guard token == processToken, let request = pending.removeValue(forKey: id) else { return }
        timeoutTasks.removeValue(forKey: id)?.cancel()
        request.continuation.resume(throwing: BackendClientError.timedOut)
    }

    private func processDidExit(token: UUID, status: Int32) {
        guard token == processToken else { return }
        failAll(for: token, with: BackendClientError.disconnected)
        closePipes()
        process = nil
        inputHandle = nil
        processToken = nil
        generation = nil
        eventContinuation?.yield(BackendEvent(name: "backend.exited", data: .object(["status": .number(Double(status))]), generation: nil))
    }

    private func failAll(for token: UUID, with error: Error) {
        let matches = pending.filter { $0.value.token == token }
        for (id, request) in matches {
            pending.removeValue(forKey: id)
            timeoutTasks.removeValue(forKey: id)?.cancel()
            request.continuation.resume(throwing: error)
        }
    }

    private func terminateOwnedProcess() {
        guard let token = processToken else { return }
        failAll(for: token, with: BackendClientError.disconnected)
        let ownedProcess = process
        closePipes()
        process = nil
        inputHandle = nil
        processToken = nil
        generation = nil
        if ownedProcess?.isRunning == true {
            ownedProcess?.terminate()
        }
    }

    private func closePipes() {
        inputHandle?.closeFile()
        outputHandle?.readabilityHandler = nil
        errorHandle?.readabilityHandler = nil
        outputContinuation?.finish()
        outputContinuation = nil
        outputTask?.cancel()
        outputTask = nil
        outputHandle = nil
        errorHandle = nil
    }

    private func clearEventContinuation(_ streamID: UUID) {
        guard eventStreamID == streamID else { return }
        eventContinuation = nil
        eventStreamID = nil
    }
}

enum BackendLocator {
    static func resolvedURL(overridePath: String?) throws -> URL {
        if let overridePath, !overridePath.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return URL(fileURLWithPath: overridePath)
        }
        throw BackendClientError.backendNotFound(L("尚未选择 CLI"))
    }
}
