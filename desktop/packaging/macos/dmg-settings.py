"""Finder layout, shared by both macOS architectures (loaded by dmgbuild)."""

from pathlib import Path

assets = Path(defines["assets"])
format = "UDZO"
files = [defines["app"]]
symlinks = {"Applications": "/Applications"}
icon = str(assets / "SmartSearch.icns")
# dmgbuild combines the PNG and its @2x sibling into a Retina TIFF.
background = str(assets / "dmg-background.png")
# Match the Codex Tweaks / DJOneHub DMG layout.
window_rect = ((200, 150), (660, 440))
icon_size = 112
text_size = 16
icon_locations = {
    "Smart Search.app": (180, 228),
    "Applications": (480, 228),
    ".background.tiff": (330, 1000),
    ".VolumeIcon.icns": (330, 1000),
}
hide = [".background.tiff", ".VolumeIcon.icns"]
# Do not hide the .app extension with SetFile: it adds FinderInfo to the signed
# bundle and makes codesign --strict reject the distributed copy.
default_view = "icon-view"
show_toolbar = False
show_status_bar = False
show_pathbar = False
show_tab_view = False
show_sidebar = False
arrange_by = None
