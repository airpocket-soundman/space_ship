"""プロローグの背景: 創業キックオフ。

借りたばかりで家具もないビルの一室。むき出しのカーペットの上で、マリアッチ楽団の演奏に合わせて
ディーロンがマラカスを振っている。宇宙企業の創業パーティーの有名な写真へのオマージュ。
640x480 のときの絵を倍率 k で縮め、床を基準に置く(会社画面の格納庫と同じ)。
"""

import math

import pyxel

from . import ui


class Painter:
    """640x480 基準の座標を、倍率 k とずらし (ox, oy) で画面に写して描く。"""

    def __init__(self, k, ox, oy):
        self.k, self.ox, self.oy = k, ox, oy

    def rect(self, x, y, w, h, col):
        k = self.k
        pyxel.rect(self.ox + x * k, self.oy + y * k, max(1, w * k), max(1, h * k), col)

    def circ(self, x, y, r, col):
        pyxel.circ(self.ox + x * self.k, self.oy + y * self.k, max(1, r * self.k), col)

    def line(self, x0, y0, x1, y1, col):
        k = self.k
        pyxel.line(self.ox + x0 * k, self.oy + y0 * k, self.ox + x1 * k, self.oy + y1 * k, col)

    def tri(self, x0, y0, x1, y1, x2, y2, col):
        k, ox, oy = self.k, self.ox, self.oy
        pyxel.tri(ox + x0 * k, oy + y0 * k, ox + x1 * k, oy + y1 * k, ox + x2 * k, oy + y2 * k, col)

    def thick(self, x0, y0, x1, y1, w, col):
        """太さ w の線(腕や楽器の棹)。"""
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        px, py = -dy / n * w / 2, dx / n * w / 2
        self.tri(x0 + px, y0 + py, x1 + px, y1 + py, x1 - px, y1 - py, col)
        self.tri(x0 + px, y0 + py, x1 - px, y1 - py, x0 - px, y0 - py, col)


def person(p, x, feet, shirt, pants, hair, skin=ui.PEACH, h=112, arms="down", sway=0.0,
           tie=None, studs=False, bald=False):
    """人物を 1 人描く。arms: down / clap / guitar / up(右手を挙げる)"""
    top = feet - h
    x += sway
    # 脚と靴
    p.rect(x - 10, feet - 50, 8, 48, pants)
    p.rect(x + 2, feet - 50, 8, 48, pants)
    if studs:  # マリアッチのズボンの飾り
        for yy in range(int(feet - 48), int(feet - 4), 6):
            p.rect(x - 11, yy, 2, 2, ui.WHITE)
            p.rect(x + 9, yy, 2, 2, ui.WHITE)
    p.rect(x - 12, feet - 3, 11, 4, ui.BLACK)
    p.rect(x + 1, feet - 3, 11, 4, ui.BLACK)
    # 胴
    p.rect(x - 13, top + 22, 26, 42, shirt)
    if tie is not None:
        p.tri(x - 6, top + 22, x, top + 27, x - 6, top + 32, tie)
        p.tri(x + 6, top + 22, x, top + 27, x + 6, top + 32, tie)
    # 頭
    p.rect(x - 3, top + 16, 6, 7, skin)
    p.circ(x, top + 10, 9, skin)
    if not bald:
        p.rect(x - 9, top, 18, 6, hair)
        p.rect(x - 9, top + 2, 3, 8, hair)
    # 腕
    sh_y = top + 26
    if arms == "down":
        p.thick(x - 13, sh_y, x - 16, sh_y + 34, 6, shirt)
        p.thick(x + 13, sh_y, x + 16, sh_y + 34, 6, shirt)
    elif arms == "clap":
        up = math.sin(pyxel.frame_count / 5) * 3
        p.thick(x - 13, sh_y, x - 3, sh_y + 20 + up, 6, shirt)
        p.thick(x + 13, sh_y, x + 3, sh_y + 20 + up, 6, shirt)
        p.circ(x, sh_y + 20 + up, 3, skin)


def guitar(p, x, y, body, big=False):
    """胴 (x, y) のギター。big でギタロン(大きいベース)。"""
    r = 13 if big else 10
    p.thick(x + 6, y - 4, x + 34, y - 26, 4, ui.BROWN)
    p.circ(x, y, r, body)
    p.circ(x + r * 0.9, y - r * 0.7, r * 0.7, body)
    p.circ(x + 2, y - 2, 3, ui.BROWN)


def maraca(p, x, y, col):
    p.line(x, y, x, y + 12, ui.BROWN)
    p.circ(x, y, 5, col)
    p.rect(x - 4, y - 1, 8, 2, ui.WHITE)


