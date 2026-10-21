# Desktop beta feedback validation — 2026-09-20

The beta feedback repairs activity metadata and Windows result presentation within the existing A3/A5/A6 scope. The earlier integration and update evidence remains in [the integration report](desktop-contributions-updates-validation.md). This report does not approve a stable 0.1.20 release.

## Changes and boundaries

- Windows activity refresh previously cleared and recreated every expander every two seconds, replaying its opening animation. Rows now retain their controls by run ID, update their text/actions in place, and keep start-time ordering instead of moving with heartbeat timestamps.
- The result body, optional source disclosure, copy/export actions and raw JSON now share one result card. Source titles wrap, show their host and retain the full URL as a tooltip. The original Markdown and export payload are preserved.
- A provider without a model no longer displays a false “model missing” caption. Main-provider connection probes record their configured request model in worker results, persisted activity and in-memory activity fallback. Final search summaries restore the primary provider/model while supplemental phase events retain their own metadata.
- Firecrawl remains a presence-only check. Both native clients label its action “检查配置”; metadata and doctor output explicitly say the credential/API has not been verified. Finishing that check is distinct from a successful API probe. No new billable Firecrawl probe was added.

## Checks performed

- Related Python suites: 254 passed (desktop runtime, provider dispatcher, UI API, UI metadata and service). New worker tests cover xAI, OpenAI-compatible and Firecrawl, model applicability, in-memory fallback and unchanged health records; another regression separates final primary metadata from supplemental phase events.
- Windows x64 build: zero warnings/errors, `.desktop-artifacts/feedback-windows-build.log`. The native backend lifecycle check also passes the added caption assertions and real stop/reconnect sequence.
- A separate `SmartSearch.FeedbackPreview` build uses an isolated synthetic profile/backend. The supplied long Markdown is rendering data only; its news claims were not fact-checked and no result URLs were opened.
- The running activity stayed expanded across snapshots 26 seconds apart, with unchanged accessibility row/control IDs and unchanged card positions while elapsed time advanced from 06:21 to 06:47. Evidence: `.desktop-artifacts/feedback-ui-evidence/activity-before.{png,txt}` and `activity-after.{png,txt}`. The backend request log records two-second activity polling.
- Firecrawl activity shows only its provider, without a missing-model warning; its provider panel shows “检查配置” and “仅检查已填写”. The long result and all ten sources are present in the accessibility tree, with a separate “来源链接（10）” disclosure inside the result card. The body wraps at normal and maximized window widths.
- The final screenshots did not cover the bottom of the fully expanded source list. That specific visual boundary, this repair's narrow/light-theme combinations, clipboard/export dialogs and macOS native interaction remain unverified. Do not describe them as passed based only on source or accessibility inspection.
- The isolated preview was closed. The desktop preference file matches its pre-test SHA256 exactly; the fixture used no real provider credentials and did not rewrite the real service configuration.

Full Runtime regression, fresh independent verification and any delivered installer are recorded separately when completed. Previous CI results apply only to their recorded source commit; this repair needs its own build evidence.
