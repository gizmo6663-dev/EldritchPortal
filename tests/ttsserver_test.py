"""Funksjonstest av opplesingsserveren i tools/opplesing_server.py.

    python3 tests/ttsserver_test.py

Serveren er broen mellom nettsida og edge-tts. Selve edge-tts krever
nett til Microsoft, som dette miljøet ikke har, så den settes på her:
det som testes er rørleggerarbeidet rundt — at appen serveres, at
stemmelista bare gir de norske, at teksten og innstillingene kommer
uendret fram til talesyntesen, at samme forespørsel to ganger bare
lager lyden én gang, og at søppel inn gir et ærlig svar ut.
"""
import importlib.util, json, os, sys, tempfile, threading
import urllib.error, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

fails = []


def check(name, got, want):
    ok = got == want
    print(("  ok    " if ok else "  FAIL  ") + name +
          ("" if ok else f": {got!r} != {want!r}"))
    if not ok:
        fails.append(name)


def load(path, navn):
    spec = importlib.util.spec_from_file_location(navn, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    import fake_edge                      # setter inn edge_tts
    edge = sys.modules["edge_tts"]
    srv_mod = load(os.path.join(REPO, "tools", "opplesing_server.py"),
                   "opplesing_server")
    import socketserver

    cache = tempfile.mkdtemp(prefix="tts-cache-")
    srv_mod.Handler.cache_dir = cache
    srv_mod.Handler.root = os.path.join(REPO, "web")
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), srv_mod.Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    base = "http://127.0.0.1:%d" % port

    def get(path):
        with urllib.request.urlopen(base + path, timeout=10) as r:
            return r.status, r.headers.get("Content-Type"), r.read()

    def post(path, payload, raw=None):
        data = raw if raw is not None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            base + path, data=data,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, r.headers.get("Content-Type"), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type"), e.read()

    try:
        print("\n== appen serveres ==")
        kode, mime, body = get("/")
        check("forsida svarer", kode, 200)
        check("og det er appen", b"Eldritch Portal" in body, True)
        check("som html", "text/html" in (mime or ""), True)

        print("\n== stemmelista ==")
        kode, _, body = get("/tts/stemmer")
        data = json.loads(body)
        check("lista svarer", kode, 200)
        navn = [v["id"] for v in data["stemmer"]]
        check("bare de norske er med", navn,
              ["nb-NO-PernilleNeural", "nb-NO-FinnNeural"])
        check("kjønn er med", data["stemmer"][0]["kjonn"], "kvinne")
        check("og mannsstemmen er merket", data["stemmer"][1]["kjonn"], "mann")
        check("Pernille er standard", data["standard"],
              "nb-NO-PernilleNeural")

        print("\n== teksten når fram uendret ==")
        del edge.KALL[:]
        kode, mime, lyd = post("/tts", {
            "tekst": "Dagrun så tyvens sanne form.",
            "stemme": "nb-NO-FinnNeural", "tempo": "-12%", "dybde": "-5Hz"})
        check("svaret er lyd", kode, 200)
        check("med riktig type", mime, "audio/mpeg")
        check("og har innhold", len(lyd) > 0, True)
        check("talesyntesen ble kalt én gang", len(edge.KALL), 1)
        check("med teksten", edge.KALL[0]["text"],
              "Dagrun så tyvens sanne form.")
        check("den valgte stemmen", edge.KALL[0]["voice"], "nb-NO-FinnNeural")
        check("tempoet", edge.KALL[0]["rate"], "-12%")
        check("og dybden", edge.KALL[0]["pitch"], "-5Hz")

        print("\n== samme spørsmål lager ikke lyden på nytt ==")
        del edge.KALL[:]
        kode, _, lyd2 = post("/tts", {
            "tekst": "Dagrun så tyvens sanne form.",
            "stemme": "nb-NO-FinnNeural", "tempo": "-12%", "dybde": "-5Hz"})
        check("svaret er det samme", lyd2, lyd)
        check("uten å spørre tjenesten igjen", len(edge.KALL), 0)
        post("/tts", {"tekst": "Dagrun så tyvens sanne form.",
                      "stemme": "nb-NO-PernilleNeural"})
        check("men en annen stemme lager ny lyd", len(edge.KALL), 1)

        print("\n== standardverdier når ingenting er valgt ==")
        del edge.KALL[:]
        post("/tts", {"tekst": "Uten valg."})
        check("Pernille brukes", edge.KALL[0]["voice"], "nb-NO-PernilleNeural")
        check("tempoet står litt ned", edge.KALL[0]["rate"], "-8%")
        check("og dybden står på null", edge.KALL[0]["pitch"], "+0Hz")

        print("\n== søppel inn gir et ærlig svar ==")
        kode, _, body = post("/tts", None, raw=b"{ikke json}")
        check("ugyldig JSON avvises", kode, 400)
        check("med en forklaring", "feil" in json.loads(body), True)
        kode, _, _ = post("/tts", {"tekst": "   "})
        check("tom tekst avvises", kode, 400)
        kode, _, _ = post("/tts", {"tekst": "x" * 90000})
        check("for mye tekst avvises", kode, 413)
        kode, _, _ = post("/finnesikke", {"tekst": "hei"})
        check("ukjent rute avvises", kode, 404)

        print("\n== teksten kortes, den kveler ikke serveren ==")
        del edge.KALL[:]
        lang = "a" * (srv_mod.MAKS_TEGN + 500)
        kode, _, _ = post("/tts", {"tekst": lang})
        check("den slipper gjennom", kode, 200)
        check("men er kortet til taket",
              len(edge.KALL[0]["text"]), srv_mod.MAKS_TEGN)

        print("\n== sida kan hentes fra en annen adresse ==")
        with urllib.request.urlopen(base + "/tts/stemmer", timeout=10) as r:
            check("CORS er åpen",
                  r.headers.get("Access-Control-Allow-Origin"), "*")
    finally:
        srv.shutdown()
        srv.server_close()

    print("\nRESULT:", "FAILED" if fails else "OK")


main()
