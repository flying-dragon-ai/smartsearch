#!/usr/bin/env python3
"""Build and verify the bundled Smart Search Python backend.

Each invocation writes only below a fresh run directory.  It deliberately does
not clean a previous build directory, user configuration, or PyInstaller cache.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packaging.version import Version


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENTRY = Path("src/smart_search/desktop_entry.py")
PACKAGE_NAME = "smart-search"
MODULE_NAME = "smart_search"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entry",
        default=str(DEFAULT_ENTRY),
        help="desktop entry module path, relative to the repository by default",
    )
    parser.add_argument(
        "--output-root",
        default=str(REPOSITORY_ROOT / ".desktop-artifacts"),
        help="parent directory for this fresh build run",
    )
    parser.add_argument(
        "--result-file",
        help="write the validated bundle manifest as JSON to this path",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="start the packaged backend and verify initialize/shutdown only",
    )
    return parser.parse_args()


def repository_path(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else REPOSITORY_ROOT / path).resolve()


def create_run_directory(output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_directory = output_root / f"backend-{stamp}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    if run_directory.exists():
        raise RuntimeError(f"refusing to reuse build directory: {run_directory}")
    run_directory.mkdir()
    return run_directory


def find_packaged_assets(bundle_directory: Path) -> Path:
    candidates = [
        path
        for path in bundle_directory.rglob("assets")
        if path.is_dir() and path.parent.name == MODULE_NAME
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            "expected exactly one packaged smart_search/assets directory; "
            f"found {len(candidates)} in {bundle_directory}"
        )
    return candidates[0]


def find_package_metadata(bundle_directory: Path) -> Path:
    candidates = [
        path
        for path in bundle_directory.rglob("*.dist-info")
        if path.is_dir()
        and path.name.lower().replace("_", "-").startswith(f"{PACKAGE_NAME}-")
        and (path / "METADATA").is_file()
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            "expected exactly one packaged smart-search distribution metadata directory; "
            f"found {len(candidates)} in {bundle_directory}"
        )
    return candidates[0]


def verify_asset_inventory(source_assets: Path, packaged_assets: Path) -> int:
    # Finder metadata is not an application asset and PyInstaller excludes it.
    source_files = [
        path for path in source_assets.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    ]
    missing = [
        path.relative_to(source_assets)
        for path in source_files
        if not (packaged_assets / path.relative_to(source_assets)).is_file()
    ]
    if missing:
        preview = ", ".join(str(path) for path in missing[:10])
        raise RuntimeError(f"PyInstaller bundle is missing source assets: {preview}")
    return len(source_files)


def smoke_backend(executable: Path, run_directory: Path, expected_version: str, *, architecture: str | None = None) -> None:
    smoke_config = run_directory / "smoke-config"
    smoke_config.mkdir()
    requests = [
        {
            "id": 1,
            "method": "initialize",
            "params": {"protocol_version": 1, "config_dir": str(smoke_config), "independent_cli": True, "enable_update_checks": False},
        },
        {"id": 2, "method": "shutdown", "params": {}},
    ]
    try:
        command = [str(executable), "--desktop-backend"]
        if architecture:
            command = ["arch", "-arch", architecture, *command]
        completed = subprocess.run(
            command,
            input="\n".join(json.dumps(request, ensure_ascii=False) for request in requests) + "\n",
            cwd=run_directory,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            text=True,
            timeout=45,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("packaged backend did not finish initialize/shutdown within 45 seconds") from error

    messages: list[dict[str, Any]] = []
    malformed: list[str] = []
    for line in completed.stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(line)
            continue
        if isinstance(value, dict):
            messages.append(value)

    initialize = next((message for message in messages if message.get("id") == 1), None)
    shutdown = next((message for message in messages if message.get("id") == 2), None)
    if completed.returncode != 0 or initialize is None or shutdown is None:
        detail = completed.stderr.strip()[-2000:]
        raise RuntimeError(
            "packaged backend protocol smoke failed "
            f"(exit={completed.returncode}, initialize={initialize is not None}, "
            f"shutdown={shutdown is not None}, malformed_stdout={len(malformed)}): {detail}"
        )
    result = initialize.get("result")
    if not isinstance(result, dict) or result.get("protocol_version") != 1:
        raise RuntimeError("packaged backend initialize response did not confirm protocol_version 1")
    if result.get("version") != expected_version:
        raise RuntimeError("packaged backend reported a different version from the build source")


def write_windows_version_info(path: Path, version: str) -> None:
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo,
    )

    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:$|[-+])", version)
    if not match or any(int(part) > 65535 for part in match.groups()):
        raise RuntimeError("Project version cannot be represented in Windows version resources")
    numbers = (*map(int, match.groups()), 0)
    strings = {
        "CompanyName": "Smart Search", "ProductName": "Smart Search",
        "FileDescription": "Smart Search desktop backend", "FileVersion": version,
        "ProductVersion": version, "InternalName": "smart-search", "OriginalFilename": "smart-search.exe",
    }
    resource = VSVersionInfo(
        ffi=FixedFileInfo(filevers=numbers, prodvers=numbers, mask=0x3F, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
        kids=[StringFileInfo([StringTable("040904B0", [StringStruct(k, v) for k, v in strings.items()])]),
              VarFileInfo([VarStruct("Translation", [1033, 1200])])],
    )
    path.write_text(str(resource), encoding="utf-8")


def main() -> int:
    args = parse_args()
    project_version = re.search(r'^version = "([^"]+)"',
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE).group(1)
    if Version(importlib.metadata.version(PACKAGE_NAME)) != Version(project_version):
        raise RuntimeError("Installed package metadata is stale; install this checkout into the build Python before packaging.")
    entry = repository_path(args.entry)
    output_root = repository_path(args.output_root)
    source_assets = REPOSITORY_ROOT / "src" / MODULE_NAME / "assets"

    if not entry.is_file():
        raise RuntimeError(f"desktop entry is not available: {entry}")
    if not source_assets.is_dir():
        raise RuntimeError(f"source asset directory is not available: {source_assets}")

    run_directory = create_run_directory(output_root)
    dist_directory = run_directory / "dist"
    work_directory = run_directory / "work"
    spec_directory = run_directory / "spec"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onedir",
        "--console",
        "--name",
        PACKAGE_NAME,
        "--paths",
        str(REPOSITORY_ROOT / "src"),
        "--collect-all",
        MODULE_NAME,
        "--copy-metadata",
        PACKAGE_NAME,
        "--distpath",
        str(dist_directory),
        "--workpath",
        str(work_directory),
        "--specpath",
        str(spec_directory),
        str(entry),
    ]
    if os.name == "nt":
        version_file = run_directory / "windows-version.txt"
        write_windows_version_info(version_file, project_version)
        command[-1:-1] = ["--version-file", str(version_file)]
    subprocess.run(command, cwd=REPOSITORY_ROOT, check=True)

    bundle_directory = dist_directory / PACKAGE_NAME
    executable = bundle_directory / f"{PACKAGE_NAME}{'.exe' if os.name == 'nt' else ''}"
    if not executable.is_file():
        raise RuntimeError(f"PyInstaller did not create the expected executable: {executable}")

    # _get_version already prefers this fixed path over versioned dist-info
    # directories that a previous Windows installation may have left behind.
    (bundle_directory / "package.json").write_bytes((REPOSITORY_ROOT / "package.json").read_bytes())
    packaged_assets = find_packaged_assets(bundle_directory)
    metadata_directory = find_package_metadata(bundle_directory)
    asset_file_count = verify_asset_inventory(source_assets, packaged_assets)
    if args.smoke:
        smoke_backend(executable, run_directory, project_version)

    result = {
        "run_directory": str(run_directory),
        "bundle_directory": str(bundle_directory),
        "executable": str(executable),
        "assets_directory": str(packaged_assets),
        "metadata_directory": str(metadata_directory),
        "asset_file_count": asset_file_count,
        "protocol_smoke": "passed" if args.smoke else "not-run",
    }
    if args.result_file:
        result_file = repository_path(args.result_file)
        result_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"backend build failed: {error}", file=sys.stderr)
        raise SystemExit(1)
