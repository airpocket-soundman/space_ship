"""ACT パート: ロケット操縦画面。"""

import math
import random

import pyxel

from . import audio, rocket_art, ui
from .i18n import tr, trf
from .missions import MissionRun
from .particles import Particles
from .physics import MU, PLANET_R

SUBSTEPS = 2
COUNTDOWN = 5.0
COUNTDOWN_AIR = 3.0  # 飛行の途中から始まるステージのカウント

# オープニングの飛行で画面に出す操作説明。(id, 文, 最短表示秒, 最長表示秒)
# 最短を過ぎて該当する操作をしたか、最長を過ぎたら次へ進む
TUTORIAL = [
    ("intro", "Eagle 1 の初飛行。操縦するのは、あなただ。", 0, 0),
    ("ignite", "SPACE で点火!", 0, 0),
    ("throttle", "↑↓ でスロットル(推力)。このエンジンは 70% より下には絞れない。", 3, 7),
    ("steer", "←→ でノズルを振って姿勢を変える。傾いたら、反対に当てて戻す。", 3, 8),
    ("window", "右のウィンドウ: 高度 10 km を通過するとき、この範囲に入っていれば高評価。", 5, 5),
    ("good", "いい調子だ。そのまま、まっすぐ上へ!", 0, 0),
]

# 台船の名前(クルーがつけた冗談)
SHIP_NAME = "説明書を読め号"


