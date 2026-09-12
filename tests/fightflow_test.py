"""Funksjonstest av angrepsflyten i kamp.

Krever playwright og en Chromium (sett CHROMIUM_PATH om nødvendig):

    CHROMIUM_PATH=/sti/til/chromium python3 tests/fightflow_test.py

Kjører en kamp slik en Keeper ville gjort det: velg angrep, velg mål,
skriv inn slaget fra bordet, la den som blir angrepet unnvike, slå
tilbake eller dykke i dekning, og se at skaden regnes ut og settes på
HP-en. Sjekker samtidig regelkjernen: suksessnivåer, fumlegrenser,
motsatte slag, og følgene av en skade for pulp-helter og alle andre.
"""
import asyncio, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="fightflow-")

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

        print("\n== regelkjernen ==")
        r = await pg.evaluate("""() => {
            const g = (roll, t) => gradeRoll(roll, t).label;
            return {
              crit: g(1, 70), extreme: g(14, 70), hard: g(35, 70),
              reg: g(70, 70), miss: g(71, 70),
              fumble100: g(100, 70), fumbleLow: g(96, 40), notFumble: g(96, 70),
              thr: thresholds(70),
            };
        }""")
        check("01 er kritisk", r["crit"], "KRITISK")
        check("<= verdi/5 er ekstrem", r["extreme"], "Ekstrem")
        check("<= verdi/2 er hard", r["hard"], "Hard")
        check("<= verdi er vanlig", r["reg"], "Suksess")
        check("over verdien er bom", r["miss"], "Bom")
        check("100 fumler alltid", r["fumble100"], "FUMLE")
        check("96 fumler under 50", r["fumbleLow"], "FUMLE")
        check("96 fumler ikke over 50", r["notFumble"], "Bom")
        check("grensene for 70%", r["thr"],
              {"extreme": 14, "hard": 35, "regular": 70, "fumble": 100})

        o = await pg.evaluate("""() => ({
            attHigher: opposedOutcome(gradeRoll(10,70), gradeRoll(60,70)).winner,
            defHigher: opposedOutcome(gradeRoll(60,70), gradeRoll(10,70)).winner,
            tieBestSkill: opposedOutcome(gradeRoll(60,70), gradeRoll(40,50)).winner,
            tieDefSkill: opposedOutcome(gradeRoll(40,50), gradeRoll(60,70)).winner,
            draw: opposedOutcome(gradeRoll(60,70), gradeRoll(65,70)).winner,
            attFailed: opposedOutcome(gradeRoll(90,70), null).winner,
            noDefence: opposedOutcome(gradeRoll(60,70), null).winner,
        })""")
        check("høyest nivå vinner (angriper)", o["attHigher"], "attacker")
        check("høyest nivå vinner (forsvarer)", o["defHigher"], "defender")
        check("likt nivå: høyest ferdighet", o["tieBestSkill"], "attacker")
        check("likt nivå: høyest ferdighet (def)", o["tieDefSkill"], "defender")
        check("likt nivå og lik ferdighet er uavgjort", o["draw"], "draw")
        check("bom er bom", o["attFailed"], "attacker-failed")
        check("uten forsvar treffer suksess", o["noDefence"], "attacker")

        w = await pg.evaluate("""() => ({
            pulpDead: woundOutcome({hp:20,hpMax:20,pulp:true}, 20).conditions,
            pulpDying: woundOutcome({hp:9,hpMax:20,pulp:true}, 10).conditions,
            pulpNoMajor: woundOutcome({hp:20,hpMax:20,pulp:true}, 10).major,
            normMajor: woundOutcome({hp:11,hpMax:11,pulp:false}, 6).conditions,
            normUnder: woundOutcome({hp:11,hpMax:11,pulp:false}, 5).conditions,
            normDead: woundOutcome({hp:11,hpMax:11,pulp:false}, 11).conditions,
            normDying: woundOutcome({hp:5,hpMax:11,pulp:false}, 6).conditions,
            armor: armorValue({armor:'4-point hide'}),
        })""")
        check("maks HP i ett slag dreper", w["pulpDead"], ["Død"])
        check("pulp-helt på null er døende", w["pulpDying"], ["Døende"])
        check("pulp-helter tar ikke major wound", w["pulpNoMajor"], False)
        check("halve maks HP er major wound", w["normMajor"], ["Major wound"])
        check("under halve er det ikke", w["normUnder"], [])
        check("maks HP dreper også andre", w["normDead"], ["Død"])
        check("major wound til null er døende", w["normDying"],
              ["Major wound", "Døende"])
        check("rustning leses ut av teksten", w["armor"], 4)

        print("\n== en kamp kjørt gjennom skjermen ==")
        chars = json.load(open(os.path.join(REPO, "characters.json")))
        await pg.evaluate("""async (l) => {
            state.characters = l.map(normalizeChar);
            await saveCharacters();
            state.combat = emptyCombat();
            const w = state.characters.find((c) => c.name === 'Walther');
            const g = state.bestiary.creatures.find((c) => /ghoul/i.test(c.name));
            await addToCombat(w);
            await addToCombat(beastToChar(g));
            state.combat.combatants.forEach((c, i) => { c.init = String(90 - i*20); });
            state.combat.active = true; state.combat.round = 1;
            await saveCombat(); render();
        }""", chars)
        await pg.evaluate("setView('combat')")
        await pg.wait_for_timeout(500)

        async def depth():
            return await pg.evaluate("() => modalStack.length")

        async def head():
            return await pg.evaluate("""() => document.querySelector('.verdict-head')
                ? document.querySelector('.verdict-head').textContent : null""")

        async def open_flow(pick):
            await pg.evaluate(
                "() => [...document.querySelectorAll('#main .cb-attacks .btn')][0].click()")
            await pg.wait_for_timeout(300)
            await pg.evaluate("""(t) => [...document.querySelectorAll('#modal-body .pickrow')]
                .find((r) => r.textContent.indexOf(t) !== -1).click()""", pick)
            await pg.wait_for_timeout(300)

        print("\n== angrepsmenyen viser rollens egne våpen ==")
        await pg.evaluate("""() => {
            const i = state.combat.combatants.findIndex((c) => c.kind === 'pc');
            [...document.querySelectorAll('#main .combatant')][i]
              .querySelector('.cb-attacks .btn').click();
        }""")
        await pg.wait_for_timeout(400)
        menu = await pg.evaluate("""() => ({
            labels: [...document.querySelectorAll('#modal-body .section-label')]
                      .map((x) => x.textContent),
            rows: [...document.querySelectorAll('#modal-body .pickrow .entry-title')]
                    .map((x) => x.textContent.trim()),
        })""")
        check("menyen er delt i rollens egne og resten", menu["labels"],
              ["Våpen og angrep", "Annet"])
        check("hele våpenlista står ikke oppe",
              len(menu["rows"]) < 12, True)
        check("men kan hentes fram",
              "Plukk opp et annet våpen" in menu["rows"], True)
        own = await pg.evaluate("""() => {
            const pc = state.combat.combatants.find((c) => c.kind === 'pc');
            return attacksOf(pc).map((a) => a.name);
        }""")
        check("radene er rollens egne angrep",
              menu["rows"][0:len(own)], own)
        await pg.evaluate("closeAllModals()")

        # «Plukk opp et annet våpen» skal gi hele våpenlista, til bruk
        # når noen griper noe som ligger der.
        await open_flow("Plukk opp et annet våpen")
        await pg.evaluate("""() => [...document.querySelectorAll('#modal-body .pickrow')]
            .find((r) => /Kniv/.test(r.textContent)).click()""")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-body .pickrow')[0].click()")
        await pg.wait_for_timeout(400)
        check("oppgjøret er fjerde nivå i modalstabelen", await depth(), 4)
        skill = await pg.evaluate(
            "() => document.getElementById('flow-atk-skill').value")
        check("treffsjansen hentes fra rollen", bool(skill), True)

        # 5 mot 50% er ekstrem suksess, og kniven spidder.
        await pg.fill("#flow-atk-roll", "5")
        await pg.wait_for_timeout(300)
        hit = await pg.evaluate("""() => ({
            head: document.querySelector('.verdict-head').textContent,
            impaled: /SPIDDET/.test(document.querySelector('.dmgbox').textContent),
            dmg: !!document.querySelector('.dmgnum'),
        })""")
        check("ekstrem suksess treffer", hit["head"], "Walther treffer")
        check("kniven spidder", hit["impaled"], True)
        await pg.screenshot(path=f"{OUT}/treff.png", full_page=True)

        # Kritisk motslag slår ekstrem: forsvareren treffer i stedet.
        await pg.evaluate("""() => [...document.querySelectorAll('.chip.resp')]
            .find((x) => /Slå tilbake/.test(x.textContent)).click()""")
        await pg.wait_for_timeout(300)
        await pg.fill("#flow-def-roll", "1")
        await pg.wait_for_timeout(300)
        check("kritisk motslag vinner", await head(),
              "Ghouls slår tilbake og treffer")
        victim = await pg.evaluate(
            "() => document.querySelector('.dmgnum').textContent")
        check("da er det angriperen som tar skaden",
              "Walther" in victim, True)
        await pg.screenshot(path=f"{OUT}/motslag.png", full_page=True)

        await pg.evaluate("""() => [...document.querySelectorAll('.chip.resp')]
            .find((x) => x.textContent === 'Unnvik').click()""")
        await pg.wait_for_timeout(300)
        await pg.fill("#flow-def-roll", "1")
        await pg.wait_for_timeout(300)
        check("unnvikelse stopper angrepet", await head(), "Ghouls unnviker")
        check("og gir ingen skade", await pg.evaluate(
            "() => !!document.querySelector('.dmgnum')"), False)

        # Uten forsvar går treffet igjennom, og skaden skal settes på HP.
        await pg.evaluate("""() => [...document.querySelectorAll('.chip.resp')]
            .find((x) => x.textContent === 'Ingenting').click()""")
        await pg.wait_for_timeout(300)
        before = await pg.evaluate(
            "() => state.combat.combatants.find((c) => /Ghoul/.test(c.name)).hp")
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-foot .btn')[1].click()")
        await pg.wait_for_timeout(600)
        after = await pg.evaluate("""() => ({
            hp: state.combat.combatants.find((c) => /Ghoul/.test(c.name)).hp,
            depth: modalStack.length,
            log: state.combat.log.length,
        })""")
        check("skaden settes på HP", after["hp"] < before, True)
        check("flyten lukkes etterpå", after["depth"], 0)
        check("og skrives i loggen", after["log"] > 0, True)

        print("\n== skytevåpen kan bare møtes med dekning ==")
        await open_flow("Plukk opp et annet våpen")
        await pg.evaluate("""() => [...document.querySelectorAll('#modal-body .pickrow')]
            .find((r) => /Colt M1911/.test(r.textContent)).click()""")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-body .pickrow')[0].click()")
        await pg.wait_for_timeout(400)
        resp = await pg.evaluate(
            "() => [...document.querySelectorAll('.chip.resp')].map((x) => x.textContent)")
        check("forsvarsvalgene mot skytevåpen", resp,
              ["Ingenting", "Dykk i dekning", "Unnvik likevel"])
        await pg.evaluate("""() => { const e = document.getElementById('flow-atk-skill');
            e.value = '60'; e.dispatchEvent(new Event('input')); }""")
        await pg.fill("#flow-atk-roll", "30")
        await pg.evaluate("""() => [...document.querySelectorAll('.chip.resp')]
            .find((x) => /Dykk/.test(x.textContent)).click()""")
        await pg.wait_for_timeout(200)
        await pg.fill("#flow-def-roll", "1")
        await pg.wait_for_timeout(300)
        # Unnvikelsen gikk, så appen skal be om en ekstra tierterning
        # i stedet for å la skuddet forsvinne.
        check("vellykket dekning ber om straffeterningen",
              await head(), "Skriv inn den ekstra tierterningen.")
        pen = await pg.evaluate(
            "() => [...document.querySelectorAll('.defroll')].pop().hidden")
        check("og feltet er synlig", pen, False)
        # Slaget var 30; tierterning 8 gjør det til 80, som bommer mot 60.
        await pg.evaluate("""() => { const e = [...document.querySelectorAll('.rollin')]
            .pop(); e.value = '8'; e.dispatchEvent(new Event('input')); }""")
        await pg.wait_for_timeout(300)
        check("straffeterningen får skuddet til å bomme",
              await head(), "Ghouls kommer seg unna")
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-foot .btn')[1].click()")
        await pg.wait_for_timeout(600)
        conds = await pg.evaluate(
            "() => state.combat.combatants.find((c) => /Ghoul/.test(c.name)).conditions")
        check("og koster neste angrep",
              "Mister neste angrep" in conds, True)

        print("\n== fumle og improvisert angrep ==")
        await open_flow("Plukk opp et annet våpen")
        await pg.evaluate("""() => [...document.querySelectorAll('#modal-body .pickrow')]
            .find((r) => /Kniv/.test(r.textContent)).click()""")
        await pg.wait_for_timeout(300)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-body .pickrow')[0].click()")
        await pg.wait_for_timeout(300)
        await pg.fill("#flow-atk-roll", "100")
        await pg.wait_for_timeout(300)
        check("100 fumler", await head(), "Walther fumler")
        check("fumling gir ingen skade", await pg.evaluate(
            "() => !!document.querySelector('.dmgnum')"), False)
        await pg.evaluate("closeAllModals()")

        await pg.evaluate("""async () => {
            const g = state.combat.combatants.find((c) => /Ghoul/.test(c.name));
            g.hp = g.hpMax; g.conditions = []; await saveCombat(); render();
        }""")
        await pg.wait_for_timeout(300)
        await open_flow("Improvisert")
        await pg.evaluate("""() => {
            document.getElementById('imp-name').value = 'Dampsleggen';
            document.getElementById('imp-skill').value = '70';
            document.getElementById('imp-damage').value = '20';
        }""")
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-foot .btn')[0].click()")
        await pg.wait_for_timeout(400)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-body .pickrow')[0].click()")
        await pg.wait_for_timeout(300)
        await pg.fill("#flow-atk-roll", "50")
        await pg.wait_for_timeout(300)
        note = await pg.evaluate("""() => [...document.querySelectorAll('.dmgbox .caveat')]
            .map((x) => x.textContent).join(" ")""")
        check("et slag over maks HP dreper", "død på stedet" in note, True)
        await pg.evaluate(
            "() => document.querySelectorAll('#modal-foot .btn')[1].click()")
        await pg.wait_for_timeout(600)
        dead = await pg.evaluate(
            "() => state.combat.combatants.find((c) => /Ghoul/.test(c.name))")
        check("og settes som tilstand", "Død" in dead["conditions"], True)
        check("med HP på null", dead["hp"], 0)
        await pg.screenshot(path=f"{OUT}/liste.png", full_page=True)

        # Dekningsdykk er IKKE et motsatt slag: en vellykket unnvikelse
        # gir angriperen én straffeterning, og skuddet slås fortsatt.
        print("\n== dykk i dekning ==")
        pen = await pg.evaluate("""() => ({
            ingen: withPenaltyTens(34, 8),
            bedre: withPenaltyTens(34, 1),
            hundre: withPenaltyTens(100, 0),
            nullEr100: withPenaltyTens(10, 0),
        })""")
        check("straffeterning tar det verste tier-resultatet", pen["ingen"], 84)
        check("og aldri det beste", pen["bedre"], 34)
        check("00 + 0 er 100", pen["nullEr100"], 100)
        check("100 er verst", pen["hundre"], 100)

        flow = await pg.evaluate("""() => {
            atkFlow = { attacker: {name:'A', build:1}, target: {name:'B', build:1},
                        attack: {name:'Skudd', damage:'1D6'}, ranged: true,
                        response: 'dive', penalised: true, penTens: '8',
                        effRoll: 84, part: 'body' };
            const a = gradeRoll(84, 60), d = gradeRoll(20, 40);
            const r = computeFlow(a, d);
            return { tone: r.tone, cond: r.conditions, dmg: !!r.damage,
                     head: r.headline };
        }""")
        check("bommet skudd etter straffeterning", flow["tone"], "miss")
        check("men dekningen koster angrepet",
              "Mister neste angrep" in flow["cond"], True)
        check("og ingen skade", flow["dmg"], False)

        hit = await pg.evaluate("""() => {
            atkFlow = { attacker: {name:'A', build:1}, target: {name:'B', build:1},
                        attack: {name:'Skudd', damage:'1D6'}, ranged: true,
                        response: 'dive', penalised: true, penTens: '1',
                        effRoll: 34, part: 'body' };
            const r = computeFlow(gradeRoll(34, 60), gradeRoll(20, 40));
            return { tone: r.tone, cond: r.conditions, dmg: !!r.damage };
        }""")
        check("skuddet treffer likevel om det går inn", hit["tone"], "hit")
        check("og dekningen koster fortsatt angrepet",
              "Mister neste angrep" in hit["cond"], True)
        check("med skade regnet ut", hit["dmg"], True)

        print("\n== alt overlever en omlasting ==")
        pg2 = await ctx.new_page()
        pg2.on("pageerror", lambda e: errs.append("PAGEERROR2: " + str(e)))
        await pg2.goto(URL)
        await pg2.wait_for_timeout(2500)
        rel = await pg2.evaluate("""() => {
            const g = state.combat.combatants.find((c) => /Ghoul/.test(c.name));
            return {hp: g.hp, conds: g.conditions, dodge: g.dodge,
                    pulp: state.combat.combatants.find((c) => c.kind === 'pc').pulp};
        }""")
        check("HP lagret", rel["hp"], 0)
        check("tilstand lagret", "Død" in rel["conds"], True)
        check("unnvikelse lagret", bool(rel["dodge"]), True)
        check("pulp-flagget lagret", rel["pulp"], True)

        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        await b.close()

    if fails or errs:
        print(f"\n{len(fails)} FAILURES")
        raise SystemExit(1)
    print("\nRESULT: OK")


asyncio.run(main())
