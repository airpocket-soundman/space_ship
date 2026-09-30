"""Native 720x720 design masters for StarX. No game files are changed."""

from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
C = {
    "black":"#000000","navy":"#2b335f","purple":"#7e2072","teal":"#19959c",
    "brown":"#8b4852","blue":"#395c98","ice":"#a9c1ff","white":"#eeeeee",
    "red":"#d4186c","orange":"#d38441","yellow":"#e9c35b","mint":"#70c6a9",
    "sky":"#7696de","gray":"#a3a3a3","pink":"#ff9798","skin":"#edc7b0",
}
CHARACTERS = "dylon maya ken sara noah dylon_ai grey doc_hughes bolt hashimoto mimi gen".split()


def rect(d, xy, color): d.rectangle(xy, fill=C[color])
def polygon(d, xy, color): d.polygon(xy, fill=C[color])
def line(d, xy, color, width=1): d.line(xy, fill=C[color], width=width)


def portrait_master(cid):
    im = Image.open(HERE / f"{cid}.png").convert("RGB").resize((128,128),Image.Resampling.NEAREST)
    d=ImageDraw.Draw(im)
    if cid not in ("noah","bolt"):
        # Redraw the whole face on the 128px canvas. This gives the eyes,
        # nose, jaw and expression genuinely independent pixels.
        skin="ice" if cid=="dylon_ai" else "skin"
        shade="blue" if cid=="dylon_ai" else "brown"
        hair={"grey":"gray","doc_hughes":"gray","ken":"yellow",
              "dylon_ai":"ice","mimi":"brown","sara":"brown",
              "gen":"gray"}.get(cid,"black")
        polygon(d,[(47,42),(80,42),(86,48),(86,68),(80,79),
                   (69,84),(56,83),(46,75),(42,63),(43,48)],"black")
        polygon(d,[(47,44),(78,44),(83,49),(83,66),(78,76),
                   (68,81),(56,80),(47,72),(45,61),(45,50)],skin)
        polygon(d,[(76,45),(83,50),(83,66),(78,76),(68,81),
                   (73,72),(77,62)],shade)
        polygon(d,[(47,47),(52,44),(56,46),(51,60),(46,64)],"white" if cid=="dylon_ai" else skin)
        # Deliberately shaped brows, sclera, iris and catchlight.
        for x in (49,70):
            line(d,(x,52,x+10,51),hair,2)
            rect(d,(x,57,x+10,64),"black")
            rect(d,(x+1,58,x+9,62),"white")
            rect(d,(x+4,57,x+7,63),"teal" if cid in ("dylon","dylon_ai") else "blue")
            rect(d,(x+5,59,x+7,62),"black")
            rect(d,(x+4,58,x+4,58),"white")
            line(d,(x,65,x+9,65),shade)
        line(d,(63,59,61,68,64,70),shade)
        line(d,(66,68,68,69),"white" if cid=="dylon_ai" else skin)
        rect(d,(63,70,65,71),shade)
        if cid in ("dylon","ken","mimi","dylon_ai"):
            line(d,(55,75,59,78,68,79,73,76),shade,2)
            line(d,(60,79,68,79),"white" if cid in ("ken","dylon") else "pink")
        else:
            line(d,(57,77,71,77),shade,2)
            line(d,(60,79,69,79),"pink" if cid=="sara" else skin)
        if cid in ("mimi","sara"):
            rect(d,(48,69,51,70),"pink")
            rect(d,(74,69,76,70),"pink")
        if cid in ("maya","doc_hughes"):
            # Dark glass outlines and small blue reflections stay readable.
            for x in (47,68):
                d.rectangle((x,54,x+15,67),outline=C["black"],width=2)
                line(d,(x+2,56,x+5,56),"ice")
            line(d,(63,58,67,58),"black",2)
        if cid=="ken":
            rect(d,(37,55,43,68),"gray")
            line(d,(41,69,48,75,54,75),"white",2)
        if cid=="gen":
            line(d,(55,80,61,84,70,84,74,80),"gray",2)
        if cid=="dylon_ai":
            for y in (46,68,81): line(d,(44,y,83,y),"teal")
        # Add fine clumps over the forehead after the face pass.
        for x,y in ((47,42),(52,39),(60,41),(74,40),(80,44)):
            if cid not in ("doc_hughes",):
                line(d,(x,y,x+2,y+4),hair)
    im.save(HERE / f"{cid}_720.png")
    return im


