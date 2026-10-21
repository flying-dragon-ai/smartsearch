#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
assets="$repository_root/desktop/packaging/macos"
temporary_directory="$(mktemp -d -t smartsearch-dmg-background)"
retina_svg="$temporary_directory/background.svg"
trap 'rm -f "$retina_svg"; rmdir "$temporary_directory"' EXIT

sips -s format png "$assets/dmg-background.svg" --out "$assets/dmg-background.png"
# Change the SVG viewport before rasterizing, not the size of a bitmap.
sed 's/width="660" height="440" viewBox/width="1320" height="880" viewBox/' \
  "$assets/dmg-background.svg" > "$retina_svg"
sips -s format png "$retina_svg" --out "$assets/dmg-background@2x.png"
