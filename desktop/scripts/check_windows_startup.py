"""Run after closing Smart Search: check the actual published native host.

Usage: python desktop/scripts/check_windows_startup.py <publish-directory>
This uses an empty temporary profile, makes no provider requests, and closes
only the test process it launches. A separate GUI check still covers behavior.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from smart_search.config import Config


def main():
    directory = Path(sys.argv[1]).resolve()
    for name in ("SmartSearch.Desktop.exe", "App.xbf", "MainWindow.xbf", "SmartSearch.Desktop.pri"):
        assert (directory / name).is_file(), f"Missing native UI resource: {name}"
    # Preserve the disposable profile as evidence; this check never deletes files.
    profile = tempfile.mkdtemp(prefix="smart-search-native-startup-")
    env = {key: value for key, value in os.environ.items() if key not in Config._CONFIG_KEYS}
    env["SMART_SEARCH_CONFIG_DIR"] = profile
    process = subprocess.Popen([str(directory / "SmartSearch.Desktop.exe")], env=env, cwd=directory)
    try:
        try:
            code = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(json.dumps({"native_host_survived_startup": True, "pid": process.pid, "profile": profile}))
        else:
            raise AssertionError(f"Native host exited during startup: {code}; close any existing instance first")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
