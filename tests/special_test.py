"""Funksjonstest av spesialreglene for skapninger.

Krever playwright og en Chromium (sett CHROMIUM_PATH om nødvendig):

    CHROMIUM_PATH=/sti/til/chromium python3 tests/special_test.py

Sjekker mekanismene som ikke lar seg lese ut av en statblokk: at en
flying polyp slår 2D6 for tentakler ved hvert rundeskifte, at hvert
tentakkelangrep bruker opp én av dem, at tentakkelskade går utenom
rustning, at vindstøtet bare kan brukes én gang per runde, at man kan
angripe tentaklene direkte, at regenerering slår inn mellom rundene,
og at skapninger som bare biter på visse våpen faktisk gjør det.
"""
import asyncio, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="special-")

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
        ctx = await b.new_context(viewport={"width": 1280, "height": 1300})
        errs = []
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.on("console", lambda m: errs.append("CONSOLE: " + m.text)
              if m.type == "error" and "ERR_CONNECTION" not in m.text else None)
        await pg.goto(URL)
        await pg.wait_for_timeout(2500)

        print("\n== reglene er koblet på riktig skapning ==")
        n = await pg.evaluate(
            "() => state.abilities ? state.abilities.entries.length : 0")
        check("spesialreglene er bygget inn", n > 0, True)
        hit = await pg.evaluate("""() => {
            const poly = specialFor({name: 'Flying Polyps'});
            const npc = specialFor({id: 'npc-flying-polyp', name: 'Flying Polyp'});
            const pc = specialFor({name: 'Walther'});
            return {poly: poly && poly.title, npc: npc && npc.title, pc: pc};
        }""")
        check("fiendebanken finner polyppen", hit["poly"], "Flying Polyp")
        check("scenarioets NPC finner den også", hit["npc"], "Flying Polyp")
        check("vanlige roller får ingen", hit["pc"], None)

        print("\n== tellere og angrep ==")
        chars = json.load(open(os.path.join(REPO, "characters.json")))
        await pg.evaluate("""async (l) => {
            state.characters = l.map(normalizeChar);
            await saveCharacters();
            state.combat = emptyCombat();
            const w = state.characters.find((c) => c.name === 'Walther');
            const poly = state.bestiary.creatures.find(
                (c) => /flying polyp/i.test(c.name));
            await addToCombat(w);
            await addToCombat(beastToChar(poly));
            state.combat.combatants.forEach((c, i) => { c.init = String(90 - i*20); });
            await saveCombat(); render();
        }""", chars)
        await pg.evaluate("setView('combat')")
        await pg.wait_for_timeout(500)

        setup = await pg.evaluate("""() => {
            const poly = state.combat.combatants.find((c) => /Polyp/i.test(c.name));
            return {
              abil: (poly.special.abilities || []).map((a) => a.id),
              atk: attacksOf(poly).map((a) => a.name),
              ignores: attacksOf(poly)[0].ignores_armor,
            };
        }""")
        check("polyppen har sine fire regler", setup["abil"],
              ["tentacles", "windblast", "fixing", "invisibility"])
        check("angrepslista er den norske, ikke statblokkas",
              setup["atk"], ["Tentakkel", "Vindstøt"])
        check("tentakkelen går utenom rustning", setup["ignores"], True)

        await pg.click("button:text-is('Start kamp')")
        await pg.wait_for_timeout(600)
        r1 = await pg.evaluate("""() => {
            const poly = state.combat.combatants.find((c) => /Polyp/i.test(c.name));
            return {t: poly.pools.tentacles,
                    logged: state.combat.log.some((l) => /Tentakler \\d+ \\(2D6\\)/.test(l))};
        }""")
        check("2D6 slås når kampen starter",
              r1["t"] >= 2 and r1["t"] <= 12, True)
        check("og skrives i loggen", r1["logged"], True)

        # En full runde skal slå på nytt.
        await pg.evaluate("() => advanceTurn()")
        await pg.wait_for_timeout(200)
        await pg.evaluate("() => advanceTurn()")
        await pg.wait_for_timeout(300)
        r2 = await pg.evaluate("""() => {
            const poly = state.combat.combatants.find((c) => /Polyp/i.test(c.name));
            return {round: state.combat.round, t: poly.pools.tentacles,
                    rolls: state.combat.log.filter((l) => /Tentakler \\d+ \\(2D6\\)/.test(l)).length};
        }""")
        check("ny runde", r2["round"], 2)
        check("tellerne slås på nytt hver runde", r2["rolls"], 2)
        check("innenfor 2D6", r2["t"] >= 2 and r2["t"] <= 12, True)

        print("\n== et tentakkelangrep bruker opp én tentakkel ==")
        await pg.evaluate("""() => {
            const i = state.combat.combatants.findIndex((c) => /Polyp/i.test(c.name));
            const cards = [...document.querySelectorAll('#main .combatant')];
            cards[i].querySelectorAll('.cb-attacks .chip.atk')[0].click();
        }""")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-body .pickrow')[0].click()")
        await pg.wait_for_timeout(400)
        skill = await pg.evaluate(
            "() => document.getElementById('flow-atk-skill').value")
        check("treffsjansen kommer fra regelen", skill, "85")
        before = await pg.evaluate("""() => ({
            t: state.combat.combatants.find((c) => /Polyp/i.test(c.name)).pools.tentacles,
            hp: state.combat.combatants.find((c) => c.kind === 'pc').hp,
        })""")
        await pg.fill("#flow-atk-roll", "10")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-foot .btn')[1].click()")
        await pg.wait_for_timeout(600)
        after = await pg.evaluate("""() => ({
            t: state.combat.combatants.find((c) => /Polyp/i.test(c.name)).pools.tentacles,
            hp: state.combat.combatants.find((c) => c.kind === 'pc').hp,
        })""")
        check("telleren går ned med én", after["t"], before["t"] - 1)
        check("og målet tar skade", after["hp"] < before["hp"], True)

        print("\n== vindstøtet er én gang per runde ==")
        await pg.evaluate("""() => {
            const i = state.combat.combatants.findIndex((c) => /Polyp/i.test(c.name));
            const cards = [...document.querySelectorAll('#main .combatant')];
            const chips = [...cards[i].querySelectorAll('.cb-attacks .chip.atk')];
            chips.find((x) => /Vindst/.test(x.textContent)).click();
        }""")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-body .pickrow')[0].click()")
        await pg.wait_for_timeout(300)
        await pg.fill("#flow-atk-roll", "10")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-foot .btn')[1].click()")
        await pg.wait_for_timeout(600)
        spent = await pg.evaluate("""() => {
            const poly = state.combat.combatants.find((c) => /Polyp/i.test(c.name));
            const wb = attacksOf(poly).find((a) => /Vindst/.test(a.name));
            return attackBudget(poly, wb);
        }""")
        check("vindstøtet er brukt opp", spent, 0)

        print("\n== å angripe tentaklene direkte ==")
        await pg.evaluate("""async () => {
            const poly = state.combat.combatants.find((c) => /Polyp/i.test(c.name));
            poly.pools.tentacles = 5; await saveCombat(); render();
        }""")
        await pg.wait_for_timeout(300)
        await pg.evaluate("""() => {
            const i = state.combat.combatants.findIndex((c) => c.kind === 'pc');
            const cards = [...document.querySelectorAll('#main .combatant')];
            cards[i].querySelector('.cb-attacks .btn').click();
        }""")
        await pg.wait_for_timeout(300)
        await pg.evaluate("""() => [...document.querySelectorAll('#modal-body .pickrow')]
            .find((r) => /Fra våpenlista/.test(r.textContent)).click()""")
        await pg.wait_for_timeout(300)
        await pg.evaluate("""() => [...document.querySelectorAll('#modal-body .pickrow')]
            .find((r) => /Colt M1911/.test(r.textContent)).click()""")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-body .pickrow')[0].click()")
        await pg.wait_for_timeout(400)
        rows = await pg.evaluate("""() => [...document.querySelectorAll('.respchips')]
            .map((r) => [...r.querySelectorAll('.chip')].map((c) => c.textContent))""")
        check("man kan velge hva man treffer", rows[0],
              ["Flying Polyps", "Tentakler (5)"])
        check("og hva slags skade det er", rows[1][0:3],
              ["Nærkamp", "Skytevåpen", "Hagle"])

        await pg.evaluate("""() => { const e = document.getElementById('flow-atk-skill');
            e.value = '60'; e.dispatchEvent(new Event('input')); }""")
        await pg.fill("#flow-atk-roll", "30")
        await pg.wait_for_timeout(300)
        gun = await pg.evaluate("""() => ({
            note: [...document.querySelectorAll('.dmgbox .caveat')]
                    .map((x) => x.textContent).join(' '),
        })""")
        check("kuler gjør minste mulige skade på en polyp",
              "minste mulige" in gun["note"], True)

        await pg.evaluate("""() => [...document.querySelectorAll('.chip.resp')]
            .find((x) => x.textContent === 'Ild').click()""")
        await pg.wait_for_timeout(300)
        fire = await pg.evaluate("""() => [...document.querySelectorAll('.dmgbox .caveat')]
            .map((x) => x.textContent).join(' ')""")
        check("ild gjør full skade", "minste mulige" in fire, False)

        await pg.evaluate("""() => [...document.querySelectorAll('.chip.resp')]
            .find((x) => /Tentakler/.test(x.textContent)).click()""")
        await pg.wait_for_timeout(300)
        part = await pg.evaluate("""() => ({
            head: document.querySelector('.verdict-head').textContent,
            dmg: !!document.querySelector('.dmgnum'),
        })""")
        check("et treff river av en tentakkel", "river av en tentakkel" in part["head"], True)
        check("og gjør ingen skade på HP", part["dmg"], False)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-foot .btn')[1].click()")
        await pg.wait_for_timeout(600)
        torn = await pg.evaluate("""() => {
            const poly = state.combat.combatants.find((c) => /Polyp/i.test(c.name));
            return {t: poly.pools.tentacles, hp: poly.hp};
        }""")
        check("telleren gikk fra 5 til 4", torn["t"], 4)
        check("HP-en står urørt", torn["hp"], 38)
        await pg.screenshot(path=f"{OUT}/polyp.png", full_page=True)

        print("\n== hvilke våpen som biter ==")
        co = await pg.evaluate("""() => {
            const c = {special: specialFor({name: 'Crawling Ones'})};
            const gun = {name: 'Colt', damage: '1D10+2', category: 'firearms'};
            const sg = {name: 'Hagle', damage: '4D6', category: 'firearms',
                        subcategory: 'shotgun'};
            const knife = {name: 'Kniv', damage: '1D6', category: 'melee'};
            const f = (a, src, imp) => filterDamage(c, a, src,
                {total: 99, impaled: !!imp}).amount;
            return {gun: f(gun, 'firearm'), shotgun: f(sg, 'shotgun'),
                    knife: f(knife, 'melee'), magic: f(knife, 'magic')};
        }""")
        check("kuler gjør ett poeng mot en crawling one", co["gun"], 1)
        check("hagle gjør minste mulige (4D6 = 4)", co["shotgun"], 4)
        check("nærkamp gjør minste mulige (1D6 = 1)", co["knife"], 1)
        check("formler gjør full skade", co["magic"], 99)

        ds = await pg.evaluate("""() => {
            const c = {special: specialFor({name: 'Dark Sargassum'})};
            const gun = {name: 'Rifle', damage: '2D6+4', category: 'firearms'};
            const f = (a, src, imp) => filterDamage(c, a, src,
                {total: 30, impaled: !!imp}).amount;
            return {plain: f(gun, 'firearm'), impale: f(gun, 'firearm', true),
                    fire: f(gun, 'fire'), melee: f({damage:'1D6'}, 'melee')};
        }""")
        check("skytevåpen gjør 1 mot dark sargassum", ds["plain"], 1)
        check("en spidding gjør 2", ds["impale"], 2)
        check("ild gjør ingenting", ds["fire"], 0)
        check("nærkamp gjør full skade", ds["melee"], 30)

        print("\n== regenerering mellom rundene ==")
        regen = await pg.evaluate("""() => {
            const c = {name: 'Test', hp: 10, hpMax: 30, conditions: [],
                       special: specialFor({name: 'Star-spawn of Cthulhu'})};
            const lines = applyRegen(c);
            const dead = {name: 'Død', hp: 0, hpMax: 46, conditions: [],
                          special: specialFor({name: 'Chthonian Full Adults'})};
            const dl = applyRegen(dead);
            return {hp: c.hp, lines: lines.length,
                    deadHp: dead.hp, deadConds: dead.conditions, dl: dl.length};
        }""")
        check("star-spawn leger 3 HP", regen["hp"], 13)
        check("og sier fra i loggen", regen["lines"], 1)
        check("en chthonian på null leger seg ikke", regen["deadHp"], 0)
        check("den dør i stedet", regen["deadConds"], ["Død"])

        print("\n== svake punkter ==")
        spot = await pg.evaluate("""() => {
            const e = specialFor({name: 'Dwellers In the Depths'});
            const nk = specialFor({name: 'Nioth-korghai'});
            return {
              dweller: e.abilities[0].chance,
              dwellerEffect: e.abilities[0].effect,
              nioth: nk.abilities[0].chance_of_skill,
            };
        }""")
        check("hjerneorganet er 10 %", spot["dweller"], 10)
        check("og dreper på stedet", spot["dwellerEffect"], "instant_death")
        check("solar plexus krever 10 % av egen ferdighet",
              spot["nioth"], 10)

        print("\n== alt overlever en omlasting ==")
        pg2 = await ctx.new_page()
        pg2.on("pageerror", lambda e: errs.append("PAGEERROR2: " + str(e)))
        await pg2.goto(URL)
        await pg2.wait_for_timeout(2500)
        rel = await pg2.evaluate("""() => {
            const poly = state.combat.combatants.find((c) => /Polyp/i.test(c.name));
            return {t: poly.pools.tentacles, abil: poly.special.abilities.length,
                    round: state.combat.round};
        }""")
        check("telleren står som den sto", rel["t"], 4)
        check("reglene er der fortsatt", rel["abil"], 4)
        check("runden er den samme", rel["round"], 2)

        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        await b.close()

    if fails or errs:
        print(f"\n{len(fails)} FAILURES")
        raise SystemExit(1)
    print("\nRESULT: OK")


asyncio.run(main())
