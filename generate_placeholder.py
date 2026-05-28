"""
generate_placeholder.py
-----------------------
Creates a simple dark placeholder poster image used when TMDB
poster is unavailable. Run once during project setup.

    python generate_placeholder.py
"""

import os
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

OUT_PATH = os.path.join(os.path.dirname(__file__), "static", "images", "placeholder.png")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if HAS_PIL:
    W, H = 300, 450
    img  = Image.new("RGB", (W, H), color=(18, 18, 26))
    draw = ImageDraw.Draw(img)

    # Gradient-like border
    for i in range(4):
        draw.rectangle([i, i, W-1-i, H-1-i], outline=(50+i*10, 10, 10+i*5))

    # Film icon text (Unicode)
    icon_text  = "🎬"
    title_text = "No Poster"
    sub_text   = "CinematIX"

    # Centre icon
    draw.text((W//2, H//2 - 40), icon_text,  fill=(229, 9,  20),  anchor="mm")
    draw.text((W//2, H//2 + 20), title_text, fill=(180, 180, 180), anchor="mm")
    draw.text((W//2, H//2 + 50), sub_text,   fill=(80,  80,  80),  anchor="mm")

    img.save(OUT_PATH, "PNG")
    print(f"Placeholder saved → {OUT_PATH}")
else:
    # Fallback: minimal 1-pixel PNG (valid but invisible)
    import struct, zlib

    def _png(w, h, colour=(18, 18, 26)):
        def chunk(tag, data):
            c = zlib.crc32(tag + data) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", c)

        raw = b""
        for _ in range(h):
            raw += b"\x00" + bytes(colour) * w

        compressed = zlib.compress(raw)
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", compressed)
            + chunk(b"IEND", b"")
        )

    with open(OUT_PATH, "wb") as f:
        f.write(_png(300, 450))
    print(f"Minimal placeholder saved → {OUT_PATH}")
