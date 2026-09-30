"""タイトルロゴ(assets/logo.png)の色と読み込み。

ロゴは tools/make_logo.py が art/starx_logo.webp から作る。
背景(黒)は透明色として扱う。ロゴの色は標準の 16 色にないので、パレットの後ろに足す。
"""

import pyxel

from . import ui

LOGO_COLORS = [
    0x0A1230,  # 縁取り
    0xFDFDFD,  # 文字
    0xDCE4F0,  # 文字の影(明)
    0xA8BCDA,  # 文字の影(暗)
    0x245599,  # 軌跡(暗)
    0x4E98F4,  # 軌跡
    0x9CCBFA,  # 軌跡(明)
]


def load_logo():
    """パレットにロゴの色を足してから読み込む(読み込み時に一番近い色へ置き換わるため)。"""
    for c in LOGO_COLORS:
        if c not in pyxel.colors.to_list():
            pyxel.colors.append(c)
    return pyxel.Image.from_image(str(ui.ASSETS / "logo.png"))
