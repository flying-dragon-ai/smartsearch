#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
sdk_path="$(xcrun --sdk macosx --show-sdk-path)"
sdk_version="$(xcrun --sdk macosx --show-sdk-version)"
minimum_os="$(plutil -extract LSMinimumSystemVersion raw "$repository_root/desktop/packaging/macos/Info.plist")"

if [[ "${sdk_version%%.*}" -lt 26 ]]; then
  echo "The native macOS interface requires Xcode with macOS SDK 26 or newer; selected SDK: $sdk_version" >&2
  exit 1
fi

# Use the actual SDK for both compilation and the linked-on SDK record. Some
# SwiftPM/toolchain combinations incorrectly record the deployment target as
# the SDK, leaving native controls in the system's older compatibility design.
swift build --package-path "$repository_root/desktop/macos" --configuration release \
  --sdk "$sdk_path" \
  -Xlinker -platform_version -Xlinker macos -Xlinker "$minimum_os" -Xlinker "$sdk_version" \
  "$@"
