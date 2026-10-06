"""飛行画面の配置と、計器(下の帯)・メッセージ欄(右)の描画。打ち上げ画面と接近画面で共通。

    +----------------------------+-----------+
    |                            | メッセージ |
    |        飛行画面(view)      | 手順・案内 |
    |                            | 通知の履歴 |
    +----------------------------+-----------+
    | 計器 2 列(項目・目標・現在値)      | バー |
    +-----------------------------------------+

文字の入る枠は、詰めた配置(360x360 / 320x240)と通常(640x480)の 2 通り。720x720 は詰めた配置を K 倍する。
"""

import re

import pyxel

from . import ui
from .i18n import tr


class FlightLayout:
    def __init__(self):
        K, compact, tiny = ui.K, ui.COMPACT, ui.TINY
        self.K = K
        self.compact = compact
        self.tiny = tiny
        self.pad = (3 if tiny else 4 if compact else 8) * K
        self.row_h = (10 if tiny else 12 if compact else 14) * K
        self.rows = 6  # 計器の行数(2 列)
        self.hud_h = self.pad * 2 + self.row_h * self.rows
        self.msg_w = (116 if tiny else 128 if compact else 196) * K
        self.view_w = ui.W - self.msg_w
        self.view_h = ui.H - self.hud_h
        # 計器の帯: 計器 2 列(項目・目標・現在値)/ 右端にバー
        if tiny:
            bar, gap, self.val_w, self.tgt_w = (30, 36), 4, 30, 40
        elif compact:
            bar, gap, self.val_w, self.tgt_w = (32, 44), 5, 36, 46
        else:
            bar, gap, self.val_w, self.tgt_w = (52, 88), 10, 76, 84
        self.val_w *= K
        self.tgt_w *= K
        bar_w = (bar[0] + bar[1]) * K
        self.bar = (ui.W - self.pad - bar_w, bar[0] * K, bar[1] * K)
        inst_w = self.bar[0] - gap * K - self.pad
        col_w = (inst_w - gap * K) // 2
        self.cols = [(self.pad, col_w), (self.pad + col_w + gap * K, col_w)]


def plus_minus(lo, hi):
    """目標の範囲を「中央±幅」の文字にする(中央が 0 なら「±幅」)。"""
    c, d = (lo + hi) / 2, (hi - lo) / 2
    def num(x):
        return f"{x:.0f}" if abs(x) >= 10 or x == int(x) else f"{x:.1f}"
    return f"±{num(d)}" if abs(c) < 1e-9 else f"{num(c)}±{num(d)}"


def target_text(rng):
    """ミッションの表の範囲の文字(「250~500」など)を「中央±幅」に直す。片側だけの条件はそのまま。"""
    m = re.match(r"^([+-]?[\d.]+)~([+-]?[\d.]+)(.*)$", rng)
    if not m:
        return rng
    return plus_minus(float(m.group(1)), float(m.group(2))) + m.group(3)


