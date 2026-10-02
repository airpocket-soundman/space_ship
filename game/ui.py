"""フォント・入力・ウィンドウ描画などの共通部品。"""

from pathlib import Path

import re

import pyxel

from . import audio
from .i18n import tr

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# 画面サイズ。どれもネイティブ解像度で描く(拡大して流用しない)。
SCREENS = {
    "640x480": (640, 480),
    "720x720": (720, 720),  # RGB20SX など正方形の画面
    "360x360": (360, 360),  # 720x720 に 2 倍で出す小さい画面
    "320x240": (320, 240),  # 640x480 に 2 倍で出す小さい画面
}
SCREEN = "640x480"
W, H = SCREENS[SCREEN]
SMALL = False  # 360x360 / 320x240 のときは文字や立ち絵を小さくする
TINY = False  # 320x240 のときはさらに縦を詰める
# 720x720 は、絵は 720 の細かさのまま、文字だけを 2 倍の大きさで描く(小さい画面で遊ぶ携帯機向け)。
# 文字の入る枠は 360x360 と同じ詰めた配置を K 倍して使う。
K = 1  # 文字と、文字の入る枠の倍率
COMPACT = False  # 文字の入る枠を、詰めた配置(360x360 と同じ並び)にする


def set_screen(name):
    """pyxel.init より前に呼ぶ。"""
    global SCREEN, W, H, SMALL, TINY, K, COMPACT, LINE_H
    if name not in SCREENS:
        raise ValueError(f"画面サイズは {' / '.join(SCREENS)} のどれか: {name}")
    SCREEN = name
    W, H = SCREENS[name]
    SMALL = W < 480
    TINY = H < 300
    K = 2 if name == "720x720" else 1
    COMPACT = SMALL or K > 1
    LINE_H = 16 * K

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
    """文字を描く。英語のときは訳してから描く(以下の幅・折り返しも同じ)。"""
    s = tr(s)
    if K > 1:
        return _text_big(x, y, s, col, size, border)
    f = _fonts[size]
    if border is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pyxel.text(x + dx, y + dy, s, border, f)
    pyxel.text(x, y, s, col, f)


_big_cache = {}  # (文字列, 色, 大きさ, 縁の色) → 文字を描いた画像(K 倍にして貼る)
_BIG_CACHE_MAX = 600


def _text_big(x, y, s, col, size, border):
    key = (s, col, size, border)
    entry = _big_cache.get(key)
    if entry is None:
        f = _fonts[size]
        w = f.text_width(s) + 2
        w += w % 2  # 拡大したときに半端なピクセルが出ないよう、幅を偶数にする
        h = size + 4
        keycol = next(c for c in (PURPLE, TEAL, BROWN) if c not in (col, border))
        img = pyxel.Image(max(w, 2), h)
        img.cls(keycol)
        if border is not None:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                img.text(1 + dx, 1 + dy, s, border, f)
        img.text(1, 1, s, col, f)
        entry = (img, keycol)
        if len(_big_cache) >= _BIG_CACHE_MAX:
            _big_cache.pop(next(iter(_big_cache)))
        _big_cache[key] = entry
    img, keycol = entry
    w, h = img.width, img.height
    # 拡大は貼り付け先の中心が基準なので、左上が (x, y) になるようにずらす(余白の 1 ドットも引く)
    pyxel.blt(x - K + w * (K - 1) / 2, y - K + h * (K - 1) / 2, img, 0, 0, w, h, keycol, 0, K)


def text_width(s, size=12):
    return _fonts[size].text_width(tr(s)) * K


def text_center(cx, y, s, col=WHITE, size=12, border=None):
    text(cx - text_width(s, size) // 2, y, s, col, size, border)


# 折り返しの単位: 英数字の語(後ろの空白ごと)か、それ以外の 1 文字
_TOKEN = re.compile(r"[!-~]+ *| +|.")


def wrap(s, width, size=12):
    """表示幅に収まるように折り返す。日本語は 1 文字単位、英語は単語単位。"""
    s = tr(s)
    lines = []
    for para in s.split("\n"):
        cur = ""
        for tok in _TOKEN.findall(para):
            if text_width(cur + tok.rstrip(), size) <= width:
                cur += tok
                continue
            if cur.strip():
                lines.append(cur.rstrip())
                cur = ""
            tok = tok.lstrip() if not cur else tok
            # 1 語だけで幅を超えるときは文字単位で切る
            while text_width(tok.rstrip(), size) > width:
                n = 1
                while n < len(tok) and text_width(tok[:n + 1], size) <= width:
                    n += 1
                lines.append(tok[:n])
                tok = tok[n:]
            cur = tok
        lines.append(cur.rstrip())
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
        self.images = []  # 行ごとの、それまでに出てきた挿絵の印の並び
        self.index = 0
        self.shown = 0
        self.on_done = None

    QUIET = set(" 　、。,.!?！？…「」()（）—-ー")  # 声を鳴らさない文字

    def start(self, lines, on_done=None):
        # ("image", 番号) は挿絵を出す位置の印。会話の行にはせず、その行から先で出す挿絵として覚えておく
        self.lines, self.images = [], []
        marks = []
        for speaker, body in lines:
            if speaker == "image":
                marks = marks + [body]
            else:
                self.lines.append((speaker, tr(body)))
                self.images.append(marks)
        self.index = 0
        self.shown = 0
        self.on_done = on_done

    @property
    def active(self):
        return self.index < len(self.lines)

    @property
    def current(self):
        return self.lines[self.index] if self.active else None

    @property
    def image_marks(self):
        """いまの行までに出てきた挿絵の印(古い順)。"""
        return self.images[self.index] if self.active else []

    def update(self):
        if not self.active:
            return
        speaker, body = self.current
        if self.shown < len(body):
            self.shown += self.SPEED
            # 3 フレームに 1 回、話者の声を鳴らす(しゃべっている感じ)
            self.tick = getattr(self, "tick", 0) + 1
            ch = body[min(self.shown, len(body)) - 1]
            if self.tick % 3 == 0 and ch not in self.QUIET:
                audio.voice(speaker)
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


# ---- 英字のドット書体(5x7) ----

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00100", "01000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
}


def big_text(x, y, s, scale, col, shadow=None, spacing=1):
    """5x7 のドット書体で英字を描く。spacing は文字間(ドット数)。"""
    cx = x
    for ch in s:
        g = GLYPHS.get(ch)
        if g is not None:
            for gy, row in enumerate(g):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        if shadow is not None:
                            pyxel.rect(cx + gx * scale + scale // 2 + 1, y + gy * scale + scale // 2 + 1,
                                       scale, scale, shadow)
                        pyxel.rect(cx + gx * scale, y + gy * scale, scale, scale, col)
        cx += (5 + spacing) * scale


def big_text_width(s, scale, spacing=1):
    return len(s) * (5 + spacing) * scale - spacing * scale