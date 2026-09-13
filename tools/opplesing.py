#!/usr/bin/env python3
"""Leser en eksportert spilløkt opp med edge-tts.

    python3 tools/opplesing.py sesjon-1.md
    python3 tools/opplesing.py sesjon-1.md --spill
    python3 tools/opplesing.py --stemmer

Eksporten fra appen er markdown, og markdown leses ikke godt opp:
stjerner blir «stjerne», datoer blir sifre på rad, og overskrifter
renner sammen med avsnittet under. Derfor vaskes teksten først, og så
sendes den til edge-tts.

Stemmen er Pernille, satt litt langsommere enn normalt. Roen skal komme
av tempoet og av teksten, ikke av å skru tonehøyden ned — det siste gir
bare metallisk klang. Alt kan overstyres med flagg; mannsstemmen heter
nb-NO-FinnNeural.

Krever nett: edge-tts snakker med Microsofts tjeneste. Den er gratis og
uten nøkkel, men den er ikke lokal.

I Termux:
    pkg install python ffmpeg
    pip install edge-tts
    python3 tools/opplesing.py ~/storage/downloads/sesjon-1.md --spill
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

# Pernille er den norske stemmen som holder best. Finn er
# mannsstemmen — bytt med -v nb-NO-FinnNeural.
STEMME = "nb-NO-PernilleNeural"

# Roen kommer av tempoet. Å skyve tonehøyden ned gir metallisk klang
# og grøtete konsonanter på en nevral stemme, så dybden står på null.
TEMPO = "-8%"
DYBDE = "+0Hz"
LYDSTYRKE = "+0%"

# ------------------------------------------------------------------
# STEMNING
#
# Talesyntesen har knapper for fart og tonehøyde, og det er omtrent
# alt. Det som faktisk gjør en opplesning alvorlig og uhyggelig er hva
# som skjer etterpå: et rom rundt stemmen, litt varme nedi, toppen
# dempet, og et jevnt trykk så den ikke spretter.
#
# Det gjøres med ffmpeg, og det virker på hvilken som helst stemme —
# edge-tts, Piper, eller et opptak av deg selv.
#
# atempo endrer farten uten å røre tonehøyden. Det er med vilje:
# asetrate ville senket tonehøyden også, og det er nettopp det som gir
# den metalliske klangen vi ikke vil ha.
# ------------------------------------------------------------------
STEMNINGER = {
    "ingen": [],
    # Rolig og alvorlig. Et lite rom, varme i bunnen, dempet topp.
    "mork": [
        "atempo=0.96",
        "highpass=f=70",
        "equalizer=f=180:t=q:w=1.2:g=2.5",
        "equalizer=f=3200:t=q:w=1.5:g=-2",
        "lowpass=f=7600",
        "aecho=0.85:0.8:38|64:0.16|0.09",
        "acompressor=threshold=-18dB:ratio=3:attack=8:release=280",
    ],
    # Større rom. Som å bli fortalt noe i en kjeller under vannlinja.
    "krypt": [
        "atempo=0.93",
        "highpass=f=60",
        "asubboost=dry=0.9:wet=0.35:decay=0.6",
        "equalizer=f=2600:t=q:w=1.5:g=-3",
        "lowpass=f=6200",
        "aecho=0.8:0.88:110|210|370:0.32|0.2|0.11",
        "acompressor=threshold=-20dB:ratio=4:attack=6:release=320",
    ],
    # Trådløsen i røykesalongen, 1936. Smalt bånd og litt trykk.
    "radio": [
        "atempo=0.97",
        "highpass=f=320",
        "lowpass=f=3000",
        "equalizer=f=1400:t=q:w=1.2:g=3",
        "acompressor=threshold=-24dB:ratio=6:attack=4:release=180",
        "aecho=0.9:0.6:18:0.12",
    ],
}

# En lav tone under stemmen. Den høres nesten ikke, men den merkes.
DRONE_HZ = 55

MAANEDER = ["januar", "februar", "mars", "april", "mai", "juni", "juli",
            "august", "september", "oktober", "november", "desember"]


def spoken_date(m):
    """2026-09-13 blir «13. september 2026», ikke fire sifre og to."""
    aar, maaned, dag = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= maaned <= 12:
        return m.group(0)
    return "%d. %s %d" % (dag, MAANEDER[maaned - 1], aar)


def vask(md):
    """Markdown til noe som kan leses høyt."""
    ut = []
    for linje in md.splitlines():
        s = linje.rstrip()

        # Vannrette streker er et taktskifte, ikke et ord.
        if re.match(r"^\s*([-*_])\s*\1\s*\1[\s\-*_]*$", s):
            ut.append("")
            ut.append("…")
            continue

        # Overskrifter skal ende i punktum, ellers renner de sammen
        # med avsnittet under.
        h = re.match(r"^\s*#{1,6}\s+(.*)$", s)
        if h:
            tittel = h.group(1).strip()
            ut.append("")
            ut.append(tittel if tittel.endswith((".", "!", "?", ":"))
                      else tittel + ".")
            continue

        s = re.sub(r"^\s*>\s?", "", s)              # sitatstrek
        s = re.sub(r"^\s*[-*+]\s+", "", s)          # kulepunkt
        s = re.sub(r"^\s*\d+[.)]\s+", "", s)        # nummerert liste

        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)  # bilder
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)   # lenker
        s = re.sub(r"`([^`]*)`", r"\1", s)               # kode
        s = re.sub(r"(\*\*\*|\*\*|\*|___|__|_)", "", s)  # utheving

        # Et klokkeslett på starten av linja er et tidspunkt, og skal
        # høres slik ut.
        s = re.sub(r"^(\d{1,2}):(\d{2})\s*(?:[—–-]\s*)?",
                   lambda m: "Klokka %s %s. " % (m.group(1), m.group(2)), s)
        s = re.sub(r"(\d{4})-(\d{2})-(\d{2})", spoken_date, s)

        # Tankestreker leses ikke, men de er et pust.
        s = re.sub(r"\s+[—–]\s+", ", ", s)
        s = re.sub(r"[ \t]{2,}", " ", s).strip()

        if s and not s.endswith((".", "!", "?", ":", ",", "…")):
            s += "."
        ut.append(s)

    # Flere tomme linjer på rad gir ingenting ekstra.
    tekst = "\n".join(ut)
    tekst = re.sub(r"\n{3,}", "\n\n", tekst).strip()
    return tekst


def ffmpeg_sti():
    """ffmpeg fra stien, eller den pip-installerte om den finnes."""
    funnet = shutil.which("ffmpeg")
    if funnet:
        return funnet
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def legg_paa_stemning(inn, ut, stemning, drone):
    """Kjører lyden gjennom ffmpeg og legger på rommet."""
    ff = ffmpeg_sti()
    if not ff:
        print("Fant ikke ffmpeg, så stemningen ble hoppet over.\n"
              "  Termux: pkg install ffmpeg")
        return False
    kjede = list(STEMNINGER.get(stemning) or [])
    if not kjede and not drone:
        return False

    if drone:
        # Dronen skal vare like lenge som stemmen, så den klippes etter
        # den korteste av de to.
        filter_complex = (
            "[0:a]" + ",".join(kjede or ["anull"]) + "[tale];"
            "sine=frequency=%d:sample_rate=44100[bass];"
            "[bass]volume=%.3f[dronen];"
            "[tale][dronen]amix=inputs=2:duration=first:dropout_transition=0"
            ":normalize=0[ut]" % (DRONE_HZ, drone)
        )
        kommando = [ff, "-y", "-i", inn, "-filter_complex", filter_complex,
                    "-map", "[ut]", "-c:a", "libmp3lame", "-q:a", "3", ut]
    else:
        kommando = [ff, "-y", "-i", inn, "-af", ",".join(kjede),
                    "-c:a", "libmp3lame", "-q:a", "3", ut]

    r = subprocess.run(kommando, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg feilet, så lyden er uten stemning:\n" +
              (r.stderr or "").strip()[-400:])
        return False
    return True


def spill(fil):
    """Termux først, så det som måtte finnes på en vanlig maskin."""
    if shutil.which("termux-media-player"):
        subprocess.run(["termux-media-player", "play", fil], check=False)
        return True
    for spiller, flagg in (("mpv", ["--no-video"]), ("ffplay", ["-nodisp",
                                                                "-autoexit"]),
                           ("play", []), ("afplay", [])):
        if shutil.which(spiller):
            subprocess.run([spiller] + flagg + [fil], check=False)
            return True
    print("Fant ingen avspiller. Fila ligger her: " + fil)
    return False


def stemmer(edge):
    r = subprocess.run([edge, "--list-voices"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("Fikk ikke listet stemmer:\n" + (r.stderr or "").strip())
    norske = [l for l in r.stdout.splitlines() if re.search(r"n[bn]-NO", l)]
    print("\n".join(norske) if norske else
          "Ingen norske stemmer i lista. Hele lista: " + edge +
          " --list-voices")


def main():
    ap = argparse.ArgumentParser(
        description="Leser en eksportert spilløkt opp med edge-tts.")
    ap.add_argument("fil", nargs="?",
                    help="markdown- eller tekstfila fra appen. "
                         "Uten den leses teksten fra stdin.")
    ap.add_argument("-o", "--ut", help="hvor lydfila skal havne "
                                       "(standard: samme navn, .mp3)")
    ap.add_argument("-v", "--stemme", default=STEMME)
    ap.add_argument("--tempo", default=TEMPO,
                    help="edge-tts --rate, f.eks. -15%% eller +5%%")
    ap.add_argument("--dybde", default=DYBDE,
                    help="edge-tts --pitch, f.eks. -20Hz")
    ap.add_argument("--lydstyrke", default=LYDSTYRKE)
    ap.add_argument("--spill", action="store_true",
                    help="spill av med én gang den er ferdig")
    ap.add_argument("--tekst", action="store_true",
                    help="skriv ut den vaskede teksten og stopp — nyttig "
                         "for å se hva som faktisk blir lest")
    ap.add_argument("--stemmer", action="store_true",
                    help="list de norske stemmene tjenesten har")
    ap.add_argument("--stemning", default="ingen",
                    choices=sorted(STEMNINGER),
                    help="rom og klang lagt på etterpå med ffmpeg. "
                         "«mork» er rolig og alvorlig, «krypt» er et "
                         "større og våtere rom, «radio» er trådløsen "
                         "i røykesalongen.")
    ap.add_argument("--drone", type=float, default=0.0, metavar="STYRKE",
                    help="legg en lav tone under stemmen, f.eks. 0.04. "
                         "Den høres nesten ikke, men den merkes.")
    args = ap.parse_args()

    edge = shutil.which("edge-tts")
    if not edge and not args.tekst:
        sys.exit("Fant ikke edge-tts. Installer den med:  pip install edge-tts")

    if args.stemmer:
        stemmer(edge)
        return

    if args.fil:
        with open(args.fil, encoding="utf-8") as f:
            raa = f.read()
    else:
        raa = sys.stdin.read()

    tekst = vask(raa)
    if not tekst.strip():
        sys.exit("Ingenting å lese opp.")

    if args.tekst:
        print(tekst)
        return

    ut = args.ut
    if not ut:
        rot = os.path.splitext(args.fil)[0] if args.fil else "opplesing"
        ut = rot + ".mp3"

    # edge-tts tar teksten fra fil, så den slipper å gjennom skallet.
    tmp = ut + ".txt"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(tekst)
    try:
        kommando = [edge, "-f", tmp, "-v", args.stemme,
                    "--rate", args.tempo, "--pitch", args.dybde,
                    "--volume", args.lydstyrke, "--write-media", ut]
        r = subprocess.run(kommando)
        if r.returncode != 0:
            sys.exit("edge-tts feilet. Har du nett? Finnes stemmen "
                     "«%s»? Sjekk med --stemmer." % args.stemme)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

    if args.stemning != "ingen" or args.drone:
        raa = ut + ".raa.mp3"
        os.replace(ut, raa)
        try:
            if not legg_paa_stemning(raa, ut, args.stemning, args.drone):
                os.replace(raa, ut)      # gi tilbake den rene lyden
            else:
                os.remove(raa)
        except Exception:
            if os.path.exists(raa):
                os.replace(raa, ut)
            raise

    print("Skrev " + ut)
    if args.spill:
        spill(ut)


if __name__ == "__main__":
    main()
