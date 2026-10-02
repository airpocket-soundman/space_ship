"""会社画面(ADV)の背景画。

絵は tools/make_backgrounds.py が assets/backgrounds の発注した絵から作り、assets/bg に置く。
絵の色は標準の 16 色にないので、パレットの後ろに足してから読み込む(読み込み時に一番近い色へ置き換わるため)。
絵がなければ None を返す。そのときは、呼び出し側が今までどおりプログラムで描く。
"""

import json

import pyxel

from . import title_earth, ui

DIR = ui.ASSETS / "bg"
_meta = None
_images = {}


def _load_meta():
    global _meta
    if _meta is None:
        path = DIR / "meta.json"
        _meta = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"colors": [], "boards": {}}
        title_earth.add_earth_colors()  # タイトルの地球は 16 番からの色を決め打ちで使うので、先に足しておく
        have = set(pyxel.colors)
        for hex_ in _meta["colors"]:
            c = int(hex_, 16)
            if c not in have:
                pyxel.colors.append(c)
                have.add(c)
    return _meta


def image(name):
    """<name>_<画面サイズ>.png の絵。なければ None。"""
    key = f"{name}_{ui.SCREEN}"
    if key not in _images:
        _load_meta()
        path = DIR / f"{key}.png"
        _images[key] = pyxel.Image.from_image(str(path)) if path.exists() else None
    return _images[key]


def board(name):
    """絵の中のホワイトボードの白い面 (x0, y0, x1, y1)。絵の左上が原点。なければ None。"""
    return _load_meta()["boards"].get(f"{name}_{ui.SCREEN}")


def draw(name, x, y):
    """絵を (x, y) に描く。描けたら True。"""
    img = image(name)
    if img is None:
        return False
    pyxel.blt(x, y, img, 0, 0, img.width, img.height)
    return True


def whiteboard(key, month):
    """ホワイトボードの落書き(キーはステージか kickoff)。何パターンかあれば、月ごとに入れ替える。なければ None。"""
    nums = _load_meta().get("whiteboard", {}).get(key)
    if not nums:
        return None
    return image(f"wb/{key}_{nums[month % len(nums)]}")


def draw_doodle(img, board, top):
    """落書きを、ボードの白い面 board(場面の絵の中の座標)の真ん中に重ねる。top: 場面の絵の上の端。"""
    x0, y0, x1, y1 = board
    x = (x0 + x1 + 1 - img.width) // 2
    y = top + (y0 + y1 + 1 - img.height) // 2
    pyxel.blt(x, y, img, 0, 0, img.width, img.height, ui.PURPLE)

