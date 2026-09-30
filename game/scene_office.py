"""ADV パート: 会社(工場)画面。"""

import math

import pyxel

from . import audio, kickoff, rocket_art, script, state, ui
from .i18n import trf
from .missions import MISSIONS
from .portraits import NAMES
from .vehicles import EAGLE9_S1R, EAGLE9_S2, HOPPER


class Layout:
    """画面サイズごとの配置(640x480 のときが元の数値)。"""

    def __init__(self):
        small, tall, tiny = ui.SMALL, ui.H > 480, ui.TINY
        self.status_h = 30 if small else 28  # 小さい画面では2段
        self.cmd_h = 28 if tiny else 32 if small else 40 if tall else 36
        self.cmd_y = ui.H - self.cmd_h - (4 if tiny else 6 if small else 16 if tall else 12)
        self.msg_lines = 3 if tiny else 4 if small else 6 if tall else 5
        self.msg_h = 26 + self.msg_lines * ui.LINE_H - (4 if small else 12 if tall else 14)
        self.msg_y = self.cmd_y - self.msg_h - (6 if tiny else 8 if small else 10)
        self.view_bottom = self.msg_y - (8 if tiny else 12)
        self.margin = 6 if small else 16
        # 格納庫の絵の倍率(640x480 が 1)。縦が足りない画面では縦に合わせて縮め、横は中央に寄せる
        view_h = self.view_bottom - self.status_h - 1
        self.k = min(ui.W / 640, view_h / 289)
        self.ox = (ui.W - 640 * self.k) / 2


