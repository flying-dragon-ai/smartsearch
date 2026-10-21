import AppKit
import SwiftUI

enum AppearancePreference: String, CaseIterable, Identifiable {
    case system = "auto"
    case light
    case dark

    static let defaultsKey = "SmartSearchDesktop.appearance"
    var id: String { rawValue }

    var title: String {
        switch self {
        case .system: return L("跟随系统")
        case .light: return L("浅色")
        case .dark: return L("深色")
        }
    }

    var colorScheme: ColorScheme? {
        switch self {
        case .system: return nil
        case .light: return .light
        case .dark: return .dark
        }
    }

    @MainActor
    func applyToApplication() {
        switch self {
        case .system: NSApp.appearance = nil
        case .light: NSApp.appearance = NSAppearance(named: .aqua)
        case .dark: NSApp.appearance = NSAppearance(named: .darkAqua)
        }
    }
}
