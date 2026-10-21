#!/usr/bin/env bash
# Builds out/film/smart-search-promo.mp4 (see tools/build.sh).
#   bash film/build.sh            full 1920x1080 @ 60 fps
#   bash film/build.sh draft      960x540 @ 30 fps
exec bash "$(dirname "$0")/../tools/build.sh" film smart-search-promo "$@"