def portrait_sheet():
    sheet=Image.new("RGB",(6*152,2*176),C["black"])
    d=ImageDraw.Draw(sheet)
    for i,cid in enumerate(CHARACTERS):
        x,y=(i%6)*152,(i//6)*176
        sheet.paste(portrait_master(cid),(x+12,y+8))
        d.text((x+12,y+142),cid,fill=C["white"])
    sheet.save(HERE/"characters_720_sheet.png")


def rocket(d,x,top,bottom,w=15):
    l,r=x-w//2,x+w//2
    n=27
    polygon(d,[(x-2,top),(x+2,top),(r-2,top+10),(r,top+n-2),
               (r,top+n),(l,top+n),(l,top+n-2),(l+2,top+10)],"white")
    rect(d,(l,top+n,r,bottom),"white")
    rect(d,(r-5,top+n,r,bottom),"gray")
    rect(d,(l+1,top+n,l+3,bottom),"ice")
    rect(d,(l,top+int((bottom-top)*.48),r,top+int((bottom-top)*.48)+5),"black")
    for y in (top+n+9,top+n+44,bottom-31):
        line(d,(l+2,y,r-5,y),"sky")
    polygon(d,[(x-4,bottom),(x+4,bottom),(x+5,bottom+8),(x-5,bottom+8)],"black")
    rect(d,(x-2,bottom+1,x+2,bottom+4),"gray")


def office_master():
    im=Image.new("RGB",(360,360),C["navy"]); d=ImageDraw.Draw(im)
    rect(d,(0,0,359,15),"black")
    d.text((8,4),"STARX  /  OFFICE",fill=C["white"])
    d.text((272,4),"100M$",fill=C["mint"])
    rect(d,(0,16,359,262),"navy")
    for x in range(12,360,24):
        line(d,(x,16,x,260),"blue")
    for y in (49,95,143,192,238):
        line(d,(0,y,359,y),"black")
    # The tall 720 format permits a much taller hangar door and rocket.
    rect(d,(162,28,348,258),"black")
    rect(d,(168,35,342,164),"sky")
    rect(d,(168,164,342,217),"teal")
    rect(d,(168,217,342,258),"blue")
    rect(d,(289,58,306,75),"yellow")
    for x,y in ((186,70),(242,96),(303,113)):
        rect(d,(x,y,x+32,y+5),"white")
        rect(d,(x+6,y-3,x+25,y+1),"ice")
    rect(d,(156,20,164,263),"gray")
    rect(d,(346,20,353,263),"gray")
    for y in range(34,261,21):
        line(d,(157,y,164,y),"white")
    rect(d,(0,257,359,264),"gray")
    for x in range(0,360,30):
        line(d,(x,264,x-12,281),"blue")
    # Workbench and diagrams have more distinct details at this scale.
    rect(d,(16,159,134,169),"brown")
    rect(d,(23,169,29,260),"black")
    rect(d,(122,169,128,260),"black")
    rect(d,(43,114,98,155),"black")
    rect(d,(47,118,94,151),"teal")
    line(d,(53,145,62,132,70,137,82,123,90,129),"mint",2)
    rect(d,(105,105,145,152),"white")
    line(d,(112,116,136,116,136,141,112,141,112,116),"blue")
    line(d,(114,137,136,119),"red")
    rocket(d,254,50,239)
    rect(d,(229,248,279,253),"gray")
    # Actual screen portrait slot is 128x128. Shown at 64 logical pixels.
    rect(d,(5,269,354,330),"black")
    rect(d,(8,272,351,327),"navy")
    p=Image.open(HERE/"maya_720.png").resize((64,64),Image.Resampling.NEAREST)
    im.paste(p,(10,266))
    d.text((81,281),"MAYA",fill=C["yellow"])
    d.text((81,300),"EAGLE 1 IS READY.",fill=C["white"])
    rect(d,(5,337,354,357),"black")
    rect(d,(8,340,351,354),"blue")
    d.text((19,343),"BUILD    INSPECT    LAUNCH",fill=C["white"])
    high=im.resize((720,720),Image.Resampling.NEAREST)
    h=ImageDraw.Draw(high)
    for x in range(18,720,60):
        h.line((x,522,x+21,526),fill=C["ice"],width=1)
    high.save(HERE/"office_screen_720.png")


def launch_master():
    im=Image.new("RGB",(360,360),C["sky"]);d=ImageDraw.Draw(im)
    # 720 width: 520px flight view, 196px instrument panel.
    rect(d,(260,0,359,359),"black")
    rect(d,(263,3,356,356),"navy")
    for y in range(0,220,3):
        c="sky" if y<78 else "ice" if y<156 else "teal"
        line(d,(0,y,258,y),c,3)
    for x,y in ((18,45),(156,70),(67,138)):
        rect(d,(x,y,x+43,y+6),"white")
        rect(d,(x+8,y-3,x+31,y),"ice")
    rect(d,(0,220,259,359),"blue")
    for y in (230,249,271,296,321,344):
        for x in range((y*3)%31,260,34):
            line(d,(x,y,x+15,y),"teal")
    polygon(d,[(0,295),(52,270),(110,283),(173,262),(259,296),(259,359),(0,359)],"orange")
    polygon(d,[(0,303),(67,283),(120,294),(183,273),(259,306),(259,359),(0,359)],"brown")
    rect(d,(108,273,180,278),"gray")
    rect(d,(169,156,176,272),"gray")
    for y in range(162,269,12):
        line(d,(169,y,176,y+11),"black")
        line(d,(176,y,169,y+11),"white")
    rocket(d,131,127,272,12)
    rect(d,(111,280,151,284),"black")
    rect(d,(92,288,172,291),"gray")
    rect(d,(4,6,95,20),"black")
    d.text((10,9),"OMEGA ISLAND",fill=C["white"])
    d.text((273,12),"EAGLE 1",fill=C["white"])
    for i,(label,value) in enumerate((("ALT","0.0 km"),("VEL","0 m/s"),("FUEL","100%"),("THR","70%"))):
        y=53+i*59
        d.text((272,y),label,fill=C["ice"])
        d.text((272,y+18),value,fill=C["white"])
        rect(d,(272,y+33,346,y+36),"blue")
        rect(d,(272,y+33,328 if i==3 else 345,y+36),"mint")
    rect(d,(270,315,348,341),"black")
    d.text((280,324),"T - 05",fill=C["yellow"])
    high=im.resize((720,720),Image.Resampling.NEAREST)
    h=ImageDraw.Draw(high)
    for x in range(32,516,67):
        h.line((x,542,x+26,542),fill=C["ice"],width=1)
    high.save(HERE/"launch_screen_720.png")


if __name__ == "__main__":
    portrait_sheet()
    office_master()
    launch_master()
