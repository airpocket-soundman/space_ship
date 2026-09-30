"""Export the approved 12-character concept sheet as game-sized PNGs.

The 128px portraits are exported first from the 4x3 master. The 64px
portraits are derived from those 128px images, preserving the same poses.
All pixels are mapped to the Pyxel 16-color palette and remain opaque.
Nothing in assets/portraits or the game code is changed.
"""

from pathlib import Path
from collections import deque

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


def foreground_mask(image):
    """Find the blue backdrop from the cell edges without eating blue clothing."""
    w, h = image.size
    pixels = image.load()
    mask = Image.new("L", (w, h), 255)
    out = mask.load()
    seen = bytearray(w * h)
    queue = deque()

    def is_back(x, y):
        r, g, b = pixels[x, y]
        # The backdrop is much darker than the blue shirt and hologram.
        return r < 28 and g < 53 and b < 100 and b > g + 10 and g > r + 7

    def add(x, y):
        key = y * w + x
        if not seen[key] and is_back(x, y):
            seen[key] = 1
            queue.append((x, y))

    for x in range(w):
        add(x, 0)
    for y in range(h):
        add(0, y)
        add(w - 1, y)
    while queue:
        x, y = queue.popleft()
        out[x, y] = 0
        if x > 0: add(x - 1, y)
        if x + 1 < w: add(x + 1, y)
        if y > 0: add(x, y - 1)
        if y + 1 < h: add(x, y + 1)
    # Generated contact sheets can leave dark single-pixel flecks in the
    # backdrop. The figure is the largest connected foreground component.
    visited = bytearray(w * h)
    biggest = []
    for y in range(h):
        for x in range(w):
            key = y * w + x
            if out[x, y] == 0 or visited[key]:
                continue
            visited[key] = 1
            component = []
            parts = deque([(x, y)])
            while parts:
                px, py = parts.popleft()
                component.append((px, py))
                for ny in range(max(0, py - 1), min(h, py + 2)):
                    for nx in range(max(0, px - 1), min(w, px + 2)):
                        nk = ny * w + nx
                        if out[nx, ny] and not visited[nk]:
                            visited[nk] = 1
                            parts.append((nx, ny))
            if len(component) > len(biggest):
                biggest = component
    keep = set(biggest)
    for y in range(h):
        for x in range(w):
            if out[x, y] and (x, y) not in keep:
                out[x, y] = 0
    return mask


def clean_export(image, mask, size, palette):
    art = image.resize((size, size), Image.Resampling.BOX)
    hard_mask = mask.resize((size, size), Image.Resampling.NEAREST)
    clean = Image.composite(art, Image.new("RGB", (size, size), "#2b335f"), hard_mask)
    return to_pyxel(clean, palette), hard_mask


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
        mask = foreground_mask(crop)
        portrait_128, mask_128 = clean_export(crop, mask, 128, palette)
        portrait_128.save(HERE / f"{cid}_128.png")
        portrait_64, _ = clean_export(portrait_128, mask_128, 64, palette)
        portrait_64.save(HERE / f"{cid}_64.png")
        large.append((cid, portrait_128))
        small.append((cid, portrait_64))
    sheet(large, 128, "portraits_128_sheet.png")
    sheet(small, 64, "portraits_64_sheet.png")


if __name__ == "__main__":
    main()
