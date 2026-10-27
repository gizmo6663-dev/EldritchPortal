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

Bildene skrives som WebP uten tap. Den nye kunsten har korn og
fargegradering, og det komprimerer dårlig som PNG — WebP tar en tredel
av vekten uten å endre et eneste piksel man kan se. Hver fil leses
tilbake og sammenlignes før den godtas; går det ikke opp, skrives PNG
i stedet.

Hver gjenstand får også en høyde (h, i rompiksler), og hvert rom får
lysdataene sine fra bestiary/lys_rom.json: vinduer, innervegger,
rekker og hvor nødlampene henger. Det er det lysmotoren i appen
trenger for å kaste skygger. Høydene og lysdataene kan legges på
alene, uten handoff-pakka:

    python3 scenarios/build_maps.py --bare-lys

Ut:
    bestiary/battlemaps.json
    web/maps/<no>-<id>/bg.webp
    web/maps/<no>-<id>/sprites.webp
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
LYS_JSON = os.path.join(REPO, "bestiary", "lys_rom.json")

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
    """Dropp alfakanalen når den er ubrukt. Tapsfritt."""
    if bilde.mode != "RGBA":
        bilde = bilde.convert("RGBA")
    alfa = bilde.getchannel("A")
    if alfa.getextrema()[0] == 255:
        return bilde.convert("RGB")
    return bilde


def likt_der_det_synes(a, b):
    """Er to bilder like overalt der man kan se forskjell?

    WebP uten tap kaster fargen under piksler som er helt
    gjennomsiktige. Den fargen kan ikke ses, så en forskjell der er
    ikke en forskjell.
    """
    if a.size != b.size:
        return False
    pa, pb = a.convert("RGBA").load(), b.convert("RGBA").load()
    for y in range(a.height):
        for x in range(a.width):
            va, vb = pa[x, y], pb[x, y]
            if va == vb:
                continue
            if va[3] == 0 and vb[3] == 0:
                continue
            return False
    return True


def skriv(bilde, mappe, stamme):
    """Skriv som WebP uten tap, med PNG som fallback.

    Returnerer filnavnet som faktisk ble skrevet, så JSON-en kan peke
    på det i stedet for at appen gjetter endelsen.
    """
    bilde = krymp(bilde)
    webp = os.path.join(mappe, stamme + ".webp")
    bilde.save(webp, "WEBP", lossless=True, quality=100, method=5)
    try:
        tilbake = Image.open(webp)
        tilbake.load()
        if likt_der_det_synes(bilde, tilbake):
            return stamme + ".webp", os.path.getsize(webp)
    except Exception:
        pass
    # Kom den ikke hel tilbake, er den ikke verdt å spare på.
    os.remove(webp)
    png = os.path.join(mappe, stamme + ".png")
    bilde.save(png, optimize=True)
    print("  %s: WebP gikk ikke, skrev PNG" % stamme)
    return stamme + ".png", os.path.getsize(png)


# ------------------------------------------------------------------
# Høyder. Lysmotoren kaster skygger fra gjenstandene, og hvor lang
# skyggen blir avhenger av hvor høy tingen er. Kunsten har ingen
# høyder, så de gjettes fra navnet: 16 piksler er én fot, så en stol
# er 44 og et skap 96. Ting som ligger på gulvet (z under 7) eller
# står oppå noe annet (z 15 og over) kaster ingen egen skygge.
# ------------------------------------------------------------------

