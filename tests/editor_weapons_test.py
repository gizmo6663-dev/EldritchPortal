"""Funksjonstest: gi en rolle våpen i editoren, og bruk dem i kamp.

Krever playwright og en Chromium (sett CHROMIUM_PATH om nødvendig):

    CHROMIUM_PATH=/sti/til/chromium python3 tests/editor_weapons_test.py

Sjekker at våpenvelgeren finnes for spillere, NPCer og fiender, at hele
statblokka følger med ut av editoren (kategori, magasin, feilgrense,
spidding), at treffsjansen fylles inn fra rollens egen ferdighet eller
fra et våpen av samme sort den alt har, og at våpenet dukker opp i
angrepsmenyen og regner riktig i en kamp.
"""
import asyncio, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="editor-")

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
        ctx = await b.new_context(viewport={"width": 1280, "height": 1200})
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
            state.combat = emptyCombat();
            await saveCombat(); render();
        }""", chars)
        await pg.evaluate("setView('characters')")
        await pg.wait_for_timeout(400)

        async def open_editor(name):
            await pg.evaluate(
                "(n) => editCharacter(state.characters.find((c) => c.name === n))",
                name)
            await pg.wait_for_timeout(400)

        async def add_weapon(match):
            await pg.evaluate(
                "() => document.getElementById('toggle-weapons').click()")
            await pg.wait_for_timeout(400)
            await pg.evaluate("""(m) => [...document.querySelectorAll('.weappanel .pickrow')]
                .find((r) => r.textContent.indexOf(m) !== -1).click()""", match)
            await pg.wait_for_timeout(300)

        async def save():
            await pg.evaluate("""() => [...document.querySelectorAll('#modal-foot .btn')]
                .find((b) => /Lagre|Opprett/.test(b.textContent)).click()""")
            await pg.wait_for_timeout(600)

        print("\n== velgeren finnes for alle tre typene ==")
        for name, kind in (("Franz", "pc"), ("Virginia Ridley", "npc"),
                           ("Zombie", "npc")):
            await open_editor(name)
            has = await pg.evaluate(
                "() => !!document.getElementById('toggle-weapons')")
            check("våpenvelger for " + name, has, True)
            await pg.evaluate("closeAllModals()")
            await pg.wait_for_timeout(200)

        print("\n== hele statblokka følger med ut av editoren ==")
        await open_editor("Virginia Ridley")
        await add_weapon("Avsaget hagle")
        await pg.screenshot(path=f"{OUT}/editor.png", full_page=True)
        await save()
        sg = await pg.evaluate("""() => {
            const c = state.characters.find((x) => x.name === 'Virginia Ridley');
            return c.attacks.find((a) => /Avsaget/.test(a.name));
        }""")
        check("våpenet er lagret", bool(sg), True)
        check("kategori", sg["category"], "firearms")
        check("underkategori", sg["subcategory"], "shotgun")
        check("skade", sg["damage"], "4D6 / 1D6")
        check("magasin", sg["ammo"], 2)
        check("feilgrense", sg["malfunction"], 100)
        check("kobling til våpenbanken", sg["weaponId"], "shotgun_sawed_off")
        # Virginia har ingen Firearms-ferdighet skrevet ned, men har alt
        # en hagle. Da skal den nye arve treffsjansen derfra.
        check("treffsjansen arves fra hagla hun har", sg["skill"], "75%")
        cls = await pg.evaluate("""(a) => ({ranged: isRangedAttack(a),
                                            src: damageSourceOf(a)})""", sg)
        check("regnes som avstandsvåpen", cls["ranged"], True)
        check("og som hagle", cls["src"], "shotgun")

        print("\n== treffsjansen hentes fra rollens egen ferdighet ==")
        await open_editor("Franz")
        await add_weapon("Kniv (stor)")
        await save()
        kn = await pg.evaluate("""() => {
            const c = state.characters.find((x) => x.name === 'Franz');
            return c.attacks.find((a) => /Kniv \\(stor\\)/.test(a.name));
        }""")
        check("kniven er lagret", bool(kn), True)
        check("med Franz' Fighting (Brawl)", kn["skill"], "65%")
        check("og spidder", kn["can_impale"], True)
        check("med halv damage bonus", kn["uses_db"], "half")

        print("\n== en fiende kan også få våpen ==")
        await pg.evaluate("""async () => {
            const g = state.bestiary.creatures.find((c) => /ghoul/i.test(c.name));
            await addBeastToRoster(g);
        }""")
        await pg.wait_for_timeout(600)
        await open_editor("Ghouls")
        await add_weapon("Kølle (stor)")
        await save()
        gh = await pg.evaluate("""() => {
            const c = state.characters.find((x) => x.name === 'Ghouls');
            return {kind: c.kind,
                    club: c.attacks.find((a) => /Kølle/.test(a.name))};
        }""")
        check("fienden er en fiende", gh["kind"], "enemy")
        check("køllen er lagret", bool(gh["club"]), True)
        check("treffsjansen arves fra klørne", gh["club"]["skill"], "30%")

        print("\n== og våpenet virker i kamp ==")
        await pg.evaluate("""async () => {
            const v = state.characters.find((c) => c.name === 'Virginia Ridley');
            await addToCombat(v);
            state.combat.active = true; state.combat.round = 1;
            await saveCombat(); render();
        }""")
        await pg.evaluate("setView('combat')")
        await pg.wait_for_timeout(500)
        await pg.evaluate("""() => document.querySelector('#main .cb-attacks .btn').click()""")
        await pg.wait_for_timeout(400)
        rows = await pg.evaluate(
            """() => [...document.querySelectorAll('#modal-body .pickrow .entry-title')]
                 .map((x) => x.textContent.trim())""")
        check("den nye hagla står i angrepsmenyen",
              any("Avsaget" in r for r in rows), True)
        check("og hele lista står fortsatt ikke oppe", len(rows) < 12, True)
        await pg.screenshot(path=f"{OUT}/meny.png", full_page=True)
        await pg.evaluate("closeAllModals()")

        print("\n== alt overlever en omlasting ==")
        pg2 = await ctx.new_page()
        pg2.on("pageerror", lambda e: errs.append("PAGEERROR2: " + str(e)))
        await pg2.goto(URL)
        await pg2.wait_for_timeout(2500)
        rel = await pg2.evaluate("""() => {
            const c = state.characters.find((x) => x.name === 'Virginia Ridley');
            const a = c.attacks.find((x) => /Avsaget/.test(x.name));
            return a ? {skill: a.skill, cat: a.category, ammo: a.ammo} : null;
        }""")
        check("våpenet er der etter omlasting",
              rel, {"skill": "75%", "cat": "firearms", "ammo": 2})

        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        await b.close()

    if fails or errs:
        print(f"\n{len(fails)} FAILURES")
        raise SystemExit(1)
    print("\nRESULT: OK")


asyncio.run(main())
