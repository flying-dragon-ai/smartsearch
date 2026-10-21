#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash desktop/scripts/build-macos.sh --architecture arm64|x86_64 [--python PATH] [--output-root PATH] [--signing-mode adhoc|required] [--update-key-file PATH] [--update-public-key BASE64] [--previous-release-directory PATH] [--release-updates]

Builds a fresh .app and DMG. Local builds default to ad-hoc; use the with-signing task for a fixed certificate. Release updates require the maintainer's code-signing and Sparkle identities. The Python interpreter and host must
match the requested architecture because PyInstaller does not cross-compile.
EOF
}

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
architecture=""
python_command="${PYTHON:-python3}"
output_root="$repository_root/.desktop-artifacts"
update_key_file=""
update_public_key="${SMART_SEARCH_SPARKLE_PUBLIC_KEY:-}"
previous_release_directory=""
release_updates=false
test_package_id=""
test_feed_url=""
signing_mode="${SMART_SEARCH_MACOS_SIGNING_MODE:-adhoc}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --architecture)
      architecture="${2:-}"
      shift 2
      ;;
    --python)
      python_command="${2:-}"
      shift 2
      ;;
    --output-root)
      output_root="${2:-}"
      shift 2
      ;;
    --signing-mode) signing_mode="${2:-}"; shift 2 ;;
    --update-key-file) update_key_file="${2:-}"; shift 2 ;;
    --update-public-key) update_public_key="${2:-}"; shift 2 ;;
    --previous-release-directory) previous_release_directory="${2:-}"; shift 2 ;;
    --release-updates) release_updates=true; shift ;;
    --test-package-id) test_package_id="${2:-}"; shift 2 ;;
    --test-feed-url) test_feed_url="${2:-}"; shift 2 ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$architecture" != "arm64" && "$architecture" != "x86_64" ]]; then
  echo "--architecture must be arm64 or x86_64" >&2
  exit 2
fi
if [[ "$signing_mode" != adhoc && "$signing_mode" != required ]]; then
  echo '--signing-mode must be adhoc or required' >&2
  exit 2
fi
if $release_updates && [[ "$signing_mode" != required || "${SMART_SEARCH_MACOS_SIGNING_KIND:-}" != self-signed ]]; then
  echo 'Release updates require the maintainer-owned macOS signing certificate; test/ad-hoc fallback is forbidden.' >&2
  exit 1
fi
if $release_updates && [[ -z "$update_key_file" || -z "$update_public_key" || -n "$test_package_id" || -n "$test_feed_url" ]]; then
  echo 'Release updates require an explicit signing key and pinned public key, without a test identity.' >&2
  exit 1
fi
if [[ -n "$test_package_id" || -n "$test_feed_url" ]]; then
  [[ "$test_package_id" =~ ^com\.smartsearch\.test\.[a-z0-9.-]+$ && "$test_feed_url" == http://127.0.0.1:*/* ]] || exit 2
fi
if [[ -n "$update_key_file" ]]; then
  [[ -f "$update_key_file" && -n "$update_public_key" ]] || { echo 'Missing Sparkle key file or public key.' >&2; exit 1; }
fi
if [[ "$output_root" != /* ]]; then
  output_root="$repository_root/$output_root"
fi
if [[ "$python_command" == */* ]]; then
  python_bin="$python_command"
else
  python_bin="$(command -v "$python_command")"
fi
if [[ ! -x "$python_bin" ]]; then
  echo "Python executable is not available: $python_command" >&2
  exit 1
fi
if [[ "$signing_mode" == required ]]; then
  "$python_bin" "$repository_root/desktop/scripts/macos_signing.py" preflight
fi
if ! command -v swift >/dev/null 2>&1 || ! command -v hdiutil >/dev/null 2>&1; then
  echo "Swift and hdiutil are required on macOS to build the desktop test package." >&2
  exit 1
fi
if ! command -v "${DMGBUILD:-dmgbuild}" >/dev/null 2>&1; then
  echo "dmgbuild is required. Run mise install, then mise run desktop:macos:build." >&2
  exit 1
fi

normalize_architecture() {
  case "$1" in
    arm64|aarch64) printf 'arm64' ;;
    x86_64|amd64) printf 'x86_64' ;;
    *) printf '%s' "$1" ;;
  esac
}

python_arch="$(normalize_architecture "$("$python_bin" -c 'import platform; print(platform.machine())')")"
host_arch="$(normalize_architecture "$(uname -m)")"
if [[ "$python_arch" != "$architecture" || "$host_arch" != "$architecture" ]]; then
  echo "Requested $architecture, but host=$host_arch and Python=$python_arch. Build on a matching architecture runner or Mac." >&2
  exit 1
fi

mkdir -p "$output_root"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
run_directory="$output_root/macos-$architecture-$stamp-$$-$RANDOM"
if [[ -e "$run_directory" ]]; then
  echo "Refusing to reuse build directory: $run_directory" >&2
  exit 1
fi
mkdir "$run_directory"

sparkle_tools="$run_directory/sparkle-tools"
mkdir "$sparkle_tools"
curl --fail --location --proto '=https' --proto-redir '=https' --max-time 180 \
  'https://github.com/sparkle-project/Sparkle/releases/download/2.9.6/Sparkle-2.9.6.tar.xz' \
  --output "$run_directory/Sparkle-2.9.6.tar.xz"
