"""会社画面(ADV)の背景画を、ゲームで使う形にする。

python tools/make_backgrounds.py

assets/backgrounds/<名前>_<型>.png(発注した 2 倍の大きさの絵。型 A / B / C)を、画面サイズごとの実寸に縮めて
assets/bg/<名前>_<画面サイズ>.png に書き出す。
- 720x720 と 360x360 は型 A、640x480 は型 B、320x240 は型 C から作る
- 大きさは会社画面の配置(game/scene_office.py の Layout)から決める
- 全部の絵を共通の COLORS 色に減らす。ゲームはその色をパレットの後ろに足してから読み込む
- 絵の中のホワイトボードの位置を測り、ゲームがそこに文字を書けるようにする
色と位置は assets/bg/meta.json に書く。

ホワイトボードの落書き(assets/whiteboard/wb_<キー>_<番号>.png、透過)も、画面ごとのボードの大きさに縮めて
assets/bg/wb/<キー>_<番号>_<画面サイズ>.png に書き出す。キーはステージ(1-1 など)か kickoff。
色は標準の 16 色に合わせ、透明なところは紫(ゲームが透明の印に使う色)で塗る。
"""

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game import ui  # noqa: E402
from game.missions import MISSIONS  # noqa: E402
from game.scene_office import Layout  # noqa: E402

SRC = ROOT / "assets" / "backgrounds"
OUT = ROOT / "assets" / "bg"
WB_SRC = ROOT / "assets" / "whiteboard"
# Pyxel の標準の 16 色。落書きはこの色にそろえる。2 番の紫は透明の印にするので、落書きには使わない
BASE = [0x000000, 0x2B335F, 0x7E2072, 0x19959C, 0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
        0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9, 0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0]
KEY = 2
COLORS = 64  # 背景に使う色の数(パレットは全部で 256 色まで。ほかの絵で 52 色使っている)
TYPE = {"720x720": "A", "360x360": "A", "640x480": "B", "320x240": "C"}
SCENES = ("b0_kickoff", "b1_hangar_omega", "b2_factory")

# ホワイトボードの、プログラムで描いていたときの位置(640x480 の格納庫の座標。床の線からの高さ)
BOARD = (160, 189, 310, 99)  # 左、床からの上端、右、床からの下端
# キックオフの部屋のホワイトボード(絵の中の中心のおよその位置。場面の幅・高さに対する割合)
KICKOFF_BOARD_CENTER = (0.50, 0.30)


def sizes(screen):
    """部品ごとの大きさと、格納庫の絵の倍率・位置。"""
    ui.set_screen(screen)
    lay = Layout()
    scene_h = lay.view_bottom - lay.status_h - 1
    return {
        "u2_status": (ui.W, lay.status_h + 1),
        "scene": (ui.W, scene_h),
        "u1_panel": (ui.W, ui.H - lay.view_bottom),
    }, lay, scene_h


def flood(img, seed, tol=24):
    """seed の色に近い、つながった範囲の外枠 (x0, y0, x1, y1)。"""
    px = img.load()
    w, h = img.size
    base = px[seed]
    near = lambda c: max(abs(c[i] - base[i]) for i in range(3)) <= tol  # noqa: E731
    seen, stack = {seed}, [seed]
    x0 = x1 = seed[0]
    y0 = y1 = seed[1]
    while stack:
        x, y = stack.pop()
        x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and near(px[nx, ny]):
                seen.add((nx, ny))
                stack.append((nx, ny))
    return x0, y0, x1, y1


def find_board(img, guess):
    """guess(予定の位置)の中から、白いボードの面を探す。見つからなければ guess を返す。"""
    gx0, gy0, gx1, gy1 = guess
    w, h = img.size
    cx, cy = (gx0 + gx1) // 2, (gy0 + gy1) // 2
    best = None
    # 予定の中心のまわりから、白い点を探して塗りつぶす(ボードの面は枠で囲まれている)
    for dy in range(-12, 13, 4):
        for dx in range(-24, 25, 6):
            x, y = min(max(cx + dx, 0), w - 1), min(max(cy + dy, 0), h - 1)
            c = img.getpixel((x, y))
            if min(c) < 190:
                continue
            box = flood(img, (x, y))
            bw, bh = box[2] - box[0], box[3] - box[1]
            # 壁ごと塗りつぶしたもの(大きすぎる)や、小さな光の点は外す
            if (gx1 - gx0) * 0.5 <= bw <= (gx1 - gx0) * 1.6 and (gy1 - gy0) * 0.4 <= bh <= (gy1 - gy0) * 1.6:
                if best is None or bw * bh > (best[2] - best[0]) * (best[3] - best[1]):
                    best = box
    return list(best) if best else list(guess)


