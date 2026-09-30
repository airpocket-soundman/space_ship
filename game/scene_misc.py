"""タイトル・リザルト・ゲームオーバー画面。"""

import math
import random

import pyxel

from . import ui


class TitleScene:
    """タイトル画面: 夜明けの地球とロゴ、メニュー。"""

    MENU = ["NEW GAME", "CONTINUE", "OPTIONS", "CREDITS"]
    LOGO_Y = 100
    GLARE = (320, 212)  # 地球の縁で朝日が昇る位置

    def __init__(self, app):
        self.app = app
        self.frame = 0
        self.sel = 0
        self.popup = None
        self.bg = pyxel.Image(320, 240)
        self.bg.load(0, 0, str(ui.ASSETS / "title_bg.png"))
        rng = random.Random(5)
        self.twinkles = [(rng.uniform(20, 620), rng.uniform(10, 190), rng.random()) for _ in range(9)]

    # ---- 更新 ----
    def update(self):
        self.frame += 1
        if self.popup:
            if ui.confirm() or ui.cancel():
                self.popup = None
            return
        if ui.up_p():
            self.sel = (self.sel - 1) % len(self.MENU)
        if ui.down_p():
            self.sel = (self.sel + 1) % len(self.MENU)
        if ui.confirm():
            item = self.MENU[self.sel]
            if item == "NEW GAME":
                self.app.new_game()
            elif item == "CONTINUE":
                self.popup = ["セーブ機能は準備中です。"]
            elif item == "OPTIONS":
                self.popup = ["オプションは準備中です。"]
            else:
                self.popup = [
                    "STAR X  ─  ロケット経営 × 操縦ゲーム",
                    "",
                    "企画・原案      airpocket-soundman",
                    "プログラム      Claude",
                    "エンジン        Pyxel",
                    "フォント        umplus(M+ / 東雲)",
                    "",
                    "実在の宇宙企業へのオマージュ(パロディ)作品です。",
                ]

    # ---- 描画 ----
    def draw(self):
        pyxel.cls(ui.BLACK)
        pyxel.blt(160, 120, self.bg, 0, 0, 320, 240, None, 0, 2)
        self.draw_twinkles()
        self.draw_trajectory()
        self.draw_station()
        self.draw_glare()
        self.draw_logo()
        self.draw_menu()
        ui.big_text(470, 422, "TO THE MOON,", 2, ui.WHITE)
        ui.big_text(470, 438, "TO MARS,", 2, ui.WHITE)
        ui.big_text(470, 454, "AND BEYOND.", 2, ui.WHITE)
        if self.popup:
            self.draw_popup()

    def draw_twinkles(self):
        for x, y, ph in self.twinkles:
            s = math.sin(self.frame / 20 + ph * 30)
            if s > 0.2:
                n = 2 if s > 0.8 else 1
                pyxel.line(x - n * 2, y, x + n * 2, y, ui.WHITE)
                pyxel.line(x, y - n * 2, x, y + n * 2, ui.WHITE)
                pyxel.pset(x, y, ui.LBLUE)

    def draw_trajectory(self):
        """地平線から右上へ昇っていく打ち上げ軌道とロケット。"""
        period = 600
        t = (self.frame % period) / period

        def pos(u):
            x = 70 + 560 * u
            y = 250 - 210 * math.sin(u * math.pi / 2) ** 0.7
            return x, y

        end = min(1.0, t * 1.4)
        steps = int(end * 120)
        prev = pos(0)
        for i in range(1, steps + 1):
            p = pos(i / 120)
            fade = i / 120
            pyxel.dither(0.25 + 0.75 * fade)
            pyxel.line(prev[0], prev[1], p[0], p[1], ui.GRAY if fade < 0.7 else ui.WHITE)
            prev = p
        pyxel.dither(1.0)
        if end < 1.0:
            x, y = pos(end)
            pyxel.circ(x, y, 2, ui.WHITE)
            pyxel.pset(x - 3, y + 1, ui.ORANGE)
        elif t < 0.95:
            x, y = pos(1.0)
            pyxel.line(x - 4, y, x + 4, y, ui.WHITE)
            pyxel.line(x, y - 4, x, y + 4, ui.WHITE)

    def draw_station(self):
        x = 560 - (self.frame * 0.05) % 700
        y = 262 + math.sin(self.frame / 90) * 2
        if x < -40:
            return
        pyxel.rect(x - 14, y - 1, 28, 2, ui.GRAY)
        for dx in (-13, -8, 8, 13):
            pyxel.rect(x + dx - 2, y - 9, 4, 18, ui.DBLUE)
            pyxel.rectb(x + dx - 2, y - 9, 4, 18, ui.GRAY)
        pyxel.rect(x - 3, y - 3, 6, 6, ui.WHITE)
        pyxel.pset(x + 2, y - 2, ui.RED)

    def draw_glare(self):
        gx, gy = self.GLARE
        pulse = 0.5 + 0.5 * math.sin(self.frame / 30)
        # 地平線に沿って広がる光
        for rx, ry, col, a in ((150, 22, ui.CYAN, 0.3), (100, 14, ui.LBLUE, 0.45), (55, 8, ui.WHITE, 0.7)):
            pyxel.dither(a)
            pyxel.elli(gx - rx, gy - ry, rx * 2, ry * 2, col)
        pyxel.dither(1.0)
        pyxel.rect(gx - 200, gy - 1, 400, 2, ui.LBLUE)
        pyxel.rect(gx - 120, gy - 1, 240, 2, ui.WHITE)
        # 光芒
        r = 26 + 8 * pulse
        for ang in range(0, 360, 45):
            a = math.radians(ang + self.frame * 0.2)
            length = r * (1.6 if ang % 90 == 0 else 0.9)
            pyxel.line(gx, gy, gx + math.cos(a) * length, gy + math.sin(a) * length * 0.8, ui.LBLUE)
        pyxel.line(gx - r * 2.2, gy, gx + r * 2.2, gy, ui.WHITE)
        pyxel.line(gx, gy - r * 1.4, gx, gy + r * 0.8, ui.WHITE)
        pyxel.circ(gx, gy, 7 + pulse * 2, ui.YELLOW)
        pyxel.circ(gx, gy, 4 + pulse, ui.WHITE)

    # ---- ロゴ ----
    def draw_logo(self):
        h, w, t, gap = 48, 70, 11, 14
        word = ["S", "T", "A", "R", " ", "X"]
        total = sum(30 if ch == " " else w for ch in word) + gap * (len(word) - 1)
        x = (ui.W - total) // 2
        y = self.LOGO_Y
        for ch in word:
            if ch == " ":
                x += 30 + gap
                continue
            self.draw_letter(ch, x + 3, y + 3, w, h, t, ui.NAVY)
            self.draw_letter(ch, x, y, w, h, t, ui.WHITE)
            x += w + gap
        sub = "FLY IT YOURSELF"
        sw = ui.big_text_width(sub, 2, spacing=4)
        ui.big_text((ui.W - sw) // 2, y + h + 22, sub, 2, ui.WHITE, spacing=4)

    @staticmethod
    def quad(p0, p1, p2, p3, col):
        pyxel.tri(*p0, *p1, *p2, col)
        pyxel.tri(*p0, *p2, *p3, col)

    def draw_letter(self, ch, x, y, w, h, t, col):
        mid = y + (h - t) // 2
        if ch == "S":
            pyxel.rect(x, y, w, t, col)
            pyxel.rect(x, y, t, (h + t) // 2, col)
            pyxel.rect(x, mid, w, t, col)
            pyxel.rect(x + w - t, mid, t, h - (mid - y), col)
            pyxel.rect(x, y + h - t, w, t, col)
        elif ch == "T":
            pyxel.rect(x, y, w, t, col)
            pyxel.rect(x + (w - t) // 2, y, t, h, col)
        elif ch == "A":
            s = t * 1.25
            ax = x + w / 2
            self.quad((ax - s / 2, y), (ax + s / 2, y), (x + s, y + h), (x, y + h), col)
            self.quad((ax - s / 2, y), (ax + s / 2, y), (x + w, y + h), (x + w - s, y + h), col)
        elif ch == "R":
            bw = w - 6
            pyxel.rect(x, y, t, h, col)
            pyxel.rect(x, y, bw, t, col)
            pyxel.rect(x + bw - t, y, t, (h + t) // 2, col)
            pyxel.rect(x, mid, bw, t, col)
            s = t * 1.3
            self.quad((x + w * 0.42, mid), (x + w * 0.42 + s, mid), (x + w, y + h), (x + w - s, y + h), col)
        elif ch == "X":
            s = t * 1.35
            self.quad((x, y), (x + s, y), (x + w, y + h), (x + w - s, y + h), col)
            self.quad((x + w - s, y), (x + w, y), (x + s, y + h), (x, y + h), col)

    # ---- メニュー ----
    def draw_menu(self):
        x, y0 = 262, 336
        pyxel.dither(0.6)
        pyxel.rect(x - 44, y0 - 16, 230, 26 * len(self.MENU) + 22, ui.BLACK)
        pyxel.dither(1.0)
        for i, item in enumerate(self.MENU):
            y = y0 + i * 26
            disabled = item in ("CONTINUE", "OPTIONS")
            col = ui.WHITE if i == self.sel else (ui.GRAY if disabled else ui.LBLUE)
            ui.big_text(x, y, item, 3, col, shadow=ui.BLACK if i == self.sel else None)
            if i == self.sel and self.frame // 20 % 3:
                pyxel.tri(x - 26, y, x - 26, y + 20, x - 12, y + 10, ui.WHITE)

    def draw_popup(self):
        lines = self.popup
        h = 30 + len(lines) * 18
        y = (ui.H - h) // 2
        ui.window(120, y, ui.W - 240, h)
        for i, line in enumerate(lines):
            ui.text(140, y + 16 + i * 18, line, ui.WHITE)


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
