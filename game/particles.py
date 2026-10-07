"""炎・煙・爆発などのパーティクル。

元になったプロトタイプ(prototype/rocket_thrast_control.py)と同じ考え方:
  - エンジンの炎は、ノズルから後ろへ飛ぶ短命の粒
  - 消えた炎の粒は煙になって残る
  - 炎が地面に当たると、煙になって横へ広がり、地面で跳ねる
  - スラスターは、機体の横から出る寿命の短い粒
  - 打ち上げで地面に当たった噴射は、たくさんの煙の粒になって左右へ広がり、巻き上がる(機体より手前に描き、機体を隠す)
重くならないように、粒の総数に上限を設け、古い煙から捨てる。座標はワールド座標 [m]。
"""

import math
import random

import pyxel

from . import ui

DT = 1 / 60

# 粒 1 個は [x, y, vx, vy, 残り寿命, 元の寿命, 色の種類]
# 炎の色(若い → 古い)。大気中は黄 → 橙 → 赤、真空では白 → 水色 → 青
FLAME_AIR = (ui.YELLOW, ui.ORANGE, ui.RED)
FLAME_VAC = (ui.WHITE, ui.LBLUE, ui.DBLUE)
FLAME_HOT = (ui.WHITE, ui.PINK, ui.ORANGE)  # 再突入の加熱

MAX_FLAME = 260
MAX_SMOKE = 420
MAX_SPARK = 420
MAX_BILLOW = 900


