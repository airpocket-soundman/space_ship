"""格納庫に立てる Eagle 9 の絵を作る。

python tools/make_rockets.py  → assets/rockets/eagle9_<画面サイズ>.png
art/redesign_proposal/falcon9_720.png(新しい機体デザイン案)を、画面サイズごとの格納庫の高さに合わせて縮め、
Pyxel 標準の 16 色にそろえる。透明な部分は紫(色番号 2)で塗り、ゲーム側で抜き色にする。
"""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game import ui  # noqa: E402
from game.scene_office import Layout  # noqa: E402

SRC = ROOT / "art" / "redesign_proposal" / "falcon9_720.png"
OUT = ROOT / "assets" / "rockets"
HEIGHT = 200  # 640x480 のときの高さ [px]。scene_office.draw_craft_in_hangar と合わせる
COLORS = [
    0x000000, 0x2B335F, 0x7E2072, 0x19959C, 0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9, 0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0,
]
KEY = 2  # 抜き色(紫)


def palette_image():
    pal = Image.new("P", (1, 1))
    values = []
    for color in COLORS:
        values.extend(((color >> 16) & 255, (color >> 8) & 255, color & 255))
    pal.putpalette(values + [0] * (768 - len(values)))
    return pal


def main():
    OUT.mkdir(exist_ok=True)
    src = Image.open(SRC).convert("RGBA")
    src = src.crop(src.getbbox())
    pal = palette_image()
    key = tuple((COLORS[KEY] >> s) & 255 for s in (16, 8, 0))
    for screen in ui.SCREENS:
        ui.set_screen(screen)
        h = round(HEIGHT * Layout().k)
        w = max(1, round(src.width * h / src.height))
        small = src.resize((w, h), Image.Resampling.BOX)
        rgb = small.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE)
        out = rgb.load()
        alpha = small.getchannel("A").load()
        for y in range(h):
            for x in range(w):
                if alpha[x, y] < 128:
                    out[x, y] = KEY
                elif out[x, y] == KEY:
                    out[x, y] = 1  # 機体の色が抜き色に化けたら、紺にする
        rgb.convert("RGB").save(OUT / f"eagle9_{screen}.png")
        assert key  # 抜き色は game/ui.py の PURPLE
        print(f"assets/rockets/eagle9_{screen}.png  {w}x{h}")


if __name__ == "__main__":
    main()
