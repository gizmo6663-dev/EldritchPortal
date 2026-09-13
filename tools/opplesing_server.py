#!/usr/bin/env python3
"""Serverer nettleserversjonen med edge-tts bak seg.

    python3 tools/opplesing_server.py
    # åpne http://127.0.0.1:8765 i nettleseren

Nettleserens egen talesyntese bruker stemmene som ligger på maskinen,
og de er ikke i nærheten av de nevrale stemmene til edge-tts. Men en
nettside kan ikke snakke med Termux av seg selv.

Løsningen er at Termux serverer sida. Da ligger appen og talesyntesen
på samme sted, og «Les opp» kan be om ordentlig lyd i stedet for å
lage den selv.

I Termux:
    pkg install python
    pip install edge-tts
    python3 tools/opplesing_server.py

Standard er at bare denne maskinen slipper til. Skal telefonen servere
til en annen skjerm i samme nett, bruk --alle — men da er den åpen for
alle på nettet, så gjør det bare på et nett du stoler på.
"""
import argparse
import asyncio
import hashlib
import http.server
import json
import os
import posixpath
import socketserver
import sys
import urllib.parse

try:
    import edge_tts
except ImportError:                                   # pragma: no cover
    edge_tts = None

STEMME = "nb-NO-PernilleNeural"
TEMPO = "-8%"
DYBDE = "+0Hz"
LYDSTYRKE = "+0%"

# Lang nok til en hel økt, kort nok til at ingen kan be om en roman.
MAKS_TEGN = 20000

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(REPO, "web")

_stemmer_cache = []


def norske_stemmer():
    """De norske stemmene tjenesten har. Hentes én gang."""
    global _stemmer_cache
    if _stemmer_cache:
        return _stemmer_cache
    if edge_tts is None:
        return []
    alle = asyncio.run(edge_tts.list_voices())
    norske = [v for v in alle
              if str(v.get("Locale", "")).lower().startswith(("nb-", "nn-"))]
    norske.sort(key=lambda v: (v.get("Gender") != "Female", v.get("ShortName")))
    _stemmer_cache = [{
        "id": v.get("ShortName"),
        "navn": v.get("FriendlyName") or v.get("ShortName"),
        "kjonn": "kvinne" if v.get("Gender") == "Female" else "mann",
        "sprak": v.get("Locale"),
    } for v in norske]
    return _stemmer_cache


def lag_lyd(tekst, stemme, tempo, dybde, lydstyrke):
    async def kjor():
        c = edge_tts.Communicate(tekst, stemme, rate=tempo, pitch=dybde,
                                 volume=lydstyrke)
        biter = []
        async for del_ in c.stream():
            if del_["type"] == "audio":
                biter.append(del_["data"])
        return b"".join(biter)
    return asyncio.run(kjor())