def draw(top, bottom, k, ox, frame):
    """top〜bottom の範囲にキックオフの場面を描く。"""
    floor_y = bottom - 64 * k  # 床(カーペット)の奥の線
    p = Painter(k, ox, floor_y - 200 * k)  # 基準座標で床の奥の線が y=200
    # 壁と天井
    pyxel.rect(0, top, ui.W, bottom - top, ui.WHITE)
    pyxel.rect(0, top, ui.W, max(2, 10 * k), ui.GRAY)
    ceil = (top - p.oy) / k + 18  # 天井の蛍光灯の高さ(基準座標)
    for lx in range(40, 640, 160):
        p.rect(lx, ceil, 80, 6, ui.LBLUE)
        p.rect(lx + 4, ceil + 1, 72, 4, ui.WHITE)
    # 奥の壁のドアと、ホワイトボード
    for dx in (40, 540):
        p.rect(dx, 90, 44, 110, ui.GRAY)
        p.rect(dx + 36, 145, 4, 4, ui.WHITE)
    bx0, by0, bw, bh = 250, 40, 130, 66
    p.rect(bx0, by0, bw, bh, ui.WHITE)
    p.line(bx0, by0, bx0 + bw, by0, ui.GRAY)
    p.line(bx0, by0 + bh, bx0 + bw, by0 + bh, ui.GRAY)
    p.line(bx0, by0, bx0, by0 + bh, ui.GRAY)
    p.line(bx0 + bw, by0, bx0 + bw, by0 + bh, ui.GRAY)
    ui.text(ox + (bx0 + 10) * k, p.oy + (by0 + 8) * k, "MARS", ui.RED, size=10 if k < 0.9 else 12)
    p.circ(bx0 + 100, by0 + 38, 12, ui.ORANGE)
    p.line(bx0 + 16, by0 + 52, bx0 + 86, by0 + 40, ui.DBLUE)
    # むき出しのカーペット
    pyxel.rect(0, floor_y, ui.W, bottom - floor_y, ui.GRAY)
    pyxel.line(0, floor_y, ui.W, floor_y, ui.DBLUE)
    for i in range(0, 640, 23):  # 織り目
        p.rect(i, 214 + (i * 7) % 40, 2, 1, ui.WHITE)
    beat = math.sin(frame / 8)

    # 後ろで手拍子する創業メンバー
    person(p, 548, 204, ui.YELLOW, ui.NAVY, ui.BLACK, h=100, arms="clap")               # マヤ
    person(p, 614, 206, ui.CYAN, ui.NAVY, ui.BROWN, h=98, arms="clap")                  # サラ
    person(p, 582, 218, ui.BLACK, ui.DBLUE, ui.NAVY, h=104, arms="down", bald=True)     # ノア
    person(p, 180, 208, ui.PINK, ui.DBLUE, ui.YELLOW, h=100, arms="clap")               # ケン

    # マリアッチ楽団(黒い衣装、赤い蝶ネクタイ、ズボンの銀の飾り)
    band = [(236, ui.ORANGE, False), (290, None, False), (346, ui.ORANGE, True), (402, ui.ORANGE, False)]
    for i, (bx, body, big) in enumerate(band):
        sway = beat * 2 if i % 2 == 0 else -beat * 2
        feet = 250 + (6 if i == 3 else 0)
        hair = ui.GRAY if i in (1, 2) else ui.BLACK
        person(p, bx, feet, ui.BLACK, ui.BLACK, hair, arms="guitar", sway=sway, tie=ui.RED, studs=True,
               h=116 if i != 3 else 104)
        top = feet - (116 if i != 3 else 104)
        if body is None:  # バイオリン
            p.rect(bx + sway - 4, top + 30, 12, 20, ui.BROWN)
            p.line(bx + sway - 14, top + 26, bx + sway + 18, top + 44, ui.WHITE)
        else:
            guitar(p, bx + sway - 4, top + 56, body, big)
            p.circ(bx + sway - 10, top + 52, 3, ui.PEACH)
            p.circ(bx + sway + 22, top + 40, 3, ui.PEACH)

    # 片手を突き上げてマラカスを振るディーロン
    dx, feet = 490, 262
    bounce = abs(beat) * 3
    person(p, dx, feet - bounce, ui.DBLUE, ui.NAVY, ui.BROWN, h=128, arms="none")
    top = feet - bounce - 128
    shake = math.sin(frame / 3) * 4
    p.thick(dx + 13, top + 26, dx + 30, top - 8, 6, ui.DBLUE)       # 挙げた右腕
    p.circ(dx + 31, top - 10, 3, ui.PEACH)
    maraca(p, dx + 31 + shake, top - 26, ui.RED)
    p.thick(dx - 13, top + 26, dx - 26, top + 44, 6, ui.DBLUE)      # 左腕
    p.circ(dx - 27, top + 46, 3, ui.PEACH)
    maraca(p, dx - 30 - shake * 0.5, top + 30, ui.LIME)

    # 音符
    for i in range(3):
        t = (frame / 50 + i / 3) % 1
        nx, ny = 220 + i * 80 + math.sin(t * 6) * 8, 150 - t * 60
        if t < 0.85:
            p.circ(nx, ny, 3, ui.NAVY)
            p.line(nx + 3, ny, nx + 3, ny - 12, ui.NAVY)
            p.line(nx + 3, ny - 12, nx + 8, ny - 9, ui.NAVY)