# Navngitte unntak, som sjekkes før alt annet. Det er her gjettingen
# gikk galt første gang: «Hudson touring» traff «ring» (livbøye) og
# fikk en halv fot, og «Pianokrakk» traff «piano».
HOYDE_FORST = [
    (r"hudson|touring|packard|sedan|traktor", 60), (r"bugatti", 48),
    (r"lastebom|veggmaleri|frakk på knagg|flaggstang|høygaffel|rotte|"
     r"shuffleboard|spillbrett|tanklokk|speil|lykt|kokebål|bålrester", 0),
    (r"pianokrakk", 44), (r"ventilratt", 40), (r"arbeidsbenk", 40),
    (r"maskintelegraf", 48), (r"vitenskapelige", 56), (r"haglgevær", 40),
    (r"talerør", 40), (r"appelsin|epler|sitron", 40), (r"høyball", 40),
    (r"tralle", 40), (r"skjenk", 44), (r"harpe", 64), (r"globus", 44),
    (r"hengende kjøtt", 72), (r"kokekar", 24), (r"kontrollpanel", 56),
    (r"leirduekaster", 30), (r"medisinsk", 44), (r"skrot", 20),
    (r"trillebår", 28), (r"vaktpost", 64), (r"vanntrau", 24),
    (r"vievann", 40), (r"funeral", 40), (r"stewarduniform", 56),
    (r"portrett", 56), (r"blomster \(", 30),
    # Ord i HOYDE_FLATE som også står inne i navnet på noe høyt:
    # «lamp» i floorlamp, «oil» i toilet, «aske» i vaskeservant,
    # «note» i noteskap, «glass» i glassballonger.
    (r"gulvlampe", 80), (r"skrivebord", 44), (r"koffert", 24),
    (r"toalett", 26), (r"servant", 44), (r"kartbord", 28),
    (r"noteskap", 96), (r"notestativ", 40), (r"orkesterstoler", 44),
    (r"papirkurv", 18), (r"glassballong", 40), (r"kasser med", 48),
    (r"pipes of leng", 48), (r"knefall", 20), (r"dieselmanifold", 40),
]

HOYDE_FLATE = re.compile(
    r"dør|door|skilt|\blab|sign|teppe|matte|rug|avis|papir|brev|flekk|"
    r"blod|søl|oil|strø|straw|tau|rope|kjetting|chain|presenning|tarp|"
    r"pall|pallet|\blik\b|body|skinn|pelt|skrue|leider|ladder|hengelås|"
    r"padlock|kart|map|spor|trail|pool|luke|hatch|rist|grate|kakerlakk|"
    r"roach|swarm|sverm|lys|lamp(?!e)|shroud|klut|håndkle|towel|note|"
    r"lapp|sko|shoe|tøfler|slipper|bok|book|glass|kopp|cup|flaske|"
    r"bottle|karaffel|decanter|pipe|sigar|aske(?!beger)|dress|suit", re.I)

# Ting som ligger lavt, men likevel står i veien for lyset.
HOYDE_SOLIDE = [
    (r"oljefat|drum", 46), (r"løs kasse|smallcrate", 30),
    (r"sekk|sack", 20), (r"verktøykasse|toolbox", 16),
    (r"bøtte|bucket", 20),
]

