"""登場人物の 64x64 ドット絵立ち絵(リアル寄り)を生成する。

Pyxel の標準 16 色パレットだけを使う。
頭・首・肩を楕円体として扱い、左上前方からの光でランバート陰影を付け、
色の段階(ランプ)を 4x4 のベイヤー行列でディザリングする。

出力:
  assets/portraits/<id>.png        64x64 の原寸
  docs/img/portraits/<id>.png      企画書用に 4 倍へ拡大したもの
  docs/img/portraits_sheet.png     確認用の一覧
  assets/portraits.py              Pyxel で読み込むための文字列データ
"""

import math
from pathlib import Path

from PIL import Image

W = H = 64

PALETTE = [
    0x000000, 0x2B335F, 0x7E2072, 0x19959C, 0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9, 0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0,
]
BLACK, NAVY, PURPLE, TEAL, BROWN, DBLUE, LBLUE, WHITE = range(8)
RED, ORANGE, YELLOW, LIME, CYAN, GRAY, PINK, PEACH = range(8, 16)

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# 色の段階(暗 → 明)
SKIN = [BROWN, ORANGE, PEACH, PEACH]
SKIN_PALE = [BROWN, PINK, PEACH, WHITE]
HAIR_BROWN = [BLACK, BROWN, BROWN, ORANGE]
HAIR_BLACK = [BLACK, BLACK, NAVY, DBLUE]
HAIR_BLOND = [BROWN, ORANGE, YELLOW, WHITE]
HAIR_GRAY = [NAVY, DBLUE, GRAY, WHITE]
HAIR_WHITE = [DBLUE, GRAY, WHITE, WHITE]
CLOTH_BLACK = [BLACK, BLACK, NAVY, DBLUE]
CLOTH_NAVY = [BLACK, NAVY, DBLUE, CYAN]
CLOTH_ORANGE = [BROWN, ORANGE, ORANGE, YELLOW]
CLOTH_RED = [PURPLE, RED, RED, PINK]
CLOTH_WHITE = [GRAY, GRAY, WHITE, WHITE]
CLOTH_GRAY = [NAVY, DBLUE, GRAY, WHITE]
CLOTH_PURPLE = [BLACK, NAVY, PURPLE, RED]
CLOTH_DBLUE = [NAVY, DBLUE, CYAN, LBLUE]
METAL = [NAVY, DBLUE, GRAY, WHITE]

LIGHT = (-0.4, -0.45, 0.8)
_n = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _n for v in LIGHT)

HX, HY, HRX, HRY = 31.5, 24.5, 11.5, 14.0  # 頭の中心と半径


class Canvas:
    def __init__(self):
        self.px = [[BLACK] * W for _ in range(H)]
        self.fig = [[False] * W for _ in range(H)]

    def put(self, x, y, c, fig=True):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c
            if fig:
                self.fig[y][x] = True

    def get(self, x, y):
        return self.px[y][x]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def sym(self, x, y, c):
        self.put(x, y, c)
        self.put(63 - x, y, c)


DITHER = 0.35  # 1.0 で全面ディザ、0 でディザなし。小さいほど境目だけに出る


def dither(ramp, v, x, y, strength=None):
    s = DITHER if strength is None else strength
    v = min(max(v, 0.0), 0.999)
    t = v * (len(ramp) - 1)
    base = int(t)
    frac = t - base
    threshold = 0.5 + ((BAYER[y % 4][x % 4] + 0.5) / 16 - 0.5) * s
    if frac > threshold and base + 1 < len(ramp):
        base += 1
    return ramp[base]


def lambert(nx, ny, nz, ambient=0.3):
    d = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    return ambient + (1 - ambient) * max(0.0, d)


def ellipsoid(cv, cx, cy, rx, ry, ramp, mask=None, egg=0.0, bias=0.0, texture=None, ymin=0, ymax=H - 1):
    """楕円体を陰影付きで描く。egg > 0 で下すぼまり(あご)になる。"""
    for y in range(max(0, ymin), min(H - 1, ymax) + 1):
        for x in range(W):
            ny = (y + 0.5 - cy) / ry
            erx = rx * (1 - egg * max(0.0, ny) ** 2)
            nx = (x + 0.5 - cx) / erx
            d = nx * nx + ny * ny
            if d > 1:
                continue
            if mask is not None and not mask(x, y, nx, ny):
                continue
            nz = math.sqrt(max(0.0, 1 - d))
            v = lambert(nx, ny, nz) + bias
            if texture is not None:
                v += texture(x, y)
            cv.put(x, y, dither(ramp, v, x, y))


