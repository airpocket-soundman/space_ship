"""タイトル画面の素材を生成する。

- assets/title_bg.png   320x240(2倍表示)の星・月・火星。地球は game/title_earth.py が毎フレーム描く
- assets/title_bg_sq.png 360x360 の同じ背景(720x720 では2倍、360x360 では等倍で表示)
- assets/earth_tex.png  地表マップ。横は軌道方向 90°ぶん(左右がつながる)、縦は軌道からの横方向 -24〜+24°
    色が地表の種類を表す: DBLUE=海 / TEAL=陸 / BROWN=砂漠 / GRAY=薄い雲 / WHITE=厚い雲 / YELLOW=都市のある陸
"""

from pathlib import Path

import numpy as np
from PIL import Image

W, H = 320, 240
TW, TH = 2048, 546
PALETTE = [
    0x000000, 0x2B335F, 0x7E2072, 0x19959C, 0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9, 0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0,
]
BLACK, NAVY, PURPLE, TEAL, BROWN, DBLUE, LBLUE, WHITE = range(8)
RED, ORANGE, YELLOW, LIME, CYAN, GRAY, PINK, PEACH = range(8, 16)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])

rng = np.random.default_rng(11)


def hash2(a, b, seed):
    n = (a * 374761393 + b * 668265263 + seed * 144269504) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def value_noise(x, y, seed, period=None):
    xi, yi = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    xf, yf = x - xi, y - yi
    x0, x1 = xi, xi + 1
    if period:
        x0, x1 = x0 % period, x1 % period
    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)
    a, b = hash2(x0, yi, seed), hash2(x1, yi, seed)
    c, d = hash2(x0, yi + 1, seed), hash2(x1, yi + 1, seed)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def fbm(x, y, seed, octaves=5, period=None):
    total, amp, freq, norm = 0.0, 0.5, 1, 0.0
    for i in range(octaves):
        p = period * freq if period else None
        total = total + amp * value_noise(x * freq, y * freq, seed + i * 17, p)
        norm += amp
        amp *= 0.5
        freq *= 2
    return total / norm


def ramp(colors, v, b):
    colors = np.array(colors)
    t = np.clip(v, 0, 0.999) * (len(colors) - 1)
    base = np.floor(t).astype(int)
    frac = t - base
    th = (b + 0.5) / 16
    base = np.where((frac > th) & (base + 1 < len(colors)), base + 1, base)
    return colors[base]


def make_texture():
    """地表マップ。横 TW が軌道方向 90°(約 1 万 km)、縦 TH が 24°。"""
    vs, us = np.mgrid[0:TH, 0:TW].astype(float)
    P = 10  # 横一周(90°)あたりのノイズの格子数
    x = us / TW * P
    y = vs / TW * P
    land = fbm(x, y + 3, 1, 7, P) > 0.53
    desert = fbm(x * 2, y * 2 + 7, 4, 4, P * 2) > 0.6
    swirl = fbm(x * 0.5, y * 0.5 + 11, 21, 3, P // 2) * 6.0
    cv = fbm(x * 4 + np.sin(swirl) * 0.8, y * 7 + np.cos(swirl) * 0.8, 7, 6, P * 4)
    lights = land & (fbm(x * 16, y * 16, 33, 2, P * 16) > 0.6) & (rng.random((TH, TW)) < 0.12)
    mat = np.full((TH, TW), DBLUE)
    mat[land] = TEAL
    mat[land & desert] = BROWN
    mat[lights] = YELLOW
    mat[cv > 0.6] = GRAY
    mat[cv > 0.66] = WHITE
    return mat


def make_bg(w, h, rng, n_stars, moon, mars):
    """星・月・火星の背景。moon / mars は (x, y, 半径)。"""
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    bx = BAYER[ys.astype(int) % 4, xs.astype(int) % 4]
    img = np.full((h, w), BLACK, dtype=int)

    # 星
    sx, sy = rng.integers(0, w, n_stars), rng.integers(0, h, n_stars)
    img[sy, sx] = rng.choice([GRAY, WHITE, LBLUE, DBLUE], n_stars, p=[0.35, 0.25, 0.15, 0.25])

    # 月
    mx, my, mr = moon
    m = np.hypot(xs - mx, ys - my) <= mr
    s = 0.75 - ((xs - mx) * 0.5 + (ys - my) * 0.4) / mr * 0.5 + (fbm(xs / 4, ys / 4, 5, 3) - 0.5) * 0.9
    img[m] = ramp([NAVY, DBLUE, GRAY, WHITE], s, bx)[m]

    # 火星
    fx, fy, fr = mars
    m = np.hypot(xs - fx, ys - fy) <= fr
    s = 0.8 - ((xs - fx) * 0.6 + (ys - fy) * 0.3) / fr * 0.5 + (fbm(xs / 5, ys / 5, 9, 3) - 0.5) * 0.8
    img[m] = ramp([PURPLE, BROWN, ORANGE, PEACH], s, bx)[m]
    return img


def main():
    root = Path(__file__).resolve().parent.parent
    rgb = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in PALETTE], dtype=np.uint8)
    img = make_bg(W, H, rng, 260, (34, 28, 13), (297, 50, 13))
    Image.fromarray(rgb[img]).save(root / "assets" / "title_bg.png")
    Image.fromarray(rgb[make_texture()]).save(root / "assets" / "earth_tex.png")
    # 正方形の画面(720x720 / 360x360)用。星の密度は 320x240 と同じ
    img = make_bg(360, 360, np.random.default_rng(12), 440, (34, 28, 13), (337, 50, 13))
    Image.fromarray(rgb[img]).save(root / "assets" / "title_bg_sq.png")


if __name__ == "__main__":
    main()
