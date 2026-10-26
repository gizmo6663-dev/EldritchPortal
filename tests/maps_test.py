"""Funksjonstest av battlemaps.

    CHROMIUM_PATH=/sti/til/chromium python3 tests/maps_test.py

To deler. Først dataene og bildene: at hver gjenstand har en rute i
atlaset, at ruta ligger innenfor bildet, og at alle filene finnes. Så
selve kartfanen i nettleseren: at kartet tegnes, at gjenstander kan
flyttes og at flyttingen overlever en omlasting, at spillervisningen
faktisk skjuler det den skal, og at dørene fører dit de sier.
"""
import asyncio, json, os, tempfile
from playwright.async_api import async_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(REPO, "web", "index.html")
OUT = os.environ.get("SHOT_DIR") or tempfile.mkdtemp(prefix="maps-")
DATA = os.path.join(REPO, "bestiary", "battlemaps.json")

fails = []


def check(name, got, want):
    ok = got == want
    print(("  ok    " if ok else "  FAIL  ") + name +
          ("" if ok else f": {got!r} != {want!r}"))
    if not ok:
        fails.append(name)


def test_data():
    print("\n== dataene og bildene ==")
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)
    check("skjemaet er vårt", d["schema"], "eldritch-battlemaps/1")
    check("alle rommene er med", len(d["rooms"]), 30)
    check("gruppene er med", len(d["groups"]), 5)
    check("målestokken står", d["units"]["pxPerFoot"], 16)

    try:
        from PIL import Image
    except ImportError:
        Image = None

    mangler, utenfor, dubletter = [], [], []
    props = spor = 0
    romIder = {r["id"] for r in d["rooms"]}
    doder = 0
    for r in d["rooms"]:
        mappe = os.path.join(REPO, "web", "maps", r["dir"])
        for fil in (r["bg"], r["atlas"]):
            if not os.path.exists(os.path.join(mappe, fil)):
                mangler.append(r["dir"] + "/" + fil)
        if Image:
            bg = Image.open(os.path.join(mappe, r["bg"]))
            if bg.size != (r["widthPx"], r["heightPx"]):
                utenfor.append("%s: bakgrunn %s != %s" %
                               (r["id"], bg.size, (r["widthPx"], r["heightPx"])))
            atlas = Image.open(os.path.join(mappe, r["atlas"]))
            if atlas.size != (r["atlasW"], r["atlasH"]):
                utenfor.append("%s: atlas %s != %s" %
                               (r["id"], atlas.size, (r["atlasW"], r["atlasH"])))
        # Rutene skal ikke overlappe hverandre heller — da ville to
        # gjenstander vist samme piksler.
        tatt = []
        for navn, (x, y, w, h) in r["frames"].items():
            if x < 0 or y < 0 or x + w > r["atlasW"] or y + h > r["atlasH"]:
                utenfor.append("%s/%s utenfor atlaset" % (r["id"], navn))
            for (ox, oy, ow, oh) in tatt:
                if x < ox + ow and ox < x + w and y < oy + oh and oy < y + h:
                    dubletter.append("%s/%s overlapper" % (r["id"], navn))
                    break
            tatt.append((x, y, w, h))
        for it in r["items"]:
            props += 1
            if it["sprite"] not in r["frames"]:
                mangler.append("%s/%s: sprite %s" %
                               (r["id"], it["id"], it["sprite"]))
            if it.get("linksTo") and it["linksTo"] not in romIder:
                doder += 1
        spor += len(r["clues"])
        for c in r["clues"]:
            if c.get("item") and not any(i["id"] == c["item"] for i in r["items"]):
                doder += 1

    check("ingen bilder eller sprites mangler", mangler, [])
    check("ingen ruter faller utenfor atlaset", utenfor, [])
    check("ingen ruter overlapper hverandre", dubletter, [])
    check("alle gjenstandene er med", props, 839)
    check("alle sporene er med", spor, 96)
    dekor = sum(1 for r in d["rooms"] for i in r["items"] if i.get("decor"))
    check("dekoren er merket som dekor", dekor, 184)
    check("ingen døde dører eller sporpekere", doder, 0)


