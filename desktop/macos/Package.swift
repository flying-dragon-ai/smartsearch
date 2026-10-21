// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "SmartSearchDesktop",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "SmartSearchDesktop", targets: ["SmartSearchDesktop"]),
    ],
    dependencies: [
        .package(url: "https://github.com/sparkle-project/Sparkle", exact: "2.9.6"),
    ],
    targets: [
        .executableTarget(name: "SmartSearchDesktop", dependencies: [.product(name: "Sparkle", package: "Sparkle")],
                          resources: [.copy("Localization.json")],
                          linkerSettings: [.unsafeFlags(["-Xlinker", "-rpath", "-Xlinker", "@executable_path/../Frameworks"])]),
        .testTarget(name: "SmartSearchDesktopTests", dependencies: ["SmartSearchDesktop"]),
    ]
)