class MissionScene:
    def __init__(self, app, mdef, cold_open=False):
        """cold_open: ゲームの最初の飛行。操作説明を出し、途中で必ず爆発する。"""
        self.app = app
        self.cold_open = cold_open
        self.tut = 0  # 操作説明の何番目か
        self.tut_time = 0.0
        # 画面サイズごとの配置: 左が飛行画面、右が計器パネル
        panel_w = 144 * ui.K if ui.COMPACT else 188  # 720x720 は文字が 2 倍なので、詰めた配置を 2 倍に
        self.panel_x = ui.W - panel_w
        self.view_w = self.panel_x - 4
        self.anchor_x = self.view_w // 2
        self.anchor_y = ui.H * 5 // 8  # 機体を置く高さ
        self.base_ppm = 1.0 if ui.TINY else 1.5 if ui.SMALL else 2.0  # 1 m あたりのピクセル数
        if mdef.kind == "reentry":
            self.base_ppm *= 2.0  # カプセルは小さいので、大きく映す
        self.zoom = 1.0  # 着陸のときは、高いところほど引いて見せる
        self.ppm = self.base_ppm
        self.fs = 10 if ui.COMPACT else 12  # 飛行画面に出すメッセージの文字(720x720 はこれが 2 倍で描かれる)
        self.m = mdef
        self.run = MissionRun(mdef, inspected=app.state.inspected, doomed=cold_open)
        self.v = self.run.v
        self.airborne = bool(mdef.start)  # 飛行の途中から始まる
        self.phase = "count"  # count / ready / flight / end
        self.count = COUNTDOWN_AIR if self.airborne else COUNTDOWN
        self.frame = 0
        self.end_timer = 0
        self.exploded = False
        self.parts = Particles()
        self.parts.ground = self.ground_y
        self.objs = []  # 切り離した段や放出した荷物
        self.messages = []  # [text, color, frames]
        self.cam_x = self.v.x
        self.cam_y = max(self.v.y, 60.0)
        self.was_engine = False
        self.warp_used = 1  # このフレームで物理を何倍進めたか
        self.was_chute = False
        rng = random.Random(7)
        self.clouds = [(rng.uniform(-600, 600), rng.uniform(1200, 4200), rng.uniform(60, 180), rng.uniform(14, 30))
                       for _ in range(40)]
        self.stars = [(rng.uniform(0, self.view_w), rng.uniform(0, ui.H), rng.choice((ui.WHITE, ui.LBLUE, ui.GRAY)))
                      for _ in range(160)]
        self.say("カウントダウン開始" if self.airborne else "射場クリア。カウントダウン開始", ui.WHITE)
        if not cold_open:
            audio.bgm(None)  # 本番の打ち上げはエンジン音だけ(オープニングは曲を流したまま)
        self.update_camera(snap=True)

    def say(self, text, col=ui.WHITE, frames=180):
        self.messages.append([tr(text), col, frames])
        self.messages = self.messages[-3:]

    # ---- 更新 ----
    def update(self):
        self.frame += 1
        steer = (1 if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT) else 0) - \
                (1 if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT) else 0)
        thr = (1 if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP) else 0) - \
              (1 if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN) else 0)
        ignite = pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)
        action = pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
        if self.cold_open:
            self.update_tutorial(steer, thr)
        v, run = self.v, self.run

        if self.phase == "count":
            prev = math.ceil(self.count)
            self.count -= 1 / 60
            if math.ceil(self.count) != prev and self.count > 0:
                self.say(f"T-{math.ceil(self.count)}", ui.WHITE, 50)
            if self.count <= 0:
                if self.airborne:
                    self.phase = "flight"
                else:
                    self.phase = "ready"
                    self.say("点火準備よし。SPACE で点火!", ui.YELLOW, 600)
        elif self.phase == "ready":
            if ignite:
                run.space()
                if v.engine_on:
                    self.phase = "flight"
        elif self.phase == "flight":
            if ignite:
                run.space()
            if action:
                run.z()
            was_lifted = v.lifted_off
            ts = round(run.time_scale)
            self.warp_used = run.warp * ts  # 基本の倍率(画面には出さない)× 早送り
            for _ in range(SUBSTEPS * run.warp * ts):
                run.step(1 / 60 / SUBSTEPS, steer, thr)
                if run.result:
                    break
            if v.lifted_off and not was_lifted:
                self.say("リフトオフ!", ui.LIME, 120)
            if run.result:
                self.phase = "end"
                self.finish_effects()
        elif self.phase == "end":
            self.end_timer += 1
            if run.result == "success" and not self.exploded and self.m.kind in ("ascent", "orbit"):
                v.step(1 / 60, 0, 0)
            if self.end_timer > 60 and ui.confirm():  # 「SPACE で続ける」を出しているので、押すまで待つ
                if self.cold_open:
                    self.app.after_cold_open()
                else:
                    self.app.finish_mission(run)
                return

        for kind, text in run.events:
            col = {"warn": ui.RED, "bad": ui.RED, "good": ui.LIME, "info": ui.CYAN}.get(kind, ui.WHITE)
            self.say(text, col, 240)
        run.events.clear()
        for d in run.dropped:
            self.add_object(d)
        run.dropped.clear()

        if v.engine_on and not self.was_engine:
            audio.ignite()
        self.was_engine = v.engine_on
        audio.engine(v.throttle * (0.4 + 0.6 * v.engine_frac) if v.engine_on and not self.exploded else 0)
        self.update_camera()
        self.update_objects()
        self.update_particles()
        for msg in self.messages:
            msg[2] -= 1
        self.messages = [m for m in self.messages if m[2] > 0]

    def update_tutorial(self, steer, thr):
        tid = TUTORIAL[self.tut][0]
        self.tut_time += 1 / 60
        if tid == "intro":
            done = self.phase != "count"
        elif tid == "ignite":
            done = self.v.lifted_off
        elif tid in ("throttle", "steer", "window"):
            _, _, lo, hi = TUTORIAL[self.tut]
            pressed = thr if tid == "throttle" else steer if tid == "steer" else True
            done = self.tut_time >= hi or (self.tut_time >= lo and pressed)
        else:
            done = False
        if done and self.tut + 1 < len(TUTORIAL):
            self.tut += 1
            self.tut_time = 0.0

    def finish_effects(self):
        """結果が出た瞬間の演出(爆発・水しぶき・着地の土煙)。"""
        run, v = self.run, self.v
        if run.result == "fail":
            if run.vehicle_lost:
                self.explode()
            return
        kind = self.m.kind
        if kind == "reentry" or (self.m.land and self.m.land.site == "sea"):
            self.parts.splash(v.x, 0.0, 90)
        elif kind in ("hop", "landing", "recover"):
            self.parts.puff(v.x, run.deck_y() + 0.5, 0.0, 1.0, 26, 9.0, 90)

    def explode(self):
        self.exploded = True
        audio.explosion()
        if self.cold_open:
            audio.bgm(None)  # 期待の曲が爆発で途切れる
        v = self.v
        cx, cy = self.rocket_center()
        self.parts.explode(cx, max(cy, self.ground_y(cx) + 1.0), self.ground_vx(), v.vy)

    def rocket_center(self):
        v = self.v
        L = v.length
        return v.x + math.sin(v.theta) * L / 2, v.y + math.cos(v.theta) * L / 2

    def ground_vx(self):
        """機体が地表に沿って進む速さ [m/s]。x は地表での距離なので、高いところでは水平速度より小さい。"""
        v = self.v
        return v.vx * PLANET_R / (PLANET_R + max(v.y, 0.0))

    def ground_y(self, x):
        """地表の高さ [m]。台船の上なら甲板の高さ。"""
        land = self.m.land
        if land and land.site == "ship" and abs(x - self.run.ship_x) <= land.half_w + 6:
            return self.run.deck_y()
        return 0.0

    # ---- 切り離した段・放出した荷物 ----
    def add_object(self, d):
        if d is None:
            return
        o = dict(d)
        o["age"] = 0
        o["stages"] = [d["params"]] + list(d.get("upper") or []) if d.get("params") else []
        if d.get("lower"):  # 捨てた1段目は、ゆっくり回りながら離れていく
            o["omega"] = d["omega"] + math.radians(random.choice((-14, 14)))
            o["vx"] -= math.sin(d["theta"]) * 3.0
            o["vy"] -= math.cos(d["theta"]) * 3.0
        self.objs.append(o)
        # 切り離した面から白い煙(下の段を捨てたなら機体の底、上を送り出したなら機体の先)
        v = self.v
        at = 0.0 if d.get("lower") else v.length
        self.parts.puff(v.x + math.sin(v.theta) * at, v.y + math.cos(v.theta) * at, self.ground_vx(), v.vy, 14, 6.0, 40)

    def update_objects(self):
        dt = 1 / 60 * (self.warp_used if self.phase == "flight" else 1)
        keep = []
        for o in self.objs:
            o["age"] += 1
            r = PLANET_R + max(o["y"], 0.0)
            ay = -(MU / (r * r) - o["vx"] ** 2 / r)
            ax = -o["vx"] * o["vy"] / r
            flying = o["stages"] and not o.get("lower") and o["age"] > 70  # 自動で飛んでいく2段目
            if flying:
                ax += math.sin(o["theta"]) * 22.0
                ay += math.cos(o["theta"]) * 22.0
                hw = rocket_art.HALF_W[o["stages"][0].style]
                self.parts.flame(o["x"], o["y"], o["vx"] * PLANET_R / r, o["vy"], o["theta"] + math.pi, 6, 150.0, 0.35,
                                 hw, 8, 1 if o["y"] > 30_000 else 0)
            o["vx"] += ax * dt
            o["vy"] += ay * dt
            o["x"] += o["vx"] * dt * PLANET_R / r
            o["y"] += o["vy"] * dt
            o["theta"] += o["omega"] * dt
            far = abs(o["x"] - self.cam_x) + abs(o["y"] - self.cam_y) > 2500 / self.ppm
            if o["age"] < 1800 and not far and o["y"] > self.ground_y(o["x"]):
                keep.append(o)
        self.objs = keep

    # ---- パーティクル ----
    def update_particles(self):
        v, run, parts = self.v, self.run, self.parts
        air = min(1.0, v.density / 1.225)
        s, c = math.sin(v.theta), math.cos(v.theta)
        gvx = self.ground_vx()  # 粒は画面上の機体と同じ速さで運ぶ
        # 先にいまある粒を動かしてから、このフレームの粒を出す(出したばかりの粒を先へ進めない)
        parts.update(self.cam_x, self.cam_y, max(self.view_w, ui.H) / self.ppm * 1.3, air)
        # 早送り中は機体が 1 フレームに何倍も進む。粒も機体と一緒に運んで、置き去りにしない
        w = self.warp_used if self.phase == "flight" else 1
        if w > 1:
            parts.shift(gvx * (w - 1) / 60, v.vy * (w - 1) / 60)
        if v.throttle > 0.05 and not self.exploded and self.phase != "count":
            style = v.p.style
            hw = rocket_art.HALF_W[style]
            # ノズルの先(いまの位置)から出す
            ta, tc = rocket_art.nozzle_tip(style, v.gimbal, self.legs_out())
            nx, ny = v.x + s * ta + c * tc, v.y + c * ta - s * tc
            ang = v.theta - v.gimbal + math.pi
            frac = math.sqrt(v.engine_frac)
            vac = air < 0.03
            if style == "phoenix":
                parts.flame(nx, ny, gvx, v.vy, ang, 5, 60.0, 0.45, hw * 1.2, 5, 1)
            else:
                big = style in ("eagle9", "eagle9r")
                n = int((8 + 10 * v.throttle) * (1.4 if big else 1.0) * (0.55 + 0.45 * frac))
                # 空気が薄いほど、炎は短く広がる
                parts.flame(nx, ny, gvx, v.vy, ang, n, (150.0 + 60.0 * v.throttle) * (0.6 + 0.4 * air),
                            0.09 + 0.26 * (1.0 - air), hw * (1.1 if big else 0.9) * frac, 8,
                            1 if vac else 0, 0.22 * air)
        # スラスター: 機首と機尾で逆向きに噴く
        if v.rcs_firing and not self.exploded:
            L = v.length
            hw = rocket_art.HALF_W[v.p.style]
            side = v.rcs_firing
            for along, sgn in ((L * 0.85, -side), (L * 0.12, side)):
                x = v.x + s * along + c * sgn * hw
                y = v.y + c * along - s * sgn * hw
                parts.jet(x, y, gvx, v.vy, v.theta + math.pi / 2 * sgn, 2)
        # 火災の炎と黒い煙
        if (run.fire_active or run.anomaly_left is not None) and not self.exploded:
            L = v.length
            h = random.uniform(0, L * 0.3) if run.fire_active else random.uniform(L * 0.55, L * 0.75)
            parts.flame(v.x + s * h, v.y + c * h, gvx, v.vy, v.theta + math.pi + random.uniform(-0.6, 0.6),
                        4, 40.0, 0.8, 4.0, 10, 0, 0.0)
            if self.frame % 3 == 0:
                parts.puff(v.x + s * h, v.y + c * h, gvx * 0.9, v.vy * 0.9, 1, 5.0, 60, dark=1)
        # 再突入の加熱: 進む側の面から、後ろへ流れる光
        hot = run.heat if self.m.kind == "reentry" and run.phase == "entry" else \
            (v.q - 12_000) / 300 if run.phase == "descent" and v.speed > 450 else 0.0
        if hot > 8 and not self.exploded and v.speed > 50:
            ux, uy = v.vx / v.speed, v.vy / v.speed
            n = min(10, int(hot / 9))
            parts.flame(v.x, v.y, gvx + ux * 40.0, v.vy + uy * 40.0, math.atan2(-ux, -uy), n, 160.0, 0.6,
                        rocket_art.HALF_W[v.p.style] * 2.2, 9, 2)
        # パラシュートが開いた
        if run.phase == "chute" and not self.was_chute:
            self.was_chute = True
            parts.puff(v.x + s * v.length, v.y + c * v.length, gvx * 0.5, v.vy * 0.5, 10, 8.0, 40)

    def update_camera(self, snap=False):
        v, run, land = self.v, self.run, self.m.land
        cx, cy = self.rocket_center()
        # 着陸: 高いところでは引いて、目標が見えるようにする
        zoom = 1.0
        descending = run.phase == "descent" or self.m.kind in ("hop", "landing")
        if land and descending:
            h = max(0.0, v.y - run.deck_y())
            zoom = max(0.2, min(1.0, 1.0 / (1.0 + h / 260.0)))
        anchor = ui.H * (4 if descending and self.m.kind != "hop" else 5) // 8
        k = 1.0 if snap else 0.06
        self.zoom += (zoom - self.zoom) * k
        self.anchor_y += (anchor - self.anchor_y) * k
        self.ppm = self.base_ppm * self.zoom
        # 地表の近くでは、地面が画面の下に見える高さより下へカメラを下げない
        floor = (ui.H - (44 * ui.K if ui.COMPACT else 60) - self.anchor_y) / self.ppm
        self.cam_x = cx
        self.cam_y = max(cy, floor)

    # ---- 座標変換 ----
    def sx(self, wx):
        return self.anchor_x + (wx - self.cam_x) * self.ppm

    def sy(self, wy):
        return self.anchor_y - (wy - self.cam_y) * self.ppm

    # ---- 描画 ----
    def draw(self):
        pyxel.clip(0, 0, self.view_w, ui.H)
        self.draw_sky()
        self.draw_clouds()
        self.draw_ground()
        self.parts.draw(self.anchor_x, self.anchor_y, self.cam_x, self.cam_y, self.ppm, self.view_w, ui.H)
        self.draw_objects()
        if not self.exploded:
            self.draw_rocket()
        self.draw_ladder()
        self.draw_markers()
        self.draw_messages()
        self.draw_alert_border()
        self.draw_tutorial()
        self.draw_guide()
        self.draw_orbit_map()
        if self.phase == "end":
            self.draw_banner()
        pyxel.clip()
        self.draw_panel()

    SKY = [(0, ui.CYAN), (3000, ui.DBLUE), (9000, ui.NAVY), (20000, ui.BLACK)]
    SKY_BLEND = 1500.0  # 色が切り替わる高度の幅 [m]

    def sky_color(self, alt):
        base = self.SKY[0][1]
        for a, col in self.SKY:
            if alt >= a:
                base = col
        for a, col in self.SKY[1:]:
            if a - self.SKY_BLEND <= alt < a:
                return base, col, (alt - (a - self.SKY_BLEND)) / self.SKY_BLEND
        return base, base, 0.0

    def draw_sky(self):
        alt = self.cam_y
        if alt > 24_000:
            pyxel.rect(0, 0, self.view_w, ui.H, ui.BLACK)
        else:
            for y in range(0, ui.H, 2):
                base, nxt, t = self.sky_color(self.cam_y + (self.anchor_y - y) / self.ppm)
                pyxel.rect(0, y, self.view_w, 2, base)
                if t > 0:
                    pyxel.dither(t)
                    pyxel.rect(0, y, self.view_w, 2, nxt)
                    pyxel.dither(1.0)
        if alt > 8000:
            a = min(1.0, (alt - 8000) / 10000)
            pyxel.dither(a)
            # 星は、横に速く飛ぶほどゆっくり流れる(遠くにあるので少しだけ)
            shift = self.cam_x * 0.0004
            for x, y, c in self.stars:
                pyxel.pset((x - shift) % self.view_w, y, c)
            pyxel.dither(1.0)
        if alt > 18_000:
            self.draw_limb(alt)

    def draw_limb(self, alt):
        """高いところから見える惑星の縁(青い弧)。高度が上がるほど丸く見える。"""
        w, h = self.view_w, ui.H
        k = min(1.0, (alt - 18_000) / 22_000)  # 0 → 1 で画面の下からせり上がる
        rise = h * (0.30 - 0.12 * min(1.0, alt / 140_000)) * k
        top = h - rise
        ew, eh = w * 3.2, rise * 2 + h * 0.5
        ex = w / 2 - ew / 2
        pyxel.elli(ex, top - 3, ew, eh, ui.LBLUE)
        pyxel.elli(ex, top, ew, eh, ui.DBLUE)
        # 雲の筋: 地表に対して動いているぶんだけ流れる
        rng = random.Random(3)
        for _ in range(14):
            cx = (rng.uniform(0, w * 1.6) - self.cam_x * 0.02) % (w * 1.6) - w * 0.3
            cy = top + rise * rng.uniform(0.25, 0.95)
            cw = rng.uniform(16, 50) * (w / 440)
            # 弧の外にはみ出さないよう、端のほうは描かない
            if abs(cx - w / 2) < w * 0.5 * (0.5 + 0.5 * (cy - top) / max(rise, 1)):
                pyxel.line(cx, cy, cx + cw, cy, ui.WHITE if rng.random() < 0.6 else ui.CYAN)

    def draw_clouds(self):
        if self.cam_y > 12_000:
            return
        ppm = self.ppm
        for wx, wy, w, h in self.clouds:
            # 雲は遠くまで続いているものとして、横に繰り返す
            wx = (wx - self.cam_x + 600) % 1200 - 600 + self.cam_x
            x, y = self.sx(wx), self.sy(wy)
            if -w * ppm < x < self.view_w + w * ppm and -h * ppm < y < ui.H + h * ppm:
                pyxel.elli(x - w * ppm / 2, y - h * ppm / 2 + 3 * ppm, w * ppm, h * ppm, ui.GRAY)
                pyxel.elli(x - w * ppm / 2, y - h * ppm / 2, w * ppm, h * ppm, ui.WHITE)

    def draw_ground(self):
        gy = self.sy(0)
        if gy > ui.H + 40:
            return
        ppm, sx = self.ppm, self.sx
        land = self.m.land
        # 海
        pyxel.rect(0, gy, self.view_w, ui.H - gy, ui.DBLUE)
        for i in range(0, int(ui.H - gy) // 14 + 1):
            y = gy + 8 + i * 14
            off = (self.frame // 2 + i * 13 - int(self.cam_x * ppm)) % 40
            for x in range(-40 + off, self.view_w, 40):
                pyxel.line(x, y, x + 12, y, ui.CYAN)
        # 島(発射場)。地上の着陸場があるなら、そこまで陸を延ばす
        right = 130.0
        if land and land.site == "pad":
            right = max(right, land.x + land.half_w + 40)
        x0, x1 = sx(-130), sx(right)
        if x1 > 0 and x0 < self.view_w:
            pyxel.rect(x0, gy, x1 - x0, 5 * ppm, ui.YELLOW)
            pyxel.rect(x0 + 5 * ppm, gy + 5 * ppm, x1 - x0 - 10 * ppm, 4 * ppm, ui.BROWN)
            pyxel.rect(sx(-110), gy - 1.5 * ppm, sx(right - 20) - sx(-110), 1.5 * ppm + 1, ui.LIME)
            # ヤシの木(着陸場のそばには植えない)
            for tx in (-100, -78, 70, 96):
                if land and land.site == "pad" and abs(tx - land.x) < land.half_w + 20:
                    continue
                x = sx(tx)
                pyxel.line(x, gy - 1.5 * ppm, x + ppm, gy - 13 * ppm, ui.BROWN)
                for dx, dy in ((-5, 2), (5, 2), (-3.5, -1), (4, -1.5)):
                    pyxel.line(x + ppm, gy - 13 * ppm, x + ppm + dx * ppm, gy - 13 * ppm + dy * ppm, ui.TEAL)
            # 格納庫
            hx = sx(-60)
            pyxel.rect(hx, gy - 11 * ppm, 20 * ppm, 9.5 * ppm, ui.GRAY)
            pyxel.rect(hx + 6 * ppm, gy - 7 * ppm, 8 * ppm, 5.5 * ppm, ui.NAVY)
            # 発射台とタワー(機体の背丈に合わせる)
            pyxel.rect(sx(-12), gy - 2.5 * ppm, 24 * ppm, 2.5 * ppm + 1, ui.GRAY)
            if self.m.kind != "hop":
                tall = sum(p.length for p in self.m.rocket.stages) + rocket_art.CARGO_LEN[self.m.rocket.cargo]
                tx, top, step = sx(8 if tall > 30 else 5), self.sy(max(26.0, tall * 0.85)), 4 * ppm
                pyxel.line(tx, top, tx, gy - 2.5 * ppm, ui.WHITE)
                pyxel.line(tx + step, top, tx + step, gy - 2.5 * ppm, ui.WHITE)
                y = top
                while y < gy - 2.5 * ppm - 1 and step >= 2:
                    pyxel.line(tx, y, tx + step, y + step, ui.WHITE)
                    pyxel.line(tx + step, y, tx, y + step, ui.WHITE)
                    y += step
            # 地上の着陸場
            if land and land.site == "pad":
                px0, px1 = sx(land.x - land.half_w), sx(land.x + land.half_w)
                pyxel.rect(px0, gy - 1, px1 - px0, max(3, 2.5 * ppm), ui.GRAY)
                pyxel.line(px0, gy - 1, px1, gy - 1, ui.WHITE)
                cxp = sx(land.x)
                pyxel.rect(cxp - 5 * ppm, gy - 1, 10 * ppm, max(2, ppm), ui.YELLOW)
                for side in (-1, 1):  # 両端の標識
                    ex = sx(land.x + side * land.half_w)
                    pyxel.line(ex, gy - 1, ex, gy - 5 * ppm, ui.WHITE)
                    pyxel.rect(ex - 1, gy - 5 * ppm - 1, 3, 3, ui.RED if self.frame // 30 % 2 else ui.YELLOW)
        # 台船
        if land and land.site == "ship":
            self.draw_ship(gy)

    def draw_ship(self, gy):
        land, ppm = self.m.land, self.ppm
        cx = self.sx(self.run.ship_x)
        hw = (land.half_w + 6) * ppm
        if cx + hw < 0 or cx - hw > self.view_w:
            return
        dy = self.sy(self.run.deck_y())
        pyxel.rect(cx - hw, dy, hw * 2, gy - dy + 2 * ppm, ui.BLACK)
        pyxel.rect(cx - hw, dy, hw * 2, max(2, 1.2 * ppm), ui.GRAY)
        pyxel.line(cx - land.half_w * ppm, dy, cx + land.half_w * ppm, dy, ui.WHITE)
        pyxel.line(cx - 6 * ppm, dy, cx + 6 * ppm, dy, ui.YELLOW)
        for side in (-1, 1):  # 四隅の設備
            pyxel.rect(cx + side * (hw - 3 * ppm) - 1.5 * ppm, dy - 3 * ppm, 3 * ppm, 3 * ppm, ui.NAVY)
        if ppm >= 1.2 and not ui.TINY:
            ui.text_center(cx, dy + 2 * ppm + 2, SHIP_NAME, ui.GRAY, size=10)

    def body_tf(self, x, y, theta):
        """ワールド座標 (x, y) を底、傾き theta の機体を描くための変換。"""
        s, c = math.sin(theta), math.cos(theta)
        ax, ay, ppm, ox, oy, cx, cy = self.anchor_x, self.anchor_y, self.ppm, x, y, self.cam_x, self.cam_y
        return lambda along, across: (ax + (ox + s * along + c * across - cx) * ppm,
                                      ay - (oy + c * along - s * across - cy) * ppm)

    def draw_objects(self):
        for o in self.objs:
            tf = self.body_tf(o["x"], o["y"], o["theta"])
            if o["stages"]:
                rocket_art.vehicle(tf, o["stages"], "none" if o.get("lower") else self.m.rocket.cargo)
            elif o.get("cargo") == "capsule":
                rocket_art.capsule(tf, 0.0, rocket_art.HALF_W["phoenix"])
            else:
                rocket_art.satellite(tf)

    def legs_out(self):
        """着陸脚を開いているか(回収型の1段目が、地表に近づいたとき)。"""
        v, run = self.v, self.run
        return v.p.style == "eagle9r" and run.phase == "descent" and bool(v.y - run.deck_y() < 1200 or run.result)

    def draw_rocket(self):
        v, run = self.v, self.run
        tf = self.body_tf(v.x, v.y, v.theta)
        style = v.p.style
        stages = [v.p] + list(v.upper)
        rocket_art.vehicle(tf, stages, self.m.rocket.cargo if v.upper or style != "eagle9r" else "none",
                           v.gimbal, self.legs_out(), v.fins)
        if run.phase == "chute":
            self.draw_chute(tf)

    def draw_chute(self, tf):
        """パラシュート: カプセルの上に傘、そこへ伸びる紐。"""
        v = self.v
        L = v.length
        hw = rocket_art.HALF_W["phoenix"]
        for i, col in enumerate((ui.ORANGE, ui.WHITE, ui.ORANGE)):
            a0 = L + 17.0 + i * 1.6
            w0, w1 = hw * (2.4 - i * 0.8), hw * (1.6 - i * 0.8) if i < 2 else 0.0
            p0, p1, p2, p3 = tf(a0, -w0), tf(a0, w0), tf(a0 + 1.6, w1), tf(a0 + 1.6, -w1)
            pyxel.tri(*p0, *p1, *p2, col)
            pyxel.tri(*p0, *p2, *p3, col)
        for side in (-1, 0, 1):
            pyxel.line(*tf(L, 0.0), *tf(L + 17.0, side * hw * 2.4), ui.WHITE)

    def draw_ladder(self):
        """左端の高度の目盛り。ズームに合わせて間隔を変える。"""
        ppm = self.ppm
        step = next(s for s in (10, 50, 100, 500, 1000, 5000, 10_000, 50_000) if s * ppm >= 8)
        big = {10: 50, 50: 500, 100: 500, 500: 5000, 1000: 5000, 5000: 50_000}.get(step, step * 5)
        lo = int((self.cam_y - (ui.H - self.anchor_y) / ppm) // step) * step
        hi = int((self.cam_y + self.anchor_y / ppm) // step + 1) * step
        for alt in range(max(0, lo), hi + step, step):
            y = self.sy(alt)
            if not (0 <= y < ui.H):
                continue
            if alt % big == 0:
                pyxel.line(0, y, 14, y, ui.WHITE)
                label = f"{alt}m" if alt < 1000 and big < 500 else f"{alt / 1000:.2f}km" if big < 500 \
                    else f"{alt / 1000:.1f}km" if big < 5000 else f"{alt // 1000}km"
                ui.text(18, y - 5 * ui.K, label, ui.WHITE, size=10, border=ui.BLACK)
            else:
                pyxel.line(0, y, 6, y, ui.WHITE)

    def dashed(self, y, col):
        for x in range(0, self.view_w, 8):
            pyxel.line(x, y, x + 4, y, col)

    def draw_markers(self):
        """目標の高さ、着陸目標、着地予想点、噴射の目安。"""
        m, run, v = self.m, self.run, self.v
        if m.kind == "ascent":
            wp = m.waypoint
            wy = self.sy(wp.altitude)
            if 0 <= wy < ui.H:
                self.dashed(wy, ui.LIME)
                ui.text(self.view_w - 90, wy - 14, f"{wp.name} {wp.altitude / 1000:.1f}km", ui.LIME, border=ui.BLACK)
            return
        land = m.land
        if not land or run.result:
            return
        if land.hop_alt:
            wy = self.sy(land.hop_alt)
            if 0 <= wy < ui.H and run.apex < land.hop_alt:
                self.dashed(wy, ui.LIME)
                ui.text(self.view_w - 60, wy - 14, f"{land.hop_alt:.0f}m", ui.LIME, border=ui.BLACK)
        if self.phase != "flight" or (m.kind == "recover" and run.phase != "descent"):
            return
        # 噴射の目安の高さ
        cue = run.burn_cue()
        if cue is not None and not v.engine_on and v.y < run.LANDING_ALT:
            cy = self.sy(cue)
            if 0 <= cy < ui.H:
                col = ui.YELLOW if v.y > cue else ui.RED
                self.dashed(cy, col)
                ui.text(self.view_w - ui.text_width("噴射の目安", 10) - 8, cy - 13, "噴射の目安", col, size=10,
                        border=ui.BLACK)
        if land.site == "sea":
            return
        # 着陸目標: 画面の外にあるときは、端に矢印と距離を出す
        gy = min(ui.H - 14, max(30, self.sy(run.deck_y())))
        tx = self.sx(run.ship_x)
        d = run.ship_x - v.x
        if tx < 8 or tx > self.view_w - 8:
            ex = 10 if tx < 8 else self.view_w - 10
            sgn = -1 if tx < 8 else 1
            pyxel.tri(ex, gy - 6, ex, gy + 6, ex + sgn * 8, gy, ui.LIME)
            label = f"{abs(d) / 1000:.1f}km" if abs(d) >= 1000 else f"{abs(d):.0f}m"
            lx = ex + 12 if sgn < 0 else ex - 12 - ui.text_width(label, 10)
            ui.text(lx, gy - 5, label, ui.LIME, size=10, border=ui.BLACK)
        elif self.sy(run.deck_y()) > ui.H - 4:
            pyxel.tri(tx - 5, ui.H - 12, tx + 5, ui.H - 12, tx, ui.H - 4, ui.LIME)
        # 着地予想点
        if run.pred_x is not None and run.phase == "descent":
            px = self.sx(run.pred_x)
            py = min(ui.H - 4, max(40, self.sy(run.deck_y())))
            ok = abs(run.pred_x - run.ship_x) <= land.half_w
            if 4 <= px <= self.view_w - 4:
                col = ui.LIME if ok else ui.YELLOW
                pyxel.line(px - 4, py - 8, px + 4, py, col)
                pyxel.line(px + 4, py - 8, px - 4, py, col)

    def draw_messages(self):
        K = ui.K
        step = (self.fs + 6) * K
        mx = 8 * K if ui.COMPACT else 12
        # 飛行画面の幅に収まらないメッセージは折り返す
        lines = [(line, col) for text, col, _ in self.messages
                 for line in ui.wrap(text, self.view_w - mx * 2, self.fs)]
        y = ui.H - (self.fs + 14) * K - step * (len(lines) - 1)
        for line, col in lines:
            ui.text(mx, y, line, col, size=self.fs, border=ui.BLACK)
            y += step
        if self.phase == "count":
            ui.text_center(self.view_w // 2, ui.H // 3 if self.cold_open else ui.H // 4,
                           f"T-{max(0, math.ceil(self.count))}", ui.WHITE, border=ui.BLACK)
        if self.phase != "flight":
            return
        # いま押すキーの案内と、早送りの表示
        prompt = self.run.prompt()
        py = ui.H // 4 + (18 * K if ui.COMPACT else 26)
        if prompt and self.frame // 12 % 3:
            ui.text_center(self.view_w // 2, py, prompt, ui.YELLOW, border=ui.BLACK)
        if self.run.warp > 1:
            ui.text_center(self.view_w // 2, py + (self.fs + 8) * K, trf(">> 早送り ×{n}", n=self.run.warp), ui.CYAN,
                           size=10, border=ui.BLACK)

    def draw_alert_border(self):
        run = self.run
        if (run.fire_active or run.anomaly_left is not None) and self.frame // 8 % 2:
            for i in range(4):
                pyxel.rectb(i, i, self.view_w - 2 * i, ui.H - 2 * i, ui.RED)
            text = "!! エンジン火災 !!" if run.fire_active else "!! タンク異常 !!"
            ui.text_center(self.view_w // 2, 60 * ui.K, text, ui.RED, border=ui.BLACK)

    def top_box(self, text, border):
        """飛行画面の上に出す説明の枠。枠の下端の y を返す。"""
        fs, K = self.fs, ui.K
        lines = ui.wrap(text, self.view_w - 40 * K, fs)
        h = (14 + len(lines) * (fs + 4)) * K
        x, y, w = 12 * K, (24 if not ui.TINY else 18) * K, self.view_w - 24 * K
        pyxel.dither(0.8)
        pyxel.rect(x, y, w, h, ui.BLACK)
        pyxel.dither(1.0)
        pyxel.rectb(x, y, w, h, border)
        for i, line in enumerate(lines):
            ui.text(x + 8 * K, y + (7 + i * (fs + 4)) * K, line, ui.WHITE, size=fs)
        return y + h

    def draw_tutorial(self):
        """画面上部の操作説明。火災が起きたら消す。"""
        if not self.cold_open or self.phase == "end" or self.run.fire_active:
            return
        tid, text, _, _ = TUTORIAL[self.tut]
        bottom = self.top_box(text, ui.YELLOW if tid in ("ignite", "throttle", "steer") else ui.WHITE)
        if tid == "window" and self.frame // 15 % 2:  # 右のウィンドウを指す矢印
            ax, ay = self.view_w - 14, bottom + 10
            pyxel.tri(ax, ay - 6, ax, ay + 6, ax + 10, ay, ui.YELLOW)

    def draw_guide(self):
        """いまやることの案内(手順の何番目か)。"""
        small = ui.COMPACT
        help_text = "SPACE点火 ↑↓出力 ←→姿勢" if small else "SPACE 点火   ↑↓ スロットル   ←→ 姿勢"
        if self.m.sep or self.m.kind in ("orbit", "reentry"):
            help_text = "SPACE点火/停止 Z分離・放出" if small else "SPACE 点火/停止   Z 分離・放出   ↑↓ 出力   ←→ 姿勢"
            if self.m.kind == "reentry":
                help_text = "SPACE噴射 Zパラシュート" if small else "SPACE 噴射/停止   Z パラシュート   ←→ 姿勢"
        elif self.m.can_cutoff:
            help_text = "SPACE点火/停止 ↑↓出力" if small else "SPACE 点火/停止   ↑↓ スロットル   ←→ 姿勢"
        ui.text(self.view_w - ui.text_width(help_text, 10) - 8 * ui.K, 6 * ui.K, help_text, ui.WHITE, size=10,
                border=ui.BLACK)
        if self.cold_open or self.phase == "end" or self.run.fire_active or self.run.anomaly_left is not None:
            return
        guide = self.run.guide()
        if guide:
            i, n, text = guide
            self.top_box(trf("手順 {i}/{n}  ", i=i, n=n) + tr(text), ui.DBLUE)

    def draw_orbit_map(self):
        """軌道の形の小さな図(惑星と、いまの軌道)。機体はいつも惑星の真上にいるものとして描く。"""
        m, v = self.m, self.v
        if m.kind not in ("orbit", "reentry") or self.cam_y < 30_000 or self.phase == "end":
            return
        size = 58 * ui.K if ui.COMPACT else 92
        x0 = 6
        y0 = ui.H - size - (70 * ui.K if ui.COMPACT else 96)
        pyxel.rect(x0, y0, size, size, ui.BLACK)
        pyxel.rectb(x0, y0, size, size, ui.DBLUE)
        pyxel.clip(x0 + 1, y0 + 1, size - 2, size - 2)
        pe, ap = v.apsides()
        span = PLANET_R + max(320_000.0, min(ap if ap != math.inf else 0.0, 2_600_000.0) * 1.1)
        k = (size / 2 - 3) / span
        cx, cy = x0 + size / 2, y0 + size / 2 + (size * 0.12 if span < PLANET_R * 2 else 0)
        # いまの軌道: 機体の位置からの角度 phi ごとの半径
        r = PLANET_R + v.y
        h = r * v.vx
        eps = (v.vx ** 2 + v.vy ** 2) / 2 - MU / r
        e = math.sqrt(max(0.0, 1 + 2 * eps * h * h / (MU * MU)))
        if abs(h) > 1 and e < 0.999:
            p = h * h / MU
            nu0 = math.atan2(v.vy * h / MU, p / r - 1)  # 近地点から測った、いまの位置の角度
            prev = None
            col = ui.LIME if pe >= 70_000 else ui.YELLOW
            for i in range(37):
                phi = math.tau * i / 36
                rr = p / (1 + e * math.cos(nu0 + phi))
                pt = (cx + math.sin(phi) * rr * k, cy - math.cos(phi) * rr * k)
                if prev:
                    pyxel.line(*prev, *pt, col)
                prev = pt
        pyxel.circ(cx, cy, PLANET_R * k, ui.DBLUE)
        pyxel.circb(cx, cy, PLANET_R * k, ui.LBLUE)
        if m.orbit:  # 目標の高さ(近地点の下限)
            rr = (PLANET_R + m.orbit.pe_lo) * k
            for i in range(0, 36, 2):
                a0, a1 = math.tau * i / 36, math.tau * (i + 1) / 36
                pyxel.line(cx + math.sin(a0) * rr, cy - math.cos(a0) * rr, cx + math.sin(a1) * rr,
                           cy - math.cos(a1) * rr, ui.GRAY)
        pyxel.rect(cx - 1, cy - r * k - 1, 3, 3, ui.WHITE if self.frame // 10 % 2 else ui.RED)
        pyxel.clip(0, 0, self.view_w, ui.H)

    def draw_banner(self):
        run = self.run
        ok = run.result == "success"
        title = ("WP1 通過 ── ミッション成功" if self.m.kind == "ascent" else "ミッション成功") if ok else "ミッション失敗"
        sub = trf("ランク {rank}", rank=run.rank()) if ok else run.fail_reason
        K = ui.K
        subs = ui.wrap(sub, self.view_w - 16 * K)
        h = (70 + 14 * len(subs)) * K
        y = ui.H * 3 // 8
        pyxel.dither(0.7)
        pyxel.rect(0, y, self.view_w, h, ui.BLACK)
        pyxel.dither(1.0)
        ui.text_center(self.view_w // 2, y + 14 * K, title, ui.LIME if ok else ui.RED, size=10 if ui.TINY else 12)
        for i, line in enumerate(subs):
            ui.text_center(self.view_w // 2, y + (36 + i * 16) * K, line, ui.WHITE)
        if self.end_timer > 60 and self.frame // 20 % 2:
            ui.text_center(self.view_w // 2, y + h - 22 * K, "SPACE で続ける", ui.WHITE, size=10)

    # ---- 計器パネル ----
    def draw_panel(self):
        v = self.v
        run = self.run
        x = self.panel_x
        small, tiny, K = ui.COMPACT, ui.TINY, ui.K  # 720x720 は詰めた配置を K 倍
        vx_ = (52 if small else 64) * K  # 値の列
        row_h = (11 if tiny else 12 if small else 13) * K
        bh = 8 * K  # バーの太さ
        bw = ui.W - x - vx_ - 10 * K if small else 112  # バーの長さ
        pyxel.rect(x - 4, 0, ui.W - x + 4, ui.H, ui.NAVY)
        pyxel.line(x - 4, 0, x - 4, ui.H, ui.DBLUE)
        if tiny:  # 320x240: 目標は下のウィンドウに出ているので省く
            y = 4
            ui.text(x + 4, y, self.m.title, ui.YELLOW, size=10)
            y += 13
        else:
            y = 8 * K
            ui.text(x + 4 * K, y, self.m.title, ui.YELLOW, size=10 if K > 1 else 12)
            y += 16 * K
            for line in ui.wrap(self.m.goal, ui.W - x - 8 * K, 10)[:2]:
                ui.text(x + 4 * K, y, line, ui.WHITE, size=10)
                y += 12 * K
            y += 8 * K

        def row(label, value, col=ui.WHITE):
            nonlocal y
            ui.text(x + 4 * K, y, label, ui.GRAY, size=10)
            ui.text(x + vx_, y, value, col, size=10)
            y += row_h

        row("T+", f"{v.t:6.1f} s")
        row("高度", f"{v.y:8.0f} m" if v.y < 100_000 else f"{v.y / 1000:7.1f} km")
        row("垂直速度", f"{v.vy:+7.1f} m/s")
        row("水平速度", f"{v.vx:+7.1f} m/s")
        limit = self.m.land.q_limit if self.m.land and run.phase == "descent" else 30_000
        row("動圧", f"{v.q / 1000:6.1f} kPa", ui.ORANGE if limit and v.q > limit * 0.7 else ui.WHITE)
        row("傾き", f"{run.tilt_deg():+6.1f} °")
        if not tiny:
            row("角速度", f"{math.degrees(v.omega):+6.2f} °/s")
        aoa = math.degrees(v.aoa_tail if run.phase in ("descent", "entry", "deorbit") else v.aoa)
        if v.air_speed < 30:
            aoa = 0.0
        row("迎角", f"{aoa:+6.1f} °", ui.RED if abs(aoa) > 8 and v.q > 5000 else ui.WHITE)
        eng = tr("燃焼中") if v.engine_on else (tr("停止") if v.t > 0 else tr("待機", "engine"))
        eng_tpl = "{eng} 点火残{n}" if small else "{eng}  点火残 {n}"
        row("エンジン", trf(eng_tpl, eng=eng, n=v.ignitions_left), ui.ORANGE if v.engine_on else ui.WHITE)
        y += (2 if tiny else 4) * K

        def bar(label, frac, col, marker=None, text=None):
            nonlocal y
            ui.text(x + 4 * K, y, label, ui.GRAY, size=10)
            bx = x + vx_
            pyxel.rect(bx, y + K, bw, bh, ui.BLACK)
            pyxel.rect(bx, y + K, int(bw * max(0.0, min(1.0, frac))), bh, col)
            pyxel.rectb(bx, y + K, bw, bh, ui.DBLUE)
            if marker is not None:
                mx = bx + int(bw * marker)
                pyxel.rect(mx, y - K, K, bh + 3 * K, ui.WHITE)
            if text:
                ui.text(bx + bw - ui.text_width(text, 10) - 2 * K, y, text, ui.WHITE, size=10)
            y += row_h + K

        bar("出力" if small else "スロットル", v.throttle, ui.ORANGE, marker=v.throttle_cmd if v.engine_on else None,
            text=f"{v.throttle * 100:3.0f}%")
        bar("推進剤", v.prop / v.p.prop_mass, ui.LIME, text=f"{v.prop / v.p.prop_mass * 100:3.0f}%")
        bar("RCS", v.rcs_fuel / v.p.rcs_fuel, ui.CYAN)
        # ジンバル
        if v.p.gimbal_max:
            ui.text(x + 4 * K, y, "ジンバル", ui.GRAY, size=10)
            bx = x + vx_
            pyxel.rect(bx, y + K, bw, bh, ui.BLACK)
            pyxel.rect(bx + bw // 2, y, K, bh + 2 * K, ui.DBLUE)
            gx = bx + bw // 2 + int(v.gimbal / v.p.gimbal_max * (bw // 2 - 2 * K))
            pyxel.rect(gx - 2 * K, y + K, 5 * K, bh, ui.YELLOW)
            pyxel.rectb(bx, y + K, bw, bh, ui.DBLUE)
            y += row_h + (1 if tiny else 3) * K
        if run.fire_at is not None and (run.fire_active or run.heat > 0) and self.m.kind != "reentry":
            bar("温度", run.heat / 100, ui.RED, text="火災!" if run.fire_active else "")
        elif self.m.kind == "reentry" and run.phase != "deorbit":
            bar("温度", run.heat / 100, ui.RED if run.heat > 80 else ui.ORANGE, text=f"{run.heat:3.0f}")
        elif run.slosh > 0:
            bar("揺れ", run.slosh / run.SLOSH[1], ui.PINK)
        elif run.anomaly_left is not None:
            bar("タンク", 1.0 - run.anomaly_left / 5.0, ui.RED, text=f"{max(0.0, run.anomaly_left):.1f}")

        # 目標のウィンドウ(320x240 は見出しと進み具合を詰め、下の説明を省く)
        y += (2 if tiny else 4) * K
        rows = run.rows()
        ww = ui.W - x - 6 * K
        pad = (6 if small else 10) * K
        cols = (48 * K, 104 * K) if small else (64, 130)  # 範囲 / 現在値 の列
        n = len(rows)
        foot = self.m.kind == "ascent" and not tiny
        wh = 24 + row_h * n if tiny else 40 * K + (row_h + K) * n + (20 if foot else 4) * K
        wh = min(wh, ui.H - y - 2)
        ui.window(x, y, ww, wh, fill=ui.BLACK, border=ui.LIME, shadow=False)
        head, prog = self.objective()
        ui.text(x + pad, y + (4 if tiny else 8) * K, head, ui.LIME, size=10)
        pw = ww - pad * 2 - 4 * K if small else 160
        py, ph = (y + 16, 3) if tiny else (y + 24 * K, 6 * K)
        pyxel.rect(x + pad, py, pw, ph, ui.NAVY)
        pyxel.rect(x + pad, py, int(pw * min(1.0, max(0.0, prog))), ph, ui.LIME)
        yy = y + (22 if tiny else 38) * K
        for label, rng, cur, ok in rows:
            if yy + 10 * K > y + wh:
                break
            ui.text(x + pad, yy, tr(label, "window"), ui.GRAY, size=10)
            ui.text(x + cols[0], yy, rng, ui.WHITE, size=10)
            ui.text(x + cols[1], yy, cur, ui.LIME if ok else ui.RED, size=10)
            yy += row_h if tiny else row_h + K
        if foot:
            ui.text(x + pad, yy + 4 * K, "ウィンドウ内でランクUP" if small else "ウィンドウに入るほどランクが上がる", ui.GRAY, size=10)

    def objective(self):
        """目標のウィンドウの見出しと、進み具合(0〜1)。"""
        m, run, v = self.m, self.run, self.v
        small = ui.COMPACT
        if m.kind == "ascent":
            wp = m.waypoint
            head = trf("{name} 高度{alt:.0f}km 通過時" if small else "{name}  高度 {alt:.0f} km 通過時",
                       name=wp.name, alt=wp.altitude / 1000)
            return head, v.y / wp.altitude
        if m.kind in ("orbit", "recover") and run.phase == "s1":
            return tr("段分離の条件"), v.y / 40_000
        if m.kind == "orbit":
            return tr("放出の条件" if run.in_orbit else "目標の軌道"), v.vx / 2_200
        if m.kind == "reentry":
            e = m.entry
            if run.phase == "deorbit":
                return tr("再突入の条件"), (100_000 - v.y) / (100_000 - e.interface)
            return tr("着水の条件"), 1.0 - v.y / e.interface
        land = m.land
        if land.hop_alt and run.apex < land.hop_alt:
            return tr("着陸の条件"), run.apex / land.hop_alt
        return tr("着陸の条件"), 1.0 - (v.y - run.deck_y()) / max(run.apex, 100.0)