class Particles:
    def __init__(self):
        self.flames = []
        self.smokes = []  # 色の種類: 0 = 白い煙 / 1 = 黒い煙
        self.sparks = []  # 色の種類 = 色番号(爆発の火花・水しぶき・破片)
        self.billows = []  # 巻き上がる煙の粒 [x, y, vx, vy, 残り寿命, 元の寿命, 最初の半径, 最後の半径]
        self.ground = None  # x [m] → 地表(甲板)の高さ [m]。None なら高さ 0

    def clear(self):
        self.flames.clear()
        self.smokes.clear()
        self.sparks.clear()
        self.billows.clear()

    def count(self):
        return len(self.flames) + len(self.smokes) + len(self.sparks) + len(self.billows)

    # ---- 出す ----
    def flame(self, x, y, vx, vy, angle, n, speed, spread, width, life, palette=0, smoke=0.0):
        """ノズルの炎。angle は噴き出す向き(鉛直下向きが π)、width はノズルの幅 [m]。

        smoke: 消えた粒が煙になる割合(0〜1)。1 フレームのあいだに出た粒が途切れて見えないよう、
        出した時刻を少しずつずらして並べる(プロトタイプの、前フレームとの間を埋めるやり方と同じ)。
        """
        add = self.flames.append
        rnd = random.random
        ca, sa = math.cos(angle), math.sin(angle)
        for _ in range(n):
            a = angle + (rnd() * 2 - 1) * spread
            sp = speed * (0.55 + 0.45 * rnd())
            dx, dy = math.sin(a) * sp, math.cos(a) * sp
            off = (rnd() - 0.5) * width
            u = rnd() * DT  # このフレームのどの時点で出た粒か
            lf = life * (0.6 + 0.8 * rnd())
            add([x + ca * off + dx * u, y - sa * off + dy * u, vx + dx, vy + dy, lf, lf, palette, smoke])
        if len(self.flames) > MAX_FLAME:
            del self.flames[:len(self.flames) - MAX_FLAME]

    def puff(self, x, y, vx, vy, n, speed=4.0, life=70, dark=0):
        """その場に広がる煙(段分離・着地・火災など)。"""
        add = self.smokes.append
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.2, 1.0) * speed
            lf = life * random.uniform(0.6, 1.3)
            add([x, y, vx + math.cos(a) * sp, vy + math.sin(a) * sp, lf, lf, dark])

    def billow(self, x, y, vx, vy, life, r0, r1):
        """巻き上がる煙の粒を 1 つ出す。半径 [m] は r0 から r1 へ、だんだん膨らむ。"""
        self.billows.append([x, y, vx, vy, life, life, r0, r1])
        if len(self.billows) > MAX_BILLOW:
            del self.billows[:len(self.billows) - MAX_BILLOW]

    def jet(self, x, y, vx, vy, angle, n=3, speed=30.0):
        """スラスター(RCS)の噴射。寿命の短い白い粒。"""
        add = self.sparks.append
        for _ in range(n):
            a = angle + random.uniform(-0.17, 0.17)
            sp = speed * random.uniform(0.6, 1.0)
            lf = random.randint(3, 6)
            add([x, y, vx + math.sin(a) * sp, vy + math.cos(a) * sp, lf, lf, ui.WHITE, 0.0])

    def burst(self, x, y, vx, vy, n, speed, life, colors, gravity=9.8, drag=0.03):
        """四方へ飛び散る粒(爆発の火花・破片・水しぶき)。"""
        add = self.sparks.append
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.1, 1.0) * speed
            lf = life * random.uniform(0.4, 1.2)
            add([x, y, vx + math.cos(a) * sp, vy + math.sin(a) * sp, lf, lf, random.choice(colors), gravity, drag])

    def explode(self, x, y, vx, vy):
        """機体の爆発: 火花・炎・黒い煙。"""
        self.burst(x, y, vx * 0.3, vy * 0.3, 240, 45.0, 55, (ui.RED, ui.ORANGE, ui.YELLOW, ui.WHITE), 0.0)
        self.burst(x, y, vx * 0.3, vy * 0.3, 40, 22.0, 120, (ui.GRAY, ui.WHITE, ui.DBLUE), 9.8, 0.01)
        self.puff(x, y, vx * 0.2, vy * 0.2, 50, 10.0, 150, dark=1)
        self.puff(x, y, vx * 0.2, vy * 0.2, 30, 16.0, 110)

    def splash(self, x, y, n=60):
        """着水の水しぶき。"""
        add = self.sparks.append
        for _ in range(n):
            a = random.uniform(-1.1, 1.1)
            sp = random.uniform(6.0, 26.0)
            lf = random.uniform(25, 60)
            add([x + random.uniform(-3, 3), y + 0.5, math.sin(a) * sp, math.cos(a) * sp, lf, lf,
                 random.choice((ui.WHITE, ui.CYAN, ui.LBLUE)), 9.8, 0.01])

    def shift(self, dx, dy):
        """すべての粒を同じだけ動かす。"""
        for group in (self.flames, self.smokes, self.sparks, self.billows):
            for p in group:
                p[0] += dx
                p[1] += dy

    # ---- 動かす ----
    def update(self, cam_x, cam_y, reach, air=1.0):
        """reach: カメラからこの距離 [m] より離れた粒は捨てる。air: 空気の濃さ(0〜1)。"""
        ground = self.ground
        rnd = random.random
        smokes = self.smokes
        add_smoke = smokes.append

        keep = []
        add = keep.append
        for p in self.flames:
            p[4] -= 1
            x = p[0] + p[2] * DT
            y = p[1] + p[3] * DT
            gy = ground(x) if ground else 0.0
            if y <= gy:
                # 地面(甲板・海面)に当たった炎は、煙になって横へ広がる
                if rnd() < 0.3:
                    sp = (abs(p[3]) * 0.12 + 3.0) * (0.4 + rnd())
                    lf = 50 + 70 * rnd()
                    add_smoke([x, gy + 0.3, sp if rnd() < 0.5 else -sp, 1.0 + 5.0 * rnd(), lf, lf, 0])
                continue
            if p[4] <= 0:
                # 消えた炎は煙になる(空気があるところだけ)
                if rnd() < p[7]:
                    lf = 45 + 60 * rnd()
                    add_smoke([x, y, p[2] * 0.12 + rnd() * 4 - 2, p[3] * 0.12 + rnd() * 4 - 2, lf, lf, 0])
                continue
            p[0], p[1] = x, y
            add(p)
        self.flames = keep

        keep = []
        add = keep.append
        damp = 1.0 - 0.06 * (0.3 + 0.7 * air)
        for p in smokes:
            p[4] -= 1
            if p[4] <= 0:
                continue
            x = p[0] + p[2] * DT
            y = p[1] + p[3] * DT
            if abs(x - cam_x) > reach or abs(y - cam_y) > reach:
                continue
            p[2] *= damp
            p[3] = p[3] * damp + 0.02
            gy = ground(x) if ground else 0.0
            if y < gy:  # 地面で跳ねる
                y = gy
                p[3] = abs(p[3]) * 0.3
            p[0], p[1] = x, y
            add(p)
        if len(keep) > MAX_SMOKE:
            del keep[:len(keep) - MAX_SMOKE]
        self.smokes = keep

        keep = []
        add = keep.append
        for p in self.sparks:
            p[4] -= 1
            if p[4] <= 0:
                continue
            if len(p) > 8:
                k = 1.0 - p[8]
                p[2] *= k
                p[3] = p[3] * k - p[7] * DT
            x = p[0] + p[2] * DT
            y = p[1] + p[3] * DT
            if abs(x - cam_x) > reach or abs(y - cam_y) > reach:
                continue
            gy = ground(x) if ground else 0.0
            if y < gy:
                y = gy
                p[3] = abs(p[3]) * 0.2
                p[2] *= 0.6
            p[0], p[1] = x, y
            add(p)
        if len(keep) > MAX_SPARK:
            del keep[:len(keep) - MAX_SPARK]
        self.sparks = keep

        # 巻き上がる煙の粒: 横へ広がりながら減速する。上へ吹き上がった粒も、機体の高さあたりで止まる
        keep = []
        add = keep.append
        for p in self.billows:
            p[4] -= 1
            if p[4] <= 0:
                continue
            p[2] *= 0.982
            p[3] = p[3] * 0.955 + 0.15 * DT
            x = p[0] + p[2] * DT
            y = p[1] + p[3] * DT
            if abs(x - cam_x) > reach or abs(y - cam_y) > reach:
                continue
            gy = ground(x) if ground else 0.0
            if y < gy:
                y = gy
                p[3] = abs(p[3]) * 0.3
            p[0], p[1] = x, y
            add(p)
        self.billows = keep

    # ---- 描く ----
    def draw_billows(self, ax, ay, cam_x, cam_y, ppm, w, h):
        """巻き上がる煙の粒。機体を描いたあとに呼び、機体を隠す。古いものから描いて、新しいものを手前に。"""
        circ = pyxel.circ
        ox = ax - cam_x * ppm
        oy = ay + cam_y * ppm
        thin = []
        for p in self.billows:
            f = p[4] / p[5]  # 1 → 0
            r = (p[6] + (p[7] - p[6]) * (1.0 - f) ** 0.5) * ppm
            x = ox + p[0] * ppm
            y = oy - p[1] * ppm
            if x < -r or x > w + r or y < -r or y > h + r or r < 1:
                continue
            if f < 0.25:  # 消えかけは薄く
                thin.append((x, y, r))
                continue
            circ(x, y, r, ui.GRAY)  # 影
            circ(x - r * 0.18, y - r * 0.22, r * 0.78, ui.WHITE)  # 日の当たる側
        if thin:
            pyxel.dither(0.45)
            for x, y, r in thin:
                circ(x, y, r, ui.GRAY)
            pyxel.dither(1.0)

    def draw(self, ax, ay, cam_x, cam_y, ppm, w, h):
        """(ax, ay) はカメラ位置が映る画面上の点、ppm は 1 m あたりのピクセル数。"""
        pset, rect, circ = pyxel.pset, pyxel.rect, pyxel.circ
        ox = ax - cam_x * ppm
        oy = ay + cam_y * ppm
        big = ppm >= 1.5

        # 煙: 古いものは薄く(ディザ)、新しいものは濃く
        old = []
        for p in self.smokes:
            x = ox + p[0] * ppm
            y = oy - p[1] * ppm
            if x < -4 or x > w + 4 or y < -4 or y > h + 4:
                continue
            f = p[4] / p[5]
            if f < 0.4:
                old.append((x, y, p[6], f))
                continue
            col = (ui.NAVY if f < 0.7 else ui.BLACK) if p[6] else (ui.GRAY if f < 0.7 else ui.WHITE)
            if big:
                circ(x, y, 1 if f > 0.85 else 2, col)
            else:
                rect(x, y, 2, 2, col)
        if old:
            pyxel.dither(0.5)
            for x, y, dark, f in old:
                col = ui.NAVY if dark else ui.GRAY
                if big:
                    circ(x, y, 2 if f > 0.15 else 1, col)
                else:
                    rect(x, y, 2, 2, col)
            pyxel.dither(1.0)

        # 炎: 若いほど明るく、ノズルの近くは太く
        pal3 = (FLAME_AIR, FLAME_VAC, FLAME_HOT)
        for p in self.flames:
            x = ox + p[0] * ppm
            y = oy - p[1] * ppm
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            f = p[4] / p[5]
            c = pal3[p[6]]
            if f > 0.66:
                if big:
                    rect(x - 1, y - 1, 3, 3, c[0])
                else:
                    rect(x, y, 2, 2, c[0])
            elif f > 0.33:
                if big:
                    rect(x, y, 2, 2, c[1])
                else:
                    pset(x, y, c[1])
            else:
                pset(x, y, c[2])

        for p in self.sparks:
            x = ox + p[0] * ppm
            y = oy - p[1] * ppm
            if 0 <= x < w and 0 <= y < h:
                pset(x, y, p[6])
