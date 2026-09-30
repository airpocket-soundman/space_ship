"""登場人物の 32x32 ドット絵立ち絵を生成する。

Pyxel の標準 16 色パレットだけを使う。
出力:
  assets/portraits/<id>.png        32x32 の原寸
  docs/img/portraits/<id>.png      企画書用に 8 倍へ拡大したもの
  assets/portraits.py              Pyxel で読み込むための文字列データ
"""

from pathlib import Path

from PIL import Image

W = H = 32

# Pyxel 2 の標準パレット
PALETTE = [
    0x000000, 0x2B335F, 0x7E2072, 0x19959C, 0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9, 0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0,
]
BLACK, NAVY, PURPLE, TEAL, BROWN, DBLUE, LBLUE, WHITE = range(8)
RED, ORANGE, YELLOW, LIME, CYAN, GRAY, PINK, PEACH = range(8, 16)

CX = 15.5  # 左右対称の中心


class Canvas:
    def __init__(self, bg):
        self.bg = bg
        self.px = [[bg] * W for _ in range(H)]
        self.fig = [[False] * W for _ in range(H)]

    def put(self, x, y, c, fig=True):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c
            if fig:
                self.fig[y][x] = True

    def sym(self, x, y, c):
        """左右対称に 1 ドット置く。"""
        self.put(x, y, c)
        self.put(31 - x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, ymin=0, ymax=H - 1):
        for y in range(max(0, ymin), min(H - 1, ymax) + 1):
            for x in range(W):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.put(x, y, c)

    def outline(self, c=BLACK):
        """人物の外周に 1 ドットの輪郭線を付ける。"""
        edge = []
        for y in range(H):
            for x in range(W):
                if self.fig[y][x]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and self.fig[ny][nx]:
                        edge.append((x, y))
                        break
        for x, y in edge:
            self.px[y][x] = c


# ---- 部品 ----------------------------------------------------------------

def body(cv, color, collar=None):
    cv.ellipse(CX, 33, 14, 9, color, ymin=24)
    if collar is not None:
        for i in range(3):
            cv.sym(13 + i, 24 + i, collar)


def neck(cv, skin=PEACH):
    cv.rect(13, 20, 18, 25, skin)


def head(cv, skin=PEACH):
    cv.ellipse(CX, 13.5, 6.6, 7.6, skin)
    cv.sym(8, 13, skin)
    cv.sym(8, 14, skin)


def eyes(cv, c=BLACK, y=13, style="dot"):
    if style == "dot":
        cv.sym(12, y, c)
        cv.sym(12, y + 1, c)
    elif style == "wide":
        cv.sym(12, y, WHITE)
        cv.sym(13, y, c)
        cv.sym(12, y + 1, c)
        cv.sym(13, y + 1, c)
    elif style == "sleepy":
        cv.sym(12, y + 1, c)
        cv.sym(13, y + 1, c)
    elif style == "sharp":
        cv.sym(12, y, c)
        cv.sym(13, y, c)
        cv.sym(13, y + 1, c)
    elif style == "glow":
        cv.sym(12, y, WHITE)
        cv.sym(13, y, WHITE)
        cv.sym(12, y + 1, LBLUE)
        cv.sym(13, y + 1, LBLUE)


def brows(cv, c, y=11, style="flat"):
    if style == "flat":
        cv.sym(11, y, c)
        cv.sym(12, y, c)
        cv.sym(13, y, c)
    elif style == "angry":
        cv.sym(11, y - 1, c)
        cv.sym(12, y, c)
        cv.sym(13, y, c)
    elif style == "thick":
        for x in (11, 12, 13):
            cv.sym(x, y, c)
            cv.sym(x, y - 1, c)


def mouth(cv, style="smile", y=18):
    if style == "smile":
        cv.rect(14, y, 17, y, BROWN)
        cv.sym(13, y - 1, BROWN)
    elif style == "grin":
        cv.rect(13, y, 18, y, WHITE)
        cv.sym(13, y, BROWN)
        cv.rect(14, y + 1, 17, y + 1, BROWN)
    elif style == "open":
        cv.rect(14, y, 17, y + 1, BROWN)
        cv.rect(15, y + 1, 16, y + 1, RED)
        cv.rect(14, y - 1, 17, y - 1, WHITE)
    elif style == "flat":
        cv.rect(14, y, 17, y, BROWN)
    elif style == "smirk":
        cv.rect(14, y, 16, y, BROWN)
        cv.put(17, y - 1, BROWN)


def cheeks(cv, c=PINK, y=16):
    cv.sym(10, y, c)
    cv.sym(11, y, c)


def nose(cv, c=PINK, y=16):
    cv.put(16, y, c)


