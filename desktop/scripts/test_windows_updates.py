#!/usr/bin/env python3
"""Exercise real Velopack packages in one isolated test installation (never the user's App)."""
from __future__ import annotations

import argparse
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def run(argv, log, *, timeout=300):
    result = subprocess.run([str(a) for a in argv], cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Native update check command failed ({result.returncode}); see {log}")


def main(build_file, signing_mode):
    import winreg
    build = json.loads(build_file.read_text(encoding="utf-8-sig"))
    publish = Path(build["publish_directory"])
    staged = Path(build["staged_project_directory"])
    for name in ("AppUpdater.cs", "MainWindow.xaml.cs", "Program.cs"):
        assert (staged / name).read_bytes() == (ROOT / "desktop/windows" / name).read_bytes(), f"Stale build: {name}"
    assert not (publish / "backend").exists(), "The App must not bundle a CLI"
    version = build["version"]
    architecture = build["installer"]["channel"].removeprefix("win-").removesuffix("-stable")
    old_version = "0.0.1"
    test_id = "com.smartsearch.test." + uuid.uuid4().hex
    root = Path(tempfile.mkdtemp(prefix="ssup-"))
    evidence = ROOT / ".desktop-artifacts" / test_id
    evidence.mkdir()
    registry_key = "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\" + test_id
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key).Close()
        raise RuntimeError("Refusing to reuse an existing installation identity")
    except FileNotFoundError:
        pass
    server = None
    receipts = []
    try:
        old = root / "old-publish"
        shutil.copytree(publish, old)
        for source, target_version, label, previous in ((old, old_version, "old", None), (publish, version, "new", root / "old-feed")):
            command = ["pwsh", "-NoProfile", "-File", ROOT / "desktop/scripts/Package-Windows.ps1",
                       "-PublishDirectory", source, "-OutputDirectory", root / (label + "-feed"),
                       "-Version", target_version, "-Architecture", architecture, "-TestPackageId", test_id,
                       "-SigningMode", signing_mode,
                       "-ResultFile", evidence / (label + "-package.json")]
            if previous:
                command += ["-PreviousReleaseDirectory", previous]
            run(command, evidence / (label + "-package.log"))
        installer = json.loads((evidence / "old-package.json").read_text(encoding="utf-8-sig"))
        installed = root / "installed"
        # Velopack's --silent explicitly does not launch the App after installation.
        run([installer["path"], "--silent", "--installto", installed, "--log", evidence / "setup.log"], evidence / "setup-console.log")
        assert (installed / "current/SmartSearch.Desktop.exe").is_file()
        fallback = root / "fallback-installed"
        shutil.copytree(installed, fallback)
        source = root / "new-feed"
        downloaded = []
        corrupt_delta = False

        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                downloaded.append(self.path)
                if corrupt_delta and self.path.endswith("-delta.nupkg"):
                    data = bytearray((source / self.path.removeprefix("/")).read_bytes())
                    data[-1] ^= 1
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    super().do_GET()

        server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(source)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        helper = ROOT / "desktop/tests/NativeUpdateCheck/bin/Release/net8.0-windows/NativeUpdateCheck.dll"
        run(["dotnet", "build", ROOT / "desktop/tests/NativeUpdateCheck", "-c", "Release", "--verbosity", "quiet"], evidence / "helper-build.log")
        for target, label in ((installed, "delta"), (fallback, "full-fallback")):
            downloaded.clear()
            corrupt_delta = label == "full-fallback"
            receipt = evidence / (label + ".json")
            run(["dotnet", helper, f"http://127.0.0.1:{server.server_port}/", target, test_id,
                 old_version, version, architecture, receipt], evidence / (label + ".log"), timeout=180)
            assert any(p.endswith("-delta.nupkg") for p in downloaded), downloaded
            assert any(p.endswith("-full.nupkg") for p in downloaded) == corrupt_delta, downloaded
            for relative in ("SmartSearch.Desktop.exe", "SmartSearch.Desktop.dll"):
                assert hashlib.sha256((target / "current" / relative).read_bytes()).digest() == hashlib.sha256((publish / relative).read_bytes()).digest(), relative
            assert not (target / "current/backend").exists(), "App update bundled a CLI"
            if signing_mode == "Required":
                run(["pwsh", "-NoProfile", "-File", ROOT / "desktop/scripts/Test-WindowsUpdateInstall.ps1",
                     "-Installation", target, "-ResultFile", evidence / (label + "-signatures.json")], evidence / (label + "-signatures.log"))
            receipts.append({"case": label, "requests": list(downloaded), "installed_version": version})
        (evidence / "receipt.json").write_text(json.dumps({"result": "passed", "root": str(root), "build": str(build_file),
            "build_run_directory": build["run_directory"], "test_identity": test_id, "cases": receipts,
            "baseline": "Current payload with version 0.0.1 in the framework manifest",
            "cancel_at_completion_blocked": True, "production_install_modified": False, "gui_tested": False}, indent=2), encoding="utf-8")
        print(evidence / "receipt.json")
    finally:
        if server:
            server.shutdown()
            server.server_close()
            thread.join(5)
        # Delete only this run's exact temporary registration; retain all fixture files for inspection.
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key) as key:
                location = Path(winreg.QueryValueEx(key, "InstallLocation")[0]).resolve()
                assert location.is_relative_to(root.resolve()), "Unexpected registry ownership; left untouched"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, registry_key)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--signing-mode", choices=["Skip", "Required"], default="Skip")
    args = parser.parse_args()
    main(args.build.resolve(), args.signing_mode)
