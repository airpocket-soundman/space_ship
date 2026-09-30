"""機体の絵。打ち上げ画面(回転する)でも格納庫(立っている)でも同じ形を描く。

形は「機体の底から軸に沿った距離 along [m]」と「軸からの横の距離 across [m]」で決め、
呼び出し側が渡す tf(along, across) → 画面座標 で好きな向き・大きさに描く。
見やすさのため、実寸より太く描いている。
"""

import math

import pyxel

from . import ui

# 描くときの半幅 [m](実際の直径とは別)
HALF_W = {"eagle1": 2.25, "eagle1_s2": 2.25, "eagle9": 3.2, "eagle9r": 3.2, "eagle9_s2": 3.2,
          "hopper": 3.2, "phoenix": 3.4}
CARGO_LEN = {"fairing": 9.0, "capsule": 6.0, "none": 0.0}
S1_LEN = 14.0  # Eagle 1 の1段目の長さ(Ch1-1 の 1 本の機体も、この位置に段の境目を描く)


def _quad(tf, a0, a1, w0, w1, col):
    """軸に対称な台形(a0 で半幅 w0、a1 で半幅 w1)。"""
    p0, p1, p2, p3 = tf(a0, -w0), tf(a0, w0), tf(a1, w1), tf(a1, -w1)
    pyxel.tri(*p0, *p1, *p2, col)
    pyxel.tri(*p0, *p2, *p3, col)


def _strip(tf, a0, a1, x0, x1, col):
    """軸に平行な帯(横の位置 x0〜x1)。"""
    p0, p1, p2, p3 = tf(a0, x0), tf(a0, x1), tf(a1, x1), tf(a1, x0)
    pyxel.tri(*p0, *p1, *p2, col)
    pyxel.tri(*p0, *p2, *p3, col)


def _body(tf, a0, a1, hw, col=ui.WHITE, shade=ui.GRAY):
    """円筒: 本体と、右側の陰。"""
    _quad(tf, a0, a1, hw, hw, col)
    _strip(tf, a0, a1, hw * 0.4, hw, shade)


def _nose(tf, a0, a1, hw, col=ui.WHITE, shade=ui.GRAY):
    """先端(a0 から a1 へすぼまる)。"""
    mid = a0 + (a1 - a0) * 0.55
    _quad(tf, a0, mid, hw, hw * 0.55, col)
    _quad(tf, mid, a1, hw * 0.55, 0.0, col)
    p0, p1, p2 = tf(a0, hw * 0.4), tf(a0, hw), tf(mid, hw * 0.55)
    pyxel.tri(*p0, *p1, *p2, shade)


def nozzle(tf, base, width, length, gimbal=0.0, col=ui.DBLUE):
    """エンジンのノズル(ジンバル角だけ振れる)。先端の中心の (along, across) を返す。"""
    s, c = math.sin(gimbal), math.cos(gimbal)
    # ジンバルが正のとき、ノズルの先は機体の右へ振れる
    cx, cy = base - c * length, s * length
    l = (cx - s * width, cy - c * width)
    r = (cx + s * width, cy + c * width)
    pyxel.tri(*tf(base, 0.0), *tf(*l), *tf(*r), col)
    pyxel.tri(*tf(base, -width * 0.45), *tf(base, width * 0.45), *tf(*l), col)
    pyxel.tri(*tf(base, width * 0.45), *tf(*l), *tf(*r), col)
    return cx, cy


def nozzle_geom(style, legs_out=False):
    """ノズルの付け根の along、幅、長さ。"""
    hw = HALF_W[style]
    lift = 1.6 if (legs_out and style == "eagle9r") or style == "hopper" else 0.0
    big = style in ("eagle9", "eagle9r")
    return lift + 0.4, hw * (0.75 if big else 0.7), 1.4 if lift else 3.0


def nozzle_tip(style, gimbal=0.0, legs_out=False):
    """ノズル先端の中心の (along, across)。炎はここから出る。"""
    if style == "phoenix":
        return 0.0, 0.0
    base, _, length = nozzle_geom(style, legs_out)
    return base - math.cos(gimbal) * length, math.sin(gimbal) * length


def legs(tf, a_top, hw, spread, col=ui.NAVY):
    """開いた着陸脚。足先は along = 0(地面)。"""
    for side in (-1, 1):
        pyxel.tri(*tf(a_top, side * hw), *tf(a_top - 2.2, side * hw), *tf(0.0, side * (hw + spread)), col)
        pyxel.line(*tf(1.2, side * hw), *tf(0.0, side * (hw + spread)), ui.GRAY)


