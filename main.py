#!/usr/bin/env python3
"""Catalogue photo of an impossible gadget: Dehydrated Water.

Loads assets/gadget.png, scales it to fit within 1024x1024, and writes a
deterministic PNG to /output/entry.png (<= 1,048,576 bytes).
"""
import hashlib
import os
from pathlib import Path

from PIL import Image

SRC = Path(__file__).resolve().parent / "assets" / "gadget.png"
OUT_DIR = Path("/output")
OUT = OUT_DIR / "entry.png"
MAX_DIM = 1024
MAX_BYTES = 1_048_576


def build() -> Path:
    img = Image.open(SRC).convert("RGB")
    if img.width > MAX_DIM or img.height > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Deterministic: fixed compression, no metadata, no timestamps.
    img.save(OUT, format="PNG", optimize=True, compress_level=9)
    # Safety net: if the PNG ever exceeds the byte limit, shrink
    # deterministically in fixed steps until it fits.
    scale = 0.9
    while OUT.stat().st_size > MAX_BYTES and img.width > 256:
        w = max(256, int(img.width * scale))
        h = max(256, int(img.height * scale))
        img = img.resize((w, h), Image.LANCZOS)
        img.save(OUT, format="PNG", optimize=True, compress_level=9)
    return OUT


def main() -> None:
    out = build()
    # Verify from the file, tolerating a transient concurrent write to the
    # shared /output path by another process (retry briefly, then give up
    # loudly rather than printing a wrong size).
    import time

    size = None
    dims = None
    for _ in range(25):
        try:
            size = out.stat().st_size
            with Image.open(out) as im:
                dims = im.size
            if size > 0 and dims:
                break
        except Exception:
            pass
        time.sleep(0.2)
    print(f"wrote {out} {size} bytes {dims[0]}x{dims[1]}")
    assert size is not None and size <= MAX_BYTES, f"output too large: {size} bytes"


if __name__ == "__main__":
    main()
