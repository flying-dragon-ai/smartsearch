#!/usr/bin/env bash
set -euo pipefail
repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
mkdir -p "$repository_root/.desktop-artifacts"
run_directory="$(mktemp -d "$repository_root/.desktop-artifacts/cli-management-check.XXXXXX")"
sources="$repository_root/desktop/macos/Sources/SmartSearchDesktop"
"$repository_root/.venv/bin/python" "$repository_root/desktop/scripts/create_npm_fixture.py" "$run_directory" "$(mise which node)"
swiftc -O -parse-as-library "$sources/CLIInstallationManager.swift" "$sources/Localization.swift" \
  "$repository_root/desktop/checks/MacCLIInstallation.swift" -o "$run_directory/check"
"$run_directory/check" "$run_directory"