def part(tf, style, base, length, legs_out=False, fins_out=False, flag=True):
    """1 段ぶんを描く(ノズルを除く)。base: この段の底の along。"""
    hw = HALF_W[style]
    top = base + length
    if style == "eagle1":
        # 1段目: 白い胴体、上端に黒い段間部。Ch1-1 の 1 本の機体では、その上に2段目と先端を続けて描く
        s1 = min(length, S1_LEN)
        _body(tf, base, base + s1 - 1.8, hw)
        _quad(tf, base + s1 - 1.8, base + s1, hw, hw, ui.BLACK)
        _strip(tf, base + 5.0, base + 5.4, -hw, hw * 0.4, ui.LBLUE)
        if length > S1_LEN:
            part(tf, "eagle1_s2", base + S1_LEN, length - S1_LEN)
    elif style == "eagle1_s2":
        _body(tf, base, base + length * 0.55, hw)
        _nose(tf, base + length * 0.55, top, hw)
        _strip(tf, base + 1.2, base + 1.6, -hw, hw * 0.4, ui.LBLUE)
    elif style in ("eagle9", "eagle9r"):
        lift = 1.6 if legs_out else 0.0  # 脚を開くと、足先が地面に付くぶん胴体が上がる
        b = base + lift
        _quad(tf, b, b + 1.6, hw, hw, ui.BLACK)
        _body(tf, b + 1.6, top - 3.0, hw)
        _quad(tf, top - 3.0, top, hw, hw, ui.BLACK)
        _strip(tf, top - 3.0, top, hw * 0.4, hw * 0.7, ui.NAVY)
        for a in (b + 9.0, b + 17.0):
            _strip(tf, a, a + 0.4, -hw, hw * 0.4, ui.LBLUE)
        if style == "eagle9r":
            if fins_out:
                for side in (-1, 1):
                    _strip(tf, top - 4.6, top - 3.2, side * hw, side * (hw + 2.6), ui.GRAY)
                    pyxel.line(*tf(top - 3.9, side * hw), *tf(top - 3.9, side * (hw + 2.6)), ui.NAVY)
            else:
                for side in (-1, 1):
                    _strip(tf, top - 6.6, top - 3.4, side * hw, side * (hw + 0.7), ui.GRAY)
            if legs_out:
                legs(tf, b + 7.0, hw, 6.5)
            else:
                for side in (-1, 1):
                    _strip(tf, b + 0.6, b + 8.0, side * (hw - 0.2), side * (hw + 0.8), ui.NAVY)
    elif style == "eagle9_s2":
        _body(tf, base, top, hw)
        _strip(tf, base + 2.0, base + 2.4, -hw, hw * 0.4, ui.LBLUE)
    elif style == "hopper":
        b = base + 1.6
        _body(tf, b, top - 2.2, hw, ui.GRAY, ui.NAVY)
        _strip(tf, b, top - 2.2, -hw, -hw * 0.45, ui.WHITE)
        _nose(tf, top - 2.2, top, hw, ui.BLACK, ui.BLACK)
        for a in (b + 5.0, b + 10.0):
            _strip(tf, a, a + 0.4, -hw, hw, ui.NAVY)
        legs(tf, b + 5.5, hw, 5.0, ui.BLACK)
    elif style == "phoenix":
        capsule(tf, base, hw, trunk=False)


def capsule(tf, base, hw, trunk=True):
    """カプセル Phoenix。底が耐熱シールド(黒)。trunk: 下に付く円筒(貨物を積むトランク)。"""
    b = base
    if trunk:
        _body(tf, b, b + 2.0, hw * 0.9, ui.GRAY, ui.NAVY)
        b += 2.0
    _quad(tf, b, b + 0.7, hw, hw, ui.BLACK)
    _quad(tf, b + 0.7, b + 3.4, hw, hw * 0.42, ui.WHITE)
    p0, p1, p2 = tf(b + 0.7, hw * 0.45), tf(b + 0.7, hw), tf(b + 3.4, hw * 0.42)
    pyxel.tri(*p0, *p1, *p2, ui.GRAY)
    _quad(tf, b + 3.4, b + 4.0, hw * 0.42, hw * 0.25, ui.GRAY)
    _strip(tf, b + 1.5, b + 2.1, -hw * 0.25, hw * 0.05, ui.NAVY)  # 窓


def cargo(tf, kind, base, hw):
    """いちばん上に載る荷物(フェアリング / カプセル)。"""
    if kind == "fairing":
        w = hw * 1.3
        _quad(tf, base, base + 1.2, hw, w, ui.WHITE)
        _body(tf, base + 1.2, base + 5.0, w)
        _nose(tf, base + 5.0, base + 9.0, w)
    elif kind == "capsule":
        capsule(tf, base, hw)


def satellite(tf):
    """放出した衛星。"""
    _quad(tf, -1.4, 1.4, 1.4, 1.4, ui.YELLOW)
    _strip(tf, -0.7, 0.7, 1.4, 6.0, ui.DBLUE)
    _strip(tf, -0.7, 0.7, -6.0, -1.4, ui.DBLUE)
    pyxel.line(*tf(1.4, 0.0), *tf(3.0, 0.0), ui.WHITE)


def vehicle(tf, stages, cargo_kind="none", gimbal=0.0, legs_out=False, fins_out=False, show_nozzle=True):
    """機体全体(下の段から順の VehicleParams の並び)。ノズル先端の (along, across) を返す。"""
    first = stages[0]
    tip = (0.0, 0.0)
    if show_nozzle and first.style != "phoenix":
        tip = nozzle(tf, *nozzle_geom(first.style, legs_out), gimbal)
    base = 0.0
    for p in stages:
        part(tf, p.style, base, p.length, legs_out, fins_out)
        base += p.length
    if cargo_kind != "none" and stages[-1].style != "eagle1_s2" and stages[-1].style != "eagle1":
        cargo(tf, cargo_kind, base, HALF_W[stages[-1].style])
    return tip


def upright(cx, base_y, k):
    """立っている機体用の tf。cx: 中心の x、base_y: 底の y、k: 1 m あたりのピクセル数。"""
    return lambda along, across: (cx + across * k, base_y - along * k)
