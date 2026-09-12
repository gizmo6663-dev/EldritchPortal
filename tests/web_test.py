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
        # --- REGELBOKSER OG FERDIGHETSOPPSLAG
        banks=await pg.evaluate("""() => ({
            keeper: state.keeperRules ? state.keeperRules.rules.length : 0,
            talent: state.talentRules ? state.talentRules.rules.length : 0,
            skills: state.skillBook ? state.skillBook.skills.length : 0,
            unsourced: [state.keeperRules, state.talentRules]
              .filter(Boolean)
              .reduce((a,bank)=>a.concat((bank.rules||[])
                .reduce((b,r)=>b.concat((r.sections||[])
                  .filter(s=>!s.source).map(s=>r.id+': '+s.title)), [])), []),
            badtag: [state.keeperRules, state.talentRules]
              .filter(Boolean)
              .reduce((a,bank)=>a.concat((bank.rules||[])
                .reduce((b,r)=>b.concat((r.sections||[])
                  .map(s=>s.source).filter(s=>String(s).split('+')
                    .map(x=>x.trim()).some(x=>
                      ['grunnbok','pulp','scenario','eget'].indexOf(x)===-1))
                  .map(s=>r.id+': '+s)), [])), []),
            ids: (state.keeperRules ? state.keeperRules.rules : []).map(r=>r.id),
            unchecked: [state.keeperRules, state.talentRules]
              .filter(Boolean)
              .reduce((a,bank)=>a.concat((bank.rules||[])
                .filter(r=>/ikke kontrollert/.test(r.source||''))
                .map(r=>r.id)), []),
        })""")
        print("regelbanker:", banks)
        assert banks["keeper"] >= 6, banks
        # Jaktreglene og sårreglene er de to oppslagene man ellers
        # må bla etter midt i en økt.
        for need in ("chases", "wounds", "insanity", "spells", "villain-luck"):
            assert need in banks["ids"], (need, banks["ids"])
        # Begge regelbøkene finnes som tekst nå, så ingen boks skal
        # fortsatt påstå at kilden ikke er kontrollert.
        assert not banks["unchecked"], banks["unchecked"]
        assert banks["skills"] >= 50, banks
        # Hver seksjon må si hvilken bok den kommer fra, med et av de
        # fire merkene — ellers vises ingen kilde i regelboksen.
        assert not banks["unsourced"], banks
        assert not banks["badtag"], banks

        # --- SPOR SOM PEKER FEIL VEI
        await pg.evaluate("setView('clues')"); await pg.wait_for_timeout(400)
        cl = await pg.evaluate("""() => {
            const c = state.scenario.clues || [];
            return {
              n: c.length,
              utenRetning: c.filter(x => !x.points).map(x => x.id),
              utenSannhet: c.filter(x => x.points && x.points !== 'sant'
                                         && !x.truth).map(x => x.id),
              villspor: c.filter(x => x.points === 'villspor').length,
              delvis: c.filter(x => x.points === 'delvis').length,
              merker: [...document.querySelectorAll('#main .pointtag')].length,
            };
        }""")
        print("spor:", cl)
        # Hvert spor må si hvilken vei det peker, og alt som peker feil
        # må si hva det egentlig er — ellers er merkingen verdiløs.
        assert not cl["utenRetning"], cl["utenRetning"]
        assert not cl["utenSannhet"], cl["utenSannhet"]
        assert cl["villspor"] >= 8, cl
        assert cl["delvis"] >= 4, cl
        assert cl["merker"] == cl["villspor"] + cl["delvis"], cl

        # Filteret skal kunne isolere villsporene.
        only = await pg.evaluate("""() => { state.cluePoints = 'villspor';
            render();
            return [...document.querySelectorAll('#main .entry-title')]
                     .map(x => x.textContent).length; }""")
        await pg.wait_for_timeout(250)
        print("filtrert til villspor ->", only, "rader")
        assert only == cl["villspor"], (only, cl)
        await pg.evaluate("() => { state.cluePoints = 'alle'; render(); }")

        # Sannheten bak et villspor skal stå i kortet, ikke bare i dataene.
        box = await pg.evaluate("""() => {
            const c = state.scenario.clues.find(x => x.points === 'villspor');
            openItem(c, 'clues');
            const m = document.querySelector('#modal-body .misdirect');
            return m ? m.textContent.slice(0, 40) : null; }""")
        await pg.wait_for_timeout(250)
        print("villspor-ramme:", box)
        assert box and "Villspor" in box, box
        await pg.evaluate("closeAllModals()")

        await pg.evaluate("setView('reference')"); await pg.wait_for_timeout(500)
        ref=await pg.evaluate("""() => ({
            groups: [...document.querySelectorAll('#main .day-head h3')]
                      .map(x=>x.textContent),
            boxes: [...document.querySelectorAll('#main .pickrow .entry-title')]
                      .map(x=>x.textContent),
        })""")
        print("regelfanen:", ref["groups"])
        assert ref["groups"] == ["Dette scenarioet", "Regelbok", "Ferdigheter"], ref
        for t in ("Galskap — når Sanity ryker", "Formlene i dette scenarioet",
                  "Vann, drukning og et skip som synker"):
            assert t in ref["boxes"], (t, ref["boxes"])

        # Søk skal nå også finne formler og ferdigheter.
        for q, want in (("dominate", "Formlene i dette scenarioet"),
                        ("drukne", "Vann, drukning og et skip som synker"),
                        ("bevegelsespoeng", "Jakt — når noen stikker av"),
                        ("døende", "Sår, døende og førstehjelp"),
                        ("mook", "Skurkens Luck, og mooks"),
                        ("psychology", "Psychology")):
            await pg.evaluate("(q) => { state.query = q; render(); }", q)
            await pg.wait_for_timeout(250)
            rows=await pg.evaluate(
                "() => [...document.querySelectorAll('#main .entry-title')].map(x=>x.textContent)")
            assert want in rows, (q, rows)
            print(f"  søk «{q}» -> {want}")
        await pg.evaluate("() => { state.query=''; render(); }")

        # Ferdighetsnavnene på et karakterkort skal være klikkbare.
        chars2=json.load(open(os.path.join(REPO,"characters.json")))
        await pg.evaluate("""async (l) => { state.characters = l.map(normalizeChar);
            await saveCharacters(); render(); }""", chars2)
        unlinked=await pg.evaluate("""(l) => { const out=[];
            l.map(normalizeChar).forEach(c => {
              Object.keys(c.skills||{}).forEach(k => {
                if (!lookupSkill(k)) out.push(c.name + ' :: ' + k); });
            }); return [...new Set(out)]; }""", chars2)
        print("ferdigheter uten oppslag:", unlinked or "ingen")
        assert not unlinked, unlinked

        await pg.evaluate("setView('characters')"); await pg.wait_for_timeout(300)
        await pg.evaluate("() => openCharacter(state.characters.find(c=>c.name==='Franz'))")
        await pg.wait_for_timeout(300)
        await pg.evaluate("""() => [...document.querySelectorAll('#modal-body .skilllink')]
            .find(x=>/Stealth/.test(x.textContent)).click()""")
        await pg.wait_for_timeout(300)
        sk=await pg.evaluate("""() => ({
            title: document.getElementById('modal-title').firstChild.textContent,
            sub: document.getElementById('modal-sub').textContent,
            depth: modalStack.length })""")
        print("ferdighetsoppslag fra kortet:", sk)
        assert sk["title"] == "Stealth" and sk["depth"] == 2, sk
        assert "20%" in sk["sub"], sk
        await pg.evaluate("closeAllModals()")

        # --- REPLIKKER OG ROLLESPILL I SCENENE
        d=await pg.evaluate("""() => { const b=state.scenario.beats;
            return {scenes: b.length,
                    withLines: b.filter(x=>(x.dialogue||[]).length).length,
                    withPlay: b.filter(x=>x.roleplay).length,
                    lines: b.reduce((n,x)=>n+(x.dialogue||[]).length,0),
                    fromBook: b.reduce((n,x)=>n+(x.dialogue||[])
                                 .filter(y=>y.source==='bok').length,0),
                    badSource: b.reduce((a,x)=>a.concat((x.dialogue||[])
                                 .filter(y=>y.source!=='bok'&&y.source!=='forslag')
                                 .map(y=>x.id+': '+y.source)), [])}; }""")
        print("replikker:", d)
        assert d["withLines"] == d["scenes"], d
        assert d["withPlay"] == d["scenes"], d
        assert d["fromBook"] > 30, d
        assert not d["badSource"], d

        await pg.evaluate("setView('beats')"); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => openItem(state.scenario.beats
            .find(x=>x.id==='beat-up-the-gangway'),'beats')""")
        await pg.wait_for_timeout(400)
        scene=await pg.evaluate("""() => ({
            labels: [...document.querySelectorAll('#modal-body .section-label')]
                      .map(x=>x.textContent),
            lines: document.querySelectorAll('#modal-body .line').length,
            book: document.querySelectorAll('#modal-body .line:not(.suggested)').length,
            sugg: document.querySelectorAll('#modal-body .line.suggested').length,
            first: document.querySelector('#modal-body .line-say').textContent,
        })""")
        print("scenekort:", scene["labels"], scene["lines"], "replikker")
        assert "Replikker" in scene["labels"], scene
        assert "Slik spilles scenen" in scene["labels"], scene
        assert scene["book"] > 0 and scene["sugg"] > 0, scene
        assert "Chad Peterson fra New York" in scene["first"], scene
        await pg.evaluate("closeAllModals()")

        # Replikkene skal kunne søkes opp.
        await pg.evaluate("""() => { state.query='englekoret'; render(); }""")
        await pg.wait_for_timeout(300)
        found=await pg.evaluate(
            "() => [...document.querySelectorAll('#main .entry-title')].map(x=>x.textContent)")
        print("søk på en replikk:", found)
        assert found == ["På jakt etter Bunny Bates"], found
        await pg.evaluate("""() => { state.query=''; render(); }""")

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
