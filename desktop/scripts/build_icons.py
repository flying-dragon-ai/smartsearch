# /// script
# requires-python = ">=3.10"
# dependencies = ["Pillow==12.3.0"]
# ///
"""Derive platform icons from the exported PNG without changing the artwork."""

from __future__ import annotations

import base64
import io
from pathlib import Path
import re
import shutil
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WINDOWS_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
MACOS_CHUNKS = ((b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024))


def png_frame(image: Image.Image, size: int) -> bytes:
    stream = io.BytesIO()
    image.resize((size, size), Image.Resampling.LANCZOS).save(
        stream, format="PNG", icc_profile=image.info.get("icc_profile")
    )
    return stream.getvalue()


def windows_icon(frames: dict[int, bytes]) -> bytes:
    directory = bytearray(struct.pack("<HHH", 0, 1, len(WINDOWS_SIZES)))
    offset = 6 + 16 * len(WINDOWS_SIZES)
    for size in WINDOWS_SIZES:
        dimension = 0 if size == 256 else size
        frame = frames[size]
        directory.extend(struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(frame), offset))
        offset += len(frame)
    return bytes(directory) + b"".join(frames[size] for size in WINDOWS_SIZES)


def macos_icon(frames: dict[int, bytes]) -> bytes:
    chunks = b"".join(
        struct.pack(">4sI", tag, len(frames[size]) + 8) + frames[size]
        for tag, size in MACOS_CHUNKS
    )
    return struct.pack(">4sI", b"icns", len(chunks) + 8) + chunks


def main() -> None:
    source_path = ROOT / "assets/branding/smart-search.png"
    sizes = sorted(set(WINDOWS_SIZES) | {size for _, size in MACOS_CHUNKS})
    with Image.open(source_path) as source:
        if source.format != "PNG" or source.size != (1024, 1024):
            raise ValueError("Export a 1024 x 1024 PNG from Icon Composer before generating icons.")
        image = source.convert("RGBA")
        frames = {size: png_frame(image, size) for size in sizes}

    page_path = ROOT / "src/smart_search/assets/ui/index.html"
    data_uri = "data:image/png;base64," + base64.b64encode(frames[64]).decode("ascii")
    page, replacements = re.subn(
        r'(data-smart-search-icon (?:src|href)=")[^"]*(")',
        lambda match: match[1] + data_uri + match[2],
        page_path.read_text(encoding="utf-8"),
    )
    if replacements != 2:
        raise ValueError("Expected the Web UI favicon and header icon markers.")

    windows_assets = ROOT / "desktop/windows/Assets"
    windows_assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, windows_assets / "smart-search.png")
    (windows_assets / "smart-search.ico").write_bytes(windows_icon(frames))
    (ROOT / "desktop/packaging/macos/SmartSearch.icns").write_bytes(macos_icon(frames))
    page_path.write_text(page, encoding="utf-8", newline="\n")
    print("Generated Windows PNG/ICO, fallback macOS ICNS and Web icons; source artwork is unchanged.")


if __name__ == "__main__":
    main()
