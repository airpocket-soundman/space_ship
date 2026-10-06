"""ACT パート: 近接操作(ステーションの把持点でカプセルを止める)。"""

import math
import random

import pyxel

from . import audio, flight_hud, rocket_art, ui
from .docking import DockRun
from .i18n import tr, trf
from .particles import Particles

COUNTDOWN = 3.0
SUBSTEPS = 2


class DockScene:
    def __init__(self, app, mdef):
        self.app = app
        self.m = mdef
        self.run = DockRun(mdef)
        # 配置は打ち上げ画面と同じ: 左上が飛行画面、右がメッセージ欄、下が計器
        self.lay = flight_hud.FlightLayout()
        self.view_w, self.view_h = self.lay.view_w, self.lay.view_h
        self.phase = "count"  # count / flight / end
        self.count = COUNTDOWN
        self.frame = 0
        self.end_timer = 0
        self.ppm = 1.0
        self.messages = []
        self.parts = Particles()
        self.parts.ground = lambda x: -1e9  # 宇宙には地面がない
        rng = random.Random(11)
        self.stars = [(rng.uniform(0, self.view_w), rng.uniform(0, self.view_h), rng.choice((ui.WHITE, ui.LBLUE, ui.GRAY)))
                      for _ in range(120)]
        audio.bgm(None)
        self.say("ステーションまで 170 m。接近を始める", ui.WHITE)
        self.update_zoom(snap=True)

    def say(self, text, col=ui.WHITE, frames=0):
        """右のメッセージ欄に通知を足す(古いものから押し出される)。"""
        self.messages.append([tr(text), col, frames])
        self.messages = self.messages[-8:]

    # ---- 更新 ----
    def update(self):
        self.frame += 1
        run = self.run
        ix = (1 if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT) else 0) - \
             (1 if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT) else 0)
        iy = (1 if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP) else 0) - \
             (1 if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN) else 0)
        if self.phase == "count":
            self.count -= 1 / 60
            if self.count <= 0:
                self.phase = "flight"
        elif self.phase == "flight":
            for _ in range(SUBSTEPS):
                run.step(1 / 60 / SUBSTEPS, ix, iy)
            self.parts.update(run.x, run.y, 400.0, 0.0)
            # スラスターの噴射(押した向きと逆へ噴く)
            tx, ty = run.thrust
            if tx:
                self.parts.jet(run.x - tx * 2.0, run.y, run.vx, run.vy, -math.pi / 2 * tx, 2, 9.0)
            if ty:
                self.parts.jet(run.x, run.y - ty * 2.0, run.vx, run.vy, 0.0 if ty < 0 else math.pi, 2, 9.0)
            audio.engine(0.35 if tx or ty else 0)
            if run.result:
                self.phase = "end"
                audio.engine(0)
                if run.result == "fail" and "衝突" in run.fail_reason:
                    audio.explosion()
                    self.parts.burst(run.x, run.y, 0, 0, 80, 8.0, 60, (ui.WHITE, ui.GRAY, ui.YELLOW), 0.0, 0.0)
        else:
            self.parts.update(run.x, run.y, 400.0, 0.0)
            self.end_timer += 1
            if self.end_timer > 60 and ui.confirm():  # 「SPACE で続ける」を出しているので、押すまで待つ
                self.app.finish_mission(run)
                return
        for kind, text in run.events:
            col = {"warn": ui.RED, "bad": ui.RED, "good": ui.LIME, "info": ui.CYAN}.get(kind, ui.WHITE)
            self.say(text, col, 240)
        run.events.clear()
        self.update_zoom()

    def update_zoom(self, snap=False):
        """カプセルと把持点の両方が入るように、近づくほど大きく映す。"""
        run = self.run
        span = max(abs(run.x) + 14, abs(run.y) * 1.6 + 14, 18)
        want = min(10.0 if not ui.SMALL else 6.0, (self.view_w * 0.42) / span)
        self.ppm = want if snap else self.ppm + (want - self.ppm) * 0.05
        # 把持点を画面の右寄りに置く(ステーションは右、カプセルは左から来る)
        self.ox = self.view_w * 0.58
        self.oy = self.view_h * 0.5

    def sx(self, x):
        return self.ox + x * self.ppm

    def sy(self, y):
        return self.oy - y * self.ppm

    # ---- 描画 ----
    def draw(self):
        pyxel.clip(0, 0, self.view_w, self.view_h)
        pyxel.rect(0, 0, self.view_w, self.view_h, ui.BLACK)
        for x, y, c in self.stars:
            pyxel.pset(x, y, c)
        # 下に地球の縁
        vh = self.view_h
        pyxel.elli(-self.view_w * 1.1, vh * 0.86 - 3, self.view_w * 3.2, vh, ui.LBLUE)
        pyxel.elli(-self.view_w * 1.1, vh * 0.86, self.view_w * 3.2, vh, ui.DBLUE)
        self.draw_station()
        self.parts.draw(self.ox, self.oy, 0.0, 0.0, self.ppm, self.view_w, self.view_h)
        self.draw_capsule()
        self.draw_texts()
        if self.phase == "end":
            self.draw_banner()
        pyxel.clip()
        self.draw_message_panel()
        self.draw_hud()

    def draw_station(self):
        run, ppm, sx, sy = self.run, self.ppm, self.sx, self.sy
        x0, y0, x1, y1 = run.STATION
        # 太陽電池パネル
        for px in (x0 + 12, x1 - 8):
            for sgn in (1, -1):
                top = sy(sgn * 24) if sgn > 0 else sy(y0)
                pyxel.rect(sx(px - 4), top, 8 * ppm, 18 * ppm, ui.DBLUE)
                pyxel.rectb(sx(px - 4), top, 8 * ppm, 18 * ppm, ui.LBLUE)
        # 本体
        pyxel.rect(sx(x0), sy(y1), (x1 - x0) * ppm, (y1 - y0) * ppm, ui.GRAY)
        pyxel.rect(sx(x0), sy(y1), (x1 - x0) * ppm, 3 * ppm, ui.WHITE)
        for mx in range(int(x0) + 10, int(x1), 10):
            pyxel.line(sx(mx), sy(y1), sx(mx), sy(y0), ui.NAVY)
        # ロボットアームと把持点
        pyxel.line(sx(x0), sy(3.0), sx(2.5), sy(5.0), ui.WHITE)
        pyxel.line(sx(2.5), sy(5.0), sx(0.0), sy(1.8), ui.WHITE)
        grabbed = run.result == "success"
        b = run.BOX
        col = ui.LIME if run.hold > 0 or grabbed else ui.TEAL
        pyxel.rectb(sx(-b), sy(b), b * 2 * ppm, b * 2 * ppm, col)
        if not grabbed and self.frame // 20 % 2:
            pyxel.rectb(sx(-b) - 2, sy(b) - 2, b * 2 * ppm + 4, b * 2 * ppm + 4, col)
        # 接近禁止ゾーン(この内側は速度制限)
        pyxel.dither(0.5)
        pyxel.circb(sx(0), sy(0), run.ZONE * ppm, ui.YELLOW)
        pyxel.dither(1.0)

    def draw_capsule(self):
        run, ppm = self.run, self.ppm
        if run.result == "fail" and "衝突" in run.fail_reason:
            return
        # 先端をステーション(右)へ向けたカプセル。近くでは実寸に合わせて縮め、遠くでは見える大きさに保つ
        k = max(0.55, min(1.5, 1.8 / ppm))
        cx, cy = self.sx(run.x), self.sy(run.y)
        tf = lambda along, across: (cx + (along - 2.0) * k * ppm, cy + across * k * ppm)  # noqa: E731
        rocket_art.capsule(tf, 0.0, rocket_art.HALF_W["phoenix"], trunk=True)
        # 速度の向きと大きさ(相対速度)
        if self.phase == "flight" and run.speed > 0.03:
            s = min(60.0, 24.0 * run.speed + 6)
            ex = cx + run.vx / run.speed * s
            ey = cy - run.vy / run.speed * s
            pyxel.line(cx, cy, ex, ey, ui.CYAN)
            pyxel.circ(ex, ey, 1, ui.CYAN)

    def draw_texts(self):
        """飛行画面の中: カウントダウンの大きな数字。"""
        if self.phase == "count":
            flight_hud.big_count(self.lay, max(0, math.ceil(self.count)))

    def draw_banner(self):
        run = self.run
        ok = run.result == "success"
        K = ui.K
        sub = trf("ランク {rank}", rank=run.rank()) if ok else run.fail_reason
        subs = ui.wrap(sub, self.view_w - 16 * K)
        h = (70 + 14 * len(subs)) * K
        y = (self.view_h - h) // 2
        pyxel.dither(0.7)
        pyxel.rect(0, y, self.view_w, h, ui.BLACK)
        pyxel.dither(1.0)
        ui.text_center(self.view_w // 2, y + 14 * K, "ミッション成功" if ok else "ミッション失敗",
                       ui.LIME if ok else ui.RED, size=10 if ui.TINY else 12)
        for i, line in enumerate(subs):
            ui.text_center(self.view_w // 2, y + (36 + i * 16) * K, line, ui.WHITE)
        if self.end_timer > 60 and self.frame // 20 % 2:
            ui.text_center(self.view_w // 2, y + h - 22 * K, "SPACE で続ける", ui.WHITE, size=10)

    def draw_message_panel(self):
        run = self.run
        guide = ""
        if self.phase != "end":
            if run.dist > run.ZONE:
                i, text = 1, "←→↑↓ で噴いて、緑の枠(把持点)へ近づく。水色の線がいまの動き"
            elif run.dist > run.BOX:
                i, text = 2, trf("黄色の円の内側は {v} m/s 以下で。反対に噴いて減速する", v=run.ZONE_SPEED)
            else:
                i, text = 3, trf("枠の中で止まる。{t:.0f} 秒静止すれば、アームがつかむ", t=run.HOLD_TIME)
            guide = trf("手順 {i}/{n}  ", i=i, n=3) + tr(text)
        prompt = run.prompt() if self.phase == "flight" else ""
        if self.phase == "end" and self.end_timer > 60:
            prompt = "SPACE で続ける"
        log = [(text, col) for text, col, _ in self.messages]
        flight_hud.draw_messages(self.lay, tr(self.m.title), tr(self.m.goal), guide, ui.DBLUE, [], tr(prompt),
                                 self.frame // 12 % 3 != 0, "", log, [tr("←→↑↓ スラスター")])

    def draw_hud(self):
        run, small = self.run, ui.COMPACT
        left = self.m.time_limit - run.t
        if small:
            l1 = [("T+", f"{run.t:.1f}", ui.WHITE), ("残り", f"{max(0.0, left):.0f}", ui.RED if left < 30 else ui.WHITE),
                  ("距離", f"{run.dist:.1f}", ui.WHITE)]
            l2 = [("前後", f"{run.vx:+.2f}", ui.WHITE), ("上下", f"{run.vy:+.2f}", ui.WHITE)]
        else:
            l1 = [("T+", f"{run.t:.1f} s", ui.WHITE),
                  ("残り時間", f"{max(0.0, left):.1f} s", ui.RED if left < 30 else ui.WHITE),
                  ("距離", f"{run.dist:.1f} m", ui.WHITE)]
            l2 = [("前後の速度", f"{run.vx:+.2f} m/s", ui.WHITE), ("上下の速度", f"{run.vy:+.2f} m/s", ui.WHITE)]
        bars = [("燃料", run.fuel / run.FUEL, ui.CYAN, None, f"{run.fuel / run.FUEL * 100:.0f}%")]
        flight_hud.draw_hud(self.lay, l1, l2, bars, tr("把持の条件"), 1.0 - run.dist / 170.0, run.rows())
