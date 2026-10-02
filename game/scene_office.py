"""ADV パート: 会社(工場)画面。"""

import math

import pyxel

from . import audio, backgrounds, kickoff, rocket_art, script, state, story, ui
from .i18n import tr, trf
from .missions import MISSIONS
from .script import NAMES
from .vehicles import EAGLE9_S1R, EAGLE9_S2, HOPPER


class Layout:
    """画面サイズごとの配置(640x480 のときが元の数値)。"""

    def __init__(self):
        # 文字の入る枠は、詰めた配置(360x360)を K 倍して使う(720x720 は文字が 2 倍)
        small, tall, tiny, K = ui.COMPACT, ui.H > 480 and not ui.COMPACT, ui.TINY, ui.K
        self.status_h = (30 if small else 28) * K  # 小さい画面では2段
        self.cmd_h = (28 if tiny else 32 if small else 40 if tall else 36) * K
        self.cmd_y = ui.H - self.cmd_h - (4 if tiny else 6 if small else 16 if tall else 12) * K
        self.msg_lines = 3 if tiny else 4 if small else 6 if tall else 5
        self.msg_h = 26 * K + self.msg_lines * ui.LINE_H - (4 if small else 12 if tall else 14) * K
        self.msg_y = self.cmd_y - self.msg_h - (6 if tiny else 8 if small else 10) * K
        self.view_bottom = self.msg_y - (8 if tiny else 12) * K
        self.margin = (6 if small else 16) * K
        # 格納庫の絵の倍率(640x480 が 1)。縦が足りない画面では縦に合わせて縮め、横は中央に寄せる
        view_h = self.view_bottom - self.status_h - 1
        self.k = min(ui.W / 640, view_h / 289)
        self.ox = (ui.W - 640 * self.k) / 2


class Command:
    def __init__(self, key, label, ap):
        self.key = key
        self.label = label
        self.ap = ap


