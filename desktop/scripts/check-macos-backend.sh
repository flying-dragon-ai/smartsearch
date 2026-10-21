#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
backend="${1:?Pass the packaged backend executable path}"
iterations="${2:-12}"
mkdir -p "$repository_root/.desktop-artifacts"
run_directory="$(mktemp -d "$repository_root/.desktop-artifacts/macos-backend-check.XXXXXX")"
sources="$repository_root/desktop/macos/Sources/SmartSearchDesktop"

# Use release optimization: the old unordered reader failed intermittently here.
swiftc -O -parse-as-library \
  "$sources/BackendClient.swift" "$sources/Models.swift" "$sources/Localization.swift" \
  "$repository_root/desktop/checks/MacBackendLifecycle.swift" \
  -o "$run_directory/backend-check"
"$run_directory/backend-check" "$backend" "$run_directory" "$iterations"
