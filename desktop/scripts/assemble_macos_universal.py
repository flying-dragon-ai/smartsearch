#!/usr/bin/env python3
"""Combine matching native UI apps into a universal App."""
from __future__ import annotations

import argparse
from pathlib import Path
import plistlib
import subprocess

from verify_macos_dmg import verify_app_architectures


def assemble(arm64: Path, intel: Path, output: Path) -> None:
    arm64, intel, output = arm64.resolve(), intel.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Universal output must be a fresh app directory")
    apps = {"arm64": arm64, "x86_64": intel}
    infos = {}
    for architecture, app in apps.items():
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
        info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
        verify_app_architectures(app, architecture)
        infos[architecture] = info
    for key in ("CFBundleIdentifier", "CFBundleVersion", "CFBundleShortVersionString",
                "LSMinimumSystemVersion", "SUPublicEDKey", "SUEnableAutomaticChecks", "SSUpdateTestBuild"):
        if infos["arm64"].get(key) != infos["x86_64"].get(key):
            raise ValueError(f"Native apps disagree on {key}")
    # Compiled icon catalogs can differ between runners; compare shared source assets.
    for name in ("Localization.json", "smart-search.png", "mascot.png"):
        relative = Path("Contents/Resources") / name
        if (arm64 / relative).read_bytes() != (intel / relative).read_bytes():
            raise ValueError(f"Native apps have different shared resources: {name}")

    subprocess.run(["ditto", str(arm64), str(output)], check=True)
    executable = "Contents/MacOS/SmartSearchDesktop"
    subprocess.run(["xcrun", "lipo", "-create", str(arm64 / executable), str(intel / executable),
                    "-output", str(output / executable)], check=True)
    info = infos["arm64"]
    info["SUFeedURL"] = "https://github.com/konbakuyomu/smartsearch/releases/latest/download/appcast-macos-universal.xml"
    (output / "Contents/Info.plist").write_bytes(plistlib.dumps(info))
    verify_app_architectures(output, "universal")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm64-app", type=Path, required=True)
    parser.add_argument("--x86_64-app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assemble(args.arm64_app, args.x86_64_app, args.output)
