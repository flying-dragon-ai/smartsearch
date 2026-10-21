"""Release trust boundaries use synthetic packages, with no network or install."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET

import pytest

spec = importlib.util.spec_from_file_location(
    "update_artifacts", Path(__file__).resolve().parents[1] / "desktop/scripts/update_artifacts.py"
)
updates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updates)
pytestmark = pytest.mark.skipif(sys.version_info < (3, 11), reason="Release runner uses Python 3.11+")
VERSION = "1.2.3"


def release_files(root):
    for platform, architectures in (("macos", ("arm64", "x86_64")), ("windows", ("arm64", "x64"))):
        for architecture in architectures:
            name = f"smart-search-cli-{VERSION}-{platform}-{architecture}.zip"
            (root / name).write_bytes(b"independent cli " + architecture.encode())
            (root / (name + ".sha256")).write_text(f"{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n")
    for arch in ("x64", "arm64"):
        package = root / f"com.smartsearch.desktop.win-{arch}-{VERSION}-full.nupkg"
        package.write_bytes(b"full " + arch.encode())
        download_arch = "x86_64" if arch == "x64" else arch
        (root / f"SmartSearch-v{VERSION}-windows-Setup-{download_arch}.exe").write_bytes(b"installer")
        (root / f"releases.win-{arch}-stable.json").write_text(json.dumps({"Assets": [{
            "PackageId": f"com.smartsearch.desktop.win-{arch}", "Version": VERSION,
            "Type": "Full", "FileName": package.name, "Size": package.stat().st_size,
            "SHA256": hashlib.sha256(package.read_bytes()).hexdigest(),
        }]}))
    for arch in ("universal", "arm64", "x86_64"):
        suffix = "" if arch == "universal" else f"-{arch}"
        package = root / f"SmartSearch-v{VERSION}{suffix}-sparkle.zip"
        package.write_bytes(b"mac full")
        (root / f"SmartSearch-v{VERSION}{suffix}.dmg").write_bytes(b"dmg")
        rss = ET.Element("rss")
        item = ET.SubElement(ET.SubElement(rss, "channel"), "item")
        ET.SubElement(item, f"{{{updates.SPARKLE}}}version").text = VERSION
        ET.SubElement(item, "enclosure", {
            "url": f"https://github.com/{updates.REPOSITORY}/releases/download/v{VERSION}/{package.name}",
            "length": str(package.stat().st_size), f"{{{updates.SPARKLE}}}edSignature": "fixture-only",
        })
        ET.ElementTree(rss).write(root / f"appcast-macos-{arch}.xml")


@pytest.mark.parametrize("damage", [None, "test-identity", "wrong-certificate", "missing-evidence", "adhoc", "empty-pin"])
@pytest.mark.parametrize("damaged_architecture", ["arm64", "universal"])
def test_macos_signed_release_requires_maintainer_identity(tmp_path, damage, damaged_architecture):
    release_files(tmp_path)
    digest = "A" * 64
    for arch in ("universal", "arm64", "x86_64"):
        (tmp_path / f"macos-signing-{arch}.json").write_text(json.dumps({
            "kind": "self-signed", "certificate_sha256": digest,
        }))
    evidence = tmp_path / f"macos-signing-{damaged_architecture}.json"
    if damage == "missing-evidence":
        evidence.unlink()
    elif damage in {"test-identity", "wrong-certificate"}:
        data = json.loads(evidence.read_text())
        data["kind" if damage == "test-identity" else "certificate_sha256"] = "self-signed-test" if damage == "test-identity" else "B" * 64
        evidence.write_text(json.dumps(data))
    elif damage == "adhoc":
        evidence.write_text(json.dumps({"kind": "ad-hoc-test"}))
    elif damage == "empty-pin":
        digest = ""
    if damage:
        with pytest.raises(ValueError):
            updates.validate_release(tmp_path, VERSION, digest)
        assert not (tmp_path / "SHA256SUMS.txt").exists()
    else:
        assert updates.validate_release(tmp_path, VERSION, digest)["assets"] == 26


@pytest.mark.parametrize("duplicate", [False, True])
def test_workflow_flattens_nested_assets_without_overwriting(tmp_path, monkeypatch, duplicate):
    root = tmp_path / "release-packages"
    nested = root / "runner-build" / "updates"
    nested.mkdir(parents=True)
    release_files(nested)
    name = "appcast-macos-arm64.xml"
    original = (nested / name).read_bytes()
    if duplicate:
        (root / name).write_bytes(b"keep existing")
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/desktop-build.yml").read_text()
    step = workflow.split("- name: Verify every feed reference and create checksums", 1)[1]
    python = textwrap.dedent(step.split("python3 - <<'PY'\n", 1)[1].split("\n          PY", 1)[0])
    monkeypatch.chdir(tmp_path)
    if duplicate:
        with pytest.raises(ValueError, match="Duplicate release asset"):
            exec(compile(python, "desktop-build.yml:flatten", "exec"), {})
        assert (root / name).read_bytes() == b"keep existing"
        assert (nested / name).read_bytes() == original
    else:
        exec(compile(python, "desktop-build.yml:flatten", "exec"), {})
        assert updates.validate_release(root, VERSION)["assets"] == 23
        assert (root / name).read_bytes() == original


@pytest.mark.parametrize("architecture", ["universal", "arm64", "x86_64"])
def test_sparkle_delta_names_are_architecture_specific_and_urls_are_decoded(tmp_path, monkeypatch, architecture):
    from urllib.parse import quote

    stage = tmp_path / "stage"
    output = tmp_path / "output"
    stage.mkdir()
    output.mkdir()
    release_files(stage)
    feed = stage / f"appcast-macos-{architecture}.xml"
    tree = ET.parse(feed)
    item = tree.find("./channel/item")
    prefix = f"https://github.com/{updates.REPOSITORY}/releases/download/v{VERSION}/"
    delta = stage / f"Smart Search{VERSION}-1.0.0.delta"
    delta.write_bytes(b"signed delta bytes")
    ET.SubElement(ET.SubElement(item, f"{{{updates.SPARKLE}}}deltas"), "enclosure", {
        "url": prefix + quote(delta.name), "length": str(delta.stat().st_size),
        f"{{{updates.SPARKLE}}}edSignature": "fixture-delta-signature",
        f"{{{updates.SPARKLE}}}deltaFrom": "1.0.0",
    })
    tree.write(feed)
    script = (Path(__file__).resolve().parents[1] / "desktop/scripts/package-sparkle.sh").read_text(encoding="utf-8")
    python = script.rsplit("<<'PY'\n", 1)[1].split("\nPY", 1)[0]
    monkeypatch.setattr(sys, "argv", ["package-sparkle", str(stage), str(output), str(feed),
                                     VERSION, architecture, "true", prefix])
    exec(compile(python, "package-sparkle.sh:python", "exec"), {})
    suffix = "" if architecture == "universal" else f"-{architecture}"
    target = f"SmartSearch-v{VERSION}-from-1.0.0{suffix}.delta"
    assert (output / target).read_bytes() == delta.read_bytes()
    enclosures = list(ET.parse(output / feed.name).find("./channel/item").iter("enclosure"))
    assert len(enclosures) == 2
    assert enclosures[1].get("url") == prefix + target
    assert enclosures[1].get(f"{{{updates.SPARKLE}}}edSignature") == "fixture-delta-signature"
    assert len(list(output.iterdir())) == 3


@pytest.mark.parametrize("damage", [None, "missing-installer", "missing-universal", "corrupt", "architecture", "traversal", "duplicate", "missing-full", "missing-signature", "foreign-url"])
def test_release_assets_fail_closed(tmp_path, damage):
    release_files(tmp_path)
    windows = tmp_path / "releases.win-x64-stable.json"
    feed = json.loads(windows.read_text())
    asset = feed["Assets"][0]
    if damage == "missing-installer":
        (tmp_path / f"SmartSearch-v{VERSION}-windows-Setup-x86_64.exe").unlink()
    elif damage == "missing-universal":
        (tmp_path / f"SmartSearch-v{VERSION}.dmg").unlink()
    elif damage == "corrupt":
        (tmp_path / asset["FileName"]).write_bytes(b"bad")
    elif damage == "architecture":
        asset["PackageId"] = "com.smartsearch.desktop.win-arm64"
    elif damage == "traversal":
        asset["FileName"] = "../escape.nupkg"
    elif damage == "duplicate":
        feed["Assets"].append(asset.copy())
    windows.write_text(json.dumps(feed))
    if damage in {"missing-full", "missing-signature", "foreign-url"}:
        path = tmp_path / "appcast-macos-arm64.xml"
        tree = ET.parse(path)
        item = tree.find("./channel/item")
        enclosure = item.find("enclosure")
        if damage == "missing-full":
            item.remove(enclosure)
        elif damage == "missing-signature":
            del enclosure.attrib[f"{{{updates.SPARKLE}}}edSignature"]
        else:
            enclosure.set("url", enclosure.get("url").replace("github.com", "invalid.example"))
        tree.write(path)
    if damage:
        with pytest.raises(ValueError):
            updates.validate_release(tmp_path, VERSION)
        assert not (tmp_path / "SHA256SUMS.txt").exists()
    else:
        assert updates.validate_release(tmp_path, VERSION)["assets"] == 23
        for row in (tmp_path / "SHA256SUMS.txt").read_text().splitlines():
            digest, name = row.split("  ")
            assert digest == hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()


@pytest.mark.parametrize("failure", [None, "network", "corrupt", "no-baseline", "invalid-platform"])
def test_previous_release_integrity_and_first_release_are_distinct(tmp_path, monkeypatch, failure):
    package_name = "com.smartsearch.desktop.win-x64-1.0.0-full.nupkg"
    feed_name = "releases.win-x64-stable.json"
    package = b"verified previous package"
    feed = json.dumps({"Assets": [{"Type": "Full", "Version": "1.0.0",
        "PackageId": "com.smartsearch.desktop.win-x64", "FileName": package_name}]}).encode()
    data = {feed_name: feed, package_name: package}
    release = {"tag_name": "v1.0.0", "assets": [{"name": name, "size": len(content),
        "digest": "sha256:" + hashlib.sha256(content).hexdigest()} for name, content in data.items()]}

    def gh(*args):
        if failure == "network":
            raise subprocess.CalledProcessError(1, "gh")
        if args[0] == "api":
            return json.dumps([[] if failure == "no-baseline" else [release]])
        name = args[args.index("--pattern") + 1]
        output = Path(args[args.index("--dir") + 1])
        (output / name).write_bytes(b"tampered" if failure == "corrupt" else data[name])
        return ""

    monkeypatch.setattr(updates, "gh", gh)
    if failure in {"network", "corrupt", "invalid-platform"}:
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            updates.fetch_baseline(None if failure == "invalid-platform" else "windows", "x64", VERSION, tmp_path / "baseline")
    else:
        result = updates.fetch_baseline("windows", "x64", VERSION, tmp_path / "baseline")
        assert result["status"] == ("first-framework-release" if failure == "no-baseline" else "verified")
        if failure is None:
            assert (Path(result["directory"]) / package_name).read_bytes() == package


@pytest.mark.parametrize("archive_name", ["SmartSearch-1.0.0-macos-arm64-sparkle.zip", "SmartSearch-v1.0.0-arm64-sparkle.zip"])
def test_macos_baseline_follows_verified_feed_across_filename_migration(tmp_path, monkeypatch, archive_name):
    package = b"previous Mac archive"
    feed_name = "appcast-macos-arm64.xml"
    feed = f'''<rss xmlns:sparkle="{updates.SPARKLE}"><channel><item>
      <sparkle:version>1.0.0</sparkle:version><enclosure
      url="https://github.com/{updates.REPOSITORY}/releases/download/v1.0.0/{archive_name}"
      length="{len(package)}" sparkle:edSignature="fixture" /></item></channel></rss>'''.encode()
    data = {feed_name: feed, archive_name: package}
    release = {"tag_name": "v1.0.0", "assets": [{"name": name, "size": len(content),
               "digest": "sha256:" + hashlib.sha256(content).hexdigest()} for name, content in data.items()]}

    def gh(*args):
        if args[0] == "api":
            return json.dumps([[release]])
        name = args[args.index("--pattern") + 1]
        (Path(args[args.index("--dir") + 1]) / name).write_bytes(data[name])
        return ""

    monkeypatch.setattr(updates, "gh", gh)
    result = updates.fetch_baseline("macos", "arm64", VERSION, tmp_path / "baseline")
    assert (Path(result["directory"]) / archive_name).read_bytes() == package
    # A per-architecture release is not a universal delta baseline.
    result = updates.fetch_baseline("macos", "universal", VERSION, tmp_path / "universal")
    assert result == {"status": "first-framework-release", "directory": None}


@pytest.mark.parametrize("damage", ["missing", "tampered"])
def test_cli_archives_are_required_and_verified(tmp_path, damage):
    release_files(tmp_path)
    archive = tmp_path / f"smart-search-cli-{VERSION}-macos-arm64.zip"
    if damage == "missing":
        archive.unlink()
    else:
        archive.write_bytes(b"tampered")
    with pytest.raises((ValueError, FileNotFoundError)):
        updates.validate_release(tmp_path, VERSION)
