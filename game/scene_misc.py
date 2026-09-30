"""タイトル・リザルト・ゲームオーバー画面。"""

import math
import random

import pyxel

from . import ui
from .i18n import trf
from .logo import load_logo
from .title_earth import EarthView


class TitleScene:
    """タイトル画面: 夜明けの地球とロゴ、メニュー。"""

    MENU = ["NEW GAME", "CONTINUE", "OPTIONS", "CREDITS"]

    # 画面サイズごとの配置。背景と地球は bg_w x bg_h で描いて bg_scale 倍で表示する
    LAYOUTS = {
        "640x480": dict(bg="title_bg.png", bg_w=320, bg_h=240, bg_scale=2, horizon=105,
                        logo_y=72, logo=1, menu_y=336, menu=3, menu_row=26, tag=2),
        "720x720": dict(bg="title_bg_sq.png", bg_w=360, bg_h=360, bg_scale=2, horizon=150,
                        logo_y=124, logo=1, menu_y=440, menu=3, menu_row=30, tag=2),
        "360x360": dict(bg="title_bg_sq.png", bg_w=360, bg_h=360, bg_scale=1, horizon=150,
                        logo_y=44, logo=1, menu_y=218, menu=2, menu_row=18, tag=1),
        "320x240": dict(bg="title_bg.png", bg_w=320, bg_h=240, bg_scale=1, horizon=105,
                        logo_y=32, logo=1, menu_y=162, menu=2, menu_row=16, tag=1),
    }

    def __init__(self, app):
        self.app = app
        self.frame = 0
        self.sel = 0
        self.popup = None
        L = self.lay = self.LAYOUTS[ui.SCREEN]
        self.bg = pyxel.Image(L["bg_w"], L["bg_h"])
        self.bg.load(0, 0, str(ui.ASSETS / L["bg"]))
        self.earth = EarthView(L["bg_w"], L["bg_h"], L["bg_scale"], L["horizon"])
        self.logo = load_logo()
        self.horizon = L["horizon"] * L["bg_scale"]  # 画面中央での地平線の高さ
        self.ky = self.horizon / 210  # 縦の倍率(640x480 が 1)
        rng = random.Random(5)
        self.twinkles = [(rng.uniform(20, ui.W - 20), rng.uniform(10, self.horizon - 20), rng.random())
                         for _ in range(9)]

    # ---- 更新 ----
    def update(self):
        self.frame += 1
        self.earth.update()
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
        L = self.lay
        w, h, sc = L["bg_w"], L["bg_h"], L["bg_scale"]
        pyxel.blt(w * (sc - 1) / 2, h * (sc - 1) / 2, self.bg, 0, 0, w, h, None, 0, sc)
        self.draw_twinkles()
        self.earth.draw()
        self.draw_trajectory()
        self.draw_station()
        self.draw_logo()
        self.draw_menu()
        self.draw_tagline()
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

        kx, ky = ui.W / 640, self.ky

        def pos(u):
            x = (70 + 560 * u) * kx
            y = self.horizon + (40 - 210 * math.sin(u * math.pi / 2) ** 0.7) * ky
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
        kx = ui.W / 640
        x = 560 * kx - (self.frame * 0.05) % (ui.W + 60)
        y = self.horizon + 52 * self.ky + math.sin(self.frame / 90) * 2
        if x < -40:
            return
        if ui.SMALL:  # 半分の大きさ
            pyxel.rect(x - 7, y, 14, 1, ui.GRAY)
            for dx in (-7, -4, 4, 7):
                pyxel.rect(x + dx - 1, y - 4, 2, 9, ui.DBLUE)
            pyxel.rect(x - 1, y - 1, 3, 3, ui.WHITE)
            return
        pyxel.rect(x - 14, y - 1, 28, 2, ui.GRAY)
        for dx in (-13, -8, 8, 13):
            pyxel.rect(x + dx - 2, y - 9, 4, 18, ui.DBLUE)
            pyxel.rectb(x + dx - 2, y - 9, 4, 18, ui.GRAY)
        pyxel.rect(x - 3, y - 3, 6, 6, ui.WHITE)
        pyxel.pset(x + 2, y - 2, ui.RED)

    def draw_tagline(self):
        ts = self.lay["tag"]
        lines = ["TO THE MOON,", "TO MARS,", "AND BEYOND."]
        m = 12 if ui.SMALL else 28
        x = ui.W - ui.big_text_width(lines[0], ts) - m
        y = ui.H - 12 - 7 * ts - 8 * ts * (len(lines) - 1)
        for i, line in enumerate(lines):
            ui.big_text(x, y + i * 8 * ts, line, ts, ui.WHITE, shadow=ui.BLACK)

    # ---- ロゴ ----
    def draw_logo(self):
        """ロゴ(画面ごとの幅で作ってある assets/logo_<画面サイズ>.png)を表示し、その下に副題を出す。"""
        k = self.lay["logo"]
        w, h = self.logo.width, self.logo.height
        x = (ui.W - w * k) // 2
        y = self.lay["logo_y"]
        # blt の拡大は転送先の中心が基準なので、左上が (x, y) になるようにずらす
        pyxel.blt(x + w * (k - 1) / 2, y + h * (k - 1) / 2, self.logo, 0, 0, w, h, ui.BLACK, 0, k)
        sub = "FLY IT YOURSELF"
        ss = 1 if ui.SMALL else 2
        sw = ui.big_text_width(sub, ss, spacing=4)
        ui.big_text((ui.W - sw) // 2, y + h * k + (4 if ui.SMALL else 8), sub, ss, ui.WHITE, shadow=ui.BLACK, spacing=4)

    # ---- メニュー ----
    def draw_menu(self):
        ms, row = self.lay["menu"], self.lay["menu_row"]
        k = ms / 3  # 640x480 のときが 1
        x, y0 = ui.W // 2 - round(58 * k), self.lay["menu_y"]
        pyxel.dither(0.6)
        pyxel.rect(x - 44 * k, y0 - 16 * k, 230 * k, row * len(self.MENU) + 22 * k, ui.BLACK)
        pyxel.dither(1.0)
        for i, item in enumerate(self.MENU):
            y = y0 + i * row
            disabled = item in ("CONTINUE", "OPTIONS")
            col = ui.WHITE if i == self.sel else (ui.GRAY if disabled else ui.LBLUE)
            ui.big_text(x, y, item, ms, col, shadow=ui.BLACK if i == self.sel else None)
            if i == self.sel and self.frame // 20 % 3:
                pyxel.tri(x - 26 * k, y, x - 26 * k, y + 20 * k, x - 12 * k, y + 10 * k, ui.WHITE)

    def draw_popup(self):
        lines = self.popup
        small = ui.SMALL
        fs, lh = (10, 14) if small else (12, 18)
        mx = 10 if small else 120 * ui.W // 640
        h = 30 + len(lines) * lh
        y = (ui.H - h) // 2
        ui.window(mx, y, ui.W - mx * 2, h)
        for i, line in enumerate(lines):
            ui.text(mx + (10 if small else 20), y + 16 + i * lh, line, ui.WHITE, size=fs)


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
        if ui.TINY:
            # 320x240: 行間をさらに詰める
            ox, oy, fs, lh = 0, 0, 10, 12
            win = (4, 4, ui.W - 8, ui.H - 8)
            ys = dict(title=10, status=26, reason=40, wp=56, rows=70, gap=4, sec=16, sec_row=13, prompt=ui.H - 22)
            cols = dict(head=12, label=18, win=70, val=214, mark=262, alt=120)
        elif ui.SMALL:
            # 360x360: 10px の文字で詰めて並べる
            ox, oy, fs, lh = 0, 0, 10, 14
            win = (6, 6, ui.W - 12, ui.H - 12)
            ys = dict(title=14, status=32, reason=48, wp=70, rows=86, gap=6, sec=20, sec_row=16, prompt=ui.H - 26)
            cols = dict(head=14, label=22, win=78, val=250, mark=300, alt=140)
        else:
            # 640x480 の配置。大きい画面では中央に置く
            ox, oy, fs, lh = (ui.W - 640) // 2, (ui.H - 480) // 2, 12, 18
            win = (60, 40, 520, 400)
            ys = dict(title=60, status=86, reason=106, wp=136, rows=158, gap=10, sec=30, sec_row=22, prompt=416)
            cols = dict(head=100, label=120, win=230, val=430, mark=500, alt=260)
        cx = ui.W // 2
        run = self.run
        ok = run.result == "success"
        wx, wy, ww, wh = win
        ui.window(ox + wx, oy + wy, ww, wh, fill=ui.BLACK, border=ui.LIME if ok else ui.RED)
        ui.text_center(cx, oy + ys["title"], "飛行結果", ui.WHITE)
        ui.text_center(cx, oy + ys["status"], "ミッション成功" if ok else "ミッション失敗", ui.LIME if ok else ui.RED)
        if not ok:
            ui.text_center(cx, oy + ys["reason"], run.fail_reason, ui.WHITE, size=fs)
        y = oy + ys["wp"]
        wp = run.m.waypoint
        ui.text(ox + cols["head"], y, trf("{name}(高度 {alt:.0f} km 通過時)", name=wp.name, alt=wp.altitude / 1000),
                ui.YELLOW, size=fs)
        y = oy + ys["rows"]
        for key, w in wp.windows.items():
            ui.text(ox + cols["label"], y, w.label, ui.GRAY, size=fs)
            ui.text(ox + cols["win"], y, trf("窓 {lo:+.0f} ~ {hi:+.0f} {unit}", lo=w.lo, hi=w.hi, unit=w.unit),
                    ui.WHITE, size=fs)
            if run.wp_values:
                val = run.wp_values[key]
                good = w.ok(val)
                ui.text(ox + cols["val"], y, f"{val:+.1f}", ui.LIME if good else ui.RED, size=fs)
                ui.text(ox + cols["mark"], y, "○" if good else "×", ui.LIME if good else ui.RED, size=fs)
            else:
                ui.text(ox + cols["val"], y, "---", ui.GRAY, size=fs)
            y += lh
        y += ys["gap"]
        ui.text(ox + cols["head"], y, trf("ランク {rank}", rank=run.rank()), ui.YELLOW, size=fs)
        ui.text(ox + cols["alt"], y, trf("最高高度 {alt:.2f} km", alt=run.max_alt / 1000), ui.WHITE, size=fs)
        y += ys["sec"]
        s = self.s
        ui.text(ox + cols["head"], y, "会社への影響", ui.YELLOW, size=fs)
        y += ys["sec_row"]
        ui.text(ox + cols["label"], y, trf("テレメトリ +{tlm}", tlm=s["tlm"]), ui.CYAN, size=fs)
        y += lh
        rep = s["rep"]
        ui.text(ox + cols["label"], y, trf("評判 {rep:+d}", rep=rep), ui.LIME if rep >= 0 else ui.RED, size=fs)
        y += lh
        ui.text(ox + cols["label"], y, "機体 -1(Eagle 1 は使い捨て)", ui.WHITE, size=fs)
        if self.frame // 20 % 2:
            ui.text_center(cx, oy + ys["prompt"], "SPACE で工場へ戻る", ui.WHITE)


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
            m = 8 if ui.SMALL else 40
            pad = 10 if ui.SMALL else 20
            h = 88 if ui.SMALL else 100
            y = ui.H - (100 if ui.SMALL else 180)
            ui.window(m, y, ui.W - m * 2, h)
            for i, line in enumerate(ui.wrap(self.dlg.visible_text(), ui.W - (m + pad) * 2)[:4]):
                ui.text(m + pad, y + pad + i * ui.LINE_H, line, ui.WHITE)
            if speaker:
                ps = self.app.portraits.size()
                self.app.portraits.draw(speaker, m + pad, y - ps - (14 if ui.SMALL else 22))
