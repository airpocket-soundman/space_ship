"""タイトルロゴを作る。

python tools/make_logo.py
- art/starx_logo.webp(元の絵、背景は黒)から作る
- assets/logo_<画面サイズ>.png  ゲーム用。画面ごとの幅に直接縮めて等倍で表示する(拡大するとギザギザになるため)。
    game/logo.py の LOGO_COLORS のどれかに振り分ける。暗い所は黒(透明色)なので、宇宙の背景にそのまま重なる
- docs/img/starx_logo.png  企画書ページ用。明るさを透明度にした PNG(光のにじみも背景になじむ)
- docs/favicon.ico, docs/img/icon-180.png  企画書ページのファビコン。ロゴの「X」と軌道の輪を正方形に切り出す
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


FAVICON_BOX = (1190, 0, 1840, 650)  # 元の絵(2000x672)のうち、X と軌道の輪の部分


def main():
    src = Image.open(ROOT / "art" / "starx_logo.webp").convert("RGB")
    icon = src.crop(FAVICON_BOX)
    icon.resize((256, 256), Image.LANCZOS).save(ROOT / "docs" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    icon.resize((180, 180), Image.LANCZOS).save(ROOT / "docs" / "img" / "icon-180.png")
    print("docs/favicon.ico / docs/img/icon-180.png")
    bright = np.asarray(src).max(-1)
    ys, xs = np.nonzero(bright > 24)
    m = 6  # 光のにじみが切れないよう少し余白をとる
    src = src.crop((xs.min() - m, ys.min() - m, xs.max() + 1 + m, ys.max() + 1 + m))
    pal = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in LOGO_COLORS], dtype=float)

    for screen, width in LOGO_WIDTHS.items():
        h = round(src.height * width / src.width)
        small = src.resize((width, h), Image.LANCZOS)
        rgb = np.asarray(small).astype(float)
        idx = ((rgb[:, :, None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)
        out = pal[idx].astype(np.uint8)
        out[rgb.max(-1) < DARK] = 0
        Image.fromarray(out).save(ROOT / "assets" / f"logo_{screen}.png")
        print(f"assets/logo_{screen}.png {width}x{h}")

    h = round(src.height * WEB_WIDTH / src.width)
    web = np.asarray(src.resize((WEB_WIDTH, h), Image.LANCZOS)).astype(float)
    alpha = web.max(-1)  # 黒い所ほど透明に。色は透明度で割り戻して元の明るさを保つ
    rgb = np.clip(web / np.maximum(alpha, 1)[..., None] * 255, 0, 255)
    rgba = np.dstack([rgb, alpha]).astype(np.uint8)
    (ROOT / "docs" / "img").mkdir(exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(ROOT / "docs" / "img" / "starx_logo.png")
    print(f"docs/img/starx_logo.png {WEB_WIDTH}x{h}")


if __name__ == "__main__":
    main()
