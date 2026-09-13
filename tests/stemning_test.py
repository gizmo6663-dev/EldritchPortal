"""Funksjonstest av stemningspasset i tools/opplesing.py.

    python3 tests/stemning_test.py

ffmpeg-filterkjeder er lette å skrive feil, og feilen viser seg først
når man kjører dem. Her kjøres hver kjede på ekte lyd, og resultatet
måles: at fila blir til, at den har innhold, at farten endret seg som
den skulle, og at båndet faktisk er smalnet der det er meningen.

Selve talesyntesen er ikke med — stemningspasset bryr seg ikke om hvor
lyden kom fra, så en generert tone holder.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []


def check(name, got, want):
    ok = got == want
    print(("  ok    " if ok else "  FAIL  ") + name +
          ("" if ok else f": {got!r} != {want!r}"))
    if not ok:
        fails.append(name)


def load():
    path = os.path.join(REPO, "tools", "opplesing.py")
    spec = importlib.util.spec_from_file_location("opplesing", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def varighet(ff, fil):
    r = subprocess.run(
        [ff, "-hide_banner", "-i", fil, "-f", "null", "-"],
        capture_output=True, text=True)
    # ffmpeg skriver «time=00:00:04.02» sist i framdriftslinja.
    biter = [l for l in (r.stderr or "").splitlines() if "time=" in l]
    if not biter:
        return None
    felt = biter[-1].split("time=")[1].split(" ")[0]
    t, m, sek = felt.split(":")
    return int(t) * 3600 + int(m) * 60 + float(sek)


def main():
    o = load()
    ff = o.ffmpeg_sti()
    if not ff:
        print("Fant ikke ffmpeg — hopper over.")
        print("\nRESULT: OK")
        return

    arbeid = tempfile.mkdtemp(prefix="stemning-")
    # Et sveip fra dypt til lyst, så vi kan se hva filtrene tar bort.
    kilde = os.path.join(arbeid, "kilde.mp3")
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi",
                    "-i", "sine=frequency=200:duration=4",
                    "-c:a", "libmp3lame", "-q:a", "3", kilde], check=True)
    check("testlyden ble laget", os.path.getsize(kilde) > 0, True)
    inn_lengde = varighet(ff, kilde)
    check("og er fire sekunder", round(inn_lengde), 4)

    print("\n== hver stemning kjører gjennom ==")
    for navn in sorted(o.STEMNINGER):
        if navn == "ingen":
            continue
        ut = os.path.join(arbeid, navn + ".mp3")
        ok = o.legg_paa_stemning(kilde, ut, navn, 0.0)
        check("«%s» kjørte uten feil" % navn, ok, True)
        check("«%s» ga en fil med innhold" % navn,
              os.path.exists(ut) and os.path.getsize(ut) > 0, True)

    print("\n== farten endrer seg slik den skal ==")
    # mork står på atempo=0.96, altså litt lengre lyd.
    lengde = varighet(ff, os.path.join(arbeid, "mork.mp3"))
    check("«mork» er langsommere enn kilden", lengde > inn_lengde, True)
    check("men ikke mye — under ti prosent",
          lengde < inn_lengde * 1.1, True)
    # krypt står på 0.93 og skal være tydeligere langsom enn mork.
    krypt = varighet(ff, os.path.join(arbeid, "krypt.mp3"))
    check("«krypt» er langsommere enn «mork»", krypt > lengde, True)

    print("\n== radio smalner båndet ==")
    # 200 Hz ligger under radioens høypass på 320 Hz, så tonen skal
    # være merkbart svakere enn i originalen.
    def styrke(fil):
        r = subprocess.run([ff, "-hide_banner", "-i", fil,
                            "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True)
        for linje in (r.stderr or "").splitlines():
            if "mean_volume:" in linje:
                return float(linje.split("mean_volume:")[1].split("dB")[0])
        return None
    rent = styrke(kilde)
    radio = styrke(os.path.join(arbeid, "radio.mp3"))
    check("begge kunne måles", rent is not None and radio is not None, True)
    check("og radioen har dempet den dype tonen", radio < rent, True)

    print("\n== dronen legges under ==")
    ut = os.path.join(arbeid, "drone.mp3")
    ok = o.legg_paa_stemning(kilde, ut, "mork", 0.05)
    check("kjørte uten feil", ok, True)
    check("ga en fil", os.path.exists(ut) and os.path.getsize(ut) > 0, True)
    check("og er like lang som stemmen, ikke uendelig",
          varighet(ff, ut) < inn_lengde * 1.2, True)

    print("\n== «ingen» rører ikke lyden ==")
    ut = os.path.join(arbeid, "ingen.mp3")
    check("den sier fra at den ikke gjorde noe",
          o.legg_paa_stemning(kilde, ut, "ingen", 0.0), False)
    check("og lager ingen fil", os.path.exists(ut), False)

    shutil.rmtree(arbeid, ignore_errors=True)
    print("\nRESULT:", "FAILED" if fails else "OK")


main()