def background(cv, top, bottom):
    for y in range(H):
        for x in range(W):
            v = 1.35 - 1.1 * y / (H - 1)
            vx = abs(x - 31.5) / 32
            v -= 0.35 * vx * vx
            cv.put(x, y, dither([bottom, top], v, x, y, strength=0.6), fig=False)


def strands(freq=1.1, amp=0.14):
    return lambda x, y: amp * math.sin(x * freq + y * 0.35) - 0.04 * ((x * 3 + y) % 7 == 0)


# ---- 体 ------------------------------------------------------------------

def torso(cv, ramp, width=29):
    ellipsoid(cv, 31.5, 71, width, 28, ramp, ymin=43)


def neck(cv, skin):
    for y in range(33, 48):
        for x in range(26, 38):
            nx = (x + 0.5 - 31.5) / 6
            v = lambert(nx, 0.0, math.sqrt(max(0, 1 - nx * nx))) - 0.15
            if y < 40:
                v -= 0.25  # あごの影
            cv.put(x, y, dither(skin, v, x, y))


def head(cv, skin):
    ellipsoid(cv, HX, HY, HRX, HRY, skin, egg=0.26, bias=0.1)
    # 耳
    for side in (-1, 1):
        ex = HX + side * (HRX - 0.5)
        ellipsoid(cv, ex, 26, 2.2, 3.6, skin, bias=-0.15 if side > 0 else 0.0)
        cv.put(int(ex) + (1 if side > 0 else 0), 26, skin[0])


def face(cv, skin, iris=BROWN, brow=BLACK, mouth="neutral", eyes="open", lip=None):
    s0, s1 = skin[0], skin[1]
    lip = lip if lip is not None else s1
    ey = 25
    # 目のくぼみの影
    for side in (-1, 1):
        cx = 31.5 + side * 5
        for y in range(ey - 1, ey + 3):
            for x in range(int(cx) - 3, int(cx) + 4):
                if ((x + 0.5 - cx) / 3.6) ** 2 + ((y + 0.5 - ey - 0.7) / 2.0) ** 2 <= 1:
                    if (x + y) % 2 == 0 or side > 0:
                        cv.put(x, y, s1 if cv.get(x, y) != s0 else s0)
    # 目
    for side in (-1, 1):
        cx = 31 + side * 5 if side < 0 else 32 + 5
        x0 = cx - 2
        if eyes == "closed":
            for x in range(x0, x0 + 5):
                cv.put(x, ey + 1, s0)
            continue
        for x in range(x0, x0 + 5):
            cv.put(x, ey, BLACK if eyes != "sleepy" else s0)
        if eyes == "sleepy":
            for x in range(x0, x0 + 5):
                cv.put(x, ey + 1, BLACK)
            cv.put(x0 + 2, ey + 1, iris)
            continue
        cv.put(x0, ey + 1, WHITE)
        cv.put(x0 + 1, ey + 1, iris)
        cv.put(x0 + 2, ey + 1, BLACK)
        cv.put(x0 + 3, ey + 1, iris)
        cv.put(x0 + 4, ey + 1, WHITE if side < 0 else GRAY)
        cv.put(x0 + 1, ey, iris)
        cv.put(x0 + 2, ey, iris if eyes == "wide" else BLACK)
        cv.put(x0 + 1, ey + 1, WHITE)  # 瞳のハイライト
        cv.put(x0 + 1, ey + 1, iris)
        cv.put(x0 + 2, ey + 1, BLACK)
        for x in range(x0 + 1, x0 + 4):
            cv.put(x, ey + 2, s1)
    # 眉
    for side in (-1, 1):
        cx = 31 + side * 5 if side < 0 else 37
        for i, x in enumerate(range(cx - 3, cx + 3)):
            yy = ey - 3 + (1 if (side < 0 and i == 0) or (side > 0 and i == 5) else 0)
            cv.put(x, yy, brow)
            if 1 <= i <= 4:
                cv.put(x, yy - 1, brow)
    # 鼻
    for y in range(ey + 1, ey + 6):
        cv.put(33, y, s1)
        cv.put(31, y, skin[-1])
    cv.put(34, ey + 5, s0)
    cv.put(34, ey + 6, s0)
    cv.put(33, ey + 6, s1)
    cv.put(30, ey + 7, s0)
    cv.put(33, ey + 7, s0)
    cv.put(31, ey + 8, s1)
    cv.put(32, ey + 8, s1)
    # 口
    my = ey + 10
    if mouth == "neutral":
        for x in range(29, 35):
            cv.put(x, my, s0)
        for x in range(30, 34):
            cv.put(x, my + 1, lip)
    elif mouth == "smile":
        for x in range(29, 35):
            cv.put(x, my, s0)
        cv.put(28, my - 1, s0)
        cv.put(35, my - 1, s0)
        for x in range(30, 34):
            cv.put(x, my + 1, lip)
    elif mouth == "grin":
        cv.put(27, my - 1, s0)
        cv.put(36, my - 1, s0)
        for x in range(28, 36):
            cv.put(x, my, s0)
        for x in range(29, 35):
            cv.put(x, my + 1, WHITE)
        for x in range(29, 35):
            cv.put(x, my + 2, s0)
    elif mouth == "open":
        for x in range(28, 36):
            cv.put(x, my - 1, s0)
        for x in range(29, 35):
            cv.put(x, my, WHITE)
        for y in range(my + 1, my + 3):
            for x in range(29, 35):
                cv.put(x, y, PURPLE)
        for x in range(30, 34):
            cv.put(x, my + 2, RED)
        for x in range(29, 35):
            cv.put(x, my + 3, s0)
    elif mouth == "smirk":
        for x in range(29, 35):
            cv.put(x, my, s0)
        cv.put(35, my - 1, s0)
        for x in range(30, 33):
            cv.put(x, my + 1, lip)


