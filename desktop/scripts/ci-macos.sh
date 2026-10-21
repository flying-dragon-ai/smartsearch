#!/usr/bin/env bash
set -euo pipefail

# Called inside macos_signing.py run so the same temporary keychain covers the
# packaged App, copied-install verification and actual Sparkle update checks.
shopt -s nullglob
build_task=desktop:macos:build
if [[ "${1:-}" == --universal ]]; then build_task=desktop:macos:universal; shift; fi
before=(.desktop-artifacts/macos-*/result.json)
mise run "$build_task" "$@"
builds=()
for result in .desktop-artifacts/macos-*/result.json; do
  existing=false
  for previous in ${before[@]+"${before[@]}"}; do
    if [[ "$result" == "$previous" ]]; then existing=true; break; fi
  done
  if ! $existing; then builds+=("$result"); fi
done
if [[ -z "${builds[*]-}" ]] || [[ ${#builds[@]} -ne 1 ]]; then
  echo 'Expected exactly one fresh macOS build for CI.' >&2
  exit 1
fi
mise run python desktop/scripts/test_sparkle_updates.py "${builds[0]}"
