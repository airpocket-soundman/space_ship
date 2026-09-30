"""タイトル画面の地球: スターリンク衛星の軌道から見た眺め。

高度 550 km・周期約 95.6 分の軌道を回る衛星に、進行方向の横(軌道面の外側)を向いた
カメラを載せた想定で、地球を透視投影で描く。
太陽は宇宙空間に固定し、衛星が進むにつれて地表と昼夜の境界線が流れていく。

画面の各ピクセルが地球のどこを見ているか(軌道座標の角度)は最初に一度だけ計算し、
毎フレームは「軌道上の位置の分だけ角度をずらして地表マップと光を引く」だけにしている。
描画は 320x240(640x480 の画面)か 360x360(720x720 / 360x360 の画面)で行い、画面に合わせて拡大する。
"""

import math

import numpy as np
import pyxel

from . import ui

R_EARTH = 6371.0  # km
ALTITUDE = 550.0  # km
PERIOD = 95.6 * 60  # s
TIME_SCALE = 12.0  # 実時間の何倍で軌道を進めるか(1 で実時間)
FOV = math.radians(100)  # 横方向の画角
SUN_BETA = math.radians(55)  # 太陽の軌道面からの角度
ATMOS = 170.0  # 大気の光を描く高さ [km]

TEX_SPAN = math.radians(90)  # 地表マップの横が表す角度
TEX_BETA = math.radians(24)  # 地表マップの縦が表す角度

BLACK, NAVY, PURPLE, TEAL, BROWN, DBLUE, LBLUE, WHITE = range(8)
RED, ORANGE, YELLOW, LIME, CYAN, GRAY, PINK, PEACH = range(8, 16)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])

MATS = [DBLUE, TEAL, BROWN, GRAY, WHITE, YELLOW]  # 地表の種類(マップの色)

# 地球だけに使う追加の色。標準の 16 色の後ろ(16 番〜)に足す。ほかの画面は 0〜15 番しか使わない
EARTH_COLORS = [
    0x040C2C, 0x0A2470, 0x1242AE, 0x1E66DA, 0x3C8EF4,  # 海(暗→明)
    0x0E2A12, 0x1E5A1E, 0x38902C, 0x6CBE3E, 0xA8E06C,  # 緑の陸
    0x3A2610, 0x7C5422, 0xBC8C3A, 0xE4C270,  # 砂漠
    0x2E3C6C, 0x8AA2CC, 0xD4E0F4,  # 雲
    0x0A1C6A, 0x1A4CD8, 0x3094FF, 0x84D6FF, 0xE8FAFF,  # 大気の光
    0xFFD43A, 0xFF9A1A,  # 街の明かり
    0x6AA8F4,  # 地平線のかすみ
]
(O0, O1, O2, O3, O4, G0, G1, G2, G3, G4, D0, D1, D2, D3, C0, C1, C2,
 A0, A1, A2, A3, A4, CITY, CITY2, HAZE) = range(16, 16 + len(EARTH_COLORS))


def add_earth_colors():
    if len(pyxel.colors) < 16 + len(EARTH_COLORS):
        pyxel.colors.extend(EARTH_COLORS)


def ramp(colors, v, b):
    t = min(max(v, 0.0), 0.999) * (len(colors) - 1)
    base = int(t)
    if t - base > (b + 0.5) / 16 and base + 1 < len(colors):
        base += 1
    return colors[base]


def surface_color(mat, lq, haze, b):
    night = lq / 15.0 < 0.12
    # 夜側も真っ暗にせず、海や陸の色が見える明るさを残す
    L = 0.3 + 0.7 * lq / 15.0
    if mat == DBLUE:  # 海
        c = ramp([O0, O1, O2, O3, O3, O4], L, b)
    elif mat == TEAL:  # 緑の陸
        c = ramp([O0, G0, G1, G2, G3, G4], L, b)
    elif mat == BROWN:  # 砂漠
        c = ramp([O0, D0, D1, D2, D3], L, b)
    elif mat == GRAY:  # 薄い雲
        c = ramp([O0, C0, C1, C2, WHITE], L * 0.85 + 0.1, b)
    elif mat == WHITE:  # 厚い雲
        c = ramp([O1, C0, C1, C2, WHITE, WHITE], L * 0.85 + 0.2, b)
    else:  # 都市のある陸(夜は明かりが灯る)
        c = (CITY if b % 3 else CITY2) if night else ramp([O0, G0, G1, G2, G3, G4], L, b)
    # 地平線近くのかすみ(昼は明るい青、夜は暗い青)
    if haze and b < haze * 4:
        c = A3 if L > 0.7 else HAZE if L > 0.45 else A1 if L > 0.2 else A0
    return c


def glow_color(iq, sq, b):
    v = (iq / 7) * (0.45 + 0.55 * (sq / 7))
    return ramp([BLACK, A0, A1, A2, A3, A4, WHITE], v, b)


