import os, sys, traceback, socket, threading, json, random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from kivy.clock import Clock

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")
log("=== APP START (v0.2 – dark theme + splash) ===")

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.button import Button
    from kivy.uix.togglebutton import ToggleButton
    from kivy.uix.label import Label
    from kivy.uix.image import Image
    from kivy.uix.slider import Slider
    from kivy.uix.spinner import Spinner
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.metrics import dp, sp
    from kivy.animation import Animation
    from kivy.properties import ListProperty, NumericProperty
    from kivy.lang import Builder
    log("Kivy imported OK")

    CAST_AVAILABLE = False
    try:
        import pychromecast
        CAST_AVAILABLE = True
    except ImportError:
        pass
    USE_JNIUS = False
    MediaPlayer = None
    if platform == 'android':
        try:
            from jnius import autoclass
            MediaPlayer = autoclass('android.media.MediaPlayer')
            USE_JNIUS = True
            log("Using Android MediaPlayer")
        except:
            pass

    BASE_DIR  = "/sdcard/Documents/EldritchPortal"
    IMG_DIR   = os.path.join(BASE_DIR, "images")
    MUSIC_DIR = os.path.join(BASE_DIR, "music")
    CHAR_FILE = os.path.join(BASE_DIR, "characters.json")
    for d in [IMG_DIR, MUSIC_DIR]:
        os.makedirs(d, exist_ok=True)

    # === FARGER – MØRKT TEMA ===
    BG   = [0.04, 0.04, 0.06, 1]      # nesten svart
    BG2  = [0.08, 0.08, 0.11, 1]      # innholdspanel
    BTN  = [0.14, 0.15, 0.20, 1]      # knappebakgrunn
    BTNH = [0.24, 0.26, 0.34, 1]      # aktiv fane
    SHAD = [0.02, 0.02, 0.03, 0.6]    # skygge (halvtransparent)
    GOLD = [0.95, 0.75, 0.25, 1]      # gylden aksent
    GDIM = [0.55, 0.43, 0.18, 1]      # dempet gull
    TXT  = [0.85, 0.82, 0.75, 1]      # lys tekst
    DIM  = [0.45, 0.43, 0.40, 1]      # dempet tekst
    RED  = [0.70, 0.22, 0.22, 1]
    GRN  = [0.22, 0.58, 0.32, 1]
    BLUE = [0.22, 0.40, 0.65, 1]
    BLK  = [0.0, 0.0, 0.0, 1]         # svart (preview-bg)
    IMG_EXT   = ('.png','.jpg','.jpeg','.webp')
    HTTP_PORT = 8089

    # ============================================================
    # KV REGLER – skygge + avrundede hjørner
    # Skygge: en mørk RoundedRectangle forskjøvet 2dp ned.
    # Hoveddel: RoundedRectangle med bg_color oppå.
    # ============================================================
    Builder.load_string('''
<RBtn>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    bold: True
    canvas.before:
        Color:
            rgba: self.shadow_color
        RoundedRectangle:
            pos: self.x, self.y - dp(2)
            size: self.width, self.height
            radius: [self.radius]
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius]

<RToggle>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    bold: True
    canvas.before:
        Color:
            rgba: self.shadow_color
        RoundedRectangle:
            pos: self.x, self.y - dp(2)
            size: self.width, self.height
            radius: [self.radius]
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius]

<RBox>:
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius]
''')

    class RBtn(Button):
        bg_color = ListProperty(BTN)
        shadow_color = ListProperty(SHAD)
        radius = NumericProperty(dp(14))

    class RToggle(ToggleButton):
        bg_color = ListProperty(BTN)
        shadow_color = ListProperty(SHAD)
        radius = NumericProperty(dp(14))

    class RBox(BoxLayout):
        bg_color = ListProperty(BG2)
        radius = NumericProperty(dp(20))

    # === LYDKILDER ===
    AMBIENT_SOUNDS = [
        {"name":"--- Natur ---"},
        {"name":"Regn og torden","url":"https://archive.org/download/RainSound13/Gentle%20Rain%20and%20Thunder.mp3"},
        {"name":"Havboelger","url":"https://archive.org/download/naturesounds-soundtheraphy/Birds%20With%20Ocean%20Waves%20on%20the%20Beach.mp3"},
        {"name":"Nattregn","url":"https://archive.org/download/RainSound13/Night%20Rain%20Sound.mp3"},
        {"name":"Vind og storm","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/epic-storm-thunder-rainwindwaves-no-loops-106800.mp3"},
        {"name":"Nattlyder","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/ambience-crickets-chirping-in-very-light-rain-followed-by-gentle-rolling-thunder-10577.mp3"},
        {"name":"Havstorm","url":"https://archive.org/download/naturesounds-soundtheraphy/Sound%20Therapy%20-%20Sea%20Storm.mp3"},
        {"name":"Lett regn","url":"https://archive.org/download/naturesounds-soundtheraphy/Light%20Gentle%20Rain.mp3"},
        {"name":"Tordenstorm","url":"https://archive.org/download/RainSound13/Rain%20Sound%20with%20Thunderstorm.mp3"},
        {"name":"Urolig hav","url":"https://archive.org/download/RelaxingRainAndLoudThunderFreeFieldRecordingOfNatureSoundsForSleepOrMeditation/Relaxing%20Rain%20and%20Loud%20Thunder%20%28Free%20Field%20Recording%20of%20Nature%20Sounds%20for%20Sleep%20or%20Meditation%20Mp3%29.mp3"},
        {"name":"--- Horror ---"},
        {"name":"Skummel atmosfaere","url":"https://archive.org/download/creepy-music-sounds/Creepy%20music%20%26%20sounds.mp3"},
        {"name":"Uhyggelig drone","url":"https://archive.org/download/scary-sound-effects-8/Evil%20Demon%20Drone%20Movie%20Halloween%20Sounds.mp3"},
        {"name":"Mork spenning","url":"https://archive.org/download/scary-sound-effects-8/Dramatic%20Suspense%20Sound%20Effects.mp3"},
        {"name":"Horrorlyder","url":"https://archive.org/download/creepy-music-sounds/Horror%20Sound%20Effects.mp3"},
    ]

    # === KARAKTERFELT ===
    CHAR_INFO = [
        ("name","Navn"), ("type","Type"), ("occ","Yrke"), ("archetype","Arketype"),
        ("age","Alder"), ("residence","Bosted"), ("birthplace","Foedested"),
    ]
    CHAR_STATS = [
        ("str","STR"), ("con","CON"), ("siz","SIZ"), ("dex","DEX"),
        ("int","INT"), ("pow","POW"), ("app","APP"), ("edu","EDU"),
    ]
    CHAR_DERIVED = [
        ("hp","HP"), ("mp","MP"), ("san","SAN"), ("luck","Luck"),
        ("db","DB"), ("build","Build"), ("move","Move"), ("dodge","Dodge"),
    ]
    CHAR_TEXT = [
        ("weapons","Vaapen"), ("talents","Pulp Talents"),
        ("backstory","Bakgrunn"), ("notes","Notater"),
    ]
    SKILLS = [
        ("Accounting","05"), ("Appraise","05"), ("Archaeology","01"),
        ("Art/Craft:","05"), ("Art/Craft 2:","05"),
        ("Charm","15"), ("Climb","20"), ("Computer Use","00"),
        ("Credit Rating","00"), ("Cthulhu Mythos","00"),
        ("Demolitions","01"), ("Disguise","05"), ("Diving","01"),
        ("Dodge","DEX/2"), ("Drive Auto","20"),
        ("Elec. Repair","10"), ("Fast Talk","05"),
        ("Fighting (Brawl)","25"), ("Fighting:",""),
        ("Firearms (Handgun)","20"), ("Firearms (Rifle)","25"), ("Firearms:",""),
        ("First Aid","30"), ("History","05"),
        ("Intimidate","15"), ("Jump","20"),
        ("Language (Other):","01"), ("Language (Other) 2:","01"),
        ("Language (Own)","EDU"),
        ("Law","05"), ("Library Use","20"), ("Listen","20"),
        ("Locksmith","01"), ("Mech. Repair","10"), ("Medicine","01"),
        ("Natural World","10"), ("Navigate","10"), ("Occult","05"),
        ("Persuade","10"), ("Pilot:","01"),
        ("Psychoanalysis","01"), ("Psychology","10"),
        ("Read Lips","01"), ("Ride","05"),
        ("Science:","01"), ("Science 2:","01"),
        ("Sleight of Hand","10"), ("Spot Hidden","25"),
        ("Stealth","20"), ("Survival","10"),
        ("Swim","20"), ("Throw","20"), ("Track","10"),
    ]

    # === REGLER & REFERANSE ===
    # Komplett CoC 7e + Pulp Cthulhu keeper-referanse.
    # Kategorier -> underkategorier -> innhold (liste av strenger).
    RULES = [
      # ──────────────────────────────────────────
      # 1. GRUNNREGLER
      # ──────────────────────────────────────────
      ("Grunnregler", "GR", [
        ("Ferdighetskast", [
          "Rull d100 (percentile) mot skill-verdi.",
          "Lik eller under = suksess.",
          "",
          "Suksessnivaaer:",
          "  Critical: resultat = 01",
          "  Extreme: resultat <= skill / 5",
          "  Hard: resultat <= skill / 2",
          "  Regular: resultat <= skill",
          "  Failure: resultat > skill",
          "",
          "Automatisk suksess: 01 alltid suksess.",
          "Fumble (basert paa KRAV, ikke base skill):",
          "  Krav >= 50: kun 100 er fumble",
          "  Krav < 50: 96-100 er fumble",
          "  Eks: skill 60, Hard diff (krav 30)",
          "    -> fumble paa 96-100",
        ]),
        ("Vanskelighetsgrad", [
          "Keeper setter vanskelighetsgrad:",
          "  Regular: skill-verdi (standard)",
          "  Hard: halv skill-verdi",
          "  Extreme: femtedel av skill-verdi",
          "",
          "Brukes naar oppgaven er vanskelig,",
          "f.eks. laase opp kompleks laas = Hard,",
          "operere i moerke = Extreme.",
        ]),
        ("Bonus & Penalty", [
          "Bonus die: rull 2 tier-terninger,",
          "  bruk den LAVESTE.",
          "Penalty die: rull 2 tier-terninger,",
          "  bruk den HOEYESTE.",
          "",
          "Kan ha maks 2 bonus ELLER 2 penalty.",
          "Bonus og penalty kansellerer 1:1.",
          "",
          "Gis av Keeper basert paa omstendigheter:",
          "  Fordel: bonus (godt lys, tid, verktøy)",
          "  Ulempe: penalty (stress, dårlig sikt)",
        ]),
        ("Pushed Rolls", [
          "Spiller kan pushe ETT mislykket kast.",
          "Maa beskrive HVA de gjør annerledes.",
          "Keeper maa godkjenne pushen.",
          "",
          "Mislykket push = ALVORLIG konsekvens",
          "(verre enn vanlig feil).",
          "",
          "KAN IKKE pushes:",
          "  SAN-sjekker",
          "  Luck-sjekker",
          "  Kamp-kast",
          "  Allerede pushede kast",
        ]),
        ("Opposed Rolls", [
          "Begge parter ruller sine skills.",
          "Hoeyeste suksessnivaa vinner.",
          "Likt nivaa: hoeyeste skill-verdi vinner.",
          "Ingen suksess: status quo.",
          "",
          "Vanlige opposed rolls:",
          "  Sneak vs Listen",
          "  Fast Talk vs Psychology",
          "  Charm vs POW",
          "  STR vs STR (bryte, holde)",
          "  DEX vs DEX (gripe, unnvike)",
          "  Disguise vs Spot Hidden",
        ]),
        ("Luck", [
          "Luck-verdi: 3d6 x 5 (ved opprettelse).",
          "Luck-sjekk: d100 <= Luck.",
          "",
          "Spending Luck:",
          "  Etter et skill-kast: trekk Luck-poeng",
          "  1:1 for aa senke resultatet.",
          "  Eks: kast 55, skill 50 -> spend 5 Luck.",
          "",
          "Luck regenereres IKKE i standard CoC.",
          "Pulp: regenerer 2d10 Luck per sesjon.",
          "",
          "Group Luck: laveste Luck i gruppen",
          "  brukes for tilfeldige hendelser.",
        ]),
        ("Erfaring & utvikling", [
          "Etter scenario: marker brukte skills.",
          "Rull d100 for hver markert skill:",
          "  Resultat > skill = +1d10 til skill.",
          "  Resultat <= skill = ingen okning.",
          "",
          "Skill-maks: 99 (unntatt CM: 99).",
          "Alderseffekter kan senke stats.",
        ]),
      ]),
      # ──────────────────────────────────────────
      # 2. KAMP
      # ──────────────────────────────────────────
      ("Kamp", "KA", [
        ("Kampflyt", [
          "1. Alle handler i DEX-rekkefølge",
          "   (hoeyeste foerst).",
          "",
          "2. Hver deltaker faar 1 handling:",
          "   - Angripe (melee eller ranged)",
          "   - Flee (trekke seg ut)",
          "   - Manoever (trip, disarm, etc.)",
          "   - Kaste besverging",
          "   - Bruke gjenstand / First Aid",
          "   - Annet (snakke, lete, etc.)",
          "",
          "3. Forsvarer velger reaksjon:",
          "   - Dodge (unngaa)",
          "   - Fight Back (motangrep, kun melee)",
          "   - Ingenting (tar full skade)",
          "",
          "4. Gjenta til kamp er over.",
        ]),
        ("Melee", [
          "Angriper: rull Fighting-skill.",
          "Forsvarer velger:",
          "",
          "DODGE (opposed vs Dodge-skill):",
          "  Angriper vinner -> full skade",
          "  Forsvarer vinner -> unngaar angrepet",
          "  Begge feiler -> ingenting skjer",
          "",
          "FIGHT BACK (opposed vs Fighting):",
          "  Angriper vinner -> full skade",
          "  Forsvarer vinner -> forsvarer gjoer skade",
          "  Begge feiler -> ingenting skjer",
          "",
          "Dodge: 1 gratis per runde,",
          "  ekstra dodge koster handling neste runde.",
          "",
          "OUTNUMBERED:",
          "  Naar forsvarer allerede har dodget",
          "  eller fought back denne runden:",
          "  -> alle etterfølgende angrep faar",
          "     +1 bonus die.",
          "  Unntak: vesener med flere angrep/runde",
          "  kan dodge/fight back like mange ganger.",
          "  Gjelder IKKE skytevaapen.",
        ]),
        ("Skytevaapen", [
          "Rull Firearms-skill. INGEN opposed roll.",
          "Forsvarer kan KUN dodge ved point-blank.",
          "Ellers: bare dekke/bevege seg ut.",
          "",
          "Rekkevidde-modifikatorer:",
          "  Point-blank (inntil 1/5 range): +1 bonus",
          "  Mellomdistanse (base range): normal",
          "  Lang (inntil 2x base): +1 penalty",
          "  Ekstrem (inntil 4x base): +2 penalty",
          "",
          "Andre modifikatorer:",
          "  Bevegelig maal: +1 penalty",
          "  Stort maal: +1 bonus",
          "  Smalt maal: +1 penalty",
          "  Sikte (bruker handling): +1 bonus",
          "",
          "Impale: Extreme suksess med",
          "  gjennomborende vaapen",
          "  = maks vaapenskade + ekstra kast.",
        ]),
        ("Manoevrer", [
          "Fighting-manoever (i stedet for skade):",
          "  Trip/knockdown: maal faller",
          "  Disarm: maal mister vaapen",
          "  Hold/grapple: maal er fastholdt",
          "  Kaste: dytte/kaste motstanderen",
          "",
          "Krever: vinn opposed Fighting-sjekk.",
          "Build-differanse kan gi bonus/penalty:",
          "  Angriper Build >= maal + 2: +1 bonus",
          "  Angriper Build <= maal - 2: +1 penalty",
        ]),
        ("Damage Bonus (DB)", [
          "DB basert paa STR + SIZ:",
          "  2-64:    -2",
          "  65-84:   -1",
          "  85-124:  0",
          "  125-164: +1d4",
          "  165-204: +1d6",
          "  205-284: +2d6",
          "  285-364: +3d6",
          "",
          "Build-verdi:",
          "  DB -2: Build -2",
          "  DB -1: Build -1",
          "  DB 0:  Build 0",
          "  DB +1d4: Build 1",
          "  DB +1d6: Build 2",
          "  DB +2d6: Build 3",
        ]),
        ("Skade & heling", [
          "SKADENIVAAER:",
          "  Minor wound: tap < halve maks HP",
          "  Major wound: tap >= halve maks HP",
          "",
          "MAJOR WOUND-konsekvenser:",
          "  CON-sjekk eller besvime",
          "  First Aid/Medicine innen 1 runde",
          "  Maa stabiliseres ellers doer",
          "",
          "DYING (0 HP):",
          "  CON-sjekk per runde",
          "  Feil = doed",
          "  Suksess = holder ut 1 runde til",
          "",
          "HELING:",
          "  First Aid: +1 HP (1 forsøk/skade)",
          "  Medicine: +1d3 HP (etter First Aid)",
          "  Naturlig: 1 HP/uke (minor)",
          "  Major wound: 1d3 HP/uke m/pleie",
        ]),
        ("Automatiske vaapen", [
          "Burst: 3 kuler, +1 bonus die til skade.",
          "Full auto: velg antall maal,",
          "  fordel kuler, rull for hvert maal.",
          "  1 bonus die per 10 kuler paa maalet.",
          "",
          "Suppressive fire:",
          "  Dekker et omraade, alle i omraadet",
          "  maa Dodge eller ta 1 treff.",
          "  Bruker halve magasinet.",
        ]),
      ]),
      # ──────────────────────────────────────────
      # 3. SANITY
      # ──────────────────────────────────────────
      ("Sanity", "SA", [
        ("SAN-sjekk", [
          "Rull d100 <= naavaerende SAN.",
          "",
          "Format: 'X/Y'",
          "  Suksess: tap = X",
          "  Feil: tap = Y",
          "  Eks: '1/1d6' = suksess taper 1,",
          "    feil taper 1d6 SAN.",
          "",
          "Maks SAN = 99 - Cthulhu Mythos skill.",
          "",
          "SAN fumble: automatisk maks SAN-tap.",
          "",
          "Hardened: etter mange lignende sjokk",
          "  kan Keeper gi automatisk suksess",
          "  paa visse SAN-sjekker.",
        ]),
        ("Temporary Insanity", [
          "TRIGGER: 5+ SAN tapt i ETT kast.",
          "",
          "Keeper krever INT-sjekk:",
          "  INT-kast SUKSESS = investigator",
          "    innser sannheten -> MIDLERTIDIG GAL",
          "  INT-kast FEIL = fortrengt minne,",
          "    investigator forblir ved sine fulle fem",
          "",
          "Midlertidig insanity varer 1d10 timer.",
          "Begynner med Bout of Madness (se neste).",
          "Etterfoelges av Underlying Insanity.",
        ]),
        ("Bout of Madness", [
          "Oppstaar ved midlertidig insanity.",
          "Keeper velger Real-Time eller Summary.",
          "",
          "REAL-TIME (varig 1d10 runder):",
          "  1: Amnesi (husker ingenting)",
          "  2: Psychosomatisk (blind/doev/lam)",
          "  3: Vold (angrip naermeste)",
          "  4: Paranoia (alle er fiender)",
          "  5: Fysisk (kvalme/besvimelse)",
          "  6: Flukt (loep i panikk)",
          "  7: Hallusinasjoner",
          "  8: Ekko (gjenta handlinger meningloest)",
          "  9: Fobi (ny eller eksisterende)",
          "  10: Katatoni (stivner helt)",
        ]),
        ("Summary (1d10 timer)", [
          "Etter real-time bout, varig effekt:",
          "  1: Amnesi for hele hendelsen",
          "  2: Tvangstanker / ritualer",
          "  3: Hallusinasjoner (vedvarende)",
          "  4: Irrasjonelt hat/frykt",
          "  5: Fobi (spesifikk, ny eller forsterket)",
          "  6: Mani (kompulsiv adferd)",
          "  7: Paranoia (stoler paa ingen)",
          "  8: Dissosiasjon (fjern, uvirkelig)",
          "  9: Spiseforstyrrelse / soemnloes",
          "  10: Mythos-besettelse (studerer forbud)",
        ]),
        ("Fobier (utvalg)", [
          "Acrophobia - hoeydefobi",
          "Agoraphobia - aapne plasser",
          "Arachnophobia - edderkopper",
          "Claustrophobia - trange rom",
          "Demophobia - folkemengder",
          "Hemophobia - blod",
          "Hydrophobia - vann",
          "Mysophobia - smitte/skitt",
          "Necrophobia - doede/lik",
          "Nyctophobia - moerke",
          "Pyrophobia - ild",
          "Thalassophobia - havet/dypt vann",
          "Xenophobia - fremmede/ukjente",
          "Zoophobia - dyr",
        ]),
        ("Manier (utvalg)", [
          "Dipsomania - trang til alkohol",
          "Kleptomania - trang til aa stjele",
          "Megalomania - storhetstanker",
          "Mythomania - tvangsloegner",
          "Necromania - besettelse med doeden",
          "Pyromania - brannstifting",
          "Thanatomania - doedslengsel",
          "Xenomania - besettelse med fremmede",
        ]),
        ("Indefinite Insanity", [
          "Trigges naar investigator har tapt",
          "  1/5 av naavaerende SAN totalt.",
          "",
          "Effekt: langvarig galskap.",
          "  Spiller mister kontroll over karakter.",
          "  Keeper bestemmer adferd.",
          "  Varer maaneder/aar.",
          "",
          "Behandling:",
          "  Institusjonalisering",
          "  Psychoanalysis over tid",
          "  +1d3 SAN per maaned (maks)",
          "  Mislykket behandling: -1d6 SAN",
        ]),
        ("SAN-gjenoppretting", [
          "Psychoanalysis: +1d3 SAN (1/maaned)",
          "  Mislykket: -1d6 SAN!",
          "Self-help: forbedre skill = +1d3 SAN",
          "Fullfoere scenario: Keeper-beloenning",
          "",
          "Maks SAN = 99 - Cthulhu Mythos skill.",
          "Permanent SAN-tap kan ikke gjenopprettes",
          "  utover denne grensen.",
        ]),
      ]),
      # ──────────────────────────────────────────
      # 4. FORFØLGELSE (CHASE)
      # ──────────────────────────────────────────
      ("Forfoelgelse", "CH", [
        ("Oppsett", [
          "1. Type: fot eller kjoeretoey.",
          "2. Antall locations: 5-10 (Keeper velger).",
          "3. Deltagere:",
          "   Fot: MOV basert paa DEX, STR, SIZ.",
          "   Bil: speed-rating.",
          "4. Speed Roll (CON-sjekk):",
          "   Extreme suksess: +1 MOV for chasen",
          "   Suksess: ingen endring",
          "   Feil: -1 MOV for chasen",
          "   (kjoeretoey: Drive Auto i stedet)",
          "5. Sammenlign MOV: hoeyere MOV flykter",
          "   umiddelbart. Ellers -> full chase.",
          "6. Sett startposisjoner paa tracken.",
          "7. Plasser barrierer/farer paa locations.",
          "",
          "MOV (Movement Rate):",
          "  Hvis DEX & STR begge > SIZ: MOV 9",
          "  Hvis enten DEX eller STR > SIZ: MOV 8",
          "  Hvis begge <= SIZ: MOV 7",
          "  Alder 40-49: MOV -1",
          "  Alder 50-59: MOV -2 (etc.)",
        ]),
        ("Bevegelse & handlinger", [
          "Runder i DEX-rekkefoelge (hoey foerst).",
          "",
          "Hver runde kan deltaker:",
          "  - Bevege seg (MOV locations)",
          "  - Utfoere 1 handling:",
          "    Speed: CON-sjekk for +1 location",
          "    Angrep: Fighting/Firearms",
          "    Barriere: skill-sjekk for aa passere",
          "    Hinder: lag barriere for forfølger",
          "",
          "Hazard-handling koster handling OG",
          "  bevegelse den runden.",
        ]),
        ("Barrierer", [
          "Keeper plasserer barrierer paa locations.",
          "Skill-sjekk for aa passere:",
          "",
          "  Hopp over gjerde: Jump / Climb",
          "  Trang passasje: DEX / Dodge",
          "  Folkemengde: STR / Charm / Intimidate",
          "  Gjoerme/glatt: DEX / Luck",
          "  Laast doer: Locksmith / STR",
          "  Trafikkert gate: Drive Auto / DEX",
          "",
          "Feil: mist 1 location bevegelse.",
          "Fumble: fall, skade, fastklemt, etc.",
        ]),
        ("Seier & tap", [
          "FLUKT lykkes naar:",
          "  Avstand mellom = antall locations + 1",
          "  (forfølger kan ikke se maalet).",
          "",
          "FANGET naar:",
          "  Forfølger er paa SAMME location.",
          "  Kamp eller interaksjon kan begynne.",
          "",
          "UTMATTELSE:",
          "  CON-sjekk per runde etter runde 5.",
          "  Feil: MOV reduseres med 1.",
          "  MOV 0: kan ikke bevege seg.",
        ]),
      ]),
      # ──────────────────────────────────────────
      # 5. MAGI & TOMER
      # ──────────────────────────────────────────
      ("Magi & Tomer", "MA", [
        ("Besverging", [
          "Kostnader varierer per spell:",
          "  Magic Points (MP): vanligst",
          "  SAN: nesten alltid",
          "  HP: noen kraftige spells",
          "  POW: permanent offer (sjeldent)",
          "",
          "Casting time: 1 runde til flere timer.",
          "Noen krever komponenter/ritualer.",
          "",
          "MP regenereres: 1 per 2 timer hvile.",
          "MP = 0: bevisstloes i 1d8 timer.",
          "POW-offer: permanent, gjenopprettes IKKE.",
        ]),
        ("Mythos-tomer", [
          "Lesing av Mythos-tome:",
          "  Initial reading: uker til maaneder",
          "  Full study: maaneder til aar",
          "",
          "Beloenning: +Cthulhu Mythos skill.",
          "Kostnad: SAN-tap (varierer per tome).",
          "Kan ogsaa laere spells fra tomen.",
          "",
          "EKSEMPLER (CM-gevinst / SAN-tap):",
          "  Necronomicon (latin): +15 / -2d10",
          "  Necronomicon (original): +22 / -3d10",
          "  De Vermis Mysteriis: +10 / -1d8",
          "  Book of Eibon: +11 / -2d4",
          "  Cultes des Goules: +9 / -1d8",
          "  Pnakotiske man.: +7 / -1d6",
          "  Unaussprechlichen Kulten: +9 / -2d4",
          "  Revelations of Glaaki: +7 / -1d4",
          "  Book of Dzyan: +5 / -1d4",
        ]),
        ("Mythos-vesener (SAN)", [
          "Vesen: suksess / feil SAN-tap",
          "",
          "  Byakhee: 1/1d6",
          "  Dark Young: 0/1d8",
          "  Deep One: 0/1d6",
          "  Elder Thing: 1/1d6",
          "  Flying Polyp: 1d3/1d20",
          "  Ghoul: 0/1d6",
          "  Great Race: 0/1d6",
          "  Hound of Tindalos: 1d3/1d20",
          "  Mi-Go: 0/1d6",
          "  Nightgaunt: 0/1d6",
          "  Shoggoth: 1d6/1d20",
          "  Star Spawn: 1d6/1d20",
          "  Star Vampire: 1/1d8",
          "",
          "  Great Old Ones:",
          "  Cthulhu: 1d10/1d100",
          "  Hastur: 1d10/1d100",
          "  Nyarlathotep: 0/1d10 (varierer)",
          "  Yog-Sothoth: 1d10/1d100",
        ]),
      ]),
      # ──────────────────────────────────────────
      # 6. PULP CTHULHU
      # ──────────────────────────────────────────
      ("Pulp Cthulhu", "PU", [
        ("Pulp-regler", [
          "Heroer er TØFFERE enn standard CoC.",
          "",
          "HP: (CON + SIZ) / 5 (avrundet ned)",
          "  Standard CoC: (CON+SIZ) / 10",
          "  Effektivt DOBBEL HP.",
          "  Valgfritt lavnivaa: (CON+SIZ)/10",
          "",
          "Luck: 2d6+6 x 5 (hoeyere enn standard)",
          "  Standard CoC: 3d6 x 5",
          "  Regenerer 2d10 Luck per sesjon.",
          "",
          "First Aid: +1d4 HP (standard: +1 HP)",
          "  Extreme suksess: automatisk 4 HP.",
          "Medicine: +1d4 HP (standard: +1d3)",
          "",
          "Pulp Talents: 2 stk (standard).",
          "  Lavnivaa pulp: 1 talent",
          "  Hoynivaa pulp: 3 talents",
          "",
          "Kampkast kan IKKE pushes (som standard).",
          "Spending Luck: kan ogsaa brukes til:",
          "  - Unngaa dying (5 Luck = stabiliser)",
          "  - Redusere skade (etter kast)",
        ]),
        ("Arketyper", [
          "Velg 1 arketype ved opprettelse.",
          "Gir bonuser og Pulp Talents.",
          "",
          "  Adventurer: allsidig eventyrer",
          "  Beefcake: fysisk sterk, ekstra HP",
          "  Bon Vivant: sjarmerende, sosialt dyktig",
          "  Cold Blooded: hensynsloes, presist",
          "  Dreamer: kreativ, Mythos-sensitiv",
          "  Egghead: intellektuell, kunnskapsrik",
          "  Explorer: utforsker, overlevelse",
          "  Femme/Homme Fatale: forfoerende",
          "  Grease Monkey: mekaniker, oppfinnsom",
          "  Hard Boiled: tøff, utholdende",
          "  Harlequin: entertainer, distraherende",
          "  Hunter: jeger, naturkyndig",
          "  Mystic: spirituell, spaadomsevne",
          "  Outsider: ensom, selvlaert",
          "  Reckless: vaaghals, risikotaker",
          "  Sidekick: lojal, støttende",
          "  Swashbuckler: akrobatisk fighter",
          "  Thrill Seeker: adrenalinjansen",
          "  Two-Fisted: naevekamp-spesialist",
        ]),
        ("Pulp Talents (utvalg)", [
          "FYSISK:",
          "  Brawler: +1d6 melee-skade",
          "  Iron Jaw: ignorer 1 K.O. per sesjon",
          "  Quick Healer: dobbel heling",
          "  Tough Guy: +1d6 ekstra HP",
          "",
          "MENTAL:",
          "  Arcane Insight: +2 Cthulhu Mythos",
          "  Gadget: lag improvisert gjenstand",
          "  Photographic Memory: husk alt",
          "  Psychic Power: sjette sans",
          "",
          "SOSIAL:",
          "  Smooth Talker: re-roll 1 sosial sjekk",
          "  Master of Disguise: +1 bonus Disguise",
          "  Lucky: +1d10 ekstra Luck-regen",
          "",
          "KAMP:",
          "  Rapid Fire: ekstra skudd uten penalty",
          "  Outmaneuver: +1 bonus paa manoevrer",
          "  Fleet Footed: +1 MOV i chase",
        ]),
      ]),
      # ──────────────────────────────────────────
      # 7. REFERANSETABELLER
      # ──────────────────────────────────────────
      ("Tabeller", "RE", [
        ("Vaapentabell - melee", [
          "Vaapen: skade / attacks",
          "",
          "  Unarmed (knytneve): 1d3+DB / 1",
          "  Head butt: 1d4+DB / 1",
          "  Kick: 1d4+DB / 1",
          "  Grapple: special / 1",
          "  Kniv (liten): 1d4+DB / 1",
          "  Kniv (stor): 1d6+DB / 1",
          "  Klubbe/fleskepost: 1d8+DB / 1",
          "  Sverd/sabel: 1d8+DB / 1",
          "  Øks (stor): 1d8+2+DB / 1",
          "  Spyd: 1d8+1+DB / 1",
          "  Motorsag: 2d8 / 1",
        ]),
        ("Vaapentabell - skytevaapen", [
          "Vaapen: skade / range / shots",
          "",
          "  Derringer (.41): 1d8 / 10y / 1",
          "  Revolver (.32): 1d8 / 15y / 6",
          "  Revolver (.45): 1d10+2 / 15y / 6",
          "  Pistol (9mm): 1d10 / 15y / 8",
          "  Pistol (.45 auto): 1d10+2 / 15y / 7",
          "  Rifle (.30): 2d6+4 / 110y / 5",
          "  Rifle (.303): 2d6+4 / 110y / 10",
          "  Shotgun (12g): 4d6/2d6/1d6",
          "    (range: 10/20/50 yard)",
          "  Thompson SMG: 1d10+2 / 20y / 20",
          "  Dynamitt: 5d6 / thrown / 1",
          "    (radius 5 yard)",
        ]),
        ("SAN-tap oversikt", [
          "HENDELSE: suksess / feil",
          "",
          "  Se et lik: 0/1d3",
          "  Se en venn doe: 0/1d4",
          "  Se noe uforklarlig: 0/1d2",
          "  Se et grusomt drap: 1/1d4+1",
          "  Se massedrap: 1d3/1d6+1",
          "  Finne en grusomhet: 0/1d3",
          "",
          "  Oppdage Mythos-bevis: 0/1d2",
          "  Laese Mythos-tome: 1/1d4",
          "  Se Mythos-ritual: 1/1d6",
          "  Bli utsatt for besverging: 1/1d6",
        ]),
        ("Alderseffekter", [
          "Alder pavirker stats ved opprettelse:",
          "",
          "  15-19: -5 SIZ/STR, -5 EDU,",
          "    Luck: rull 2x, bruk best",
          "  20-39: EDU-forbedring: +1",
          "  40-49: EDU +2, -5 fritt STR/CON/DEX,",
          "    APP -5, MOV -1",
          "  50-59: EDU +3, -10 fritt STR/CON/DEX,",
          "    APP -10, MOV -2",
          "  60-69: EDU +4, -20 fritt STR/CON/DEX,",
          "    APP -15, MOV -3",
          "  70-79: EDU +4, -40 fritt STR/CON/DEX,",
          "    APP -20, MOV -4",
          "  80-89: EDU +4, -80 fritt STR/CON/DEX,",
          "    APP -25, MOV -5",
        ]),
        ("Credit Rating", [
          "Credit Rating = formue/sosial status:",
          "",
          "  0: fattig, hjemlos",
          "  1-9: fattig, kun nødvendig",
          "  10-49: gjennomsnittlig",
          "  50-89: velstaaende",
          "  90-98: rik",
          "  99: enormt rik",
          "",
          "Spending level (per dag):",
          "  CR 0: $0.50",
          "  CR 1-9: $2",
          "  CR 10-49: $10",
          "  CR 50-89: $50",
          "  CR 90-98: $250",
          "  CR 99: $5000",
        ]),
      ]),
    ]

    def request_android_permissions():
        if platform != 'android':
            return
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES,
                Permission.READ_MEDIA_AUDIO,
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.ACCESS_WIFI_STATE,
                Permission.CHANGE_WIFI_MULTICAST_STATE
            ])
        except:
            pass

    def load_json(p, d=None):
        try:
            with open(p, 'r') as f:
                return json.load(f)
        except:
            return d if d is not None else []

    def save_json(p, d):
        try:
            with open(p, 'w') as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
        except:
            pass

    # === HJELPEFUNKSJONER ===

    def mkbtn(text, cb=None, accent=False, danger=False, small=False, **kw):
        c = GOLD if accent else (RED if danger else TXT)
        b = RBtn(text=text, color=c, bg_color=BTN,
                 font_size=sp(11) if small else sp(13), **kw)
        if cb:
            b.bind(on_release=lambda x: cb())
        return b

    def mklbl(text, color=TXT, size=12, bold=False, h=None, wrap=False):
        kw = {'text': text, 'font_size': sp(size), 'color': color, 'bold': bold}
        if h:
            kw['size_hint_y'] = None
            kw['height'] = dp(h)
        l = Label(**kw)
        if wrap:
            l.halign = 'left'
            l.text_size = (Window.width - dp(24), None)
            l.size_hint_y = None
            l.bind(texture_size=l.setter('size'))
        return l

    def mksep(h=6):
        return Widget(size_hint_y=None, height=dp(h))

    def mkvol(callback, value=0.7):
        vr = BoxLayout(size_hint_y=None, height=dp(32), padding=[dp(10), 0])
        vr.add_widget(Label(text="Vol", color=DIM, size_hint_x=0.08, font_size=sp(10)))
        sl = Slider(min=0, max=1, value=value, size_hint_x=0.92)
        sl.bind(value=lambda s, v: callback(v))
        vr.add_widget(sl)
        return vr

    # === SERVER / CAST / PLAYERS ===
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, f, *a):
            pass

    class MediaServer:
        def __init__(self):
            self._h = None
        def start(self):
            if self._h:
                return
            try:
                h = partial(QuietHandler, directory=BASE_DIR)
                self._h = HTTPServer(('0.0.0.0', HTTP_PORT), h)
                threading.Thread(target=self._h.serve_forever, daemon=True).start()
            except:
                pass
        def stop(self):
            if self._h:
                self._h.shutdown()
                self._h = None
        @staticmethod
        def ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                r = s.getsockname()[0]
                s.close()
                return r
            except:
                return "127.0.0.1"
        def url(self, fp):
            return f"http://{self.ip()}:{HTTP_PORT}/{os.path.relpath(fp, BASE_DIR)}"

    class CastMgr:
        def __init__(self):
            self.devices = {}
            self.cc = None
            self.mc = None
            self._br = None
        def scan(self, cb=None):
            if not CAST_AVAILABLE:
                return
            self.devices = {}
            def _s():
                try:
                    ccs, br = pychromecast.get_chromecasts()
                    self._br = br
                except:
                    ccs = []
                for c in ccs:
                    self.devices[c.cast_info.friendly_name] = c
                if cb:
                    Clock.schedule_once(lambda dt: cb(list(self.devices.keys())), 0)
            threading.Thread(target=_s, daemon=True).start()
        def connect(self, name, cb=None):
            if name not in self.devices:
                return
            def _c():
                try:
                    c = self.devices[name]
                    c.wait()
                    self.cc = c
                    self.mc = c.media_controller
                    ok = True
                except:
                    ok = False
                if cb:
                    Clock.schedule_once(lambda dt: cb(ok), 0)
            threading.Thread(target=_c, daemon=True).start()
        def cast_img(self, url, cb=None):
            if not self.mc:
                return
            def _c():
                try:
                    self.mc.play_media(url, 'image/jpeg')
                    self.mc.block_until_active()
                    ok = True
                except:
                    ok = False
                if cb:
                    Clock.schedule_once(lambda dt: cb(ok), 0)
            threading.Thread(target=_c, daemon=True).start()
        def disconnect(self):
            try:
                if self._br:
                    self._br.stop_discovery()
                if self.cc:
                    self.cc.disconnect()
            except:
                pass
            self.cc = None
            self.mc = None

    class APlayer:
        def __init__(self):
            self.mp = None
            self.is_playing = False
            self._v = 0.7
        def play(self, path):
            self.stop()
            try:
                self.mp = MediaPlayer()
                self.mp.setDataSource(path)
                self.mp.setVolume(self._v, self._v)
                self.mp.prepare()
                self.mp.start()
                self.is_playing = True
            except:
                self.mp = None
                self.is_playing = False
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying():
                        self.mp.stop()
                    self.mp.release()
                except:
                    pass
                self.mp = None
            self.is_playing = False
        def pause(self):
            if self.mp and self.is_playing:
                try:
                    self.mp.pause()
                    self.is_playing = False
                except:
                    pass
        def resume(self):
            if self.mp and not self.is_playing:
                try:
                    self.mp.start()
                    self.is_playing = True
                except:
                    pass
        def vol(self, v):
            self._v = v
            if self.mp:
                try:
                    self.mp.setVolume(v, v)
                except:
                    pass

    class SPlayer:
        def __init__(self):
            self.mp = None
            self.is_playing = False
            self._v = 0.5
        def play_url(self, url):
            self.stop()
            if not USE_JNIUS:
                return False
            def _s():
                try:
                    self.mp = MediaPlayer()
                    self.mp.setDataSource(url)
                    self.mp.setVolume(self._v, self._v)
                    self.mp.prepare()
                    self.mp.start()
                    self.is_playing = True
                    log("Stream OK")
                except Exception as e:
                    log(f"Stream err: {e}")
                    if self.mp:
                        try: self.mp.release()
                        except: pass
                        self.mp = None
                    self.is_playing = False
            threading.Thread(target=_s, daemon=True).start()
            return True
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying():
                        self.mp.stop()
                    self.mp.release()
                except:
                    pass
                self.mp = None
            self.is_playing = False
        def vol(self, v):
            self._v = v
            if self.mp:
                try:
                    self.mp.setVolume(v, v)
                except:
                    pass

    class FPlayer:
        def __init__(self):
            from kivy.core.audio import SoundLoader
            self.SL = SoundLoader
            self.snd = None
            self.is_playing = False
            self._v = 0.7
        def play(self, path):
            self.stop()
            self.snd = self.SL.load(path)
            if self.snd:
                self.snd.volume = self._v
                self.snd.play()
                self.is_playing = True
        def stop(self):
            if self.snd:
                try: self.snd.stop()
                except: pass
                self.snd = None
            self.is_playing = False
        def pause(self):
            if self.snd and self.is_playing:
                self.snd.stop()
                self.is_playing = False
        def resume(self):
            if self.snd and not self.is_playing:
                self.snd.play()
                self.is_playing = True
        def vol(self, v):
            self._v = v
            if self.snd:
                self.snd.volume = v

    # ============================================================
    class EldritchApp(App):
        def build(self):
            log("=== BUILD (v0.2 dark + splash) ===")
            Window.clearcolor = BG
            self.title = "Eldritch Portal"
            self.tracks = []
            self.ct = -1
            self.sel_img = None
            self.auto_cast = True
            self.cur_folder = IMG_DIR
            self.player = APlayer() if USE_JNIUS else FPlayer()
            self.streamer = SPlayer()
            self.cast = CastMgr()
            self.server = MediaServer()
            self.chars = load_json(CHAR_FILE, [])
            self.edit_idx = None

            # FloatLayout som rot – lar oss legge splash oppå
            wrapper = FloatLayout()

            main = BoxLayout(orientation='vertical', spacing=0,
                             size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            main.add_widget(Widget(size_hint_y=None, height=dp(30)))

            # FANER
            tabs = RBox(size_hint_y=None, height=dp(52), spacing=dp(4),
                        padding=[dp(8), 0], bg_color=BTN)
            self._tabs = {}
            for key, txt in [('img','Bilder'),('mus','Musikk'),('amb','Ambient'),('tool','Karakter'),('rules','Regler'),('cast','Cast')]:
                active = key == 'img'
                b = RToggle(text=txt, group='tabs',
                            state='down' if active else 'normal',
                            bg_color=BTNH if active else BTN,
                            color=GOLD if active else DIM,
                            font_size=sp(11))
                b.bind(state=self._tab_color)
                b.bind(on_release=lambda x, k=key: self._tab(k))
                tabs.add_widget(b)
                self._tabs[key] = b
            main.add_widget(tabs)

            # HOVEDINNHOLD
            self.content = RBox(bg_color=BG2)
            main.add_widget(self.content)

            # MINI-PLAYER
            mp = RBox(size_hint_y=None, height=dp(48), spacing=dp(6),
                      padding=[dp(10), dp(4)], bg_color=BTN)
            mp.add_widget(Widget(size_hint_x=None, width=dp(4)))
            self.mp_lbl = Label(text="Ingen musikk", font_size=sp(11),
                                color=DIM, size_hint_x=0.45, halign='left')
            self.mp_lbl.bind(size=self.mp_lbl.setter('text_size'))
            mp.add_widget(self.mp_lbl)
            for t, cb in [("<<", self.prev_track), (">>", self.next_track)]:
                mp.add_widget(mkbtn(t, cb, small=True, size_hint_x=None, width=dp(44)))
            self.mp_btn = mkbtn("Play", self.toggle_play, accent=True,
                                small=True, size_hint_x=None, width=dp(60))
            mp.add_widget(self.mp_btn)
            main.add_widget(mp)

            self.status = Label(text="", font_size=sp(10), color=DIM,
                                size_hint_y=None, height=dp(20))
            main.add_widget(self.status)

            wrapper.add_widget(main)

            # === SPLASH SCREEN ===
            self.splash = RBox(bg_color=BG, radius=0,
                               orientation='vertical',
                               size_hint=(1, 1),
                               pos_hint={'x': 0, 'y': 0})
            # Sentrert innhold
            self.splash.add_widget(Widget())  # fyll topp
            t1 = Label(text="ELDRITCH", font_size=sp(42), color=GOLD,
                       bold=True, size_hint_y=None, height=dp(60),
                       halign='center')
            t1.bind(size=t1.setter('text_size'))
            self.splash.add_widget(t1)
            t2 = Label(text="PORTAL", font_size=sp(42), color=GDIM,
                       bold=True, size_hint_y=None, height=dp(60),
                       halign='center')
            t2.bind(size=t2.setter('text_size'))
            self.splash.add_widget(t2)
            sub = Label(text="Keeper Companion Tool", font_size=sp(13),
                        color=DIM, size_hint_y=None, height=dp(30),
                        halign='center')
            sub.bind(size=sub.setter('text_size'))
            self.splash.add_widget(sub)
            self.splash.add_widget(Widget())  # fyll bunn
            wrapper.add_widget(self.splash)

            self._tab('img')
            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init(), 3)
            # Fade ut splash etter 2.5 sek
            Clock.schedule_once(self._dismiss_splash, 2.5)
            return wrapper

        def _dismiss_splash(self, dt):
            if self.splash:
                anim = Animation(opacity=0, duration=0.8)
                def _remove(*a):
                    if self.splash.parent:
                        self.splash.parent.remove_widget(self.splash)
                    self.splash = None
                anim.bind(on_complete=_remove)
                anim.start(self.splash)

        def _tab_color(self, btn, state):
            if state == 'down':
                btn.bg_color = BTNH
                btn.color = GOLD
            else:
                btn.bg_color = BTN
                btn.color = DIM

        def _init(self):
            self.server.start()
            self._load_imgs()
            self._load_tracks()
            self.status.text = f"IP: {MediaServer.ip()}  |  Cast: {'Ja' if CAST_AVAILABLE else 'Nei'}"

        def _tab(self, k):
            self.content.clear_widgets()
            builders = {
                'img': self._mk_img, 'mus': self._mk_mus,
                'amb': self._mk_amb, 'tool': self._mk_tool,
                'rules': self._mk_rules, 'cast': self._mk_cast,
            }
            if k in builders:
                self.content.add_widget(builders[k]())

        # ---------- BILDER ----------
        def _mk_img(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            # Svart bakgrunn bak preview-bildet
            preview_box = RBox(size_hint_y=0.4, bg_color=BLK, radius=dp(12))
            self.preview = Image(allow_stretch=True, keep_ratio=True,
                                 color=[1, 1, 1, 0] if not self.sel_img else [1, 1, 1, 1])
            if self.sel_img:
                self.preview.source = self.sel_img
            preview_box.add_widget(self.preview)
            p.add_widget(preview_box)
            p.add_widget(Label(text="ELDRITCH PORTAL", font_size=sp(18), color=GDIM,
                               bold=True, size_hint_y=None, height=dp(28)))
            self.img_lbl = Label(text="", font_size=sp(12), color=DIM,
                                 size_hint_y=None, height=dp(20))
            p.add_widget(self.img_lbl)
            nav = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6), padding=[dp(6), 0])
            self.path_lbl = Label(text="", font_size=sp(10), color=DIM, size_hint_x=0.35)
            nav.add_widget(self.path_lbl)
            nav.add_widget(mkbtn("Opp", self.folder_up, small=True, size_hint_x=0.2))
            self.ac_btn = mkbtn("AC:PA", self._toggle_ac, accent=True, small=True, size_hint_x=0.25)
            nav.add_widget(self.ac_btn)
            nav.add_widget(mkbtn("Oppdater", self._load_imgs, small=True, size_hint_x=0.2))
            p.add_widget(nav)
            scroll = ScrollView(size_hint_y=0.4)
            self.img_grid = GridLayout(cols=3, spacing=dp(6), padding=dp(6), size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid)
            p.add_widget(scroll)
            self._load_imgs()
            return p

        def _load_imgs(self):
            if not hasattr(self, 'img_grid'):
                return
            self.img_grid.clear_widgets()
            f = self.cur_folder
            rel = os.path.relpath(f, IMG_DIR) if f != IMG_DIR else ""
            self.path_lbl.text = f"/{rel}" if rel else "/"
            try:
                if not os.path.exists(f):
                    return
                items = sorted(os.listdir(f))
                dirs = [d for d in items if os.path.isdir(os.path.join(f, d)) and not d.startswith('.')]
                imgs = [x for x in items if x.lower().endswith(IMG_EXT)]
                self.img_lbl.text = f"{len(dirs)} mapper, {len(imgs)} bilder"
                for d in dirs:
                    self.img_grid.add_widget(
                        mkbtn(f"[{d}]", lambda dn=d: self._enter(dn),
                              accent=True, small=True, size_hint_y=None, height=dp(70)))
                for fn in imgs:
                    path = os.path.join(f, fn)
                    img = Image(source=path, allow_stretch=True, keep_ratio=True,
                                size_hint_y=None, height=dp(100), mipmap=True)
                    img._path = path
                    img.bind(on_touch_down=self._img_touch)
                    self.img_grid.add_widget(img)
            except Exception as e:
                log(f"load_imgs: {e}")

        def _img_touch(self, w, touch):
            if w.collide_point(*touch.pos):
                self._sel_img(w._path)
                return True
            return False

        def _enter(self, name):
            self.cur_folder = os.path.join(self.cur_folder, name)
            self._load_imgs()

        def folder_up(self):
            if self.cur_folder != IMG_DIR:
                self.cur_folder = os.path.dirname(self.cur_folder)
                self._load_imgs()

        def _sel_img(self, path):
            self.sel_img = path
            self.img_lbl.text = os.path.basename(path)
            self.img_lbl.color = GOLD
            Animation.cancel_all(self.preview, 'opacity')
            fade_out = Animation(opacity=0, duration=0.3)
            def _swap(*a):
                self.preview.source = path
                Animation(opacity=1, duration=0.4).start(self.preview)
                if self.auto_cast and self.cast.mc:
                    self.img_lbl.text = "Caster..."
                    self.cast.cast_img(self.server.url(path),
                                       cb=lambda ok: setattr(self.img_lbl, 'text',
                                                             "Castet!" if ok else "Feilet"))
            fade_out.bind(on_complete=_swap)
            self.preview.color = [1, 1, 1, 1]
            fade_out.start(self.preview)

        def _toggle_ac(self):
            self.auto_cast = not self.auto_cast
            self.ac_btn.text = f"AC:{'PA' if self.auto_cast else 'AV'}"

        # ---------- MUSIKK ----------
        def _mk_mus(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            self.trk_lbl = Label(text="Velg et spor", font_size=sp(14), color=DIM,
                                 size_hint_y=None, height=dp(34), bold=True)
            p.add_widget(self.trk_lbl)
            ctrl = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            ctrl.add_widget(mkbtn("<<", self.prev_track, small=True))
            ctrl.add_widget(mkbtn("Play", self.toggle_play, accent=True))
            ctrl.add_widget(mkbtn(">>", self.next_track, small=True))
            ctrl.add_widget(mkbtn("Stopp", self.stop_music, danger=True, small=True))
            p.add_widget(ctrl)
            p.add_widget(mkvol(self.player.vol, 0.7))
            scroll = ScrollView()
            self.trk_grid = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            self.trk_grid.bind(minimum_height=self.trk_grid.setter('height'))
            scroll.add_widget(self.trk_grid)
            p.add_widget(scroll)
            self._load_tracks()
            return p

        def _load_tracks(self):
            if not hasattr(self, 'trk_grid'):
                return
            self.trk_grid.clear_widgets()
            self.tracks = []
            try:
                if not os.path.exists(MUSIC_DIR):
                    return
                fl = sorted([f for f in os.listdir(MUSIC_DIR)
                             if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                self.trk_lbl.text = f"{len(fl)} spor"
                for i, fn in enumerate(fl):
                    self.tracks.append(os.path.join(MUSIC_DIR, fn))
                    self.trk_grid.add_widget(
                        mkbtn(fn, lambda idx=i: self.play_track(idx),
                              small=True, size_hint_y=None, height=dp(42)))
            except Exception as e:
                log(f"load_tracks: {e}")

        def play_track(self, idx):
            if idx < 0 or idx >= len(self.tracks):
                return
            self.ct = idx
            self.player.play(self.tracks[idx])
            n = os.path.basename(self.tracks[idx])
            self.trk_lbl.text = f"Spiller: {n}"
            self.trk_lbl.color = GOLD
            self.mp_lbl.text = n
            self.mp_btn.text = "Pause"

        def toggle_play(self):
            if not self.player.is_playing and self.ct < 0:
                if self.tracks:
                    self.play_track(0)
                return
            if self.player.is_playing:
                self.player.pause()
                self.mp_btn.text = "Play"
            else:
                self.player.resume()
                self.mp_btn.text = "Pause"

        def stop_music(self):
            self.player.stop()
            self.mp_btn.text = "Play"
            self.mp_lbl.text = "Stoppet"
            self.trk_lbl.text = "Stoppet"

        def next_track(self):
            if self.tracks:
                self.play_track((self.ct + 1) % len(self.tracks))

        def prev_track(self):
            if self.tracks:
                self.play_track((self.ct - 1) % len(self.tracks))

        # ---------- AMBIENT ----------
        def _mk_amb(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for snd in AMBIENT_SOUNDS:
                if 'url' not in snd:
                    g.add_widget(mklbl(snd['name'], color=GDIM, size=11, bold=True, h=24))
                else:
                    g.add_widget(
                        mkbtn(snd['name'],
                              lambda u=snd['url'], n=snd['name']: self._pa(u, n),
                              small=True, size_hint_y=None, height=dp(40)))
            scroll.add_widget(g)
            p.add_widget(scroll)
            p.add_widget(mkbtn("Stopp ambient", self._sa, danger=True,
                               size_hint_y=None, height=dp(44)))
            p.add_widget(mkvol(self.streamer.vol, 0.5))
            self.amb_lbl = mklbl("", color=DIM, size=11, h=20)
            p.add_widget(self.amb_lbl)
            p.add_widget(Widget(size_hint_y=1))
            return p

        def _pa(self, url, name):
            self._an = name
            self._ac = 0
            self.amb_lbl.text = f"Laster: {name}..."
            if self.streamer.play_url(url):
                Clock.schedule_interval(self._poll, 2)

        def _poll(self, dt):
            self._ac += 1
            if self.streamer.is_playing:
                self.amb_lbl.text = f"Spiller: {self._an}"
                self.amb_lbl.color = GRN
                return False
            if self._ac >= 10:
                self.amb_lbl.text = f"Feilet: {self._an}"
                self.amb_lbl.color = RED
                return False
            self.amb_lbl.text = f"Laster: {self._an} ({self._ac*2}s)..."
            return True

        def _sa(self):
            self.streamer.stop()
            self.amb_lbl.text = "Stoppet"
            self.amb_lbl.color = DIM

        # ---------- REGLER ----------
        def _mk_rules(self):
            """Regelreferanse med 3-nivaa navigasjon:
               Kategorier -> Underkategorier -> Innhold."""
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))
            self._rules_area = BoxLayout()
            p.add_widget(self._rules_area)
            self._rules_show_categories()
            return p

        def _rules_show_categories(self):
            """Nivaa 1: vis alle hovedkategorier som grid."""
            self._rules_area.clear_widgets()
            outer = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))
            outer.add_widget(mklbl("REGLER & REFERANSE", color=GOLD, size=16, bold=True, h=32))
            outer.add_widget(mksep(4))

            scroll = ScrollView()
            g = GridLayout(cols=2, spacing=dp(8), padding=dp(6), size_hint_y=None,
                           row_default_height=dp(56))
            g.bind(minimum_height=g.setter('height'))

            cat_colors = [BLUE, RED, GOLD, GDIM, BLUE, GOLD, DIM]
            for i, (cat_name, short, subs) in enumerate(RULES):
                btn = RBtn(text=f"[{short}]\n{cat_name}", bg_color=BTN,
                           color=cat_colors[i % len(cat_colors)],
                           font_size=sp(12), halign='center',
                           size_hint_y=None, height=dp(56))
                btn.bind(on_release=lambda x, idx=i: self._rules_show_subs(idx))
                g.add_widget(btn)

            scroll.add_widget(g)
            outer.add_widget(scroll)
            self._rules_area.add_widget(outer)

        def _rules_show_subs(self, cat_idx):
            """Nivaa 2: vis underkategorier for valgt kategori."""
            cat_name, short, subs = RULES[cat_idx]
            self._rules_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))

            # Header med tilbake-knapp
            hdr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            hdr.add_widget(mkbtn("< Tilbake", self._rules_show_categories,
                                 small=True, size_hint_x=0.35))
            hdr.add_widget(mklbl(cat_name, color=GOLD, size=15, bold=True))
            p.add_widget(hdr)
            p.add_widget(mksep(4))

            # Underkategori-liste
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for j, (sub_name, content) in enumerate(subs):
                n_lines = len([l for l in content if l])
                btn = mkbtn(f"  {sub_name}  ({n_lines} pkt)",
                            lambda ci=cat_idx, si=j: self._rules_show_content(ci, si),
                            small=True, size_hint_y=None, height=dp(44))
                btn.halign = 'left'
                g.add_widget(btn)

            scroll.add_widget(g)
            p.add_widget(scroll)
            self._rules_area.add_widget(p)

        def _rules_show_content(self, cat_idx, sub_idx):
            """Nivaa 3: vis regelinnhold."""
            cat_name, short, subs = RULES[cat_idx]
            sub_name, content = subs[sub_idx]

            self._rules_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))

            # Header med tilbake + navigering
            hdr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
            hdr.add_widget(mkbtn("< Tilbake",
                                 lambda: self._rules_show_subs(cat_idx),
                                 small=True, size_hint_x=0.3))
            # Forrige/neste underkategori
            if sub_idx > 0:
                hdr.add_widget(mkbtn("<<",
                                     lambda: self._rules_show_content(cat_idx, sub_idx - 1),
                                     small=True, size_hint_x=None, width=dp(40)))
            else:
                hdr.add_widget(Widget(size_hint_x=None, width=dp(40)))

            hdr.add_widget(mklbl(sub_name, color=GOLD, size=13, bold=True))

            if sub_idx < len(subs) - 1:
                hdr.add_widget(mkbtn(">>",
                                     lambda: self._rules_show_content(cat_idx, sub_idx + 1),
                                     small=True, size_hint_x=None, width=dp(40)))
            else:
                hdr.add_widget(Widget(size_hint_x=None, width=dp(40)))
            p.add_widget(hdr)

            # Breadcrumb
            p.add_widget(mklbl(f"{cat_name}  >  {sub_name}",
                               color=DIM, size=10, h=18))
            p.add_widget(mksep(2))

            # Innhold
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(1), padding=dp(8), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for line in content:
                if line == "":
                    g.add_widget(mksep(8))
                elif line.startswith("  "):
                    g.add_widget(mklbl(line, color=DIM, size=12, h=20))
                else:
                    g.add_widget(mklbl(line, color=TXT, size=13, h=22))

            g.add_widget(mksep(30))
            scroll.add_widget(g)
            p.add_widget(scroll)
            self._rules_area.add_widget(p)

        # ---------- CAST ----------
        def _mk_cast(self):
            p = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
            if not CAST_AVAILABLE:
                p.add_widget(mklbl("Casting utilgjengelig\npychromecast mangler", color=DIM, size=13))
                return p
            self.cast_lbl = mklbl("Ikke tilkoblet", color=DIM, size=13, h=30)
            p.add_widget(self.cast_lbl)
            p.add_widget(mkbtn("Sok etter enheter", self._scan, accent=True,
                               size_hint_y=None, height=dp(46)))
            self.cast_sp = Spinner(text="Velg enhet...", values=[],
                                   size_hint_y=None, height=dp(46),
                                   background_color=BTN, color=TXT)
            p.add_widget(self.cast_sp)
            r = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
            r.add_widget(mkbtn("Koble til", self._cn, accent=True))
            r.add_widget(mkbtn("Koble fra", self._dc, danger=True))
            p.add_widget(r)
            p.add_widget(Widget(size_hint_y=1))
            return p

        def _scan(self):
            self.cast_lbl.text = "Soker..."
            self.cast.scan(cb=self._od)

        def _od(self, n):
            if n:
                self.cast_sp.values = n
                self.cast_sp.text = n[0]
            self.cast_lbl.text = f"Fant {len(n)}" if n else "Ingen"

        def _cn(self):
            n = self.cast_sp.text
            if not n or n == "Velg enhet...":
                return
            self.cast.connect(n, cb=lambda ok: setattr(
                self.cast_lbl, 'text', "Tilkoblet!" if ok else "Feilet"))

        def _dc(self):
            self.cast.disconnect()
            self.cast_lbl.text = "Frakoblet"

        # ---------- KARAKTERER ----------
        def _mk_tool(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            tb = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6), padding=[dp(6), 0])
            tb.add_widget(mkbtn("+ Ny", self._new_char, accent=True, size_hint_x=0.35))
            tb.add_widget(mkbtn("Oppdater", self._show_list, small=True, size_hint_x=0.35))
            tb.add_widget(mklbl("Karakterer", color=GOLD, size=14, bold=True))
            p.add_widget(tb)
            self.tool_area = BoxLayout()
            p.add_widget(self.tool_area)
            self._show_list()
            return p

        def _show_list(self):
            self.tool_area.clear_widgets()
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            if not self.chars:
                g.add_widget(mklbl("Ingen karakterer ennaa.\nTrykk '+ Ny' for aa lage en.",
                                   color=DIM, size=12, h=50))
            else:
                for i, ch in enumerate(self.chars):
                    nm, tp = ch.get('name', '?'), ch.get('type', 'PC')
                    oc = ch.get('occ', '')
                    c = GRN if tp == 'PC' else GOLD
                    txt = f"[{tp}]  {nm}"
                    if oc:
                        txt += f"  -  {oc}"
                    row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
                    b = mkbtn(txt, lambda idx=i: self._view_char(idx),
                              small=True, size_hint_x=0.72)
                    b.color = c
                    b.halign = 'left'
                    row.add_widget(b)
                    row.add_widget(mkbtn("Rediger", lambda idx=i: self._edit_char(idx),
                                        accent=True, small=True, size_hint_x=0.28))
                    g.add_widget(row)
            scroll.add_widget(g)
            self.tool_area.add_widget(scroll)

        def _view_char(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            ch = self.chars[idx]
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
            top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            top.add_widget(mkbtn("Tilbake", self._show_list, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Rediger", lambda: self._edit_char(idx),
                                 accent=True, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Slett", lambda: self._del_char(idx),
                                 danger=True, small=True, size_hint_x=0.3))
            p.add_widget(top)
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            nm, tp = ch.get('name', '?'), ch.get('type', 'PC')
            g.add_widget(mklbl(f"[{tp}]  {nm}", color=GOLD, size=18, bold=True, h=34))
            for key, lbl in CHAR_INFO:
                v = ch.get(key, '')
                if v and key not in ('name', 'type'):
                    g.add_widget(mklbl(f"{lbl}:  {v}", color=TXT, size=14, h=26))
            stats = "   ".join(f"{lbl} {ch[key]}" for key, lbl in CHAR_STATS if ch.get(key))
            if stats:
                g.add_widget(mklbl(stats, color=TXT, size=14, h=28))
            derived = "   ".join(f"{lbl} {ch[key]}" for key, lbl in CHAR_DERIVED if ch.get(key))
            if derived:
                g.add_widget(mklbl(derived, color=TXT, size=14, h=28))
            sk = ch.get('skills', {})
            if sk and isinstance(sk, dict):
                g.add_widget(mksep(4))
                g.add_widget(mklbl("FERDIGHETER", color=GOLD, size=13, bold=True, h=24))
                sk_txt = "   ".join(f"{sn} {sv}" for sn, sv in sorted(sk.items()) if sv)
                if sk_txt:
                    g.add_widget(mklbl(sk_txt, color=TXT, size=13, wrap=True))
            for key, lbl in CHAR_TEXT:
                v = ch.get(key, '')
                if v:
                    g.add_widget(mksep(4))
                    g.add_widget(mklbl(lbl.upper(), color=GOLD, size=13, bold=True, h=24))
                    g.add_widget(mklbl(str(v), color=TXT, size=13, wrap=True))
            scroll.add_widget(g)
            p.add_widget(scroll)
            self.tool_area.add_widget(p)

        def _new_char(self):
            self.chars.append({"name": "Ny karakter", "type": "PC", "skills": {}})
            save_json(CHAR_FILE, self.chars)
            self._edit_char(len(self.chars) - 1)

        def _edit_char(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            self.edit_idx = idx
            ch = self.chars[idx]
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
            top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            top.add_widget(mkbtn("Lagre", self._save_edit, accent=True, small=True, size_hint_x=0.35))
            top.add_widget(mkbtn("Avbryt", self._show_list, small=True, size_hint_x=0.35))
            top.add_widget(mkbtn("Skills", lambda: self._edit_skills(idx), small=True, size_hint_x=0.3))
            p.add_widget(top)
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            self._ei = {}
            g.add_widget(mklbl("GRUNNINFO", color=GOLD, size=12, bold=True, h=24))
            for key, lbl in CHAR_INFO:
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
                row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                     size_hint_x=0.3, halign='right'))
                if key == 'type':
                    w = Spinner(text=ch.get(key, 'PC'), values=['PC', 'NPC'],
                                background_color=BTN, color=GOLD, font_size=sp(11), size_hint_x=0.7)
                else:
                    w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                  background_color=BTN, foreground_color=TXT,
                                  size_hint_x=0.7, padding=[dp(6), dp(4)])
                self._ei[key] = w
                row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("KARAKTERISTIKKER", color=GOLD, size=12, bold=True, h=24))
            for i in range(0, len(CHAR_STATS), 2):
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
                for j in range(2):
                    if i + j < len(CHAR_STATS):
                        key, lbl = CHAR_STATS[i + j]
                        row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                             size_hint_x=0.15, halign='right'))
                        w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                      background_color=BTN, foreground_color=TXT, size_hint_x=0.35,
                                      padding=[dp(6), dp(4)], input_filter='int')
                        self._ei[key] = w
                        row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("HP / MP / SAN / LUCK", color=GOLD, size=12, bold=True, h=24))
            for i in range(0, len(CHAR_DERIVED), 2):
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
                for j in range(2):
                    if i + j < len(CHAR_DERIVED):
                        key, lbl = CHAR_DERIVED[i + j]
                        row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                             size_hint_x=0.15, halign='right'))
                        w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                      background_color=BTN, foreground_color=TXT, size_hint_x=0.35,
                                      padding=[dp(6), dp(4)])
                        self._ei[key] = w
                        row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("NOTATER / UTSTYR", color=GOLD, size=12, bold=True, h=24))
            for key, lbl in CHAR_TEXT:
                g.add_widget(Label(text=lbl, font_size=sp(10), color=DIM,
                                   size_hint_y=None, height=dp(20), halign='left'))
                w = TextInput(text=str(ch.get(key, '')), font_size=sp(11), multiline=True,
                              background_color=BTN, foreground_color=TXT,
                              size_hint_y=None, height=dp(80), padding=[dp(6), dp(4)])
                self._ei[key] = w
                g.add_widget(w)
            scroll.add_widget(g)
            p.add_widget(scroll)
            self.tool_area.add_widget(p)

        def _edit_skills(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            ch = self.chars[idx]
            sk = ch.get('skills', {})
            if not isinstance(sk, dict):
                sk = {}
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
            top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            top.add_widget(mkbtn("Lagre skills", lambda: self._save_skills(idx),
                                 accent=True, small=True, size_hint_x=0.5))
            top.add_widget(mkbtn("Tilbake", lambda: self._edit_char(idx),
                                 small=True, size_hint_x=0.5))
            p.add_widget(top)
            p.add_widget(mklbl(f"Skills: {ch.get('name', '?')}", color=GOLD, size=13, bold=True, h=26))
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            self._sk_inputs = {}
            for sname, sdefault in SKILLS:
                row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
                is_spec = sname.endswith(':')
                if is_spec:
                    row.add_widget(Label(text=sname, font_size=sp(10), color=GDIM,
                                         size_hint_x=0.35, halign='right'))
                    w = TextInput(text=str(sk.get(sname, '')), hint_text="Spesifiser + verdi",
                                  font_size=sp(11), multiline=False, background_color=BTN,
                                  foreground_color=TXT, size_hint_x=0.65, padding=[dp(6), dp(4)])
                    self._sk_inputs[sname] = w
                else:
                    row.add_widget(Label(text=f"{sname} ({sdefault})", font_size=sp(10),
                                         color=DIM, size_hint_x=0.65, halign='left'))
                    w = TextInput(text=str(sk.get(sname, '')), hint_text=sdefault,
                                  font_size=sp(12), multiline=False, background_color=BTN,
                                  foreground_color=TXT, size_hint_x=0.35,
                                  padding=[dp(6), dp(4)], input_filter='int')
                    self._sk_inputs[sname] = w
                row.add_widget(w)
                g.add_widget(row)
            scroll.add_widget(g)
            p.add_widget(scroll)
            self.tool_area.add_widget(p)

        def _save_skills(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            sk = {sn: w.text.strip() for sn, w in self._sk_inputs.items() if w.text.strip()}
            self.chars[idx]['skills'] = sk
            save_json(CHAR_FILE, self.chars)
            self._edit_char(idx)

        def _save_edit(self):
            if self.edit_idx is None or self.edit_idx >= len(self.chars):
                return
            ch = self.chars[self.edit_idx]
            for key, w in self._ei.items():
                ch[key] = w.text if isinstance(w, (TextInput, Spinner)) else ''
            save_json(CHAR_FILE, self.chars)
            self._show_list()

        def _del_char(self, idx):
            if 0 <= idx < len(self.chars):
                self.chars.pop(idx)
                save_json(CHAR_FILE, self.chars)
                self._show_list()

        def on_stop(self):
            self.player.stop()
            self.streamer.stop()
            self.server.stop()
            self.cast.disconnect()
            save_json(CHAR_FILE, self.chars)

    log("Starting app...")
    EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())
