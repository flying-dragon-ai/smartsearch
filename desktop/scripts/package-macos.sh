#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
app_directory="$1"; sparkle_tools="$2"; architecture="$3"; python_bin="$4"
update_key_file="${5:-}"; previous_release_directory="${6:-}"
signing_mode="${7:-${SMART_SEARCH_MACOS_SIGNING_MODE:-adhoc}}"
[[ "$signing_mode" == adhoc || "$signing_mode" == required ]] || exit 2
run_directory="$(dirname "$app_directory")"
version="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$app_directory/Contents/Info.plist")"
suffix="-$architecture"
verify_args=(--architecture "$architecture" --version "$version" --signing-mode "$signing_mode")
if [[ "$architecture" == universal ]]; then
  suffix=""
else
  verify_args+=(--sdk-version "$(xcrun --sdk macosx --show-sdk-version)")
fi

# Sign after final assembly, including the Universal UI and framework slices.
signing_result="$run_directory/signing.json"
if [[ "$signing_mode" == required ]]; then
  "$python_bin" "$repository_root/desktop/scripts/macos_signing.py" sign "$app_directory" --result "$signing_result"
else
  codesign --force --deep --sign - "$app_directory"
  printf '{"kind":"ad-hoc-test"}\n' > "$signing_result"
fi
codesign --verify --deep --strict --verbose=2 "$app_directory"
dmg="$run_directory/SmartSearch-v$version$suffix.dmg"
"${DMGBUILD:-dmgbuild}" -s "$repository_root/desktop/packaging/macos/dmg-settings.py" \
  -D "app=$app_directory" -D "assets=$repository_root/desktop/packaging/macos" "Smart Search" "$dmg"
"$python_bin" "$repository_root/desktop/scripts/verify_macos_dmg.py" "$dmg" \
  "${verify_args[@]}"

updates_directory=""
if [[ -n "$update_key_file" ]]; then
  updates_directory="$run_directory/updates"
  bash "$repository_root/desktop/scripts/package-sparkle.sh" "$app_directory" "$sparkle_tools" \
    "$updates_directory" "$update_key_file" "$architecture" "$previous_release_directory"
  cp "$dmg" "$updates_directory/"
  cp "$signing_result" "$updates_directory/macos-signing-$architecture.json"
  if [[ -d "$run_directory/cli" ]]; then cp "$run_directory/cli/"* "$updates_directory/"; fi
fi
"$python_bin" - "$run_directory/result.json" "$app_directory" "$dmg" "$sparkle_tools" "$updates_directory" "$architecture" "$signing_result" <<'PY'
import json, sys
from pathlib import Path
result, app, dmg, tools, updates, architecture, signing_result = sys.argv[1:]
signing = json.loads(Path(signing_result).read_text())
Path(result).write_text(json.dumps(dict(app=app, dmg=dmg, sparkle_tools=tools, updates_directory=updates,
    architecture=architecture, code_signing=signing['kind'], signing=signing, notarized=False), indent=2))
PY
echo "macOS package (signing=$signing_mode, not notarized): $dmg"
