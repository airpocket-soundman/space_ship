"""タイトルロゴ(assets/logo_<画面サイズ>.png)の色と読み込み。

ロゴは tools/make_logo.py が art/starx_logo.png から作る。画面ごとの幅で作ってあり、等倍で表示する。
背景(黒)は透明色として扱う。ロゴの色は標準の 16 色にないので、パレットの後ろに足す。
"""

import pyxel

from . import ui

LOGO_WIDTHS = {"640x480": 520, "720x720": 560, "360x360": 300, "320x240": 280}

LOGO_COLORS = [
    0xFDFDFD,  # 文字
    0xC8D2E2,  # 文字の縁(明)
    0x8C98B0,  # 文字の縁
    0x4A5468,  # 文字の縁(暗)
    0x5B7CA8,  # 軌跡(暗)
    0x93ADCF,  # 軌跡
    0xC5D4E9,  # 軌跡(明)
]


def load_logo():
    """パレットにロゴの色を足してから読み込む(読み込み時に一番近い色へ置き換わるため)。"""
    for c in LOGO_COLORS:
        if c not in pyxel.colors.to_list():
            pyxel.colors.append(c)
    return pyxel.Image.from_image(str(ui.ASSETS / f"logo_{ui.SCREEN}.png"))
