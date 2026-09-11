"""Funksjonstest av nettleserversjonen.

Krever playwright og en Chromium. Kjøres slik:

    python3 tests/web_test.py

Sjekker at avkryssinger, notater og biblioteket overlever at sida
lastes på nytt, at terningkasteren svarer, og at søket filtrerer.
"""
import asyncio
from playwright.async_api import async_playwright
import os
import json
URL = "file://" + os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "web", "index.html")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        ctx = await b.new_context(viewport={"width":1280,"height":900})
        errs=[]
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: "+str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1800)

        # tick one item in every flagged section + write notes
        await pg.evaluate("""async () => {
          for (const sec of ['clues','timeline','beats','locations','handouts']) {
            const items = state.scenario[sec] || [];
            if (items.length) await toggleFlag(items[0].id);
          }
          await setItemNote(state.scenario.npcs[0].id, 'Møtt i baren.');
          state.progress.notes = 'Notat fra test';
          await saveProgress();
        }""")
        await pg.wait_for_timeout(600)

        # reload in a NEW page of the same context (same localStorage)
        pg2 = await ctx.new_page()
        pg2.on("pageerror", lambda e: errs.append("PAGEERROR2: "+str(e)))
        await pg2.goto(URL); await pg2.wait_for_timeout(1800)
        res = await pg2.evaluate("""() => {
          const out = {};
          for (const sec of ['clues','timeline','beats','locations','handouts']) {
            const items = state.scenario[sec] || [];
            out[sec] = items.length ? !!items[0][FLAGS[sec]] : null;
          }
          out.npcNote = state.scenario.npcs[0].userNotes;
          out.notes = state.progress.notes;
          out.libCount = state.library.items.length;
          return out;
        }""")
        print("after reload:", res)
        ok = all(res[k] for k in ['clues','timeline','beats','locations','handouts']) \
             and res['npcNote'] and res['notes'] and res['libCount']==1
        # dice roller
        await pg2.fill("#dice-target","60")
        await pg2.click("#dice-roll")
        await pg2.wait_for_timeout(200)
        print("dice:", await pg2.inner_text("#dice-out"))
        # search
        await pg2.evaluate("setView('npcs')"); await pg2.wait_for_timeout(300)
        n = await pg2.evaluate("(()=>{state.query='polyp';render();return document.querySelectorAll('.entry').length;})()")
        print("npc search 'polyp' ->", n, "rows")
        # --- HALV OG FEMTEDEL OVERALT DER FERDIGHETER VISES
        steps=await pg.evaluate("""() => ({
            calc: [stepsLabel(65), stepsLabel('75%'), stepsLabel(25),
                   stepsLabel(0), stepsLabel('—')],
            text: annotateSkillText('Hide 30%, Track 35%'),
            already: annotateSkillText('Brawl 60% (30/12) skade 1D3'),
        })""")
        print("halv/femtedel:", steps)
        assert steps["calc"] == ["32/13", "37/15", "12/5", "", ""], steps
        assert steps["text"] == "Hide 30% (15/6), Track 35% (17/7)", steps
        assert steps["already"] == "Brawl 60% (30/12) skade 1D3", steps

        chars=json.load(open(os.path.join(REPO,"characters.json")))
        await pg.evaluate("""async (l) => {
            state.characters = l.map(normalizeChar);
            await saveCharacters(); render();
        }""", chars)
        await pg.evaluate("setView('characters')"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => openCharacter(state.characters.find(c=>c.name==='Franz'))")
        await pg.wait_for_timeout(400)
        card=await pg.evaluate("""() => ({
            stat: [...document.querySelectorAll('#modal-body .stat')]
                    .map((x) => x.textContent).find((t) => t.indexOf('STR') === 0),
            hp: [...document.querySelectorAll('#modal-body .stat')]
                    .map((x) => x.textContent).find((t) => t.indexOf('HP') === 0),
            skill: [...document.querySelectorAll('#modal-body table.skills tr')]
                    .map((x) => x.textContent).find((t) => /Fighting/.test(t)),
            legend: !!document.querySelector('#modal-body .steps-legend'),
        })""")
        print("karakterkort:", card)
        assert card["stat"] == "STR6532/13", card
        # HP slås det ikke mot — der skal tallparet ikke stå.
        assert card["hp"] == "HP18", card
        assert card["skill"] == "Fighting (Brawl)65%32/13", card
        assert card["legend"], card
        await pg.evaluate("closeAllModals()")

        # Fiendebankens kort: både angrepstabellen og ferdighetslinja
        await pg.evaluate("""() => openBeast(state.bestiary.creatures
            .find((c) => /flying polyp/i.test(c.name)))""")
        await pg.wait_for_timeout(400)
        beast=await pg.evaluate("""() => ({
            atk: [...document.querySelectorAll('#modal-body table.skills tr')]
                   .map((x) => x.textContent)[0],
            skills: [...document.querySelectorAll('#modal-body .prose')]
                   .map((x) => x.textContent).find((t) => /Hide/.test(t)),
        })""")
        print("fiendekort:", beast)
        assert "42/17" in beast["atk"], beast
        assert beast["skills"] == "Hide 30% (15/6), Track 35% (17/7)", beast
        await pg.evaluate("closeAllModals()")

        print("ERRORS:", errs or "none")
        print("PERSISTENCE:", "OK" if ok else "FAILED")
        await b.close()
asyncio.run(main())
