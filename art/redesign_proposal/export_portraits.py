"""Export the approved 12-character concept sheet as game-sized PNGs.

The 128px portraits are exported first from the 4x3 master. The 64px
portraits are derived from those 128px images, preserving the same poses.
All pixels are mapped to the Pyxel 16-color palette and remain opaque.
Nothing in assets/portraits or the game code is changed.
"""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "character_faces_concept_720_v7.png"
IDS = [
    "dylon", "maya", "ken", "sara",
    "noah", "dylon_ai", "grey", "doc_hughes",
    "bolt", "hashimoto", "mimi", "gen",
]
COLORS = [
    0x000000, 0x2B335F, 0x7E2072, 0x19959C,
    0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9,
    0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0,
]


def palette_image():
    pal = Image.new("P", (1, 1))
    values = []
    for color in COLORS:
        values.extend(((color >> 16) & 255, (color >> 8) & 255, color & 255))
    pal.putpalette(values + [0] * (768 - len(values)))
    return pal


def to_pyxel(image, palette):
    return image.quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB")


def sheet(images, size, name):
    scale = 2 if size == 64 else 1
    tile = size * scale
    pad, label_h, cols = 8, 17, 4
    rows = 3
    canvas = Image.new("RGB", (cols * (tile + pad) + pad,
                               rows * (tile + pad + label_h) + pad), "#000000")
    draw = ImageDraw.Draw(canvas)
    for i, (cid, image) in enumerate(images):
        x = pad + i % cols * (tile + pad)
        y = pad + i // cols * (tile + pad + label_h)
        shown = image.resize((tile, tile), Image.Resampling.NEAREST)
        canvas.paste(shown, (x, y))
        draw.text((x + 2, y + tile + 2), cid, fill="#eeeeee")
    canvas.save(HERE / name)


def main():
    source = Image.open(SOURCE).convert("RGB")
    assert source.size == (1448, 1086), source.size
    cell = source.width // 4
    assert cell == source.height // 3 == 362
    palette = palette_image()
    large, small = [], []
    for i, cid in enumerate(IDS):
        x, y = i % 4 * cell, i // 4 * cell
        crop = source.crop((x, y, x + cell, y + cell))
        portrait_128 = to_pyxel(crop.resize((128, 128), Image.Resampling.BOX), palette)
        portrait_128.save(HERE / f"{cid}_128.png")
        portrait_64 = to_pyxel(portrait_128.resize((64, 64), Image.Resampling.BOX), palette)
        portrait_64.save(HERE / f"{cid}_64.png")
        large.append((cid, portrait_128))
        small.append((cid, portrait_64))
    sheet(large, 128, "portraits_128_sheet.png")
    sheet(small, 64, "portraits_64_sheet.png")


if __name__ == "__main__":
    main()
