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

    print("Skrev " + ut)
    if args.spill:
        spill(ut)


if __name__ == "__main__":
    main()
