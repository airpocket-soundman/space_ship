"""言語と画面サイズを選ぶ画面(初回の起動と、タイトルの OPTIONS)。

画面サイズを変えたときは起動し直す(game/settings.py)。
"""

import pyxel

from . import i18n, settings, ui
from .i18n import tr

SCREEN_NOTES = {"640x480": "", "720x720": "RGB20SX", "360x360": "", "320x240": ""}
LANG_NAMES = {"ja": "日本語", "en": "English"}


class SetupScene:
    ROWS = ("lang", "screen", "start")

    def __init__(self, app, from_title=False):
        self.app = app
        self.from_title = from_title  # タイトルから開いたときは X で戻れる
        self.frame = 0
        self.row = 0
        self.lang = i18n.LANG
        self.screen = ui.SCREEN

    def update(self):
        self.frame += 1
        if self.from_title and ui.cancel():
            self.app.to_title()
            return
        if ui.up_p():
            self.row = (self.row - 1) % len(self.ROWS)
        if ui.down_p():
            self.row = (self.row + 1) % len(self.ROWS)
        step = (1 if ui.right_p() else 0) - (1 if ui.left_p() else 0)
        if step:
            if self.ROWS[self.row] == "lang":
                keys = list(i18n.LANGS)
                self.lang = keys[(keys.index(self.lang) + step) % len(keys)]
                i18n.set_lang(self.lang)  # 画面の文字をすぐ切り替える
            elif self.ROWS[self.row] == "screen":
                keys = list(ui.SCREENS)
                self.screen = keys[(keys.index(self.screen) + step) % len(keys)]
        if ui.confirm():
            settings.save(self.screen, self.lang)
            if self.screen == ui.SCREEN:
                self.app.to_title()
            else:
                settings.relaunch(self.screen, self.lang)

    def draw(self):
        pyxel.cls(ui.BLACK)
        K = ui.K
        fs = 10 if ui.SMALL else 12
        lh = (16 if ui.SMALL else 22) * K
        cx = ui.W // 2
        y = ui.H // 2 - lh * 3
        ui.text_center(cx, y, "STAR X", ui.WHITE)
        ui.text_center(cx, y + lh, "言語と画面 / Language & Screen", ui.GRAY, size=fs)
        y += lh * 2 + 6 * K
        note = SCREEN_NOTES[self.screen]
        rows = [
            ("言語 / Language", LANG_NAMES[self.lang]),
            ("画面 / Screen", self.screen + (f"  ({note})" if note else "")),
            ("決定 / Start", ""),
        ]
        for i, (label, value) in enumerate(rows):
            sel = i == self.row
            col = ui.YELLOW if sel else ui.WHITE
            if value:
                ui.text_center(cx, y, label, ui.GRAY, size=fs)
                arrow = "< " if sel else "  "
                ui.text_center(cx, y + (fs + 4) * K, f"{arrow}{value}{' >' if sel else '  '}", col)
                y += lh + (fs + 4) * K
            else:
                ui.text_center(cx, y + 4 * K, f"> {label}" if sel and self.frame // 15 % 2 else label, col)
                y += lh
        hint = tr("↑↓ 選ぶ  ←→ 変える  SPACE 決定") + ("  " + tr("X 戻る") if self.from_title else "")
        ui.text_center(cx, ui.H - 16 * K, hint, ui.GRAY, size=10)
        if self.screen != ui.SCREEN:
            ui.text_center(cx, ui.H - 30 * K, "決定すると、この画面サイズで起動し直します。", ui.ORANGE, size=10)
