"""Funksjonstest av hurtignotatet og øktloggen.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/quicknote_test.py

Hele poenget med hurtignotatet er at det skal koste ett felt og én
enter, uansett hvilken fane man står på. Derfor testes det som ville
gjort det verdiløst: at linja havner i nyeste sesjon selv om ingen
sesjon finnes ennå, at loggknappen i Økta gir en påbegynt linje som
husker hvilken rad den kom fra, at linja overlever en omlasting, og at
den kommer med i eksporten.
"""
import asyncio, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="quicknote-")

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

        print("\n== linja ligger der uansett fane ==")
        for view in ("overview", "clues", "combat", "spells"):
            synlig = await pg.evaluate(
                "(v) => { setView(v); return !document.getElementById"
                "('quickbar').hidden; }", view)
            check("hurtignotatet er med på " + view, synlig, True)
        plass = await pg.evaluate("""() => {
            const bar = document.getElementById('quickbar');
            const pad = getComputedStyle(document.querySelector('.main'))
                          .paddingBottom;
            return { hoy: bar.getBoundingClientRect().height,
                     pad: parseFloat(pad) }; }""")
        check("innholdet slutter over linja, ikke bak den",
              plass["pad"] > plass["hoy"], True)

        print("\n== én enter er nok, også uten sesjon fra før ==")
        start = await pg.evaluate("() => state.progress.sessions.length")
        check("ingen sesjoner å skrive til ennå", start, 0)
        await pg.evaluate("setView('overview')")
        await pg.fill("#quick-note", "Wang Ma funnet død på lugaren.")
        await pg.press("#quick-note", "Enter")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => {
            const s = state.progress.sessions[state.progress.sessions.length-1];
            return { sesjoner: state.progress.sessions.length,
                     tittel: s.title, linjer: s.log.length,
                     tekst: s.log[0].text, fane: s.log[0].view,
                     klokke: /^\\d\\d:\\d\\d$/.test(logTime(s.log[0])),
                     felt: document.getElementById('quick-note').value }; }""")
        check("sesjonen ble laget av seg selv", r["sesjoner"], 1)
        check("og fikk et navn", r["tittel"], "Sesjon 1")
        check("linja ligger i loggen", r["linjer"], 1)
        check("med teksten man skrev", r["tekst"],
              "Wang Ma funnet død på lugaren.")
        check("og hvilken fane man sto på", r["fane"], "Oversikt")
        check("linja er tidsstemplet", r["klokke"], True)
        check("feltet er tomt igjen", r["felt"], "")

        print("\n== loggknappen i Økta gir en påbegynt linje ==")
        s = await pg.evaluate("""() => {
            setView('stream'); render();
            const knapp = document.querySelector('#main .logbtn');
            knapp.click();
            const felt = document.getElementById('quick-note');
            return { verdi: felt.value,
                     fokus: document.activeElement === felt,
                     markor: felt.selectionStart === felt.value.length,
                     merke: document.getElementById('quick-ref').hidden,
                     ref: state.quickRef && state.quickRef.section }; }""")
        print("  påbegynt:", s["verdi"])
        check("linja er påbegynt", s["verdi"].endswith(" — "), True)
        check("og navngir raden", len(s["verdi"]) > 6, True)
        check("markøren står i feltet", s["fokus"], True)
        check("og bakerst i teksten", s["markor"], True)
        check("merkelappen viser hvilken rad", s["merke"], False)
        check("og raden er en del av scenarioet", s["ref"] is not None, True)

        await pg.evaluate("""() => {
            const f = document.getElementById('quick-note');
            f.value = f.value + 'blod på trekassa'; }""")
        await pg.press("#quick-note", "Enter")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => {
            const s = state.progress.sessions[0];
            const e = s.log[s.log.length - 1];
            return { linjer: s.log.length, tekst: e.text,
                     ref: !!e.ref, tittel: e.refTitle,
                     merke: document.getElementById('quick-ref').hidden }; }""")
        check("linje nummer to ligger der", r["linjer"], 2)
        check("med hele teksten", r["tekst"].endswith("blod på trekassa"), True)
        check("og den husker hvilken rad den kom fra", r["ref"], True)
        check("med navn", bool(r["tittel"]), True)
        check("merkelappen er borte etterpå", r["merke"], True)

        print("\n== N setter markøren i feltet ==")
        await pg.evaluate("() => { setView('clues'); document.body.focus(); }")
        await pg.wait_for_timeout(200)
        await pg.keyboard.press("n")
        fokus = await pg.evaluate(
            "() => document.activeElement.id === 'quick-note'")
        check("snarveien treffer feltet", fokus, True)
        await pg.fill("#quick-note", "n")
        await pg.keyboard.press("n")
        verdi = await pg.evaluate(
            "() => document.getElementById('quick-note').value")
        check("men spiser ikke bokstaver når man skriver", verdi, "nn")
        await pg.evaluate(
            "() => { document.getElementById('quick-note').value = ''; }")

        print("\n== loggen i sesjonsfanen ==")
        s = await pg.evaluate("""() => {
            setView('sessions'); render();
            return { rader: document.querySelectorAll('#main .logrow').length,
                     flett: [...document.querySelectorAll('#main button')]
                       .some(b => /Sett sammen/.test(b.textContent)) }; }""")
        check("begge linjene vises", s["rader"], 2)
        check("og kan settes sammen", s["flett"], True)
        flettet = await pg.evaluate("""async () => {
            const knapp = [...document.querySelectorAll('#main button')]
              .find(b => /Sett sammen/.test(b.textContent));
            if (!knapp) return { fant: false };
            knapp.click();
            await new Promise(r => setTimeout(r, 400));
            const s = state.progress.sessions[0];
            return { fant: true, sammendrag: s.summary,
                     merket: s.log.every(e => e.merged),
                     igjen: [...document.querySelectorAll('#main button')]
                       .some(b => /Sett sammen/.test(b.textContent)) }; }""")
        check("knappen finnes", flettet["fant"], True)
        check("linjene havnet i sammendraget",
              "Wang Ma funnet død" in flettet["sammendrag"], True)
        check("og er merket som flettet", flettet["merket"], True)
        check("så de ikke kan flettes to ganger", flettet["igjen"], False)

        print("\n== eksporten tar med loggen ==")
        md = await pg.evaluate(
            "() => oneSessionMarkdown(state.progress.sessions[0])")
        check("loggen har sin egen del", "### Logg underveis" in md, True)
        check("med linjene i", "blod på trekassa" in md, True)

        print("\n== alt overlever en omlasting ==")
        await pg.evaluate("() => { flushWrites(); }")
        await pg.wait_for_timeout(300)
        await pg.reload()
        await pg.wait_for_timeout(2500)
        r = await pg.evaluate("""() => {
            const s = state.progress.sessions[0];
            return { linjer: s.log.length, forste: s.log[0].text,
                     ref: !!s.log[1].ref,
                     bar: !document.getElementById('quickbar').hidden }; }""")
        check("loggen er der fortsatt", r["linjer"], 2)
        check("med teksten", r["forste"], "Wang Ma funnet død på lugaren.")
        check("koblingen til raden også", r["ref"], True)
        check("og hurtiglinja står klar", r["bar"], True)

        await pg.evaluate("setView('stream')")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{OUT}/okta-logg.png", full_page=True)
        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{OUT}/sesjonslogg.png", full_page=True)

        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("\nRESULT:", "FAILED" if fails else "OK")
        await b.close()

asyncio.run(main())
