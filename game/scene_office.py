"""ADV パート: 会社(工場)画面。"""

import math

import pyxel

from . import kickoff, script, ui
from .i18n import trf
from .missions import MISSIONS
from .portraits import NAMES



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
            Command("dev", "開発", 1, "研究で機体を扱いやすくする(準備中)", self.cmd_dev),
            Command("build", "製造", 1, trf("Eagle 1 を製造する({cost:.0f}M$・{months}ヶ月)", cost=self.st.ROCKET_COST, months=self.st.ROCKET_MONTHS), self.cmd_build),
            Command("inspect", "点検", 1, trf("次の打ち上げの故障を起きにくくする({cost}M$)", cost=self.st.INSPECT_COST), self.cmd_inspect),
            Command("pr", "宣伝", 1, "ケンに配信を頼んで評判を上げる。CEO の SNS は当たり外れあり", self.cmd_pr),
            Command("sales", "営業", 1, "顧客を探す", self.cmd_sales),
            Command("fund", "調達", 1, "投資家にピッチして資金を集める(3ヶ月に1回)", self.cmd_fund),
            Command("hire", "採用", 1, "エンジニアを採用。AP +1、固定費 +0.5M$", self.cmd_hire),
            Command("launch", "打上", 0, "ミッションを選んで打ち上げる(その月の残り AP をすべて使う)", self.cmd_launch),
            Command("wait", "待機", 0, "次の月へ進む", self.cmd_wait),
        ]
        if lines:
            self.dlg.start(lines)

    # ---- コマンド ----
    def say(self, lines, on_done=None):
        self.dlg.start(lines, on_done)

    def use_ap(self, n):
        if self.st.ap < n:
            self.say([("sara", "今月はもう動けないわ。「待機」で次の月へ進めて。")])
            return False
        self.st.ap -= n
        return True

    def cmd_dev(self):
        self.say([("maya", "研究メニューはまだ準備中よ。次のアップデートを待ってて。")])

    def cmd_build(self):
        st = self.st
        if st.rockets + len(st.building) >= 2:
            self.say([("maya", "もう手元と製造中を合わせて2機ある。これ以上は置き場所がないわ。")])
            return
        if st.funds < st.ROCKET_COST:
            self.say([("sara", "製造するお金が足りないわ。")])
            return
        if not self.use_ap(1):
            return
        st.funds -= st.ROCKET_COST
        st.building.append(st.ROCKET_MONTHS)
        self.say([("maya", trf("Eagle 1 の製造を始めたわ。{months}ヶ月後に完成する。", months=st.ROCKET_MONTHS))])

    def cmd_inspect(self):
        st = self.st
        if st.inspected:
            self.say([("maya", "点検はもう済んでる。次の打ち上げまで有効よ。")])
            return
        if not self.use_ap(1):
            return
        st.funds -= st.INSPECT_COST
        st.inspected = True
        self.say([("maya", "燃料ラインの継ぎ目とナットを全部見直した。これで火災の危険はだいぶ下がるはず。")])

    def cmd_pr(self):
        if not self.use_ap(1):
            return
        r = pyxel.rndf(0, 1)
        if r < 0.2:
            self.st.reputation += 8
            self.say([("dylon", "(SNS に投稿)「俺たちは火星に行く」"),
                      ("ken", "バズった! 評判がぐっと上がったよ!")])
        elif r < 0.3:
            self.st.reputation = max(0, self.st.reputation - 3)
            self.say([("dylon", "(SNS に投稿)「ロケットなんて簡単だ」"),
                      ("ken", "……炎上してる。評判が下がったよ。")])
        else:
            gain = pyxel.rndi(2, 4)
            self.st.reputation += gain
            self.say([("ken", trf("工場見学の配信をしたよ! 評判が {gain} 上がった。", gain=gain))])

    def cmd_sales(self):
        if not self.use_ap(1):
            return
        self.say([("sara", "どこも「まず飛んでから来てくれ」って。実績がないと話も聞いてもらえないわ。")])

    def cmd_fund(self):
        st = self.st
        if st.month_index - st.last_fundraise < 3:
            self.say([("sara", "この前ピッチしたばかりよ。3ヶ月は空けないと、投資家も会ってくれない。")])
            return
        if not self.use_ap(1):
            return
        st.last_fundraise = st.month_index
        amount = round(3 + st.reputation * 0.4 + (10 if "1-1" in st.cleared else 0), 1)
        st.funds += amount
        if "schedule" not in st.seen:
            st.seen.add("schedule")
            lines = list(script.FUND_FIRST)
        else:
            lines = [("dylon", "(投資家に)俺たちは、戻ってくるロケットで宇宙を安くする。")]
        lines.append(("sara", trf("{amount}M$ 集まったわ。", amount=amount)))
        self.say(lines)

    def cmd_hire(self):
        st = self.st
        if st.ap_max >= 5:
            self.say([("maya", "今の工場じゃ、これ以上は人を置けないわ。")])
            return
        if not self.use_ap(1):
            return
        first = st.staff == 0
        st.ap_max += 1
        st.fixed_cost += 0.5
        st.staff += 1
        lines = list(script.HIRE_FIRST) if first else [("maya", "腕のいい溶接工を一人採用したわ。来月から AP が 1 増える。")]
        lines.append(("sara", trf("固定費は月 {cost:.1f}M$ になったわよ。", cost=st.fixed_cost)))
        self.say(lines)

    def cmd_launch(self):
        st = self.st
        if st.rockets <= 0:
            self.say([("maya", "飛ばせる機体がないわ。「製造」で新しい Eagle 1 を作って。")])
            return
        mdef = MISSIONS.get(st.stage) or MISSIONS["1-1"]
        lines = list(script.BRIEFING_1_1)
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
        build = trf(" 製造中{n}", n=len(st.building)) if st.building else ""
        funds = trf("資金 {funds:6.1f}M$", funds=st.funds)
        rep = trf("評判 {rep}", rep=st.reputation)
        rockets = trf("機体 {n}{build}", n=st.rockets, build=build)
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
        ui.text(ox + 170 * k, by + 6 * k, "EAGLE 1", ui.DBLUE, size=10 if ui.SMALL else 12)
        pyxel.circb(ox + 235 * k, by + 60 * k, 22 * k, ui.RED)
        pyxel.circ(ox + 235 * k, by + 60 * k, 6 * k, ui.DBLUE)
        pyxel.line(ox + 170 * k, by + 28 * k, ox + 250 * k, by + 28 * k, ui.BLACK)
        if not ui.TINY:  # 320x240 ではボードが小さくて入らない
            ui.text(ox + 260 * k, by + 34 * k, "10km!", ui.RED, size=10)
        # 机とノートPC
        pyxel.rect(ox + 40 * k, floor - 40 * k, 120 * k, 10 * k, ui.BROWN)
        pyxel.rect(ox + 48 * k, floor - 30 * k, 6 * k, 40 * k, ui.BROWN)
        pyxel.rect(ox + 146 * k, floor - 30 * k, 6 * k, 40 * k, ui.BROWN)
        pyxel.rect(ox + 80 * k, floor - 58 * k, 40 * k, 18 * k, ui.GRAY)
        pyxel.rect(ox + 82 * k, floor - 56 * k, 36 * k, 14 * k, ui.TEAL if self.frame // 30 % 2 else ui.LIME)
        # Eagle 1(機体があれば格納庫に立っている)
        if self.st.rockets > 0 or self.st.building:
            self.draw_rocket_in_hangar(ox + 470 * k, floor, k, built=self.st.rockets > 0)

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
            for i, line in enumerate(ui.wrap(cmd.desc, tw)[:n]):
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