class OfficeScene:
    def __init__(self, app, lines=None, party=0):
        """party: 最初の何行のあいだ、背景を創業キックオフの場面にするか。"""
        self.app = app
        self.st = app.state
        self.dlg = ui.Dialogue()
        self.lay = Layout()
        self.party = party
        self.sel = 0
        self.frame = 0
        self.commands = [Command(*c) for c in story.COMMANDS]
        self.eagle9 = None  # 格納庫に立てる Eagle 9 の絵(必要になったら読み込む)
        state.save(self.st)  # 会社に戻るたびに自動でセーブする
        if lines:
            self.dlg.start(lines)

    def describe(self, cmd):
        """コマンドの説明文(製造と打上は、いまのステージに合わせて変わる)。"""
        return story.describe(self.st, cmd.key)

    def run_command(self, key):
        self.party = 0  # キックオフの場面は最初の会話だけ。コマンドの会話では出さない
        lines, then = story.command(self.st, key)
        if then == "launch":
            mdef = MISSIONS[self.st.stage]
            self.dlg.start(lines, lambda: self.app.start_mission(mdef))
        elif then == "game_over":
            self.dlg.start(lines, self.app.game_over)
        else:
            self.dlg.start(lines)

    # ---- 更新 ----
    def update(self):
        self.frame += 1
        audio.bgm("mariachi" if self.dlg.active and self.dlg.index < self.party else "adv")
        if self.dlg.active:
            self.dlg.update()
            return
        if ui.left_p():
            self.sel = (self.sel - 1) % len(self.commands)
        if ui.right_p():
            self.sel = (self.sel + 1) % len(self.commands)
        if ui.confirm():
            self.run_command(self.commands[self.sel].key)

    # ---- 描画 ----
    def draw(self):
        pyxel.cls(ui.BLACK)
        lay = self.lay
        backgrounds.draw("u1_panel", 0, lay.view_bottom)  # 会話の窓とコマンドの後ろ
        if self.draw_illustration():
            pass
        elif self.dlg.active and self.dlg.index < self.party:
            kickoff.draw(lay.status_h + 1, lay.view_bottom, lay.k, lay.ox, self.frame,
                         bg=backgrounds.image("b0_kickoff"), board=backgrounds.board("b0_kickoff"),
                         doodle=backgrounds.whiteboard("kickoff", self.st.month_index))
        else:
            self.draw_hangar()
        self.draw_status()
        speaker = self.dlg.current[0] if self.dlg.active else ""
        if speaker:
            ps = self.app.portraits.size()
            m = 8 * ui.K if ui.COMPACT else 24
            self.app.portraits.draw(speaker, m, self.lay.view_bottom - ps - m // 3)
        self.draw_message(speaker)
        self.draw_commands()

    def draw_status(self):
        st = self.st
        h = self.lay.status_h
        if not backgrounds.draw("u2_status", 0, 0):
            pyxel.rect(0, 0, ui.W, h, ui.NAVY)
            pyxel.line(0, h, ui.W, h, ui.DBLUE)
        col = ui.RED if st.funds < 10 else ui.YELLOW
        build = trf(" 製造中{n}", n=st.building_now()) if st.building_now() else ""
        funds = trf("資金 {funds:6.1f}M$", funds=st.funds)
        rep = trf("評判 {rep}", rep=st.reputation)
        rockets = trf("機体 {n}{build}", n=st.ready(), build=build)
        if ui.COMPACT:  # 2段に分ける
            c1, c2, K = ui.W // 3, ui.W * 2 // 3, ui.K
            ui.text(6 * K, 3 * K, st.date_str(), ui.WHITE, size=10)
            ui.text(c1, 3 * K, funds, col, size=10)
            ui.text(c2, 3 * K, f"AP {st.ap}/{st.ap_max}", ui.WHITE, size=10)
            ui.text(6 * K, 16 * K, rep, ui.LIME, size=10)
            ui.text(c1, 16 * K, f"TLM {st.tlm}", ui.CYAN, size=10)
            ui.text(c2, 16 * K, rockets, ui.WHITE, size=10)
            return
        k = ui.W / 640
        ui.text(12, 8, st.date_str(), ui.WHITE)
        ui.text(150 * k, 8, funds, col)
        ui.text(290 * k, 8, rep, ui.LIME)
        ui.text(370 * k, 8, f"TLM {st.tlm}", ui.CYAN)
        ui.text(450 * k, 8, f"AP {st.ap}/{st.ap_max}", ui.WHITE)
        ui.text(530 * k, 8, rockets, ui.WHITE, size=10)

    def illustration_state(self):
        """いまの会話の行で出す挿絵: (場面の絵の番号, 小窓の番号, 重ねる文字)。どれも、なければ None。"""
        scene = inset = overlay = None
        for num in self.dlg.image_marks:
            if num in script.IMAGE_SKIP:
                scene = inset = overlay = None
            elif num in script.IMAGE_OVERLAYS:
                overlay = script.IMAGE_OVERLAYS[num]
            elif num in script.IMAGE_INSETS:
                inset = num
            else:  # 新しい場面の絵になったら、小窓と文字は消す
                scene, inset, overlay = num, None, None
        return scene, inset, overlay

    def draw_illustration(self):
        """会話の挿絵を、場面の位置に描く。描いたら True(格納庫などは描かない)。"""
        if not self.dlg.active:
            return False
        scene, inset, overlay = self.illustration_state()
        img, _ = backgrounds.illustration(scene) if scene else (None, None)
        if img is None:
            return False
        lay = self.lay
        top = lay.status_h + 1
        pyxel.blt(0, top, img, 0, 0, img.width, img.height)
        view_h = lay.view_bottom - top
        if inset:
            win, _ = backgrounds.illustration(inset)
            if win is not None:
                # 右寄りに小窓。縁取りと影をつける
                m = 8 * ui.K if not ui.TINY else 3
                x, y = ui.W - win.width - m * 2, top + (view_h - win.height) // 2
                pyxel.rect(x + 3, y + 3, win.width, win.height, ui.BLACK)
                pyxel.blt(x, y, win, 0, 0, win.width, win.height)
                pyxel.rectb(x - 1, y - 1, win.width + 2, win.height + 2, ui.WHITE)
                lines = script.IMAGE_TEXT.get(inset)
                if lines and ui.TINY:  # 320x240 は小窓が小さいので、1 行目(機体名)だけ
                    lines = lines[:1]
                if lines:  # スペックなどの文字を、小窓の右側に重ねる
                    size = 10
                    ty = y + 6 * ui.K
                    for i, t in enumerate(lines):
                        t = tr(t)
                        tx = x + win.width - ui.text_width(t, size) - 6 * ui.K
                        ui.text(tx, ty, t, ui.YELLOW if i == 0 else ui.WHITE, size=size, border=ui.BLACK)
                        ty += ui.LINE_H - 2 * ui.K if not ui.TINY else 11
        if overlay and self.frame % 120 < 24:  # モニターの隅に、ときどき一瞬だけ映る文字
            size = 10
            tx = ui.W - ui.text_width(overlay, size) - 12 * ui.K
            ty = lay.view_bottom - 18 * ui.K
            ui.text(tx, ty, overlay, ui.LIME, size=size, border=ui.BLACK)
        return True

    def draw_hangar(self):
        """格納庫。背景画があればそれを使い、なければ 640x480 のときの絵を倍率 k で描く。床を基準に機体を立てる。"""
        k, ox = self.lay.k, self.lay.ox
        top, bottom = self.lay.status_h + 1, self.lay.view_bottom
        floor = bottom - 70 * k
        scene = "b1_hangar_omega" if self.st.craft == "eagle1" else "b2_factory"  # Chapter 1 は島の格納庫
        if backgrounds.draw(scene, 0, top):
            board = backgrounds.board(scene) or (ox + 160 * k, floor - 189 * k - top, ox + 310 * k, floor - 99 * k - top)
            doodle = backgrounds.whiteboard(self.st.stage, self.st.month_index)
            if doodle:  # ステージごとの落書き(月ごとに入れ替わる)
                backgrounds.draw_doodle(doodle, board, top)
            else:
                x0, y0, x1, y1 = board
                self.draw_board(x0, top + y0, x1, top + y1)
        else:
            self.draw_hangar_room(top, bottom, floor)
        # 機体(あれば格納庫に立っている)
        if self.st.ready() > 0 or self.st.building_now():
            built = self.st.ready() > 0
            cx = ox + 470 * k
            if self.st.craft == "eagle1":
                self.draw_rocket_in_hangar(cx, floor, k, built=built)
            else:
                self.draw_craft_in_hangar(cx, floor, k, built)

    def draw_board(self, x0, y0, x1, y1):
        """ホワイトボードの字と落書き。(x0, y0)〜(x1, y1) はボードの白い面。元の絵(150 x 90)の位置を、面の大きさに合わせて置く。"""
        sx, sy = (x1 - x0) / 150, (y1 - y0) / 90
        size = 10 if ui.COMPACT else 12
        ui.text(x0 + 10 * sx, y0 + 6 * sy, self.st.craft_name.upper(), ui.DBLUE, size=size)
        line_y = max(y0 + 28 * sy, y0 + 6 * sy + size * ui.K + 1)  # 字の大きさに対してボードが小さいときは、字の下へずらす
        pyxel.line(x0 + 10 * sx, line_y, x0 + 90 * sx, line_y, ui.BLACK)
        right = x1 - 6 * sx  # 落書きの丸を置ける右の端(目標の字があれば、その左まで)
        if not ui.TINY:  # 320x240 ではボードが小さくて入らない
            goal = script.BOARD.get(self.st.stage, "")
            right = x0 + 144 * sx - ui.text_width(goal, 10)
            ui.text(right, line_y + 6 * sy, goal, ui.RED, size=10)
        cx = (x0 + 10 * sx + right) / 2  # 丸は、左の端と目標の字のあいだの真ん中
        cy = (line_y + y1) / 2
        r = min(22 * min(sx, sy), (right - x0 - 10 * sx) / 2 - 2, (y1 - line_y) / 2 - 2)
        if r >= 3:
            pyxel.circb(cx, cy, r, ui.RED)
            pyxel.circ(cx, cy, max(1, r * 0.27), ui.DBLUE)

    def draw_hangar_room(self, top, bottom, floor):
        """背景画がないときの格納庫(プログラムで描く)。"""
        k, ox = self.lay.k, self.lay.ox
        # 壁
        pyxel.rect(0, top, ui.W, bottom - top, ui.NAVY)
        for x in range(0, ui.W, round(40 * k)):
            pyxel.line(x, top, x, floor, ui.BLACK)
        # 開いた格納庫の扉と空(縦に余裕がある画面では扉を高くする)
        dx, dw = ox + 360 * k, 250 * k
        dtop = max(top + 16 * k, floor - 203 * k - (floor - top) * 0.25)
        dh = floor - 3 - dtop
        pyxel.rect(dx, dtop, dw, dh, ui.CYAN)
        pyxel.rect(dx, floor - 69 * k, dw, 66 * k, ui.DBLUE)
        pyxel.circ(ox + 560 * k, dtop + 44 * k, 16 * k, ui.YELLOW)
        for i, (cx, cy) in enumerate(((400, 34), (470, 64))):
            pyxel.elli(ox + (cx + int(math.sin((self.frame + i * 90) / 120) * 6)) * k, dtop + cy * k, 50 * k, 14 * k, ui.WHITE)
        pyxel.rectb(dx - 2, dtop - 2, dw + 4, dh + 4, ui.GRAY)
        for y in range(int(dtop), int(dtop + dh), round(20 * k)):
            pyxel.line(dx, y, dx + 4 * k, y, ui.GRAY)
        # 床
        pyxel.rect(0, floor, ui.W, bottom - floor, ui.GRAY)
        pyxel.line(0, floor, ui.W, floor, ui.WHITE)
        for x in range(round(-200 * k), ui.W, round(60 * k)):
            pyxel.line(x, bottom, x + 120 * k, floor, ui.DBLUE)
        # ホワイトボード
        by = floor - 189 * k
        pyxel.rect(ox + 160 * k, by, 150 * k, 90 * k, ui.WHITE)
        pyxel.rectb(ox + 160 * k, by, 150 * k, 90 * k, ui.GRAY)
        self.draw_board(ox + 160 * k, by, ox + 310 * k, by + 90 * k)
        # 机とノートPC
        pyxel.rect(ox + 40 * k, floor - 40 * k, 120 * k, 10 * k, ui.BROWN)
        pyxel.rect(ox + 48 * k, floor - 30 * k, 6 * k, 40 * k, ui.BROWN)
        pyxel.rect(ox + 146 * k, floor - 30 * k, 6 * k, 40 * k, ui.BROWN)
        pyxel.rect(ox + 80 * k, floor - 58 * k, 40 * k, 18 * k, ui.GRAY)
        pyxel.rect(ox + 82 * k, floor - 56 * k, 36 * k, 14 * k, ui.TEAL if self.frame // 30 % 2 else ui.LIME)

    def draw_craft_in_hangar(self, cx, base, k, built):
        """Eagle 9 / Hopper。Eagle 9 は用意した絵(assets/rockets)があればそれを使う。"""
        craft = self.st.craft
        top = base - 200 * k
        if craft == "eagle9":
            if self.eagle9 is None:
                path = ui.ASSETS / "rockets" / f"eagle9_{ui.SCREEN}.png"
                self.eagle9 = pyxel.Image.from_image(str(path)) if path.exists() else False
            img = self.eagle9
            if img:
                top = base - img.height
                pyxel.blt(cx - img.width // 2, top, img, 0, 0, img.width, img.height, ui.PURPLE)
            else:
                rocket_art.vehicle(rocket_art.upright(cx, base, 200 * k / 54), [EAGLE9_S1R, EAGLE9_S2], "fairing")
        else:
            top = base - 120 * k
            rocket_art.vehicle(rocket_art.upright(cx, base, 120 * k / 18), [HOPPER])
        if not built:
            pyxel.dither(0.5)
            pyxel.rect(cx - 30 * k, top, 60 * k, base - top, ui.NAVY)
            pyxel.dither(1.0)
        # 足場
        for x in (cx - 30 * k, cx + 30 * k):
            pyxel.line(x, top + 30 * k, x, base, ui.YELLOW)
        y = top + 40 * k
        while y < base:
            pyxel.line(cx - 30 * k, y, cx - 22 * k, y, ui.YELLOW)
            pyxel.line(cx + 22 * k, y, cx + 30 * k, y, ui.YELLOW)
            y += 30 * k
        if not built:
            # 機体の上に出す。上のステータス欄に隠れるなら、欄のすぐ下へ
            ui.text_center(cx, max(top - 16, self.lay.status_h + 6), "製造中", ui.YELLOW, border=ui.BLACK)

    def draw_rocket_in_hangar(self, cx, base, k, built=True):
        h = 190 * k
        top = base - h
        hw = 9 * k
        body = ui.WHITE if built else ui.GRAY
        pyxel.rect(cx - hw, top + 22 * k, hw * 2, h - 22 * k, body)
        pyxel.tri(cx - hw, top + 22 * k, cx + hw - 1, top + 22 * k, cx, top, body)
        pyxel.rect(cx - hw, top + 70 * k, hw * 2, 6 * k, ui.BLACK)
        pyxel.rect(cx + 4 * k, top + 22 * k, 5 * k, h - 22 * k, ui.GRAY if built else ui.DBLUE)
        if not ui.COMPACT:  # 360x360 では機体が細くて文字が入らない(720x720 は文字が大きくて入らない)
            for i, ch in enumerate("STARX"):
                ui.text(cx - 3, top + (90 + i * 12) * k, ch, ui.DBLUE, size=10)
        pyxel.tri(cx - 7 * k, base, cx + 6 * k, base, cx, base - 12 * k, ui.BLACK)
        # 足場
        for x in (cx - 30 * k, cx + 30 * k):
            pyxel.line(x, top + 30 * k, x, base, ui.YELLOW)
        y = top + 40 * k
        while y < base:
            pyxel.line(cx - 30 * k, y, cx + 30 * k, y, ui.YELLOW)
            y += 30 * k
        if not built:
            # 機体の上に出す。上のステータス欄に隠れるなら、欄のすぐ下へ
            ui.text_center(cx, max(top - 16, self.lay.status_h + 6), "製造中", ui.YELLOW, border=ui.BLACK)

    def draw_message(self, speaker):
        lay = self.lay
        m, y0, h = lay.margin, lay.msg_y, lay.msg_h
        K = ui.K
        pad = 10 * K if ui.COMPACT else 16
        tw = ui.W - (m + pad) * 2
        ui.window(m, y0, ui.W - m * 2, h)
        if self.dlg.active:
            if speaker:
                name = NAMES.get(speaker, speaker)
                nx = m + self.app.portraits.size() + (16 * K if ui.COMPACT else 26)
                pyxel.rect(nx, y0 - 14 * K, ui.text_width(name) + 16 * K, 18 * K, ui.DBLUE)
                pyxel.rectb(nx, y0 - 14 * K, ui.text_width(name) + 16 * K, 18 * K, ui.WHITE)
                ui.text(nx + 8 * K, y0 - 11 * K, name, ui.YELLOW)
            lines = ui.wrap(self.dlg.visible_text(), tw)
            for i, line in enumerate(lines[:lay.msg_lines]):
                ui.text(m + pad, y0 + 12 * K + i * ui.LINE_H, line, ui.WHITE)
            if self.dlg.waiting() and self.frame // 15 % 2:
                ax, ay = ui.W - m - 24 * K, y0 + h - 16 * K
                pyxel.tri(ax, ay, ax + 10 * K, ay, ax + 5 * K, ay + 6 * K, ui.WHITE)
        else:
            cmd = self.commands[self.sel]
            ui.text(m + pad, y0 + 12 * K, trf("【{label}】", label=ui.tr(cmd.label)), ui.YELLOW)
            dy = 10 * K if ui.COMPACT else 16
            # 320x240 は操作説明を省いて、説明文に 2 行使う
            n = lay.msg_lines - (1 if ui.TINY else 2)
            for i, line in enumerate(ui.wrap(self.describe(cmd), tw)[:n]):
                ui.text(m + pad, y0 + dy + (i + 1) * ui.LINE_H, line, ui.WHITE)
            if not ui.TINY:
                ui.text(m + pad, y0 + h - (16 * K if ui.COMPACT else 20), "←→ 選択 / SPACE・Z 決定", ui.GRAY, size=10)

    def draw_commands(self):
        lay = self.lay
        n = len(self.commands)
        K = ui.K
        gap = 2 * K if ui.COMPACT else 4
        bw = int(min(64 * ui.W / 640, (ui.W - lay.margin * 2 - (n - 1) * gap) / n))
        if K > 1:
            bw = int(min(36 * K * 1.4, (ui.W - lay.margin * 2 - (n - 1) * gap) / n))
        x0 = (ui.W - (n * bw + (n - 1) * gap)) // 2
        y, bh = lay.cmd_y, lay.cmd_h
        for i, cmd in enumerate(self.commands):
            x = x0 + i * (bw + gap)
            selected = i == self.sel and not self.dlg.active
            usable = cmd.ap == 0 or self.st.ap >= cmd.ap
            fill = ui.DBLUE if selected else ui.NAVY
            pyxel.rect(x, y, bw, bh, fill)
            pyxel.rectb(x, y, bw, bh, ui.YELLOW if selected else ui.DBLUE)
            col = ui.WHITE if usable else ui.GRAY
            fs = 12 if ui.text_width(cmd.label) <= bw - 4 else 10  # 英語の長い名前は小さい字で
            ui.text_center(x + bw // 2, y + bh // 2 - (12 if fs == 12 else 11) * K, cmd.label, col, size=fs)
            ap = f"AP{cmd.ap}" if cmd.ap else "-"
            ui.text_center(x + bw // 2, y + bh // 2 + (2 if ui.TINY else 4) * K, ap, ui.GRAY, size=10)
