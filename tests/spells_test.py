"""Funksjonstest av formelbanken og formler brukt som angrep.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/spells_test.py

Poenget med formelfanen er at man ikke skal lete opp en formel for å
se hva som skal til for å kaste den. Derfor testes kostnaden: at den
vises, at den regnes mot kasterens magic points, at et nivå kan velges
når kostnaden varierer, og at resten tas fra hit points når magic
points er tomt — som er grunnbokas regel.
"""
import asyncio, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="spells-")

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

        chars = json.load(open(os.path.join(REPO, "characters.json"),
                               encoding="utf-8"))
        await pg.evaluate("""async (l) => { state.characters = l.map(normalizeChar);
            await saveCharacters(); render(); }""", chars)
        await pg.wait_for_timeout(400)

        print("\n== formelfanen ==")
        v = await pg.evaluate("""() => { setView('spells'); render();
            return {
              rader: document.querySelectorAll('#main .entry').length,
              grupper: [...document.querySelectorAll('#main .day-head h3')]
                         .map(x => x.textContent),
              ikamp: [...document.querySelectorAll('#main .entry-open')]
                       .filter(x => x.textContent === 'I KAMP').length,
            }; }""")
        print("  fanen:", v)
        check("alle formlene står der", v["rader"], 10)
        check("delt i skurkens og heltenes", v["grupper"],
              ["Skapningens formler", "Det heltene kan lære"])
        check("og de som kan brukes i kamp er merket", v["ikamp"], 7)

        card = await pg.evaluate("""() => {
            openSpell(spellIndex['spell-dominate']);
            return {
              sub: document.getElementById('modal-sub').textContent,
              felt: [...document.querySelectorAll('#modal-body .stat dt')]
                      .map(x => x.textContent),
            }; }""")
        check("kostnaden står i undertittelen", card["sub"],
              "1 magic point · 1 Sanity")
        check("og kortet sier hva som avgjør den",
              "Avgjøres av" in card["felt"], True)
        await pg.evaluate("closeAllModals()")

        print("\n== kostnaden regnes mot kasteren ==")
        mp = await pg.evaluate("""() => {
            const c = state.characters.find(x => /Crawling/.test(x.name));
            c.mp = '18';
            openSpell(spellIndex['spell-mindblast'], c);
            const box = document.querySelector('#modal-body .callout');
            return { klasse: box.className.trim(),
                     tekst: box.textContent.includes('nok til 10') }; }""")
        check("18 MP holder til Mindblast", mp["tekst"], True)
        check("og da er ruta ikke rød", mp["klasse"], "callout")
        await pg.evaluate("closeAllModals()")

        kort = await pg.evaluate("""() => {
            const c = state.characters.find(x => /Crawling/.test(x.name));
            c.mp = '4';
            openSpell(spellIndex['spell-mindblast'], c);
            const box = document.querySelector('#modal-body .callout');
            const r = { rod: box.className.includes('short'),
                        sier: box.textContent.includes('HIT POINTS') };
            c.mp = '18';
            return r; }""")
        check("4 MP er for lite, og ruta blir rød", kort["rod"], True)
        check("og den sier at resten tas fra hit points", kort["sier"], True)
        await pg.evaluate("closeAllModals()")

        print("\n== formler i angrepsmenyen ==")
        a = await pg.evaluate("""() => {
            const c = state.characters.find(x => /Crawling/.test(x.name));
            const cb = { name: c.name, charId: c.id, hp: 17, hpMax: 17 };
            state.combat = { combatants: [cb], round: 1, turn: 0,
                             active: true, log: [] };
            openAttackFlow(cb);
            return {
              seksjoner: [...document.querySelectorAll('#modal-body .section-label')]
                           .map(x => x.textContent),
              formler: [...document.querySelectorAll('#modal-body .entry-open')]
                         .filter(x => x.textContent === 'FORMEL').length,
            }; }""")
        print("  menyen:", a)
        check("Formler står som egen bolk", "Formler" in a["seksjoner"], True)
        # Skapningen har sju formler, men bare fire kan brukes i kamp.
        check("bare de som virker i kamp er med", a["formler"], 4)
        await pg.evaluate("closeAllModals()")

        print("\n== kostnaden trekkes, og går over på HP ==")
        niv = await pg.evaluate("""() => ({
            varierer: spellMpOptions(spellIndex['spell-mental-suggestion']),
            fast: spellMpOptions(spellIndex['spell-mindblast']) })""")
        check("en kostnad som varierer gir tre nivåer",
              niv["varierer"], [5, 10, 15])
        check("en fast kostnad gir ett", niv["fast"], [10])

        r = await pg.evaluate("""async () => {
            const c = state.characters.find(x => /Crawling/.test(x.name));
            c.mp = '18';
            const cb = state.combat.combatants[0];
            cb.hp = 17;
            await spendSpellCost(cb, spellIndex['spell-mental-suggestion'], 15);
            const etter = { mp: c.mp, hp: cb.hp };
            await spendSpellCost(cb, spellIndex['spell-mindblast']);
            return { etter, slutt: { mp: c.mp, hp: cb.hp },
                     logg: state.combat.log }; }""")
        check("15 av 18 trukket", r["etter"], {"mp": "3", "hp": 17})
        check("så 10 til: 3 MP igjen og 7 fra HP",
              r["slutt"], {"mp": "0", "hp": 10})
        check("og loggen sier hvorfor HP-en gikk",
              "magic points tok slutt" in r["logg"][-1], True)

        print("\n== våpenbanken dekker scenarioet ==")
        w = await pg.evaluate("""() => {
            const bank = (state.weapons && state.weapons.weapons) || [];
            const names = bank.map(x => x.name.toLowerCase());
            const mangler = [];
            [['.32', '32'], ['.44', '44'], ['nunchaku', 'nunchaku'],
             ['blåserør', 'blåserør'], ['brekkjern', 'brekkjern'],
             ['brannøks', 'brannøks'], ['saltsyre', 'saltsyre'],
             ['skipskanoner', 'skipskanoner']].forEach(([label, needle]) => {
               if (!names.some(n => n.includes(needle))) mangler.push(label);
             });
            return { antall: names.length, mangler }; }""")
        print("  våpen:", w)
        check("alt som er nevnt i scenarioet finnes", w["mangler"], [])
        check("banken har vokst", w["antall"] >= 37, True)

        await pg.evaluate("() => { setView('spells'); render(); }")
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=f"{OUT}/formler.png", full_page=True)
        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("\nRESULT:", "FAILED" if fails else "OK")
        await b.close()

asyncio.run(main())