# ---- 人物 ----------------------------------------------------------------

def dylon(skin=PEACH, hair=BROWN, shirt=BLACK, bg=DBLUE, eye="wide"):
    cv = Canvas(bg)
    body(cv, shirt)
    # 胸の X ロゴ
    for i in range(4):
        cv.put(14 + i, 26 + i, WHITE)
        cv.put(17 - i, 26 + i, WHITE)
    neck(cv, skin)
    head(cv, skin)
    # 短髪。前髪を右に流す
    cv.ellipse(CX, 12, 7.2, 7.2, hair, ymax=9)
    cv.rect(9, 8, 10, 12, hair)
    cv.rect(21, 8, 22, 11, hair)
    for x in range(13, 21):
        cv.put(x, 10, hair)
    cv.put(19, 11, hair)
    cv.put(20, 11, hair)
    eyes(cv, style=eye)
    brows(cv, hair, style="angry")
    nose(cv)
    mouth(cv, "grin")
    return cv


def dylon_ai():
    cv = dylon(skin=CYAN, hair=DBLUE, shirt=NAVY, bg=BLACK, eye="glow")
    # 走査線
    for y in range(1, H, 3):
        for x in range(W):
            if cv.fig[y][x] and cv.px[y][x] == CYAN:
                cv.px[y][x] = LBLUE
    cv.outline(TEAL)
    return cv


def maya():
    cv = Canvas(TEAL)
    body(cv, ORANGE, collar=WHITE)
    # 長い黒髪(後ろ)
    cv.ellipse(CX, 17, 9, 12, NAVY, ymax=26)
    neck(cv)
    head(cv)
    cv.ellipse(CX, 11, 7.4, 6.4, NAVY, ymax=9)
    cv.rect(9, 9, 9, 18, NAVY)
    cv.rect(22, 9, 22, 18, NAVY)
    # 頭の上のゴーグル
    cv.rect(9, 7, 22, 7, GRAY)
    cv.rect(11, 6, 14, 8, LBLUE)
    cv.rect(17, 6, 20, 8, LBLUE)
    # 眼鏡
    cv.rect(11, 12, 14, 15, GRAY)
    cv.rect(17, 12, 20, 15, GRAY)
    cv.rect(12, 13, 13, 14, PEACH)
    cv.rect(18, 13, 19, 14, PEACH)
    cv.put(15, 13, GRAY)
    cv.put(16, 13, GRAY)
    cv.sym(12, 14, BLACK)
    nose(cv)
    mouth(cv, "smirk")
    return cv


