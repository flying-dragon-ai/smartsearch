#!/usr/bin/env python3
"""Fetch verified previous packages and validate native updater release assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

REPOSITORY = "konbakuyomu/smartsearch"
SPARKLE = "http://www.andymatuschak.org/xml-namespaces/sparkle"
MACOS_ARCHITECTURES = ("universal", "arm64", "x86_64")


def macos_stem(version, architecture):
    suffix = "" if architecture == "universal" else f"-{architecture}"
    return f"SmartSearch-v{version}{suffix}"


def windows_installer(version, architecture):
    download_architecture = "x86_64" if architecture == "x64" else architecture
    return f"SmartSearch-v{version}-windows-Setup-{download_architecture}.exe"


def version_tuple(version):
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version):
        raise ValueError("A stable X.Y.Z version is required")
    return tuple(map(int, version.split(".")))


def file_path(root, name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ValueError("Unsafe release asset filename")
    path = root / name
    if path.is_symlink():
        raise ValueError("Linked release files are not allowed")
    return path


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def gh(*args):
    result = subprocess.run(["gh", *args], check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


def fetch_baseline(platform, architecture, version, output):
    if platform not in {"windows", "macos"} or architecture not in (
        {"x64", "arm64"} if platform == "windows" else set(MACOS_ARCHITECTURES)
    ):
        raise ValueError("A matching platform and architecture are required")
    target = version_tuple(version)
    output.mkdir(parents=True, exist_ok=False)
    pages = json.loads(gh("api", f"repos/{REPOSITORY}/releases?per_page=100", "--paginate", "--slurp"))
    eligible = []
    feed_name = f"releases.win-{architecture}-stable.json" if platform == "windows" else f"appcast-macos-{architecture}.xml"
    for release in (r for page in pages for r in page):
        tag = release.get("tag_name", "")
        if release.get("draft") or release.get("prerelease") or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
            continue
        if version_tuple(tag[1:]) < target and any(a["name"] == feed_name for a in release["assets"]):
            eligible.append(release)
    if not eligible:
        return {"status": "first-framework-release", "directory": None}
    release = max(eligible, key=lambda r: version_tuple(r["tag_name"][1:]))
    assets = {a["name"]: a for a in release["assets"]}
    checksums = None

    def download(name):
        nonlocal checksums
        path = file_path(output, name)
        asset = assets[name]
        if not 0 < asset["size"] <= 1024 ** 3:
            raise ValueError("Invalid baseline asset size")
        gh("release", "download", release["tag_name"], "--repo", REPOSITORY, "--pattern", name, "--dir", str(output))
        digest = asset.get("digest") or ""
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            if checksums is None:
                sums = file_path(output, "SHA256SUMS.txt")
                if not 0 < assets["SHA256SUMS.txt"]["size"] <= 65536:
                    raise ValueError("Invalid checksum manifest size")
                gh("release", "download", release["tag_name"], "--repo", REPOSITORY, "--pattern", sums.name, "--dir", str(output))
                checksums = {line[66:]: line[:64] for line in sums.read_text().splitlines()
                             if re.fullmatch(r"[0-9a-f]{64}  .+", line)}
            digest = "sha256:" + checksums[name]
        if path.stat().st_size != asset["size"] or sha256(path) != digest[7:]:
            raise ValueError("Baseline asset integrity failed")
        return path

    feed = download(feed_name)
    previous = release["tag_name"][1:]
    if platform == "windows":
        entries = [a for a in json.loads(feed.read_text(encoding="utf-8-sig"))["Assets"]
                   if a["Type"] == "Full" and a["Version"] == previous
                   and a["PackageId"] == f"com.smartsearch.desktop.win-{architecture}"]
        if len(entries) != 1:
            raise ValueError("Baseline feed does not identify one matching full package")
        download(entries[0]["FileName"])
    else:
        items = [item for item in ET.parse(feed).findall("./channel/item")
                 if item.findtext(f"{{{SPARKLE}}}version") == previous]
        if len(items) != 1 or len(items[0].findall("enclosure")) != 1:
            raise ValueError("Baseline feed does not identify one full Sparkle archive")
        enclosure = items[0].find("enclosure")
        prefix = f"https://github.com/{REPOSITORY}/releases/download/v{previous}/"
        names = {macos_stem(previous, architecture) + "-sparkle.zip"}
        if architecture != "universal":
            # v0.1.24 is the first update baseline and uses the old naming scheme.
            names.add(f"SmartSearch-{previous}-macos-{architecture}-sparkle.zip")
        name = next((name for name in names if enclosure.get("url") == prefix + name), None)
        if name is None or not enclosure.get(f"{{{SPARKLE}}}edSignature"):
            raise ValueError("Baseline Sparkle URL or signature is invalid")
        archive = download(name)
        if archive.stat().st_size != int(enclosure.attrib["length"]):
            raise ValueError("Baseline Sparkle size mismatch")
    return {"status": "verified", "directory": str(output.resolve()), "version": previous, "feed": feed.name}


def validate_release(root, version, macos_certificate_sha256=None):
    version_tuple(version)
    if macos_certificate_sha256 is not None and not re.fullmatch(r"[0-9A-Fa-f]{64}", macos_certificate_sha256):
        raise ValueError("A pinned macOS certificate SHA-256 is required for signed releases")
    required = set()
    for arch in ("x64", "arm64"):
        name = f"releases.win-{arch}-stable.json"
        required |= {name, windows_installer(version, arch)}
        feed = json.loads(file_path(root, name).read_text(encoding="utf-8-sig"))
        full = 0
        names = set()
        for asset in feed["Assets"]:
            if asset["Version"] != version or asset["PackageId"] != f"com.smartsearch.desktop.win-{arch}":
                raise ValueError("Wrong version or architecture in Velopack feed")
            if asset["Type"] not in {"Full", "Delta"}:
                raise ValueError("Unexpected Velopack asset type")
            full += asset["Type"] == "Full"
            path = file_path(root, asset["FileName"])
            if path.name in names:
                raise ValueError("Duplicate Velopack package reference")
            names.add(path.name)
            if path.stat().st_size != asset["Size"] or sha256(path).upper() != asset["SHA256"].upper():
                raise ValueError("Velopack feed integrity mismatch")
            required.add(path.name)
        if full != 1:
            raise ValueError("Each Windows feed must have one full target package")
    for arch in MACOS_ARCHITECTURES:
        name = f"appcast-macos-{arch}.xml"
        required |= {name, macos_stem(version, arch) + ".dmg"}
        if macos_certificate_sha256 is not None:
            signing_name = f"macos-signing-{arch}.json"
            signing_path = file_path(root, signing_name)
            if not signing_path.is_file():
                raise ValueError("Missing macOS release signing evidence")
            signing = json.loads(signing_path.read_text())
            if signing.get("kind") != "self-signed" or signing.get("certificate_sha256") != macos_certificate_sha256.upper():
                raise ValueError("macOS release signing evidence does not match the maintainer identity")
            required.add(signing_name)
        feed = ET.parse(file_path(root, name))
        current = [item for item in feed.findall("./channel/item")
                   if item.findtext(f"{{{SPARKLE}}}version") == version]
        if len(current) != 1 or len(feed.findall("./channel/item")) != 1:
            raise ValueError("Sparkle feed must have one current version")
        full = current[0].findall("enclosure")
        if len(full) != 1:
            raise ValueError("Sparkle feed must have one full target archive")
        if not full[0].get("url", "").endswith("/" + macos_stem(version, arch) + "-sparkle.zip"):
            raise ValueError("Sparkle full archive does not match the target")
        for enclosure in current[0].iter("enclosure"):
            prefix = f"https://github.com/{REPOSITORY}/releases/download/v{version}/"
            url = enclosure.attrib["url"]
            if not url.startswith(prefix) or not enclosure.attrib.get(f"{{{SPARKLE}}}edSignature"):
                raise ValueError("Sparkle update URL or signature is missing")
            path = file_path(root, url[len(prefix):])
            if path.stat().st_size != int(enclosure.attrib["length"]):
                raise ValueError("Sparkle update size mismatch")
            delta_from = enclosure.get(f"{{{SPARKLE}}}deltaFrom")
            if delta_from is None:
                expected = macos_stem(version, arch) + "-sparkle.zip"
            else:
                if version_tuple(delta_from) >= version_tuple(version):
                    raise ValueError("Sparkle delta must upgrade an older version")
                suffix = "" if arch == "universal" else f"-{arch}"
                expected = f"SmartSearch-v{version}-from-{delta_from}{suffix}.delta"
            if path.name != expected:
                raise ValueError("Sparkle update architecture mismatch")
            required.add(path.name)
    for platform, architectures in (("macos", ("arm64", "x86_64")), ("windows", ("arm64", "x64"))):
        for architecture in architectures:
            name = f"smart-search-cli-{version}-{platform}-{architecture}.zip"
            archive = file_path(root, name)
            checksum = file_path(root, name + ".sha256")
            if checksum.read_text().strip() != f"{sha256(archive)}  {name}":
                raise ValueError("Standalone CLI archive checksum mismatch")
            required |= {name, checksum.name}
    actual = {p.name for p in root.iterdir() if p.is_file()}
    if actual != required:
        raise ValueError(f"Missing or unexpected release files: {sorted(actual ^ required)}")
    rows = [f"{sha256(file_path(root, name))}  {name}" for name in sorted(required)]
    (root / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {"version": version, "assets": len(required), "status": "verified"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["baseline", "validate"])
    parser.add_argument("--platform", choices=["windows", "macos"])
    parser.add_argument("--architecture", choices=["x64", *MACOS_ARCHITECTURES])
    parser.add_argument("--version", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--macos-certificate-sha256", help="Require maintainer-signed macOS assets and matching signing evidence")
    args = parser.parse_args()
    if args.operation == "baseline":
        if not args.platform or args.architecture not in ({"x64", "arm64"} if args.platform == "windows" else set(MACOS_ARCHITECTURES)):
            parser.error("A matching platform and architecture are required")
        result = fetch_baseline(args.platform, args.architecture, args.version, args.directory)
    else:
        result = validate_release(args.directory, args.version, args.macos_certificate_sha256)
    if args.result:
        args.result.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
