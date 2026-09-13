"""Funksjonstest av «kryss av = logg» og angreknappen.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/angre_test.py

To ting som henger sammen: avkryssingen skriver sin egen linje i
loggen, og en feil avkryssing skal kunne tas tilbake — også linja den
skrev. Ellers står det igjen en hendelse i loggen som aldri skjedde.
"""
import asyncio, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="angre-")

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

        await pg.evaluate("""async () => {
            state.progress.sessions = [{ title: "Sesjon 1", date: "2026-09-13",
                                         summary: "", cast: [], log: [] }];
            await saveProgress(); }""")

        print("\n== bryteren står av til man slår den på ==")
        r = await pg.evaluate("""async () => {
            setView('stream'); render();
            const av = !state.progress.autoLog;
            const spor = state.scenario.clues[0];
            await toggleFlag(spor.id);
            const etter = state.progress.sessions[0].log.length;
            await toggleFlag(spor.id);      // rydd opp
            return { av, etter }; }""")
        check("den er av i utgangspunktet", r["av"], True)
        check("og da skriver avkryssing ingenting", r["etter"], 0)

        print("\n== kryss av = logg ==")
        r = await pg.evaluate("""async () => {
            const knapp = [...document.querySelectorAll('#main .chip.resp')]
              .find(c => c.textContent === 'Kryss av = logg');
            if (!knapp) return { fant: false };
            knapp.click();
            await new Promise(r => setTimeout(r, 400));
            return { fant: true, pa: !!state.progress.autoLog,
                     merket: [...document.querySelectorAll('#main .chip.resp')]
                       .find(c => c.textContent === 'Kryss av = logg')
                       .getAttribute('aria-pressed') }; }""")
        check("bryteren finnes i Økta", r["fant"], True)
        check("og kan slås på", r["pa"], True)
        check("og viser at den står på", r["merket"], "true")

        # Uten nå-peker har et spor ingenting å feste seg i, med mindre
        # en tidslinjehendelse peker på det. Det er riktig — linja blir
        # merket «uten sted» og kan festes etterpå.
        r = await pg.evaluate("""async () => {
            const spor = state.scenario.clues.find(c => !c.found);
            await toggleFlag(spor.id);
            const log = state.progress.sessions[0].log;
            const e = log[log.length - 1];
            return { linjer: log.length, tekst: e.text, kind: e.kind,
                     ref: e.ref === spor.id,
                     tittel: spor.title, krysset: !!spor.found }; }""")
        check("avkryssingen skrev én linje", r["linjer"], 1)
        check("raden er faktisk krysset av", r["krysset"], True)
        check("linja leser som noe som skjedde",
              r["tekst"], "Spor funnet: " + r["tittel"])
        check("den er merket som avkrysset", r["kind"], "kryss")
        check("den husker hvilken rad", r["ref"], True)

        print("\n== avkryssing på tidslinja flytter nå-pekeren ==")
        r = await pg.evaluate("""async () => {
            const ev = state.scenario.timeline.find(x => !x.triggered);
            await toggleFlag(ev.id);
            const log = state.progress.sessions[0].log;
            const e = log[log.length - 1];
            return { now: state.progress.now === ev.id,
                     anchor: e.anchor === ev.id,
                     knapp: document.getElementById('quick-now')
                              .textContent.startsWith('NÅ ·') }; }""")
        check("pekeren flyttet seg dit", r["now"], True)
        check("og linja er forankret der", r["anchor"], True)
        check("knappen viser det", r["knapp"], True)

        r = await pg.evaluate("""async () => {
            // Nå har alt som logges et sted å høre hjemme.
            const spor = state.scenario.clues.find(c => !c.found);
            await toggleFlag(spor.id);
            const log = state.progress.sessions[0].log;
            return !!log[log.length - 1].anchor; }""")
        check("og et spor arver den", r, True)

        r = await pg.evaluate("""async () => {
            const for_ = state.progress.now;
            document.getElementById('quick-undo').click();
            await new Promise(r => setTimeout(r, 400));
            document.getElementById('quick-undo').click();
            await new Promise(r => setTimeout(r, 400));
            return { nullstilt: state.progress.now === "" }; }""")
        check("og angring setter pekeren tilbake", r["nullstilt"], True)

        r = await pg.evaluate("""async () => {
            const scene = state.scenario.beats.find(x => !x.done);
            const sted = state.scenario.locations.find(x => !x.visited);
            await toggleFlag(scene.id);
            await toggleFlag(sted.id);
            const log = state.progress.sessions[0].log;
            return log.slice(-2).map(e => e.text.split(':')[0]); }""")
        check("hver type får sin egen ordlyd", r, ["Scene spilt", "Besøkte"])

        print("\n== å fjerne krysset skriver ingenting nytt ==")
        r = await pg.evaluate("""async () => {
            const spor = state.scenario.clues.find(c => c.found);
            const for_ = state.progress.sessions[0].log.length;
            await toggleFlag(spor.id);
            return { for_: for_,
                     etter: state.progress.sessions[0].log.length,
                     krysset: !!spor.found }; }""")
        check("krysset ble fjernet", r["krysset"], False)
        check("uten en ny linje i loggen", r["etter"], r["for_"])

        print("\n== angre ==")
        r = await pg.evaluate("""() => ({
            synlig: !document.getElementById('quick-undo').hidden,
            tittel: document.getElementById('quick-undo').title })""")
        check("angreknappen er framme", r["synlig"], True)
        check("og sier hva den angrer",
              r["tittel"].startswith("Angre: fjernet kryss for"), True)

        r = await pg.evaluate("""async () => {
            // Kryss av noe feil, og ta det tilbake.
            const spor = state.scenario.clues.find(c => !c.found);
            await toggleFlag(spor.id);
            const etterKryss = { krysset: !!spor.found,
                                 linjer: state.progress.sessions[0].log.length };
            document.getElementById('quick-undo').click();
            await new Promise(r => setTimeout(r, 500));
            const samme = state.scenario.clues.find(c => c.id === spor.id);
            return { etterKryss,
                     krysset: !!samme.found,
                     linjer: state.progress.sessions[0].log.length,
                     iFlagg: !!state.progress.flags[spor.id] }; }""")
        check("krysset kom på", r["etterKryss"]["krysset"], True)
        check("og angringen tok det av igjen", r["krysset"], False)
        check("også i det som lagres", r["iFlagg"], False)
        check("og linja loggen fikk er borte",
              r["linjer"], r["etterKryss"]["linjer"] - 1)

        print("\n== ctrl-Z gjør det samme ==")
        await pg.evaluate("""async () => {
            const scene = state.scenario.beats.find(x => !x.done);
            await toggleFlag(scene.id); }""")
        for_ = await pg.evaluate(
            "() => state.progress.sessions[0].log.length")
        await pg.evaluate("() => document.body.focus()")
        await pg.keyboard.press("Control+z")
        await pg.wait_for_timeout(500)
        etter = await pg.evaluate(
            "() => state.progress.sessions[0].log.length")
        check("snarveien angret også", etter, for_ - 1)

        skrev = await pg.evaluate("""async () => {
            // Men ikke når man skriver et sted.
            const f = document.getElementById('quick-note');
            f.value = "en tekst";
            f.focus();
            const for_ = undoStack.length;
            f.dispatchEvent(new KeyboardEvent('keydown',
              { key: 'z', ctrlKey: true, bubbles: true }));
            await new Promise(r => setTimeout(r, 200));
            f.value = "";
            return { for_: for_, etter: undoStack.length }; }""")
        check("snarveien tar ikke angringen fra tekstfeltet",
              skrev["etter"], skrev["for_"])

        print("\n== en slettet logglinje kan hentes tilbake ==")
        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""async () => {
            const for_ = state.progress.sessions[0].log.map(e => e.text);
            document.querySelector('#main .logdrop').click();
            await new Promise(r => setTimeout(r, 500));
            const mellom = state.progress.sessions[0].log.length;
            document.getElementById('quick-undo').click();
            await new Promise(r => setTimeout(r, 500));
            return { for_: for_.length, mellom: mellom,
                     etter: state.progress.sessions[0].log.length,
                     samme: JSON.stringify(
                       state.progress.sessions[0].log.map(e => e.text)) ===
                       JSON.stringify(for_) }; }""")
        check("linja ble slettet", r["mellom"], r["for_"] - 1)
        check("og kom tilbake", r["etter"], r["for_"])
        check("på samme plass i rekka", r["samme"], True)

        print("\n== stabelen vokser ikke i det uendelige ==")
        r = await pg.evaluate("""async () => {
            for (let i = 0; i < UNDO_MAX + 6; i += 1) {
              const x = state.scenario.clues[i % state.scenario.clues.length];
              await toggleFlag(x.id);
            }
            return undoStack.length; }""")
        check("den stopper på taket", r, 12)

        print("\n== bryteren overlever en omlasting ==")
        await pg.evaluate("() => { flushWrites(); }")
        await pg.wait_for_timeout(300)
        await pg.reload()
        await pg.wait_for_timeout(2500)
        r = await pg.evaluate("""() => ({
            pa: !!state.progress.autoLog,
            angre: document.getElementById('quick-undo').hidden })""")
        check("bryteren står fortsatt på", r["pa"], True)
        check("men angrestabelen er tom etter omlasting", r["angre"], True)

        await pg.evaluate("setView('stream')")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{OUT}/okta.png")
        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("\nRESULT:", "FAILED" if fails else "OK")
        await b.close()

asyncio.run(main())
