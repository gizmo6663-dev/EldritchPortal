#!/usr/bin/env python3
"""Bygger battlemap-dataene og bildene inn i verktøyet.

    python3 scenarios/build_maps.py --src <utpakket handoff-mappe>

Handoff-pakka har 30 bakgrunner og 516 enkeltsprites, altså 546 filer.
Et publisert artifact tar 255 filer, så enkeltsprites går ikke. Derfor
pakkes alle spritene et rom bruker i ett atlasbilde per rom, og
posisjonene legges i JSON-en. Det gir 60 filer, og nettleseren henter
to bilder per rom i stedet for førti.

Noen av filene i pakka heter .png, men er SVG med pikselkunst i. De
rasteriseres her, så alt ligger som ekte bilder når appen skal bruke
dem.

Ut:
    bestiary/battlemaps.json
    web/maps/<no>-<id>/bg.png
    web/maps/<no>-<id>/sprites.png
"""
import argparse
import collections
import json
import os
import shutil
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Trenger Pillow:  pip install pillow")

import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UT_JSON = os.path.join(REPO, "bestiary", "battlemaps.json")
UT_BILDER = os.path.join(REPO, "web", "maps")

# Luft mellom spritene i atlaset, så nærmeste-nabo-skalering ikke
# drar en pikselrad fra naboen med seg inn i kanten.
LUFT = 2


# ------------------------------------------------------------------
# Noen av filene i handoff-pakka heter .png, men er SVG. De er ren
# pikselkunst: én <path> per farge, satt sammen av rader som er én
# piksel høye. Det er enklere å tegne dem selv enn å dra inn en hel
# SVG-motor for 33 filer.
# ------------------------------------------------------------------

RAD = re.compile(r"M(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)h(-?\d+(?:\.\d+)?)")
PATH = re.compile(r'<path\s+fill="([^"]*)"\s+d="([^"]*)"')
MAAL = re.compile(r'width="(\d+)"\s+height="(\d+)"')


def farge(tekst):
    """#rrggbb eller rgba(r,g,b,a) til en firer."""
    t = tekst.strip()
    if t.startswith("#") and len(t) == 7:
        return (int(t[1:3], 16), int(t[3:5], 16), int(t[5:7], 16), 255)
    m = re.match(r"rgba?\(([^)]*)\)", t)
    if m:
        d = [x.strip() for x in m.group(1).split(",")]
        a = float(d[3]) if len(d) > 3 else 1.0
        return (int(d[0]), int(d[1]), int(d[2]), int(round(a * 255)))
    return (0, 0, 0, 255)


def er_svg(sti):
    with open(sti, "rb") as f:
        return f.read(4) == b"<svg"


def tegn_svg(sti):
    """Rasteriser en av pikselkunst-SVG-ene til et RGBA-bilde."""
    raa = open(sti, encoding="utf-8", errors="replace").read()
    # Metadatablokka inneholder base64 som ellers ville forvirret
    # uttrykkene under.
    kropp = re.sub(r"<metadata>.*?</metadata>", "", raa, flags=re.S)
    m = MAAL.search(kropp)
    if not m:
        raise ValueError("fant ikke målene i " + sti)
    bredde, hoyde = int(m.group(1)), int(m.group(2))

    bilde = Image.new("RGBA", (bredde, hoyde), (0, 0, 0, 0))
    tegner = ImageDraw.Draw(bilde)
    for fill, d in PATH.findall(kropp):
        f = farge(fill)
        rader = [(float(a), float(b), float(c)) for a, b, c in RAD.findall(d)]
        if not rader:
            continue
        if f[3] == 255:
            # Dekkende farge kan skrives rett inn.
            for x, y, w in rader:
                tegner.rectangle([x, y, x + w - 1, y], fill=f)
        else:
            # Skygger må blandes med det som alt ligger under.
            lag = Image.new("RGBA", (bredde, hoyde), (0, 0, 0, 0))
            d2 = ImageDraw.Draw(lag)
            for x, y, w in rader:
                d2.rectangle([x, y, x + w - 1, y], fill=f)
            bilde = Image.alpha_composite(bilde, lag)
            tegner = ImageDraw.Draw(bilde)
    return bilde


def apne(sti):
    """Les en fil fra pakka, uansett om den er PNG eller SVG."""
    if er_svg(sti):
        return tegn_svg(sti)
    return Image.open(sti).convert("RGBA")


def pakk(bilder):
    """Enkel hyllepakking: høyest først, ny hylle når raden er full.

    Returnerer (bredde, høyde, {navn: (x, y, w, h)}). Atlaset blir ikke
    minst mulig, men det blir lite nok — det største rommet har førti
    sprites på noen hundre piksler.
    """
    etter_hoyde = sorted(bilder.items(), key=lambda kv: -kv[1].height)
    # Bredde nær kvadratrota av arealet gir et nokså kvadratisk atlas.
    areal = sum((b.width + LUFT) * (b.height + LUFT) for b in bilder.values())
    bredde = max(int(areal ** 0.5) + 1, max(b.width for b in bilder.values()))

    rammer = {}
    x = y = hylle = 0
    for navn, bilde in etter_hoyde:
        if x and x + bilde.width > bredde:
            x = 0
            y += hylle + LUFT
            hylle = 0
        rammer[navn] = (x, y, bilde.width, bilde.height)
        x += bilde.width + LUFT
        hylle = max(hylle, bilde.height)
    return bredde, y + hylle, rammer