class Command:
    def __init__(self, key, label, ap, desc, action):
        self.key = key
        self.label = label
        self.ap = ap
        self.desc = desc
        self.action = action


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
        self.commands = [
            Command("build", "製造", 1, "", self.cmd_build),
            Command("inspect", "点検", 1, trf("次の打ち上げの故障を起きにくくする({cost}M$)", cost=self.st.INSPECT_COST), self.cmd_inspect),
            Command("fund", "調達", 1, "資金を集める(3ヶ月に1回)", self.cmd_fund),
            Command("launch", "打上", 0, "", self.cmd_launch),
            Command("wait", "待機", 0, "次の月へ進む", self.cmd_wait),
        ]
        self.eagle9 = None  # 格納庫に立てる Eagle 9 の絵(必要になったら読み込む)
        state.save(self.st)  # 会社に戻るたびに自動でセーブする
        if lines:
            self.dlg.start(lines)

    def describe(self, cmd):
        """コマンドの説明文(製造と打上は、いまのステージに合わせて変わる)。"""
        st = self.st
        if cmd.key == "build":
            cost, months = st.build_cost()
            if st.craft == "eagle9" and st.recovered > 0:
                return trf("回収した1段目を整備して Eagle 9 にする({cost:.0f}M$・{months}ヶ月)", cost=cost, months=months)
            return trf("{name} を製造する({cost:.0f}M$・{months}ヶ月)", name=st.craft_name, cost=cost, months=months)
        if cmd.key == "launch":
            m = MISSIONS[st.stage]
            return trf("{title}: {goal}(その月の残り AP をすべて使う)", title=ui.tr(m.title), goal=ui.tr(m.goal))
        return cmd.desc

    # ---- コマンド ----
    def say(self, lines, on_done=None):
        self.dlg.start(lines, on_done)

    def use_ap(self, n):
        if self.st.ap < n:
            self.say([("sara", "今月はもう動けないわ。「待機」して。")])
            return False
        self.st.ap -= n
        return True

    def cmd_build(self):
        st = self.st
        if st.ready() + st.building_now() >= 2:
            self.say([("maya", "もう2機あるわ。置き場所がない。")])
            return
        cost, months = st.build_cost()
        if st.funds < cost:
            self.say([("sara", "製造するお金が足りないわ。")])
            return
        if not self.use_ap(1):
            return
        st.funds -= cost
        if st.craft == "eagle9" and st.recovered > 0:
            st.recovered -= 1
        st.building.append([st.craft, months])
        self.say([("maya", trf("{name} の製造を始めたわ。{months}ヶ月後に完成する。", name=st.craft_name, months=months))])

    def cmd_inspect(self):
        st = self.st
        if st.inspected:
            self.say([("maya", "点検はもう済んでる。次の打ち上げまで有効よ。")])
            return
        if not self.use_ap(1):
            return
        st.funds -= st.INSPECT_COST
        st.inspected = True
        self.say([("maya", "機体を隅々まで見直した。故障はだいぶ起きにくくなるはず。")])

    def cmd_fund(self):
        st = self.st
        if st.month_index - st.last_fundraise < 3:
            self.say([("sara", "調達は3ヶ月に1回までよ。")])
            return
        if not self.use_ap(1):
            return
        st.last_fundraise = st.month_index
        amount = st.fundraise_amount()
        st.funds += amount
        self.say([("sara", trf("{amount}M$ 集まったわ。", amount=amount))])

    def cmd_launch(self):
        st = self.st
        if st.ready() <= 0:
            self.say([("maya", "機体がないわ。「製造」して。")])
            return
        mdef = MISSIONS[st.stage]
        lines = list(script.BRIEFING[mdef.id])
        lines += script.BRIEFING_INSPECTED if st.inspected else script.BRIEFING_NOT_INSPECTED
        lines += script.BRIEFING_END
        self.say(lines, on_done=lambda: self.app.start_mission(mdef))

    def cmd_wait(self):
        lines = self.st.next_month()
        if self.st.funds < 0:
            self.say(lines, on_done=self.app.game_over)
        else:
            self.say(lines)

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
            self.commands[self.sel].action()

    # ---- 描画 ----
    def draw(self):
        pyxel.cls(ui.BLACK)
        if self.dlg.active and self.dlg.index < self.party:
            lay = self.lay
            kickoff.draw(lay.status_h + 1, lay.view_bottom, lay.k, lay.ox, self.frame)
        else:
            self.draw_hangar()
        self.draw_status()
        speaker = self.dlg.current[0] if self.dlg.active else ""
        if speaker:
            ps = self.app.portraits.size()
            m = 8 if ui.SMALL else 24
            self.app.portraits.draw(speaker, m, self.lay.view_bottom - ps - m // 3)
        self.draw_message(speaker)
        self.draw_commands()

    def draw_status(self):
        st = self.st
        h = self.lay.status_h
        pyxel.rect(0, 0, ui.W, h, ui.NAVY)
        pyxel.line(0, h, ui.W, h, ui.DBLUE)
        col = ui.RED if st.funds < 10 else ui.YELLOW
        build = trf(" 製造中{n}", n=st.building_now()) if st.building_now() else ""
        funds = trf("資金 {funds:6.1f}M$", funds=st.funds)
        rep = trf("評判 {rep}", rep=st.reputation)
        rockets = trf("機体 {n}{build}", n=st.ready(), build=build)
        if ui.SMALL:  # 2段に分ける
            c1, c2 = ui.W // 3, ui.W * 2 // 3
            ui.text(6, 3, st.date_str(), ui.WHITE, size=10)
            ui.text(c1, 3, funds, col, size=10)
            ui.text(c2, 3, f"AP {st.ap}/{st.ap_max}", ui.WHITE, size=10)
            ui.text(6, 16, rep, ui.LIME, size=10)
            ui.text(c1, 16, f"TLM {st.tlm}", ui.CYAN, size=10)
            ui.text(c2, 16, rockets, ui.WHITE, size=10)
            return
        k = ui.W / 640
        ui.text(12, 8, st.date_str(), ui.WHITE)
        ui.text(150 * k, 8, funds, col)
        ui.text(290 * k, 8, rep, ui.LIME)
        ui.text(370 * k, 8, f"TLM {st.tlm}", ui.CYAN)
        ui.text(450 * k, 8, f"AP {st.ap}/{st.ap_max}", ui.WHITE)
        ui.text(530 * k, 8, rockets, ui.WHITE, size=10)

    def draw_hangar(self):
        """格納庫。640x480 のときの絵を倍率 k で拡大・縮小し、床を基準に置く。"""
        k, ox = self.lay.k, self.lay.ox
        top, bottom = self.lay.status_h + 1, self.lay.view_bottom
        floor = bottom - 70 * k
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
        ui.text(ox + 170 * k, by + 6 * k, self.st.craft_name.upper(), ui.DBLUE, size=10 if ui.SMALL else 12)
        pyxel.circb(ox + 235 * k, by + 60 * k, 22 * k, ui.RED)
        pyxel.circ(ox + 235 * k, by + 60 * k, 6 * k, ui.DBLUE)
        pyxel.line(ox + 170 * k, by + 28 * k, ox + 250 * k, by + 28 * k, ui.BLACK)
        if not ui.TINY:  # 320x240 ではボードが小さくて入らない
            goal = script.BOARD.get(self.st.stage, "")
            ui.text(ox + 304 * k - ui.text_width(goal, 10), by + 34 * k, goal, ui.RED, size=10)
        # 机とノートPC
        pyxel.rect(ox + 40 * k, floor - 40 * k, 120 * k, 10 * k, ui.BROWN)
        pyxel.rect(ox + 48 * k, floor - 30 * k, 6 * k, 40 * k, ui.BROWN)
        pyxel.rect(ox + 146 * k, floor - 30 * k, 6 * k, 40 * k, ui.BROWN)
        pyxel.rect(ox + 80 * k, floor - 58 * k, 40 * k, 18 * k, ui.GRAY)
        pyxel.rect(ox + 82 * k, floor - 56 * k, 36 * k, 14 * k, ui.TEAL if self.frame // 30 % 2 else ui.LIME)
        # 機体(あれば格納庫に立っている)
        if self.st.ready() > 0 or self.st.building_now():
            built = self.st.ready() > 0
            cx = ox + 470 * k
            if self.st.craft == "eagle1":
                self.draw_rocket_in_hangar(cx, floor, k, built=built)
            else:
                self.draw_craft_in_hangar(cx, floor, k, built)

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
            ui.text_center(cx, top - 16, "製造中", ui.YELLOW, border=ui.BLACK)

    def draw_rocket_in_hangar(self, cx, base, k, built=True):
        h = 190 * k
        top = base - h
        hw = 9 * k
        body = ui.WHITE if built else ui.GRAY
        pyxel.rect(cx - hw, top + 22 * k, hw * 2, h - 22 * k, body)
        pyxel.tri(cx - hw, top + 22 * k, cx + hw - 1, top + 22 * k, cx, top, body)
        pyxel.rect(cx - hw, top + 70 * k, hw * 2, 6 * k, ui.BLACK)
        pyxel.rect(cx + 4 * k, top + 22 * k, 5 * k, h - 22 * k, ui.GRAY if built else ui.DBLUE)
        if not ui.SMALL:  # 360x360 では機体が細くて文字が入らない
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
            ui.text_center(cx, top - 16, "製造中", ui.YELLOW, border=ui.BLACK)

    def draw_message(self, speaker):
        lay = self.lay
        m, y0, h = lay.margin, lay.msg_y, lay.msg_h
        pad = 10 if ui.SMALL else 16
        tw = ui.W - (m + pad) * 2
        ui.window(m, y0, ui.W - m * 2, h)
        if self.dlg.active:
            if speaker:
                name = NAMES.get(speaker, speaker)
                nx = m + self.app.portraits.size() + (16 if ui.SMALL else 26)
                pyxel.rect(nx, y0 - 14, ui.text_width(name) + 16, 18, ui.DBLUE)
                pyxel.rectb(nx, y0 - 14, ui.text_width(name) + 16, 18, ui.WHITE)
                ui.text(nx + 8, y0 - 11, name, ui.YELLOW)
            lines = ui.wrap(self.dlg.visible_text(), tw)
            for i, line in enumerate(lines[:lay.msg_lines]):
                ui.text(m + pad, y0 + 12 + i * ui.LINE_H, line, ui.WHITE)
            if self.dlg.waiting() and self.frame // 15 % 2:
                ax, ay = ui.W - m - 24, y0 + h - 16
                pyxel.tri(ax, ay, ax + 10, ay, ax + 5, ay + 6, ui.WHITE)
        else:
            cmd = self.commands[self.sel]
            ui.text(m + pad, y0 + 12, trf("【{label}】", label=ui.tr(cmd.label)), ui.YELLOW)
            dy = 10 if ui.SMALL else 16
            # 320x240 は操作説明を省いて、説明文に 2 行使う
            n = lay.msg_lines - (1 if ui.TINY else 2)
            for i, line in enumerate(ui.wrap(self.describe(cmd), tw)[:n]):
                ui.text(m + pad, y0 + dy + (i + 1) * ui.LINE_H, line, ui.WHITE)
            if not ui.TINY:
                ui.text(m + pad, y0 + h - (16 if ui.SMALL else 20), "←→ 選択 / SPACE・Z 決定", ui.GRAY, size=10)

    def draw_commands(self):
        lay = self.lay
        n = len(self.commands)
        gap = 2 if ui.SMALL else 4
        bw = int(min(64 * ui.W / 640, (ui.W - lay.margin * 2 - (n - 1) * gap) / n))
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
            ui.text_center(x + bw // 2, y + bh // 2 - (12 if fs == 12 else 11), cmd.label, col, size=fs)
            ap = f"AP{cmd.ap}" if cmd.ap else "-"
            ui.text_center(x + bw // 2, y + bh // 2 + (2 if ui.TINY else 4), ap, ui.GRAY, size=10)