HOYDE_TABELL = [
    (r"skap|garderobe|wardrobe|kabinett|cabinet|hylle|shelf|reol", 96),
    (r"gulvlampe|floorlamp|stålampe", 80),
    (r"orgel|organ|piano|flygel", 64), (r"statue", 72),
    (r"palme|palm|plante|plant", 64), (r"bagasje|luggage", 64),
    (r"våpenstativ|våpenskap|guns|arms|gevær", 80),
    (r"maskin|motor|kjele|boiler|turbin|dynamo", 96),
    (r"pumpe|pump", 48), (r"maleri|paint", 56),
    (r"bar\b|disk|counter", 48), (r"lenestol|armchair", 46),
    (r"stol|chair|benk|bench|krakk|stool", 44),
    (r"sofa|settee|divan", 42), (r"servant|sink", 44),
    (r"askebeger|ashtray", 40),
    (r"skrivebord|desk|pult|alter|altar|prekestol|lectern|talerstol", 44),
    (r"nattbord|nightstand", 36),
    (r"dampkoffert|trunk|kiste|chest|greenbox", 36),
    (r"seng|bed|køye|bunk|hengekøye", 30), (r"badekar|tub", 30),
    (r"ovn|radiator|komfyr|stove|peis|fire", 32),
    (r"bord|table", 28), (r"koffert|suitcase|veske|bag", 24),
    (r"toalett|toilet", 26), (r"kurv|waste|basket", 18),
    (r"hatteske|hatbox|eske|box", 20), (r"kasse|crate|kasser", 48),
    (r"fat|tønne|barrel|keg", 48), (r"vin|wine", 44),
    (r"instrument|kontrabass|cello|tromme|drum kit", 48),
    (r"urne|urns|vase", 30), (r"ballong|carboy", 40),
    (r"plank|redwood|tømmer", 22),
    (r"bil\b|car\b|automobil|limousin", 56),
    (r"hest|horse|ku\b|cow|okse|bur|cage|binge|pen\b|kyr", 60),
    (r"vinsj|winch|ankerspill|windlass|spill\b|capstan|pullert|bollard|"
     r"bitt", 36),
    (r"livbåt|lifeboat|båt|boat", 64),
    (r"ventil|vent|luftrør|cowl|ventilator", 60),
    (r"mast|kran|crane|bom\b|boom", 96),
    (r"rorhjul|ratt|wheel|kompass|binnacle|telegraf", 48),
    (r"klokke|bell|klokka", 40), (r"livbøye|lifebuoy|ring", 8),
    (r"trapp|stair|rekke|rail|rekkverk", 0),
]

# Det som ikke treffer noe, får en vanlig møbelhøyde.
HOYDE_STANDARD = 28


def hoyde(item):
    """Hvor høy gjenstanden er, i rompiksler."""
    n = ((item.get("name") or "") + " " + (item.get("sprite") or "")).lower()
    z = item.get("z") or 0
    if z >= 15:
        return 0
    for monster, h in HOYDE_FORST:
        if re.search(monster, n):
            return h
    for monster, h in HOYDE_SOLIDE:
        if re.search(monster, n):
            return h
    if HOYDE_FLATE.search(n) or z <= 6:
        return 0
    for monster, h in HOYDE_TABELL:
        if re.search(monster, n):
            return h
    return HOYDE_STANDARD


# ------------------------------------------------------------------
# Havet. Uterommene har sjø langs kanten, og appen lar den glitre og
# sprute. Hvor havet er, finnes fra bakgrunnen: blått som henger sammen
# med kanten av bildet. Blågrått stål midt på dekket — lukerammer,
# bølgebrytere — henger ikke sammen med kanten, og et vindu som så vidt
# rører kanten er for lite til å telle.
# ------------------------------------------------------------------

HAV_CELLE = 4          # piksler per celle i masken
HAV_MINSTE = 3000      # piksler; mindre blått mot kanten er ikke hav


def er_hav(p):
    r, g, b = p[:3]
    return b > r + 15 and b > g - 5