def krymp(bilde):
    """Slank bildet uten å endre et eneste piksel.

    Kvantisering til palett ville spart mer, men pikselkunst med myke
    skygger tåler det dårlig, og her er det kunsten som er poenget. Det
    eneste som gjøres er å droppe alfakanalen når den er ubrukt — det
    er tapsfritt og tar en firedel av de rå bytene.
    """
    if bilde.mode != "RGBA":
        bilde = bilde.convert("RGBA")
    alfa = bilde.getchannel("A")
    if alfa.getextrema()[0] == 255:
        return bilde.convert("RGB")
    return bilde


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True,
                    help="den utpakkede handoff-mappa "
                         "(den med assets/ og data/ i seg)")
    ap.add_argument("--behold", action="store_true",
                    help="ikke tøm web/maps først")
    args = ap.parse_args()

    kilde = os.path.abspath(args.src)
    data_fil = os.path.join(kilde, "data", "sbtc-scenario.json")
    if not os.path.exists(data_fil):
        sys.exit("Fant ikke data/sbtc-scenario.json under " + kilde)
    with open(data_fil, encoding="utf-8") as f:
        inn = json.load(f)

    if not args.behold and os.path.isdir(UT_BILDER):
        shutil.rmtree(UT_BILDER)
    os.makedirs(UT_BILDER, exist_ok=True)

    ut = collections.OrderedDict()
    ut["schema"] = "eldritch-battlemaps/1"
    ut["scenario"] = inn.get("scenario", "")
    ut["ship"] = inn.get("ship", "")
    ut["units"] = inn["units"]
    ut["groups"] = inn["groups"]
    ut["rooms"] = []

    bytes_bg = bytes_atlas = 0
    for rom in sorted(inn["rooms"], key=lambda r: r["no"]):
        mappe = "%s-%s" % (rom["no"], rom["id"])
        fra = os.path.join(kilde, "assets", mappe)
        til = os.path.join(UT_BILDER, mappe)
        os.makedirs(til, exist_ok=True)

        bg_fra = os.path.join(fra, "background.png")
        if not os.path.exists(bg_fra):
            sys.exit("Mangler bakgrunn for " + mappe)
        bg = krymp(apne(bg_fra))
        bg_til = os.path.join(til, "bg.png")
        bg.save(bg_til, optimize=True)
        bytes_bg += os.path.getsize(bg_til)

        # Bare de spritene rommet faktisk bruker. Flere items kan dele
        # én sprite, og da skal den ligge én gang i atlaset.
        navn = sorted({i["sprite"] for i in rom["items"]})
        bilder = collections.OrderedDict()
        for n in navn:
            sti = os.path.join(fra, "sprites", n + ".png")
            if not os.path.exists(sti):
                sys.exit("Mangler sprite %s i %s" % (n, mappe))
            bilder[n] = apne(sti)

        bredde, hoyde, rammer = pakk(bilder)
        atlas = Image.new("RGBA", (bredde, hoyde), (0, 0, 0, 0))
        for n, (x, y, w, h) in rammer.items():
            atlas.paste(bilder[n], (x, y))
        atlas_til = os.path.join(til, "sprites.png")
        krymp(atlas).save(atlas_til, optimize=True)
        bytes_atlas += os.path.getsize(atlas_til)

        r = collections.OrderedDict()
        for k in ("id", "no", "group", "title", "scene", "note",
                  "widthPx", "heightPx", "widthFt", "heightFt"):
            if k in rom:
                r[k] = rom[k]
        r["dir"] = mappe
        r["atlasW"] = bredde
        r["atlasH"] = hoyde
        # [x, y, w, h] er kortere enn et objekt, og det er 516 av dem.
        r["frames"] = collections.OrderedDict(
            (n, list(rammer[n])) for n in navn)
        r["items"] = rom["items"]
        r["clues"] = inn["clues"].get(rom["id"], [])
        ut["rooms"].append(r)

    with open(UT_JSON, "w", encoding="utf-8") as f:
        json.dump(ut, f, ensure_ascii=False, indent=1)
        f.write("\n")

    spor = sum(len(r["clues"]) for r in ut["rooms"])
    props = sum(len(r["items"]) for r in ut["rooms"])
    filer = len(ut["rooms"]) * 2
    print("%d rom, %d props, %d spor" % (len(ut["rooms"]), props, spor))
    print("%d bildefiler: %.1f MB bakgrunn + %.1f MB atlas"
          % (filer, bytes_bg / 1e6, bytes_atlas / 1e6))
    print("%s er %.0f kB" % (os.path.relpath(UT_JSON, REPO),
                             os.path.getsize(UT_JSON) / 1e3))


if __name__ == "__main__":
    main()
