"""Funksjonstest av kampflyten: huk av deltakere, tast inn initiativ,
start kamp.

Krever playwright og en Chromium (sett CHROMIUM_PATH om nødvendig):

    CHROMIUM_PATH=/sti/til/chromium python3 tests/initiative_test.py

Sjekker at «+ Legg til» lar deg krysse av flere om gangen med antall,
at initiativ skrevet inn i feltet lagres, at lista IKKE sorteres mens
du skriver, at «Start kamp» setter rekkefølgen etter initiativ, og at
alt overlever en omlasting.
"""
import asyncio, os, json, tempfile
from playwright.async_api import async_playwright
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(REPO,"web","index.html")
# Skjermbilder er til øyekontroll, ikke noe som skal i repoet.
OUT=os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="initflow-")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        ctx = await b.new_context(viewport={"width":1280,"height":1000})
        errs=[]
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: "+str(e)))
        pg.on("console", lambda m: errs.append("CONSOLE: "+m.text) if m.type=="error" and "ERR_CONNECTION" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_timeout(2200)

        chars = json.load(open(os.path.join(REPO,"characters.json")))
        await pg.evaluate("""async (list) => {
            state.characters = list.map(normalizeChar);
            await saveCharacters();
            state.combat = emptyCombat(); await saveCombat();
            render();
        }""", chars)
        await pg.wait_for_timeout(400)

        await pg.evaluate("setView('combat')"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{OUT}/1-tom.png")

        # --- åpne "+ Legg til"
        await pg.click("button:has-text('+ Legg til')"); await pg.wait_for_timeout(500)
        n_rows = await pg.evaluate("() => document.querySelectorAll('.pickrow').length")
        print("rader i plukkelista:", n_rows)
        await pg.screenshot(path=f"{OUT}/2-dialog.png")

        # knappen skal være deaktivert før man huker av
        disabled = await pg.evaluate("() => document.querySelector('#modal-foot .btn.primary').disabled")
        print("knapp deaktivert før avkryssing:", disabled)

        # huk av 3 spillere
        await pg.evaluate("""() => {
            const rows = [...document.querySelectorAll('.pickrow')];
            rows.slice(0,3).forEach(r => r.click());
        }""")
        await pg.wait_for_timeout(300)
        label = await pg.evaluate("() => document.querySelector('#modal-foot .btn.primary').textContent")
        print("knappetekst etter 3:", label)

        # finn en ghoul i banken via søk og sett antall 3
        await pg.fill("#pick-search", "ghoul"); await pg.wait_for_timeout(500)
        await pg.evaluate("""() => {
            const rows = [...document.querySelectorAll('.pickrow')];
            const r = rows.find(x => x.textContent.indexOf('Ghoul') !== -1);
            if (r) { r.querySelector('.pickcount').value = '3';
                     r.querySelector('.pickcount').dispatchEvent(new Event('input',{bubbles:true}));
                     r.click(); }
        }""")
        await pg.wait_for_timeout(300)
        label2 = await pg.evaluate("() => document.querySelector('#modal-foot .btn.primary').textContent")
        print("knappetekst etter ghouls:", label2)
        await pg.screenshot(path=f"{OUT}/3-valgt.png")

        await pg.evaluate("() => document.querySelector('#modal-foot .btn.primary').click()")
        await pg.wait_for_timeout(700)
        names = await pg.evaluate("() => state.combat.combatants.map(c=>c.name)")
        print("i kampen:", names)

        # --- tast inn initiativ manuelt
        await pg.evaluate("""async () => {
            const vals = [72, 41, 95, 18, 60, 33];
            state.combat.combatants.forEach((c,i) => { c.init = String(vals[i % vals.length]); });
            await saveCombat(); render();
        }""")
        await pg.wait_for_timeout(400)
        before = await pg.evaluate("() => state.combat.combatants.map(c=>c.name+':'+c.init)")
        print("før start (urørt rekkefølge):", before)
        await pg.screenshot(path=f"{OUT}/4-initiativ.png")

        # skriv i ett felt gjennom UI-et for å sjekke at det lagres
        first_id = await pg.evaluate("() => state.combat.combatants[0].id")
        await pg.fill(f"#init-{first_id}", "88")
        await pg.wait_for_timeout(700)
        stored = await pg.evaluate("(id) => state.combat.combatants.find(c=>c.id===id).init", first_id)
        print("skrevet i feltet ->", stored)

        # --- start kamp: nå skal det sorteres
        await pg.click("button:text-is('Start kamp')"); await pg.wait_for_timeout(700)
        order = await pg.evaluate("() => state.combat.combatants.map(c=>c.name+':'+initiativeOf(c))")
        print("etter start (sortert):", order)
        nums = await pg.evaluate("() => state.combat.combatants.map(c=>initiativeOf(c))")
        sorted_ok = all(nums[i] >= nums[i+1] for i in range(len(nums)-1))
        print("synkende rekkefølge:", sorted_ok)
        await pg.screenshot(path=f"{OUT}/5-startet.png")

        log0 = await pg.evaluate("() => state.combat.log[0]")
        print("logg:", (log0 or "(tom)")[:110])

        # persistens
        pg2 = await ctx.new_page()
        pg2.on("pageerror", lambda e: errs.append("PAGEERROR2: "+str(e)))
        await pg2.goto(URL); await pg2.wait_for_timeout(2200)
        after = await pg2.evaluate("""() => ({
            n: state.combat.combatants.length,
            inits: state.combat.combatants.map(c=>c.init),
            active: state.combat.active,
        })""")
        print("etter reload:", after)

        mob = await ctx.new_page()
        await mob.set_viewport_size({"width":390,"height":844})
        await mob.goto(URL); await mob.wait_for_timeout(2000)
        await mob.evaluate("setView('combat')"); await mob.wait_for_timeout(400)
        await mob.screenshot(path=f"{OUT}/6-mobil.png")
        await mob.evaluate("() => addCombatantDialog()"); await mob.wait_for_timeout(500)
        await mob.screenshot(path=f"{OUT}/7-dialog-mobil.png")

        # Rekkefølgen skal være urørt fram til «Start kamp».
        untouched = before == ['Dagrun:72', 'Walther:41', 'Skjoldvår:95',
                               'Ghouls:18', 'Ghouls 2:60', 'Ghouls 3:33']
        ok = (len(names)==6 and sorted_ok and stored=="88" and untouched
              and after['n']==6 and after['active']
              and after['inits']==['95','88','60','41','33','18'])
        print("skjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("RESULT:", "OK" if ok else "FAILED")
        await b.close()
asyncio.run(main())
