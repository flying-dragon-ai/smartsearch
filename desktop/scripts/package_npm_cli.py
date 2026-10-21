#!/usr/bin/env python3
"""Assemble an npm platform package from a verified, self-contained CLI build."""
from __future__ import annotations

import argparse
import json
import os
import sysconfig
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build = json.loads(args.manifest.read_text(encoding="utf-8"))
    source = Path(build["bundle_directory"]).resolve()
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    target_os = {"darwin": "darwin", "win32": "win32", "linux": "linux"}[sys.platform]
    # Windows on ARM can run an x64 build interpreter. Label the interpreter
    # target, not platform.machine(), which reports the host CPU in that case.
    machine = sysconfig.get_platform().rsplit("-", 1)[-1].lower()
    arch = {"arm64": "arm64", "aarch64": "arm64", "amd64": "x64", "x86_64": "x64"}[machine]
    name = f"{package['name']}-{target_os}-{arch}"
    if package["optionalDependencies"].get(name) != package["version"]:
        raise RuntimeError("Platform dependency version is out of sync")
    if build.get("protocol_smoke") != "passed":
        raise RuntimeError("Build the CLI with --smoke before packaging")
    if json.loads((source / "package.json").read_text())["version"] != package["version"]:
        raise RuntimeError("CLI build version does not match npm package version")
    # npm omits symlinks. Materialize framework links without copying anything
    # outside the validated PyInstaller runtime.
    for entry in source.rglob("*"):
        if entry.is_symlink() and not entry.resolve().is_relative_to(source):
            raise RuntimeError(f"Runtime symlink escapes the bundle: {entry}")
    args.output.mkdir(parents=True, exist_ok=False)
    destination = args.output / "runtime" / "smart-search"
    shutil.copytree(source, destination, symlinks=False)
    binary = destination / ("smart-search.exe" if os.name == "nt" else "smart-search")
    binary.chmod(binary.stat().st_mode | 0o111)
    metadata = {
        "name": name, "version": package["version"], "description": f"Self-contained Smart Search CLI for {target_os}/{arch}",
        "license": "MIT", "repository": package["repository"], "os": [target_os], "cpu": [arch],
        "files": ["runtime/"], "publishConfig": {"access": "public"},
    }
    if target_os == "linux":
        metadata["libc"] = ["glibc"]
    (args.output / "package.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(ROOT / "LICENSE", args.output / "LICENSE")
    print(json.dumps({"name": name, "version": package["version"], "directory": str(args.output.resolve())}))


if __name__ == "__main__":
    main()
