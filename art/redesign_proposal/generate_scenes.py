"""Draw standalone pixel-art proposals. Does not modify the game."""

from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
C = {
    "black": "#000000", "navy": "#2b335f", "night": "#2b335f", "purple": "#7e2072",
    "teal": "#19959c", "brown": "#8b4852", "blue": "#395c98",
    "ice": "#a9c1ff", "white": "#eeeeee", "red": "#d4186c",
    "orange": "#d38441", "yellow": "#e9c35b", "mint": "#70c6a9",
    "sky": "#7696de", "gray": "#a3a3a3", "pink": "#ff9798",
    "skin": "#edc7b0",
}


def new(w, h, bg="black"):
    im = Image.new("RGB", (w, h), C[bg])
    return im, ImageDraw.Draw(im)


def box(d, xy, c): d.rectangle(xy, fill=C[c])
def poly(d, xy, c): d.polygon(xy, fill=C[c])
def line(d, xy, c, width=1): d.line(xy, fill=C[c], width=width)
def save(im, name, scale=2):
    im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST).save(OUT / name)


def rocket(d, x, top, height, width, variant, legs=False):
    """Orthographic side silhouette with discrete cylindrical shading."""
    bottom = top + height
    half = width // 2
    left, right = x-half, x+half
    nose = max(10, round(width * (1.2 if variant == "starship" else 1.4)))
    # Body shadow and stepped highlight explain the cylinder at game scale.
    box(d, (left-1, top+nose, right+1, bottom), "black")
    box(d, (left, top+nose, right, bottom-1), "gray" if variant == "starship" else "white")
    box(d, (left+1, top+nose, left+max(2,width//3), bottom-1), "white")
    box(d, (right-max(2,width//4), top+nose, right, bottom-1), "blue" if variant == "starship" else "gray")
    # Rounded fairing / stainless ship nose rather than a triangular spear.
    poly(d, [(x-2,top), (x+2,top), (x+half-2,top+nose//3),
             (right,top+nose-2), (right,top+nose), (left,top+nose),
             (left,top+nose-2), (left+2,top+nose//3)],
         "gray" if variant == "starship" else "white")
    line(d, (x-2,top+1,left+2,top+nose-2), "white")
    poly(d, [(x+2,top+1),(right-1,top+nose-2),(right-3,top+nose)], "blue" if variant == "starship" else "gray")
    if variant == "starship":
        # Three visible body planes: sunlit stainless, midtone, tiled windward face.
        box(d, (left+2, top+nose, x-2, bottom-4), "white")
        box(d, (x-1, top+nose, x+4, bottom-4), "gray")
        box(d, (x+5, top+nose//2, right, bottom-4), "black")
        poly(d, [(x+2,top+1),(x+5,top+6),(right-1,top+nose-3),
                 (right,top+nose),(x+5,top+nose)], "black")
        # Pixel-scale tile joints and the stainless ring-weld cadence.
        for y in range(top+nose+8, bottom-8, 7):
            line(d, (left+3,y,x-2,y), "gray")
            line(d, (x+6,y,right-1,y), "navy")
            for tx in range(x+7,right-1,5):
                line(d,(tx,y-3,tx,y-1),"navy")
        # Small forward flaps near the nose, broad aft flaps low on the hull.
        poly(d, [(left,top+nose+10),(left-6,top+nose+5),
                 (left-6,top+nose+20),(left,top+nose+24)], "gray")
        line(d,(left-4,top+nose+8,left-4,top+nose+18),"white")
        poly(d, [(right,bottom-34),(right+10,bottom-38),
                 (right+11,bottom-14),(right,bottom-10)], "black")
        box(d, (left,bottom-5,right,bottom), "black")
        for nx in (x-5,x,x+5): box(d,(nx-1,bottom,nx+1,bottom+4),"gray")
    else:
        inter = top + int(height*.41)
        box(d, (left,inter,right,inter+5), "black")
        box(d, (left+1,inter,right-3,inter), "navy")
        for y in (top+nose+8, inter-4, bottom-13):
            line(d,(left+2,y,right-3,y),"ice")
        # A small engine bell; Eagle 1 is a single-engine first-gen vehicle.
        poly(d, [(x-3,bottom),(x+3,bottom),(x+4,bottom+5),(x-4,bottom+5)],"black")
        box(d,(x-2,bottom+1,x+2,bottom+3),"gray")
        if variant == "falcon":
            # Grid fins attached at the top of the first stage.
            for xx in (left-5,right+1):
                box(d,(xx,inter+7,xx+4,inter+13),"gray")
                for yy in (inter+9,inter+11): line(d,(xx,yy,xx+4,yy),"black")
        if legs:
            line(d,(left,bottom-16,left-8,bottom+3),"gray",2)
            line(d,(right,bottom-16,right+8,bottom+3),"gray",2)
            box(d,(left-10,bottom+3,left-6,bottom+4),"black")
            box(d,(right+6,bottom+3,right+10,bottom+4),"black")
    return bottom


def rocket_sheet():
    im,d = new(320,240,"night")
    box(d,(0,0,319,25),"black")
    box(d,(0,206,319,239),"navy")
    for x in range(0,320,16): line(d,(x,205,x+9,201),"blue")
    rocket(d,55,80,113,11,"eagle")
    rocket(d,156,41,153,12,"falcon",True)
    rocket(d,260,23,166,28,"starship")
    for x in (55,156,260):
        box(d,(x-31,204,x+31,205),"gray")
        box(d,(x-21,209,x+21,210),"blue")
    # Labels live on this study, never in the in-game sprite.
    d.text((18,12),"EAGLE 1",fill=C["white"])
    d.text((123,12),"REUSABLE",fill=C["white"])
    d.text((225,12),"STARSHIP TYPE",fill=C["white"])
    d.text((16,218),"SINGLE ENGINE",fill=C["ice"])
    d.text((118,218),"LEGS + GRID FINS",fill=C["ice"])
    d.text((224,218),"FLAPS + TILES",fill=C["ice"])
    save(im,"rocket_silhouette_study_v3.png")


def office():
    im,d = new(320,240,"navy")
    # Sample 640x480 screen: 29px status, 276px playfield, dialogue,
    # command row. The picture can be cropped independent of UI.
    box(d,(0,0,319,14),"black")
    d.text((8,3),"STARX  |  OFFICE",fill=C["white"])
    d.text((227,3),"FUNDS 100M",fill=C["mint"])
    box(d,(0,15,319,147),"night")
    for x in range(13,320,30):
        line(d,(x,15,x,147),"blue")
    for y in (39,87,123): line(d,(0,y,319,y),"black")
    # Open hangar: warm horizon, sea, secondary frame.
    box(d,(164,22,305,141),"black")
    box(d,(170,29,299,102),"sky")
    box(d,(170,102,299,141),"teal")
    box(d,(170,119,299,141),"blue")
    box(d,(263,40,275,52),"yellow")
    for xx,yy in ((185,45),(220,60),(274,73)):
        box(d,(xx,yy,xx+22,yy+4),"white")
        box(d,(xx+4,yy-2,xx+17,yy+2),"ice")
    for x in (160,307): box(d,(x,17,x+6,147),"gray")
    box(d,(0,141,319,150),"gray")
    for x in range(0,320,26): line(d,(x,149,x-18,169),"blue")
    # Distinct foreground props: drafting table, monitor, tool rack.
    box(d,(25,98,120,106),"brown")
    box(d,(31,106,36,145),"black")
    box(d,(109,106,114,145),"black")
    box(d,(48,67,89,95),"black")
    box(d,(51,70,86,91),"teal")
    line(d,(57,86,65,77,71,80,80,72),"mint",2)
    box(d,(131,39,160,96),"black")
    for y in (46,57,68,79):
        box(d,(137,y,154,y+3),"orange")
    rocket(d,240,43,94,8,"eagle")
    # Preview of dialogue and portrait placement at the actual layout scale.
    box(d,(4,153,315,212),"black")
    box(d,(7,156,312,209),"navy")
    p=Image.open(OUT/"maya.png").resize((52,52),Image.Resampling.NEAREST)
    im.paste(p,(10,157))
    d.text((71,163),"MAYA",fill=C["yellow"])
    d.text((71,180),"EAGLE 1 IS READY.",fill=C["white"])
    box(d,(4,217,315,235),"black")
    box(d,(7,220,312,232),"blue")
    d.text((18,222),"BUILD   /   INSPECT   /   LAUNCH",fill=C["white"])
    save(im,"office_screen_proposal.png")


def launch():
    im,d = new(320,240,"sky")
    # The current UI reserves 188/640 px on the right. Keep that structure.
    box(d,(224,0,319,239),"black")
    box(d,(227,3,316,236),"night")
    for y in range(0,155,3):
        c="sky" if y<50 else "ice" if y<100 else "teal"
        line(d,(0,y,222,y),c,3)
    for x,y in ((18,25),(137,41),(74,85)):
        box(d,(x,y,x+31,y+6),"white")
        box(d,(x+7,y-3,x+23,y),"ice")
    box(d,(0,156,222,239),"blue")
    for y in (164,180,199,219):
        for x in range((y*7)%23,223,29): line(d,(x,y,x+14,y),"teal")
    poly(d,[(0,189),(55,174),(104,181),(146,168),(223,189),(223,239),(0,239)],"orange")
    poly(d,[(0,197),(65,184),(110,189),(157,176),(223,196),(223,239),(0,239)],"brown")
    box(d,(70,177,153,181),"gray")
    # Pad structure and simplified tower recede behind the rocket.
    box(d,(132,93,137,178),"gray")
    for y in range(98,174,11):
        line(d,(132,y,137,y+10),"black")
        line(d,(137,y,132,y+10),"white")
    rocket(d,108,83,92,9,"eagle")
    box(d,(95,180,121,183),"black")
    box(d,(78,185,139,187),"gray")
    box(d,(3,5,72,16),"black")
    d.text((8,7),"OMEGA ISLAND",fill=C["white"])
    d.text((235,8),"EAGLE 1",fill=C["white"])
    for i,(label,value) in enumerate((("ALT","0.0 km"),("VEL","0 m/s"),("FUEL","100%"),("THR","70%"))):
        y=36+i*37
        d.text((235,y),label,fill=C["ice"])
        d.text((235,y+12),value,fill=C["white"])
        box(d,(234,y+24,308,y+26),"blue")
        box(d,(234,y+24,292 if i==3 else 305,y+26),"mint")
    box(d,(233,198,309,220),"black")
    d.text((238,204),"T - 05",fill=C["yellow"])
    save(im,"launch_screen_proposal.png")


def starship_v3_detail():
    """Two orthographic views of the V3 upper stage, based on 2026 flight hardware."""
    im,d = new(320,240,"night")
    box(d,(0,0,319,26),"black")
    d.text((11,9),"STARSHIP V3  /  UPPER STAGE",fill=C["white"])
    for x in (83,237):
        box(d,(x-51,214,x+51,216),"blue")
    # Left: heat-shield side, facing the viewer. Long tapered nose and
    # broad cylinder approximate the 52m x 9m ratio from SpaceX's vehicle page.
    for x,tile_view in ((83,True),(237,False)):
        top,bottom,w=41,198,27
        l,r=x-w//2,x+w//2
        poly(d,[(x-2,top),(x+2,top),(x+8,top+6),(r-2,top+24),
                (r,top+30),(l,top+30),(l+2,top+24),(x-8,top+6)],
             "black" if tile_view else "gray")
        box(d,(l,top+30,r,bottom),"black")
        if tile_view:
            box(d,(l+1,top+30,l+4,bottom-1),"gray")
            box(d,(l+5,top+30,r-1,bottom-1),"black")
            for y in range(top+35,bottom-6,6):
                line(d,(l+6,y,r-2,y),"navy")
                off=2 if (y//6)%2 else 0
                for xx in range(l+7+off,r-2,5):
                    line(d,(xx,y-4,xx,y-1),"navy")
            poly(d,[(l,top+44),(l-8,top+41),(l-8,top+58),(l,top+64)],"black")
            poly(d,[(r,bottom-44),(r+11,bottom-50),(r+11,bottom-20),(r,bottom-15)],"black")
        else:
            box(d,(l+1,top+30,l+4,bottom-1),"white")
            box(d,(l+5,top+30,r-7,bottom-1),"gray")
            box(d,(r-6,top+30,r-1,bottom-1),"blue")
            line(d,(l+3,top+10,l+1,top+29),"white")
            for y in range(top+39,bottom-4,9):
                line(d,(l+2,y,l+4,y),"gray")
                line(d,(l+5,y,r-8,y),"ice")
            poly(d,[(l,top+44),(l-7,top+40),(l-7,top+58),(l,top+62)],"gray")
            poly(d,[(r,bottom-44),(r+11,bottom-48),(r+11,bottom-20),(r,bottom-15)],"gray")
            line(d,(r+2,bottom-40,r+8,bottom-26),"white")
        box(d,(l,bottom-5,r,bottom),"navy")
        for nx in (x-6,x,x+6):
            poly(d,[(nx-2,bottom),(nx+2,bottom),(nx+3,bottom+6),(nx-3,bottom+6)],"gray")
    d.text((37,221),"HEAT-SHIELD SIDE",fill=C["ice"])
    d.text((198,221),"STEEL SIDE",fill=C["ice"])
    save(im,"starship_v3_detail.png")


if __name__ == "__main__":
    rocket_sheet()
    starship_v3_detail()
