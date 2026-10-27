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

    # Lysmotoren trenger høyder og lysdata.
    hoyde = sum(1 for r in d["rooms"] for i in r["items"] if i.get("h"))
    check("gjenstandene har høyder", hoyde > 350, True)
    rom = {r["id"]: r for r in d["rooms"]}
    check("alle rom har lysdata", all("lys" in r for r in d["rooms"]), True)
    check("koøyene i kabinen er med", len(rom["kabin"]["lys"]["vinduer"]), 4)
    check("veggene i kabinen er med", len(rom["kabin"]["lys"]["vegger"]), 3)
    check("dekkene ute har rekker",
          [bool(rom[k]["lys"].get("rekker")) for k in
           ("bow", "stern", "promenade", "bridge", "soong")], [True] * 5)
    check("lasterom 2 har nødlampene fra verkstedet",
          len(rom["hold2"]["lys"]["nodlamper"]), 4)
    check("lykter og lamper kjennes igjen", bool(d.get("lys")), True)
    bil = [i for i in rom["hold6"]["items"] if "Hudson" in (i.get("name") or "")]
    check("en bil er høy, ikke en livbøye", bil and bil[0].get("h"), 60)


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

        print("\n== lys og skygge: rommene ==")
        r = await pg.evaluate("""() => {
            const typer = {};
            state.maps.rooms.forEach(r => {
              typer[roomLight(r)] = (typer[roomLight(r)] || 0) + 1; });
            const t = (id) => roomLight(mapRoomById(id));
            return { typer, ute: t('promenade'), vindu: t('kabin'),
                     sovesal: t('steerage'), dypt: t('hold7'),
                     kjolerom: t('hold3'), lensa: t('bilge'),
                     bro: t('bridge'), soong: t('soong') }; }""")
        check("åpent dekk kjennes igjen", r["ute"], "ute")
        check("en lugar med koøyer har vinduer", r["vindu"], "vindu")
        check("sovesalen har ingen vinduer", r["sovesal"], "dypt")
        check("lasterommet har ingen", r["dypt"], "dypt")
        check("kjølerommet har heller ingen", r["kjolerom"], "dypt")
        check("og lensa ikke", r["lensa"], "dypt")
        check("broen er ute, med vinduer i styrhuset", r["bro"], "vindu")
        check("Soongs lugar har vinduer mot dekket", r["soong"], "vindu")
        check("alle tre typene er i bruk",
              sorted(r["typer"].keys()), ["dypt", "ute", "vindu"])

        r = await pg.evaluate("""async () => {
            await byttRom('kabin');
            await new Promise(r => setTimeout(r, 400));
            const ut = {};
            for (const [tid, strom] of [['dag',true],['natt',true],
                                        ['dag',false],['natt',false]]) {
              state.mapTime = tid; state.mapPower = strom; render();
              await new Promise(r => setTimeout(r, 150));
              const o = lysFor(currentMapRoom());
              ut[tid + '/' + strom] = {
                kart: !!document.querySelector('.maplys.kart'),
                straaler: o.lys.filter(l => l.type === 'stråle').length,
                farge: (o.lys.find(l => l.type === 'stråle') || {}).farge,
                lamper: o.lys.filter(l => l.type === 'punkt' && l.hoyde === 150).length,
              };
            }
            state.mapTime = 'dag'; state.mapPower = true; render();
            return ut; }""")
        check("om dagen med strøm står kunsten som tegnet",
              r["dag/true"]["kart"], False)
        check("om natta tennes taklampene", r["natt/true"]["lamper"] > 0, True)
        check("ved strømbrudd om dagen skinner sola inn gjennom koøyene",
              r["dag/false"]["straaler"], 4)
        check("med varmt lys", r["dag/false"]["farge"], [255, 228, 182])
        check("om natta er det månen som skinner inn",
              r["natt/false"]["farge"], [150, 175, 230])
        check("og lyskartet ligger over i alle tre",
              [r[k]["kart"] for k in ("natt/true", "dag/false", "natt/false")],
              [True, True, True])

        r = await pg.evaluate("""() => {
            // Et rom uten vinduer skal se likt ut natt og dag.
            const dypt = mapRoomById('hold7');
            const ute = mapRoomById('promenade');
            const hent = (rom, tid, strom) => {
              state.mapTime = tid; state.mapPower = strom;
              const o = lysFor(rom);
              return { aktiv: o.aktiv, lys: JSON.stringify(o.lys),
                       rode: o.lys.filter(l => l.farge === FARGE.rod).length,
                       lenker: o.lenker.length, lykter: o.lykter.length,
                       paerer: o.lenker.reduce((n, l) => n + l.punkter.length, 0) }; };
            const ut = {
              d1: hent(dypt, 'dag', true), d2: hent(dypt, 'natt', true),
              d3: hent(dypt, 'dag', false), d4: hent(dypt, 'natt', false),
              u1: hent(ute, 'dag', true), u2: hent(ute, 'dag', false),
              u3: hent(ute, 'natt', true), u4: hent(ute, 'natt', false) };
            state.mapTime = 'dag'; state.mapPower = true;
            return ut; }""")
        check("uten vinduer er natt og dag likt med strøm",
              [r["d1"]["aktiv"], r["d2"]["aktiv"]], [False, False])
        check("og likt uten strøm", r["d3"]["lys"], r["d4"]["lys"])
        check("strømbrudd gir nødlamper med en gang", r["d3"]["rode"] >= 4, True)
        check("og ingen når strømmen står på", r["d1"]["rode"], 0)
        check("ute merkes strømbrudd ikke om dagen",
              [r["u1"]["aktiv"], r["u2"]["aktiv"]], [False, False])
        check("om natta henger det lyslenker langs rekka",
              r["u3"]["paerer"] > 20, True)
        check("uten strøm er lenkene mørke", r["u4"]["lenker"], 0)
        check("men oljelyktene er tent", r["u4"]["lykter"] > 2, True)

        r = await pg.evaluate("""() => {
            // Selve motoren: et lys bak en kasse gir skygge bak kassa,
            // ikke ved siden av.
            const pkt = (c, x, y) => c.getContext('2d').getImageData(x, y, 1, 1).data[0];
            const kasse = [Lysmotor.hinder(Lysmotor.hjorner(40, 40, 20, 12, 0), 40, 'k')];
            const felles = { aktiv: true, omgivelse: [0, 0, 0], soner: [],
                             kilder: [], vignett: 0, dis: 0, uskarp: 0.5 };
            const punkt = Lysmotor.render(100, 100, Object.assign({}, felles, {
              hindre: kasse, lys: [{ type: 'punkt', x: 50, y: 10, radius: 120,
                farge: [255, 255, 255], styrke: 1, hoyde: 80, maksSkygge: 200 }] }));
            const uten = Lysmotor.render(100, 100, Object.assign({}, felles, {
              hindre: [], lys: [{ type: 'punkt', x: 50, y: 10, radius: 120,
                farge: [255, 255, 255], styrke: 1, hoyde: 80, maksSkygge: 200 }] }));
            const sol = Lysmotor.render(100, 100, Object.assign({}, felles, {
              hindre: kasse, lys: [{ type: 'stråle', x: 50, y: 0, vinkel: 0,
                lengde: 100, bredde: 60, spredning: 1, farge: [255, 255, 255],
                styrke: 1, skyggelengde: 1 }] }));
            const egen = Lysmotor.render(100, 100, Object.assign({}, felles, {
              hindre: kasse, lys: [{ type: 'punkt', x: 50, y: 10, radius: 120,
                farge: [255, 255, 255], styrke: 1, hoyde: 80, maksSkygge: 200,
                selv: 'k' }] }));
            return { bak: pkt(punkt.kart, 50, 64), siden: pkt(punkt.kart, 25, 64),
                     utenKasse: pkt(uten.kart, 50, 64), topp: pkt(punkt.kart, 50, 46),
                     solBak: pkt(sol.kart, 50, 70), solSiden: pkt(sol.kart, 30, 70),
                     egen: pkt(egen.kart, 50, 64) }; }""")
        check("bak kassa er det skygge", r["bak"] < r["utenKasse"] * 0.4, True)
        check("ved siden av er det lyst", r["siden"] > r["bak"] * 2, True)
        check("toppen av kassa er opplyst", r["topp"] > r["bak"] * 2, True)
        check("sola kaster parallelle skygger", r["solBak"] < r["solSiden"] * 0.4, True)
        check("en lampe skygger ikke for seg selv", r["egen"] >= r["utenKasse"] * 0.9, True)

        r = await pg.evaluate("""async () => {
            // Lyset må ligge over gjenstandene, ellers mørkner gulvet
            // mens møblene står og lyser.
            state.mapTime = 'natt'; state.mapPower = false; render();
            await new Promise(r => setTimeout(r, 300));
            const kart = document.querySelector('.maplys.kart');
            const prop = document.querySelector('.mapprop:not(.sel)');
            const z = (n) => parseInt(getComputedStyle(n).zIndex, 10) || 0;
            const svar = { over: z(kart) > z(prop),
                           blend: getComputedStyle(kart).mixBlendMode,
                           dis: getComputedStyle(document.querySelector('.maplys.glod'))
                                  .mixBlendMode,
                           klikk: getComputedStyle(kart).pointerEvents,
                           rutenettOverst: z(document.querySelector('.mapgrid')) > z(kart),
                           maal: kart.style.width === currentMapRoom().widthPx + 'px' };
            state.mapTime = 'dag'; state.mapPower = true; render();
            return svar; }""")
        check("lyset ligger over gjenstandene", r["over"], True)
        check("og mørkner dem med multiply", r["blend"], "multiply")
        check("gløden lyser opp med screen", r["dis"], "screen")
        check("lagene stjeler ikke klikk", r["klikk"], "none")
        check("rutenettet ligger øverst", r["rutenettOverst"], True)
        check("lyskartet har rommets mål", r["maal"], True)

        r = await pg.evaluate("""() => {
            state.mapTime = 'natt'; state.mapPower = false;
            const a = [...document.querySelectorAll('.chip.resp')]
                .map(c => c.textContent);
            state.mapTime = 'dag'; state.mapPower = true; render();
            return a; }""")
        check("valgene står i verktøylinja",
              "Strømbrudd" in r and ("Dag" in r or "Natt" in r), True)

        print("\n== lykter og lamper på kartet ==")
        r = await pg.evaluate("""async () => {
            const rom = mapRoomById('hold2');
            const lykt = rom.items.find(i => i.sprite === 'lantern');
            state.mapTime = 'natt'; state.mapPower = false;
            const finn = () => lysFor(rom).lys.find(l => l.selv === lykt.id);
            const for_ = finn();
            await setProp(rom, lykt, { x: lykt.x + 100 });
            const flyttet = finn();
            await setProp(rom, lykt, { hidden: true });
            const skjult = finn();
            delete state.progress.maps[rom.id];
            const kabin = mapRoomById('kabin');
            const gulvlampe = () => lysFor(kabin).lys.some(l => l.selv === 'floorlamp');
            state.mapPower = true; const medStrom = gulvlampe();
            state.mapPower = false; const utenStrom = gulvlampe();
            state.mapTime = 'dag'; state.mapPower = true;
            return { lyser: !!for_, fulgte: flyttet && for_ && flyttet.x - for_.x,
                     skjult: !!skjult, medStrom, utenStrom }; }""")
        check("lykta i lasterommet lyser i mørket", r["lyser"], True)
        check("lyset følger med når den flyttes", r["fulgte"], 100)
        check("og slukker når den skjules", r["skjult"], False)
        check("gulvlampa lyser når strømmen står på", r["medStrom"], True)
        check("men ikke ved strømbrudd", r["utenStrom"], False)

        print("\n== lyskilder man setter ut selv ==")
        r = await pg.evaluate("""async () => {
            await byttRom('hold7');
            state.mapTime = 'natt'; state.mapPower = false;
            if (state.progress) state.progress.mapLights = {};
            render(); await new Promise(r => setTimeout(r, 400));
            const for_ = document.querySelectorAll('.maplyshandle').length;
            const rom = currentMapRoom();
            await addLight(rom, 'lommelykt');
            await new Promise(r => setTimeout(r, 400));
            const lys = mapLights(rom.id)[0];
            const kjegle = lysFor(rom).lys.find(l => l.kjegle);
            return { for_, etter: document.querySelectorAll('.maplyshandle').length,
                     valgt: state.mapSelLight === lys.id,
                     merket: !!document.querySelector('.maplyshandle.sel'),
                     kjegle: !!kjegle,
                     midt: lys.x === Math.round(rom.widthPx / 2) }; }""")
        check("ingen egne lyskilder før man setter dem ut", r["for_"], 0)
        check("lommelykta kom på kartet", r["etter"], 1)
        check("den lyser i en kjegle", r["kjegle"], True)
        check("den havner midt i rommet", r["midt"], True)
        check("og blir valgt med én gang", r["valgt"] and r["merket"], True)

        # Dra lykta med musa: håndtaket ligger der lyset er.
        boks = await pg.evaluate("""() => {
            const b = document.querySelector('.maplyshandle').getBoundingClientRect();
            return { x: b.x + b.width / 2, y: b.y + b.height / 2,
                     k: parseFloat(document.getElementById('maplayer').dataset.scale) }; }""")
        await pg.mouse.move(boks["x"], boks["y"])
        await pg.mouse.down()
        await pg.mouse.move(boks["x"] + 40, boks["y"] + 20, steps=5)
        await pg.wait_for_timeout(150)
        await pg.mouse.up()
        await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => {
            const rom = currentMapRoom();
            const lys = mapLights(rom.id)[0];
            return { dx: lys.x - Math.round(rom.widthPx / 2),
                     dy: lys.y - Math.round(rom.heightPx / 2) }; }""")
        forventet = round(40 / boks["k"])
        check("lykta kan dras med musa",
              abs(r["dx"] - forventet) <= 1 and abs(r["dy"] - round(20 / boks["k"])) <= 1,
              True)

        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            const lys = mapLights(rom.id)[0];
            await setLight(rom, lys.id, { x: 100, y: 120, rot: 90, r: 220 });
            render(); await new Promise(r => setTimeout(r, 300));
            const etter = mapLights(rom.id)[0];
            const k = lysFor(rom).lys.find(l => l.kjegle);
            return { x: etter.x, rot: k.kjegle.retning, r: k.radius }; }""")
        check("den kan flyttes", r["x"], 100)
        check("snus", r["rot"], 90)
        check("og skaleres", r["r"], 220)

        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            await addLight(rom, 'lykt');
            await addLight(rom, 'nod');
            await addLight(rom, 'lenke');
            const o = lysFor(rom);
            const antall = mapLights(rom.id).length;
            const sist = mapLights(rom.id)[3];
            await removeLight(rom, sist.id);
            await new Promise(r => setTimeout(r, 300));
            const etterSletting = mapLights(rom.id).length;
            document.getElementById('quick-undo').click();
            await new Promise(r => setTimeout(r, 400));
            return { antall, etterSletting, lykter: o.lykter.length,
                     paerer: o.lenker.reduce((n, l) => n + l.punkter.length, 0),
                     etterAngre: mapLights(rom.id).length }; }""")
        check("flere lys kan stå samtidig", r["antall"], 4)
        check("lykta tegnes som en lykt", r["lykter"] >= 1, True)
        check("lyslenka er pærer på rad", r["paerer"] >= 8, True)
        check("ett kan slukkes", r["etterSletting"], 3)
        check("og tennes igjen med angre", r["etterAngre"], 4)

        r = await pg.evaluate("""async () => {
            // Lyset regnes ikke ut på nytt når ingenting har endret seg,
            // men gjør det når noe flyttes.
            const rom = currentMapRoom();
            const a = lysLag(rom), b = lysLag(rom);
            const lys = mapLights(rom.id)[0];
            await setLight(rom, lys.id, { x: lys.x + 10 });
            const c = lysLag(rom);
            const stor = lysLag(rom, null, 3);
            return { samme: a === b, nytt: c !== a,
                     eksport: stor.kart.width === rom.widthPx * 3 }; }""")
        check("lagene gjenbrukes", r["samme"], True)
        check("og tegnes på nytt når noe endrer seg", r["nytt"], True)
        check("eksporten tegner i høyere oppløsning", r["eksport"], True)

        r = await pg.evaluate("""async () => {
            const rom = currentMapRoom();
            delete state.progress.mapLights[rom.id];
            await saveProgress(); render();
            return { etter: mapLights(rom.id).length,
                     handtak: document.querySelectorAll('.maplyshandle').length }; }""")
        check("lysene kan slukkes alle sammen", [r["etter"], r["handtak"]], [0, 0])

        r = await pg.evaluate("""() => {
            // Det største rommet med flest lys skal ikke henge.
            let verst = 0;
            for (const rom of state.maps.rooms) {
              for (const [tid, strom] of [['natt',true],['dag',false],['natt',false]]) {
                state.mapTime = tid; state.mapPower = strom;
                const t0 = performance.now();
                lysLag(rom, {});
                verst = Math.max(verst, performance.now() - t0);
              }
            }
            state.mapTime = 'dag'; state.mapPower = true;
            return Math.round(verst); }""")
        print("        (tregeste rom: %d ms)" % r)
        check("alle rom tegnes på under et sekund", r < 1000, True)

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
