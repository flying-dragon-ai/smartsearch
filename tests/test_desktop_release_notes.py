"""Download links must point to supplied assets and preserve editorial release notes."""
import importlib.util
import json
from pathlib import Path
import re

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "desktop/scripts"


@pytest.fixture
def notes(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("desktop_release_notes", SCRIPTS / "release_notes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def assets(tmp_path):
    for name in ("SmartSearch-v1.2.3.dmg", "SmartSearch-v1.2.3-arm64.dmg", "SmartSearch-v1.2.3-x86_64.dmg",
                 "SmartSearch-v1.2.3-windows-Setup-x86_64.exe", "SmartSearch-v1.2.3-windows-Setup-arm64.exe", "SHA256SUMS.txt"):
        (tmp_path / name).write_bytes(b"verified release asset")
    for arch in ("universal", "arm64", "x86_64"):
        (tmp_path / f"macos-signing-{arch}.json").write_text(json.dumps({"kind": "self-signed", "certificate_sha256": "A" * 64}))
    for platform, architectures in (("macos", ("arm64", "x86_64")), ("windows", ("arm64", "x64"))):
        for architecture in architectures:
            (tmp_path / f"smart-search-cli-1.2.3-{platform}-{architecture}.zip").write_bytes(b"cli")
    return tmp_path


def test_downloads_keep_original_notes_and_only_link_existing_assets(notes, assets):
    original = "## 修复\n\n保留用户写的说明。\n\n## Contributors\n\nThanks @developer.\n"
    output = notes.with_downloads(original, "1.2.3", assets)
    assert output.endswith(original)
    assert notes.with_downloads(output, "1.2.3", assets) == output
    links = re.findall(r"\]\(https://github.com/konbakuyomu/smartsearch/releases/download/v1\.2\.3/([^)]*)\)", output)
    assert len(links) == 10
    assert {path.name for path in assets.iterdir() if path.suffix != ".json"} == set(links)
    assert "fixed self-signed certificate" in output


def test_partial_release_does_not_advertise_missing_universal_installer(notes, assets):
    (assets / "SmartSearch-v1.2.3.dmg").unlink()
    with pytest.raises(ValueError, match="missing or empty"):
        notes.with_downloads("Existing notes", "1.2.3", assets)


def test_malformed_markers_do_not_erase_user_notes(notes, assets):
    with pytest.raises(ValueError, match="malformed"):
        notes.with_downloads(notes.START + "\nUser notes", "1.2.3", assets)


@pytest.mark.parametrize("kind,label", [("self-signed-test", "disposable test certificate"), ("ad-hoc-test", "ad-hoc signing")])
def test_downloads_describe_actual_candidate_signing(notes, assets, kind, label):
    for path in assets.glob("macos-signing-*.json"):
        path.write_text(json.dumps({"kind": kind}))
    output = notes.with_downloads("Existing notes", "1.2.3", assets)
    assert label in output and "fixed self-signed certificate" not in output


@pytest.mark.parametrize("damage", ["test-identity", "wrong-certificate"])
def test_downloads_reject_mixed_universal_signing(notes, assets, damage):
    path = assets / "macos-signing-universal.json"
    signing = json.loads(path.read_text())
    signing["kind" if damage == "test-identity" else "certificate_sha256"] = "self-signed-test" if damage == "test-identity" else "B" * 64
    path.write_text(json.dumps(signing))
    with pytest.raises(ValueError, match="signing status|certificates must match"):
        notes.with_downloads("Existing notes", "1.2.3", assets)
