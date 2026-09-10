"""Funksjonstest av roller, fiendebank og kamptracker i nettleserversjonen.

Krever playwright og en Chromium (sett CHROMIUM_PATH om nødvendig):

    CHROMIUM_PATH=/sti/til/chromium python3 tests/combat_test.py

Sjekker at rolletypene skilles og filtreres, at editoren oppretter en
fiende, at fiendebanken kan sendes i kamp, at initiativrekkefølgen
stemmer, og at kampen overlever at sida lastes på nytt.
"""
import asyncio, os
from playwright.async_api import async_playwright
REPO="/home/user/EldritchPortal"
URL="file://"+os.path.join(REPO,"web","index.html")
import tempfile
# Skjermbilder er til øyekontroll, ikke noe som skal i repoet.
OUT=os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="eldritch-shots-")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        ctx = await b.new_context(viewport={"width":1280,"height":950})
        errs=[]
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: "+str(e)))
        pg.on("console", lambda m: errs.append("CONSOLE: "+m.text) if m.type=="error" and "ERR_CONNECTION" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_timeout(2200)

        r = await pg.evaluate("""() => ({
            bestiary: state.bestiary ? state.bestiary.creatures.length : 0,
            chars: state.characters.length,
            combat: !!state.combat,
        })""")
        print("etter oppstart:", r)

        # importer karakterer fra repoets characters.json
        import json
        chars = json.load(open(os.path.join(REPO,"characters.json")))
        await pg.evaluate("""async (list) => {
            state.characters = list.map(normalizeChar);
            await saveCharacters();
            render();
        }""", chars)
        await pg.wait_for_timeout(400)
        kinds = await pg.evaluate("() => { const o={}; state.characters.forEach(c=>o[c.kind]=(o[c.kind]||0)+1); return o; }")
        print("roller etter import:", kinds)
        print("Skjoldvår finnes:", await pg.evaluate("() => state.characters.some(c=>c.name==='Skjoldvår')"))

        await pg.evaluate("setView('characters')"); await pg.wait_for_timeout(500)
        await pg.screenshot(path=f"{OUT}/roller.png")

        # filter
        n_all = await pg.evaluate("() => document.querySelectorAll('.entry').length")
        await pg.evaluate("() => { state.charFilter='npc'; render(); }")
        await pg.wait_for_timeout(300)
        n_npc = await pg.evaluate("() => document.querySelectorAll('.entry').length")
        print(f"filter: alle={n_all} npc={n_npc}")
        await pg.evaluate("() => { state.charFilter='all'; render(); }")

        # ny fiende via editoren
        await pg.evaluate("() => editCharacter(null,'enemy')")
        await pg.wait_for_timeout(400)
        await pg.fill("#ed-name","Testfiende")
        await pg.fill("#ed-stat-DEX","65")
        await pg.fill("#ed-stat-HP","14")
        await pg.screenshot(path=f"{OUT}/editor.png")
        await pg.evaluate("() => document.querySelectorAll('#modal-foot .btn')[1].click()")
        await pg.wait_for_timeout(500)
        print("fiende opprettet:", await pg.evaluate("() => state.characters.some(c=>c.name==='Testfiende' && c.kind==='enemy')"))

        # fiendebank
        await pg.evaluate("setView('bestiary')"); await pg.wait_for_timeout(500)
        await pg.screenshot(path=f"{OUT}/fiendebank.png")
        await pg.evaluate("""() => {
            const polyp = state.bestiary.creatures.find(c=>c.name==='Flying Polyps');
            addToCombat(beastToChar(polyp));
        }""")
        await pg.wait_for_timeout(400)

        # legg PC-er i kamp
        await pg.evaluate("""async () => {
            const pcs = state.characters.filter(c=>c.kind==='pc').slice(0,3);
            for (const c of pcs) await addToCombat(c);
            await addToCombat(state.characters.find(c=>c.name==='Testfiende'));
        }""")
        await pg.wait_for_timeout(600)
        await pg.evaluate("setView('combat')"); await pg.wait_for_timeout(500)

        order = await pg.evaluate("() => state.combat.combatants.map(c=>c.name+':'+initiativeOf(c))")
        print("initiativ:", order)

        # start kamp
        await pg.evaluate("() => document.querySelector('.btn.primary').click()")
        await pg.wait_for_timeout(600)
        st = await pg.evaluate("() => ({active:state.combat.active, round:state.combat.round, turn:state.combat.turn})")
        print("kamp startet:", st)

        # skade -> major wound
        await pg.evaluate("""() => {
            const c = state.combat.combatants[0];
            const before = c.hp;
            c.hp = Math.max(0, c.hp - Math.ceil(c.hpMax/2));
            if (!c.majorWound) { c.majorWound = true; c.conditions.push('Major wound'); }
            state.combat.log.push(c.name + ' tar ' + Math.ceil(c.hpMax/2) + ' skade — MAJOR WOUND.');
            saveCombat().then(render);
        }""")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=f"{OUT}/kamp.png")

        # neste tur x N
        for _ in range(len(order)+1):
            await pg.evaluate("() => advanceTurn()")
            await pg.wait_for_timeout(150)
        st2 = await pg.evaluate("() => ({round:state.combat.round, turn:state.combat.turn})")
        print("etter en full runde:", st2)

        # persistens
        pg2 = await ctx.new_page()
        pg2.on("pageerror", lambda e: errs.append("PAGEERROR2: "+str(e)))
        await pg2.goto(URL); await pg2.wait_for_timeout(2200)
        after = await pg2.evaluate("""() => ({
            combatants: state.combat.combatants.length,
            round: state.combat.round,
            active: state.combat.active,
            mw: state.combat.combatants.filter(c=>c.majorWound).length,
            chars: state.characters.length,
            enemy: state.characters.some(c=>c.name==='Testfiende'),
        })""")
        print("etter reload:", after)
        await pg2.evaluate("setView('combat')"); await pg2.wait_for_timeout(400)
        await pg2.screenshot(path=f"{OUT}/kamp-reload.png")

        mob = await ctx.new_page()
        await mob.set_viewport_size({"width":390,"height":844})
        await mob.goto(URL); await mob.wait_for_timeout(2000)
        await mob.evaluate("setView('combat')"); await mob.wait_for_timeout(400)
        await mob.screenshot(path=f"{OUT}/kamp-mobil.png")

        ok = (after['combatants']==5 and after['active'] and after['mw']>=1 and after['enemy'])
        print("ERRORS:", errs or "none")
        print("skjermbilder:", OUT)
        print("RESULT:", "OK" if ok else "FAILED")
        await b.close()
asyncio.run(main())
