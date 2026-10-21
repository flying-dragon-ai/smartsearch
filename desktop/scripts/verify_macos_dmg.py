#!/usr/bin/env python3
"""Mount the actual DMG read-only and verify the copied app, then unmount it."""

from __future__ import annotations

import argparse
import os
import plistlib
import re
import subprocess
import tempfile
from pathlib import Path

from macos_signing import verify_app

MACHO_MAGIC = {b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",
               b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"}


def verify_binary_architectures(path: Path, architectures: tuple[str, ...]) -> None:
    actual = subprocess.check_output(["xcrun", "lipo", "-archs", str(path)], text=True).split()
    if not set(architectures).issubset(actual):
        raise RuntimeError(f"{path} requires {architectures}, found {actual}")


def verify_macho_tree(directory: Path, architectures: tuple[str, ...]) -> None:
    seen = set()
    for path in directory.rglob("*"):
        resolved = path.resolve()
        if not path.is_file() or resolved in seen:
            continue
        seen.add(resolved)
        with path.open("rb") as stream:
            is_macho = stream.read(4) in MACHO_MAGIC
        if is_macho:
            verify_binary_architectures(path, architectures)


def verify_app_architectures(app: Path, architecture: str, expected_sdk: str | None = None) -> None:
    architectures = ("arm64", "x86_64") if architecture == "universal" else (architecture,)
    desktop = app / "Contents/MacOS/SmartSearchDesktop"
    backend = app / "Contents/Resources/backend"
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    if backend.exists():
        raise RuntimeError("The native App must not embed a CLI or Python runtime")
    verify_binary_architectures(desktop, architectures)
    for arch in architectures:
        verify_frontend_sdk(desktop, arch, info["LSMinimumSystemVersion"], expected_sdk)
    verify_macho_tree(app / "Contents/Frameworks", architectures)


def verify_frontend_sdk(executable: Path, architecture: str, minimum_os: str, expected_sdk: str | None = None) -> None:
    """Check the real Mach-O linked-on SDK, not the compiler or plist version."""
    output = subprocess.run(
        ["xcrun", "vtool", "-arch", architecture, "-show-build", str(executable)],
        check=True, capture_output=True, text=True,
    ).stdout
    versions = dict(re.findall(r"^\s*(minos|sdk)\s+(\d+(?:\.\d+)*)\s*$", output, re.MULTILINE))

    def version(value: str) -> tuple[int, ...]:
        return (tuple(int(part) for part in value.split(".")) + (0, 0))[:3]

    if "sdk" not in versions or version(versions["sdk"]) < (26, 0, 0):
        raise RuntimeError(f"Frontend linked-on SDK is {versions.get('sdk', 'missing')}; SDK 26+ is required for the new native design")
    if expected_sdk is not None and version(versions["sdk"]) != version(expected_sdk):
        raise RuntimeError(f"Frontend records SDK {versions['sdk']} but was built with SDK {expected_sdk}")
    if "minos" not in versions or version(versions["minos"]) != version(minimum_os):
        raise RuntimeError(f"Frontend deployment target differs from Info.plist minimum {minimum_os}")
    print(f"Frontend verified: linked-on SDK {versions['sdk']}, minimum macOS {versions['minos']}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dmg", type=Path)
    parser.add_argument("--architecture", required=True, choices=("arm64", "x86_64", "universal"))
    parser.add_argument("--runtime-architecture", choices=("arm64", "x86_64"),
                        help="Legacy argument retained for build-script compatibility; the App contains no CLI")
    parser.add_argument("--version", required=True)
    parser.add_argument("--sdk-version", help="Expected SDK used by the build toolchain")
    parser.add_argument("--signing-mode", choices=("adhoc", "required"), default="adhoc")
    parser.add_argument("--certificate-sha256", default=os.environ.get("SMART_SEARCH_MACOS_CERT_SHA256", ""))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="smartsearch-dmg-") as directory:
        root = Path(directory)
        mount = root / "volume"
        mount.mkdir()
        subprocess.run(
            ["hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint", str(mount), str(args.dmg.resolve())],
            check=True,
        )
        try:
            app = mount / "Smart Search.app"
            subprocess.run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app)], check=True)
            if args.signing_mode == "required":
                verify_app(app, args.certificate_sha256)
            info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
            if info["CFBundleShortVersionString"] != args.version or info["CFBundleVersion"] != args.version:
                raise RuntimeError("The packaged app version differs from the build source")
            if not (mount / "Applications").is_symlink() or os.readlink(mount / "Applications") != "/Applications":
                raise RuntimeError("The DMG is missing its Applications installation link")
            if not (mount / ".DS_Store").is_file() or not (mount / ".background.tiff").is_file():
                raise RuntimeError("The DMG is missing its Finder layout or Retina background")
            verify_app_architectures(app, args.architecture, args.sdk_version)
            # Copy exactly what a Finder install copies, including resource seals.
            installed = root / "Applications/Smart Search.app"
            subprocess.run(["ditto", str(app), str(installed)], check=True)
            subprocess.run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(installed)], check=True)
            if args.signing_mode == "required":
                verify_app(installed, args.certificate_sha256)
            print("DMG verified: signature, version, architecture, frontend SDK, install layout and absence of bundled CLI.")
            print("Local/self-signed code identities do not establish Developer ID trust or Apple notarization.")
        finally:
            subprocess.run(["hdiutil", "detach", str(mount)], check=True)


if __name__ == "__main__":
    main()
