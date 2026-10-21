import Foundation

enum Localization {
    static let preferenceKey = "SmartSearchDesktop.language"
    static var language: String {
        resolve(UserDefaults.standard.string(forKey: preferenceKey) ?? "auto")
    }

    static func resolve(_ preference: String) -> String {
        if preference == "zh" || preference == "en" { return preference }
        return (Locale.preferredLanguages.first ?? "en").lowercased().hasPrefix("zh") ? "zh" : "en"
    }

    static let messages: [String: [String]] = {
        // Installed .apps use their own resource directory; SwiftPM serves development/tests.
        guard let url = Bundle.main.url(forResource: "Localization", withExtension: "json")
                ?? Bundle.module.url(forResource: "Localization", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let result = try? JSONDecoder().decode([String: [String]].self, from: data) else { return [:] }
        return result
    }()
    static let placeholders = try! NSRegularExpression(pattern: #"\{([0-9]+)\}"#)
}

func L(_ source: String, _ arguments: String...) -> String {
    let text = Localization.messages[source]?[Localization.language == "zh" ? 0 : 1] ?? source
    guard !arguments.isEmpty else { return text }
    let result = NSMutableString(string: text)
    let range = NSRange(location: 0, length: result.length)
    // Work backwards in the template; argument text is never interpreted as a placeholder.
    for match in Localization.placeholders.matches(in: text, range: range).reversed() {
        let index = Int((text as NSString).substring(with: match.range(at: 1)))!
        if arguments.indices.contains(index) { result.replaceCharacters(in: match.range, with: arguments[index]) }
    }
    return result as String
}
