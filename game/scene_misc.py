"""タイトル・リザルト・ゲームオーバー画面。"""

import math
import random

import pyxel

from . import ui


class TitleScene:
    def __init__(self, app):
        self.app = app
        self.frame = 0
        rng = random.Random(3)
        self.stars = [(rng.uniform(0, ui.W), rng.uniform(0, ui.H), rng.random()) for _ in range(220)]

    def update(self):
        self.frame += 1
        if ui.confirm():
            self.app.new_game()

    def draw(self):
        pyxel.cls(ui.BLACK)
        for x, y, ph in self.stars:
            if math.sin(self.frame / 25 + ph * 20) > -0.3:
                pyxel.pset(x, y, ui.WHITE if ph > 0.5 else ui.GRAY)
        # 地球の縁
        pyxel.circ(ui.W // 2, ui.H + 620, 700, ui.DBLUE)
        pyxel.circ(ui.W // 2, ui.H + 628, 700, ui.NAVY)
        # 上昇するロケット
        t = self.frame % 480
        rx = 470 + t * 0.15
        ry = 420 - t * 1.1
        pyxel.line(rx, ry + 20, rx - t * 0.05, ui.H, ui.GRAY)
        pyxel.rect(rx - 2, ry, 5, 18, ui.WHITE)
        pyxel.tri(rx - 2, ry, rx + 2, ry, rx, ry - 6, ui.WHITE)
        pyxel.tri(rx - 2, ry + 18, rx + 2, ry + 18, rx, ry + 26 + (self.frame % 4), ui.ORANGE)
        scale = 12
        w = ui.big_text_width("STARX", scale)
        ui.big_text((ui.W - w) // 2, 120, "STARX", scale, ui.WHITE, shadow=ui.DBLUE)
        ui.text_center(ui.W // 2, 220, "ロケット経営 × 操縦ゲーム", ui.LBLUE)
        ui.text_center(ui.W // 2, 240, "DEMO  ─  Chapter 1-1「初飛行」", ui.GRAY, size=10)
        if self.frame // 30 % 2:
            ui.text_center(ui.W // 2, 330, "PRESS SPACE", ui.YELLOW)
        ui.text_center(ui.W // 2, ui.H - 20, "これは実在の宇宙企業へのオマージュ(パロディ)作品です", ui.GRAY, size=10)


class ResultScene:
    def __init__(self, app, run, summary):
        self.app = app
        self.run = run
        self.s = summary
        self.frame = 0

    def update(self):
        self.frame += 1
        if self.frame > 30 and ui.confirm():
            self.app.back_to_office_after(self.run)

    def draw(self):
        pyxel.cls(ui.NAVY)
        run = self.run
        ok = run.result == "success"
        ui.window(60, 40, ui.W - 120, ui.H - 80, fill=ui.BLACK, border=ui.LIME if ok else ui.RED)
        ui.text_center(ui.W // 2, 60, "飛行結果", ui.WHITE)
        ui.text_center(ui.W // 2, 86, "ミッション成功" if ok else "ミッション失敗", ui.LIME if ok else ui.RED)
        if not ok:
            ui.text_center(ui.W // 2, 106, run.fail_reason, ui.WHITE)
        y = 136
        wp = run.m.waypoint
        ui.text(100, y, f"{wp.name}(高度 {wp.altitude / 1000:.0f} km 通過時)", ui.YELLOW)
        y += 22
        for key, win in wp.windows.items():
            ui.text(120, y, win.label, ui.GRAY)
            ui.text(230, y, f"窓 {win.lo:+.0f} ~ {win.hi:+.0f} {win.unit}", ui.WHITE)
            if run.wp_values:
                val = run.wp_values[key]
                good = win.ok(val)
                ui.text(430, y, f"{val:+.1f}", ui.LIME if good else ui.RED)
                ui.text(500, y, "○" if good else "×", ui.LIME if good else ui.RED)
            else:
                ui.text(430, y, "---", ui.GRAY)
            y += 18
        y += 10
        ui.text(100, y, f"ランク {run.rank()}", ui.YELLOW)
        ui.text(260, y, f"最高高度 {run.max_alt / 1000:.2f} km", ui.WHITE)
        y += 30
        s = self.s
        ui.text(100, y, "会社への影響", ui.YELLOW)
        y += 22
        ui.text(120, y, f"テレメトリ +{s['tlm']}", ui.CYAN)
        y += 18
        rep = s["rep"]
        ui.text(120, y, f"評判 {rep:+d}", ui.LIME if rep >= 0 else ui.RED)
        y += 18
        ui.text(120, y, "機体 -1(Eagle 1 は使い捨て)", ui.WHITE)
        if self.frame // 20 % 2:
            ui.text_center(ui.W // 2, ui.H - 64, "SPACE で工場へ戻る", ui.WHITE)


class GameOverScene:
    def __init__(self, app, lines):
        self.app = app
        self.dlg = ui.Dialogue()
        self.dlg.start(lines, on_done=app.to_title)
        self.frame = 0

    def update(self):
        self.frame += 1
        self.dlg.update()

    def draw(self):
        pyxel.cls(ui.BLACK)
        if self.dlg.active:
            speaker, _ = self.dlg.current
            ui.window(40, 300, ui.W - 80, 100)
            for i, line in enumerate(ui.wrap(self.dlg.visible_text(), ui.W - 120)[:4]):
                ui.text(60, 320 + i * ui.LINE_H, line, ui.WHITE)
            if speaker:
                self.app.portraits.draw(speaker, 60, 150)
