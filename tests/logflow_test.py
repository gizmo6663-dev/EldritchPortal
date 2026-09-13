"""Funksjonstest av snarveier, kamplogg, skrivemodus og rollebesetning.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/logflow_test.py

Dette er de fire tingene som skal gjøre loggen verdt å føre: at det man
skriver om igjen og om igjen er ett trykk unna, at kampen skriver sitt
eget sammendrag, at linjene kan skrives om til prosa mens man husker
dem, og at økta vet hvem som var med.
"""
import asyncio, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="logflow-")

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

        chars = json.load(open(os.path.join(REPO, "characters.json")))
        await pg.evaluate("""async (l) => {
            state.characters = l.map(normalizeChar);
            await saveCharacters(); render(); }""", chars)

        print("\n== snarveiene ==")
        s = await pg.evaluate("""() => {
            setView('overview');
            const skjult = getComputedStyle(
              document.getElementById('quick-chips')).display;
            document.getElementById('quick-note').focus();
            const synlig = getComputedStyle(
              document.getElementById('quick-chips')).display;
            return { skjult, synlig,
                     antall: document.querySelectorAll('.quickchip').length }; }""")
        check("snarveiene ligger unna til man skal skrive", s["skjult"], "none")
        check("og kommer fram når markøren står i linja", s["synlig"], "flex")
        check("alle seks er der", s["antall"], 6)

        s = await pg.evaluate("""() => {
            const chip = [...document.querySelectorAll('.quickchip')]
              .find(c => c.textContent === 'SAN-tap');
            chip.click();
            const f = document.getElementById('quick-note');
            return { verdi: f.value, fokus: document.activeElement === f,
                     merket: chip.getAttribute('aria-pressed'),
                     kind: state.quickKind }; }""")
        check("snarveien starter linja", s["verdi"], "SAN-tap: ")
        check("markøren står i feltet", s["fokus"], True)
        check("og knappen viser at den er valgt", s["merket"], "true")
        check("linja er merket", s["kind"], "san")

        av = await pg.evaluate("""() => {
            const chip = [...document.querySelectorAll('.quickchip')]
              .find(c => c.textContent === 'SAN-tap');
            chip.click();
            return { verdi: document.getElementById('quick-note').value,
                     kind: state.quickKind }; }""")
        check("et nytt trykk slår den av", av["verdi"], "")
        check("og fjerner merket", av["kind"], None)

        await pg.evaluate("""() => {
            [...document.querySelectorAll('.quickchip')]
              .find(c => c.textContent === 'SAN-tap').click(); }""")
        await pg.evaluate("""() => {
            const f = document.getElementById('quick-note');
            f.value = f.value + 'Dagrun mistet 6 på synet av tyven'; }""")
        await pg.press("#quick-note", "Enter")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => {
            const s = state.progress.sessions[0];
            const e = s.log[0];
            return { kind: e.kind, tekst: e.text,
                     etter: state.quickKind,
                     knapp: [...document.querySelectorAll('.quickchip')]
                       .some(c => c.getAttribute('aria-pressed') === 'true') }; }""")
        check("merkelappen følger linja", r["kind"], "san")
        check("med hele teksten", r["tekst"],
              "SAN-tap: Dagrun mistet 6 på synet av tyven")
        check("merket nullstilles etterpå", r["etter"], None)
        check("og ingen knapp står igjen valgt", r["knapp"], False)

        print("\n== kampen skriver sitt eget sammendrag ==")
        await pg.evaluate("""async () => {
            state.combat = emptyCombat();
            const w = state.characters.find((c) => c.name === 'Walther');
            const d = state.characters.find((c) => c.name === 'Dagrun');
            const g = state.bestiary.creatures.find((c) => /ghoul/i.test(c.name));
            await addToCombat(w); await addToCombat(d);
            await addToCombat(beastToChar(g));
            state.combat.combatants.forEach((c, i) => { c.init = String(90-i*20); });
            state.combat.active = true; state.combat.round = 4;
            // Walther kom skadet fra det, ghoulen overlevde ikke.
            const cw = state.combat.combatants.find(c => c.name === 'Walther');
            cw.hp = Math.max(1, cw.hpMax - 5);
            const cg = state.combat.combatants.find(c => /Ghoul/.test(c.name));
            cg.hp = 0; cg.conditions = ['Død'];
            await saveCombat(); setView('combat'); render(); }""")
        await pg.wait_for_timeout(500)
        sammendrag = await pg.evaluate("() => combatSummary()")
        print("  sammendrag:", sammendrag)
        check("begge sidene er navngitt",
              "Walther" in sammendrag and "Ghoul" in sammendrag, True)
        check("med antall runder", "4 runder" in sammendrag, True)
        check("hvem som døde", "Døde: " in sammendrag, True)
        check("og hvem som gikk skadet derfra",
              "Skadet: Walther" in sammendrag, True)

        r = await pg.evaluate("""async () => {
            const knapp = [...document.querySelectorAll('#main button')]
              .find(b => b.textContent === 'Ta med i øktnotatet');
            knapp.click();
            await new Promise(r => setTimeout(r, 300));
            return { pa: !!state.combat.toLog,
                     tekst: [...document.querySelectorAll('#main button')]
                       .some(b => b.textContent === 'Tas med i øktnotatet') }; }""")
        check("bryteren kan slås på", r["pa"], True)
        check("og sier fra at den står på", r["tekst"], True)

        r = await pg.evaluate("""async () => {
            const knapp = [...document.querySelectorAll('#main button')]
              .find(b => b.textContent === 'Avslutt kamp');
            knapp.click();
            await new Promise(r => setTimeout(r, 200));
            [...document.querySelectorAll('button')]
              .filter(b => /Avslutt|Ja|Bekreft/i.test(b.textContent))
              .slice(-1)[0].click();
            await new Promise(r => setTimeout(r, 600));
            const s = state.progress.sessions[0];
            const e = s.log[s.log.length - 1];
            return { linjer: s.log.length, kind: e.kind, tekst: e.text,
                     runde: state.combat.round }; }""")
        check("kampen havnet i loggen da den ble avsluttet", r["linjer"], 2)
        check("merket som kamp", r["kind"], "kamp")
        check("med runder talt før nullstillingen",
              "4 runder" in r["tekst"], True)
        check("og kampen er faktisk avsluttet", r["runde"], 0)

        print("\n== hvem var med ==")
        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => ({
            chips: document.querySelectorAll('.castchip').length,
            valgt: [...document.querySelectorAll('.castchip')]
              .filter(c => c.getAttribute('aria-pressed') === 'true').length,
            cast: state.progress.sessions[0].cast.length }); }""") \
            if False else await pg.evaluate("""() => ({
            chips: document.querySelectorAll('.castchip').length,
            valgt: [...document.querySelectorAll('.castchip')]
              .filter(c => c.getAttribute('aria-pressed') === 'true').length,
            cast: (state.progress.sessions[0].cast || []).length })""")
        check("alle spillerne står der", r["chips"] > 0, True)
        check("og er med som utgangspunkt", r["valgt"], r["chips"])
        check("det er lagret på økta", r["cast"], r["chips"])

        borte = await pg.evaluate("""async () => {
            document.querySelector('.castchip').click();
            await new Promise(r => setTimeout(r, 400));
            return { cast: state.progress.sessions[0].cast.length,
                     md: oneSessionMarkdown(state.progress.sessions[0]) }; }""")
        check("den som ikke møtte krysses bort", borte["cast"], r["chips"] - 1)
        check("og eksporten navngir de som var der",
              "*Med: " in borte["md"], True)

        print("\n== skrivemodus ==")
        w = await pg.evaluate("""async () => {
            const knapp = [...document.querySelectorAll('#main button')]
              .find(b => b.textContent === 'Skriv ferdig');
            knapp.click();
            await new Promise(r => setTimeout(r, 300));
            return { felt: document.querySelectorAll('#main .logwrite textarea').length,
                     linjer: state.progress.sessions[0].log.length,
                     tilbake: [...document.querySelectorAll('#main button')]
                       .some(b => b.textContent === 'Ferdig å skrive') }; }""")
        check("hver linje fikk et felt", w["felt"], w["linjer"])
        check("og knappen kan slås av igjen", w["tilbake"], True)

        await pg.fill("#prose-0-0",
                      "Dagrun så tyvens sanne form og brast ut i panikk.")
        await pg.wait_for_timeout(800)
        satt = await pg.evaluate("""async () => {
            const knapp = [...document.querySelectorAll('#main button')]
              .find(b => /Sett sammen/.test(b.textContent));
            knapp.click();
            await new Promise(r => setTimeout(r, 600));
            const s = state.progress.sessions[0];
            return { sammendrag: s.summary, prosa: s.log[0].prose,
                     merket: s.log.every(e => e.merged),
                     igjen: [...document.querySelectorAll('#main button')]
                       .some(b => /Sett sammen/.test(b.textContent)) }; }""")
        check("prosaen er lagret på linja",
              satt["prosa"], "Dagrun så tyvens sanne form og brast ut i panikk.")
        check("sammendraget bruker prosaen",
              "brast ut i panikk" in satt["sammendrag"], True)
        check("og rålinja er ikke med for den",
              "SAN-tap: Dagrun mistet" not in satt["sammendrag"], True)
        check("kamplinja kom med som den var",
              "Kamp: " in satt["sammendrag"], True)
        check("alle er merket som satt sammen", satt["merket"], True)
        check("så de ikke settes sammen to ganger", satt["igjen"], False)

        md = await pg.evaluate(
            "() => oneSessionMarkdown(state.progress.sessions[0])")
        check("eksporten tar vare på prosaen også i loggen",
              "> Dagrun så tyvens sanne form" in md, True)

        print("\n== alt overlever en omlasting ==")
        await pg.evaluate("() => { flushWrites(); }")
        await pg.wait_for_timeout(300)
        await pg.reload()
        await pg.wait_for_timeout(2500)
        r = await pg.evaluate("""() => {
            const s = state.progress.sessions[0];
            return { linjer: s.log.length, kind: s.log[0].kind,
                     prosa: !!s.log[0].prose, cast: s.cast.length,
                     bryter: !!state.combat.toLog }; }""")
        check("loggen er der", r["linjer"], 2)
        check("merkelappene også", r["kind"], "san")
        check("prosaen også", r["prosa"], True)
        check("rollebesetningen også", r["cast"] > 0, True)
        check("og kampbryteren husker seg selv", r["bryter"], True)

        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{OUT}/sesjon.png", full_page=True)
        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("\nRESULT:", "FAILED" if fails else "OK")
        await b.close()

asyncio.run(main())
