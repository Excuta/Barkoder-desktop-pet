"""Regenerate assets/icon.ico from the sitting-south sprite.

Run from project root: uv run python tools/make_icon.py
"""
from pathlib import Path
from PIL import Image

SRC = Path("assets/sitting/rotations/south.png")
DST = Path("assets/icon.ico")
SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> None:
    img = Image.open(SRC).convert("RGBA")
    bbox = img.getbbox()  # auto-crop transparent padding to content
    if bbox is None:
        raise ValueError(f"{SRC} is fully transparent")
    content = img.crop(bbox)

    # Make square with equal padding on both axes (keeps dog centred)
    w, h = content.size
    side = max(w, h)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(content, ((side - w) // 2, (side - h) // 2))

    # Upscale to 256x256 first — Pillow ICO encoder downscales from the input image
    large = square.resize((256, 256), Image.NEAREST)  # NEAREST keeps pixel art crisp
    large.save(DST, format="ICO", sizes=SIZES)

    # Verify
    check = Image.open(DST)
    embedded = list(check.info.get("sizes", {(check.size,)}))
    print(f"Generated {DST}  ({DST.stat().st_size} bytes)  sizes={embedded}  bbox={bbox}")


if __name__ == "__main__":
    main()