def outline(cv, c=BLACK):
    edge = []
    for y in range(H):
        for x in range(W):
            if cv.fig[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and cv.fig[ny][nx]:
                    edge.append((x, y))
                    break
    for x, y in edge:
        cv.px[y][x] = c


def hair_shell(cv, ramp, mask, grow=1.8, cy_off=-0.8, freq=1.1):
    ellipsoid(cv, HX, HY + cy_off, HRX + grow, HRY + grow, ramp, mask=mask, egg=0.2, texture=strands(freq))


# ---- 人物 ----------------------------------------------------------------

def dylon(skin=SKIN, hair=HAIR_BROWN, cloth=CLOTH_BLACK, bg=(DBLUE, NAVY), iris=TEAL):
    cv = Canvas()
    background(cv, *bg)
    torso(cv, cloth)
    neck(cv, skin)
    # 丸首の襟
    for x in range(24, 40):
        dy = int(3.2 * math.cos((x - 31.5) / 8.5 * math.pi / 2))
        cv.put(x, 45 + dy, cloth[0])
    head(cv, skin)
    face(cv, skin, iris=iris, brow=hair[0], mouth="grin")
    # 短髪。前髪を右へ流す
    hair_shell(cv, hair, lambda x, y, nx, ny: ny < -0.5 + 0.18 * nx or (abs(nx) > 0.86 and ny < 0.02))
    # 胸の X ロゴ
    for i in range(5):
        cv.put(29 + i, 51 + i, GRAY)
        cv.put(33 - i, 51 + i, GRAY)
    return cv


def dylon_ai():
    cv = dylon()
    ramp = [BLACK, NAVY, DBLUE, CYAN, LBLUE, WHITE]
    lum = {c: (0.299 * (PALETTE[c] >> 16 & 255) + 0.587 * (PALETTE[c] >> 8 & 255) + 0.114 * (PALETTE[c] & 255)) / 255
           for c in range(16)}
    for y in range(H):
        for x in range(W):
            if cv.fig[y][x]:
                v = lum[cv.px[y][x]] * 1.25 + 0.12
                if y % 3 == 0:
                    v -= 0.2
                cv.px[y][x] = dither(ramp, v, x, y)
            else:
                cv.px[y][x] = TEAL if (x % 8 == 0 or y % 8 == 0) and (x + y) % 2 == 0 else BLACK
    outline(cv, TEAL)
    return cv


def maya():
    cv = Canvas()
    background(cv, TEAL, NAVY)
    # 後ろ髪
    ellipsoid(cv, HX, 31, 14.5, 21, HAIR_BLACK, texture=strands(1.6, 0.1), ymax=50)
    torso(cv, CLOTH_ORANGE)
    # つなぎの襟
    for i in range(7):
        cv.put(24 + i, 44 + i, WHITE)
        cv.put(39 - i, 44 + i, WHITE)
    neck(cv, SKIN)
    head(cv, SKIN)
    face(cv, SKIN, iris=BROWN, brow=BLACK, mouth="smirk")
    # 前髪(センター分け)と顔まわりの髪
    hair_shell(cv, HAIR_BLACK,
               lambda x, y, nx, ny: (ny < -0.55 + 0.35 * abs(nx) and abs(nx) > 0.06) or (abs(nx) > 0.8 and ny < 0.75),
               freq=1.6)
    # 眼鏡
    for side in (-1, 1):
        x0 = 26 if side < 0 else 34
        for x in range(x0 - 1, x0 + 6):
            cv.put(x, 24, GRAY)
            cv.put(x, 29, GRAY)
        for y in range(24, 30):
            cv.put(x0 - 1, y, GRAY)
            cv.put(x0 + 5, y, GRAY)
    cv.put(31, 25, GRAY)
    cv.put(32, 25, GRAY)
    # 頭の上のゴーグル
    for x in range(21, 43):
        cv.put(x, 13, DBLUE)
    for side in (-1, 1):
        cx = 26.5 if side < 0 else 36.5
        ellipsoid(cv, cx, 12.5, 3.6, 2.6, [NAVY, DBLUE, LBLUE, WHITE])
    return cv


def ken():
    cv = Canvas()
    background(cv, CYAN, DBLUE)
    torso(cv, CLOTH_RED)
    for y in range(46, 64):
        cv.put(31, y, GRAY)
        cv.put(32, y, WHITE if y % 2 else GRAY)
    for i in range(6):
        cv.put(25 + i, 44 + i, CLOTH_RED[3])
        cv.put(38 - i, 44 + i, CLOTH_RED[3])
    neck(cv, SKIN)
    head(cv, SKIN)
    face(cv, SKIN, iris=DBLUE, brow=ORANGE, mouth="open")
    # ツンツンの金髪
    hair_shell(cv, HAIR_BLOND, lambda x, y, nx, ny: ny < -0.45 or (abs(nx) > 0.88 and ny < -0.05))
    for sx, top in ((21, 7), (25, 4), (29, 2), (33, 2), (37, 4), (41, 7)):
        for y in range(top, 14):
            w = (y - top) // 3
            for x in range(sx - w, sx + w + 1):
                v = 0.8 - (y - top) * 0.03 - (0.3 if x > sx else 0)
                cv.put(x, y, dither(HAIR_BLOND, v, x, y))
    # ヘッドセット
    for y in range(20, 32):
        cv.put(19, y, BLACK)
        cv.put(20, y, NAVY)
    ellipsoid(cv, 20, 27, 2.5, 3.5, METAL)
    for i in range(10):
        cv.put(21 + i, 33 + i // 3, GRAY)
    cv.rect(30, 35, 31, 36, BLACK)
    return cv


def sara():
    cv = Canvas()
    background(cv, GRAY, DBLUE)
    torso(cv, CLOTH_NAVY)
    # 白いシャツの V 襟
    for y in range(44, 64):
        half = max(0, (y - 44) // 2)
        for x in range(31 - half // 2, 33 + half // 2):
            if abs(x - 31.5) < 4:
                cv.put(x, y, WHITE if (x + y) % 5 else GRAY)
    neck(cv, SKIN)
    # 後ろ髪(ボブ)
    ellipsoid(cv, HX, 26, 14, 15, HAIR_BROWN, texture=strands(1.4, 0.1), ymax=33,
              mask=lambda x, y, nx, ny: abs(x + 0.5 - HX) > 9.5 or y < 20)
    head(cv, SKIN)
    face(cv, SKIN, iris=BROWN, brow=BROWN, mouth="neutral", lip=RED)
    hair_shell(cv, HAIR_BROWN,
               lambda x, y, nx, ny: ny < -0.38 or (abs(nx) > 0.86 and ny < 0.5),
               grow=2.4, freq=1.4)
    # 前髪をまっすぐ切りそろえる
    for x in range(22, 42):
        cv.put(x, 20, HAIR_BROWN[1])
    # 真珠のイヤリング
    cv.put(20, 32, WHITE)
    cv.put(43, 32, GRAY)
    return cv


def noah():
    cv = Canvas()
    background(cv, NAVY, BLACK)
    # 台
    ellipsoid(cv, 31.5, 60, 14, 5, METAL)
    cv.rect(28, 46, 35, 56, GRAY)
    for y in range(46, 57):
        cv.put(35, y, DBLUE)
    # モニター(外枠は陰影付き)
    for y in range(8, 47):
        for x in range(9, 55):
            nx = (x - 31.5) / 26
            ny = (y - 27) / 22
            v = lambert(nx * 0.6, ny * 0.6, 0.8)
            cv.put(x, y, dither(METAL, v, x, y))
    # 画面
    for y in range(12, 43):
        for x in range(13, 51):
            v = 0.25 + 0.15 * (1 - abs(x - 31.5) / 20) - (0.12 if y % 3 == 0 else 0)
            cv.put(x, y, dither([BLACK, NAVY, DBLUE], v, x, y))
    # 目
    for cx in (24.5, 38.5):
        ellipsoid(cv, cx, 23.5, 4.5, 4.5, [DBLUE, CYAN, LBLUE, WHITE], bias=0.2)
    # 声の波形
    for i in range(22):
        x = 21 + i
        amp = 3 * math.sin(i * 0.9) * math.sin(i / 21 * math.pi)
        cv.put(x, int(34 + amp), LIME)
        cv.put(x, int(34 - amp), TEAL)
    cv.put(51, 44, RED)
    cv.put(50, 44, RED)
    outline(cv, BLACK)
    return cv


def grey():
    cv = Canvas()
    background(cv, LBLUE, DBLUE)
    torso(cv, CLOTH_DBLUE)
    for y in range(44, 64):
        half = (y - 44) // 3
        for x in range(30 - half, 34 + half):
            if abs(x - 31.5) < 5:
                cv.put(x, y, WHITE)
    for y in range(46, 64):
        w = 1 if y < 49 else 2
        for x in range(32 - w, 32 + w):
            cv.put(x, y, dither(CLOTH_RED, 0.5 + 0.2 * ((y % 4) < 2), x, y))
    neck(cv, SKIN)
    head(cv, SKIN)
    face(cv, SKIN, iris=DBLUE, brow=GRAY, mouth="neutral")
    # 口ひげ
    for x in range(28, 36):
        cv.put(x, 35, GRAY if x < 32 else DBLUE)
    for x in range(29, 35):
        cv.put(x, 34, GRAY)
    # 七三分けの白髪まじり
    hair_shell(cv, HAIR_GRAY,
               lambda x, y, nx, ny: ny < -0.52 + (0.12 if nx < -0.35 else 0.0) or (abs(nx) > 0.87 and ny < 0.05),
               grow=1.4)
    # ほうれい線
    cv.put(27, 34, SKIN[1])
    cv.put(36, 34, SKIN[1])
    return cv


def doc_hughes():
    cv = Canvas()
    background(cv, PURPLE, NAVY)
    torso(cv, CLOTH_WHITE)
    for i in range(10):
        cv.put(25 + i // 2, 44 + i, GRAY)
        cv.put(38 - i // 2, 44 + i, GRAY)
    for x, y in ((22, 54), (23, 55), (40, 52), (41, 53), (42, 53)):
        cv.put(x, y, BLACK)
    neck(cv, SKIN)
    # 爆発した白髪(後ろ)
    for cx, cy, r in ((20, 16, 7), (26, 9, 7), (33, 7, 7), (40, 10, 7), (45, 17, 6), (17, 24, 5), (47, 25, 5)):
        ellipsoid(cv, cx, cy, r, r * 0.9, HAIR_WHITE, texture=strands(2.0, 0.18))
    head(cv, SKIN)
    face(cv, SKIN, iris=BROWN, brow=WHITE, mouth="grin")
    hair_shell(cv, HAIR_WHITE, lambda x, y, nx, ny: ny < -0.62, grow=1.2, freq=2.0)
    # 目にかけた溶接ゴーグル
    for x in range(20, 44):
        cv.put(x, 24, BLACK)
    for cx in (26.5, 36.5):
        ellipsoid(cv, cx, 26.5, 4.2, 3.4, [BLACK, BROWN, ORANGE, YELLOW], bias=0.1)
        cv.put(int(cx) - 1, 25, WHITE)
    # すす
    for x, y in ((24, 33), (25, 33), (39, 31), (36, 17), (37, 17)):
        cv.put(x, y, DBLUE)
    return cv


def bolt():
    cv = Canvas()
    background(cv, ORANGE, BROWN)
    torso(cv, CLOTH_GRAY, width=31)
    # ステンレスのエプロン
    for y in range(48, 64):
        for x in range(22, 42):
            v = 0.55 + 0.35 * math.sin((x - 22) / 20 * math.pi) * 0.6 + (0.2 if (x - y) % 9 == 0 else 0)
            cv.put(x, y, dither(METAL, v, x, y))
    neck(cv, SKIN)
    head(cv, SKIN)
    face(cv, SKIN, iris=BROWN, brow=BROWN, mouth="neutral")
    # 濃いひげ
    ellipsoid(cv, HX, 34, 11.5, 8.5, HAIR_BROWN, texture=strands(2.2, 0.12), ymin=30,
              mask=lambda x, y, nx, ny: not (28 <= x <= 35 and 35 <= y <= 37))
    for x in range(29, 35):
        cv.put(x, 36, RED)
    # はね上げた溶接マスク
    ellipsoid(cv, HX, 13, 12.5, 7.5, [NAVY, DBLUE, CYAN, LBLUE], ymax=18)
    for y in range(9, 13):
        for x in range(23, 41):
            cv.put(x, y, BLACK if y in (9, 12) else TEAL)
    cv.put(25, 10, WHITE)
    return cv


def hashimoto():
    cv = Canvas()
    background(cv, LIME, TEAL)
    torso(cv, CLOTH_NAVY)
    # 安全ベストの反射帯
    for y in (52, 53, 58, 59):
        for x in range(8, 56):
            if cv.fig[y][x]:
                cv.put(x, y, YELLOW if (x + y) % 3 else WHITE)
    neck(cv, SKIN)
    head(cv, SKIN)
    face(cv, SKIN, iris=BROWN, brow=BLACK, mouth="smile")
    hair_shell(cv, HAIR_BLACK, lambda x, y, nx, ny: abs(nx) > 0.86 and -0.3 < ny < 0.1)
    # 黄色いヘルメット
    ellipsoid(cv, HX, 17, 13, 10, HAIR_BLOND, ymax=19)
    for x in range(16, 48):
        cv.put(x, 19, dither(HAIR_BLOND, 0.5 - (x - 16) / 60, x, 19))
        cv.put(x, 20, BROWN)
    for y in range(8, 19):
        cv.put(31, y, ORANGE)
        cv.put(32, y, ORANGE)
    # 耳にはさんだ箸
    for i in range(14):
        cv.put(42 + i // 3, 22 + i, BROWN)
        cv.put(43 + i // 3, 22 + i, ORANGE)
    return cv


def mimi():
    cv = Canvas()
    background(cv, NAVY, BLACK)
    # フード
    ellipsoid(cv, HX, 28, 16, 22, CLOTH_PURPLE, ymax=52)
    torso(cv, CLOTH_PURPLE)
    for y in range(48, 62):
        cv.put(28, y, WHITE)
        cv.put(35, y, GRAY)
    # フードの内側
    ellipsoid(cv, HX, 27, 13, 17, [BLACK, BLACK, NAVY])
    neck(cv, SKIN_PALE)
    head(cv, SKIN_PALE)
    face(cv, SKIN_PALE, iris=NAVY, brow=BLACK, mouth="neutral", eyes="sleepy")
    # 目の下のくま
    for x in (26, 27, 28, 35, 36, 37):
        cv.put(x, 29, PINK)
    # 重い前髪
    hair_shell(cv, HAIR_BLACK, lambda x, y, nx, ny: ny < -0.25 or (abs(nx) > 0.82 and ny < 0.5), grow=1.2, freq=1.8)
    # ヘッドホン
    for side in (-1, 1):
        cx = HX + side * 12.5
        ellipsoid(cv, cx, 27, 3.5, 5, [BLACK, NAVY, RED, PINK])
    # エナジードリンク
    for y in range(47, 62):
        for x in range(48, 55):
            v = 0.3 + 0.6 * (1 - abs(x - 50) / 5)
            cv.put(x, y, dither([TEAL, LIME, LIME, WHITE], v, x, y))
    cv.rect(48, 47, 54, 48, GRAY)
    cv.rect(50, 53, 52, 55, BLACK)
    return cv


def gen():
    cv = Canvas()
    background(cv, BROWN, PURPLE)
    torso(cv, CLOTH_DBLUE)
    # つなぎの肩ひもと胸当て
    for y in range(44, 64):
        for x in (20, 21, 42, 43):
            cv.put(x, y, NAVY)
    for y in range(54, 64):
        for x in range(22, 42):
            cv.put(x, y, dither(CLOTH_DBLUE, 0.35, x, y))
    cv.put(21, 54, YELLOW)
    cv.put(42, 54, YELLOW)
    neck(cv, SKIN)
    head(cv, SKIN)
    face(cv, SKIN, iris=BLACK, brow=WHITE, mouth="smile")
    # しわ
    for x in range(27, 37):
        if x % 2:
            cv.put(x, 16, SKIN[1])
            cv.put(x + 1, 18, SKIN[1])
    cv.put(26, 34, SKIN[1])
    cv.put(37, 34, SKIN[1])
    # 白い横髪
    hair_shell(cv, HAIR_WHITE, lambda x, y, nx, ny: abs(nx) > 0.8 and -0.45 < ny < 0.3, grow=1.6, freq=1.8)
    # はちまき
    for x in range(20, 44):
        for y in (19, 20, 21):
            cv.put(x, y, dither(CLOTH_WHITE, 0.7 - (x - 20) / 50, x, y))
    for x in range(22, 42):
        cv.put(x, 20, RED if x % 3 else WHITE)
    for i in range(6):
        cv.put(44 + i, 18 + i // 2, WHITE)
        cv.put(44 + i, 22 + i // 2, GRAY)
    return cv


CHARACTERS = [
    ("dylon", dylon),
    ("maya", maya),
    ("ken", ken),
    ("sara", sara),
    ("noah", noah),
    ("dylon_ai", dylon_ai),
    ("grey", grey),
    ("doc_hughes", doc_hughes),
    ("bolt", bolt),
    ("hashimoto", hashimoto),
    ("mimi", mimi),
    ("gen", gen),
]


def to_image(cv):
    img = Image.new("RGB", (W, H))
    for y in range(H):
        for x in range(W):
            c = PALETTE[cv.px[y][x]]
            img.putpixel((x, y), (c >> 16 & 255, c >> 8 & 255, c & 255))
    return img


def main():
    root = Path(__file__).resolve().parent.parent
    raw_dir = root / "assets" / "portraits"
    big_dir = root / "docs" / "img" / "portraits"
    raw_dir.mkdir(parents=True, exist_ok=True)
    big_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        '"""登場人物の 64x64 立ち絵 (tools/make_portraits.py で自動生成)。',
        "",
        "各行は 64 文字の 16 進数 (Pyxel のパレット番号)。",
        "pyxel.images[n].set(x, y, PORTRAITS[id]) で読み込める。",
        '"""',
        "",
        "PORTRAITS = {",
    ]
    images = []
    for cid, fn in CHARACTERS:
        cv = fn()
        if cid not in ("noah", "dylon_ai"):
            outline(cv, BLACK)
        img = to_image(cv)
        img.save(raw_dir / f"{cid}.png")
        img.resize((W * 4, H * 4), Image.NEAREST).save(big_dir / f"{cid}.png")
        images.append(img)
        lines.append(f'    "{cid}": [')
        for row in cv.px:
            lines.append('        "' + "".join(f"{c:x}" for c in row) + '",')
        lines.append("    ],")
    lines.append("}")
    (root / "assets" / "portraits.py").write_text("\n".join(lines) + "\n", encoding="utf-8")

    cols, scale, pad = 6, 3, 6
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (W * scale + pad) + pad, rows * (H * scale + pad) + pad), (40, 40, 40))
    for i, img in enumerate(images):
        sheet.paste(img.resize((W * scale, H * scale), Image.NEAREST),
                    (pad + (i % cols) * (W * scale + pad), pad + (i // cols) * (H * scale + pad)))
    sheet.save(root / "docs" / "img" / "portraits_sheet.png")


if __name__ == "__main__":
    main()