def finn_hav(bilde):
    """Havet som rader av celler: [[y, x0, x1], ...], x1 eksklusiv."""
    bilde = bilde.convert("RGB")
    W, H = bilde.size
    px = bilde.load()
    blatt = [bytearray(1 if er_hav(px[x, y]) else 0 for x in range(W))
             for y in range(H)]
    hav = [bytearray(W) for _ in range(H)]
    kant = [(x, y) for x in range(W) for y in (0, H - 1)] + \
           [(x, y) for y in range(H) for x in (0, W - 1)]
    for sx, sy in kant:
        if not blatt[sy][sx] or hav[sy][sx]:
            continue
        # Fyll denne flekken, og behold den bare hvis den er stor nok.
        flekk = [(sx, sy)]
        hav[sy][sx] = 2
        i = 0
        while i < len(flekk):
            x, y = flekk[i]
            i += 1
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < W and 0 <= ny < H and blatt[ny][nx] and not hav[ny][nx]:
                    hav[ny][nx] = 2
                    flekk.append((nx, ny))
        verdi = 1 if len(flekk) >= HAV_MINSTE else 3
        for x, y in flekk:
            hav[y][x] = verdi
    rader = []
    c = HAV_CELLE
    for cy in range(H // c):
        start = None
        for cx in range(W // c + 1):
            fullt = False
            if cx < W // c:
                n = sum(1 for y in range(cy * c, cy * c + c)
                        for x in range(cx * c, cx * c + c) if hav[y][x] == 1)
                fullt = n >= c * c * 3 // 4
            if fullt and start is None:
                start = cx
            elif not fullt and start is not None:
                rader.append([cy, start, cx])
                start = None
    return rader


def legg_paa_lys(ut):
    """Høyder på gjenstandene og lysdataene på rommene."""
    with open(LYS_JSON, encoding="utf-8") as f:
        lys = json.load(f)
    ut["lys"] = lys.get("proplys", [])
    ukjente = set(lys.get("rom", {})) - {r["id"] for r in ut["rooms"]}
    if ukjente:
        sys.exit("lys_rom.json nevner rom som ikke finnes: " +
                 ", ".join(sorted(ukjente)))
    for r in ut["rooms"]:
        for item in r["items"]:
            h = hoyde(item)
            if h:
                item["h"] = h
            else:
                item.pop("h", None)
        r["lys"] = dict(lys.get("rom", {}).get(r["id"], {}))
        if r["lys"].get("ute") or r["lys"].get("rekker"):
            bg = os.path.join(UT_BILDER, r["dir"], r["bg"])
            rader = finn_hav(Image.open(bg))
            if rader:
                r["lys"]["hav"] = {"celle": HAV_CELLE, "rader": rader}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src",
                    help="den utpakkede handoff-mappa "
                         "(den med assets/ og data/ i seg)")
    ap.add_argument("--behold", action="store_true",
                    help="ikke tøm web/maps først")
    ap.add_argument("--bare-lys", action="store_true",
                    help="legg bare høyder og lysdata på den eksisterende "
                         "battlemaps.json")
    args = ap.parse_args()

    if args.bare_lys:
        with open(UT_JSON, encoding="utf-8") as f:
            ut = json.load(f, object_pairs_hook=collections.OrderedDict)
        legg_paa_lys(ut)
        with open(UT_JSON, "w", encoding="utf-8") as f:
            json.dump(ut, f, ensure_ascii=False, indent=1)
            f.write("\n")
        hoyder = sum(1 for r in ut["rooms"] for i in r["items"] if i.get("h"))
        print("%d gjenstander har høyde, %d rom har lysdata"
              % (hoyder, sum(1 for r in ut["rooms"] if r["lys"])))
        return
    if not args.src:
        ap.error("--src trengs, med mindre det er --bare-lys")

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
        bg_navn, bg_vekt = skriv(apne(bg_fra), til, "bg")
        bytes_bg += bg_vekt

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
        atlas_navn, atlas_vekt = skriv(atlas, til, "sprites")
        bytes_atlas += atlas_vekt

        r = collections.OrderedDict()
        for k in ("id", "no", "group", "title", "scene", "note",
                  "widthPx", "heightPx", "widthFt", "heightFt"):
            if k in rom:
                r[k] = rom[k]
        r["dir"] = mappe
        r["bg"] = bg_navn
        r["atlas"] = atlas_navn
        r["atlasW"] = bredde
        r["atlasH"] = hoyde
        # [x, y, w, h] er kortere enn et objekt, og det er 516 av dem.
        r["frames"] = collections.OrderedDict(
            (n, list(rammer[n])) for n in navn)
        r["items"] = rom["items"]
        r["clues"] = inn["clues"].get(rom["id"], [])
        ut["rooms"].append(r)

    legg_paa_lys(ut)
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
