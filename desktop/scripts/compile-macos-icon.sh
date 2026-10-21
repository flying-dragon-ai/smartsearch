#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
output_directory="${1:-$repository_root/.desktop-artifacts/icons/macos}"
minimum_os="$(plutil -extract LSMinimumSystemVersion raw "$repository_root/desktop/packaging/macos/Info.plist")"

mkdir -p "$output_directory"
xcrun actool "$repository_root/desktop/packaging/macos/SmartSearch.icon" \
  --compile "$output_directory" \
  --platform macosx \
  --minimum-deployment-target "$minimum_os" \
  --app-icon SmartSearch \
  --output-partial-info-plist "$output_directory/icon-info.plist" \
  --output-format human-readable-text --warnings --errors

test -s "$output_directory/Assets.car"
test -s "$output_directory/SmartSearch.icns"
