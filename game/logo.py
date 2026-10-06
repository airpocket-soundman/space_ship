"""タイトルロゴ(assets/logo_<画面サイズ>.png)の色と読み込み。

ロゴは tools/make_logo.py が art/starx_logo.webp から作る。画面ごとの幅で作ってあり、等倍で表示する。
背景(黒)は透明色として扱う。ロゴの色は標準の 16 色にないので、パレットの後ろに足す。
"""

import pyxel

from . import ui

LOGO_WIDTHS = {"640x480": 520, "720x720": 560, "360x360": 300, "320x240": 240}

LOGO_COLORS = [
    0xFFFFFF,  # 文字(白)
    0xE8EEF6,  # 文字(明)
    0xC8D2E2,  # 文字(中)
    0x9AB0CC,  # 文字(影)
    0x0A1A40,  # 光(暗)
    0x1C3F80,  # 光
    0x2F6CE0,  # 軌道の輪
    0x7FB4F0,  # 軌道の輪(明)
    0x4A4F5A,  # 月(暗)
    0x8A8F9A,  # 月
]


def load_logo():
    """パレットにロゴの色を足してから読み込む(読み込み時に一番近い色へ置き換わるため)。"""
    have = list(pyxel.colors)
    ui.add_colors(c for c in dict.fromkeys(LOGO_COLORS) if c not in have)
    return pyxel.Image.from_image(str(ui.ASSETS / f"logo_{ui.SCREEN}.png"))
