"""Exercise the real universal backend launcher without touching any installed app."""
from pathlib import Path
import platform
import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Requires Apple's native Mach-O toolchain")
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def backend(tmp_path):
    directory = tmp_path / "Original App.app/Contents/Resources/backend"
    directory.mkdir(parents=True)
    subprocess.run(["xcrun", "clang", "-arch", "arm64", "-arch", "x86_64", "-Wall", "-Wextra", "-Werror",
                    str(ROOT / "desktop/packaging/macos/backend-launcher.c"), "-o", str(directory / "smart-search")], check=True)
    source = tmp_path / "backend.c"
    source.write_text('''#include <stdio.h>
int main(int argc, char **argv) {
    char input[80];
    if (argc != 2 || !fgets(input, sizeof(input), stdin)) return 2;
    printf("%s|%s|%s", ARCH, argv[1], input);
    return 23;
}
''')
    for architecture in ("arm64", "x86_64"):
        (directory / architecture).mkdir()
        subprocess.run(["xcrun", "clang", "-arch", architecture, f'-DARCH="{architecture}"',
                        str(source), "-o", str(directory / architecture / "smart-search")], check=True)
    # Finder installations change the absolute path and commonly contain spaces.
    relocated = tmp_path / "Installed App.app"
    (tmp_path / "Original App.app").rename(relocated)
    return relocated / "Contents/Resources/backend"


@pytest.mark.parametrize("architecture", ["arm64", "x86_64"])
def test_launcher_selects_native_backend_and_preserves_process_io(backend, architecture):
    available = subprocess.run(["arch", "-arch", architecture, "/usr/bin/true"], capture_output=True).returncode == 0
    if not available:
        pytest.skip(f"Host cannot execute {architecture}; native CI covers it")
    result = subprocess.run(["arch", "-arch", architecture, str(backend / "smart-search"), "argument with spaces"],
                            input="IPC request\n", text=True, capture_output=True)
    assert result.returncode == 23
    assert result.stdout == f"{architecture}|argument with spaces|IPC request\n"
    assert result.stderr == ""


def test_launcher_fails_if_matching_backend_is_missing(backend):
    (backend / platform.machine() / "smart-search").unlink()
    result = subprocess.run([str(backend / "smart-search")], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Cannot start" in result.stderr
