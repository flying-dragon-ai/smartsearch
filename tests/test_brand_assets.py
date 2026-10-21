"""Check native icon containers and the packaged Web UI without image dependencies."""
import base64
from pathlib import Path
import plistlib
import re
import struct

ROOT = Path(__file__).resolve().parents[1]


def png_size(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_brand_assets_are_complete_and_consistent():
    png = (ROOT / "assets/branding/smart-search.png").read_bytes()
    assert png_size(png) == (1024, 1024)
    assert png == (ROOT / "desktop/windows/Assets/smart-search.png").read_bytes()
    ico = (ROOT / "desktop/windows/Assets/smart-search.ico").read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", ico)
    assert (reserved, kind, count) == (0, 1, 9)
    frames = {}
    for index in range(count):
        width, height, _, _, planes, depth, length, offset = struct.unpack_from("<BBBBHHII", ico, 6 + index * 16)
        width, height = width or 256, height or 256
        assert (planes, depth) == (1, 32)
        frames[width] = ico[offset:offset + length]
        assert len(frames[width]) == length and png_size(frames[width]) == (width, height)
    assert set(frames) == {16, 20, 24, 32, 40, 48, 64, 128, 256}

    icns = (ROOT / "desktop/packaging/macos/SmartSearch.icns").read_bytes()
    assert struct.unpack_from(">4sI", icns) == (b"icns", len(icns))
    offset = 8
    for tag, size in [(b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024)]:
        chunk_tag, length = struct.unpack_from(">4sI", icns, offset)
        frame = icns[offset + 8:offset + length]
        assert chunk_tag == tag and png_size(frame) == (size, size)
        if size in frames:
            assert frame == frames[size]
        offset += length
    assert offset == len(icns)
    plist = plistlib.loads((ROOT / "desktop/packaging/macos/Info.plist").read_bytes())
    assert plist["CFBundleIconFile"] == "SmartSearch.icns"

    page = (ROOT / "src/smart_search/assets/ui/index.html").read_text(encoding="utf-8")
    embedded = re.findall(r'data-smart-search-icon (?:src|href)="data:image/png;base64,([^"]+)"', page)
    assert len(embedded) == 2 and embedded[0] == embedded[1]
    assert base64.b64decode(embedded[0]) == frames[64]
