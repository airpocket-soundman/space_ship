"""タイトル画面の背景(320x240、2倍表示)を生成する。

星空・月・火星・夜明けの地球(大気の光・雲・都市の灯り)を
Pyxel の標準 16 色だけで描き、assets/title_bg.png に保存する。
"""

from pathlib import Path

import numpy as np
from PIL import Image

W, H = 320, 240
PALETTE = [
    0x000000, 0x2B335F, 0x7E2072, 0x19959C, 0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9, 0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0,
]
BLACK, NAVY, PURPLE, TEAL, BROWN, DBLUE, LBLUE, WHITE = range(8)
RED, ORANGE, YELLOW, LIME, CYAN, GRAY, PINK, PEACH = range(8, 16)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32

rng = np.random.default_rng(11)


def value_noise(x, y, seed):
    """格子の値をなめらかに補間したノイズ(0〜1)。"""
    xi, yi = np.floor(x).astype(int), np.floor(y).astype(int)
    xf, yf = x - xi, y - yi

    def h(a, b):
        n = (a * 374761393 + b * 668265263 + seed * 144269504) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0

    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)
    a, b = h(xi, yi), h(xi + 1, yi)
    c, d = h(xi, yi + 1), h(xi + 1, yi + 1)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def fbm(x, y, seed, octaves=5):
    total, amp, freq, norm = 0.0, 0.5, 1.0, 0.0
    for i in range(octaves):
        total = total + amp * value_noise(x * freq, y * freq, seed + i * 17)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


def ramp_pick(ramp, v, bx):
    """v(0〜1)を色の段階に割り当て、ベイヤー行列でディザする。"""
    ramp = np.array(ramp)
    t = np.clip(v, 0, 0.999) * (len(ramp) - 1)
    base = np.floor(t).astype(int)
    frac = t - base
    base = np.where((frac > bx) & (base + 1 < len(ramp)), base + 1, base)
    return ramp[base]


def main():
    ys, xs = np.mgrid[0:H, 0:W].astype(float)
    bx = BAYER[ys.astype(int) % 4, xs.astype(int) % 4]
    img = np.full((H, W), BLACK, dtype=int)

    # 星
    n = 260
    sx, sy = rng.integers(0, W, n), rng.integers(0, H, n)
    img[sy, sx] = rng.choice([GRAY, WHITE, LBLUE, DBLUE], n, p=[0.35, 0.25, 0.15, 0.25])

    # 月(左上)
    mx, my, mr = 34, 28, 13
    d = np.hypot(xs - mx, ys - my)
    moon = d <= mr
    shade = 0.75 - ((xs - mx) * 0.5 + (ys - my) * 0.4) / mr * 0.5 + (fbm(xs / 4, ys / 4, 5, 3) - 0.5) * 0.9
    img[moon] = ramp_pick([NAVY, DBLUE, GRAY, WHITE], shade, bx)[moon]

    # 火星(右)
    fx, fy, fr = 297, 50, 13
    d = np.hypot(xs - fx, ys - fy)
    mars = d <= fr
    shade = 0.8 - ((xs - fx) * 0.6 + (ys - fy) * 0.3) / fr * 0.5 + (fbm(xs / 5, ys / 5, 9, 3) - 0.5) * 0.8
    img[mars] = ramp_pick([PURPLE, BROWN, ORANGE, PEACH], shade, bx)[mars]

    # 地球
    cx, cy, R = 160.0, 438.0, 332.0
    nx, ny = (xs - cx) / R, (ys - cy) / R
    r2 = nx * nx + ny * ny
    earth = r2 <= 1
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    # 球面の歪みを付けた座標でノイズを引く
    k = 1.0 / (nz + 0.25)
    u = nx * k * 3.2 + 10
    v = ny * k * 3.2 + 5
    land = fbm(u, v, 1) > 0.57
    desert = fbm(u * 1.7, v * 1.7, 4, 3) > 0.62
    # 渦を巻く雲
    swirl = fbm(u * 0.6, v * 0.6, 21, 3) * 6.0
    cloud_v = fbm(u * 2.4 + np.sin(swirl), v * 4.5 + np.cos(swirl), 7)
    cloud = cloud_v > 0.6
    # 光: 上(地平線の向こう)からの朝日。下ほど夜になる
    sun = np.array([0.0, -0.55, -0.83])
    sun = sun / np.linalg.norm(sun)
    light = nx * sun[0] + ny * sun[1] + nz * sun[2]
    light = np.clip(light * 2.2 + 0.18, 0, 1)

    ocean = ramp_pick([NAVY, NAVY, DBLUE, DBLUE, CYAN], light * 0.95, bx)
    landc = ramp_pick([NAVY, TEAL, TEAL, LIME], light, bx)
    desc = ramp_pick([NAVY, BROWN, BROWN, ORANGE], light, bx)
    cloudc = ramp_pick([DBLUE, DBLUE, GRAY, WHITE, WHITE], light * 0.85 + (cloud_v - 0.6) * 2.0 + 0.15, bx)

    col = np.where(land, np.where(desert, desc, landc), ocean)
    col = np.where(cloud, cloudc, col)
    # 夜側の都市の灯り
    lights = land & ~cloud & (light < 0.25) & (fbm(u * 6, v * 6, 33, 2) > 0.58) & (rng.random((H, W)) < 0.4)
    col = np.where(lights, np.where(rng.random((H, W)) < 0.5, YELLOW, ORANGE), col)
    img[earth] = col[earth]

    # 大気の縁の光(地球の外側の細い帯と、縁の内側)
    dist = np.sqrt(r2) * R - R  # 縁からの距離 [px]
    top_weight = np.clip(-ny, 0, 1)  # 上の縁ほど明るい
    halo = (dist > 0) & (dist < 7)
    glow = (1 - dist / 7) * (0.55 + 0.45 * top_weight)
    img[halo] = ramp_pick([BLACK, NAVY, DBLUE, CYAN, LBLUE], glow, bx)[halo]
    rim = earth & (dist > -5)
    rim_v = (1 + dist / 5) * (0.5 + 0.5 * top_weight) + 0.2
    rim_c = ramp_pick([DBLUE, CYAN, LBLUE, WHITE], rim_v, bx)
    img[rim & (rim_v > 0.45)] = rim_c[rim & (rim_v > 0.45)]

    out = Image.new("RGB", (W, H))
    rgb = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in PALETTE], dtype=np.uint8)
    out = Image.fromarray(rgb[img])
    root = Path(__file__).resolve().parent.parent
    out.save(root / "assets" / "title_bg.png")
    out.resize((W * 2, H * 2), Image.NEAREST).save(root / "tools" / "title_bg_preview.png")


if __name__ == "__main__":
    main()