async def test_view():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path=os.environ.get("CHROMIUM_PATH") or None)
        ctx = await b.new_context(viewport={"width": 1400, "height": 1000})
        errs = []
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
        pg.on("console", lambda m: errs.append("CONSOLE: " + m.text)
              if m.type == "error" and "ERR_CONNECTION" not in m.text else None)
        await pg.goto(URL)
        await pg.wait_for_timeout(2500)

        print("\n== kartet tegnes ==")
        await pg.evaluate("setView('maps')")
        await pg.wait_for_timeout(1200)
        r = await pg.evaluate("""() => {
            const rom = currentMapRoom();
            const bg = document.querySelector('.mapbg');
            return { tittel: rom.title,
                     props: document.querySelectorAll('.mapprop').length,
                     synlige: visibleProps(rom).length,
                     spor: document.querySelectorAll('.cluerow').length,
                     rom: document.querySelectorAll('.maproomrow').length,
                     bgLastet: bg.complete && bg.naturalWidth > 0,
                     bgBredde: bg.naturalWidth,
                     romBredde: rom.widthPx,
                     rutenett: !!document.querySelector('.mapgrid'),
                     skala: parseFloat(
                       document.getElementById('maplayer').dataset.scale) }; }""")
        check("bakgrunnen er lastet", r["bgLastet"], True)
        check("og har rommets mål", r["bgBredde"], r["romBredde"])
        check("alle synlige gjenstander er tegnet", r["props"], r["synlige"])
        check("sporlista er der", r["spor"] > 0, True)
        check("alle 30 rommene står i lista", r["rom"], 30)
        check("rutenettet er på", r["rutenett"], True)
        check("kartet er skalert til plassen", r["skala"] > 0, True)

        print("\n== en gjenstand kan flyttes ==")
        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const it = rom.items.find(i => !i.hiddenByDefault);
            const for_ = propNow(rom, it);
            await setProp(rom, it, { x: for_.x + 48, y: for_.y + 16 });
            render();
            await new Promise(r => setTimeout(r, 300));
            const node = document.querySelector('[data-prop="' + it.id + '"]');
            return { id: it.id, startX: for_.x,
                     naaX: propNow(rom, it).x,
                     iDom: parseInt(node.style.left, 10),
                     lagret: !!(state.progress.maps[rom.id] || {})[it.id] }; }""")
        check("den flyttet seg", r["naaX"], r["startX"] + 48)
        check("og kartet viser den der", r["iDom"], r["startX"] + 48)
        check("avviket er lagret", r["lagret"], True)

        print("\n== rotere, skjule og hente fram igjen ==")
        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const it = rom.items.find(i => !i.hiddenByDefault);
            await setProp(rom, it, { r: 90 });
            render(); await new Promise(r => setTimeout(r, 200));
            const snudd = document.querySelector('[data-prop="' + it.id + '"]')
                            .style.transform;
            await setProp(rom, it, { hidden: true });
            render(); await new Promise(r => setTimeout(r, 200));
            const borte = !document.querySelector('[data-prop="' + it.id + '"]');
            const chip = [...document.querySelectorAll('.maphidden .chip')]
                           .some(c => c.textContent.includes(it.name));
            return { snudd, borte, chip }; }""")
        check("rotasjonen står i kartet", "rotate(90deg)" in r["snudd"], True)
        check("skjult gjenstand tegnes ikke", r["borte"], True)
        check("men ligger i lista under kartet", r["chip"], True)

        r = await pg.evaluate("""async () => {
            const chip = document.querySelector('.maphidden .chip');
            chip.click();
            await new Promise(r => setTimeout(r, 400));
            return document.querySelectorAll('.maphidden .chip').length; }""")
        check("og kan hentes fram igjen", r, 0)

        print("\n== tilbakestilling ==")
        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            delete state.progress.maps[rom.id];
            await saveProgress(); render();
            await new Promise(r => setTimeout(r, 300));
            const it = rom.items.find(i => !i.hiddenByDefault);
            const st = propNow(rom, it);
            return { x: st.x === it.x, r: st.r === (it.rotation || 0) }; }""")
        check("alt står som det sto", r["x"] and r["r"], True)

        print("\n== spillervisning skjuler sporene ==")
        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const medSpor = visibleProps(rom).length;
            const sporProps = rom.items.filter(i => i.clue).length;
            state.mapPlayer = true; render();
            await new Promise(r => setTimeout(r, 300));
            const uten = document.querySelectorAll('.mapprop').length;
            const merket = document.querySelectorAll('.mapprop.clueprop').length;
            state.mapPlayer = false; render();
            return { medSpor, sporProps, uten, merket }; }""")
        check("rommet har spor-gjenstander", r["sporProps"] > 0, True)
        check("de forsvinner i spillervisning",
              r["uten"], r["medSpor"] - r["sporProps"])
        check("og ingen er merket som spor da", r["merket"], 0)

        print("\n== lys og skygge ==")
        r = await pg.evaluate("""() => {
            const typer = {};
            state.maps.rooms.forEach(r => {
              typer[roomLight(r)] = (typer[roomLight(r)] || 0) + 1; });
            return { typer,
                     ute: roomLight(mapRoomById('promenade')),
                     vindu: roomLight(mapRoomById('kabin')),
                     svakt: roomLight(mapRoomById('steerage')),
                     dypt: roomLight(mapRoomById('hold7')),
                     kjolerom: roomLight(mapRoomById('hold3')),
                     lensa: roomLight(mapRoomById('bilge')) }; }""")
        check("åpent dekk kjennes igjen", r["ute"], "ute")
        check("en lugar på A-dekk har koøye", r["vindu"], "vindu")
        check("sovesalen på D-dekk har så vidt dagslys", r["svakt"], "svakt")
        check("lasterommet på E-dekk har ingen", r["dypt"], "dypt")
        check("kjølerommet på B-dekk har heller ingen",
              r["kjolerom"], "dypt")
        check("og lensa under E-dekk ikke", r["lensa"], "dypt")
        check("alle fire typene er i bruk",
              sorted(r["typer"].keys()), ["dypt", "svakt", "ute", "vindu"])

        r = await pg.evaluate("""async () => {
            await byttRom('kabin');
            await new Promise(r => setTimeout(r, 500));
            const tell = () => document.querySelectorAll('.maplight').length;
            const ut = {};
            for (const [tid, strom] of [['dag',true],['natt',true],
                                        ['dag',false],['natt',false]]) {
              state.mapTime = tid; state.mapPower = strom; render();
              await new Promise(r => setTimeout(r, 250));
              ut[tid + '/' + strom] = {
                lag: tell(),
                skygge: document.getElementById('maplayer')
                          .style.getPropertyValue('--propskygge'),
              };
            }
            state.mapTime = 'dag'; state.mapPower = true; render();
            return ut; }""")
        for n in ("dag/true", "natt/true", "dag/false", "natt/false"):
            check("%s har lyslag" % n, r[n]["lag"] > 0, True)
        check("skyggen vokser når det blir natt",
              r["natt/true"]["skygge"] != r["dag/true"]["skygge"], True)
        check("og når strømmen går",
              r["dag/false"]["skygge"] != r["dag/true"]["skygge"], True)

        r = await pg.evaluate("""() => {
            // Et rom uten dagslys skal se likt ut natt og dag.
            const dypt = state.maps.rooms.find(r => roomLight(r) === 'dypt');
            const ute = state.maps.rooms.find(r => roomLight(r) === 'ute');
            const hent = (rom, tid, strom) => {
              state.mapTime = tid; state.mapPower = strom;
              return JSON.stringify(lightFor(rom)); };
            const d1 = hent(dypt, 'dag', true), d2 = hent(dypt, 'natt', true);
            const d3 = hent(dypt, 'dag', false), d4 = hent(dypt, 'natt', false);
            const u1 = hent(ute, 'dag', true), u2 = hent(ute, 'dag', false);
            const u3 = hent(ute, 'natt', true);
            state.mapTime = 'dag'; state.mapPower = true;
            return { dyptLikt: d1 === d2, dyptMorktLikt: d3 === d4,
                     dyptEndrerSegUtenStrom: d1 !== d3,
                     uteUpaavirket: u1 === u2, uteNattAnnerledes: u1 !== u3 }; }""")
        check("uten dagslys er natt og dag likt", r["dyptLikt"], True)
        check("også når strømmen er borte", r["dyptMorktLikt"], True)
        check("men strømbrudd merkes med en gang",
              r["dyptEndrerSegUtenStrom"], True)
        check("ute merkes strømbrudd ikke om dagen",
              r["uteUpaavirket"], True)
        check("men natta gjør det", r["uteNattAnnerledes"], True)

        r = await pg.evaluate("""async () => {
            // Lyset må ligge over gjenstandene, ellers mørkner gulvet
            // mens møblene står og lyser.
            state.mapTime = 'natt'; state.mapPower = false; render();
            await new Promise(r => setTimeout(r, 300));
            const lys = document.querySelector('.maplight');
            const prop = document.querySelector('.mapprop:not(.sel)');
            const z = (n) => parseInt(getComputedStyle(n).zIndex, 10) || 0;
            const svar = { over: z(lys) > z(prop),
                           blend: getComputedStyle(
                             document.querySelector('.maplight.tone'))
                             .mixBlendMode,
                           rutenettOverst: z(document.querySelector('.mapgrid'))
                             > z(lys) };
            state.mapTime = 'dag'; state.mapPower = true; render();
            return svar; }""")
        check("lyset ligger over gjenstandene", r["over"], True)
        check("og mørkner dem med multiply", r["blend"], "multiply")
        check("rutenettet ligger øverst", r["rutenettOverst"], True)

        r = await pg.evaluate("""() => {
            const f = [];
            state.mapTime = 'natt'; state.mapPower = false;
            const a = (document.querySelector('.maptools') &&
              [...document.querySelectorAll('.chip.resp')]
                .map(c => c.textContent));
            state.mapTime = 'dag'; state.mapPower = true; render();
            return a; }""")
        check("valgene står i verktøylinja",
              "Strømbrudd" in r and ("Dag" in r or "Natt" in r), True)

        print("\n== lyskilder ==")
        r = await pg.evaluate("""async () => {
            await byttRom('hold7');
            state.mapTime = 'natt'; state.mapPower = false;
            if (state.progress) state.progress.mapLights = {};
            render(); await new Promise(r => setTimeout(r, 400));
            // Bare de man har satt ut selv — nødlampene henger der
            // uansett, og de har ingen data-lys.
            const for_ = document.querySelectorAll(
              '.maplight.kilde[data-lys]').length;
            const rom = currentMapRoom();
            await addLight(rom, 'lommelykt');
            await new Promise(r => setTimeout(r, 400));
            const lys = mapLights(rom.id)[0];
            const node = document.querySelector('.maplight.kilde[data-lys]');
            return { for_, etter: document.querySelectorAll(
                       '.maplight.kilde[data-lys]').length,
                     type: lys.t, valgt: state.mapSelLight === lys.id,
                     iDom: !!node,
                     kjegle: node && getComputedStyle(node).clipPath !== 'none',
                     midt: lys.x === Math.round(rom.widthPx / 2) }; }""")
        check("ingen egne lyskilder før man setter dem ut", r["for_"], 0)
        check("lommelykta kom på kartet", r["etter"], 1)
        check("den er en kjegle", r["kjegle"], True)
        check("den havner midt i rommet", r["midt"], True)
        check("og blir valgt med én gang", r["valgt"], True)

        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const lys = mapLights(rom.id)[0];
            await setLight(rom, lys.id, { x: 100, y: 120, rot: 90, r: 220 });
            render(); await new Promise(r => setTimeout(r, 300));
            const etter = mapLights(rom.id)[0];
            return { x: etter.x, rot: etter.rot, r: etter.r }; }""")
        check("den kan flyttes", r["x"], 100)
        check("snus", r["rot"], 90)
        check("og skaleres", r["r"], 220)

        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            await addLight(rom, 'lykt');
            await addLight(rom, 'nod');
            const antall = mapLights(rom.id).length;
            const sist = mapLights(rom.id)[2];
            await removeLight(rom, sist.id);
            await new Promise(r => setTimeout(r, 300));
            const etterSletting = mapLights(rom.id).length;
            document.getElementById('quick-undo').click();
            await new Promise(r => setTimeout(r, 400));
            return { antall, etterSletting,
                     etterAngre: mapLights(rom.id).length }; }""")
        check("flere lys kan stå samtidig", r["antall"], 3)
        check("ett kan slukkes", r["etterSletting"], 2)
        check("og tennes igjen med angre", r["etterAngre"], 3)

        print("\n== nødlys, vinduer og dekkslykter ==")
        r = await pg.evaluate("""() => {
            const dypt = mapRoomById('hold7');
            const vindu = mapRoomById('kabin');
            const ute = mapRoomById('promenade');
            const sett = (t, p) => { state.mapTime = t; state.mapPower = p; };
            const nod = (rom) => !!(lightFor(rom).nodlys);
            const ut = {};
            sett('dag', true);   ut.nodMedStrom = nod(dypt);
            ut.vinduMedStrom = windowShafts(vindu).length;
            sett('dag', false);  ut.nodDagUtenStrom = nod(dypt);
            ut.vinduDagUtenStrom = windowShafts(vindu).length;
            ut.dyptHarIngenVinduer = windowShafts(dypt).length;
            sett('natt', false); ut.nodNattUtenStrom = nod(dypt);
            ut.vinduNattUtenStrom = windowShafts(vindu).length;
            ut.uteNattUtenStrom = autoLights(ute).map(l => l.t);
            sett('natt', true);  ut.uteNattMedStrom = autoLights(ute).map(l => l.t);
            sett('dag', true);   ut.uteDag = autoLights(ute).length;
            ut.dyptHarIngenAuto = autoLights(dypt).length;
            return ut; }""")
        check("nødlyset er av når strømmen står på", r["nodMedStrom"], False)
        check("og på når den går, om dagen", r["nodDagUtenStrom"], True)
        check("og om natta", r["nodNattUtenStrom"], True)
        check("vinduene gir ikke lys når lampene virker",
              r["vinduMedStrom"], 0)
        check("men de gjør det ved strømbrudd om dagen",
              r["vinduDagUtenStrom"] > 0, True)
        check("ikke om natta — da er det mørkt ute",
              r["vinduNattUtenStrom"], 0)
        check("et rom uten vinduer får ingen striper",
              r["dyptHarIngenVinduer"], 0)
        check("dekkslykter og lyslenke henger ute om natta",
              sorted(set(r["uteNattMedStrom"])), ["lenke", "lykt"])
        check("uten strøm står bare månen igjen",
              sorted(set(r["uteNattUtenStrom"])), ["maane"])
        check("om dagen trengs de ikke", r["uteDag"], 0)
        check("og under dekk henger det ingen", r["dyptHarIngenAuto"], 0)

        r = await pg.evaluate("""() => {
            const dypt = mapRoomById('hold7');
            state.mapTime = 'natt'; state.mapPower = false;
            const lamper = autoLights(dypt);
            state.mapPower = true;
            const medStrom = autoLights(dypt).length;
            state.mapTime = 'dag'; state.mapPower = true;
            return { antall: lamper.length,
                     alleRode: lamper.every(l => l.t === 'nod'),
                     parvis: lamper.length % 2 === 0,
                     medStrom: medStrom }; }""")
        check("nødlampene henger som lamper, ikke som tåke",
              r["antall"] >= 4, True)
        check("alle er røde", r["alleRode"], True)
        check("en på hver langvegg", r["parvis"], True)
        check("og ingen når strømmen står på", r["medStrom"], 0)

        r = await pg.evaluate("""() => {
            // Lyslenka skal være pærer på rad, ikke én stor flekk.
            const paerer = lenkePaerer({ x: 0, y: 35, bredde: 440 });
            const avstand = paerer[1].x - paerer[0].x;
            return { antall: paerer.length, avstand: avstand,
                     starter: paerer[0].x > 0,
                     innenfor: paerer[paerer.length - 1].x < 440 }; }""")
        check("lenka har flere pærer", r["antall"] >= 8, True)
        check("med jevn avstand", r["avstand"] > 20, True)
        check("den første er inne på lenka", r["starter"], True)
        check("og den siste også", r["innenfor"], True)

        r = await pg.evaluate("""async () => {
            state.mapTime = 'natt'; state.mapPower = false;
            await byttRom('hold7');
            render(); await new Promise(r => setTimeout(r, 400));
            const lag = [...document.querySelectorAll('.maplight')];
            const vign = lag.findIndex(n => n.classList.contains('vignett'));
            const kilde = lag.findIndex(n => n.classList.contains('kilde'));
            const z = (n) => parseInt(getComputedStyle(n).zIndex, 10) || 0;
            return { etterVignett: kilde > vign,
                     over: z(lag[kilde]) >= z(lag[vign]),
                     blend: getComputedStyle(lag[kilde]).mixBlendMode }; }""")
        check("lyskildene tegnes etter vignetten", r["etterVignett"], True)
        check("og ligger over den", r["over"], True)
        check("de lyser opp med screen", r["blend"], "screen")

        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const for_ = mapLights(rom.id).length;
            delete state.progress.mapLights[rom.id];
            await saveProgress(); render();
            return { for_, etter: mapLights(rom.id).length }; }""")
        check("lysene kan slukkes alle sammen", r["etter"], 0)

        print("\n== dekoren kan slås av ==")
        r = await pg.evaluate("""async () => {
            // Finn et rom som faktisk har dekor.
            const rom = state.maps.rooms.find(r =>
              r.items.some(i => i.decor));
            await byttRom(rom.id);
            await new Promise(r => setTimeout(r, 600));
            const med = document.querySelectorAll('.mapprop').length;
            const dekor = rom.items.filter(i => i.decor).length;
            const knapp = [...document.querySelectorAll('.chip.resp')]
              .find(c => c.textContent.startsWith('Dekor'));
            if (!knapp) return { fant: false };
            knapp.click();
            await new Promise(r => setTimeout(r, 500));
            const uten = document.querySelectorAll('.mapprop').length;
            state.mapDecor = true; render();
            return { fant: true, med, uten, dekor,
                     tekst: knapp.textContent }; }""")
        check("bryteren finnes", r["fant"], True)
        check("og teller dekoren", r["tekst"], "Dekor " + str(r["dekor"]))
        check("dekoren forsvinner", r["uten"], r["med"] - r["dekor"])

        print("\n== sporpanelet peker ut gjenstanden ==")
        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const i = rom.clues.findIndex(c => c.item &&
              rom.items.some(x => x.id === c.item));
            if (i < 0) return { fant: false };
            document.querySelectorAll('.cluerow')[i].click();
            await new Promise(r => setTimeout(r, 400));
            return { fant: true, valgt: state.mapSel === rom.clues[i].item,
                     apen: document.querySelectorAll('.cluerow')[i]
                             .getAttribute('aria-expanded'),
                     tekst: !!document.querySelector('.cluebody p'),
                     logg: [...document.querySelectorAll('.cluebody button')]
                             .some(b => b.textContent === 'Logg') }; }""")
        check("et spor med gjenstand ble funnet", r["fant"], True)
        check("sporet åpner seg", r["apen"], "true")
        check("forklaringen vises", r["tekst"], True)
        check("gjenstanden blir valgt", r["valgt"], True)
        check("og sporet kan logges i økta", r["logg"], True)

        print("\n== dørene fører dit de sier ==")
        r = await pg.evaluate("""async () => {
            // Finn et rom med en dør, velg døra, og gå gjennom den.
            const fra = state.maps.rooms.find(r =>
              r.items.some(i => i.linksTo));
            await byttRom(fra.id);
            await new Promise(r => setTimeout(r, 500));
            const dor = fra.items.find(i => i.linksTo);
            state.mapSel = dor.id;
            oppdaterVerktoy();
            const knapp = document.getElementById('mapgoto');
            const tekst = knapp.textContent;
            const skjult = knapp.hidden;
            knapp.click();
            await new Promise(r => setTimeout(r, 600));
            return { fra: fra.id, maal: dor.linksTo, skjult: skjult,
                     tekst: tekst, naa: currentMapRoom().id }; }""")
        check("knappen vises når en dør er valgt", r["skjult"], False)
        check("og sier hvor den går", r["tekst"].startswith("Gå til"), True)
        check("man havner i riktig rom", r["naa"], r["maal"])

        print("\n== eksport ==")
        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const skala = Math.max(2, Math.min(6,
              Math.floor(4000 / rom.widthPx)));
            const c = document.createElement('canvas');
            c.width = rom.widthPx * skala; c.height = rom.heightPx * skala;
            const g = c.getContext('2d');
            const last = (s) => new Promise((ok, nei) => {
              const i = new Image(); i.onload = () => ok(i); i.onerror = nei;
              i.src = s; });
            const bg = await last(mapAsset(rom, 'bg'));
            const atlas = await last(mapAsset(rom, 'sprites'));
            g.drawImage(bg, 0, 0, c.width, c.height);
            return { bredde: c.width, bgOk: bg.naturalWidth === rom.widthPx,
                     atlasOk: atlas.naturalWidth === rom.atlasW }; }""")
        check("bakgrunnen kan tegnes på lerretet", r["bgOk"], True)
        check("atlaset også", r["atlasOk"], True)
        check("og lerretet er større enn rommet", r["bredde"] > 1000, True)

        print("\n== alt overlever en omlasting ==")
        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const it = rom.items.find(i => !i.hiddenByDefault);
            await setProp(rom, it, { x: it.x + 32, hidden: false });
            flushWrites();
            return { rom: rom.id, prop: it.id, x: it.x + 32 }; }""")
        await pg.wait_for_timeout(400)
        await pg.reload()
        await pg.wait_for_timeout(2500)
        etter = await pg.evaluate("""(f) => {
            const rom = mapRoomById(f.rom);
            const it = rom.items.find(i => i.id === f.prop);
            return { x: propNow(rom, it).x, rom: currentMapRoom().id }; }""", r)
        check("flyttingen står", etter["x"], r["x"])
        check("og rommet huskes", etter["rom"], r["rom"])

        await pg.evaluate("setView('maps')")
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=f"{OUT}/kart.png")
        print("\nskjermbilder:", OUT)
        print("ERRORS:", errs or "none")
        await ctx.close()
        await b.close()


test_data()
asyncio.run(test_view())
print("\nRESULT:", "FAILED" if fails else "OK")
