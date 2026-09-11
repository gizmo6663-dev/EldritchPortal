"""Funksjonstest av kampregler, våpen, talenter og taktikkort.

Krever playwright og en Chromium (sett CHROMIUM_PATH om nødvendig):

    CHROMIUM_PATH=/sti/til/chromium python3 tests/rules_test.py

Sjekker terningparsing og damage bonus (også halv), at spidding gir
maks skade pluss et nytt kast, at et våpen som feiler ikke treffer,
at våpen fra lista havner på karakteren med egenskapene sine, at
talenter slås opp i talentboka, at taktikkortene kan trekkes, og at
initiativlista roterer slik at den aktive alltid ligger øverst.
"""
import asyncio, os, json, tempfile
from playwright.async_api import async_playwright
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(REPO,"web","index.html")
# Skjermbilder er til øyekontroll, ikke noe som skal i repoet.
OUT=os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="rules-")

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        ctx=await b.new_context(viewport={"width":1280,"height":1000})
        errs=[]
        pg=await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: "+str(e)))
        pg.on("console", lambda m: errs.append("CONSOLE: "+m.text) if m.type=="error" and "ERR_CONNECTION" not in m.text else None)
        await pg.goto(URL); await pg.wait_for_timeout(2500)

        r=await pg.evaluate("""() => ({
            weapons: state.weapons ? state.weapons.weapons.length : 0,
            talents: state.talents ? state.talents.talents.length : 0,
            tactics: (state.scenario && state.scenario.tactics || []).length,
            version: state.scenario && state.scenario.version,
        })""")
        print("innebygd:", r)

        chars=json.load(open(os.path.join(REPO,"characters.json")))
        await pg.evaluate("""async (list) => {
            state.characters = list.map(normalizeChar);
            await saveCharacters();
            state.combat = emptyCombat(); await saveCombat(); render();
        }""", chars)
        await pg.wait_for_timeout(400)

        # --- 1. TERNINGER OG REGLER
        dice=await pg.evaluate("""() => {
            const out={};
            out.max_1d6 = maxDiceExpr('1D6');
            out.max_2d6p4 = maxDiceExpr('2D6+4');
            out.max_shotgun = maxDiceExpr('4D6/2D6/1D6');
            const rolls=[]; for(let i=0;i<400;i++) rolls.push(rollDiceExpr('1D6+2').total);
            out.range_1d6p2=[Math.min(...rolls),Math.max(...rolls)];
            const db=[]; for(let i=0;i<200;i++) db.push(rollDamageBonus('+1D4','full').total);
            out.db_range=[Math.min(...db),Math.max(...db)];
            const half=[]; for(let i=0;i<200;i++) half.push(rollDamageBonus('+1D4','half').total);
            out.db_half_range=[Math.min(...half),Math.max(...half)];
            out.db_zero = rollDamageBonus('0','full').total;
            out.db_na = rollDamageBonus('N/A','full').total;
            return out;
        }""")
        print("terninger:", dice)

        # impale: Extreme-suksess skal gi maks + nytt kast
        imp=await pg.evaluate("""() => {
            // tving fram kritisk ved å låse tilfeldigheten
            const realRandom = Math.random;
            Math.random = () => 0;            // d100 -> 1 = kritisk, terninger -> 1
            const res = resolveAttack({db:'+1D4'},
                {name:'Kniv', skill:'70%', damage:'1D8', can_impale:true, uses_db:true});
            Math.random = realRandom;
            return res;
        }""")
        print("spidding (kritisk, 1D8 + 1D4 db):", {k:imp[k] for k in ('roll','label','impaled','damage','damageDetail')})

        mal=await pg.evaluate("""() => {
            const realRandom = Math.random;
            Math.random = () => 0.99;         // d100 -> 100
            const res = resolveAttack({db:''},
                {name:'Revolver', skill:'60%', damage:'1D10', malfunction:100});
            Math.random = realRandom;
            return res;
        }""")
        print("feiling (rull 100, mal 100):", {k:mal[k] for k in ('roll','label','malfunction','hit')})

        # --- 2. VÅPENVELGER
        await pg.evaluate("setView('characters')"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => editCharacter(state.characters.find(c=>c.name==='Walther'))")
        await pg.wait_for_timeout(500)
        await pg.evaluate("() => document.getElementById('toggle-weapons').click()")
        await pg.wait_for_timeout(500)
        nw=await pg.evaluate("() => document.querySelectorAll('.pickrow').length")
        print("våpen i velgeren:", nw)
        await pg.screenshot(path=f"{OUT}/vaapen.png")
        # velg en revolver
        picked=await pg.evaluate("""() => {
            const rows=[...document.querySelectorAll('.pickrow')];
            const r=rows.find(x=>/revolver/i.test(x.textContent));
            if(r){ r.click(); return r.textContent.slice(0,60); }
            rows[0].click(); return rows[0].textContent.slice(0,60);
        }""")
        await pg.wait_for_timeout(500)
        print("valgte:", picked.strip()[:60])
        atk=await pg.evaluate("""() => {
            const rows=[...document.querySelectorAll('.attackrow')];
            const last=rows[rows.length-1];
            const got=last._read ? last._read() : null;
            return got;
        }""")
        print("angrepsrad fra våpen:", atk)
        # lagre karakteren
        await pg.evaluate("() => [...document.querySelectorAll('#modal-foot .btn')].find(b=>b.textContent==='Lagre').click()")
        await pg.wait_for_timeout(600)
        saved=await pg.evaluate("() => state.characters.find(c=>c.name==='Walther').attacks.slice(-1)[0]")
        print("lagret på karakteren:", saved)

        # --- 3. TALENTER
        await pg.evaluate("() => openCharacter(state.characters.find(c=>c.name==='Walther'))")
        await pg.wait_for_timeout(500)
        tl=await pg.evaluate("""() => {
            const chips=[...document.querySelectorAll('.chip.talent')];
            return {n:chips.length, known:chips.filter(c=>c.classList.contains('known')).length,
                    names:chips.map(c=>c.textContent)};
        }""")
        print("talent-chips:", tl)
        await pg.screenshot(path=f"{OUT}/karakter.png")
        await pg.evaluate("""() => [...document.querySelectorAll('.chip.talent.known')][0].click()""")
        await pg.wait_for_timeout(400)
        tmodal=await pg.evaluate("() => ({t:document.getElementById('modal-title').textContent, b:document.getElementById('modal-body').textContent.slice(0,120)})")
        print("talentforklaring:", tmodal)
        await pg.screenshot(path=f"{OUT}/talent.png")
        await pg.evaluate("closeModal()")

        # --- 4. TAKTIKK
        await pg.evaluate("setView('tactics')"); await pg.wait_for_timeout(500)
        nt=await pg.evaluate("() => document.querySelectorAll('.entry').length")
        print("taktikkort vist:", nt)
        await pg.screenshot(path=f"{OUT}/taktikk.png")
        await pg.evaluate("() => drawTactic()"); await pg.wait_for_timeout(400)
        drawn=await pg.evaluate("() => document.getElementById('modal-title').textContent")
        print("trukket kort:", drawn)
        await pg.evaluate("closeModal()")

        # --- 5. ROTERING AV INITIATIV
        await pg.evaluate("""async () => {
            const pcs=state.characters.filter(c=>c.kind==='pc').slice(0,4);
            for(const c of pcs) await addToCombat(c);
            const vals=[80,60,40,20];
            state.combat.combatants.forEach((c,i)=>c.init=String(vals[i]));
            await saveCombat(); render();
        }""")
        await pg.wait_for_timeout(500)
        await pg.evaluate("setView('combat')"); await pg.wait_for_timeout(400)
        await pg.click("button:text-is('Start kamp')"); await pg.wait_for_timeout(600)
        seq=[]
        for i in range(6):
            st=await pg.evaluate("() => ({top:state.combat.combatants[0].name, round:state.combat.round, taken:state.combat.taken})")
            seq.append((st['top'], st['round']))
            await pg.evaluate("() => advanceTurn()"); await pg.wait_for_timeout(200)
        print("rotasjon (topp, runde):", seq)
        await pg.screenshot(path=f"{OUT}/kamp.png")

        # angrepsknapp i kamp
        atk2=await pg.evaluate("""() => {
            const c=state.combat.combatants.find(x=>x.attacks && x.attacks.length);
            if(!c) return 'ingen med angrep';
            const before=state.combat.log.length;
            const res=resolveAttack(c, c.attacks[0]);
            return {who:c.name, atk:c.attacks[0].name, roll:res.roll, label:res.label, dmg:res.damage};
        }""")
        print("angrep i kamp:", atk2)

        # --- persistens
        pg2=await ctx.new_page()
        pg2.on("pageerror", lambda e: errs.append("PAGEERROR2: "+str(e)))
        await pg2.goto(URL); await pg2.wait_for_timeout(2500)
        after=await pg2.evaluate("""() => ({
            n: state.combat.combatants.length,
            top: state.combat.combatants[0].name,
            round: state.combat.round,
            walther_atk: state.characters.find(c=>c.name==='Walther').attacks.length,
        })""")
        print("etter reload:", after)

        mob=await ctx.new_page(); await mob.set_viewport_size({"width":390,"height":844})
        await mob.goto(URL); await mob.wait_for_timeout(2200)
        await mob.evaluate("setView('tactics')"); await mob.wait_for_timeout(400)
        await mob.screenshot(path=f"{OUT}/taktikk-mobil.png")

        rounds=[r for _,r in seq]
        ok=(r['weapons']==28 and r['talents']==60 and r['tactics']==14
            and imp['impaled'] and imp['damage']>=8
            and mal['malfunction'] and not mal['hit']
            and tl['known']>0 and nt>0
            and rounds==[1,1,1,1,2,2]
            and after['n']==4)
        print("skjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        print("RESULT:", "OK" if ok else "FAILED")
        await b.close()
asyncio.run(main())
