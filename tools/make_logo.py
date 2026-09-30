"""タイトルロゴを作る。

python tools/make_logo.py
- art/starx_logo.png(元の絵、背景は透明)から作る
- assets/logo_<画面サイズ>.png  ゲーム用。画面ごとの幅に直接縮めて等倍で表示する(拡大するとギザギザになるため)。
    黒い宇宙の上に置く前提で黒に重ね、game/logo.py の LOGO_COLORS のどれかに振り分ける。暗い所は黒(透明色)
- docs/img/starx_logo.png  企画書ページ用。なめらかなまま縮めた透明 PNG
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.logo import LOGO_COLORS, LOGO_WIDTHS  # noqa: E402

WEB_WIDTH = 1080
DARK = 48  # 黒に重ねてこれより暗い所は透明にする(0〜255)


def main():
    src = Image.open(ROOT / "art" / "starx_logo.png").convert("RGBA")
    alpha = np.asarray(src)[..., 3]
    ys, xs = np.nonzero(alpha > 16)
    src = src.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    pal = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in LOGO_COLORS], dtype=float)

    for screen, width in LOGO_WIDTHS.items():
        h = round(src.height * width / src.width)
        small = src.resize((width, h), Image.LANCZOS)
        dark = Image.new("RGBA", small.size, (0, 0, 0, 255))
        dark.alpha_composite(small)
        rgb = np.asarray(dark.convert("RGB")).astype(float)
        idx = ((rgb[:, :, None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)
        out = pal[idx].astype(np.uint8)
        out[rgb.max(-1) < DARK] = 0
        Image.fromarray(out).save(ROOT / "assets" / f"logo_{screen}.png")
        print(f"assets/logo_{screen}.png {width}x{h}")

    h = round(src.height * WEB_WIDTH / src.width)
    (ROOT / "docs" / "img").mkdir(exist_ok=True)
    src.resize((WEB_WIDTH, h), Image.LANCZOS).save(ROOT / "docs" / "img" / "starx_logo.png")
    print(f"docs/img/starx_logo.png {WEB_WIDTH}x{h}")


if __name__ == "__main__":
    main()