class Handler(http.server.SimpleHTTPRequestHandler):
    cache_dir = None
    root = WEB

    def log_message(self, fmt, *args):
        # Én linje per forespørsel er nok; standarden skriver tre.
        sys.stderr.write("%s %s\n" % (self.command, self.path.split("?")[0]))

    # --- felles -----------------------------------------------------
    def _send(self, code, body, mime, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        # Så sida virker også om den åpnes fra en annen adresse.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, data):
        self._send(code, json.dumps(data).encode("utf-8"),
                   "application/json; charset=utf-8")

    def translate_path(self, path):
        # Alt som ikke er /tts serveres fra web/, ikke fra der man
        # tilfeldigvis startet skriptet.
        path = urllib.parse.urlparse(path).path
        path = posixpath.normpath(urllib.parse.unquote(path))
        biter = [b for b in path.split("/") if b and b not in (os.curdir, os.pardir)]
        return os.path.join(self.root, *biter)

    # --- ruter ------------------------------------------------------
    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    def do_GET(self):
        rute = urllib.parse.urlparse(self.path).path
        if rute == "/tts/stemmer":
            if edge_tts is None:
                self._json(503, {"feil": "edge-tts er ikke installert"})
                return
            try:
                self._json(200, {"stemmer": norske_stemmer(),
                                 "standard": STEMME})
            except Exception as e:
                self._json(502, {"feil": "fikk ikke kontakt: %s" % e})
            return
        if rute == "/":
            self.path = "/index.html"
        http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/tts":
            self._json(404, {"feil": "ukjent rute"})
            return
        if edge_tts is None:
            self._json(503, {"feil": "edge-tts er ikke installert. "
                                     "pip install edge-tts"})
            return
        try:
            lengde = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            lengde = 0
        if lengde <= 0 or lengde > MAKS_TEGN * 4:
            self._json(413, {"feil": "for mye tekst"})
            return
        try:
            data = json.loads(self.rfile.read(lengde).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._json(400, {"feil": "ugyldig JSON"})
            return

        tekst = str(data.get("tekst") or "").strip()[:MAKS_TEGN]
        if not tekst:
            self._json(400, {"feil": "ingen tekst"})
            return
        stemme = str(data.get("stemme") or STEMME)
        tempo = str(data.get("tempo") or TEMPO)
        dybde = str(data.get("dybde") or DYBDE)
        lydstyrke = str(data.get("lydstyrke") or LYDSTYRKE)

        # Samme tekst med samme innstillinger gir samme lyd. Å lage den
        # på nytt hver gang man trykker spill er bare venting.
        nokkel = hashlib.sha256(
            "\x00".join([tekst, stemme, tempo, dybde, lydstyrke])
            .encode("utf-8")).hexdigest()
        fil = os.path.join(self.cache_dir, nokkel + ".mp3")
        if os.path.exists(fil):
            with open(fil, "rb") as f:
                lyd = f.read()
        else:
            try:
                lyd = lag_lyd(tekst, stemme, tempo, dybde, lydstyrke)
            except Exception as e:
                self._json(502, {"feil": "edge-tts feilet: %s" % e})
                return
            if not lyd:
                self._json(502, {"feil": "edge-tts ga ingen lyd. Finnes "
                                         "stemmen «%s»?" % stemme})
                return
            with open(fil, "wb") as f:
                f.write(lyd)
        self._send(200, lyd, "audio/mpeg",
                   {"Content-Disposition": 'inline; filename="opplesing.mp3"'})


def aapne(url):
    """Termux har sin egen måte å åpne en lenke på."""
    import shutil
    import subprocess
    if shutil.which("termux-open-url"):
        subprocess.run(["termux-open-url", url], check=False)
        return
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(
        description="Serverer nettleserversjonen med edge-tts bak seg.")
    ap.add_argument("-p", "--port", type=int, default=8765)
    ap.add_argument("--alle", action="store_true",
                    help="slipp til andre maskiner i samme nett. Bare på "
                         "et nett du stoler på — endepunktet er åpent.")
    ap.add_argument("--mappe", default=WEB,
                    help="hvor index.html ligger (standard: web/)")
    ap.add_argument("--cache", default=None,
                    help="hvor de ferdige lydfilene mellomlagres")
    ap.add_argument("--apne", action="store_true",
                    help="åpne appen i nettleseren med én gang")
    args = ap.parse_args()

    if edge_tts is None:
        print("Merk: edge-tts er ikke installert, så opplesingen vil svare "
              "med feil.\n      pip install edge-tts")

    cache = args.cache or os.path.join(
        os.environ.get("TMPDIR") or "/tmp", "eldritch-tts")
    os.makedirs(cache, exist_ok=True)
    Handler.cache_dir = cache
    Handler.root = os.path.abspath(args.mappe)

    vert = "0.0.0.0" if args.alle else "127.0.0.1"
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((vert, args.port), Handler) as srv:
        print("Appen kjører på http://%s:%d" %
              ("127.0.0.1" if not args.alle else vert, args.port))
        print("Lydfiler mellomlagres i " + cache)
        print("Ctrl-C for å stoppe.")
        if args.apne:
            aapne("http://127.0.0.1:%d/" % args.port)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nStoppet.")


if __name__ == "__main__":
    main()