class EarthView:
    def __init__(self, w=320, h=240, scale=2, horizon_y=105):
        """w x h で描いて scale 倍で表示する。horizon_y は画面中央で地平線が来る高さ(w x h の座標)。"""
        self.w, self.h, self.scale, self.horizon_y = w, h, scale, horizon_y
        add_earth_colors()
        W, H = w, h
        self.image = pyxel.Image(W, H)
        self.pix = np.ctypeslib.as_array(self.image.data_ptr()).reshape(H, W)
        self.pix[:] = BLACK
        self.omega = 2 * math.pi / PERIOD
        self._load_texture()
        self._build_luts()
        self._precompute()
        self.theta = 0.0
        self.theta = self._find_dawn()

    # ---- 準備 ----
    def _load_texture(self):
        img = pyxel.Image(2048, 546)
        img.load(0, 0, str(ui.ASSETS / "earth_tex.png"))
        raw = np.ctypeslib.as_array(img.data_ptr()).reshape(546, 2048).copy()
        lut = np.zeros(16, dtype=np.uint8)
        for i, m in enumerate(MATS):
            lut[m] = i
        self.tex = lut[raw]
        self.th, self.tw = self.tex.shape

    def _build_luts(self):
        self.surf_lut = np.zeros((len(MATS), 16, 4, 16), dtype=np.uint8)
        for mi, m in enumerate(MATS):
            for lq in range(16):
                for hz in range(4):
                    for b in range(16):
                        self.surf_lut[mi, lq, hz, b] = surface_color(m, lq, hz, b)
        self.glow_lut = np.zeros((8, 8, 16), dtype=np.uint8)
        for iq in range(8):
            for sq in range(8):
                for b in range(16):
                    self.glow_lut[iq, sq, b] = glow_color(iq, sq, b)

    def _precompute(self):
        W, H = self.w, self.h
        ys, xs = np.mgrid[0:H, 0:W].astype(float)
        f_len = (W / 2) / math.tan(FOV / 2)
        r_cam = R_EARTH + ALTITUDE
        dip = math.acos(R_EARTH / r_cam)
        pitch = dip + math.atan((H / 2 - self.horizon_y) / f_len)
        cp, sp = math.cos(pitch), math.sin(pitch)
        # 軌道座標: x = 進行方向、y = 軌道面の外側(カメラの向き)、z = 地心から衛星の方向
        fwd = np.array([0.0, cp, -sp])
        up = np.array([0.0, sp, cp])
        right = np.array([1.0, 0.0, 0.0])
        self.cam = np.array([0.0, 0.0, r_cam])
        self.f_len, self.fwd, self.up, self.right = f_len, fwd, up, right

        dx = (xs + 0.5 - W / 2) / f_len
        dy = (ys + 0.5 - H / 2) / f_len
        d = fwd[None, None, :] + dx[..., None] * right - dy[..., None] * up
        d /= np.linalg.norm(d, axis=-1, keepdims=True)
        b = d @ self.cam
        c = r_cam * r_cam - R_EARTH * R_EARTH
        disc = b * b - c
        hit = (disc >= 0) & (b < 0)
        t = -b - np.sqrt(np.clip(disc, 0, None))
        p = self.cam + t[..., None] * d
        bayer = BAYER[ys.astype(int) % 4, xs.astype(int) % 4]

        # 地表のピクセル
        ph = p[hit] / R_EARTH
        self.hit_idx = np.flatnonzero(hit.ravel())
        self.h_alpha = np.arctan2(ph[:, 0], ph[:, 2])
        beta = np.arcsin(np.clip(ph[:, 1], -1, 1))
        self.h_cb, self.h_sb = np.cos(beta), np.sin(beta)
        self.h_v = np.clip((beta / TEX_BETA * self.th).astype(int), 0, self.th - 1)
        mu = -(ph * d[hit]).sum(axis=1)  # 見下ろす角度(地平線付近で 0)
        self.h_haze = np.clip((0.35 - mu) / 0.1, 0, 3).astype(int)
        self.h_bayer = bayer[hit]

        # 大気の光(地球に当たらず、大気をかすめるピクセル)
        closest = np.sqrt(np.clip(r_cam * r_cam - b * b, 0, None))
        hr = closest - R_EARTH
        glow = (~hit) & (b < 0) & (hr < ATMOS)
        self.glow_idx = np.flatnonzero(glow.ravel())
        tp = self.cam + (-b[glow])[:, None] * d[glow]
        tp /= np.linalg.norm(tp, axis=1, keepdims=True)
        self.g_alpha = np.arctan2(tp[:, 0], tp[:, 2])
        gb = np.arcsin(np.clip(tp[:, 1], -1, 1))
        self.g_cb, self.g_sb = np.cos(gb), np.sin(gb)
        self.g_iq = np.clip(np.exp(-np.maximum(hr[glow], 0) / 45.0) * 7.99, 0, 7).astype(int)
        self.g_bayer = bayer[glow]

        # 列ごとの地平線の高さ(朝日の位置合わせ用)
        self.horizon_row = np.where(hit.any(axis=0), hit.argmax(axis=0), H)

    def sun_dir(self, theta):
        """カメラから見た太陽の向き(軌道座標)。衛星が進むと逆向きに回る。"""
        lam = -theta
        return np.array([math.cos(SUN_BETA) * math.sin(lam), math.sin(SUN_BETA), math.cos(SUN_BETA) * math.cos(lam)])

    def _find_dawn(self):
        """最初の画面が、画面中央付近で日の出の直前になる軌道位置を探す。"""
        best, best_score = 0.0, 1e9
        for i in range(1440):
            th = i / 1440 * 2 * math.pi
            self.theta = th
            info = self.sun_screen()
            if info is None:
                continue
            x, _y, elev = info
            score = abs(elev + math.radians(1.5)) * 10 + abs(x - self.w * 0.55) / self.w
            if score < best_score:
                best, best_score = th, score
        return best

    # ---- 毎フレーム ----
    def update(self, dt=1 / 60):
        self.theta += self.omega * TIME_SCALE * dt

    def light(self, alpha, cb, sb):
        # 地表の点の法線と太陽の向きの内積。点は衛星に対して -theta だけ回っている
        return cb * math.cos(SUN_BETA) * np.cos(alpha + self.theta) + sb * math.sin(SUN_BETA)

    def render(self):
        pix = self.pix.reshape(-1)
        a = self.h_alpha + self.theta
        u = ((a % TEX_SPAN) / TEX_SPAN * self.tw).astype(int) % self.tw
        mat = self.tex[self.h_v, u]
        L = self.light(self.h_alpha, self.h_cb, self.h_sb)
        lq = np.clip((L * 2.0 + 0.25) * 15, 0, 15).astype(int)
        pix[self.hit_idx] = self.surf_lut[mat, lq, self.h_haze, self.h_bayer]

        gl = self.light(self.g_alpha, self.g_cb, self.g_sb)
        sq = np.clip((gl * 1.6 + 0.45) * 7.99, 0, 7).astype(int)
        pix[self.glow_idx] = self.glow_lut[self.g_iq, sq, self.g_bayer]

    def sun_screen(self):
        """太陽の画面上の位置(描画解像度の座標)と、地平線からの高さ[rad]。見えなければ None。"""
        s = self.sun_dir(self.theta)
        zf = s @ self.fwd
        if zf <= 0.05:
            return None
        x = self.w / 2 + self.f_len * (s @ self.right) / zf
        y = self.h / 2 - self.f_len * (s @ self.up) / zf
        dip = math.acos(R_EARTH / (R_EARTH + ALTITUDE))
        elev = math.asin(max(-1.0, min(1.0, s @ (self.cam / np.linalg.norm(self.cam))))) + dip
        return x, y, elev

    def draw(self, sx=0, sy=0):
        self.render()
        W, H, S = self.w, self.h, self.scale
        # blt の拡大は転送先の中心が基準なので、左上が (sx, sy) になるようにずらす
        pyxel.blt(sx + W * (S - 1) / 2, sy + H * (S - 1) / 2, self.image, 0, 0, W, H, BLACK, 0, S)
        self.draw_sun(sx, sy)

    def draw_sun(self, sx, sy):
        info = self.sun_screen()
        if info is None:
            return
        x, y, elev = info
        W, S = self.w, self.scale
        g = S / 2  # 光の大きさ(2 倍表示のときが 1)
        if not (-40 < x < W + 40):
            return
        col = int(min(max(x, 0), W - 1))
        horizon = self.horizon_row[col]
        fx = sx + x * S
        if elev < 0:
            # 地平線の下: 地平線の上に朝焼け(夕焼け)の光だけ出す
            k = max(0.0, 1 + elev / math.radians(6))
            if k <= 0:
                return
            gy = sy + horizon * S
            for rx, ry, c, a in ((120, 14, A2, 0.35), (70, 8, A3, 0.5), (30, 4, WHITE, 0.8)):
                rx, ry = rx * g, ry * g
                pyxel.dither(a * k)
                pyxel.elli(fx - rx * k, gy - ry, rx * 2 * k, ry * 2, c)
            pyxel.dither(1.0)
            pyxel.rect(fx - 160 * g * k, gy - 1, 320 * g * k, 2, A3)
            if k > 0.6:
                pyxel.rect(fx - 60 * g * k, gy - 1, 120 * g * k, 2, WHITE)
            return
        # 地平線の上: 太陽と光芒
        fy = sy + y * S
        if fy > sy + horizon * S + 4:
            return
        pulse = 0.5 + 0.5 * math.sin(pyxel.frame_count / 30)
        r = (22 + 6 * pulse) * g
        pyxel.dither(0.5)
        pyxel.circ(fx, fy, r * 0.9, LBLUE)
        pyxel.dither(1.0)
        for ang in range(0, 180, 45):
            a = math.radians(ang)
            L = r * (2.2 if ang % 90 == 0 else 1.3)
            pyxel.line(fx - math.cos(a) * L, fy - math.sin(a) * L, fx + math.cos(a) * L, fy + math.sin(a) * L, WHITE)
        pyxel.circ(fx, fy, 7 * g, YELLOW)
        pyxel.circ(fx, fy, 5 * g, WHITE)
