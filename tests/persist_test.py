"""Funksjonstest av lagring, eksport og den samlede Økta-fanen.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/persist_test.py

Det som testes er det som gjør vondt hvis det svikter: at tekst man
nettopp har skrevet ikke ligger og venter på en timer når fanen
forsvinner, at Lagre nå faktisk skriver, og at en økt kan eksporteres
med hvor langt gruppa er kommet.
"""
import asyncio, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="persist-")

fails = []


def check(name, got, want):
    ok = got == want
    print(("  ok    " if ok else "  FAIL  ") + name +
          ("" if ok else f": {got!r} != {want!r}"))
    if not ok:
        fails.append(name)


async def main():
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

        print("\n== utsatte skrivinger kan tvinges ut ==")
        r = await pg.evaluate("""() => {
            let n = 0;
            const f = debounce(() => { n += 1; }, 5000);
            f();                       // ligger og venter i 5 sekunder
            const ventet = pendingWrites.size;
            const skrevet = flushWrites();
            return { ventet, skrevet, kjort: n, igjen: pendingWrites.size };
        }""")
        check("skrivingen meldte seg inn som ventende", r["ventet"], 1)
        check("flushWrites skrev den ut", r["skrevet"], 1)
        check("og funksjonen kjørte faktisk", r["kjort"], 1)
        check("køen er tom etterpå", r["igjen"], 0)

        print("\n== sesjonstekst overlever at fanen forsvinner ==")
        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(400)
        await pg.click("button:text-is('Ny sesjon')")
        await pg.wait_for_timeout(500)
        await pg.fill("#sess-sum-0", "Beefcake gikk amok i korridoren.")
        # Ikke vent på debouncen — lat som fanen forsvinner med én gang.
        await pg.evaluate("""() => {
            document.dispatchEvent(new Event('visibilitychange'));
            Object.defineProperty(document, 'visibilityState',
                                  { value: 'hidden', configurable: true });
            document.dispatchEvent(new Event('visibilitychange'));
        }""")
        await pg.wait_for_timeout(400)
        lagret = await pg.evaluate(
            "() => (state.progress.sessions[0] || {}).summary || ''")
        check("teksten rakk ned før fanen ble skjult",
              lagret, "Beefcake gikk amok i korridoren.")
        raw = await pg.evaluate("""() => {
            const k = Object.keys(localStorage).find(x => /progress/.test(x));
            return k ? localStorage.getItem(k) : ''; }""")
        check("og den ligger i localStorage",
              "Beefcake gikk amok" in raw, True)

        print("\n== Lagre nå ==")
        chip = await pg.evaluate("""async () => {
            document.getElementById('save-now').click();
            await new Promise(r => setTimeout(r, 500));
            return document.getElementById('save-chip').textContent; }""")
        print("  merket sier:", chip)
        check("knappen setter et tidsstempel", chip.startswith("Lagret "), True)

        print("\n== eksport av økta ==")
        md = await pg.evaluate("""() => {
            // Kryss av et spor og en scene, så statusdelen har noe å vise.
            const c = state.scenario.clues.find(x => x.points === 'villspor');
            toggleFlag(c.id);
            return sessionsMarkdown(true); }""")
        await pg.wait_for_timeout(400)
        check("sammendraget er med", "Beefcake gikk amok" in md, True)
        check("scenarioets tittel står øverst",
              md.startswith("# A Slow Boat to China"), True)
        check("statusdelen er med", "Hvor langt dere er kommet" in md, True)
        check("og villspor merkes også der", "[villspor]" in md, True)
        one = await pg.evaluate("""() =>
            oneSessionMarkdown(state.progress.sessions[0])""")
        check("én enkelt økt kan eksporteres alene",
              "Beefcake gikk amok" in one and "Hvor langt" not in one, True)

        print("\n== Økta: alt i én strøm ==")
        s = await pg.evaluate("""() => { setView('stream'); render();
            return {
              rader: document.querySelectorAll('#main .entry').length,
              merker: document.querySelectorAll('#main .streamtag').length,
              koblet: document.querySelectorAll('#main .entryline.linked').length,
              typer: [...new Set([...document.querySelectorAll('#main .streamtag')]
                       .map(x => x.textContent))].sort(),
            }; }""")
        print("  strøm:", s)
        check("hver rad sier hvor den kommer fra", s["merker"], s["rader"])
        check("alle fire delene er med", s["typer"],
              ["SCENE", "SPOR", "STED", "TIDSLINJE"])
        check("og noe henger under en tidslinjehendelse", s["koblet"] > 0, True)

        valget = await pg.evaluate("""() => {
            state.streamOn.locations = false; saveStreamPrefs(); render();
            const etter = document.querySelectorAll('#main .streamtag.locations').length;
            state.streamOn.locations = true; saveStreamPrefs();
            return etter; }""")
        check("delene kan skrus av", valget, 0)

        await pg.screenshot(path=f"{OUT}/okta.png", full_page=True)
        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("\nRESULT:", "FAILED" if fails else "OK")
        await b.close()

asyncio.run(main())
