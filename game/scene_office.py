"""ADV パート: 会社(工場)画面。"""

import math

import pyxel

from . import script, ui
from .missions import MISSIONS
from .portraits import NAMES

STATUS_H = 28
VIEW_BOTTOM = 318
MSG_Y = 330
MSG_H = 92
CMD_Y = 432


class Command:
    def __init__(self, key, label, ap, desc, action):
        self.key = key
        self.label = label
        self.ap = ap
        self.desc = desc
        self.action = action


class OfficeScene:
    def __init__(self, app, lines=None):
        self.app = app
        self.st = app.state
        self.dlg = ui.Dialogue()
        self.sel = 0
        self.frame = 0
        self.commands = [
            Command("dev", "開発", 1, "研究で機体を扱いやすくする(準備中)", self.cmd_dev),
            Command("build", "製造", 1, f"Eagle 1 を製造する({self.st.ROCKET_COST:.0f}M$・{self.st.ROCKET_MONTHS}ヶ月)", self.cmd_build),
            Command("inspect", "点検", 1, f"次の打ち上げの故障を起きにくくする({self.st.INSPECT_COST}M$)", self.cmd_inspect),
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
        self.say([("maya", f"Eagle 1 の製造を始めたわ。{st.ROCKET_MONTHS}ヶ月後に完成する。")])

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
            self.say([("ken", f"工場見学の配信をしたよ! 評判が {gain} 上がった。")])

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
        self.say([("dylon", "(投資家に)俺たちは、戻ってくるロケットで宇宙を安くする。"),
                  ("sara", f"{amount}M$ 集まったわ。")])

    def cmd_hire(self):
        st = self.st
        if st.ap_max >= 5:
            self.say([("maya", "今の工場じゃ、これ以上は人を置けないわ。")])
            return
        if not self.use_ap(1):
            return
        st.ap_max += 1
        st.fixed_cost += 0.5
        st.staff += 1
        self.say([("maya", "腕のいい溶接工を一人採用したわ。来月から AP が 1 増える。"),
                  ("sara", f"固定費は月 {st.fixed_cost:.1f}M$ になったわよ。")])

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
        self.draw_hangar()
        self.draw_status()
        speaker = self.dlg.current[0] if self.dlg.active else ""
        if speaker:
            self.app.portraits.draw(speaker, 24, VIEW_BOTTOM - 136)
        self.draw_message(speaker)
        self.draw_commands()

    def draw_status(self):
        st = self.st
        pyxel.rect(0, 0, ui.W, STATUS_H, ui.NAVY)
        pyxel.line(0, STATUS_H, ui.W, STATUS_H, ui.DBLUE)
        ui.text(12, 8, st.date_str(), ui.WHITE)
        col = ui.RED if st.funds < 10 else ui.YELLOW
        ui.text(150, 8, f"資金 {st.funds:6.1f}M$", col)
        ui.text(290, 8, f"評判 {st.reputation}", ui.LIME)
        ui.text(370, 8, f"TLM {st.tlm}", ui.CYAN)
        ui.text(450, 8, f"AP {st.ap}/{st.ap_max}", ui.WHITE)
        build = f" 製造中{len(st.building)}" if st.building else ""
        ui.text(530, 8, f"機体 {st.rockets}{build}", ui.WHITE, size=10)

    def draw_hangar(self):
        top, bottom = STATUS_H + 1, VIEW_BOTTOM
        # 壁
        pyxel.rect(0, top, ui.W, bottom - top, ui.NAVY)
        for x in range(0, ui.W, 40):
            pyxel.line(x, top, x, bottom - 70, ui.BLACK)
        # 開いた格納庫の扉と空
        pyxel.rect(360, top + 16, 250, 200, ui.CYAN)
        pyxel.rect(360, top + 150, 250, 66, ui.DBLUE)
        pyxel.circ(560, top + 60, 16, ui.YELLOW)
        for i, (cx, cy) in enumerate(((400, top + 50), (470, top + 80))):
            pyxel.elli(cx + int(math.sin((self.frame + i * 90) / 120) * 6), cy, 50, 14, ui.WHITE)
        pyxel.rectb(358, top + 14, 254, 204, ui.GRAY)
        for y in range(top + 16, top + 216, 20):
            pyxel.line(360, y, 364, y, ui.GRAY)
        # 床
        pyxel.rect(0, bottom - 70, ui.W, 70, ui.GRAY)
        pyxel.line(0, bottom - 70, ui.W, bottom - 70, ui.WHITE)
        for x in range(-200, ui.W, 60):
            pyxel.line(x, bottom, x + 120, bottom - 70, ui.DBLUE)
        # ホワイトボード
        pyxel.rect(160, top + 30, 150, 90, ui.WHITE)
        pyxel.rectb(160, top + 30, 150, 90, ui.GRAY)
        ui.text(170, top + 36, "EAGLE 1", ui.DBLUE)
        pyxel.circb(235, top + 90, 22, ui.RED)
        pyxel.circ(235, top + 90, 6, ui.DBLUE)
        pyxel.line(170, top + 58, 250, top + 58, ui.BLACK)
        ui.text(260, top + 64, "10km!", ui.RED, size=10)
        # 机とノートPC
        pyxel.rect(40, bottom - 110, 120, 10, ui.BROWN)
        pyxel.rect(48, bottom - 100, 6, 40, ui.BROWN)
        pyxel.rect(146, bottom - 100, 6, 40, ui.BROWN)
        pyxel.rect(80, bottom - 128, 40, 18, ui.GRAY)
        pyxel.rect(82, bottom - 126, 36, 14, ui.TEAL if self.frame // 30 % 2 else ui.LIME)
        # Eagle 1(機体があれば格納庫に立っている)
        if self.st.rockets > 0 or self.st.building:
            self.draw_rocket_in_hangar(470, bottom - 70, built=self.st.rockets > 0)

    def draw_rocket_in_hangar(self, cx, base, built=True):
        h = 190
        top = base - h
        body = ui.WHITE if built else ui.GRAY
        pyxel.rect(cx - 9, top + 22, 18, h - 22, body)
        pyxel.tri(cx - 9, top + 22, cx + 8, top + 22, cx, top, body)
        pyxel.rect(cx - 9, top + 70, 18, 6, ui.BLACK)
        pyxel.rect(cx + 4, top + 22, 5, h - 22, ui.GRAY if built else ui.DBLUE)
        ui.text(cx - 3, top + 90, "S", ui.DBLUE, size=10)
        ui.text(cx - 3, top + 102, "T", ui.DBLUE, size=10)
        ui.text(cx - 3, top + 114, "A", ui.DBLUE, size=10)
        ui.text(cx - 3, top + 126, "R", ui.DBLUE, size=10)
        ui.text(cx - 3, top + 138, "X", ui.DBLUE, size=10)
        pyxel.tri(cx - 7, base, cx + 6, base, cx, base - 12, ui.BLACK)
        # 足場
        for x in (cx - 30, cx + 30):
            pyxel.line(x, top + 30, x, base, ui.YELLOW)
        for y in range(top + 40, base, 30):
            pyxel.line(cx - 30, y, cx + 30, y, ui.YELLOW)
        if not built:
            ui.text_center(cx, top - 16, "製造中", ui.YELLOW, border=ui.BLACK)

    def draw_message(self, speaker):
        ui.window(16, MSG_Y, ui.W - 32, MSG_H)
        if self.dlg.active:
            if speaker:
                name = NAMES.get(speaker, speaker)
                pyxel.rect(170, MSG_Y - 14, ui.text_width(name) + 16, 18, ui.DBLUE)
                pyxel.rectb(170, MSG_Y - 14, ui.text_width(name) + 16, 18, ui.WHITE)
                ui.text(178, MSG_Y - 11, name, ui.YELLOW)
            lines = ui.wrap(self.dlg.visible_text(), ui.W - 64)
            for i, line in enumerate(lines[:5]):
                ui.text(32, MSG_Y + 12 + i * ui.LINE_H, line, ui.WHITE)
            if self.dlg.waiting() and self.frame // 15 % 2:
                pyxel.tri(ui.W - 40, MSG_Y + MSG_H - 16, ui.W - 30, MSG_Y + MSG_H - 16, ui.W - 35, MSG_Y + MSG_H - 10, ui.WHITE)
        else:
            cmd = self.commands[self.sel]
            ui.text(32, MSG_Y + 12, f"【{cmd.label}】", ui.YELLOW)
            for i, line in enumerate(ui.wrap(cmd.desc, ui.W - 64)[:3]):
                ui.text(32, MSG_Y + 32 + i * ui.LINE_H, line, ui.WHITE)
            ui.text(32, MSG_Y + MSG_H - 20, "←→ 選択 / SPACE・Z 決定", ui.GRAY, size=10)

    def draw_commands(self):
        n = len(self.commands)
        bw, gap = 64, 4
        x0 = (ui.W - (n * bw + (n - 1) * gap)) // 2
        for i, cmd in enumerate(self.commands):
            x = x0 + i * (bw + gap)
            selected = i == self.sel and not self.dlg.active
            usable = cmd.ap == 0 or self.st.ap >= cmd.ap
            fill = ui.DBLUE if selected else ui.NAVY
            pyxel.rect(x, CMD_Y, bw, 36, fill)
            pyxel.rectb(x, CMD_Y, bw, 36, ui.YELLOW if selected else ui.DBLUE)
            col = ui.WHITE if usable else ui.GRAY
            ui.text_center(x + bw // 2, CMD_Y + 6, cmd.label, col)
            ap = f"AP{cmd.ap}" if cmd.ap else "-"
            ui.text_center(x + bw // 2, CMD_Y + 22, ap, ui.GRAY, size=10)
