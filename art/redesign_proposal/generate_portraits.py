"""StarX portrait redesign: hand-authored 32px pixel shapes, exported at 64px.

Run: python art/redesign_proposal/generate_portraits.py
The original portraits in assets/portraits are intentionally untouched.
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = Path(__file__).resolve().parent
P = {
    "ink": "#000000", "night": "#2b335f", "plum": "#7e2072",
    "teal": "#19959c", "brown": "#8b4852", "blue": "#395c98",
    "ice": "#a9c1ff", "white": "#eeeeee", "red": "#d4186c",
    "orange": "#d38441", "yellow": "#e9c35b", "mint": "#70c6a9",
    "sky": "#7696de", "gray": "#a3a3a3", "pink": "#ff9798",
    "skin": "#edc7b0",
}


def add_face_detail(im, cid, spec):
    """One-pixel accents at the final 64px resolution, not doubled 32px blocks."""
    if spec.get("robot"):
        return im
    d = ImageDraw.Draw(im)
    def dot(x, y, color): d.point((x, y), fill=P[color])
    def stroke(points, color): d.line(points, fill=P[color], width=1)
    hair = spec["hair"]
    light = spec["hair_light"]
    # Irregular locks follow the cap shape and distinguish individual hairlines.
    for i, (x, y) in enumerate(((24, 18), (28, 17), (34, 18), (39, 20))):
        if spec.get("style") != "bald":
            stroke((x, y, x + (1 if i % 2 else -1), y + 3), light)
            dot(x + 1, y + 4, hair)
    if spec.get("style") in ("bob", "parted"):
        stroke((18, 29, 18, 39), light)
        stroke((46, 28, 46, 40), hair)
    if spec.get("style") == "spikes":
        for x, y in ((23, 12), (31, 8), (38, 10)):
            dot(x, y, "white")
    # Face shading: contour, bridge of nose, nostril, cheek light.
    stroke((23, 26, 23, 33), "brown")
    stroke((42, 29, 42, 36), "brown")
    dot(30, 33, "skin")
    dot(34, 33, "brown")
    dot(31, 34, "brown")
    dot(25, 34, "pink" if cid in ("mimi", "sara") else "skin")
    dot(39, 34, "brown")
    # Retain the strong eyebrow but break the eye into sclera, iris and catchlight.
    if not spec.get("visor"):
        for x in (27, 39):
            dot(x, 29, "white")
            dot(x + 1, 30, "teal" if cid in ("dylon", "dylon_ai") else "blue")
            dot(x + 1, 29, "white")
            dot(x + 2, 31, "brown")
        stroke((25, 26, 29, 26), hair)
        stroke((37, 26, 41, 26), hair)
    # Mouth: lip highlight is thinner than the 32px construction line.
    stroke((29, 37, 36, 37), "brown")
    dot(30, 38, "pink" if cid in ("mimi", "sara") else "skin")
    dot(35, 38, "skin")
    if spec.get("smile"):
        dot(28, 36, "brown")
        dot(37, 36, "brown")
    if spec.get("beard"):
        for x, y in ((26, 38), (29, 41), (33, 42), (37, 40)):
            dot(x, y, hair)
    if spec.get("glasses"):
        dot(25, 28, "white")
        dot(39, 28, "white")
    return im


def portrait(cid, spec):
    im = Image.new("RGB", (32, 32), P[spec["bg"]])
    d = ImageDraw.Draw(im)
    def R(box, c): d.rectangle(box, fill=P[c])
    def E(box, c): d.ellipse(box, fill=P[c])
    def L(points, c, w=1): d.line(points, fill=P[c], width=w)
    def G(points, c): d.polygon(points, fill=P[c])

    # Framed, quiet background. Three planes put the figure in a room,
    # without the speckled dithering that made the old portraits noisy.
    R((0, 0, 31, 5), "night")
    R((0, 24, 31, 31), "night")
    R((2, 3, 2, 21), spec["accent"])
    R((29, 7, 29, 22), spec["accent"])
    R((4, 27, 27, 27), "blue")
    R((7, 29, 24, 29), "blue")

    if spec.get("robot") == "screen":
        R((6, 5, 25, 25), "ink")
        R((7, 6, 24, 23), "gray")
        R((9, 8, 22, 20), "night")
        R((11, 12, 13, 14), "mint")
        R((18, 12, 20, 14), "mint")
        L((12, 17, 15, 18, 19, 17), "ice")
        R((14, 24, 17, 27), "gray")
        R((10, 28, 21, 29), "white")
    elif spec.get("robot") == "bolt":
        G([(5, 31), (6, 24), (10, 20), (21, 20), (26, 24), (27, 31)], "ink")
        R((8, 23, 23, 31), "orange")
        R((12, 21, 19, 24), "gray")
        R((8, 8, 23, 21), "ink")
        R((9, 9, 22, 19), "gray")
        R((11, 11, 20, 18), "blue")
        R((12, 13, 14, 14), "mint")
        R((18, 13, 20, 14), "mint")
        R((14, 17, 18, 17), "white")
        R((12, 5, 19, 7), "gray")
        R((15, 2, 16, 5), "white")
        R((15, 1, 16, 1), "yellow")
    else:
        jacket = spec["jacket"]
        shade = spec["shade"]
        skin = spec.get("skin", "skin")
        hair = spec["hair"]
        # Strong shoulders, simple three-tone garment, offset lighting.
        G([(2, 31), (3, 26), (7, 22), (11, 21), (21, 21), (25, 22), (29, 26), (30, 31)], "ink")
        G([(4, 31), (5, 26), (9, 23), (23, 23), (27, 26), (28, 31)], jacket)
        G([(4, 28), (7, 24), (11, 23), (10, 31), (4, 31)], shade)
        R((14, 19, 18, 24), skin)
        R((17, 20, 19, 22), "brown")
        if spec.get("long_hair"):
            R((8, 8, 23, 25), hair)
            R((7, 13, 9, 23), hair)
            R((22, 13, 24, 23), hair)
        # Face with a square chin and one-pixel edge shadow.
        R((10, 9, 22, 18), "ink")
        R((11, 10, 21, 19), skin)
        R((19, 11, 21, 18), "brown")
        R((13, 19, 19, 20), skin)
        R((10, 14, 11, 16), skin)
        R((21, 14, 22, 16), "brown")
        # Hair silhouette can change independently of the face shape.
        style = spec.get("style", "short")
        if style == "swept":
            G([(9, 14), (9, 8), (12, 5), (21, 6), (24, 9), (22, 12),
               (18, 10), (15, 11), (12, 10), (11, 15)], hair)
            L((11, 8, 16, 7, 21, 8), spec["hair_light"])
        elif style == "bob":
            R((9, 7, 23, 11), hair)
            R((8, 10, 10, 22), hair)
            R((22, 10, 24, 22), hair)
            R((10, 8, 21, 9), spec["hair_light"])
        elif style == "parted":
            G([(8, 12), (10, 7), (14, 6), (16, 9), (18, 6), (22, 7),
               (24, 12), (22, 16), (20, 10), (17, 10), (16, 12),
               (13, 9), (11, 15)], hair)
            R((17, 7, 19, 7), spec["hair_light"])
        elif style == "spikes":
            G([(9, 13), (8, 7), (12, 9), (13, 4), (16, 8), (19, 3),
               (20, 9), (24, 6), (23, 14), (21, 11), (12, 11)], hair)
            L((12, 7, 15, 9, 18, 7), spec["hair_light"])
        elif style == "bald":
            R((10, 10, 11, 12), hair)
            R((21, 10, 22, 12), hair)
        elif style == "cap":
            R((9, 5, 22, 9), hair)
            R((7, 9, 25, 10), hair)
            R((10, 6, 19, 6), spec["hair_light"])
        else:
            R((10, 6, 21, 10), hair)
            R((9, 8, 11, 13), hair)
            R((21, 8, 23, 12), hair)
            R((12, 7, 19, 7), spec["hair_light"])
        # Reserved facial pixels; each expression stays legible at 64px.
        R((12, 13, 14, 13), hair)
        R((18, 13, 20, 13), hair)
        R((13, 14, 14, 15), "ink")
        R((19, 14, 20, 15), "ink")
        R((13, 14, 13, 14), "white")
        R((19, 14, 19, 14), "white")
        R((16, 16, 17, 16), "brown")
        if spec.get("smile"):
            L((13, 18, 15, 19, 18, 19, 20, 18), "brown")
        else:
            R((14, 18, 19, 18), "brown")
        if spec.get("glasses"):
            R((11, 13, 15, 16), "ink")
            R((18, 13, 22, 16), "ink")
            R((12, 14, 14, 15), "ice")
            R((19, 14, 21, 15), "ice")
            R((16, 14, 17, 14), "ink")
        if spec.get("beard"):
            R((12, 19, 13, 20), hair)
            R((19, 19, 20, 20), hair)
            R((13, 21, 19, 21), hair)
        if spec.get("visor"):
            R((10, 12, 22, 16), "ink")
            R((11, 13, 21, 15), "teal")
            R((12, 13, 16, 13), "mint")
        if spec.get("headset"):
            R((8, 12, 10, 18), "gray")
            L((9, 18, 12, 20, 15, 20), "white")
        if spec.get("badge"):
            R((20, 25, 23, 26), spec["accent"])
        if spec.get("tie"):
            G([(15, 23), (18, 23), (17, 29), (16, 30)], spec["accent"])
        if spec.get("overall"):
            R((12, 24, 13, 31), "gray")
            R((20, 24, 21, 31), "gray")
            R((14, 27, 19, 27), "yellow")
        if spec.get("ai"):
            for y in range(3, 32, 4):
                L((0, y, 31, y), "teal")
            R((4, 3, 6, 4), "mint")
            R((25, 27, 27, 28), "mint")
    im = add_face_detail(im.resize((64, 64), Image.Resampling.NEAREST), cid, spec)
    im.save(OUT / f"{cid}.png")
    return im


SPECS = {
    "dylon": dict(bg="blue", accent="yellow", jacket="night", shade="ink", hair="brown", hair_light="orange", style="swept", smile=True, badge=True),
    "maya": dict(bg="teal", accent="orange", jacket="orange", shade="brown", hair="ink", hair_light="blue", style="parted", long_hair=True, glasses=True, overall=True),
    "ken": dict(bg="blue", accent="red", jacket="red", shade="plum", hair="yellow", hair_light="white", style="spikes", smile=True, headset=True),
    "sara": dict(bg="night", accent="mint", jacket="blue", shade="night", hair="brown", hair_light="orange", style="bob", tie=True),
    "noah": dict(bg="night", accent="mint", robot="screen"),
    "dylon_ai": dict(bg="night", accent="mint", jacket="blue", shade="night", hair="ice", hair_light="white", style="swept", smile=True, ai=True),
    "grey": dict(bg="blue", accent="ice", jacket="gray", shade="blue", hair="gray", hair_light="white", style="short", badge=True),
    "doc_hughes": dict(bg="teal", accent="white", jacket="white", shade="gray", hair="gray", hair_light="white", style="bald", glasses=True, beard=True),
    "bolt": dict(bg="night", accent="orange", robot="bolt"),
    "hashimoto": dict(bg="night", accent="yellow", jacket="gray", shade="blue", hair="ink", hair_light="night", style="short", badge=True),
    "mimi": dict(bg="plum", accent="pink", jacket="pink", shade="red", hair="brown", hair_light="orange", style="bob", smile=True),
    "gen": dict(bg="teal", accent="yellow", jacket="orange", shade="brown", hair="gray", hair_light="white", style="cap", beard=True, overall=True),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    images = [(name, portrait(name, spec)) for name, spec in SPECS.items()]
    sheet = Image.new("RGB", (6 * 128, 2 * 152), P["ink"])
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(images):
        x, y = (i % 6) * 128, (i // 6) * 152
        sheet.paste(im.resize((128, 128), Image.Resampling.NEAREST), (x, y))
        d.text((x + 4, y + 131), name, fill=P["white"])
    sheet.save(OUT / "_contact_sheet.png")


if __name__ == "__main__":
    main()