def draw_hud(lay, entries, bars):
    """下の帯の計器。

    entries: 計器の行。(項目, 目標 or "", 現在値, 色)。2 列に、上から順に詰める
    bars: (ラベル, 割合, 色, 目盛り or None, 右端の文字 or "") の並び。割合が None ならジンバル(-1〜1)
    戻り値: 1 行目の目標の列の位置(操作説明の矢印で指す)
    """
    K, rh = lay.K, lay.row_h
    y0 = ui.H - lay.hud_h
    pyxel.rect(0, y0, ui.W, lay.hud_h, ui.NAVY)
    pyxel.rect(0, y0, ui.W, K, ui.DBLUE)
    top = y0 + lay.pad

    for n, (label, target, value, col) in enumerate(entries[:lay.rows * 2]):
        x, w = lay.cols[n // lay.rows]
        y = top + (n % lay.rows) * rh
        ui.text(x, y, tr(label, "hud"), ui.GRAY, size=10)
        if target:
            tx = x + w - lay.val_w - K
            ui.text(tx - ui.text_width(target, 10), y, target, ui.CYAN, size=10)
        ui.text(x + w - ui.text_width(value, 10), y, value, col, size=10)

    bx0, lw, bw = lay.bar
    bh = max(4, rh - 5 * K)
    y = top
    for label, frac, col, marker, text in bars[:lay.rows]:
        ui.text(bx0, y, tr(label, "hud"), ui.GRAY, size=10)
        bx, by = bx0 + lw, y + (rh - bh) // 2 - K
        pyxel.rect(bx, by, bw, bh, ui.BLACK)
        if frac is None:  # ジンバル: 真ん中からの振れ
            pyxel.rect(bx + bw // 2, by - K, K, bh + 2 * K, ui.DBLUE)
            gx = bx + bw // 2 + int(marker * (bw // 2 - 3 * K))
            pyxel.rect(gx - 2 * K, by, 5 * K, bh, col)
        else:
            pyxel.rect(bx, by, int(bw * max(0.0, min(1.0, frac))), bh, col)
            if marker is not None:
                pyxel.rect(bx + int(bw * marker), by - K, K, bh + 2 * K, ui.WHITE)
        pyxel.rectb(bx, by, bw, bh, ui.DBLUE)
        if text:
            ui.text(bx + bw - ui.text_width(text, 10) - 2 * K, y, text, ui.WHITE, size=10)
        y += rh
    x, w = lay.cols[0]
    return x + w - lay.val_w - lay.tgt_w // 2, top


def draw_messages(lay, title, goal, guide, guide_col, extra, prompt, blink, warp, log, keys, objective=None):
    """右のメッセージ欄。上から: ミッション名と目標 / 手順の案内 / 目安 / 押すキー / 通知の履歴 / 操作キー。

    guide: 手順の案内の文(枠で囲む。guide_col は枠の色)。extra: 案内の下に出す補足の行
    log: (文, 色) の並び(新しいものが下)
    """
    K = lay.K
    x0, w, h = lay.view_w, lay.msg_w, lay.view_h
    pad = (4 if lay.compact else 8) * K
    fs = 10
    lh = (11 if lay.tiny else 12) * K if lay.compact else 14
    tw = w - pad * 2
    pyxel.rect(x0, 0, w, h, ui.NAVY)
    pyxel.rect(x0, 0, K, h, ui.DBLUE)
    x = x0 + pad
    y = pad

    tfs = fs if lay.compact else 12
    for line in ui.wrap(title, tw, tfs)[:2]:  # 長いステージ名は折り返す
        ui.text(x, y, line, ui.YELLOW, size=tfs)
        y += lh if lay.compact else 18
    if goal and not lay.tiny:
        for line in ui.wrap(goal, tw, fs)[:2]:
            ui.text(x, y, line, ui.WHITE, size=fs)
            y += lh
    if objective:  # いま目指すもの(計器の水色の目標の見出し)と進み具合
        head, prog = objective
        for line in ui.wrap(head, tw, fs)[:2]:
            ui.text(x, y, line, ui.CYAN, size=fs)
            y += lh
        pyxel.rect(x, y, tw, 3 * K, ui.BLACK)
        pyxel.rect(x, y, int(tw * max(0.0, min(1.0, prog))), 3 * K, ui.CYAN)
        y += 5 * K
    y += 3 * K

    if guide:
        lines = ui.wrap(guide, tw - 6 * K, fs)
        bh = len(lines) * lh + 6 * K
        pyxel.rect(x - 2 * K, y, tw + 4 * K, bh, ui.BLACK)
        pyxel.rectb(x - 2 * K, y, tw + 4 * K, bh, guide_col)
        for i, line in enumerate(lines):
            ui.text(x + 2 * K, y + 3 * K + i * lh, line, ui.WHITE, size=fs)
        y += bh + 3 * K
    for line in extra:
        for part in ui.wrap(line, tw, fs):
            ui.text(x, y, part, ui.CYAN, size=fs)
            y += lh
    if prompt and blink:
        for part in ui.wrap(prompt, tw, fs):
            ui.text(x, y, part, ui.YELLOW, size=fs)
            y += lh
    elif prompt:
        y += lh * len(ui.wrap(prompt, tw, fs))
    if warp:
        ui.text(x, y, warp, ui.CYAN, size=fs)
        y += lh

    # 操作キー(いちばん下)
    key_lines = [part for line in keys for part in ui.wrap(line, tw, fs)]
    ky = h - pad - len(key_lines) * lh
    for i, line in enumerate(key_lines):
        ui.text(x, ky + i * lh, line, ui.GRAY, size=fs)

    # 通知の履歴: 操作キーの上に、新しいものが下になるよう詰める
    y = max(y + 3 * K, 0)
    space = ky - 3 * K - y
    lines = [(part, col) for text, col in log for part in ui.wrap(text, tw, fs)]
    n = max(0, space // lh)
    lines = lines[-n:] if n else []
    yy = ky - 3 * K - len(lines) * lh
    if lines:
        pyxel.rect(x - 2 * K, yy - 2 * K, tw + 4 * K, K, ui.DBLUE)
    for text, col in lines:
        ui.text(x, yy, text, col, size=fs)
        yy += lh


def big_count(lay, n):
    """カウントダウンの数字を、飛行画面の真ん中に大きく出す。"""
    s = str(n)
    scale = (6 if lay.compact else 10) * lay.K
    w = ui.big_text_width(s, scale)
    ui.big_text((lay.view_w - w) // 2, (lay.view_h - 7 * scale) // 2, s, scale, ui.WHITE, shadow=ui.BLACK)