printf '%s  %s\n' '52bf9e88cdd972fc0c81501377a880e90d47031bd8ca5462488f843e2609e192' "$run_directory/Sparkle-2.9.6.tar.xz" | shasum -a 256 --check
tar -xJf "$run_directory/Sparkle-2.9.6.tar.xz" -C "$sparkle_tools"

backend_manifest="$run_directory/backend.json"
"$python_bin" "$repository_root/desktop/scripts/build_backend.py" \
  --output-root "$run_directory" \
  --result-file "$backend_manifest" \
  --smoke
backend_directory="$("$python_bin" -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["bundle_directory"])' "$backend_manifest")"

macos_directory="$repository_root/desktop/macos"
if [[ ! -f "$macos_directory/Package.swift" ]]; then
  echo "SwiftPM package is not available: $macos_directory/Package.swift" >&2
  exit 1
fi
scratch_directory="$run_directory/swift-build"
bash "$repository_root/desktop/scripts/compile-macos.sh" --product SmartSearchDesktop --arch "$architecture" --scratch-path "$scratch_directory"
bin_directory="$(bash "$repository_root/desktop/scripts/compile-macos.sh" --arch "$architecture" --scratch-path "$scratch_directory" --show-bin-path)"
desktop_binary="$bin_directory/SmartSearchDesktop"
if [[ ! -f "$desktop_binary" ]]; then
  echo "SwiftPM did not create the expected desktop executable: $desktop_binary" >&2
  exit 1
fi

version="$("$python_bin" - "$repository_root/pyproject.toml" <<'PY'
import re
import sys
from pathlib import Path

match = re.search(r'^\s*version\s*=\s*"([^"]+)"', Path(sys.argv[1]).read_text(encoding="utf-8"), re.MULTILINE)
if not match:
    raise SystemExit("project version is missing from pyproject.toml")
print(match.group(1))
PY
)"
app_directory="$run_directory/Smart Search.app"
mkdir -p "$app_directory/Contents/MacOS" "$app_directory/Contents/Resources" "$app_directory/Contents/Frameworks"
cp "$desktop_binary" "$app_directory/Contents/MacOS/SmartSearchDesktop"
cp "$repository_root/desktop/packaging/macos/Info.plist" "$app_directory/Contents/Info.plist"
icon_directory="$run_directory/icon"
bash "$repository_root/desktop/scripts/compile-macos-icon.sh" "$icon_directory"
cp "$icon_directory/Assets.car" "$icon_directory/SmartSearch.icns" "$app_directory/Contents/Resources/"
cp "$repository_root/assets/branding/smart-search.png" "$app_directory/Contents/Resources/smart-search.png"
cp "$repository_root/assets/branding/source.png" "$app_directory/Contents/Resources/mascot.png"
cp "$repository_root/src/smart_search/assets/i18n/messages.json" "$app_directory/Contents/Resources/Localization.json"
cmp "$repository_root/src/smart_search/assets/i18n/messages.json" "$app_directory/Contents/Resources/Localization.json"
plutil -replace CFBundleShortVersionString -string "$version" "$app_directory/Contents/Info.plist"
plutil -replace CFBundleVersion -string "$version" "$app_directory/Contents/Info.plist"
chmod +x "$app_directory/Contents/MacOS/SmartSearchDesktop"
"$python_bin" "$repository_root/desktop/scripts/package_cli.py" --bundle "$backend_directory" \
  --output "$run_directory/cli" --platform macos --architecture "$architecture" --version "$version"
ditto "$sparkle_tools/Sparkle.framework" "$app_directory/Contents/Frameworks/Sparkle.framework"
plutil -insert SUEnableAutomaticChecks -bool true "$app_directory/Contents/Info.plist"
plutil -insert SUAutomaticallyUpdate -bool false "$app_directory/Contents/Info.plist"
plutil -insert SUSendProfileInfo -bool false "$app_directory/Contents/Info.plist"
plutil -insert SUVerifyUpdateBeforeExtraction -bool true "$app_directory/Contents/Info.plist"
plutil -insert SURequireSignedFeed -bool true "$app_directory/Contents/Info.plist"
feed_url="https://github.com/konbakuyomu/smartsearch/releases/latest/download/appcast-macos-$architecture.xml"
if [[ -n "$test_package_id" ]]; then
  plutil -replace CFBundleIdentifier -string "$test_package_id" "$app_directory/Contents/Info.plist"
  plutil -insert SSUpdateTestBuild -bool true "$app_directory/Contents/Info.plist"
  plutil -insert NSAppTransportSecurity -json '{"NSAllowsLocalNetworking":true}' "$app_directory/Contents/Info.plist"
  feed_url="$test_feed_url"
fi
plutil -insert SUFeedURL -string "$feed_url" "$app_directory/Contents/Info.plist"
if [[ -n "$update_public_key" ]]; then
  plutil -insert SUPublicEDKey -string "$update_public_key" "$app_directory/Contents/Info.plist"
fi
plutil -lint "$app_directory/Contents/Info.plist"
if [[ -e "$app_directory/Contents/Resources/backend" ]]; then
  echo "The App must not contain a CLI backend." >&2
  exit 1
fi

bash "$repository_root/desktop/scripts/package-macos.sh" "$app_directory" "$sparkle_tools" "$architecture" \
  "$python_bin" "$update_key_file" "$previous_release_directory" "$signing_mode"
