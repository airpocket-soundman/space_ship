"""タイトルロゴを作る。

python tools/make_logo.py
- art/starx_logo.webp(元の絵、背景は透明)を、ロゴ本来のドットの大きさ(幅 WIDTH ドット)に縮め、
  各ドットを game/logo.py の LOGO_COLORS のどれか(または透明)に振り分ける
- assets/logo.png         ゲーム用。透明の所は黒(透明色)。640x480 / 720x720 では 2 倍、小さい画面では等倍で表示
- docs/img/starx_logo.png 企画書ページ用。透明 PNG を 4 倍に拡大
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.logo import LOGO_COLORS  # noqa: E402

WIDTH = 270  # 元の絵は 1 ドットがおよそ 7 px
WEB_SCALE = 4


def main():
    src = Image.open(ROOT / "art" / "starx_logo.webp").convert("RGBA")
    alpha = np.asarray(src)[..., 3]
    ys, xs = np.nonzero(alpha > 128)
    src = src.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    h = round(src.height * WIDTH / src.width)
    small = np.asarray(src.resize((WIDTH, h), Image.BOX)).astype(float)

    pal = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in LOGO_COLORS], dtype=float)
    rgb = small[..., :3]
    idx = ((rgb[:, :, None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)
    opaque = small[..., 3] >= 128
    out = pal[idx].astype(np.uint8)

    game = out.copy()
    game[~opaque] = 0
    Image.fromarray(game).save(ROOT / "assets" / "logo.png")

    web = np.dstack([out, np.where(opaque, 255, 0).astype(np.uint8)])
    img = Image.fromarray(web, "RGBA")
    img = img.resize((img.width * WEB_SCALE, img.height * WEB_SCALE), Image.NEAREST)
    (ROOT / "docs" / "img").mkdir(exist_ok=True)
    img.save(ROOT / "docs" / "img" / "starx_logo.png")
    print(f"assets/logo.png {WIDTH}x{h} / docs/img/starx_logo.png {img.width}x{img.height}")


if __name__ == "__main__":
    main()
