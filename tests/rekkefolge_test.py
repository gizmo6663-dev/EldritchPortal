"""Funksjonstest av historisk rekkefølge i loggen.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/rekkefolge_test.py

Feilen dette skal fange: man husker en hendelse for sent og logger den
etterpå, og da sto den etterpå i loggen også. Da kunne loggen si at
spillerne fant et lik i ballasttanken og deretter gikk om bord på
skipet. Loggen skal leses i den rekkefølgen ting skjedde, ikke i den
rekkefølgen de ble skrevet.

Her testes også at loggknappen finnes på alle radene og ikke bare i
Økta, at nå-pekeren fester nye linjer, og at alt kan rettes etterpå.
"""
import asyncio, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="rekkefolge-")

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

        print("\n== loggknappen finnes på alle radene ==")
        for view, navn in (("timeline", "Tidslinje"), ("beats", "Scener"),
                           ("clues", "Spor"), ("locations", "Steder"),
                           ("stream", "Økta")):
            n = await pg.evaluate("""(v) => { setView(v); render();
                return { rader: document.querySelectorAll('#main .entry').length,
                         logg: document.querySelectorAll('#main .logbtn').length
                }; }""", view)
            check(navn + " har en loggknapp per rad", n["logg"], n["rader"])
            check(navn + " har rader i det hele tatt", n["rader"] > 0, True)

        print("\n== den feilen du så ==")
        # To hendelser som ligger langt fra hverandre på tidslinja.
        ids = await pg.evaluate("""() => {
            const tl = state.scenario.timeline;
            return { forste: tl[0].id, forsteTittel: tl[0].title,
                     senere: tl[Math.floor(tl.length/2)].id,
                     senereTittel: tl[Math.floor(tl.length/2)].title,
                     antall: tl.length }; }""")
        print("  tidlig:", ids["forsteTittel"], "| senere:", ids["senereTittel"])

        r = await pg.evaluate("""async (ids) => {
            state.progress.sessions = [{ title: "Sesjon 1", date: "2026-09-13",
                                         summary: "", cast: [], log: [] }];
            // Først logges den SENERE hendelsen — man var à jour.
            await addLogEntry("Fant et lik i ballasttanken",
                              { anchor: ids.senere });
            // Så husker man den TIDLIGERE, og logger den etterpå.
            await addLogEntry("Spillerne gikk om bord",
                              { anchor: ids.forste });
            const log = state.progress.sessions[0].log;
            return {
              skrevet: log.map(e => e.text),
              historisk: storyOrder(log).map(e => e.text),
            }; }""", ids)
        check("skrevet i feil rekkefølge", r["skrevet"],
              ["Fant et lik i ballasttanken", "Spillerne gikk om bord"])
        check("men leses i riktig", r["historisk"],
              ["Spillerne gikk om bord", "Fant et lik i ballasttanken"])

        md = await pg.evaluate(
            "() => oneSessionMarkdown(state.progress.sessions[0])")
        check("og eksporten bruker den riktige",
              md.index("gikk om bord") < md.index("ballasttanken"), True)

        print("\n== linjer uten forankring havner bakerst ==")
        r = await pg.evaluate("""async (ids) => {
            await addLogEntry("Noe jeg ikke vet hvor hører hjemme", {});
            const log = state.progress.sessions[0].log;
            return storyOrder(log).map(e => e.text); }""", ids)
        check("den ukjente ligger sist",
              r[-1], "Noe jeg ikke vet hvor hører hjemme")
        check("og dytter ikke de andre ut av stilling",
              r[0], "Spillerne gikk om bord")

        print("\n== nå-pekeren fester det som logges ==")
        r = await pg.evaluate("""async (ids) => {
            await setNow(ids.senere);
            await addLogEntry("Skjedde mens vi sto her", {});
            const log = state.progress.sessions[0].log;
            const e = log[log.length - 1];
            return { anchor: e.anchor, knapp:
                       document.getElementById('quick-now').textContent }; }""",
            ids)
        check("linja arvet nå-pekeren", r["anchor"], ids["senere"])
        check("og knappen viser hvor vi er",
              r["knapp"].startswith("NÅ ·"), True)

        print("\n== en scene arver dagen sin fra tidslinja ==")
        r = await pg.evaluate("""() => {
            // Finn en tidslinjehendelse som peker på en scene.
            const tl = state.scenario.timeline;
            for (const t of tl) {
              for (const ref of (t.connects_to || [])) {
                const scene = (state.scenario.beats || [])
                  .find(x => x.id === ref);
                if (scene) return { tid: t.id, scene: scene.id,
                                    fant: storyAnchorFor(scene, 'beats') };
              }
            }
            return null; }""")
        check("scenen ble funnet", r is not None, True)
        if r:
            check("og den festes til hendelsen som peker på den",
                  r["fant"], r["tid"])

        print("\n== alt kan rettes etterpå ==")
        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => ({
            rader: document.querySelectorAll('#main .logrow').length,
            merker: document.querySelectorAll('#main .anchorchip').length,
            uten: document.querySelectorAll('#main .anchorchip.none').length,
            valg: [...document.querySelectorAll('#main .chip.resp')]
              .map(c => c.textContent) })""")
        check("alle linjene vises", r["rader"], 4)
        check("hver har en forankringsmerkelapp", r["merker"], 4)
        check("og den uforankrede er merket som det", r["uten"], 1)
        check("rekkefølgen kan velges",
              "Slik det skjedde" in r["valg"] and
              "Slik du skrev det" in r["valg"], True)

        rettet = await pg.evaluate("""async () => {
            // Trykk på teksten, rett den, trykk enter.
            const p = document.querySelector('#main .logrow p.clickable');
            const fra = p.textContent;
            p.click();
            await new Promise(r => setTimeout(r, 200));
            const felt = document.querySelector('#main .logedit');
            if (!felt) return { fant: false };
            felt.value = "Spillerne gikk om bord i San Francisco";
            felt.dispatchEvent(new KeyboardEvent('keydown',
              { key: 'Enter', bubbles: true }));
            await new Promise(r => setTimeout(r, 500));
            return { fant: true, fra: fra,
                     tekster: state.progress.sessions[0].log.map(e => e.text),
                     apen: !!document.querySelector('#main .logedit') }; }""")
        check("teksten kan redigeres ved å trykke på den", rettet["fant"], True)
        check("og den nye teksten er lagret",
              "Spillerne gikk om bord i San Francisco" in rettet["tekster"],
              True)
        check("feltet lukker seg etterpå", rettet["apen"], False)

        flyttet = await pg.evaluate("""async (ids) => {
            // Flytt den uforankrede linja til den første hendelsen.
            const chip = document.querySelector('#main .anchorchip.none');
            chip.click();
            await new Promise(r => setTimeout(r, 400));
            const valg = [...document.querySelectorAll('#modal-body .entry')]
              .find(e => e.textContent.includes(ids.forsteTittel));
            if (!valg) return { fant: false };
            valg.click();
            await new Promise(r => setTimeout(r, 500));
            const log = state.progress.sessions[0].log;
            const e = log.find(x => /ikke vet hvor/.test(x.text));
            return { fant: true, anchor: e.anchor,
                     uten: document.querySelectorAll(
                       '#main .anchorchip.none').length }; }""", ids)
        check("velgeren åpner seg fra merkelappen", flyttet["fant"], True)
        check("linja ble flyttet", flyttet["anchor"], ids["forste"])
        check("og ingen står uten sted lenger", flyttet["uten"], 0)

        slettet = await pg.evaluate("""async () => {
            // Slett nettopp den linja som var feil, ikke bare den
            // øverste — det er sånn man faktisk rydder.
            const for_ = state.progress.sessions[0].log.length;
            const rad = [...document.querySelectorAll('#main .logrow')]
              .find(r => /ikke vet hvor/.test(r.textContent));
            if (!rad) return { fant: false };
            rad.querySelector('.logdrop').click();
            await new Promise(r => setTimeout(r, 500));
            const igjen = state.progress.sessions[0].log.map(e => e.text);
            return { fant: true, for_: for_, etter: igjen.length,
                     borte: !igjen.some(t => /ikke vet hvor/.test(t)) }; }""")
        check("raden ble funnet", slettet["fant"], True)
        check("en feil linje kan slettes",
              slettet["etter"], slettet["for_"] - 1)
        check("og det er den man pekte på", slettet["borte"], True)

        print("\n== alt overlever en omlasting ==")
        await pg.evaluate("() => { flushWrites(); }")
        await pg.wait_for_timeout(300)
        await pg.reload()
        await pg.wait_for_timeout(2500)
        r = await pg.evaluate("""() => {
            const s = state.progress.sessions[0];
            return { linjer: s.log.length,
                     forankret: s.log.filter(e => e.anchor).length,
                     now: !!state.progress.now,
                     rekke: storyOrder(s.log).map(e => e.text) }; }""")
        check("loggen er der", r["linjer"], 3)
        check("forankringene også", r["forankret"], 3)
        check("nå-pekeren også", r["now"], True)
        check("og den tidligste hendelsen ligger først",
              "om bord" in r["rekke"][0], True)
        # Liket ble funnet senere i historien enn ombordstigningen, og
        # skal ligge etter den — uansett at det ble logget først.
        rekke = r["rekke"]
        ombord = [i for i, t in enumerate(rekke) if "om bord" in t][0]
        liket = [i for i, t in enumerate(rekke) if "ballasttanken" in t][0]
        check("med liket etterpå, slik det skjedde", liket > ombord, True)

        await pg.evaluate("setView('sessions')")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{OUT}/logg.png", full_page=True)
        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("\nRESULT:", "FAILED" if fails else "OK")
        await b.close()

asyncio.run(main())