def ken():
    cv = Canvas(CYAN)
    body(cv, RED, collar=WHITE)
    neck(cv)
    head(cv)
    # ツンツンの金髪
    cv.ellipse(CX, 11, 7.4, 6, YELLOW, ymax=9)
    for x, top in ((9, 3), (12, 2), (15, 1), (18, 2), (21, 3)):
        for y in range(top, 8):
            cv.put(x, y, YELLOW)
            cv.put(x + 1, y + 1, YELLOW)
    cv.rect(9, 8, 9, 12, YELLOW)
    cv.rect(22, 8, 22, 12, YELLOW)
    # ヘッドセット
    cv.rect(8, 11, 8, 15, BLACK)
    cv.rect(23, 11, 23, 15, BLACK)
    for i in range(4):
        cv.put(9 + i, 17 + i // 2, GRAY)
    cv.put(13, 19, BLACK)
    eyes(cv, style="wide")
    brows(cv, ORANGE)
    cheeks(cv)
    mouth(cv, "open")
    return cv


def sara():
    cv = Canvas(GRAY)
    body(cv, NAVY, collar=WHITE)
    cv.rect(15, 26, 16, 31, WHITE)
    neck(cv)
    head(cv)
    # ボブカット
    cv.ellipse(CX, 12, 8, 7.6, BROWN, ymax=10)
    cv.rect(8, 9, 9, 19, BROWN)
    cv.rect(22, 9, 23, 19, BROWN)
    for x in range(10, 15):
        cv.put(x, 10, BROWN)
    cv.put(10, 11, BROWN)
    eyes(cv, style="sharp")
    brows(cv, BROWN)
    nose(cv)
    mouth(cv, "flat")
    # 真珠のイヤリング
    cv.sym(8, 20, WHITE)
    return cv


def noah():
    cv = Canvas(BLACK)
    # モニター型の頭と台
    cv.rect(13, 24, 18, 27, GRAY)
    cv.rect(9, 28, 22, 31, GRAY)
    cv.rect(5, 5, 26, 23, GRAY)
    cv.rect(7, 7, 24, 21, NAVY)
    # 目
    cv.rect(10, 11, 13, 14, CYAN)
    cv.rect(18, 11, 21, 14, CYAN)
    cv.rect(11, 12, 12, 13, LBLUE)
    cv.rect(19, 12, 20, 13, LBLUE)
    # 口(波形)
    for i, dy in enumerate((0, -1, 0, 1, 0, -1, 0, 1)):
        cv.put(12 + i, 18 + dy, LIME)
    # ランプ
    cv.put(24, 22, RED)
    cv.outline(DBLUE)
    return cv


def grey():
    cv = Canvas(LBLUE)
    body(cv, DBLUE, collar=WHITE)
    cv.rect(15, 26, 16, 31, RED)
    neck(cv)
    head(cv)
    # 七三分けの白髪まじり
    cv.ellipse(CX, 12, 7.2, 7, GRAY, ymax=9)
    cv.rect(9, 8, 9, 13, GRAY)
    cv.rect(22, 8, 22, 13, GRAY)
    for x in range(9, 13):
        cv.put(x, 10, GRAY)
    eyes(cv, style="dot")
    brows(cv, GRAY, style="thick")
    nose(cv)
    # 口ひげ
    cv.rect(13, 17, 18, 17, GRAY)
    mouth(cv, "flat", y=19)
    return cv


def doc_hughes():
    cv = Canvas(PURPLE)
    body(cv, WHITE)
    cv.put(11, 28, BLACK)
    cv.put(12, 29, BLACK)
    cv.put(20, 27, BLACK)
    neck(cv)
    head(cv)
    # 爆発した白髪
    for x, top in ((6, 6), (8, 3), (11, 2), (14, 1), (17, 1), (20, 2), (23, 3), (25, 6)):
        for y in range(top, 11):
            cv.put(x, y, WHITE)
            cv.put(x + 1, y, WHITE)
    cv.ellipse(CX, 10, 9, 5, WHITE, ymax=9)
    cv.rect(7, 9, 8, 15, WHITE)
    cv.rect(23, 9, 24, 15, WHITE)
    # 目にかけた溶接ゴーグル
    cv.rect(9, 12, 22, 12, BLACK)
    cv.rect(10, 12, 14, 15, BLACK)
    cv.rect(17, 12, 21, 15, BLACK)
    cv.rect(11, 13, 13, 14, ORANGE)
    cv.rect(18, 13, 20, 14, ORANGE)
    # すす
    cv.put(11, 17, GRAY)
    cv.put(20, 18, GRAY)
    cv.put(19, 9, GRAY)
    mouth(cv, "grin")
    return cv


def bolt():
    cv = Canvas(ORANGE)
    body(cv, GRAY)
    cv.rect(12, 26, 19, 31, LBLUE)  # ステンレスのエプロン
    neck(cv)
    head(cv)
    # はね上げた溶接マスク
    cv.ellipse(CX, 8, 8, 5, DBLUE, ymax=10)
    cv.rect(11, 5, 20, 7, BLACK)
    cv.rect(12, 6, 19, 6, TEAL)
    # ひげ
    cv.ellipse(CX, 18.5, 6.5, 4, BROWN, ymin=16)
    cv.rect(9, 13, 9, 17, BROWN)
    cv.rect(22, 13, 22, 17, BROWN)
    cv.rect(14, 18, 17, 18, RED)
    eyes(cv, style="dot")
    brows(cv, BROWN, style="thick")
    return cv


def hashimoto():
    cv = Canvas(LIME)
    body(cv, DBLUE, collar=YELLOW)
    neck(cv)
    head(cv)
    # 黄色いヘルメット
    cv.ellipse(CX, 10, 8.2, 6, YELLOW, ymax=10)
    cv.rect(6, 10, 25, 10, YELLOW)
    cv.rect(15, 4, 16, 9, ORANGE)
    cv.rect(9, 11, 9, 13, BLACK)
    cv.rect(22, 11, 22, 13, BLACK)
    # 耳にはさんだ箸
    for i in range(8):
        cv.put(23 + i // 3, 11 + i, BROWN)
        cv.put(24 + i // 3, 11 + i, ORANGE)
    eyes(cv, style="wide")
    brows(cv, BLACK)
    nose(cv)
    mouth(cv, "smile")
    return cv


def mimi():
    cv = Canvas(NAVY)
    # フード
    cv.ellipse(CX, 15, 10, 12, PURPLE, ymax=26)
    body(cv, PURPLE)
    cv.rect(14, 26, 14, 30, WHITE)
    cv.rect(17, 26, 17, 30, WHITE)
    head(cv, PEACH)
    # 前髪
    cv.ellipse(CX, 10, 7, 4.2, BLACK, ymax=11)
    cv.rect(9, 9, 9, 15, BLACK)
    cv.rect(22, 9, 22, 15, BLACK)
    # ヘッドホン
    cv.rect(7, 11, 8, 16, BLACK)
    cv.rect(23, 11, 24, 16, BLACK)
    cv.rect(7, 12, 8, 14, RED)
    cv.rect(23, 12, 24, 14, RED)
    eyes(cv, style="sleepy")
    cv.sym(12, 15, PURPLE)  # くま
    mouth(cv, "flat")
    # エナジードリンク
    cv.rect(25, 24, 27, 30, LIME)
    cv.rect(25, 24, 27, 24, GRAY)
    cv.put(26, 27, BLACK)
    return cv


def gen():
    cv = Canvas(BROWN)
    body(cv, DBLUE)
    cv.rect(11, 25, 12, 31, NAVY)  # つなぎの肩ひも
    cv.rect(19, 25, 20, 31, NAVY)
    neck(cv)
    head(cv)
    # はちまきと白い横髪
    cv.rect(9, 9, 22, 10, WHITE)
    cv.rect(10, 9, 21, 9, RED)
    cv.rect(23, 9, 25, 11, WHITE)
    cv.rect(9, 11, 9, 15, WHITE)
    cv.rect(22, 11, 22, 15, WHITE)
    # しわ
    cv.sym(12, 7, PINK)
    cv.sym(13, 7, PINK)
    eyes(cv, style="dot")
    brows(cv, WHITE, style="thick")
    cv.sym(10, 16, PINK)
    nose(cv)
    mouth(cv, "smile")
    return cv


CHARACTERS = [
    ("dylon", "ディーロン・マスク", dylon),
    ("maya", "マヤ・ホシノ", maya),
    ("ken", "ケン・ドウジマ", ken),
    ("sara", "サラ・カネダ", sara),
    ("noah", "ノア", noah),
    ("dylon_ai", "ディーロン AI", dylon_ai),
    ("grey", "グレイ", grey),
    ("doc_hughes", "ドク・ヒューズ", doc_hughes),
    ("bolt", "ボルト", bolt),
    ("hashimoto", "ハシモト", hashimoto),
    ("mimi", "ミミ", mimi),
    ("gen", "ゲンさん", gen),
]


def to_image(cv):
    img = Image.new("RGB", (W, H))
    for y in range(H):
        for x in range(W):
            c = PALETTE[cv.px[y][x]]
            img.putpixel((x, y), (c >> 16 & 255, c >> 8 & 255, c & 255))
    return img


def main():
    root = Path(__file__).resolve().parent.parent
    raw_dir = root / "assets" / "portraits"
    big_dir = root / "docs" / "img" / "portraits"
    raw_dir.mkdir(parents=True, exist_ok=True)
    big_dir.mkdir(parents=True, exist_ok=True)

    data_lines = [
        '"""登場人物の 32x32 立ち絵 (tools/make_portraits.py で自動生成)。',
        "",
        "各行は 32 文字の 16 進数 (Pyxel のパレット番号)。",
        "pyxel.images[n].set(x, y, PORTRAITS[id]) で読み込める。",
        '"""',
        "",
        "PORTRAITS = {",
    ]
    for cid, _name, fn in CHARACTERS:
        cv = fn()
        if cid not in ("noah", "dylon_ai"):
            cv.outline()
        img = to_image(cv)
        img.save(raw_dir / f"{cid}.png")
        img.resize((W * 8, H * 8), Image.NEAREST).save(big_dir / f"{cid}.png")
        data_lines.append(f'    "{cid}": [')
        for row in cv.px:
            data_lines.append('        "' + "".join(f"{c:x}" for c in row) + '",')
        data_lines.append("    ],")
    data_lines.append("}")
    (root / "assets" / "portraits.py").write_text("\n".join(data_lines) + "\n", encoding="utf-8")

    # 確認用の一覧シート
    cols = 6
    rows = (len(CHARACTERS) + cols - 1) // cols
    scale = 6
    sheet = Image.new("RGB", (cols * (W * scale + 8) + 8, rows * (H * scale + 8) + 8), (40, 40, 40))
    for i, (cid, _n, _f) in enumerate(CHARACTERS):
        img = Image.open(raw_dir / f"{cid}.png").resize((W * scale, H * scale), Image.NEAREST)
        sheet.paste(img, (8 + (i % cols) * (W * scale + 8), 8 + (i // cols) * (H * scale + 8)))
    sheet.save(root / "docs" / "img" / "portraits_sheet.png")


if __name__ == "__main__":
    main()
