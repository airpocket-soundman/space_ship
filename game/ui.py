"""フォント・入力・ウィンドウ描画などの共通部品。"""

from pathlib import Path

import pyxel

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

W, H = 640, 480

# Pyxel 標準パレットの番号
BLACK, NAVY, PURPLE, TEAL, BROWN, DBLUE, LBLUE, WHITE = range(8)
RED, ORANGE, YELLOW, LIME, CYAN, GRAY, PINK, PEACH = range(8, 16)

LINE_H = 16

_fonts = {}


def load_fonts():
    _fonts[12] = pyxel.Font(str(ASSETS / "fonts" / "umplus_j12r.bdf"))
    _fonts[10] = pyxel.Font(str(ASSETS / "fonts" / "umplus_j10r.bdf"))


def font(size=12):
    return _fonts[size]


def text(x, y, s, col=WHITE, size=12, border=None):
    f = _fonts[size]
    if border is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pyxel.text(x + dx, y + dy, s, border, f)
    pyxel.text(x, y, s, col, f)


def text_width(s, size=12):
    return _fonts[size].text_width(s)


def text_center(cx, y, s, col=WHITE, size=12, border=None):
    text(cx - text_width(s, size) // 2, y, s, col, size, border)


def wrap(s, width, size=12):
    """表示幅に収まるように折り返す(日本語は1文字単位)。"""
    lines = []
    for para in s.split("\n"):
        cur = ""
        for ch in para:
            if text_width(cur + ch, size) > width:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


def window(x, y, w, h, fill=NAVY, border=WHITE, shadow=True):
    if shadow:
        pyxel.rect(x + 3, y + 3, w, h, BLACK)
    pyxel.rect(x, y, w, h, fill)
    pyxel.rectb(x, y, w, h, border)
    pyxel.rectb(x + 2, y + 2, w - 4, h - 4, DBLUE)


def confirm():
    return (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A))


def cancel():
    return pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.KEY_BACKSPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)


def left_p():
    return pyxel.btnp(pyxel.KEY_LEFT, 12, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT, 12, 4)


def right_p():
    return pyxel.btnp(pyxel.KEY_RIGHT, 12, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT, 12, 4)


def up_p():
    return pyxel.btnp(pyxel.KEY_UP, 12, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP, 12, 4)


def down_p():
    return pyxel.btnp(pyxel.KEY_DOWN, 12, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN, 12, 4)


class Dialogue:
    """会話を1行ずつ文字送りで表示する。"""

    SPEED = 2  # 1 フレームに出す文字数

    def __init__(self):
        self.lines = []
        self.index = 0
        self.shown = 0
        self.on_done = None

    def start(self, lines, on_done=None):
        self.lines = list(lines)
        self.index = 0
        self.shown = 0
        self.on_done = on_done

    @property
    def active(self):
        return self.index < len(self.lines)

    @property
    def current(self):
        return self.lines[self.index] if self.active else None

    def update(self):
        if not self.active:
            return
        _speaker, body = self.current
        if self.shown < len(body):
            self.shown += self.SPEED
            if confirm():
                self.shown = len(body)
            return
        if confirm():
            self.index += 1
            self.shown = 0
            if not self.active and self.on_done:
                cb, self.on_done = self.on_done, None
                cb()

    def visible_text(self):
        _speaker, body = self.current
        return body[: self.shown]

    def waiting(self):
        return self.active and self.shown >= len(self.current[1])


# ---- 大きなロゴ用の簡易ビットマップ文字 ----

GLYPHS = {
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
}


def big_text(x, y, s, scale, col, shadow=None):
    cx = x
    for ch in s:
        g = GLYPHS.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "1":
                    if shadow is not None:
                        pyxel.rect(cx + gx * scale + 3, y + gy * scale + 3, scale, scale, shadow)
                    pyxel.rect(cx + gx * scale, y + gy * scale, scale, scale, col)
        cx += 6 * scale


def big_text_width(s, scale):
    return len(s) * 6 * scale - scale
