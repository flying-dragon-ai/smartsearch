[Guide](../README.md) · [简体中文](../zh-CN/troubleshooting.md)

# Troubleshooting

## Troubleshooting

If `doctor` reports `config_error`:

```powershell
smart-search setup
smart-search config list --format json
smart-search doctor --format markdown
```

If OpenAI-compatible `search` hangs or times out after `doctor` passes:

```powershell
smart-search doctor --format markdown
smart-search diagnose openai-compatible --format markdown
```

The diagnose report masks the API key and says whether the problem is missing config, the upstream/relay hanging on the real Smart Search prompt, or a stream/no-stream compatibility mismatch.

If search is slow:

- reduce `--extra-sources`;
- split broad questions into smaller queries;
- use `exa-search` or `zhipu-search` for source discovery, then `fetch` key pages.

If installed CLI health is uncertain:

```powershell
smart-search --help
smart-search --version
smart-search regression
smart-search smoke --mock --format json
```

On Windows npm/mise installs, verify non-ASCII JSON piping:

```powershell
smart-search deep "深度搜索一下最近的比特币行情" --format json | ConvertFrom-Json
```

## Using Smart Search in WSL or on Linux

The App is available for Windows and macOS only. Install and configure the CLI directly in WSL or Linux (glibc 2.35+ is required, for example Ubuntu 22.04 or later); the Windows App can also connect to a CLI inside WSL, and install or update it in a distribution that has Node.js, see [Windows and WSL](app.md#windows-and-wsl):

```bash
npm install -g @konbakuyomu/smart-search@latest
smart-search setup                                # or open the web config page with smart-search ui
smart-search skills update --targets claude,codex
```

WSL keeps its own configuration (`~/.config/smart-search`) and Skills (for example `~/.claude/skills`), separate from the App on Windows. Agents running in WSL read only the WSL copy, so set up keys and Skills inside WSL as well; to manage them from the Windows App, select the WSL installation in **Environment details…** first.

In WSL, `smart-search ui` opens the Windows default browser through `wslview` or `explorer.exe`, or through `BROWSER` when it is set. WSL's default NAT networking forwards `127.0.0.1` to Windows. With `networkingMode=mirrored` in `.wslconfig`, the Hyper-V firewall blocks connections from Windows into WSL by default and the page never loads. In that case, fix the port in WSL:

```bash
smart-search ui --port 8765
```

Then allow that port from an administrator PowerShell, as described in [Microsoft's documentation](https://learn.microsoft.com/windows/wsl/networking#mirrored-mode-networking):

```powershell
New-NetFirewallHyperVRule -Name SmartSearchUI -DisplayName "Smart Search UI" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 8765
```

## The CLI package updated but its runtime is not ready

The new npm CLI needs neither lifecycle scripts nor system Python. If its native package is missing, run `npm install -g @konbakuyomu/smart-search@latest --include=optional` with the same npm, then detect again; do not use `--omit=optional`. A manual npm path needs its matching Node.js and a writable global prefix. Published npm 0.1.24 requires updating after the new binary release is available.

## App update failed or is unavailable

Retry the App check in Settings after restoring the network. A downloaded update still needs installation and restart. Finish App tasks, protected writes and unsaved drafts before proceeding. Windows development folders and old Inno installations must first use the new full installer; macOS test builds without an update key cannot update. Use only the official release matching your architecture. Signature or integrity failures must not be bypassed; keep using the installed version and report the error. App updates do not repair or upgrade the separate CLI/Skills automatically.

## macOS says the app is damaged or the developer cannot be verified

Download from this project's release page and check the DMG against that release's `SHA256SUMS.txt`. Open the DMG, drag **Smart Search** to **Applications**, then launch it from Applications. These are still unnotarized test packages.

“Damaged” does not necessarily mean a failed download. Before the packaging fix, v0.1.22 did not re-sign the assembled app, so verification reports `code has no resources but signature indicates they must be present`. Check the installed copy:

```bash
codesign --verify --deep --strict --verbose=2 "/Applications/Smart Search.app"
```

If verification fails, use a new build containing the packaging fix. Do not just remove quarantine to hide an invalid signature. A matching SHA-256 only proves that the download matches the published file.

If verification passes and macOS says it cannot verify the developer or check the app, follow [Apple's instructions](https://support.apple.com/en-us/102445):

1. Attempt to open **Smart Search** from Applications once.
2. Open **Apple menu → System Settings → Privacy & Security**, then scroll to Security.
3. Click **Open Anyway** beside the Smart Search message and authenticate if requested.
4. Click **Open** in the confirmation dialog. Future launches can open the app directly.

If Open Anyway is missing, attempt another launch before returning to Settings; organization-managed devices may restrict this option. If macOS says the app will damage your computer or detects malicious content, stop opening it and report the warning to the project.

If this unnotarized test build still shows “damaged”, only after checking its official source, checksum and signature and deciding to trust it, remove the download quarantine flag from this app and reopen it:

```bash
xattr -dr com.apple.quarantine "/Applications/Smart Search.app"
```

This targets only this app; do not disable Gatekeeper globally. Ad-hoc signing does not verify the publisher's identity or constitute Apple notarization.

## Interface language

Set the App language in Settings & about, and the independent CLI language with `smart-search config set SMART_SEARCH_LANGUAGE en`. If the CLI still uses another language, check a per-call `--lang` and the `SMART_SEARCH_LANGUAGE` environment override. `auto` follows the CLI locale, which can differ from the GUI session. Use `smart-search --lang en --help` to test without changing settings. Unreadable preferences fall back with a warning; repair that configuration file without deleting provider keys. Original page text and third-party logs do not change language.

## AI integration is still pending

Use Update Skills to check the stable source and select Agents with changed files; a software version change alone does not require Skill sync. An unready CLI does not block content sync, but prepare it under Shared independent CLI environment before making calls. If detection fails in Settings, read the specific reason, select Refresh installed versions, then check for updates. Matching files do not prove the Agent loaded the Skill. Reopen the session or use Gemini `/skills reload`, then verify the actual CLI version. Changed content is backed up and the result shows its recovery path. See [App setup](app.md).
