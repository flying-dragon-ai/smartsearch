#!/usr/bin/env python3
"""Package an independently runnable CLI; never put it inside the native App."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def package(bundle, output, platform, architecture, version):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("A stable CLI version is required")
    binary = bundle / ("smart-search.exe" if platform == "windows" else "smart-search")
    if bundle.name != "smart-search" or not binary.is_file():
        raise ValueError("Expected the complete smart-search standalone bundle")
    metadata = json.loads((bundle / "package.json").read_text())
    if metadata.get("version") != version:
        raise ValueError("CLI source and standalone bundle versions differ")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"smart-search-cli-{version}-{platform}-{architecture}.zip"
    if archive.exists():
        raise FileExistsError(archive)
    if platform == "macos":
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(binary)], check=True)
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(bundle), str(archive)], check=True)
    else:
        shutil.make_archive(str(archive.with_suffix("")), "zip", bundle.parent, bundle.name)
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n")
    return {"archive": str(archive), "sha256": digest, "version": version,
            "platform": platform, "architecture": architecture, "desktop_protocol_version": 1}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--platform", choices=("macos", "windows"), required=True)
    parser.add_argument("--architecture", choices=("arm64", "x86_64", "x64"), required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.bundle, args.output, args.platform, args.architecture, args.version)))
