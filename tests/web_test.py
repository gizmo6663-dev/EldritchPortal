"""Funksjonstest av nettleserversjonen.

Krever playwright og en Chromium. Kjøres slik:

    python3 tests/web_test.py

Sjekker at avkryssinger, notater og biblioteket overlever at sida
lastes på nytt, at terningkasteren svarer, og at søket filtrerer.
"""
import asyncio
from playwright.async_api import async_playwright
import os
URL = "file://" + os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "web", "index.html")

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
        print("ERRORS:", errs or "none")
        print("PERSISTENCE:", "OK" if ok else "FAILED")
        await b.close()
asyncio.run(main())
