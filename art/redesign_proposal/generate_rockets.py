"""Draw separate, transparent rocket proposals for 720 and 360 game layouts.

The dimensions are deliberately schematic. Stage proportions and visible hardware
follow SpaceX's vehicle pages and the 2025 Falcon user guide; this is game art.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
C = {
    "ink": "#172033", "black": "#262b35", "tile": "#30343c",
    "tile_light": "#515761", "shadow": "#646c78", "steel": "#aeb7c0",
    "light": "#e6e8e7", "white": "#f6f5ef", "glint": "#ffffff",
    "warm": "#c7bcb1", "engine": "#49515b", "copper": "#a9744d",
    "blue": "#7993ad", "bg": "#101525", "line": "#394762",
    "gold": "#e9c35b", "muted": "#b7c6dd",
}


def canvas(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def rect(d, box, fill, outline=None):
    d.rectangle(box, fill=C.get(fill, fill), outline=C.get(outline, outline))


def poly(d, points, fill, outline=None):
    d.polygon(points, fill=C.get(fill, fill), outline=C.get(outline, outline))


def grid_fin(d, x, y, w=17, h=25):
    # Flat lattice, not a triangular aerodynamic flap.
    rect(d, (x, y, x+w, y+h), "ink")
    rect(d, (x+2, y+2, x+w-2, y+h-2), "shadow")
    for gx in range(x+4, x+w-2, 4):
        d.line((gx, y+2, gx, y+h-2), fill=C["ink"], width=1)
    for gy in range(y+5, y+h-2, 5):
        d.line((x+2, gy, x+w-2, gy), fill=C["ink"], width=1)
    rect(d, (x+3, y+h, x+w-3, y+h+3), "engine")


def engine_cluster(d, cx, y, count=3, radius=6):
    gap = radius*2+2
    x0 = cx-(count-1)*gap//2
    for i in range(count):
        x = x0+i*gap
        poly(d, [(x-4,y),(x+4,y),(x+radius,y+9),(x+radius-1,y+13),
                 (x-radius+1,y+13),(x-radius,y+9)], "engine", "ink")
        rect(d, (x-3,y+3,x+3,y+5), "copper")


def stainless_body(d, cx, top, bottom, half=24):
    rect(d, (cx-half, top, cx+half, bottom), "steel", "ink")
    rect(d, (cx-half+2, top+2, cx-half+8, bottom-2), "light")
    rect(d, (cx-half+9, top+2, cx-half+11, bottom-2), "white")
    rect(d, (cx+half-10, top+2, cx+half-2, bottom-2), "shadow")
    for y in range(top+37, bottom-5, 43):
        d.line((cx-half+2,y,cx+half-2,y), fill=C["shadow"], width=1)
        d.line((cx-half+3,y+1,cx+half-5,y+1), fill=C["light"], width=1)


def starship_ship():
    im,d = canvas(144, 280)
    cx=72
    # Upper stage: 52 m x 9 m. Blunt ogive, stainless leeward face and black windward tiles.
    poly(d, [(cx-4,10),(cx-8,14),(cx-14,25),(cx-20,48),(cx-24,78),
             (cx-24,243),(cx+24,243),(cx+24,78),(cx+20,48),
             (cx+14,25),(cx+8,14),(cx+4,10)], "steel", "ink")
    poly(d, [(cx+2,11),(cx+6,13),(cx+14,27),(cx+20,49),(cx+24,79),
             (cx+24,241),(cx+4,241),(cx+4,29)], "tile", "ink")
    poly(d, [(cx-4,14),(cx-13,29),(cx-19,52),(cx-22,80),
             (cx-22,241),(cx-13,241),(cx-13,76),(cx-10,45)], "light")
    d.line((cx-20,81,cx-20,240), fill=C["white"], width=2)
    d.line((cx+5,33,cx+5,238), fill=C["tile_light"], width=1)
    for y in range(98,233,23):
        d.line((cx-18,y,cx+2,y), fill=C["shadow"], width=1)
        d.line((cx+7,y,cx+21,y), fill=C["tile_light"], width=1)
    # Two of four forward flaps seen in this profile. Small swept paddles, not wings.
    poly(d, [(cx-23,57),(cx-30,59),(cx-34,77),(cx-36,91),
             (cx-30,93),(cx-23,83)], "steel", "ink")
    poly(d, [(cx+23,57),(cx+30,59),(cx+34,77),(cx+36,91),
             (cx+30,93),(cx+23,83)], "tile", "ink")
    d.line((cx-29,64,cx-32,85), fill=C["light"], width=2)
    d.line((cx+30,64,cx+32,85), fill=C["tile_light"], width=2)
    # Aft flaps have a swept root and a broad, nearly parallel outer edge.
    poly(d, [(cx-24,188),(cx-32,191),(cx-43,210),(cx-48,220),
             (cx-48,238),(cx-45,244),(cx-39,244),(cx-23,225)], "steel", "ink")
    poly(d, [(cx+24,188),(cx+32,191),(cx+43,210),(cx+48,220),
             (cx+48,238),(cx+45,244),(cx+39,244),(cx+23,225)], "tile", "ink")
    d.line((cx-31,197,cx-44,222), fill=C["light"], width=2)
    d.line((cx+31,197,cx+44,222), fill=C["tile_light"], width=2)
    rect(d, (cx-23,237,cx+23,245), "black", "ink")
    # Six Raptors in two rows, with the far row partly hidden.
    for dx in (-13,0,13):
        poly(d, [(cx+dx-3,244),(cx+dx+3,244),(cx+dx+5,257),
                 (cx+dx-5,257)], "engine", "ink")
        rect(d,(cx+dx-2,247,cx+dx+2,249),"copper")
    for dx in (-6,6):
        poly(d,[(cx+dx-3,245),(cx+dx+3,245),(cx+dx+4,252),
                (cx+dx-4,252)],"shadow","ink")
    return im


def super_heavy():
    im,d=canvas(144,370)
    cx=72
    stainless_body(d,cx,36,337)
    # Integrated hot-stage interface above the tank, with vent slots.
    rect(d,(cx-24,24,cx+24,43),"black","ink")
    for x in range(cx-19,cx+20,8):
        rect(d,(x,28,x+3,37),"shadow")
    rect(d,(cx-24,44,cx+24,50),"engine","ink")
    # V3 has three larger grid fins around circumference; two are visible in profile.
    grid_fin(d,cx-43,63,18,30)
    grid_fin(d,cx+25,63,18,30)
    rect(d,(cx-25,73,cx-22,100),"engine")
    rect(d,(cx+22,73,cx+25,100),"engine")
    rect(d,(cx-23,323,cx+23,339),"black","ink")
    for dx in (-16,-8,0,8,16):
        poly(d,[(cx+dx-3,338),(cx+dx+3,338),(cx+dx+5,350),
                (cx+dx-5,350)],"engine","ink")
        rect(d,(cx+dx-2,341,cx+dx+2,343),"copper")
    # No landing legs: tower catches Super Heavy by its fittings.
    return im


def starship_stack(ship,booster):
    im=Image.new("RGBA",(160,600),(0,0,0,0))
    im.alpha_composite(booster,(8,229))
    im.alpha_composite(ship,(8,8))
    return im


def falcon_core(side=False, deployed=False):
    im,d=canvas(100,365)
    cx=50
    # Falcon 9 diameter 3.7 m. White cylinder, dark interstage, 9 Merlin engines.
    rect(d,(cx-13,27,cx+13,326),"white","ink")
    rect(d,(cx-11,29,cx-7,324),"light")
    rect(d,(cx+7,29,cx+11,324),"warm")
    if side:
        poly(d,[(cx,9),(cx-5,11),(cx-10,18),(cx-13,30),
                (cx+13,30),(cx+10,18),(cx+5,11)],"white","ink")
    else:
        rect(d,(cx-13,21,cx+13,53),"black","ink")
        rect(d,(cx-10,25,cx-8,49),"shadow")
    grid_fin(d,cx-27,55,12,17)
    grid_fin(d,cx+15,55,12,17)
    for y in (102,175,246,303):
        d.line((cx-10,y,cx+9,y),fill=C["warm"],width=1)
    # Landing legs stowed against core in flight, not broad triangular wings.
    if deployed:
        poly(d,[(cx-12,272),(cx-18,283),(cx-31,329),(cx-38,337),
                (cx-30,340),(cx-19,326),(cx-11,299)],"engine","ink")
        poly(d,[(cx+12,272),(cx+18,283),(cx+31,329),(cx+38,337),
                (cx+30,340),(cx+19,326),(cx+11,299)],"engine","ink")
    else:
        poly(d,[(cx-14,257),(cx-18,268),(cx-17,325),(cx-11,325),
                (cx-12,274)],"engine","ink")
        poly(d,[(cx+14,257),(cx+18,268),(cx+17,325),(cx+11,325),
                (cx+12,274)],"engine","ink")
    rect(d,(cx-13,324,cx+13,333),"black","ink")
    for dx in (-8,0,8):
        poly(d,[(cx+dx-3,333),(cx+dx+3,333),(cx+dx+5,347),
                (cx+dx-5,347)],"engine","ink")
        rect(d,(cx+dx-2,336,cx+dx+2,338),"copper")
    return im


def falcon_nine(core):
    im,d=canvas(104,585)
    cx=52
    im.alpha_composite(core,(2,220))
    # Dark stage coupling and narrower white second stage.
    rect(d,(cx-11,139,cx+11,252),"white","ink")
    rect(d,(cx-9,142,cx-6,249),"light")
    rect(d,(cx+6,142,cx+9,249),"warm")
    rect(d,(cx-11,245,cx+11,252),"black","ink")
    # Payload fairing: 5.2 m diameter, broader than 3.7 m core, smooth ogive.
    poly(d,[(cx,13),(cx-5,16),(cx-12,24),(cx-18,43),(cx-19,60),
            (cx-19,134),(cx-11,143),(cx+11,143),(cx+19,134),
            (cx+19,60),(cx+18,43),(cx+12,24),(cx+5,16)],"white","ink")
    poly(d,[(cx-16,44),(cx-18,61),(cx-18,130),(cx-13,138),
            (cx-10,138),(cx-12,62)],"light")
    poly(d,[(cx+13,37),(cx+18,60),(cx+18,130),(cx+13,138),
            (cx+10,138),(cx+12,60)],"warm")
    d.line((cx,18,cx,139),fill=C["warm"],width=1)
    rect(d,(cx-19,127,cx+19,135),"white","ink")
    return im


def falcon_heavy(core,side):
    im,d=canvas(236,585)
    # Three distinct first-stage cores; side noses stop below the payload fairing.
    im.alpha_composite(side,(4,220))
    im.alpha_composite(side,(132,220))
    im.alpha_composite(core,(68,220))
    rect(d,(95,250,140,254),"engine","ink")
    rect(d,(95,382,140,386),"engine","ink")
    # Centre second stage and one fairing; Falcon Heavy is not three full rockets.
    centre=falcon_nine(falcon_core())
    im.alpha_composite(centre.crop((0,0,104,254)),(66,0))
    return im


def save_pair(name, im):
    im.save(OUT/f"{name}_720.png")
    im.resize((im.width//2,im.height//2),Image.Resampling.NEAREST).save(OUT/f"{name}_360.png")


def sheet(title, items):
    im=Image.new("RGB",(720,720),C["bg"])
    d=ImageDraw.Draw(im)
    font=ImageFont.truetype("C:/Windows/Fonts/consola.ttf",18)
    small=ImageFont.truetype("C:/Windows/Fonts/consola.ttf",13)
    d.text((24,20),title,font=font,fill=C["gold"])
    d.line((24,49,696,49),fill=C["line"],width=2)
    count=len(items)
    colw=672//count
    for i,(label,sprite) in enumerate(items):
        x=24+i*colw
        d.rectangle((x,66,x+colw-12,667),outline=C["line"],width=2)
        sx=x+(colw-12-sprite.width)//2
        sy=668-sprite.height
        im.paste(sprite,(sx,sy),sprite)
        d.text((x+9,680),label,font=small,fill=C["muted"])
    return im


def main():
    ship=starship_ship()
    heavy=super_heavy()
    stack=starship_stack(ship,heavy)
    f9core=falcon_core()
    f9=falcon_nine(f9core)
    fhside=falcon_core(side=True)
    fhcentre=falcon_core()
    fh=falcon_heavy(f9core,fhside)
    sprites={
        "starship_ship":ship,"super_heavy_booster":heavy,
        "starship_stack":stack,"falcon9":f9,
        "falcon9_booster":f9core,"falconheavy":fh,
        "falconheavy_side_booster":fhside,
        "falconheavy_centre_booster":fhcentre,
    }
    for name,sprite in sprites.items():
        save_pair(name,sprite)
    sheet("STARSHIP V3  /  separate transparent sprites",[
        ("SHIP",ship),("SUPER HEAVY",heavy),("FULL STACK",stack),
    ]).save(OUT/"starship_family_sheet_720.png")
    sheet("FALCON  /  separate transparent sprites",[
        ("FALCON 9",f9),("F9 CORE",f9core),("FALCON HEAVY",fh),
        ("SIDE CORE",fhside),
    ]).save(OUT/"falcon_family_sheet_720.png")


if __name__=="__main__":
    main()
