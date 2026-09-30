"""立ち絵の読み込みと表示。

assets/portraits/<id>.png を読み込んで 128x128 の枠(360x360 の画面では 64x64)に表示する。
PNG は 128x128 か 64x64 を想定し、枠に合わせて拡大・縮小する。
ファイルがなければ名前入りの仮枠を出す。
"""

import struct

import pyxel

from . import ui

MAX_PNG = 128  # 読み込める PNG の最大サイズ
BANK = 2
SLOTS = [(0, 0), (128, 0), (0, 128), (128, 128)]

NAMES = {
    "dylon": "ディーロン",
    "maya": "マヤ",
    "ken": "ケン",
    "sara": "サラ",
    "noah": "ノア",
    "dylon_ai": "ディーロンAI",
    "grey": "グレイ",
    "doc_hughes": "ドク・ヒューズ",
    "bolt": "ボルト",
    "hashimoto": "ハシモト",
    "mimi": "ミミ",
    "gen": "ゲンさん",
}


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


class Portraits:
    def __init__(self):
        self.loaded = {}  # id -> (slot, w, h)
        self.order = []

    def _load(self, cid):
        if cid in self.loaded:
            self.order.remove(cid)
            self.order.append(cid)
            return self.loaded[cid]
        path = ui.ASSETS / "portraits" / f"{cid}.png"
        if not path.exists():
            self.loaded[cid] = None
            return None
        w, h = png_size(path)
        if w > MAX_PNG or h > MAX_PNG:
            self.loaded[cid] = None
            return None
        if len(self.order) >= len(SLOTS):
            old = self.order.pop(0)
            slot = self.loaded.pop(old)[0]
        else:
            used = {v[0] for v in self.loaded.values() if v}
            slot = next(s for s in SLOTS if s not in used)
        pyxel.images[BANK].load(slot[0], slot[1], str(path))
        self.loaded[cid] = (slot, w, h)
        self.order.append(cid)
        return self.loaded[cid]

    @staticmethod
    def size():
        """表示する枠の大きさ。"""
        return 64 if ui.SMALL else 128

    def draw(self, cid, x, y, dim=False):
        SIZE = self.size()
        pyxel.rect(x - 2, y - 2, SIZE + 4, SIZE + 4, ui.BLACK)
        info = self._load(cid)
        if info is None:
            pyxel.rect(x, y, SIZE, SIZE, ui.DBLUE)
            k = SIZE / 128
            pyxel.circ(x + 64 * k, y + 50 * k, 26 * k, ui.NAVY)
            pyxel.elli(x + 24 * k, y + 80 * k, 80 * k, 60 * k, ui.NAVY)
            ui.text_center(x + SIZE // 2, y + SIZE - 18, NAMES.get(cid, cid), ui.WHITE, size=10 if ui.SMALL else 12)
        else:
            (u, v), w, h = info
            scale = SIZE / max(w, h)
            pyxel.blt(x + SIZE / 2 - w / 2, y + SIZE / 2 - h / 2, BANK, u, v, w, h, None, 0, scale)
        pyxel.rectb(x - 2, y - 2, SIZE + 4, SIZE + 4, ui.WHITE)
        if dim:
            pyxel.dither(0.5)
            pyxel.rect(x, y, SIZE, SIZE, ui.BLACK)
            pyxel.dither(1.0)
