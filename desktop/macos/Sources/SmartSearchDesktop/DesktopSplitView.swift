import AppKit
import SwiftUI

/// Keeps pane geometry independent of the selected SwiftUI content.
struct DesktopSplitView<Leading: View, Detail: View>: View {
    let identifier: String
    let leadingWidths: ClosedRange<CGFloat>
    let initialLeadingWidth: CGFloat
    let detailMinimumWidth: CGFloat
    let leading: Leading
    let detail: Detail

    init(_ identifier: String, leadingWidths: ClosedRange<CGFloat> = 184...280,
         initialLeadingWidth: CGFloat = 220, detailMinimumWidth: CGFloat = 400,
         @ViewBuilder leading: () -> Leading, @ViewBuilder detail: () -> Detail) {
        self.identifier = identifier
        self.leadingWidths = leadingWidths
        self.initialLeadingWidth = initialLeadingWidth
        self.detailMinimumWidth = detailMinimumWidth
        self.leading = leading()
        self.detail = detail()
    }

    var body: some View {
        NativeSplitView(identifier: identifier, leadingWidths: leadingWidths,
                        initialLeadingWidth: initialLeadingWidth, detailMinimumWidth: detailMinimumWidth,
                        leading: leading, detail: detail)
            .frame(minWidth: leadingWidths.lowerBound + detailMinimumWidth + 1,
                   maxWidth: .infinity, maxHeight: .infinity)
            .background(DesktopAppearance.contentBackground)
    }
}

private struct NativeSplitView<Leading: View, Detail: View>: NSViewControllerRepresentable {
    let identifier: String
    let leadingWidths: ClosedRange<CGFloat>
    let initialLeadingWidth: CGFloat
    let detailMinimumWidth: CGFloat
    let leading: Leading
    let detail: Detail

    func makeNSViewController(context: Context) -> StableSplitViewController {
        StableSplitViewController(identifier: identifier, leadingWidths: leadingWidths,
                                  initialLeadingWidth: initialLeadingWidth, detailMinimumWidth: detailMinimumWidth,
                                  leading: hosted(leading, context: context), detail: hosted(detail, context: context))
    }

    func updateNSViewController(_ controller: StableSplitViewController, context: Context) {
        controller.update(leading: hosted(leading, context: context), detail: hosted(detail, context: context))
    }

    private func hosted<Content: View>(_ content: Content, context: Context) -> AnyView {
        // Separate hosting controllers do not inherit the surrounding SwiftUI environment.
        AnyView(content
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .background(DesktopAppearance.contentBackground)
            .environment(\.locale, context.environment.locale)
            .environment(\.colorScheme, context.environment.colorScheme)
            .groupBoxStyle(DesktopGroupBoxStyle())
            .toggleStyle(.switch)
            .disclosureGroupStyle(WholeRowDisclosureStyle())
            .textFieldStyle(.roundedBorder))
    }
}

private final class StableSplitViewController: NSSplitViewController {
    private let leadingHost: NSHostingController<AnyView>
    private let detailHost: NSHostingController<AnyView>
    private let storageKey: String
    private let leadingWidths: ClosedRange<CGFloat>
    private let detailMinimumWidth: CGFloat
    private var preferredLeadingWidth: CGFloat
    private var containerWidth: CGFloat = 0
    private var initialPositionApplied = false
    private var applyingPosition = false

    init(identifier: String, leadingWidths: ClosedRange<CGFloat>, initialLeadingWidth: CGFloat,
         detailMinimumWidth: CGFloat, leading: AnyView, detail: AnyView) {
        self.storageKey = "SmartSearchDesktop.splitWidth.\(identifier)"
        self.leadingWidths = leadingWidths
        self.detailMinimumWidth = detailMinimumWidth
        let savedWidth = UserDefaults.standard.double(forKey: storageKey)
        self.preferredLeadingWidth = savedWidth.isFinite && savedWidth > 0 ? savedWidth : initialLeadingWidth
        self.leadingHost = NSHostingController(rootView: leading)
        self.detailHost = NSHostingController(rootView: detail)
        super.init(nibName: nil, bundle: nil)

        // The split items own the constraints; a long field, empty state or result must
        // never change a host's intrinsic size and move the divider or resize the window.
        leadingHost.sizingOptions = []
        detailHost.sizingOptions = []
        leadingHost.view.translatesAutoresizingMaskIntoConstraints = false
        detailHost.view.translatesAutoresizingMaskIntoConstraints = false
        splitView.isVertical = true
        splitView.dividerStyle = .thin

        let leadingItem = NSSplitViewItem(viewController: leadingHost)
        leadingItem.minimumThickness = leadingWidths.lowerBound
        leadingItem.maximumThickness = leadingWidths.upperBound
        // Stay below .dragThatCannotResizeWindow (490) so native divider dragging wins.
        leadingItem.holdingPriority = NSLayoutConstraint.Priority(251)
        leadingItem.canCollapse = false
        addSplitViewItem(leadingItem)

        let detailItem = NSSplitViewItem(viewController: detailHost)
        detailItem.minimumThickness = detailMinimumWidth
        detailItem.holdingPriority = .defaultLow
        detailItem.canCollapse = false
        addSplitViewItem(detailItem)

        NotificationCenter.default.addObserver(self, selector: #selector(dividerDidMove),
                                               name: NSSplitView.didResizeSubviewsNotification, object: splitView)
    }

    required init?(coder: NSCoder) { fatalError("Use init(identifier:leadingWidths:initialLeadingWidth:detailMinimumWidth:leading:detail:)") }

    deinit { NotificationCenter.default.removeObserver(self) }

    func update(leading: AnyView, detail: AnyView) {
        leadingHost.rootView = leading
        detailHost.rootView = detail
    }

    override func viewDidLayout() {
        super.viewDidLayout()
        let width = splitView.bounds.width
        guard !applyingPosition, width >= leadingWidths.lowerBound + detailMinimumWidth + splitView.dividerThickness,
              !initialPositionApplied || abs(width - containerWidth) > 0.5 else { return }
        containerWidth = width
        let position = fittingLeadingWidth
        applyingPosition = true
        splitView.setPosition(position, ofDividerAt: 0)
        initialPositionApplied = abs(leadingHost.view.frame.width - position) < 0.5
        applyingPosition = false
    }

    @objc private func dividerDidMove(_ notification: Notification) {
        // Ignore the controller's initial placement and intermediate window resizing.
        guard !applyingPosition, initialPositionApplied,
              abs(splitView.bounds.width - containerWidth) < 0.5 else { return }
        let width = leadingHost.view.frame.width
        // A narrow window can temporarily clamp the pane; retain the wider user preference.
        guard width.isFinite, leadingWidths.contains(width), abs(width - fittingLeadingWidth) > 0.5 else { return }
        preferredLeadingWidth = width
        UserDefaults.standard.set(Double(width), forKey: storageKey)
    }

    private var fittingLeadingWidth: CGFloat {
        let maximum = min(leadingWidths.upperBound, containerWidth - detailMinimumWidth - splitView.dividerThickness)
        return min(max(preferredLeadingWidth, leadingWidths.lowerBound), maximum)
    }
}
