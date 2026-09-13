"""Funksjonstest av opplesingen — både teksten og leseren.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/opplesing_test.py

To ting testes. Først vasken i tools/opplesing.py, som gjør markdown om
til noe som kan leses høyt: den er ren tekstbehandling og testes
direkte. Så leseren i nettleseren, med en påsatt talesyntese, slik at
rekkefølgen og stoppingen kan sjekkes uten at noen faktisk snakker.

Selve edge-tts er ikke testet her: den krever nett til Microsoft, og
det har ikke dette miljøet.
"""
import asyncio, importlib.util, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="opplesing-")

fails = []


def check(name, got, want):
    ok = got == want
    print(("  ok    " if ok else "  FAIL  ") + name +
          ("" if ok else f": {got!r} != {want!r}"))
    if not ok:
        fails.append(name)


def load_tool():
    path = os.path.join(REPO, "tools", "opplesing.py")
    spec = importlib.util.spec_from_file_location("opplesing", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_vask():
    print("\n== markdown vasket for opplesing ==")
    o = load_tool()
    check("overskrifter ender i punktum",
          o.vask("# A Slow Boat to China"), "A Slow Boat to China.")
    check("datoer blir til ord",
          o.vask("*2026-09-13*"), "13. september 2026.")
    check("utheving forsvinner",
          o.vask("Han så **den sanne formen**"), "Han så den sanne formen.")
    check("kulepunkt blir setninger",
          o.vask("- Wang Ma er død"), "Wang Ma er død.")
    check("klokkeslett blir lest som tid",
          o.vask("- **11:43** Kamp: Ghouls nede"),
          "Klokka 11 43. Kamp: Ghouls nede.")
    check("tankestrek blir et pust",
          o.vask("Fire runder — ingen døde"), "Fire runder, ingen døde.")
    check("lenker beholder teksten",
          o.vask("Se [boka](http://x.no) igjen"), "Se boka igjen.")
    check("sitatstrek forsvinner",
          o.vask("> Hun rakk ikke se det"), "Hun rakk ikke se det.")
    check("en linje som allerede har punktum får ikke ett til",
          o.vask("Det var slutt."), "Det var slutt.")
    check("en ugyldig dato får stå som den er",
          o.vask("2026-19-13"), "2026-19-13.")


async def test_reader():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path=os.environ.get("CHROMIUM_PATH") or None)
        ctx = await b.new_context(viewport={"width": 1280, "height": 1100})
        errs = []
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.on("console", lambda m: errs.append("CONSOLE: " + m.text)
              if m.type == "error" and "ERR_CONNECTION" not in m.text else None)
        await pg.goto(URL)
        await pg.wait_for_timeout(2500)

        chars = json.load(open(os.path.join(REPO, "characters.json")))
        await pg.evaluate("""async (l) => {
            state.characters = l.map(normalizeChar);
            await saveCharacters();
            state.progress.sessions = [{
              title: "Sesjon 1", date: "2026-09-13",
              summary: "Dagrun så tyvens sanne form — og brast ut i panikk.\\n\\n" +
                       "Skytteren kastet seg over rekka.",
              cast: ["Dagrun", "Franz"],
              log: [{ t: "2026-09-13T21:14:00.000Z", text: "Wang Ma funnet død",
                      view: "Økta" }],
            }];
            await saveProgress(); render(); }""", chars)

        print("\n== teksten som skal leses ==")
        t = await pg.evaluate(
            "() => speechTextFor(state.progress.sessions[0], false)")
        print("  " + t.replace("\n", "\n  "))
        check("tittelen står først", t.startswith("Sesjon 1."), True)
        check("datoen er skrevet ut", "13. september 2026." in t, True)
        check("hvem som var med er med", "Med: Dagrun, Franz." in t, True)
        check("tankestreken er blitt et pust",
              "sanne form, og brast ut i panikk." in t, True)
        check("loggen er ikke med når den ikke er bedt om",
              "Wang Ma" in t, False)
        med = await pg.evaluate(
            "() => speechTextFor(state.progress.sessions[0], true)")
        check("men den kommer med når den er det",
              "Wang Ma funnet død." in med, True)

        biter = await pg.evaluate(
            "() => splitForSpeech(speechTextFor(state.progress.sessions[0], true))")
        check("teksten deles i biter", len(biter) > 1, True)
        check("og ingen bit er for lang for talesyntesen",
              max(len(x) for x in biter) <= 200, True)

        print("\n== stemmevalget ==")
        r = await pg.evaluate("""() => {
            const fake = [
              { name: "Google US English", lang: "en-US", voiceURI: "en" },
              { name: "Microsoft Pernille", lang: "nb-NO", voiceURI: "nb-p" },
              { name: "Microsoft Finn", lang: "nb-NO", voiceURI: "nb-f" },
              { name: "Dansk", lang: "da-DK", voiceURI: "da" },
            ];
            return fake.slice().sort((a,b) => voiceScore(b) - voiceScore(a))
              .map(v => v.voiceURI); }""")
        check("norsk mannsstemme først", r[0], "nb-f")
        check("så den andre norske", r[1], "nb-p")
        check("og engelsk sist", r[3], "en")

        print("\n== leseren kjører gjennom hele teksten ==")
        r = await pg.evaluate("""async () => {
            // Påsatt talesyntese: den sier ingenting, men svarer som om
            // den leste ferdig hver bit.
            const sagt = [];
            window.SpeechSynthesisUtterance = function (text) {
              this.text = text; this.onend = null; this.onerror = null;
            };
            const fake = {
              speaking: false, cancelled: 0, paused: false,
              getVoices: () => [{ name: "Finn", lang: "nb-NO",
                                  voiceURI: "nb-f" }],
              speak(u) {
                sagt.push({ text: u.text, rate: u.rate, pitch: u.pitch,
                            voice: u.voice && u.voice.voiceURI });
                this.speaking = true;
                setTimeout(() => { this.speaking = false;
                                   if (u.onend) u.onend(); }, 5);
              },
              cancel() { this.cancelled += 1; this.speaking = false; },
              pause() { this.paused = true; },
              resume() { this.paused = false; },
            };
            Object.defineProperty(window, "speechSynthesis",
                                  { value: fake, configurable: true });
            const prefs = { voice: "nb-f", rate: 0.82, pitch: 0.7,
                            withLog: false };
            readerStart(speechTextFor(state.progress.sessions[0], false), prefs);
            await new Promise(r => setTimeout(r, 400));
            return { sagt: sagt, spiller: reader.playing,
                     avbrutt: fake.cancelled }; }""")
        check("alle bitene ble lest", len(r["sagt"]) > 1, True)
        check("den valgte stemmen ble brukt", r["sagt"][0]["voice"], "nb-f")
        check("langsomt", r["sagt"][0]["rate"], 0.82)
        check("og mørkt", r["sagt"][0]["pitch"], 0.7)
        check("tittelen kom først",
              r["sagt"][0]["text"].startswith("Sesjon 1"), True)
        check("og leseren stanser av seg selv til slutt",
              r["spiller"], False)

        print("\n== stopp midt i ==")
        r = await pg.evaluate("""async () => {
            const lang = Array(40).fill("Skipet gynget i mørket.").join(" ");
            readerStart(lang, { voice: "nb-f", rate: 1, pitch: 1 });
            const biter = reader.chunks.length;
            await new Promise(r => setTimeout(r, 12));
            readerStop();
            const etter = reader.playing;
            await new Promise(r => setTimeout(r, 60));
            return { biter, etter, spiller: reader.playing,
                     igjen: reader.chunks.length,
                     avbrutt: window.speechSynthesis.cancelled }; }""")
        check("det var flere biter å stoppe i", r["biter"] > 2, True)
        check("stopp stopper med én gang", r["etter"], False)
        check("og den starter ikke opp igjen", r["spiller"], False)
        check("køen er tom", r["igjen"], 0)
        check("talesyntesen ble avbrutt", r["avbrutt"] > 0, True)

        print("\n== knappen i sesjonskortet ==")
        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""async () => {
            const knapp = [...document.querySelectorAll('#main button')]
              .find(b => b.textContent === 'Les opp');
            if (!knapp) return { fant: false };
            knapp.click();
            await new Promise(r => setTimeout(r, 400));
            const body = document.getElementById('modal-body');
            return { fant: true,
                     apen: !document.getElementById('scrim').hidden,
                     tittel: document.getElementById('modal-title')
                               .textContent,
                     stemmer: !!body.querySelector('#speech-voice'),
                     tempo: !!body.querySelector('#speech-rate'),
                     dybde: !!body.querySelector('#speech-pitch'),
                     knapper: [...body.querySelectorAll('button')]
                       .map(b => b.textContent) }; }""")
        check("knappen finnes i kortet", r["fant"], True)
        check("og åpner leseren", r["apen"], True)
        check("med riktig tittel", "Les opp" in r["tittel"], True)
        check("stemmevalget er der", r["stemmer"], True)
        check("tempo er der", r["tempo"], True)
        check("dybde er der", r["dybde"], True)
        check("og teksten kan lastes ned til edge-tts",
              "Last ned teksten" in r["knapper"], True)

        lukket = await pg.evaluate("""async () => {
            readerStart("En lang tekst. Som fortsetter. Og fortsetter.",
                        { voice: "nb-f", rate: 1, pitch: 1 });
            const under = reader.playing;
            closeModal();
            await new Promise(r => setTimeout(r, 60));
            return { under, etter: reader.playing }; }""")
        check("leseren snakker mens kortet er oppe", lukket["under"], True)
        check("og tier når det lukkes", lukket["etter"], False)

        print("\n== innstillingene huskes ==")
        r = await pg.evaluate("""() => {
            saveSpeechPrefs({ voice: "nb-f", rate: 0.6, pitch: 0.4,
                              withLog: true });
            const p = speechPrefs();
            return { rate: p.rate, pitch: p.pitch, log: p.withLog }; }""")
        check("tempoet er lagret", r["rate"], 0.6)
        check("dybden er lagret", r["pitch"], 0.4)
        check("og om loggen skal med", r["log"], True)

        await pg.screenshot(path=f"{OUT}/leser.png")
        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        await b.close()


test_vask()
asyncio.run(test_reader())
print("\nRESULT:", "FAILED" if fails else "OK")
