#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
python_bin="${PYTHON:-python3}"
arm64_app=""; intel_app=""; sparkle_tools=""; update_key_file=""; previous=""
signing_mode="${SMART_SEARCH_MACOS_SIGNING_MODE:-adhoc}"
release_updates=false
output_root="$repository_root/.desktop-artifacts"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) python_bin="$2"; shift 2 ;;
    --arm64-app) arm64_app="$2"; shift 2 ;;
    --x86_64-app) intel_app="$2"; shift 2 ;;
    --sparkle-tools) sparkle_tools="$2"; shift 2 ;;
    --output-root) output_root="$2"; shift 2 ;;
    --signing-mode) signing_mode="$2"; shift 2 ;;
    --release-updates) release_updates=true; shift ;;
    --update-key-file) update_key_file="$2"; shift 2 ;;
    --previous-release-directory) previous="$2"; shift 2 ;;
    *) echo "Unknown universal packaging argument: $1" >&2; exit 2 ;;
  esac
done
[[ "$signing_mode" == adhoc || "$signing_mode" == required ]] || exit 2
if $release_updates && [[ "$signing_mode" != required || "${SMART_SEARCH_MACOS_SIGNING_KIND:-}" != self-signed || -z "$update_key_file" ]]; then
  echo 'Release updates require the maintainer code-signing identity and Sparkle key.' >&2; exit 1
fi
if [[ "$signing_mode" == required ]]; then
  "$python_bin" "$repository_root/desktop/scripts/macos_signing.py" preflight
fi
[[ -d "$arm64_app" && -d "$intel_app" && -d "$sparkle_tools" ]] || {
  echo 'Pass --arm64-app, --x86_64-app and --sparkle-tools from matching native builds.' >&2; exit 2;
}
if [[ "$output_root" != /* ]]; then output_root="$repository_root/$output_root"; fi
sparkle_tools="$(cd "$sparkle_tools" && pwd -P)"
mkdir -p "$output_root"
run_directory="$(mktemp -d "$output_root/macos-universal-XXXXXX")"
app="$run_directory/Smart Search.app"
"$python_bin" "$repository_root/desktop/scripts/assemble_macos_universal.py" \
  --arm64-app "$arm64_app" --x86_64-app "$intel_app" --output "$app"
bash "$repository_root/desktop/scripts/package-macos.sh" "$app" "$sparkle_tools" universal "$python_bin" "$update_key_file" "$previous" "$signing_mode"