def whiteboards(boards):
    """落書きを、画面ごとのボードの大きさに縮めて書き出す。{キー: [番号, ...]} を返す。"""
    found = {}
    rgb = [((c >> 16) & 255, (c >> 8) & 255, c & 255) for c in BASE]
    pens = [c for i, c in enumerate(rgb) if i != KEY]
    nearest = lambda c: min(pens, key=lambda p: sum((c[i] - p[i]) ** 2 for i in range(3)))  # noqa: E731
    out_dir = OUT / "wb"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):  # 消した落書きが残らないように、作り直す
        old.unlink()
    for path in sorted(WB_SRC.glob("wb_*.png")) if WB_SRC.exists() else []:
        key, _, num = path.stem[3:].rpartition("_")
        if not num.isdigit() or (key != "kickoff" and key not in MISSIONS):
            print(f"名前が決まりと違うので飛ばす: {path.name}")
            continue
        scene = "b0_kickoff" if key == "kickoff" else "b1_hangar_omega" if MISSIONS[key].craft == "eagle1" else "b2_factory"
        src = Image.open(path).convert("RGBA")
        for screen in TYPE:
            x0, y0, x1, y1 = boards[f"{scene}_{screen}"]
            bw, bh = (x1 - x0 + 1) * 0.94, (y1 - y0 + 1) * 0.90  # ボードの縁に少し余白を残す
            s = min(bw / src.width, bh / src.height)
            im = src.resize((max(1, round(src.width * s)), max(1, round(src.height * s))), Image.LANCZOS)
            px = im.load()
            out = Image.new("RGB", im.size, rgb[KEY])
            opx = out.load()
            cache = {}
            for y in range(im.height):
                for x in range(im.width):
                    r, g, b, a = px[x, y]
                    if a >= 128:
                        c = (r, g, b)
                        if c not in cache:
                            cache[c] = nearest(c)
                        opx[x, y] = cache[c]
            out.save(out_dir / f"{key}_{num}_{screen}.png", optimize=True)
        found.setdefault(key, []).append(int(num))
        print(f"落書き {path.name}")
    return {k: sorted(v) for k, v in found.items()}


def main():
    out = {}  # 出力の名前 → 画像(RGB)
    plan = []  # (出力の名前, 画面, 部品)
    boards_guess = {}
    for screen, t in TYPE.items():
        sz, lay, scene_h = sizes(screen)
        for part in ("u2_status", "u1_panel"):
            plan.append((f"{part}_{screen}", f"{part}_{t}", sz[part]))
        for name in SCENES:
            plan.append((f"{name}_{screen}", f"{name}_{t}", sz["scene"]))
            # 格納庫のボードの予定の位置(場面の絵の中の座標)
            k, ox, floor = lay.k, lay.ox, scene_h - 70 * lay.k
            if name == "b0_kickoff":
                bw, bh = 130 * k, 66 * k
                cx, cy = KICKOFF_BOARD_CENTER[0] * ui.W, KICKOFF_BOARD_CENTER[1] * scene_h
                boards_guess[f"{name}_{screen}"] = [int(cx - bw / 2), int(cy - bh / 2), int(cx + bw / 2), int(cy + bh / 2)]
            else:
                boards_guess[f"{name}_{screen}"] = [int(ox + BOARD[0] * k), int(floor - BOARD[1] * k),
                                                    int(ox + BOARD[2] * k), int(floor - BOARD[3] * k)]
    for name, src, size in plan:
        path = SRC / f"{src}.png"
        if not path.exists():
            print(f"ありません: {path.relative_to(ROOT)}")
            continue
        im = Image.open(path).convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        bg.alpha_composite(im)
        out[name] = bg.convert("RGB").resize(size, Image.LANCZOS)

    # 全部の絵をつなげて、共通の色を決める
    total_h = sum(im.height for im in out.values())
    strip = Image.new("RGB", (max(im.width for im in out.values()), total_h))
    y = 0
    for im in out.values():
        strip.paste(im, (0, y))
        y += im.height
    pal = strip.quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    flat = pal.getpalette()[: COLORS * 3]
    colors = sorted({(flat[i], flat[i + 1], flat[i + 2]) for i in range(0, len(flat), 3)})

    OUT.mkdir(exist_ok=True)
    boards = {}
    for name, im in out.items():
        q = im.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
        q.save(OUT / f"{name}.png", optimize=True)
        if name in boards_guess:
            boards[name] = find_board(q, boards_guess[name])
        print(f"{name}.png {q.size[0]}x{q.size[1]}" + (f"  ボード {boards[name]}" if name in boards else ""))
    meta = {"colors": ["%02X%02X%02X" % c for c in colors], "boards": boards, "whiteboard": whiteboards(boards)}
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"色 {len(colors)} / {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
