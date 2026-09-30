"""ACT パート: ロケット操縦画面。"""

import math
import random

import pyxel

from . import ui
from .i18n import tr, trf
from .missions import MissionRun

ROCKET_W = 4.5  # 見やすさのため実寸(1.7 m)より太く描く
SUBSTEPS = 2
COUNTDOWN = 5.0


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "drag")

    def __init__(self, x, y, vx, vy, life, col, drag=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = life
        self.col = col
        self.drag = drag


class MissionScene:
    def __init__(self, app, mdef):
        self.app = app
        # 画面サイズごとの配置: 左が飛行画面、右が計器パネル
        panel_w = 144 if ui.SMALL else 196 if ui.W > 640 else 188
        self.panel_x = ui.W - panel_w
        self.view_w = self.panel_x - 4
        self.anchor_x = self.view_w // 2
        self.anchor_y = ui.H * 5 // 8  # 機体を置く高さ
        self.ppm = 1.0 if ui.TINY else 1.5 if ui.SMALL else 2.0  # 1 m あたりのピクセル数
        self.fs = 10 if ui.SMALL else 12  # 飛行画面に出すメッセージの文字
        self.m = mdef
        self.run = MissionRun(mdef, inspected=app.state.inspected)
        self.v = self.run.v
        self.phase = "count"  # count / ready / flight / end
        self.count = COUNTDOWN
        self.frame = 0
        self.end_timer = 0
        self.exploded = False
        self.particles = []
        self.messages = []  # [text, color, frames]
        self.cam_x = 0.0
        self.cam_y = 60.0
        rng = random.Random(7)
        self.clouds = [(rng.uniform(-600, 600), rng.uniform(1200, 4200), rng.uniform(60, 180), rng.uniform(14, 30))
                       for _ in range(40)]
        self.stars = [(rng.uniform(0, self.view_w), rng.uniform(0, ui.H), rng.choice((ui.WHITE, ui.LBLUE, ui.GRAY)))
                      for _ in range(160)]
        self.say("射場クリア。カウントダウン開始", ui.WHITE)

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

        if self.phase == "count":
            prev = math.ceil(self.count)
            self.count -= 1 / 60
            if math.ceil(self.count) != prev and self.count > 0:
                self.say(f"T-{math.ceil(self.count)}", ui.WHITE, 50)
            if self.count <= 0:
                self.phase = "ready"
                self.say("点火準備よし。SPACE で点火!", ui.YELLOW, 600)
        elif self.phase == "ready":
            if ignite:
                self.v.ignite()
                self.phase = "flight"
                self.say("点火!", ui.ORANGE, 90)
        elif self.phase == "flight":
            was_lifted = self.v.lifted_off
            for _ in range(SUBSTEPS):
                self.run.step(1 / 60 / SUBSTEPS, steer, thr)
                if self.run.result:
                    break
            if self.v.lifted_off and not was_lifted:
                self.say("リフトオフ!", ui.LIME, 120)
            for kind, text in self.run.events:
                col = {"warn": ui.RED, "bad": ui.RED, "good": ui.LIME, "info": ui.CYAN}.get(kind, ui.WHITE)
                self.say(text, col, 240)
            self.run.events.clear()
            if self.run.result:
                self.phase = "end"
                if self.run.result == "fail":
                    self.explode()
        elif self.phase == "end":
            self.end_timer += 1
            if self.run.result == "success" and not self.exploded:
                self.v.step(1 / 60, 0, 0)
            if self.end_timer > 60 and ui.confirm() or self.end_timer > 240:
                self.app.finish_mission(self.run)
                return

        self.update_particles()
        self.update_camera()
        for msg in self.messages:
            msg[2] -= 1
        self.messages = [m for m in self.messages if m[2] > 0]

    def explode(self):
        self.exploded = True
        v = self.v
        cx, cy = self.rocket_center()
        for _ in range(260):
            a = random.uniform(0, math.tau)
            s = random.uniform(5, 45)
            col = random.choice((ui.RED, ui.ORANGE, ui.YELLOW, ui.WHITE))
            self.particles.append(Particle(cx, cy, v.vx * 0.3 + math.cos(a) * s, v.vy * 0.3 + math.sin(a) * s,
                                           random.randint(20, 60), col, 0.03))
        for _ in range(80):
            a = random.uniform(0, math.tau)
            s = random.uniform(2, 12)
            self.particles.append(Particle(cx, cy, math.cos(a) * s, math.sin(a) * s,
                                           random.randint(90, 200), random.choice((ui.GRAY, ui.DBLUE)), 0.02))

    def rocket_center(self):
        v = self.v
        L = v.p.length
        return v.x + math.sin(v.theta) * L / 2, v.y + math.cos(v.theta) * L / 2

    def update_particles(self):
        v = self.v
        dt = 1 / 60
        if v.engine_on and v.throttle > 0.05 and not self.exploded:
            n = int(3 + 6 * v.throttle)
            ang = v.theta - v.gimbal
            ex, ey = -math.sin(ang), -math.cos(ang)
            for _ in range(n):
                spread = random.uniform(-0.18, 0.18)
                sp = random.uniform(40, 80)
                dx = ex * math.cos(spread) - ey * math.sin(spread)
                dy = ex * math.sin(spread) + ey * math.cos(spread)
                col = random.choice((ui.YELLOW, ui.ORANGE, ui.ORANGE, ui.RED, ui.WHITE))
                self.particles.append(Particle(v.x, v.y, v.vx + dx * sp, v.vy + dy * sp,
                                               random.randint(4, 9), col))
            # 地面付近の煙
            if v.y < 150:
                for _ in range(3):
                    side = random.choice((-1, 1))
                    self.particles.append(Particle(v.x + random.uniform(-4, 4), 0.5,
                                                   side * random.uniform(8, 25), random.uniform(0.5, 4),
                                                   random.randint(80, 160), random.choice((ui.WHITE, ui.GRAY)), 0.02))
            # 上空の飛行機雲
            elif v.y < 12_000 and self.frame % 2 == 0:
                self.particles.append(Particle(v.x + random.uniform(-1, 1), v.y - 3, v.vx * 0.1, v.vy * 0.1,
                                               random.randint(60, 120), ui.WHITE if v.y < 8000 else ui.LBLUE, 0.0))
        # 火災の炎
        if self.run.fire_active and not self.exploded:
            L = v.p.length
            for _ in range(4):
                h = random.uniform(0, L * 0.3)
                self.particles.append(Particle(v.x + math.sin(v.theta) * h + random.uniform(-2, 2),
                                               v.y + math.cos(v.theta) * h,
                                               v.vx + random.uniform(-6, 6), v.vy + random.uniform(-2, 6),
                                               random.randint(6, 14), random.choice((ui.RED, ui.ORANGE, ui.YELLOW))))
        alive = []
        for p in self.particles:
            p.life -= 1
            if p.life <= 0:
                continue
            if p.drag:
                p.vx *= 1 - p.drag
                p.vy *= 1 - p.drag
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.y < 0:
                p.y = 0
                p.vy = abs(p.vy) * 0.2
            alive.append(p)
        self.particles = alive[-1800:]

    def update_camera(self):
        cx, cy = self.rocket_center()
        tx = cx
        ty = max(cy, 60.0)
        self.cam_x += (tx - self.cam_x) * 0.2
        self.cam_y += (ty - self.cam_y) * 0.35

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
        self.draw_particles()
        if not self.exploded:
            self.draw_rocket()
        self.draw_ladder()
        self.draw_messages()
        self.draw_fire_border()
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
        for y in range(0, ui.H, 2):
            base, nxt, t = self.sky_color(self.cam_y + (self.anchor_y - y) / self.ppm)
            pyxel.rect(0, y, self.view_w, 2, base)
            if t > 0:
                pyxel.dither(t)
                pyxel.rect(0, y, self.view_w, 2, nxt)
                pyxel.dither(1.0)
        alt = self.cam_y
        if alt > 8000:
            a = min(1.0, (alt - 8000) / 10000)
            pyxel.dither(a)
            for x, y, c in self.stars:
                pyxel.pset(x, y, c)
            pyxel.dither(1.0)
    def draw_clouds(self):
        for wx, wy, w, h in self.clouds:
            x, y = self.sx(wx), self.sy(wy)
            if -w * self.ppm < x < self.view_w + w * self.ppm and -h * self.ppm < y < ui.H + h * self.ppm:
                pyxel.elli(x - w * self.ppm / 2, y - h * self.ppm / 2 + 6, w * self.ppm, h * self.ppm, ui.GRAY)
                pyxel.elli(x - w * self.ppm / 2, y - h * self.ppm / 2, w * self.ppm, h * self.ppm, ui.WHITE)

    def draw_ground(self):
        gy = self.sy(0)
        if gy > ui.H:
            return
        # 海
        pyxel.rect(0, gy, self.view_w, ui.H - gy, ui.DBLUE)
        for i in range(0, int(ui.H - gy) // 14 + 1):
            y = gy + 8 + i * 14
            off = (self.frame // 2 + i * 13) % 40
            for x in range(-40 + off, self.view_w, 40):
                pyxel.line(x, y, x + 12, y, ui.CYAN)
        # 島
        x0, x1 = self.sx(-130), self.sx(130)
        pyxel.rect(x0, gy, x1 - x0, 10, ui.YELLOW)
        pyxel.rect(x0 + 10, gy + 10, x1 - x0 - 20, 8, ui.BROWN)
        pyxel.rect(self.sx(-110), gy - 3, self.sx(110) - self.sx(-110), 3, ui.LIME)
        # ヤシの木
        for tx in (-100, -78, 70, 96):
            x = self.sx(tx)
            pyxel.line(x, gy - 3, x + 2, gy - 26, ui.BROWN)
            for dx, dy in ((-10, 4), (10, 4), (-7, -2), (8, -3)):
                pyxel.line(x + 2, gy - 26, x + 2 + dx, gy - 26 + dy, ui.TEAL)
        # 格納庫
        hx = self.sx(-60)
        pyxel.rect(hx, gy - 22, 40, 19, ui.GRAY)
        pyxel.rect(hx + 12, gy - 14, 16, 11, ui.NAVY)
        # 発射台とタワー
        pyxel.rect(self.sx(-12), gy - 5, 24 * self.ppm, 5, ui.GRAY)
        tx = self.sx(5)
        top = self.sy(26)
        pyxel.line(tx, top, tx, gy - 5, ui.WHITE)
        pyxel.line(tx + 8, top, tx + 8, gy - 5, ui.WHITE)
        y = top
        while y < gy - 5:
            pyxel.line(tx, y, tx + 8, y + 8, ui.WHITE)
            pyxel.line(tx + 8, y, tx, y + 8, ui.WHITE)
            y += 8

    def draw_particles(self):
        for p in self.particles:
            x, y = self.sx(p.x), self.sy(p.y)
            if 0 <= x < self.view_w and 0 <= y < ui.H:
                if p.life > 40 and p.col in (ui.WHITE, ui.GRAY):
                    pyxel.rect(x - 1, y - 1, 3, 3, p.col)
                else:
                    pyxel.pset(x, y, p.col)

    def draw_rocket(self):
        v = self.v
        L = v.p.length
        s, c = math.sin(v.theta), math.cos(v.theta)
        ax, ay = s, c  # 機体軸(上向き)
        nx, ny = c, -s  # 機体の右方向

        def pt(along, across):
            wx = v.x + ax * along + nx * across
            wy = v.y + ay * along + ny * across
            return self.sx(wx), self.sy(wy)

        hw = ROCKET_W / 2
        body_top = L * 0.86

        def quad(a0, a1, col):
            p0, p1, p2, p3 = pt(a0, -hw), pt(a0, hw), pt(a1, hw), pt(a1, -hw)
            pyxel.tri(*p0, *p1, *p2, col)
            pyxel.tri(*p0, *p2, *p3, col)

        quad(0, body_top, ui.WHITE)
        quad(L * 0.55, L * 0.62, ui.BLACK)
        # 陰になる側
        p0, p1, p2, p3 = pt(0, hw * 0.4), pt(0, hw), pt(body_top, hw), pt(body_top, hw * 0.4)
        pyxel.tri(*p0, *p1, *p2, ui.GRAY)
        pyxel.tri(*p0, *p2, *p3, ui.GRAY)
        tip = pt(L, 0)
        pyxel.tri(*pt(body_top, -hw), *pt(body_top, hw), *tip, ui.WHITE)
        # ノズル(ジンバル角だけ振れる)
        g = v.theta - v.gimbal
        gs, gc = math.sin(g), math.cos(g)
        base = pt(0, 0)
        n_len, n_w = 3.0, 1.6
        tip_l = (self.sx(v.x - gs * n_len - gc * n_w), self.sy(v.y - gc * n_len + gs * n_w))
        tip_r = (self.sx(v.x - gs * n_len + gc * n_w), self.sy(v.y - gc * n_len - gs * n_w))
        pyxel.tri(*base, *tip_l, *tip_r, ui.DBLUE)
        if v.engine_on and v.throttle > 0.05:
            flen = (6 + 10 * v.throttle + pyxel.rndf(0, 3)) * (1.0 + min(1.5, v.y / 15000))
            fx = self.sx(v.x - gs * (n_len + flen))
            fy = self.sy(v.y - gc * (n_len + flen))
            pyxel.tri(*tip_l, *tip_r, fx, fy, ui.ORANGE)
            mx = self.sx(v.x - gs * (n_len + flen * 0.55))
            my = self.sy(v.y - gc * (n_len + flen * 0.55))
            inner_l = ((tip_l[0] * 2 + tip_r[0]) / 3, (tip_l[1] * 2 + tip_r[1]) / 3)
            inner_r = ((tip_l[0] + tip_r[0] * 2) / 3, (tip_l[1] + tip_r[1] * 2) / 3)
            pyxel.tri(*inner_l, *inner_r, mx, my, ui.YELLOW)        # スラスター噴射
        if v.rcs_firing:
            side = -v.rcs_firing
            for along in (L * 0.8,):
                x, y = pt(along, side * (hw + 1))
                pyxel.line(x, y, x + side * nx * 8, y - side * ny * 8, ui.WHITE)

    def draw_ladder(self):
        base = self.cam_y
        lo = int((base - self.anchor_y / self.ppm - 60) // 50) * 50
        hi = int((base + (ui.H - self.anchor_y) / self.ppm + 200) // 50) * 50
        lo, hi = min(lo, hi), max(lo, hi)
        for alt in range(max(0, lo), hi + 200, 50):
            y = self.sy(alt)
            if not (0 <= y < ui.H):
                continue
            if alt % 500 == 0:
                pyxel.line(0, y, 14, y, ui.WHITE)
                ui.text(18, y - 5, f"{alt / 1000:.1f}km", ui.WHITE, size=10, border=ui.BLACK)
            else:
                pyxel.line(0, y, 6, y, ui.WHITE)
        # WP1 の高さ
        wy = self.sy(self.m.waypoint.altitude)
        if 0 <= wy < ui.H:
            for x in range(0, self.view_w, 8):
                pyxel.line(x, wy, x + 4, wy, ui.LIME)
            ui.text(self.view_w - 90, wy - 14, "WP1 10.0km", ui.LIME, border=ui.BLACK)

    def draw_messages(self):
        step = self.fs + 6
        mx = 8 if ui.SMALL else 12
        # 飛行画面の幅に収まらないメッセージは折り返す
        lines = [(line, col) for text, col, _ in self.messages
                 for line in ui.wrap(text, self.view_w - mx * 2, self.fs)]
        y = ui.H - self.fs - 14 - step * (len(lines) - 1)
        for line, col in lines:
            ui.text(mx, y, line, col, size=self.fs, border=ui.BLACK)
            y += step
        help_text = "SPACE点火 ↑↓出力 ←→姿勢" if ui.SMALL else "SPACE 点火   ↑↓ スロットル   ←→ 姿勢"
        ui.text(self.view_w - ui.text_width(help_text, 10) - 8, 6, help_text, ui.WHITE, size=10, border=ui.BLACK)
        if self.phase == "count":
            ui.text_center(self.view_w // 2, ui.H // 4, f"T-{max(0, math.ceil(self.count))}", ui.WHITE, border=ui.BLACK)

    def draw_fire_border(self):
        if self.run.fire_active and self.frame // 8 % 2:
            for i in range(4):
                pyxel.rectb(i, i, self.view_w - 2 * i, ui.H - 2 * i, ui.RED)
            ui.text_center(self.view_w // 2, 60, "!! エンジン火災 !!", ui.RED, border=ui.BLACK)

    def draw_banner(self):
        ok = self.run.result == "success"
        title = "WP1 通過 ── ミッション成功" if ok else "ミッション失敗"
        sub = trf("ランク {rank}", rank=self.run.rank()) if ok else self.run.fail_reason
        subs = ui.wrap(sub, self.view_w - 16)
        h = 70 + 14 * len(subs)
        y = ui.H * 3 // 8
        pyxel.dither(0.7)
        pyxel.rect(0, y, self.view_w, h, ui.BLACK)
        pyxel.dither(1.0)
        ui.text_center(self.view_w // 2, y + 14, title, ui.LIME if ok else ui.RED, size=10 if ui.TINY else 12)
        for i, line in enumerate(subs):
            ui.text_center(self.view_w // 2, y + 36 + i * 16, line, ui.WHITE)
        if self.end_timer > 60 and self.frame // 20 % 2:
            ui.text_center(self.view_w // 2, y + h - 22, "SPACE で続ける", ui.WHITE, size=10)

    # ---- 計器パネル ----
    def draw_panel(self):
        v = self.v
        run = self.run
        x = self.panel_x
        small, tiny = ui.SMALL, ui.TINY
        vx_ = 52 if small else 64  # 値の列
        row_h = 11 if tiny else 12 if small else 13
        bw = ui.W - x - vx_ - 10 if small else 112  # バーの長さ
        pyxel.rect(x - 4, 0, ui.W - x + 4, ui.H, ui.NAVY)
        pyxel.line(x - 4, 0, x - 4, ui.H, ui.DBLUE)
        if tiny:  # 320x240: 目標は WP の窓に出ているので省く
            y = 4
            ui.text(x + 4, y, self.m.title, ui.YELLOW, size=10)
            y += 13
        else:
            y = 8
            ui.text(x + 4, y, self.m.title, ui.YELLOW)
            y += 16
            ui.text(x + 4, y, self.m.goal, ui.WHITE, size=10)
            y += 20

        def row(label, value, col=ui.WHITE):
            nonlocal y
            ui.text(x + 4, y, label, ui.GRAY, size=10)
            ui.text(x + vx_, y, value, col, size=10)
            y += row_h

        row("T+", f"{v.t:6.1f} s")
        row("高度", f"{v.y:8.0f} m")
        row("垂直速度", f"{v.vy:+7.1f} m/s")
        row("水平速度", f"{v.vx:+7.1f} m/s")
        row("動圧", f"{v.q / 1000:6.1f} kPa", ui.ORANGE if v.q > 30_000 else ui.WHITE)
        row("傾き", f"{math.degrees(v.theta):+6.1f} °")
        if not tiny:
            row("角速度", f"{math.degrees(v.omega):+6.2f} °/s")
        aoa = math.degrees(v.aoa)
        row("迎角", f"{aoa:+6.1f} °", ui.RED if abs(aoa) > 8 else ui.WHITE)
        eng = tr("燃焼中") if v.engine_on else (tr("停止") if v.t > 0 else tr("待機", "engine"))
        eng_tpl = "{eng} 点火残{n}" if small else "{eng}  点火残 {n}"
        row("エンジン", trf(eng_tpl, eng=eng, n=v.ignitions_left), ui.ORANGE if v.engine_on else ui.WHITE)
        y += 2 if tiny else 4

        def bar(label, frac, col, marker=None, text=None):
            nonlocal y
            ui.text(x + 4, y, label, ui.GRAY, size=10)
            bx = x + vx_
            pyxel.rect(bx, y + 1, bw, 8, ui.BLACK)
            pyxel.rect(bx, y + 1, int(bw * max(0.0, min(1.0, frac))), 8, col)
            pyxel.rectb(bx, y + 1, bw, 8, ui.DBLUE)
            if marker is not None:
                mx = bx + int(bw * marker)
                pyxel.line(mx, y - 1, mx, y + 10, ui.WHITE)
            if text:
                ui.text(bx + bw - ui.text_width(text, 10) - 2, y, text, ui.WHITE, size=10)
            y += row_h + 1

        bar("出力" if small else "スロットル", v.throttle, ui.ORANGE, marker=v.throttle_cmd, text=f"{v.throttle * 100:3.0f}%")
        bar("推進剤", v.prop / v.p.prop_mass, ui.LIME, text=f"{v.prop / v.p.prop_mass * 100:3.0f}%")
        bar("RCS", v.rcs_fuel / v.p.rcs_fuel, ui.CYAN)
        # ジンバル
        ui.text(x + 4, y, "ジンバル", ui.GRAY, size=10)
        bx = x + vx_
        pyxel.rect(bx, y + 1, bw, 8, ui.BLACK)
        pyxel.line(bx + bw // 2, y, bx + bw // 2, y + 10, ui.DBLUE)
        gx = bx + bw // 2 + int(v.gimbal / v.p.gimbal_max * (bw // 2 - 2))
        pyxel.rect(gx - 2, y + 1, 5, 8, ui.YELLOW)
        pyxel.rectb(bx, y + 1, bw, 8, ui.DBLUE)
        y += row_h + (1 if tiny else 3)
        if run.fire_at is not None and (run.fire_active or run.heat > 0):
            bar("温度", run.heat / 100, ui.RED, text="火災!" if run.fire_active else "")

        # WP1 の窓(320x240 は見出しと進み具合を詰め、下の説明を省く)
        y += 2 if tiny else 4
        wp = self.m.waypoint
        ww = ui.W - x - 6
        pad = 6 if small else 10
        cols = (48, 104) if small else (64, 130)  # 窓 / 現在値 の列
        n = len(wp.windows)
        wh = 24 + row_h * n if tiny else 38 + (row_h + 1) * n + 22 if small else 150
        ui.window(x, y, ww, wh, fill=ui.BLACK, border=ui.LIME, shadow=False)
        head = trf("{name} 高度{alt:.0f}km 通過時" if small else "{name}  高度 {alt:.0f} km 通過時",
                   name=wp.name, alt=wp.altitude / 1000)
        ui.text(x + pad, y + (4 if tiny else 8), head, ui.LIME, size=10)
        prog = min(1.0, max(0.0, v.y / wp.altitude))
        pw = ww - pad * 2 - 4 if small else 160
        py, ph = (y + 16, 3) if tiny else (y + 24, 6)
        pyxel.rect(x + pad, py, pw, ph, ui.NAVY)
        pyxel.rect(x + pad, py, int(pw * prog), ph, ui.LIME)
        yy = y + (22 if tiny else 38)
        status = run.window_status() if run.wp_values is None else \
            {k: (run.wp_values[k], w.ok(run.wp_values[k])) for k, w in wp.windows.items()}
        for key, win in wp.windows.items():
            cur, ok = status[key]
            ui.text(x + pad, yy, tr(win.label, "window"), ui.GRAY, size=10)
            rng = f"{win.lo:.0f}~{win.hi:.0f}" if small else f"{win.lo:+.0f}~{win.hi:+.0f}"
            ui.text(x + cols[0], yy, rng, ui.WHITE, size=10)
            ui.text(x + cols[1], yy, f"{cur:+.0f}", ui.LIME if ok else ui.RED, size=10)
            yy += row_h if tiny else row_h + 1
        if not tiny:
            ui.text(x + pad, yy + 4, "窓に入るほどランクUP" if small else "窓に入るほどランクが上がる", ui.GRAY, size=10)
