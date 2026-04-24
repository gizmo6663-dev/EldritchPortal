import os, sys, traceback, socket, threading, json, random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from kivy.clock import Clock

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")
log("=== APP START (v0.3.3 – Kamp + Lyd + Scenario) ===")

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
    from kivy.uix.filechooser import FileChooserListView
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
    # Karakter-fil: primær lagring i user_data_dir (app-private,
    # alltid skrivbar). Ekstern sti brukes kun for migrering ved
    # første oppstart — unngår Android 13+ scoped storage-problem.
    EXTERNAL_CHAR_FILE = os.path.join(BASE_DIR, "characters.json")
    # CHAR_FILE settes i build() når user_data_dir er tilgjengelig.
    CHAR_FILE = EXTERNAL_CHAR_FILE  # midlertidig; overstyres i build()
    # Scenario-fil: primær lagring i user_data_dir (app-private,
    # alltid skrivbar). Ekstern import-sti forsøkes lest ved
    # "Importer" — unngår Android 13+ scoped storage-problem.
    EXTERNAL_SCENARIO = os.path.join(BASE_DIR, "scenario.json")
    # SCENARIO_FILE settes i build() når user_data_dir er tilgjengelig.

    # Våpendata er BUNDLET med appen (pakket inn i APK).
    # Dette unngår Android 13+ scoped storage permission-problemer.
    try:
        _BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        _BUNDLE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    BUNDLED_WEAPONS = os.path.join(_BUNDLE_DIR, "weapons.json")
    BUNDLED_CHARS   = os.path.join(_BUNDLE_DIR, "characters.json")
    # Også prøv en ekstern versjon — hvis den finnes OG er lesbar,
    # bruk den (lar brukeren overstyre med egen fil hvis mulig).
    EXTERNAL_WEAPONS = os.path.join(BASE_DIR, "weapons.json")
    # Favoritter lagres i user_data_dir (app-private, alltid skrivbar).
    # WEAPONS_FAV_FILE settes i build() når user_data_dir er tilgjengelig.

    def ensure_dirs():
        """Opprett mapper ETTER tillatelser er gitt."""
        for d in [IMG_DIR, MUSIC_DIR]:
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                log(f"makedirs {d}: {e}")
        log(f"Dirs OK: {os.path.exists(IMG_DIR)}, {os.path.exists(MUSIC_DIR)}")

    # === FARGER – ABYSSAL PURPLE ===
    BG   = [0.05, 0.03, 0.07, 1]      # dyp lilla-svart bakgrunn
    BG2  = [0.10, 0.05, 0.12, 1]      # panel
    INPUT= [0.07, 0.03, 0.09, 1]      # tekstfelt-bakgrunn
    BTN  = [0.22, 0.10, 0.16, 1]      # knapp (burgunder)
    BTNH = [0.38, 0.15, 0.22, 1]      # aktiv fane
    SHAD = [0.02, 0.01, 0.03, 0.6]    # skygge
    GOLD = [0.95, 0.78, 0.22, 1]      # gylden aksent
    GDIM = [0.58, 0.45, 0.20, 1]      # dempet gull
    TXT  = [0.90, 0.85, 0.80, 1]      # lys tekst
    DIM  = [0.52, 0.38, 0.45, 1]      # dempet tekst (lilla-tone)
    RED  = [0.75, 0.20, 0.22, 1]      # fare/stopp
    GRN  = [0.25, 0.58, 0.32, 1]      # OK/PC
    BLUE = [0.30, 0.40, 0.65, 1]      # info
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

<FramedBox>:
    canvas.before:
        Color:
            rgba: self.frame_color
        Line:
            rectangle: (self.x, self.y, self.width, self.height)
            width: 1.5
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

    class FramedBox(BoxLayout):
        frame_color = ListProperty(GOLD)

    # === LYDKILDER ===
    AMBIENT_SOUNDS = [
        {"name":"--- Natur ---"},
        {"name":"Regn og torden","url":"https://archive.org/download/RainSound13/Gentle%20Rain%20and%20Thunder.mp3"},
        {"name":"Havbølger","url":"https://archive.org/download/naturesounds-soundtheraphy/Birds%20With%20Ocean%20Waves%20on%20the%20Beach.mp3"},
        {"name":"Nattregn","url":"https://archive.org/download/RainSound13/Night%20Rain%20Sound.mp3"},
        {"name":"Vind og storm","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/epic-storm-thunder-rainwindwaves-no-loops-106800.mp3"},
        {"name":"Nattlyder","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/ambience-crickets-chirping-in-very-light-rain-followed-by-gentle-rolling-thunder-10577.mp3"},
        {"name":"Havstorm","url":"https://archive.org/download/naturesounds-soundtheraphy/Sound%20Therapy%20-%20Sea%20Storm.mp3"},
        {"name":"Lett regn","url":"https://archive.org/download/naturesounds-soundtheraphy/Light%20Gentle%20Rain.mp3"},
        {"name":"Tordenstorm","url":"https://archive.org/download/RainSound13/Rain%20Sound%20with%20Thunderstorm.mp3"},
        {"name":"Urolig hav","url":"https://archive.org/download/RelaxingRainAndLoudThunderFreeFieldRecordingOfNatureSoundsForSleepOrMeditation/Relaxing%20Rain%20and%20Loud%20Thunder%20%28Free%20Field%20Recording%20of%20Nature%20Sounds%20for%20Sleep%20or%20Meditation%20Mp3%29.mp3"},
        {"name":"--- Horror ---"},
        {"name":"Skummel atmosfære","url":"https://archive.org/download/creepy-music-sounds/Creepy%20music%20%26%20sounds.mp3"},
        {"name":"Uhyggelig drone","url":"https://archive.org/download/scary-sound-effects-8/Evil%20Demon%20Drone%20Movie%20Halloween%20Sounds.mp3"},
        {"name":"Mørk spenning","url":"https://archive.org/download/scary-sound-effects-8/Dramatic%20Suspense%20Sound%20Effects.mp3"},
        {"name":"Horrorlyder","url":"https://archive.org/download/creepy-music-sounds/Horror%20Sound%20Effects.mp3"},
    ]

    # === KARAKTERFELT ===
    CHAR_INFO = [
        ("name","Navn"), ("type","Type"), ("occ","Yrke"), ("archetype","Arketype"),
        ("age","Alder"), ("residence","Bosted"), ("birthplace","Fødested"),
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
        ("weapons","Våpen"), ("talents","Pulp Talents"),
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
    RULES = [
      ("Grunnregler", "", [
        ("Ferdighetskast", [
          "Rull d100 (percentile) mot skill-verdi.",
          "Lik eller under = suksess.",
          "",
          "Suksessnivåer:",
          "  Critical: resultat = 01",
          "  Extreme: resultat \u2264 skill / 5",
          "  Hard: resultat \u2264 skill / 2",
          "  Regular: resultat \u2264 skill",
          "  Failure: resultat > skill",
          "",
          "Automatisk suksess: 01 alltid suksess.",
          "Fumble (basert på KRAV, ikke base skill):",
          "  Krav \u2265 50: kun 100 er fumble",
          "  Krav < 50: 96\u2013100 er fumble",
          "  Eks: skill 60, Hard diff (krav 30)",
          "    -> fumble på 96\u2013100",
        ]),
        ("Vanskelighetsgrad", [
          "Keeper setter vanskelighetsgrad:",
          "  Regular: skill-verdi (standard)",
          "  Hard: halv skill-verdi",
          "  Extreme: femtedel av skill-verdi",
          "",
          "Mot levende motstandere:",
          "  Motstanders skill < 50: Regular",
          "  Motstanders skill \u2265 50: Hard",
          "  Motstanders skill \u2265 90: Extreme",
        ]),
        ("Bonus & Penalty", [
          "Bonus die: rull 2 tier-terninger,",
          "  bruk den LAVESTE.",
          "Penalty die: rull 2 tier-terninger,",
          "  bruk den HØYESTE.",
          "",
          "Maks 2 bonus ELLER 2 penalty.",
          "Bonus og penalty kansellerer 1:1.",
          "",
          "Gis av Keeper basert på omstendigheter:",
          "  Fordel: bonus (godt lys, tid, verktøy)",
          "  Ulempe: penalty (stress, dårlig sikt)",
        ]),
        ("Pushed Rolls", [
          "Spiller kan pushe ETT mislykket kast.",
          "Må beskrive HVA de gjør annerledes.",
          "Keeper må godkjenne pushen.",
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
          "Høyeste suksessnivå vinner.",
          "Likt nivå: høyeste skill-verdi vinner.",
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
          "Luck-sjekk: d100 \u2264 Luck.",
          "",
          "Spending Luck:",
          "  Etter et skill-kast: trekk Luck-poeng",
          "  1:1 for å senke resultatet.",
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
          "  Resultat \u2264 skill = ingen økning.",
          "",
          "Skill-maks: 99 (unntatt CM: 99).",
          "Alderseffekter kan senke stats.",
        ]),
      ]),
      ("Kamp", "", [
        ("Kampflyt", [
          "1. Alle handler i DEX-rekkefølge",
          "   (høyeste først).",
          "",
          "2. Hver deltaker får 1 handling:",
          "   - Angripe (melee eller ranged)",
          "   - Flee (trekke seg ut)",
          "   - Manøver (trip, disarm, etc.)",
          "   - Kaste besvergelse",
          "   - Bruke gjenstand / First Aid",
          "   - Annet (snakke, lete, etc.)",
          "",
          "3. Forsvarer velger reaksjon:",
          "   - Dodge (unngå)",
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
          "  Forsvarer vinner -> unngår angrepet",
          "  Begge feiler -> ingenting skjer",
          "",
          "FIGHT BACK (opposed vs Fighting):",
          "  Angriper vinner -> full skade",
          "  Forsvarer vinner -> forsvarer gjør skade",
          "  Begge feiler -> ingenting skjer",
          "",
          "Dodge: 1 gratis per runde,",
          "  ekstra dodge koster handling neste runde.",
          "",
          "OUTNUMBERED:",
          "  Når forsvarer allerede har dodget",
          "  eller fought back denne runden:",
          "  -> alle etterfølgende angrep får",
          "     +1 bonus die.",
          "  Unntak: vesener med flere angrep/runde",
          "  kan dodge/fight back like mange ganger.",
          "  Gjelder IKKE skytevåpen.",
        ]),
        ("Skytevåpen", [
          "Rull Firearms-skill. INGEN opposed roll.",
          "Forsvarer kan KUN dodge ved point-blank.",
          "Ellers: bare dekke/bevege seg ut.",
          "",
          "Rekkevidde-modifikatorer:",
          "  Point-blank (\u2264 1/5 range): +1 bonus",
          "  Mellomdistanse (base range): normal",
          "  Lang (inntil 2x base): +1 penalty",
          "  Ekstrem (inntil 4x base): +2 penalty",
          "",
          "Andre modifikatorer:",
          "  Bevegelig mål: +1 penalty",
          "  Stort mål: +1 bonus",
          "  Smalt mål: +1 penalty",
          "  Sikte (bruker handling): +1 bonus",
          "",
          "Impale: Extreme suksess med",
          "  gjennomborende våpen",
          "  = maks våpenskade + ekstra kast.",
        ]),
        ("Manøvrer", [
          "Fighting-manøver (i stedet for skade):",
          "  Trip/knockdown: mål faller",
          "  Disarm: mål mister våpen",
          "  Hold/grapple: mål er fastholdt",
          "  Kaste: dytte/kaste motstanderen",
          "",
          "Krever: vinn opposed Fighting-sjekk.",
          "Build-differanse kan gi bonus/penalty:",
          "  Angriper Build \u2265 mål + 2: +1 bonus",
          "  Angriper Build \u2264 mål - 2: +1 penalty",
        ]),
        ("Damage Bonus (DB)", [
          "DB basert på STR + SIZ:",
          "  2\u201364:    -2",
          "  65\u201384:   -1",
          "  85\u2013124:  0",
          "  125\u2013164: +1d4",
          "  165\u2013204: +1d6",
          "  205\u2013284: +2d6",
          "  285\u2013364: +3d6",
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
          "SKADENIVÅER:",
          "  Minor wound: tap < halve maks HP",
          "  Major wound: tap \u2265 halve maks HP",
          "",
          "MAJOR WOUND-konsekvenser:",
          "  CON-sjekk eller besvime",
          "  First Aid/Medicine innen 1 runde",
          "  Må stabiliseres ellers dør",
          "",
          "DYING (0 HP):",
          "  CON-sjekk per runde",
          "  Feil = død",
          "  Suksess = holder ut 1 runde til",
          "",
          "HELING:",
          "  First Aid: +1 HP (1 forsøk/skade)",
          "  Medicine: +1d3 HP (etter First Aid)",
          "  Naturlig: 1 HP/uke (minor)",
          "  Major wound: 1d3 HP/uke m/pleie",
        ]),
        ("Automatiske våpen", [
          "Burst: 3 kuler, +1 bonus die til skade.",
          "Full auto: velg antall mål,",
          "  fordel kuler, rull for hvert mål.",
          "  1 bonus die per 10 kuler på målet.",
          "",
          "Suppressive fire:",
          "  Dekker et område, alle i området",
          "  må Dodge eller ta 1 treff.",
          "  Bruker halve magasinet.",
        ]),
      ]),
      ("Sanity", "", [
        ("SAN-sjekk", [
          "Rull d100 \u2264 nåværende SAN.",
          "",
          "Format: 'X/Y'",
          "  Suksess: tap = X",
          "  Feil: tap = Y",
          "  Eks: '1/1d6' = suksess taper 1,",
          "    feil taper 1d6 SAN.",
          "",
          "Maks SAN = 99 \u2013 Cthulhu Mythos skill.",
          "",
          "SAN fumble: automatisk maks SAN-tap.",
        ]),
        ("Temporary Insanity", [
          "TRIGGER: 5+ SAN tapt i ETT kast.",
          "",
          "Keeper krever INT-sjekk:",
          "  INT suksess = investigator innser",
          "    sannheten -> MIDLERTIDIG GAL",
          "  INT feil = fortrengt minne,",
          "    investigator forblir ved sine fulle fem",
          "",
          "Midlertidig insanity varer 1d10 timer.",
          "Begynner med Bout of Madness.",
          "Etterfølges av Underlying Insanity.",
        ]),
        ("Bout of Madness", [
          "Oppstår ved midlertidig insanity.",
          "Keeper velger Real-Time eller Summary.",
          "",
          "REAL-TIME (varig 1d10 runder):",
          "  1: Amnesi (husker ingenting)",
          "  2: Psykosomatisk (blind/døv/lam)",
          "  3: Vold (angrip nærmeste)",
          "  4: Paranoia (alle er fiender)",
          "  5: Fysisk (kvalme/besvimelse)",
          "  6: Flukt (løp i panikk)",
          "  7: Hallusinasjoner",
          "  8: Ekko (gjenta handlinger meningsløst)",
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
          "  7: Paranoia (stoler på ingen)",
          "  8: Dissosiasjon (fjern, uvirkelig)",
          "  9: Spiseforstyrrelse / søvnløshet",
          "  10: Mythos-besettelse (studerer forbudt)",
        ]),
        ("Fobier (utvalg)", [
          "Acrophobia \u2013 høydefobi",
          "Agoraphobia \u2013 åpne plasser",
          "Arachnophobia \u2013 edderkopper",
          "Claustrophobia \u2013 trange rom",
          "Demophobia \u2013 folkemengder",
          "Hemophobia \u2013 blod",
          "Hydrophobia \u2013 vann",
          "Mysophobia \u2013 smitte/skitt",
          "Necrophobia \u2013 døde/lik",
          "Nyctophobia \u2013 mørke",
          "Pyrophobia \u2013 ild",
          "Thalassophobia \u2013 havet/dypt vann",
          "Xenophobia \u2013 fremmede/ukjente",
          "Zoophobia \u2013 dyr",
        ]),
        ("Manier (utvalg)", [
          "Dipsomania \u2013 trang til alkohol",
          "Kleptomania \u2013 trang til å stjele",
          "Megalomania \u2013 storhetstanker",
          "Mythomania \u2013 tvangsløgner",
          "Necromania \u2013 besettelse med døden",
          "Pyromania \u2013 brannstifting",
          "Thanatomania \u2013 dødslengsel",
          "Xenomania \u2013 besettelse med fremmede",
        ]),
        ("Indefinite Insanity", [
          "Trigges når investigator har tapt",
          "  1/5 av nåværende SAN totalt.",
          "",
          "Effekt: langvarig galskap.",
          "  Spiller mister kontroll over karakter.",
          "  Keeper bestemmer adferd.",
          "  Varer måneder/år.",
          "",
          "Behandling:",
          "  Institusjonalisering",
          "  Psychoanalysis over tid",
          "  +1d3 SAN per måned (maks)",
          "  Mislykket behandling: -1d6 SAN",
        ]),
        ("SAN-gjenoppretting", [
          "Psychoanalysis: +1d3 SAN (1/måned)",
          "  Mislykket: -1d6 SAN!",
          "Self-help: forbedre skill = +1d3 SAN",
          "Fullføre scenario: Keeper-belønning",
          "",
          "Maks SAN = 99 \u2013 Cthulhu Mythos skill.",
          "Permanent SAN-tap kan ikke gjenopprettes",
          "  utover denne grensen.",
        ]),
      ]),
      ("Forfølgelse", "", [
        ("Oppsett", [
          "1. Type: fot eller kjøretøy.",
          "2. Antall locations: 5\u201310 (Keeper velger).",
          "3. Deltakere:",
          "   Fot: MOV basert på DEX, STR, SIZ.",
          "   Bil: speed-rating.",
          "4. Speed Roll (CON-sjekk):",
          "   Extreme suksess: +1 MOV for chasen",
          "   Suksess: ingen endring",
          "   Feil: -1 MOV for chasen",
          "   (kjøretøy: Drive Auto i stedet)",
          "5. Sammenlign MOV: høyere MOV flykter",
          "   umiddelbart. Ellers -> full chase.",
          "6. Sett startposisjoner på tracken.",
          "7. Plasser barrierer/farer på locations.",
          "",
          "MOV (Movement Rate):",
          "  Hvis DEX & STR begge > SIZ: MOV 9",
          "  Hvis enten DEX eller STR > SIZ: MOV 8",
          "  Hvis begge \u2264 SIZ: MOV 7",
          "  Alder 40\u201349: MOV -1",
          "  Alder 50\u201359: MOV -2 (etc.)",
        ]),
        ("Bevegelse & handlinger", [
          "Runder i DEX-rekkefølge (høy først).",
          "",
          "Hver runde kan deltaker:",
          "  - Bevege seg (MOV locations)",
          "  - Utføre 1 handling:",
          "    Speed: CON-sjekk for +1 location",
          "    Angrep: Fighting/Firearms",
          "    Barriere: skill-sjekk for å passere",
          "    Hinder: lag barriere for forfølger",
          "",
          "Hazard-handling koster handling OG",
          "  bevegelse den runden.",
        ]),
        ("Barrierer", [
          "Keeper plasserer barrierer på locations.",
          "Skill-sjekk for å passere:",
          "",
          "  Hopp over gjerde: Jump / Climb",
          "  Trang passasje: DEX / Dodge",
          "  Folkemengde: STR / Charm / Intimidate",
          "  Gjørme/glatt: DEX / Luck",
          "  Låst dør: Locksmith / STR",
          "  Trafikkert gate: Drive Auto / DEX",
          "",
          "Feil: mist 1 location bevegelse.",
          "Fumble: fall, skade, fastklemt, etc.",
        ]),
        ("Seier & tap", [
          "FLUKT lykkes når:",
          "  Avstand mellom = antall locations + 1",
          "  (forfølger kan ikke se målet).",
          "",
          "FANGET når:",
          "  Forfølger er på SAMME location.",
          "  Kamp eller interaksjon kan begynne.",
          "",
          "UTMATTELSE:",
          "  CON-sjekk per runde etter runde 5.",
          "  Feil: MOV reduseres med 1.",
          "  MOV 0: kan ikke bevege seg.",
        ]),
      ]),
      ("Magi & Tomer", "", [
        ("Besvergelse", [
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
          "MP = 0: bevisstløs i 1d8 timer.",
          "POW-offer: permanent, gjenopprettes IKKE.",
        ]),
        ("Mythos-tomer", [
          "Lesing av Mythos-tome:",
          "  Initial reading: uker til måneder",
          "  Full study: måneder til år",
          "",
          "Belønning: +Cthulhu Mythos skill.",
          "Kostnad: SAN-tap (varierer per tome).",
          "Kan også lære spells fra tomen.",
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
      ("Pulp Cthulhu", "", [
        ("Pulp-regler", [
          "Helter er TØFFERE enn standard CoC.",
          "",
          "HP: (CON + SIZ) / 5 (avrundet ned)",
          "  Standard CoC: (CON+SIZ) / 10",
          "  Effektivt DOBBEL HP.",
          "  Valgfritt lavnivå: (CON+SIZ)/10",
          "",
          "Luck: 2d6+6 x 5 (høyere enn standard)",
          "  Standard CoC: 3d6 x 5",
          "  Regenerer 2d10 Luck per sesjon.",
          "",
          "First Aid: +1d4 HP (standard: +1 HP)",
          "  Extreme suksess: automatisk 4 HP.",
          "Medicine: +1d4 HP (standard: +1d3)",
          "",
          "Pulp Talents: 2 stk (standard).",
          "  Lavnivå pulp: 1 talent",
          "  Høynivå pulp: 3 talents",
          "",
          "Kampkast kan IKKE pushes (som standard).",
          "Spending Luck: kan også brukes til:",
          "  - Unngå dying (5 Luck = stabiliser)",
          "  - Redusere skade (etter kast)",
        ]),
        ("Arketyper", [
          "Velg 1 arketype ved opprettelse.",
          "Gir bonuser og Pulp Talents.",
          "",
          "  Adventurer: allsidig eventyrer",
          "  Beefcake: fysisk sterk, ekstra HP",
          "  Bon Vivant: sjarmerende, sosialt dyktig",
          "  Cold Blooded: hensynsløs, presist",
          "  Dreamer: kreativ, Mythos-sensitiv",
          "  Egghead: intellektuell, kunnskapsrik",
          "  Explorer: utforsker, overlevelse",
          "  Femme/Homme Fatale: forførende",
          "  Grease Monkey: mekaniker, oppfinnsom",
          "  Hard Boiled: tøff, utholdende",
          "  Harlequin: entertainer, distraherende",
          "  Hunter: jeger, naturkyndig",
          "  Mystic: spirituell, spådomsevne",
          "  Outsider: ensom, selvlært",
          "  Reckless: våghals, risikotaker",
          "  Sidekick: lojal, støttende",
          "  Swashbuckler: akrobatisk fighter",
          "  Thrill Seeker: adrenalinjansen",
          "  Two-Fisted: nevekamp-spesialist",
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
          "  Outmaneuver: +1 bonus på manøvrer",
          "  Fleet Footed: +1 MOV i chase",
        ]),
      ]),
      ("Tabeller", "", [
        ("Våpentabell \u2013 melee", [
          "Våpen: skade / attacks",
          "",
          "  Unarmed (knytneve): 1d3+DB / 1",
          "  Head butt: 1d4+DB / 1",
          "  Kick: 1d4+DB / 1",
          "  Grapple: special / 1",
          "  Kniv (liten): 1d4+DB / 1",
          "  Kniv (stor): 1d6+DB / 1",
          "  Klubbe/kølle: 1d8+DB / 1",
          "  Sverd/sabel: 1d8+DB / 1",
          "  Øks (stor): 1d8+2+DB / 1",
          "  Spyd: 1d8+1+DB / 1",
          "  Motorsag: 2d8 / 1",
        ]),
        ("Våpentabell \u2013 skytevåpen", [
          "Våpen: skade / range / shots",
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
          "  Se en venn dø: 0/1d4",
          "  Se noe uforklarlig: 0/1d2",
          "  Se et grusomt drap: 1/1d4+1",
          "  Se massedrap: 1d3/1d6+1",
          "  Finne en grusomhet: 0/1d3",
          "",
          "  Oppdage Mythos-bevis: 0/1d2",
          "  Lese Mythos-tome: 1/1d4",
          "  Se Mythos-ritual: 1/1d6",
          "  Bli utsatt for besvergelse: 1/1d6",
        ]),
        ("Alderseffekter", [
          "Alder påvirker stats ved opprettelse:",
          "",
          "  15\u201319: -5 SIZ/STR, -5 EDU,",
          "    Luck: rull 2x, bruk best",
          "  20\u201339: EDU-forbedring: +1",
          "  40\u201349: EDU +2, -5 fritt STR/CON/DEX,",
          "    APP -5, MOV -1",
          "  50\u201359: EDU +3, -10 fritt STR/CON/DEX,",
          "    APP -10, MOV -2",
          "  60\u201369: EDU +4, -20 fritt STR/CON/DEX,",
          "    APP -15, MOV -3",
          "  70\u201379: EDU +4, -40 fritt STR/CON/DEX,",
          "    APP -20, MOV -4",
          "  80\u201389: EDU +4, -80 fritt STR/CON/DEX,",
          "    APP -25, MOV -5",
        ]),
        ("Credit Rating", [
          "Credit Rating = formue/sosial status:",
          "",
          "  0: fattig, hjemløs",
          "  1\u20139: fattig, kun nødvendig",
          "  10\u201349: gjennomsnittlig",
          "  50\u201389: velstående",
          "  90\u201398: rik",
          "  99: enormt rik",
          "",
          "Spending level (per dag):",
          "  CR 0: $0.50",
          "  CR 1\u20139: $2",
          "  CR 10\u201349: $10",
          "  CR 50\u201389: $50",
          "  CR 90\u201398: $250",
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
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES,
                Permission.READ_MEDIA_AUDIO,
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.ACCESS_WIFI_STATE,
                Permission.CHANGE_WIFI_MULTICAST_STATE
            ])
        except:
            pass

    def has_all_files_access():
        """Sjekk om appen har MANAGE_EXTERNAL_STORAGE (Android 11+).
        Returnerer True hvis ja, False hvis nei, None hvis ikke
        Android eller ikke relevant."""
        if platform != 'android':
            return None
        try:
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            Build = autoclass('android.os.Build$VERSION')
            # Kun relevant på Android 11 (API 30) og nyere
            if Build.SDK_INT < 30:
                return None
            return bool(Environment.isExternalStorageManager())
        except Exception as e:
            log(f"has_all_files_access sjekk feilet: {e}")
            return None

    def request_all_files_access():
        """Åpne Android-innstillinger hvor brukeren kan gi appen
        'All files access'. Krever Android 11+ og at appen
        deklarerer MANAGE_EXTERNAL_STORAGE i manifestet."""
        if platform != 'android':
            return False
        try:
            from jnius import autoclass
            PythonActivity = autoclass(
                'org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            Uri = autoclass('android.net.Uri')
            activity = PythonActivity.mActivity
            package = activity.getPackageName()
            try:
                intent = Intent(
                    Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                intent.setData(Uri.parse(f"package:{package}"))
                activity.startActivity(intent)
            except Exception:
                # Fallback: generell "All files access"-skjerm
                intent = Intent(
                    Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                activity.startActivity(intent)
            return True
        except Exception as e:
            log(f"request_all_files_access feilet: {e}")
            return False

    def load_json(p, d=None):
        try:
            with open(p, 'r') as f:
                return json.load(f)
        except:
            return d if d is not None else []

    def first_non_empty(dct, keys):
        if not isinstance(dct, dict):
            return ''
        for k in keys:
            v = dct.get(k)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                return s
        return ''

    def normalize_skills(raw):
        if isinstance(raw, dict):
            return {str(k).strip(): str(v).strip()
                    for k, v in raw.items()
                    if str(k).strip() and str(v).strip()}
        if isinstance(raw, list):
            out = {}
            for entry in raw:
                if isinstance(entry, dict):
                    name = first_non_empty(
                        entry, ['name', 'skill', 'title', 'label'])
                    value = first_non_empty(
                        entry, ['value', 'score', 'percent', 'pct', 'rank'])
                    if name and value:
                        out[name] = value
            return out
        return {}

    def normalize_char_type(raw_type):
        t = (str(raw_type or '').strip().upper())
        if t in ('NPC', 'NON-PLAYER', 'NONPLAYER'):
            return 'NPC'
        if t in ('FIENDE', 'ENEMY', 'CREATURE', 'S', 'SKAPNING', 'MONSTER'):
            return 'Fiende'
        return 'PC'

    def normalize_character_entry(raw):
        if not isinstance(raw, dict):
            return None
        candidate = raw
        for k in ('character', 'profile', 'investigator', 'sheet'):
            nested = raw.get(k)
            if isinstance(nested, dict) and (
                ('name' in nested) or ('full_name' in nested)
            ):
                candidate = nested
                break

        name = first_non_empty(candidate, [
            'name', 'full_name', 'character_name', 'investigator_name'
        ])
        if not name:
            return None

        ch = {
            'name': name,
            'type': normalize_char_type(first_non_empty(candidate, [
                'type', 'role', 'kind'
            ]) or first_non_empty(raw, ['type', 'role', 'kind'])),
            'occ': first_non_empty(candidate, [
                'occ', 'occupation', 'job', 'profession'
            ]),
            'archetype': first_non_empty(candidate, ['archetype', 'class']),
            'age': first_non_empty(candidate, ['age']),
            'residence': first_non_empty(candidate, ['residence', 'home']),
            'birthplace': first_non_empty(candidate, [
                'birthplace', 'birth_place', 'born'
            ]),
            'str': first_non_empty(candidate, ['str', 'STR']),
            'con': first_non_empty(candidate, ['con', 'CON']),
            'siz': first_non_empty(candidate, ['siz', 'SIZ']),
            'dex': first_non_empty(candidate, ['dex', 'DEX']),
            'int': first_non_empty(candidate, ['int', 'INT']),
            'app': first_non_empty(candidate, ['app', 'APP']),
            'pow': first_non_empty(candidate, ['pow', 'POW']),
            'edu': first_non_empty(candidate, ['edu', 'EDU']),
            'hp': first_non_empty(candidate, ['hp', 'HP']),
            'mp': first_non_empty(candidate, ['mp', 'MP']),
            'san': first_non_empty(candidate, ['san', 'SAN']),
            'luck': first_non_empty(candidate, ['luck', 'LUCK']),
            'db': first_non_empty(candidate, ['db', 'DB']),
            'build': first_non_empty(candidate, ['build', 'BUILD']),
            'move': first_non_empty(candidate, ['move', 'MOVE']),
            'dodge': first_non_empty(candidate, ['dodge', 'DODGE']),
            'weapons': first_non_empty(candidate, [
                'weapons', 'weapon', 'equipment', 'gear'
            ]),
            'talents': first_non_empty(candidate, [
                'talents', 'pulp_talents'
            ]),
            'backstory': first_non_empty(candidate, [
                'backstory', 'background', 'history', 'description'
            ]),
            'notes': first_non_empty(candidate, ['notes']),
            'skills': normalize_skills(
                candidate.get('skills', candidate.get('skill', {})))
        }
        return ch

    def normalize_characters_data(raw):
        candidates = []
        if isinstance(raw, list):
            candidates = raw
        elif isinstance(raw, dict):
            for k in (
                'characters', 'profiles', 'investigators',
                'party', 'members', 'pcs', 'npcs', 'entries', 'data'
            ):
                v = raw.get(k)
                if isinstance(v, list):
                    candidates.extend(v)
            if not candidates:
                candidates = [raw]
        else:
            return []

        out = []
        seen = set()
        for item in candidates:
            ch = normalize_character_entry(item)
            if not ch:
                continue
            key = (ch.get('name', '').strip().lower(), ch.get('type', 'PC'))
            if key in seen:
                continue
            seen.add(key)
            out.append(ch)
        return out

    def load_characters(path):
        raw = load_json(path, [])
        return normalize_characters_data(raw)

    def save_json(p, d):
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"save_json feilet ({p}): {type(e).__name__}: {e}")

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
            l.size_hint_y = None
            # Bind text_size til label-bredden slik at det tilpasser seg rotasjon
            l.bind(width=lambda w, v: setattr(w, 'text_size', (v - dp(8), None)))
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

    class FilePicker:
        """Android Storage Access Framework-filvelger.

        Åpner systemets filvelger og leser valgt fil via URI —
        krever ingen storage-tillatelser, fungerer på alle
        Android-versjoner, og brukeren kan velge fra hvor som
        helst (Documents, Downloads, Google Drive, osv).
        """
        REQUEST_CODE = 7331

        def __init__(self):
            self.callback = None
            self._activity = None
            self._bound = False

        def _ensure_bound(self):
            """Koble på Android activity-result-listener."""
            if self._bound or platform != 'android':
                return
            try:
                from jnius import autoclass
                PythonActivity = autoclass(
                    'org.kivy.android.PythonActivity')
                self._activity = PythonActivity.mActivity
                # Registrer callback for activity result
                from android import activity as android_activity
                android_activity.bind(
                    on_activity_result=self._on_result)
                self._bound = True
                log("FilePicker bundet til Android activity")
            except Exception as e:
                log(f"FilePicker bind-feil: {e}")

        def pick(self, callback, mime_type='application/json'):
            """Åpne filvelger. callback(ok, text_or_err) kalles
            når brukeren har valgt (eller avbrutt)."""
            if platform != 'android':
                callback(False, "Filvelger kun tilgjengelig på Android")
                return
            self._ensure_bound()
            if not self._activity:
                callback(False, "Fikk ikke tilgang til Android activity")
                return
            self.callback = callback
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.setType(mime_type)
                self._activity.startActivityForResult(
                    intent, self.REQUEST_CODE)
            except Exception as e:
                log(f"FilePicker pick-feil: {e}")
                callback(False, f"Kunne ikke åpne filvelger: {e}")

        def _on_result(self, request_code, result_code, intent):
            """Mottatt resultat fra filvelgeren."""
            if request_code != self.REQUEST_CODE:
                return
            cb = self.callback
            self.callback = None
            if cb is None:
                return
            # RESULT_OK = -1, RESULT_CANCELED = 0
            if result_code != -1 or intent is None:
                Clock.schedule_once(
                    lambda dt: cb(False, "Avbrutt"), 0)
                return
            try:
                from jnius import autoclass
                uri = intent.getData()
                if uri is None:
                    Clock.schedule_once(
                        lambda dt: cb(False, "Ingen fil valgt"), 0)
                    return
                # Åpne input stream via content resolver
                resolver = self._activity.getContentResolver()
                stream = resolver.openInputStream(uri)
                # Les innhold (byte-vis gjennom InputStreamReader)
                BufferedReader = autoclass(
                    'java.io.BufferedReader')
                InputStreamReader = autoclass(
                    'java.io.InputStreamReader')
                reader = BufferedReader(
                    InputStreamReader(stream, 'UTF-8'))
                sb = []
                line = reader.readLine()
                while line is not None:
                    sb.append(line)
                    line = reader.readLine()
                    if line is not None:
                        sb.append('\n')
                reader.close()
                stream.close()
                text = ''.join(sb)
                Clock.schedule_once(
                    lambda dt: cb(True, text), 0)
            except Exception as e:
                log(f"FilePicker read-feil: {e}")
                err = f"Lesing feilet: {type(e).__name__}: {e}"
                Clock.schedule_once(
                    lambda dt: cb(False, err), 0)

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
            log("=== BUILD (v0.3.2 Abyssal Purple) ===")
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
            self.file_picker = FilePicker()

            # Karakterer: lagres i app-private storage (alltid skrivbar),
            # unngår Android 13+ scoped storage permission-problemer.
            global CHAR_FILE
            CHAR_FILE = os.path.join(self.user_data_dir, "characters.json")
            # Migrer fra ekstern sti ved første kjøring (én gang)
            if not os.path.exists(CHAR_FILE) and os.path.exists(EXTERNAL_CHAR_FILE):
                try:
                    import shutil
                    shutil.copy2(EXTERNAL_CHAR_FILE, CHAR_FILE)
                    log(f"Karakterer migrert: {EXTERNAL_CHAR_FILE} → {CHAR_FILE}")
                except Exception as e:
                    log(f"Migrering av karakterfil feilet: {e}")

            self.chars = load_characters(CHAR_FILE)
            # Første oppstart uten lagrede karakterer: seed fra bundlet characters.json
            if not self.chars and os.path.exists(BUNDLED_CHARS):
                try:
                    with open(BUNDLED_CHARS, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    seeded = normalize_characters_data(data)
                    if seeded:
                        self.chars = seeded
                        save_json(CHAR_FILE, self.chars)
                        log(f"Seedet {len(self.chars)} karakterer fra bundlet fil")
                except Exception as e:
                    log(f"Kunne ikke laste bundlet karakterer: {e}")
            self.edit_idx = None
            self._chars_overlay = None
            self._chars_dim = None

            # Våpen: favoritt-fil går i app-private storage (alltid skrivbar)
            self.WEAPONS_FAV_FILE = os.path.join(
                self.user_data_dir, "weapons_favorites.json")
            # Scenario: også app-private (unngår scoped storage-feil
            # ved lesing av .json i /sdcard/Documents/ på Android 13+)
            self.SCENARIO_FILE = os.path.join(
                self.user_data_dir, "scenario.json")
            self.weapons_data = {
                "weapons": [], "categories": {},
                "subcategories": {}, "field_labels": {}
            }
            self.weap_favorites = set(load_json(self.WEAPONS_FAV_FILE, []))
            self._weap_cat = 'all'
            self._weap_era = 'all'
            self._weap_search = ''
            self._weap_fav_only = False
            self._weap_overlay = None
            self._weap_dim = None
            self._weap_last_error = None

            # FloatLayout som rot – lar oss legge splash oppå
            wrapper = FloatLayout()

            main = BoxLayout(orientation='vertical', spacing=0,
                             size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            main.add_widget(Widget(size_hint_y=None, height=dp(30)))

            # FANER
            tabs = RBox(size_hint_y=None, height=dp(52), spacing=dp(4),
                        padding=[dp(8), 0], bg_color=BTN)
            self._tabs = {}
            for key, txt in [('img','Bilder'),('snd','Lyd'),('cmb','Kamp'),('tool','Verktøy'),('rules','Regler'),('cast','Cast')]:
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
            ensure_dirs()
            self.server.start()
            self._load_imgs()
            self._load_tracks()
            self._weap_do_load()
            self.status.text = f"IP: {MediaServer.ip()}  |  Cast: {'Ja' if CAST_AVAILABLE else 'Nei'}"

        def _weap_do_load(self):
            """Last våpendata. Prøv ekstern først (brukerens egen),
            fall tilbake til bundlet versjon."""
            # Forsøk 1: ekstern fil i /sdcard/Documents/EldritchPortal/
            if os.path.exists(EXTERNAL_WEAPONS):
                try:
                    with open(EXTERNAL_WEAPONS, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict) and 'weapons' in data:
                        n = len(data.get('weapons', []))
                        log(f"_weap_do_load: ekstern OK, {n} våpen")
                        self.weapons_data = data
                        self._weap_last_error = None
                        return
                except PermissionError:
                    log("_weap_do_load: ekstern finnes men ingen tilgang, bruker bundlet")
                except Exception as e:
                    log(f"_weap_do_load: ekstern feil ({e}), bruker bundlet")
            # Forsøk 2: bundlet fil (pakket inn i APK)
            if os.path.exists(BUNDLED_WEAPONS):
                try:
                    with open(BUNDLED_WEAPONS, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    n = len(data.get('weapons', []))
                    log(f"_weap_do_load: bundlet OK, {n} våpen")
                    self.weapons_data = data
                    self._weap_last_error = None
                    return
                except Exception as e:
                    err = f"Bundlet fil: {type(e).__name__}: {e}"
                    log(f"_weap_do_load: {err}")
                    self._weap_last_error = err
                    return
            # Ingen kilder fungerte
            err = (f"Fant ingen weapons.json.\n"
                   f"Bundlet sti: {BUNDLED_WEAPONS}\n"
                   f"Ekstern sti: {EXTERNAL_WEAPONS}")
            log(f"_weap_do_load: {err}")
            self._weap_last_error = err

        def _tab(self, k):
            self.content.clear_widgets()
            builders = {
                'img': self._mk_img, 'snd': self._mk_sound,
                'cmb': self._mk_combat, 'tool': self._mk_tool,
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
                    self.img_lbl.text = "Mappe ikke funnet"
                    self.img_grid.add_widget(
                        mklbl("Mappen finnes ikke ennå.\n"
                              "Start appen på nytt etter å ha\n"
                              "godtatt tillatelser.",
                              color=DIM, size=11, wrap=True))
                    return
                items = sorted(os.listdir(f))
                dirs = [d for d in items if os.path.isdir(os.path.join(f, d)) and not d.startswith('.')]
                imgs = [x for x in items if x.lower().endswith(IMG_EXT)]
                self.img_lbl.text = f"{len(dirs)} mapper, {len(imgs)} bilder"
                if not dirs and not imgs:
                    self.img_grid.add_widget(
                        mklbl("Ingen bilder funnet.\n\n"
                              "Legg bilder i:\n"
                              "Dokumenter/EldritchPortal/images/\n\n"
                              "Tips: lag undermapper for\n"
                              "å organisere etter scenario,\n"
                              "f.eks. images/Slow Boat/\n\n"
                              "Støttede formater:\n"
                              ".png  .jpg  .jpeg  .webp",
                              color=DIM, size=11, wrap=True))
                    return
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

        # ---------- KAMP (Initiativ + Kart i sub-tabs) ----------
        def _mk_combat(self):
            """Kamp-fane med sub-tabs: Initiativ og Kart."""
            self._init_tracker_init()
            if not hasattr(self, '_cmb_sub'):
                self._cmb_sub = 'init'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            # Sub-tab-rad
            sub_bar = RBox(size_hint_y=None, height=dp(42),
                           spacing=dp(4), padding=[dp(6), dp(4)],
                           bg_color=BTN, radius=dp(10))

            b_init = RToggle(
                text='Initiativ', group='cmb_sub',
                state='down' if self._cmb_sub == 'init' else 'normal',
                bg_color=BTNH if self._cmb_sub == 'init' else BTN,
                color=GOLD if self._cmb_sub == 'init' else DIM,
                font_size=sp(12), bold=True)
            b_init.bind(on_release=lambda b: self._cmb_switch('init'))
            sub_bar.add_widget(b_init)

            b_map = RToggle(
                text='Kart', group='cmb_sub',
                state='down' if self._cmb_sub == 'map' else 'normal',
                bg_color=BTNH if self._cmb_sub == 'map' else BTN,
                color=GOLD if self._cmb_sub == 'map' else DIM,
                font_size=sp(12), bold=True)
            b_map.bind(on_release=lambda b: self._cmb_switch('map'))
            sub_bar.add_widget(b_map)

            p.add_widget(sub_bar)

            # Innholds-område — fungerer som "tool_area" for init-tracker
            # og som vert for kart-visningen.
            self._cmb_area = BoxLayout()
            p.add_widget(self._cmb_area)

            self._cmb_render()
            return p

        def _cmb_switch(self, which):
            self._cmb_sub = which
            self._cmb_render()

        def _cmb_render(self):
            """Vis initiativ-tracker eller kart-visning."""
            self._cmb_area.clear_widgets()
            # Pek init-tracker sitt target til cmb_area
            self._init_target_area = self._cmb_area
            if self._cmb_sub == 'init':
                self._mk_init_tracker()
            else:
                self._mk_cmb_map()

        def _mk_cmb_map(self):
            """Kart-sub-tab: åpne battlemap eller vis info om tom liste."""
            p = BoxLayout(orientation='vertical',
                          spacing=dp(10), padding=dp(12))

            if not self._init_list:
                p.add_widget(Widget())
                p.add_widget(mklbl(
                    "Legg til deltakere i Initiativ-fanen\n"
                    "for å bruke kartet.",
                    color=DIM, size=13, wrap=True))
                p.add_widget(Widget())
                self._cmb_area.add_widget(p)
                return

            # Info om lista
            n_pc = sum(1 for e in self._init_list
                       if e.get('type') == 'PC')
            n_npc = sum(1 for e in self._init_list
                        if e.get('type') == 'NPC')
            n_fiende = sum(1 for e in self._init_list
                           if e.get('type') == 'Fiende')
            n_s = sum(1 for e in self._init_list
                      if e.get('type') == 'S')

            info_box = RBox(orientation='vertical', bg_color=BG2,
                            size_hint_y=None, height=dp(110),
                            padding=dp(12), spacing=dp(4),
                            radius=dp(10))
            info_box.add_widget(mklbl(
                "KLAR FOR KART", color=GOLD, size=13, bold=True, h=22))
            summary = []
            if n_pc:
                summary.append(f"{n_pc} investigator(er)")
            if n_npc:
                summary.append(f"{n_npc} NPC")
            if n_fiende:
                summary.append(f"{n_fiende} fiende(r)")
            if n_s:
                summary.append(f"{n_s} skapning(er)")
            info_box.add_widget(mklbl(
                "  •  ".join(summary) if summary else "Ingen deltakere",
                color=TXT, size=12, wrap=True))

            act_name = (self._init_list[0].get('name', '')
                        if self._init_phase == 'active'
                        and self._init_list else '')
            if act_name:
                info_box.add_widget(mklbl(
                    f"Nåværende tur: {act_name}",
                    color=DIM, size=11, wrap=True))
            else:
                info_box.add_widget(mklbl(
                    "Gå til Initiativ-fanen og trykk 'Fullfør' "
                    "for å starte runde-rekkefølge.",
                    color=DIM, size=10, wrap=True))
            p.add_widget(info_box)

            # Åpne-knapp
            p.add_widget(mkbtn("Åpne kart (fullskjerm)",
                               self._bm_open, accent=True,
                               size_hint_y=None, height=dp(56)))

            p.add_widget(mklbl(
                "Kartet åpnes som overlay i full skjermbredde. "
                "Bruk 'Lukk' for å komme tilbake hit.",
                color=DIM, size=10, wrap=True, h=40))

            p.add_widget(Widget())
            self._cmb_area.add_widget(p)

        # ---------- LYD (kombinert Musikk + Ambient) ----------
        def _mk_sound(self):
            """Lyd-fane med toggle mellom Musikk og Ambient."""
            if not hasattr(self, '_sound_sub'):
                self._sound_sub = 'mus'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            # Sub-tab-rad
            sub_bar = RBox(size_hint_y=None, height=dp(42),
                           spacing=dp(4), padding=[dp(6), dp(4)],
                           bg_color=BTN, radius=dp(10))

            b_mus = RToggle(
                text='Musikk', group='sound_sub',
                state='down' if self._sound_sub == 'mus' else 'normal',
                bg_color=BTNH if self._sound_sub == 'mus' else BTN,
                color=GOLD if self._sound_sub == 'mus' else DIM,
                font_size=sp(12), bold=True)
            b_mus.bind(on_release=lambda b: self._sound_switch('mus'))
            sub_bar.add_widget(b_mus)

            b_amb = RToggle(
                text='Ambient', group='sound_sub',
                state='down' if self._sound_sub == 'amb' else 'normal',
                bg_color=BTNH if self._sound_sub == 'amb' else BTN,
                color=GOLD if self._sound_sub == 'amb' else DIM,
                font_size=sp(12), bold=True)
            b_amb.bind(on_release=lambda b: self._sound_switch('amb'))
            sub_bar.add_widget(b_amb)

            p.add_widget(sub_bar)

            # Innholds-område
            self._sound_area = BoxLayout()
            p.add_widget(self._sound_area)

            self._sound_render()
            return p

        def _sound_switch(self, which):
            self._sound_sub = which
            self._sound_render()

        def _sound_render(self):
            self._sound_area.clear_widgets()
            if self._sound_sub == 'mus':
                self._sound_area.add_widget(self._mk_mus())
            else:
                self._sound_area.add_widget(self._mk_amb())

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
                    self.trk_lbl.text = "Mappe ikke funnet"
                    self.trk_grid.add_widget(
                        mklbl("Musikkmappen finnes ikke ennå.\n"
                              "Start appen på nytt etter å ha\n"
                              "godtatt tillatelser.",
                              color=DIM, size=11, wrap=True))
                    return
                fl = sorted([f for f in os.listdir(MUSIC_DIR)
                             if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                self.trk_lbl.text = f"{len(fl)} spor"
                if not fl:
                    self.trk_grid.add_widget(
                        mklbl("Ingen musikkfiler funnet.\n\n"
                              "Legg lydfiler i:\n"
                              "Dokumenter/EldritchPortal/music/\n\n"
                              "Støttede formater:\n"
                              ".mp3  .ogg  .wav  .flac",
                              color=DIM, size=11, wrap=True))
                    return
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
            """Sammenleggbar mappe-visning med overlay for innhold."""
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))
            self._rules_expanded = set()
            self._rules_overlay = None

            # Header
            hdr = BoxLayout(size_hint_y=None, height=dp(34))
            hdr.add_widget(mklbl("REGLER & REFERANSE", color=GOLD, size=15, bold=True))
            p.add_widget(hdr)
            p.add_widget(mksep(2))

            # Mappe-liste
            scroll = ScrollView()
            self._rules_tree = GridLayout(cols=1, spacing=dp(2), padding=dp(4), size_hint_y=None)
            self._rules_tree.bind(minimum_height=self._rules_tree.setter('height'))
            scroll.add_widget(self._rules_tree)
            p.add_widget(scroll)

            # Overlay-container (usynlig til innhold åpnes)
            self._rules_main = p
            self._rules_build_tree()
            return p

        def _rules_build_tree(self):
            """Bygg mappetreet med åpne/lukkede mapper."""
            self._rules_tree.clear_widgets()
            for i, (cat_name, icon, subs) in enumerate(RULES):
                expanded = i in self._rules_expanded
                arrow = "[-]" if expanded else "[+]"
                # Mappe-knapp
                fbtn = RBtn(
                    text=f"  {arrow}  {cat_name}",
                    bg_color=BTNH if expanded else BTN,
                    color=GOLD if expanded else TXT,
                    font_size=sp(13), halign='left',
                    size_hint_y=None, height=dp(44))
                fbtn.bind(on_release=lambda x, idx=i: self._rules_toggle(idx))
                self._rules_tree.add_widget(fbtn)

                if expanded:
                    for j, (sub_name, content) in enumerate(subs):
                        n = len([l for l in content if l])
                        sbtn = RBtn(
                            text=f"       >  {sub_name}",
                            bg_color=BG2, color=TXT,
                            font_size=sp(12), halign='left',
                            size_hint_y=None, height=dp(38))
                        sbtn.bind(on_release=lambda x, ci=i, si=j: self._rules_open(ci, si))
                        self._rules_tree.add_widget(sbtn)

        def _rules_toggle(self, cat_idx):
            """Åpne/lukke en mappe."""
            if cat_idx in self._rules_expanded:
                self._rules_expanded.discard(cat_idx)
            else:
                self._rules_expanded.add(cat_idx)
            self._rules_build_tree()

        def _rules_open(self, cat_idx, sub_idx):
            """Vis regelinnhold som overlay."""
            cat_name, icon, subs = RULES[cat_idx]
            sub_name, content = subs[sub_idx]

            # Fjern evt. eksisterende overlay
            self._rules_close_overlay()

            # Bygg overlay
            overlay = RBox(bg_color=BG, radius=dp(16),
                           orientation='vertical', spacing=dp(4),
                           padding=dp(8),
                           size_hint=(0.95, 0.92),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})

            # Header med lukk + navigering
            hdr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
            hdr.add_widget(mkbtn("Lukk", self._rules_close_overlay,
                                 danger=True, small=True, size_hint_x=0.25))
            if sub_idx > 0:
                hdr.add_widget(mkbtn("<<",
                    lambda: (self._rules_close_overlay(), self._rules_open(cat_idx, sub_idx - 1)),
                    small=True, size_hint_x=None, width=dp(36)))
            else:
                hdr.add_widget(Widget(size_hint_x=None, width=dp(36)))

            hdr.add_widget(mklbl(sub_name, color=GOLD, size=13, bold=True))

            if sub_idx < len(subs) - 1:
                hdr.add_widget(mkbtn(">>",
                    lambda: (self._rules_close_overlay(), self._rules_open(cat_idx, sub_idx + 1)),
                    small=True, size_hint_x=None, width=dp(36)))
            else:
                hdr.add_widget(Widget(size_hint_x=None, width=dp(36)))
            overlay.add_widget(hdr)

            # Breadcrumb
            overlay.add_widget(mklbl(f"{cat_name}  >  {sub_name}",
                                     color=DIM, size=10, h=18))

            # Separator
            sep = Widget(size_hint_y=None, height=dp(1))
            from kivy.graphics import Color as GColor, Rectangle as GRect
            with sep.canvas:
                GColor(rgba=BTNH)
                r = GRect(pos=sep.pos, size=sep.size)
            sep.bind(pos=lambda w, v: setattr(r, 'pos', w.pos),
                     size=lambda w, v: setattr(r, 'size', w.size))
            overlay.add_widget(sep)
            overlay.add_widget(mksep(4))

            # Innhold
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(1), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for line in content:
                if line == "":
                    g.add_widget(mksep(10))
                elif line.startswith("  "):
                    g.add_widget(mklbl(line, color=DIM, size=12, h=20))
                else:
                    g.add_widget(mklbl(line, color=TXT, size=13, h=22))

            g.add_widget(mksep(30))
            scroll.add_widget(g)
            overlay.add_widget(scroll)

            # Legg overlay over hele content-området
            # Bruk FloatLayout-wrapperen (root)
            root = self._rules_main
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            fl = root.parent if isinstance(root.parent, FloatLayout) else root

            # Dimmet bakgrunn
            dim = Widget(size_hint=(1, 1))
            from kivy.graphics import Color as GC2, Rectangle as GR2
            with dim.canvas:
                GC2(rgba=[0, 0, 0, 0.6])
                dr = GR2(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            dim.bind(on_touch_down=lambda w, t: self._rules_close_overlay() or True)

            self._rules_dim = dim
            self._rules_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _rules_close_overlay(self):
            """Lukk regelinnhold-overlay."""
            if self._rules_overlay and self._rules_overlay.parent:
                fl = self._rules_overlay.parent
                fl.remove_widget(self._rules_overlay)
                if hasattr(self, '_rules_dim') and self._rules_dim and self._rules_dim.parent:
                    fl.remove_widget(self._rules_dim)
            self._rules_overlay = None
            self._rules_dim = None


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

        # ---------- KARAKTERER / VERKTØY ----------
        def _mk_tool(self):
            """Verktøy-fane med sub-tabs: Karakterer, Våpen, Scenario."""
            self._scen_init()
            # Migrer bort fra gammel 'init'-sub-tab hvis det ligger igjen
            if not hasattr(self, '_tool_sub') or self._tool_sub == 'init':
                self._tool_sub = 'chars'

            p = BoxLayout(orientation='vertical', spacing=dp(6))

            # Sub-tab-rad
            sub_bar = RBox(size_hint_y=None, height=dp(42),
                           spacing=dp(4), padding=[dp(6), dp(4)],
                           bg_color=BTN, radius=dp(10))
            b_chars = RToggle(
                text='Karakterer', group='tool_sub',
                state='down' if self._tool_sub == 'chars' else 'normal',
                bg_color=BTNH if self._tool_sub == 'chars' else BTN,
                color=GOLD if self._tool_sub == 'chars' else DIM,
                font_size=sp(11), bold=True)
            b_chars.bind(on_release=lambda b: self._tool_switch('chars'))
            sub_bar.add_widget(b_chars)

            b_weap = RToggle(
                text='Våpen', group='tool_sub',
                state='down' if self._tool_sub == 'weap' else 'normal',
                bg_color=BTNH if self._tool_sub == 'weap' else BTN,
                color=GOLD if self._tool_sub == 'weap' else DIM,
                font_size=sp(11), bold=True)
            b_weap.bind(on_release=lambda b: self._tool_switch('weap'))
            sub_bar.add_widget(b_weap)

            b_scen = RToggle(
                text='Scenario', group='tool_sub',
                state='down' if self._tool_sub == 'scen' else 'normal',
                bg_color=BTNH if self._tool_sub == 'scen' else BTN,
                color=GOLD if self._tool_sub == 'scen' else DIM,
                font_size=sp(11), bold=True)
            b_scen.bind(on_release=lambda b: self._tool_switch('scen'))
            sub_bar.add_widget(b_scen)

            p.add_widget(sub_bar)

            # Handlings-rad
            self._tool_action_bar = BoxLayout(
                size_hint_y=None, height=dp(42),
                spacing=dp(6), padding=[dp(6), 0])
            p.add_widget(self._tool_action_bar)

            self.tool_area = BoxLayout()
            p.add_widget(self.tool_area)

            # Når vi er i Verktøy-fanen skal init-tracker (hvis den kalles)
            # bruke denne tool_area — men siden init-sub-tab er fjernet,
            # skal det ikke skje. Sett target til None for sikkerhets skyld.
            self._init_target_area = None

            self._tool_render_sub()
            return p

        def _tool_switch(self, which):
            """Bytt mellom karakterer, våpen og scenario."""
            self._tool_sub = which
            self._tool_render_sub()

        def _tool_render_sub(self):
            """Rendre riktig sub-visning."""
            self._tool_action_bar.clear_widgets()
            if self._tool_sub == 'chars':
                self._tool_action_bar.add_widget(
                    mkbtn("+ Ny", self._new_char, accent=True,
                          small=True, size_hint_x=0.22))
                self._tool_action_bar.add_widget(
                    mkbtn("Importer", self._chars_import,
                          small=True, size_hint_x=0.25))
                self._tool_action_bar.add_widget(
                    mkbtn("Eksporter", self._chars_export,
                          small=True, size_hint_x=0.25))
                self._tool_action_bar.add_widget(
                    mklbl("Karakterer", color=GOLD, size=13, bold=True))
                self._show_list()
            elif self._tool_sub == 'scen':
                self._mk_scenario()
            else:
                self._mk_weapons()

        def _show_list(self):
            self.tool_area.clear_widgets()
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(6), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            if not self.chars:
                g.add_widget(mklbl("Ingen karakterer ennå.\nTrykk '+ Ny' for å lage en.",
                                   color=DIM, size=12, h=50))
            else:
                for i, ch in enumerate(self.chars):
                    nm, tp = ch.get('name', '?'), ch.get('type', 'PC')
                    oc = ch.get('occ', '')
                    c = GRN if tp == 'PC' else (RED if tp == 'Fiende' else GOLD)
                    txt = f"[{tp}]  {nm}"
                    if oc:
                        txt += f"  -  {oc}"
                    row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(4))
                    b = mkbtn(txt, lambda idx=i: self._view_char(idx),
                              small=True, size_hint_x=0.52)
                    b.color = c
                    b.halign = 'left'
                    row.add_widget(b)
                    row.add_widget(mkbtn("Rediger", lambda idx=i: self._edit_char(idx),
                                        accent=True, small=True, size_hint_x=0.22))
                    up_btn = mkbtn("▲", lambda idx=i: self._move_char(idx, -1),
                                   small=True, size_hint_x=0.12)
                    up_btn.disabled = (i == 0)
                    row.add_widget(up_btn)
                    down_btn = mkbtn("▼", lambda idx=i: self._move_char(idx, 1),
                                     small=True, size_hint_x=0.12)
                    down_btn.disabled = (i == len(self.chars) - 1)
                    row.add_widget(down_btn)
                    g.add_widget(row)
            scroll.add_widget(g)
            self.tool_area.add_widget(scroll)

        def _move_char(self, idx, direction):
            """Flytt karakter opp (direction=-1) eller ned (direction=1) i lista."""
            new_idx = idx + direction
            if 0 <= new_idx < len(self.chars):
                self.chars[idx], self.chars[new_idx] = self.chars[new_idx], self.chars[idx]
                save_json(CHAR_FILE, self.chars)
                self._show_list()

        def _reload_characters(self):
            self.chars = load_characters(CHAR_FILE)
            self._show_list()

        # ---------- KARAKTER IMPORT / EKSPORT ----------

        def _open_char_overlay(self, overlay):
            """Legg overlay + dim på FloatLayout-roten (samme mønster som våpen-detalj)."""
            root = self.content
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                self.tool_area.add_widget(overlay)
                self._chars_overlay = overlay
                return
            fl = root.parent

            from kivy.graphics import Color as GColor, Rectangle as GRect
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GColor(rgba=[0, 0, 0, 0.6])
                dr = GRect(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))

            self._chars_dim = dim
            self._chars_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _chars_close_overlay(self):
            """Lukk aktivt karakter-overlay."""
            if self._chars_overlay and self._chars_overlay.parent:
                parent = self._chars_overlay.parent
                parent.remove_widget(self._chars_overlay)
                if self._chars_dim and self._chars_dim.parent:
                    parent.remove_widget(self._chars_dim)
            self._chars_overlay = None
            self._chars_dim = None

        def _chars_show_message(self, msg, success=False):
            """Vis kort statusmelding som overlay."""
            self._chars_close_overlay()
            color = GRN if success else RED
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(8),
                padding=dp(16),
                size_hint=(0.82, None),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            overlay.height = dp(180)
            overlay.add_widget(mklbl(msg, color=color, size=13, wrap=True))
            overlay.add_widget(Widget())
            overlay.add_widget(mkbtn("OK", self._chars_close_overlay,
                                     accent=True, size_hint_y=None, height=dp(44)))
            self._open_char_overlay(overlay)

        def _chars_export(self):
            """Eksporter karakterlisten til Documents-mappen som characters_export.json."""
            if not self.chars:
                self._chars_show_message("Ingen karakterer å eksportere.")
                return
            try:
                export_path = os.path.join(BASE_DIR, "characters_export.json")
                os.makedirs(BASE_DIR, exist_ok=True)
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self.chars, f, indent=2, ensure_ascii=False)
                n = len(self.chars)
                self._chars_show_message(
                    f"Eksporterte {n} karakter{'er' if n != 1 else ''} til:\n{export_path}",
                    success=True)
            except Exception as e:
                self._chars_show_message(f"Eksport feilet:\n{e}")

        def _chars_import(self):
            """Åpne filvelger-overlay for å importere en karakterfil."""
            self._chars_close_overlay()
            try:
                os.makedirs(BASE_DIR, exist_ok=True)
            except Exception:
                pass
            start_path = BASE_DIR if os.path.exists(BASE_DIR) else os.path.expanduser("~")
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(4),
                padding=dp(10),
                size_hint=(0.96, 0.92),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            hdr.add_widget(mkbtn("Avbryt", self._chars_close_overlay,
                                 danger=True, small=True, size_hint_x=0.3))
            hdr.add_widget(mklbl("Velg .json-fil", color=GOLD, size=14, bold=True))
            overlay.add_widget(hdr)

            fc = FileChooserListView(
                path=start_path,
                filters=['*.json'],
                size_hint_y=1)
            overlay.add_widget(fc)

            sel_btn = mkbtn("Velg", lambda: self._chars_import_selected(fc.selection),
                            accent=True, size_hint_y=None)
            sel_btn.height = dp(44)
            overlay.add_widget(sel_btn)
            self._open_char_overlay(overlay)

        def _chars_import_selected(self, selection):
            """Valider valgt .json-fil og vis forhåndsvisning."""
            if not selection:
                self._chars_show_message("Ingen fil valgt.")
                return
            path = selection[0]
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self._chars_show_message(f"Feil ved lesing av fil:\n{e}")
                return
            valid = normalize_characters_data(data)
            if not valid:
                self._chars_show_message(
                    "Ingen gyldige karakterer funnet i filen.\n\n"
                    "Forventet et JSON-objekt eller en liste med karakterer "
                    "(hvert objekt må ha et 'name'-felt).")
                return
            self._chars_close_overlay()
            self._chars_show_import_preview(valid)

        def _chars_show_import_preview(self, chars_to_import):
            """Vis forhåndsvisning av karakterer som skal importeres med Slå sammen/Erstatt."""
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(6),
                padding=dp(12),
                size_hint=(0.94, 0.90),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            hdr.add_widget(mkbtn("Avbryt", self._chars_close_overlay,
                                 danger=True, small=True, size_hint_x=0.3))
            hdr.add_widget(mklbl("Forhåndsvisning", color=GOLD, size=14, bold=True))
            overlay.add_widget(hdr)

            n = len(chars_to_import)
            overlay.add_widget(mklbl(
                f"{n} karakter{'er' if n != 1 else ''} funnet:",
                color=TXT, size=13, h=28))

            scroll = ScrollView(size_hint_y=1)
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for ch in chars_to_import[:20]:
                nm = ch.get('name', '?')
                tp = ch.get('type', 'PC')
                oc = ch.get('occ', '')
                txt = f"[{tp}]  {nm}"
                if oc:
                    txt += f"  —  {oc}"
                c = GRN if tp == 'PC' else (RED if tp == 'Fiende' else GOLD)
                g.add_widget(mklbl(txt, color=c, size=12, h=28))
            if n > 20:
                g.add_widget(mklbl(f"... og {n - 20} til", color=DIM, size=11, h=22))
            scroll.add_widget(g)
            overlay.add_widget(scroll)

            overlay.add_widget(mksep(4))
            btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            btns.add_widget(mkbtn(
                "Legg til eksisterende",
                lambda: self._chars_do_import(chars_to_import, replace=False),
                accent=True, small=True))
            btns.add_widget(mkbtn(
                "Erstatt alle",
                lambda: self._chars_do_import(chars_to_import, replace=True),
                danger=True, small=True))
            overlay.add_widget(btns)
            self._open_char_overlay(overlay)

        def _chars_do_import(self, chars_to_import, replace=False):
            """Utfør import, lagre og oppdater karakterlisten."""
            if replace:
                self.chars = list(chars_to_import)
            else:
                self.chars.extend(chars_to_import)
            save_json(CHAR_FILE, self.chars)
            n = len(chars_to_import)
            verb = "Erstattet alle med" if replace else "La til"
            self._chars_close_overlay()
            self._chars_show_message(
                f"{verb} {n} karakter{'er' if n != 1 else ''}.",
                success=True)
            self._show_list()

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
            # Karakteristikker med individuelle rammer
            stats_list = [(lbl, ch[key]) for key, lbl in CHAR_STATS if ch.get(key)]
            if stats_list:
                g.add_widget(mksep(4))
                g.add_widget(mklbl("KARAKTERISTIKKER", color=GOLD, size=13, bold=True, h=24))
                stats_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
                for lbl, val in stats_list:
                    framed = FramedBox(orientation='vertical', size_hint_x=1, padding=dp(4), spacing=dp(2))
                    framed.add_widget(Label(text=lbl, font_size=sp(10), color=GOLD, bold=True))
                    framed.add_widget(Label(text=str(val), font_size=sp(14), color=TXT, bold=True))
                    stats_row.add_widget(framed)
                g.add_widget(stats_row)
            # Derived stats med individuelle rammer
            derived_list = [(lbl, ch[key]) for key, lbl in CHAR_DERIVED if ch.get(key)]
            if derived_list:
                g.add_widget(mksep(4))
                g.add_widget(mklbl("HP / MP / SAN / LUCK", color=GOLD, size=13, bold=True, h=24))
                derived_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
                for lbl, val in derived_list:
                    framed = FramedBox(orientation='vertical', size_hint_x=1, padding=dp(4), spacing=dp(2))
                    framed.add_widget(Label(text=lbl, font_size=sp(10), color=GOLD, bold=True))
                    framed.add_widget(Label(text=str(val), font_size=sp(14), color=TXT, bold=True))
                    derived_row.add_widget(framed)
                g.add_widget(derived_row)
            sk = ch.get('skills', {})
            if sk and isinstance(sk, dict):
                g.add_widget(mksep(4))
                g.add_widget(mklbl("FERDIGHETER", color=GOLD, size=13, bold=True, h=24))
                for sn in sorted(sk.keys()):
                    sv = sk[sn]
                    if sv:
                        sk_txt = f"{sn}: {sv}"
                        framed = FramedBox(orientation='horizontal', size_hint_y=None, 
                                         height=dp(34), padding=dp(4), spacing=dp(4))
                        framed.add_widget(mklbl(sk_txt, color=TXT, size=12, wrap=True))
                        g.add_widget(framed)
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
                    w = Spinner(text=ch.get(key, 'PC'), values=['PC', 'NPC', 'Fiende'],
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

        # ---------- INITIATIV-TRACKER (CoC / Pulp Cthulhu) ----------
        def _init_tracker_init(self):
            """Initialiser state for initiativ-tracker."""
            if not hasattr(self, '_init_phase'):
                self._init_phase = 'setup'
                self._init_list = []
            # target_area overstyres av Kamp-fanen til self._cmb_area
            if not hasattr(self, '_init_target_area'):
                self._init_target_area = None

        def _init_area(self):
            """Returner current container for initiativ-UI."""
            tgt = getattr(self, '_init_target_area', None)
            if tgt is not None:
                return tgt
            return self.tool_area

        def _mk_init_tracker(self):
            """Bygg initiativ-tracker-UI."""
            self._init_tracker_init()
            area = self._init_area()
            area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            if self._init_phase == 'setup':
                self._init_build_setup(p)
            else:
                self._init_build_active(p)

            area.add_widget(p)

        def _init_build_setup(self, p):
            """Setup-fase: velg deltakere og juster DEX-verdier."""
            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("+ Investigator", self._init_show_char_picker,
                                 accent=True, small=True, size_hint_x=0.37))
            top.add_widget(mkbtn("+ Skapning", self._init_show_enemy_picker,
                                 small=True, size_hint_x=0.33))
            top.add_widget(mkbtn("Tom", self._init_clear_list,
                                 danger=True, small=True, size_hint_x=0.3))
            p.add_widget(top)

            p.add_widget(mklbl(
                "DEX avgjør rekkefølgen. +50 hvis skyter med håndvåpen.",
                color=DIM, size=10, h=18))

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            if not self._init_list:
                g.add_widget(mklbl(
                    "Ingen deltakere. Bruk knappene over.",
                    color=DIM, size=12, h=60))
            else:
                # Header
                hdr = BoxLayout(size_hint_y=None, height=dp(22),
                                spacing=dp(4))
                hdr.add_widget(mklbl("Navn", color=GDIM, size=9, h=20))
                hdr.add_widget(Label(text="DEX", font_size=sp(9),
                                     color=GDIM, size_hint_x=None,
                                     width=dp(50)))
                hdr.add_widget(Label(text="+50", font_size=sp(9),
                                     color=GDIM, size_hint_x=None,
                                     width=dp(34)))
                hdr.add_widget(Label(text="", size_hint_x=None,
                                     width=dp(36)))
                g.add_widget(hdr)

                self._init_inputs = []
                for i, entry in enumerate(self._init_list):
                    row_box = RBox(orientation='horizontal', bg_color=BG2,
                                   size_hint_y=None, height=dp(44),
                                   padding=dp(6), spacing=dp(4), radius=dp(8))

                    # Type-chip (PC/NPC/S = skapning)
                    tp = entry.get('type', 'PC')
                    chip_color = GRN if tp == 'PC' else (GOLD if tp == 'NPC' else RED)
                    chip = Label(text=tp, font_size=sp(10), color=chip_color,
                                 bold=True, size_hint_x=None, width=dp(46))
                    row_box.add_widget(chip)

                    # Navn + base DEX-hint
                    nm = entry.get('name', '?')
                    base_dex = entry.get('base_dex', 0)
                    hint = f"  (base {base_dex})" if base_dex else ""
                    nm_lb = Label(text=f"{nm}{hint}",
                                  font_size=sp(12), color=TXT,
                                  halign='left', valign='middle')
                    nm_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                    row_box.add_widget(nm_lb)

                    # DEX-verdi (redigerbar)
                    dex_val = str(entry.get('dex', entry.get('base_dex', 0)))
                    dex_inp = TextInput(
                        text=dex_val, font_size=sp(13), multiline=False,
                        background_color=INPUT, foreground_color=TXT,
                        cursor_color=GOLD,
                        size_hint_x=None, width=dp(50),
                        padding=[dp(4), dp(6)],
                        input_filter='int')
                    dex_inp._init_idx = i
                    dex_inp.bind(text=self._init_on_dex_change)
                    self._init_inputs.append(dex_inp)
                    row_box.add_widget(dex_inp)

                    # +50 firearms-toggle
                    fa_tog = RToggle(
                        text='X' if entry.get('firearms') else '',
                        state='down' if entry.get('firearms') else 'normal',
                        color=GOLD if entry.get('firearms') else DIM,
                        bg_color=BTNH if entry.get('firearms') else INPUT,
                        font_size=sp(11), bold=True,
                        size_hint_x=None, width=dp(34))
                    fa_tog._init_idx = i
                    fa_tog.bind(state=self._init_on_firearms_change)
                    row_box.add_widget(fa_tog)

                    # Fjern-knapp
                    del_btn = RBtn(text='X', bg_color=BTN, color=RED,
                                   font_size=sp(11), bold=True,
                                   size_hint_x=None, width=dp(36))
                    del_btn.bind(on_release=lambda b, idx=i:
                                 self._init_remove_entry(idx))
                    row_box.add_widget(del_btn)

                    g.add_widget(row_box)

            scroll.add_widget(g)
            p.add_widget(scroll)

            bottom = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            bottom.add_widget(mkbtn("Kart", self._bm_open,
                                    small=True, size_hint_x=0.4))
            bottom.add_widget(mkbtn("Fullfør", self._init_finish,
                                    accent=True, size_hint_x=0.6))
            p.add_widget(bottom)

        def _init_on_dex_change(self, inst, value):
            """Lagre DEX-verdi."""
            idx = inst._init_idx
            if 0 <= idx < len(self._init_list):
                try:
                    self._init_list[idx]['dex'] = int(value) if value else 0
                except ValueError:
                    self._init_list[idx]['dex'] = 0

        def _init_on_firearms_change(self, inst, value):
            """Oppdater +50 firearms-toggle."""
            idx = inst._init_idx
            if 0 <= idx < len(self._init_list):
                on = (value == 'down')
                self._init_list[idx]['firearms'] = on
                inst.text = 'X' if on else ''
                inst.color = GOLD if on else DIM
                inst.bg_color = BTNH if on else INPUT

        def _init_show_char_picker(self):
            """Vis Investigator-velger."""
            already_in = {e.get('name', '') for e in self._init_list}
            pcs = [ch for ch in self.chars
                   if ch.get('type', 'PC') == 'PC'
                   and ch.get('name', '') not in already_in]
            npcs = [ch for ch in self.chars
                    if ch.get('type', 'PC') == 'NPC'
                    and ch.get('name', '') not in already_in]
            fiender = [ch for ch in self.chars
                       if ch.get('type', 'PC') == 'Fiende'
                       and ch.get('name', '') not in already_in]

            area = self._init_area()
            area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("Tilbake", self._mk_init_tracker,
                                 small=True, size_hint_x=0.3))
            top.add_widget(mklbl("Velg karakter", color=GOLD, size=13,
                                 bold=True))
            p.add_widget(top)

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            if pcs:
                g.add_widget(mklbl("INVESTIGATORER (PC)",
                                   color=GRN, size=11, bold=True, h=22))
                for ch in pcs:
                    g.add_widget(self._init_make_char_btn(ch))

            if npcs:
                g.add_widget(mklbl("NPC-ER",
                                   color=GOLD, size=11, bold=True, h=22))
                for ch in npcs:
                    g.add_widget(self._init_make_char_btn(ch))

            if fiender:
                g.add_widget(mklbl("FIENDER",
                                   color=RED, size=11, bold=True, h=22))
                for ch in fiender:
                    g.add_widget(self._init_make_char_btn(ch))

            if not pcs and not npcs and not fiender:
                g.add_widget(mklbl(
                    "Ingen tilgjengelige karakterer.\n"
                    "Legg til karakterer under 'Verktøy > Karakterer' først.",
                    color=DIM, size=11, h=60))

            scroll.add_widget(g)
            p.add_widget(scroll)
            area.add_widget(p)

        def _init_make_char_btn(self, ch):
            """Lag knapp for en karakter i picker-liste."""
            nm = ch.get('name', '?')
            occ = ch.get('occ', '')
            dex = ch.get('dex', '')
            parts = []
            if occ:
                parts.append(occ)
            if dex:
                parts.append(f"DEX {dex}")
            sub = "  -  ".join(parts)
            txt = f"{nm}   {sub}" if sub else nm
            b = mkbtn(txt, lambda c=ch: self._init_add_character(c),
                      small=True)
            b.halign = 'left'
            b.size_hint_y = None
            b.height = dp(42)
            return b

        def _init_add_character(self, ch):
            """Legg til karakter i initiativ-lista."""
            try:
                dex = int(ch.get('dex', 0) or 0)
            except (ValueError, TypeError):
                dex = 0
            self._init_list.append({
                'name': ch.get('name', '?'),
                'type': ch.get('type', 'PC'),
                'base_dex': dex,
                'dex': dex,
                'firearms': False,
                'hp': ch.get('hp', ''),
            })
            self._mk_init_tracker()

        # Vanlige fiender og skapninger i Call of Cthulhu / Pulp Cthulhu.
        # (navn, DEX, HP)
        COMMON_ENEMIES = [
            # --- Mennesker ---
            ("Kultist", 55, 11),
            ("Kult-leder", 65, 12),
            ("Leiesoldat", 65, 13),
            ("Bandit", 50, 10),
            ("Politimann", 55, 12),
            ("Detektiv", 60, 12),
            ("Soldat", 60, 13),
            ("Offiser", 65, 14),
            ("Gal vitenskapsmann", 50, 10),
            ("Prestinne", 55, 11),
            ("Tyv", 70, 10),
            ("Brutal slager", 55, 14),
            ("Mystiker", 60, 10),
            ("Nekromantiker", 55, 11),
            ("Spion", 70, 11),
            # --- Normale dyr ---
            ("Hund (vakt)", 60, 8),
            ("Ulv", 75, 11),
            ("Bjørn", 50, 19),
            ("Puma", 85, 12),
            ("Slange (giftig)", 85, 4),
            ("Rotte (stor)", 60, 2),
            ("Rotte-svamp", 90, 35),
            ("Krokodille", 50, 14),
            ("Hai", 80, 18),
            # --- Udøde ---
            ("Zombie", 45, 12),
            ("Ghoul", 65, 13),
            ("Mumie", 50, 18),
            ("Vampyr", 80, 15),
            ("Skjelett", 55, 10),
            ("Gjenferd (spectre)", 70, 0),
            # --- Mindre mytos-skapninger ---
            ("Byakhee", 50, 11),
            ("Chthonian (ung)", 20, 42),
            ("Chthonian (voksen)", 15, 85),
            ("Deep One", 45, 15),
            ("Deep One Hybrid", 60, 12),
            ("Dark Young (Shub-Niggurath)", 45, 60),
            ("Dimensional Shambler", 45, 25),
            ("Dhole", 30, 120),
            ("Fire Vampire", 45, 12),
            ("Flying Polyp", 70, 55),
            ("Formless Spawn", 60, 30),
            ("Ghast", 75, 18),
            ("Ghoul (Mytos)", 65, 13),
            ("Gnorri", 40, 15),
            ("Hound of Tindalos", 90, 34),
            ("Hunting Horror", 75, 46),
            ("Lloigor", 60, 25),
            ("Mi-Go", 55, 13),
            ("Moon-Beast", 50, 42),
            ("Nightgaunt", 65, 12),
            ("Rat-Thing", 80, 4),
            ("Sand-Dweller", 55, 14),
            ("Servant of Glaaki", 35, 18),
            ("Serpent Person", 65, 12),
            ("Shantak", 45, 40),
            ("Shoggoth", 25, 100),
            ("Shoggoth (mindre)", 25, 65),
            ("Spawn of Cthulhu", 40, 60),
            ("Star Vampire", 75, 36),
            ("Star Spawn of Cthulhu", 30, 135),
            ("Tcho-Tcho", 70, 11),
            ("Wendigo", 60, 65),
            ("Winged One (av Yuggoth)", 55, 14),
            ("Y'm-bhi (aktivert ghoul)", 55, 14),
            # --- Uavhengige vesener ---
            ("Elder Thing", 45, 28),
            ("Great Race of Yith", 25, 25),
            ("Yithian (i menneske-vert)", 50, 13),
            # --- Pulp-spesifikke gangstere/pulp-fiender ---
            ("Gangster (lakei)", 55, 12),
            ("Gangster (boss)", 60, 14),
            ("Nazi-offiser", 65, 13),
            ("Nazi-soldat", 60, 12),
            ("SS-okkultist", 65, 13),
            ("Pulp-skurk (mastermind)", 75, 15),
            ("Femme fatale", 75, 11),
            ("Privat etterforsker (Pulp)", 70, 13),
        ]

        def _init_show_enemy_picker(self):
            """Vis liste over CoC-fiender og skapninger + egendefinert."""
            area = self._init_area()
            area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))

            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("Tilbake", self._mk_init_tracker,
                                 small=True, size_hint_x=0.3))
            top.add_widget(mklbl("Velg skapning", color=GOLD, size=13,
                                 bold=True))
            p.add_widget(top)

            # Egendefinert
            cust_box = RBox(orientation='vertical', bg_color=BG2,
                            size_hint_y=None, height=dp(110),
                            padding=dp(10), spacing=dp(6), radius=dp(10))
            cust_box.add_widget(mklbl("Egendefinert skapning",
                                      color=GOLD, size=11, bold=True, h=18))

            name_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            name_row.add_widget(Label(text="Navn:", font_size=sp(11),
                                      color=DIM, size_hint_x=0.2,
                                      halign='right', valign='middle'))
            self._init_custom_name = TextInput(
                text='', font_size=sp(12), multiline=False,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD, padding=[dp(8), dp(6)],
                size_hint_x=0.8)
            name_row.add_widget(self._init_custom_name)
            cust_box.add_widget(name_row)

            stat_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            stat_row.add_widget(Label(text="DEX:", font_size=sp(11),
                                      color=DIM, size_hint_x=0.2,
                                      halign='right', valign='middle'))
            self._init_custom_dex = TextInput(
                text='50', font_size=sp(12), multiline=False,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD, padding=[dp(8), dp(6)],
                size_hint_x=0.2, input_filter='int')
            stat_row.add_widget(self._init_custom_dex)

            stat_row.add_widget(Widget(size_hint_x=0.1))
            add_btn = mkbtn("Legg til", self._init_add_custom,
                            accent=True, small=True, size_hint_x=0.5)
            stat_row.add_widget(add_btn)
            cust_box.add_widget(stat_row)

            p.add_widget(cust_box)

            p.add_widget(mklbl("CoC & Pulp Cthulhu-skapninger",
                               color=GOLD, size=11, bold=True, h=22))

            scroll = ScrollView()
            g = GridLayout(cols=2, spacing=dp(4), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for name, dex, hp in self.COMMON_ENEMIES:
                txt = f"{name} ({dex})"
                b = mkbtn(txt,
                          lambda n=name, d=dex, h=hp:
                              self._init_add_enemy(n, d, h),
                          small=True)
                b.size_hint_y = None
                b.height = dp(42)
                b.halign = 'left'
                b.font_size = sp(10)
                g.add_widget(b)

            scroll.add_widget(g)
            p.add_widget(scroll)
            area.add_widget(p)

        def _init_add_enemy(self, name, dex, hp):
            """Legg til fiende fra lista. Inkrement hvis duplicate."""
            final_name = name
            existing = [e.get('name', '') for e in self._init_list]
            if final_name in existing:
                n = 2
                while f"{name} {n}" in existing:
                    n += 1
                final_name = f"{name} {n}"

            self._init_list.append({
                'name': final_name,
                'type': 'S',
                'base_dex': dex,
                'dex': dex,
                'firearms': False,
                'hp': str(hp) if hp else '',
            })
            self._mk_init_tracker()

        def _init_add_custom(self):
            """Legg til egendefinert skapning."""
            name = self._init_custom_name.text.strip()
            if not name:
                return
            try:
                dex = int(self._init_custom_dex.text or '0')
            except ValueError:
                dex = 0
            self._init_add_enemy(name, dex, '')

        def _init_remove_entry(self, idx):
            """Fjern deltaker fra lista."""
            if 0 <= idx < len(self._init_list):
                self._init_list.pop(idx)
                self._mk_init_tracker()

        def _init_clear_list(self):
            """Tom hele lista."""
            self._init_list = []
            self._init_phase = 'setup'
            self._mk_init_tracker()

        def _init_finish(self):
            """Gå fra setup til aktiv: sorter etter effektiv DEX."""
            # Effektiv DEX = DEX + 50 hvis firearms
            for entry in self._init_list:
                base = entry.get('dex', 0)
                entry['effective'] = base + (50 if entry.get('firearms') else 0)
            # Sorter høyest først (CoC-regel: høy DEX går først)
            # Tiebreak: høyere base DEX, så alfabetisk navn
            self._init_list.sort(
                key=lambda e: (e.get('effective', 0),
                               e.get('base_dex', 0),
                               e.get('name', '')),
                reverse=True)
            self._init_phase = 'active'
            self._mk_init_tracker()

        def _init_build_active(self, p):
            """Aktiv fase: vis sortert rekkefølge."""
            top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            top.add_widget(mkbtn("Ny runde", self._init_new_encounter,
                                 danger=True, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Rediger", self._init_back_to_setup,
                                 small=True, size_hint_x=0.25))
            top.add_widget(mkbtn("Kart", self._bm_open,
                                 accent=True, small=True, size_hint_x=0.25))
            top.add_widget(mklbl("Tur", color=GOLD, size=12, bold=True))
            p.add_widget(top)

            p.add_widget(mklbl(
                "Trykk på aktiv (øverst) for å avslutte turen.",
                color=DIM, size=10, h=18))

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(6), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for i, entry in enumerate(self._init_list):
                is_active = (i == 0)

                bg = BTNH if is_active else BG2
                box = RBox(orientation='horizontal',
                           bg_color=bg,
                           size_hint_y=None,
                           height=dp(56) if is_active else dp(46),
                           padding=dp(10), spacing=dp(8), radius=dp(10))

                # Effektiv DEX stor
                eff = entry.get('effective', entry.get('dex', 0))
                eff_lb = Label(
                    text=str(eff),
                    font_size=sp(18) if is_active else sp(15),
                    color=GOLD if is_active else TXT,
                    bold=True,
                    size_hint_x=None, width=dp(46),
                    halign='center', valign='middle')
                eff_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                box.add_widget(eff_lb)

                # Type-chip
                tp = entry.get('type', 'PC')
                chip_color = GRN if tp == 'PC' else (GOLD if tp == 'NPC' else RED)
                chip = Label(text=tp, font_size=sp(10), color=chip_color,
                             bold=True,
                             size_hint_x=None, width=dp(46))
                box.add_widget(chip)

                # Navn + firearms-markering
                nm = entry.get('name', '?')
                if entry.get('firearms'):
                    nm_display = f"{nm}  [+50]"
                else:
                    nm_display = nm
                nm_lb = Label(
                    text=nm_display,
                    font_size=sp(15) if is_active else sp(12),
                    color=TXT,
                    bold=is_active,
                    halign='left', valign='middle')
                nm_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                box.add_widget(nm_lb)

                # HP
                hp = entry.get('hp', '')
                if hp:
                    hp_lb = Label(text=f"HP {hp}", font_size=sp(10),
                                  color=DIM,
                                  size_hint_x=None, width=dp(70),
                                  halign='right', valign='middle')
                    hp_lb.bind(size=lambda w, v: setattr(w, 'text_size', v))
                    box.add_widget(hp_lb)

                if is_active:
                    box.bind(on_touch_down=lambda w, t, idx=i:
                             self._init_on_card_touch(w, t, idx))

                g.add_widget(box)

            scroll.add_widget(g)
            p.add_widget(scroll)

        def _init_on_card_touch(self, widget, touch, idx):
            """Trykk på øverste kort = dens tur er ferdig."""
            if not widget.collide_point(*touch.pos):
                return False
            if idx == 0:
                top_entry = self._init_list.pop(0)
                self._init_list.append(top_entry)
                self._mk_init_tracker()
                return True
            return False

        def _init_new_encounter(self):
            """Tøm listen og gå tilbake til setup."""
            self._init_list = []
            self._init_phase = 'setup'
            self._mk_init_tracker()

        def _init_back_to_setup(self):
            """Gå tilbake til setup - behold listen."""
            self._init_phase = 'setup'
            self._mk_init_tracker()


        # ---------- BATTLEMAP ----------
        BM_SIZE = 15  # 15x15 rutenett

        def _bm_open(self):
            """Åpne battlemap som overlay. Sync tokens fra init-lista."""
            if not self._init_list:
                # Ingen deltakere ennå
                return
            self._bm_tokens = {}       # (x, y) -> token dict
            self._bm_unplaced = []     # tokens som ikke er plassert
            self._bm_selected = None   # (x, y) eller None
            self._bm_placing = None    # token som holdes for plassering
            self._bm_overlay = None
            self._bm_dim = None
            self._bm_sync_from_init()
            self._bm_build_overlay()

        def _bm_find_mov(self, name, tp):
            """Finn MOV for en karakter, default 8."""
            if tp in ('PC', 'NPC', 'Fiende'):
                for ch in self.chars:
                    if ch.get('name') == name:
                        try:
                            return int(ch.get('move', 8) or 8)
                        except (ValueError, TypeError):
                            return 8
            return 8

        def _bm_sync_from_init(self):
            """Generer token-liste fra initiativlista."""
            pc_n = 1
            npc_n = 1
            en_n = 1
            for entry in self._init_list:
                tp = entry.get('type', 'PC')
                if tp == 'PC':
                    label = f"P{pc_n}"
                    pc_n += 1
                elif tp == 'NPC':
                    label = f"N{npc_n}"
                    npc_n += 1
                else:
                    label = f"E{en_n}"
                    en_n += 1
                self._bm_unplaced.append({
                    'label': label,
                    'name': entry.get('name', '?'),
                    'type': tp,
                    'mov': self._bm_find_mov(
                        entry.get('name', ''), tp),
                    'used_mov': 0,
                    'hp': entry.get('hp', ''),
                })

        def _bm_build_overlay(self):
            """Bygg overlay-widget."""
            self._bm_close_overlay()

            overlay = RBox(
                bg_color=BG, radius=dp(12),
                orientation='vertical', spacing=dp(4),
                padding=dp(6),
                size_hint=(0.98, 0.95),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            # Header
            hdr = BoxLayout(size_hint_y=None, height=dp(40),
                            spacing=dp(4))
            hdr.add_widget(mkbtn("Lukk", self._bm_close_overlay,
                                 danger=True, small=True,
                                 size_hint_x=0.22))
            self._bm_active_lbl = mklbl(
                "", color=GOLD, size=12, bold=True)
            hdr.add_widget(self._bm_active_lbl)
            hdr.add_widget(mkbtn("Neste", self._bm_next_turn,
                                 accent=True, small=True,
                                 size_hint_x=0.25))
            overlay.add_widget(hdr)

            # Unplaced row
            self._bm_unp_label = mklbl(
                "", color=DIM, size=10, h=20)
            overlay.add_widget(self._bm_unp_label)

            self._bm_unp_scroll = ScrollView(
                size_hint_y=None, height=dp(44),
                do_scroll_y=False)
            self._bm_unp_row = BoxLayout(
                size_hint_x=None, spacing=dp(4),
                padding=[dp(2), 0])
            self._bm_unp_row.bind(
                minimum_width=self._bm_unp_row.setter('width'))
            self._bm_unp_scroll.add_widget(self._bm_unp_row)
            overlay.add_widget(self._bm_unp_scroll)

            # Selve rutenettet — pakket i ScrollView slik at
            # det fyller plassen men ikke krever eksakt kvadrat
            grid_wrap = BoxLayout(padding=dp(2))
            self._bm_grid = GridLayout(
                cols=self.BM_SIZE, rows=self.BM_SIZE,
                spacing=dp(1))
            self._bm_cells = {}
            for y in range(self.BM_SIZE):
                for x in range(self.BM_SIZE):
                    btn = Button(
                        text='',
                        background_normal='',
                        background_down='',
                        background_color=BG2,
                        font_size=sp(9),
                        bold=True,
                        color=[1, 1, 1, 1])
                    btn.bind(on_release=lambda b, _x=x, _y=y:
                             self._bm_tap(_x, _y))
                    self._bm_cells[(x, y)] = btn
                    self._bm_grid.add_widget(btn)
            grid_wrap.add_widget(self._bm_grid)
            overlay.add_widget(grid_wrap)

            # Status og bunn-knapper
            self._bm_status = mklbl(
                "Trykk på en token i 'Å plassere' for å begynne.",
                color=DIM, size=10, h=22, wrap=True)
            overlay.add_widget(self._bm_status)

            btm = BoxLayout(size_hint_y=None, height=dp(38),
                            spacing=dp(4))
            btm.add_widget(mkbtn(
                "Til plassering", self._bm_unplace_selected,
                small=True, size_hint_x=0.5))
            btm.add_widget(mkbtn(
                "Tøm kart", self._bm_clear,
                danger=True, small=True, size_hint_x=0.5))
            overlay.add_widget(btm)

            # Legg overlay på FloatLayout-root
            root = self.content
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                self.tool_area.add_widget(overlay)
                self._bm_overlay = overlay
                self._bm_render()
                return
            fl = root.parent

            from kivy.graphics import Color as GCbm, Rectangle as GRbm
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCbm(rgba=[0, 0, 0, 0.75])
                dr = GRbm(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            # Merk: ingen "close on dim-tap" — vi vil ikke risikere
            # at brukeren lukker kartet ved uhell midt i kamp.

            self._bm_dim = dim
            self._bm_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

            self._bm_render()

        def _bm_close_overlay(self):
            """Lukk battlemap-overlayet."""
            ov = getattr(self, '_bm_overlay', None)
            if ov and ov.parent:
                parent = ov.parent
                parent.remove_widget(ov)
                dim = getattr(self, '_bm_dim', None)
                if dim and dim.parent:
                    parent.remove_widget(dim)
            self._bm_overlay = None
            self._bm_dim = None

        def _bm_token_color(self, tp, is_selected=False,
                            is_active_turn=False):
            """Farge for en token basert på type og tilstand."""
            if tp == 'PC':
                base = [0.25, 0.58, 0.32, 1]  # GRN
            elif tp == 'NPC':
                base = [0.78, 0.60, 0.18, 1]  # dempet gull
            else:
                base = [0.60, 0.18, 0.20, 1]  # mørk rød
            if is_selected:
                base = [min(1, c * 1.5) for c in base[:3]] + [1]
            elif is_active_turn:
                base = [min(1, c * 1.2) for c in base[:3]] + [1]
            return base

        def _bm_active_name(self):
            """Hvem har tur akkurat nå (første i init-lista)?"""
            if self._init_list:
                return self._init_list[0].get('name', '')
            return ''

        def _bm_render(self):
            """Tegn opp hele kartet basert på state."""
            # Oppdater aktiv-label
            act = self._bm_active_name()
            if act:
                self._bm_active_lbl.text = f"Tur: {act}"
            else:
                self._bm_active_lbl.text = ""

            # Rebuild unplaced-row
            self._bm_unp_row.clear_widgets()
            placing_label = None
            if self._bm_placing:
                placing_label = self._bm_placing.get('label', '')
            for tok in self._bm_unplaced:
                lbl = tok.get('label', '?')
                is_holding = (lbl == placing_label)
                b = RBtn(
                    text=lbl,
                    bg_color=BTNH if is_holding else (
                        self._bm_token_color(tok.get('type', 'PC'))),
                    color=GOLD if is_holding else [1, 1, 1, 1],
                    font_size=sp(12), bold=True,
                    size_hint_x=None, width=dp(54),
                    size_hint_y=None, height=dp(40))
                b.bind(on_release=lambda x, t=tok:
                       self._bm_hold_for_place(t))
                self._bm_unp_row.add_widget(b)

            n_unp = len(self._bm_unplaced)
            if n_unp == 0 and not self._bm_placing:
                self._bm_unp_label.text = "Alle plassert."
            elif placing_label:
                self._bm_unp_label.text = (
                    f"Holder: {placing_label} — "
                    f"trykk på ledig rute for å plassere.")
            else:
                self._bm_unp_label.text = (
                    f"Å plassere ({n_unp}): trykk for å velge.")

            # Beregn gyldig move-ruter om token er valgt
            valid_moves = set()
            sel = self._bm_selected
            if sel is not None:
                tok = self._bm_tokens.get(sel)
                if tok:
                    mov = tok.get('mov', 8)
                    used = tok.get('used_mov', 0)
                    remaining = max(0, mov - used)
                    sx, sy = sel
                    if remaining > 0:
                        for y in range(self.BM_SIZE):
                            for x in range(self.BM_SIZE):
                                if (x, y) == (sx, sy):
                                    continue
                                dist = max(abs(x - sx), abs(y - sy))
                                if dist <= remaining:
                                    valid_moves.add((x, y))

            # Tegn hver rute
            act_name = act
            for (x, y), btn in self._bm_cells.items():
                tok = self._bm_tokens.get((x, y))
                is_sel = (x, y) == sel
                can_move = (x, y) in valid_moves and tok is None
                can_place = (self._bm_placing is not None
                             and tok is None)
                if tok:
                    btn.text = tok['label']
                    is_active = (tok.get('name') == act_name
                                 and act_name)
                    btn.background_color = self._bm_token_color(
                        tok.get('type', 'PC'),
                        is_selected=is_sel,
                        is_active_turn=is_active)
                    btn.color = [1, 1, 1, 1]
                    btn.font_size = sp(10)
                else:
                    btn.text = ''
                    if can_move:
                        btn.background_color = [0.15, 0.32, 0.18, 1]
                    elif can_place:
                        btn.background_color = [0.25, 0.18, 0.22, 1]
                    else:
                        btn.background_color = BG2

            # Status-tekst
            if self._bm_placing:
                lb = self._bm_placing.get('label', '?')
                nm = self._bm_placing.get('name', '?')
                self._bm_status.text = (
                    f"Plasserer {lb} ({nm}) — trykk en ledig rute.")
            elif sel is not None:
                tok = self._bm_tokens.get(sel)
                if tok:
                    lb = tok.get('label', '?')
                    nm = tok.get('name', '?')
                    mv = tok.get('mov', 8)
                    used = tok.get('used_mov', 0)
                    remaining = max(0, mv - used)
                    hp = tok.get('hp', '')
                    hp_s = f" HP {hp}" if hp else ""
                    if remaining <= 0:
                        self._bm_status.text = (
                            f"Valgt: {lb} ({nm}) — MOV brukt opp "
                            f"({used}/{mv}). Trykk «Neste» for ny runde."
                            f"{hp_s}")
                    else:
                        self._bm_status.text = (
                            f"Valgt: {lb} ({nm}) — MOV {remaining} igjen "
                            f"({used}/{mv} brukt).{hp_s}")
                else:
                    self._bm_status.text = ""
            else:
                self._bm_status.text = (
                    "Trykk på en token for å velge og flytte.")

        def _bm_hold_for_place(self, tok):
            """Velg token for plassering (fra unplaced-raden)."""
            # Toggle: trykk igjen = slipp
            if self._bm_placing and \
               self._bm_placing.get('label') == tok.get('label'):
                self._bm_placing = None
            else:
                self._bm_placing = tok
                self._bm_selected = None
            self._bm_render()

        def _bm_tap(self, x, y):
            """Håndter trykk på en rute."""
            cell = (x, y)
            tok_here = self._bm_tokens.get(cell)

            # Modus 1: plasserer token fra unplaced
            if self._bm_placing:
                if tok_here:
                    # Rute opptatt — ikke flytt, bare gi beskjed
                    self._bm_status.text = (
                        "Ruten er opptatt. Velg en ledig rute.")
                    return
                # Plasser tokenen her
                self._bm_tokens[cell] = self._bm_placing
                self._bm_unplaced = [
                    t for t in self._bm_unplaced
                    if t.get('label') !=
                    self._bm_placing.get('label')]
                self._bm_placing = None
                self._bm_render()
                return

            # Modus 2: ingen aktiv valgt — velg token her
            if self._bm_selected is None:
                if tok_here:
                    self._bm_selected = cell
                    self._bm_render()
                return

            # Modus 3: token valgt fra før
            sel = self._bm_selected
            if cell == sel:
                # Trykk på valgt = dropp valg
                self._bm_selected = None
                self._bm_render()
                return

            if tok_here:
                # Bytt valg til annen token
                self._bm_selected = cell
                self._bm_render()
                return

            # Flytt valgt token hit hvis innenfor gjenværende MOV
            sel_tok = self._bm_tokens.get(sel)
            if not sel_tok:
                self._bm_selected = None
                self._bm_render()
                return
            mov = sel_tok.get('mov', 8)
            used = sel_tok.get('used_mov', 0)
            remaining = max(0, mov - used)
            sx, sy = sel
            dist = max(abs(x - sx), abs(y - sy))
            if remaining <= 0:
                self._bm_status.text = (
                    f"MOV brukt opp ({used}/{mov}).")
                return
            if dist > remaining:
                self._bm_status.text = (
                    f"For langt ({dist} > {remaining} igjen).")
                return
            # Utfør flytt — og tell bruk
            sel_tok['used_mov'] = used + dist
            del self._bm_tokens[sel]
            self._bm_tokens[cell] = sel_tok
            self._bm_selected = cell
            self._bm_render()

        def _bm_unplace_selected(self):
            """Flytt valgt token tilbake til 'Å plassere'."""
            sel = self._bm_selected
            if sel is None:
                return
            tok = self._bm_tokens.get(sel)
            if not tok:
                return
            self._bm_unplaced.append(tok)
            del self._bm_tokens[sel]
            self._bm_selected = None
            self._bm_render()

        def _bm_clear(self):
            """Tøm kartet — alle tokens tilbake til unplaced."""
            for tok in self._bm_tokens.values():
                self._bm_unplaced.append(tok)
            self._bm_tokens = {}
            self._bm_selected = None
            self._bm_placing = None
            self._bm_render()

        def _bm_next_turn(self):
            """Flytt øverste init-entry til bunn + nullstill brukt MOV.
            Autovelg neste deltakers token hvis den er på kartet.
            CoC: hver ny runde får alle full bevegelse igjen."""
            if self._init_list:
                top = self._init_list.pop(0)
                self._init_list.append(top)
            # Nullstill brukt MOV for alle tokens (plasserte + å plassere)
            for tok in self._bm_tokens.values():
                tok['used_mov'] = 0
            for tok in self._bm_unplaced:
                tok['used_mov'] = 0
            # Autovelg tokenen som tilhører neste aktive deltaker
            self._bm_selected = None
            self._bm_placing = None
            next_name = self._bm_active_name()
            if next_name:
                for cell, tok in self._bm_tokens.items():
                    if tok.get('name') == next_name:
                        self._bm_selected = cell
                        break
            self._bm_render()


        # ---------- SCENARIO-TRACKER ----------
        def _scen_init(self):
            """Initialiser scenario-state."""
            if not hasattr(self, '_scen_data'):
                self._scen_data = None
                self._scen_view = 'clues'  # clues | timeline | beats | notes

        def _scen_load(self):
            """Les scenario.json fra app-private storage."""
            path = self.SCENARIO_FILE
            if not os.path.exists(path):
                self._scen_data = None
                return None
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._scen_data = data
                log(f"Scenario lastet: {data.get('title', '?')}")
                return data
            except Exception as e:
                log(f"Scenario-feil: {e}")
                self._scen_data = {'_error': str(e)}
                return None

        def _scen_save(self):
            """Lagre scenario.json til app-private storage."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            try:
                os.makedirs(os.path.dirname(self.SCENARIO_FILE),
                            exist_ok=True)
                with open(self.SCENARIO_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._scen_data, f,
                              ensure_ascii=False, indent=2)
            except Exception as e:
                log(f"Scenario-lagring feilet: {e}")

        def _scen_try_import(self):
            """Prøv å kopiere scenario.json fra Documents-mappen til
            app-private storage. Returner (ok, melding)."""
            # Sjekk All Files Access-status
            has_access = has_all_files_access()
            if not os.path.exists(EXTERNAL_SCENARIO):
                hint = ""
                if has_access is False:
                    hint = ("\n\nHint: appen har ikke 'Tilgang til alle "
                            "filer' ennå. Trykk 'Gi tilgang' for å åpne "
                            "innstillingene og slå det på.")
                return False, (
                    f"Ingen fil funnet i Documents.\n\n"
                    f"Forventet sti:\n{EXTERNAL_SCENARIO}{hint}")
            try:
                with open(EXTERNAL_SCENARIO, 'r',
                          encoding='utf-8') as f:
                    data = json.load(f)
                # Valider at det faktisk er et scenario
                if not isinstance(data, dict):
                    return False, "Filen er ikke et JSON-objekt."
                # Skriv til app-private
                os.makedirs(os.path.dirname(self.SCENARIO_FILE),
                            exist_ok=True)
                with open(self.SCENARIO_FILE, 'w',
                          encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log(f"Scenario importert: {data.get('title', '?')}")
                return True, f"Importert: {data.get('title', '(uten tittel)')}"
            except PermissionError:
                hint = ""
                if has_access is False:
                    hint = ("\n\nLøsning: trykk 'Gi tilgang' nedenfor "
                            "og slå på 'Tillat administrering av "
                            "alle filer' for Eldritch Portal.")
                return False, (
                    "Ingen tilgang til Documents-mappen."
                    + hint)
            except json.JSONDecodeError as e:
                return False, f"Ugyldig JSON i filen:\n{e}"
            except Exception as e:
                return False, f"Feil: {type(e).__name__}: {e}"

        def _mk_scenario(self):
            """Bygg scenario-sub-tab UI."""
            self._scen_init()
            # Les inn fra disk hvis vi ikke har data ennå
            if self._scen_data is None:
                self._scen_load()

            self._tool_action_bar.add_widget(
                mkbtn("Velg fil", self._scen_do_pick_file,
                      accent=True, small=True, size_hint_x=0.3))
            self._tool_action_bar.add_widget(
                mkbtn("Last inn", self._scen_reload,
                      small=True, size_hint_x=0.25))
            self._tool_action_bar.add_widget(
                mkbtn("Nullstill", self._scen_confirm_reset,
                      danger=True, small=True, size_hint_x=0.25))
            title_text = "Scenario"
            if self._scen_data and '_error' not in self._scen_data:
                title_text = self._scen_data.get('title', 'Scenario')
            self._tool_action_bar.add_widget(
                mklbl(title_text, color=GOLD, size=11, bold=True))

            self.tool_area.clear_widgets()

            # Ingen data
            if self._scen_data is None:
                self._scen_show_empty()
                return

            # Feil ved lasting
            if '_error' in self._scen_data:
                self._scen_show_error()
                return

            # Normal visning
            p = BoxLayout(orientation='vertical',
                          spacing=dp(4), padding=dp(4))

            # View-selector
            sel = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
            for key, txt in [('clues', 'Ledetråder'),
                             ('timeline', 'Tidslinje'),
                             ('beats', 'Plot'),
                             ('notes', 'Notater')]:
                active = (key == self._scen_view)
                b = RBtn(
                    text=txt,
                    bg_color=BTNH if active else BTN,
                    color=GOLD if active else TXT,
                    font_size=sp(11), bold=active,
                    size_hint_y=None, height=dp(36))
                b.bind(on_release=lambda x, k=key:
                       self._scen_switch_view(k))
                sel.add_widget(b)
            p.add_widget(sel)

            # System-info
            sys_txt = self._scen_data.get('system', '')
            if sys_txt:
                p.add_widget(mklbl(f"System: {sys_txt}",
                                   color=DIM, size=10, h=16))

            # Innhold
            content = BoxLayout()
            if self._scen_view == 'clues':
                self._scen_build_list(
                    content,
                    self._scen_data.get('clues', []),
                    'where', 'found',
                    "Ingen ledetråder i denne scenarioet.")
            elif self._scen_view == 'timeline':
                self._scen_build_list(
                    content,
                    self._scen_data.get('timeline', []),
                    'when', 'triggered',
                    "Ingen tidslinje-hendelser.")
            elif self._scen_view == 'beats':
                self._scen_build_list(
                    content,
                    self._scen_data.get('beats', []),
                    None, 'done',
                    "Ingen plot-punkter.")
            else:
                self._scen_build_notes(content)
            p.add_widget(content)

            self.tool_area.add_widget(p)

        def _scen_show_empty(self):
            """Vis melding når scenario.json ikke finnes."""
            scroll = ScrollView()
            box = BoxLayout(orientation='vertical',
                            spacing=dp(8), padding=dp(16),
                            size_hint_y=None)
            box.bind(minimum_height=box.setter('height'))

            box.add_widget(mklbl(
                "Ingen scenario lastet.",
                color=GOLD, size=14, bold=True, h=28))

            # PRIMÆR METODE: SAF-filvelger (ingen tillatelser kreves)
            box.add_widget(mksep(8))
            box.add_widget(mklbl(
                "ENKLEST — Velg fil",
                color=GOLD, size=12, bold=True, h=22))
            box.add_widget(mklbl(
                "Trykk 'Velg fil' for å åpne Android sin "
                "filvelger. Bla til scenario.json hvor enn "
                "du har den — Documents, Downloads, Google "
                "Drive, minnekort. Krever ingen ekstra "
                "tillatelser.",
                color=TXT, size=11, wrap=True))
            box.add_widget(mkbtn(
                "Velg fil",
                self._scen_do_pick_file, accent=True,
                size_hint_y=None, height=dp(52)))

            # ALTERNATIV: All files access
            access = has_all_files_access()
            box.add_widget(mksep(10))
            box.add_widget(mklbl(
                "ALTERNATIV — Importer fra Documents",
                color=GOLD, size=12, bold=True, h=22))

            if access is True:
                box.add_widget(mklbl(
                    "Tilgang til alle filer: PÅ",
                    color=GRN, size=11, bold=True, h=20))
                box.add_widget(mklbl(
                    f"Legg scenario.json i:\n{EXTERNAL_SCENARIO}\n\n"
                    "Trykk deretter 'Importer' nedenfor.",
                    color=TXT, size=11, wrap=True))
                box.add_widget(mkbtn(
                    "Importer fra Documents",
                    self._scen_do_import,
                    size_hint_y=None, height=dp(44)))
            elif access is False:
                box.add_widget(mklbl(
                    "Tilgang til alle filer: AV",
                    color=RED, size=11, bold=True, h=20))
                box.add_widget(mklbl(
                    "For å bruke Importer-knappen må du slå "
                    "på 'Tilgang til alle filer' for appen. "
                    "Engangsjobb — men 'Velg fil' over er "
                    "enklere og trenger ikke dette.",
                    color=TXT, size=11, wrap=True))
                box.add_widget(mkbtn(
                    "Gi tilgang (åpner innstillinger)",
                    self._scen_request_access,
                    size_hint_y=None, height=dp(44)))
            else:
                box.add_widget(mklbl(
                    "Kun tilgjengelig på Android 11+.",
                    color=DIM, size=10, wrap=True))

            # MANUELL KOPI: siste fallback
            box.add_widget(mksep(10))
            box.add_widget(mklbl(
                "MANUELT — Kopier hit",
                color=GDIM, size=11, bold=True, h=20))
            box.add_widget(mklbl(
                self.SCENARIO_FILE,
                color=GDIM, size=10, wrap=True))
            box.add_widget(mklbl(
                "Trykk 'Last inn' etterpå.",
                color=DIM, size=10, wrap=True))

            box.add_widget(mksep(8))
            box.add_widget(mkbtn(
                "Last inn på nytt",
                self._scen_reload,
                size_hint_y=None, height=dp(40)))

            scroll.add_widget(box)
            self.tool_area.add_widget(scroll)

        def _scen_request_access(self):
            """Åpne Android-innstillinger for All Files Access."""
            ok = request_all_files_access()
            if not ok:
                self._scen_show_message(
                    "Kunne ikke åpne innstillinger",
                    "Prøv å gå manuelt til:\n"
                    "Innstillinger > Apper > Eldritch Portal > "
                    "Tillatelser > Alle filer",
                    is_error=True)

        def _scen_do_pick_file(self):
            """Åpne Android filvelger og la brukeren velge scenario.json."""
            if platform != 'android':
                self._scen_show_message(
                    "Ikke støttet",
                    "Filvelger er kun tilgjengelig på Android.",
                    is_error=True)
                return
            self._scen_show_message(
                "Åpner filvelger...",
                "Velg en scenario.json-fil. Du kan bla til "
                "Documents, Downloads, Drive, eller hvor som "
                "helst du har fila.",
                is_error=False)
            # Lukk meldingen etter kort tid så filvelgeren vises ren
            Clock.schedule_once(
                lambda dt: self._scen_close_overlay(), 0.8)
            Clock.schedule_once(
                lambda dt: self.file_picker.pick(
                    self._scen_on_file_picked,
                    mime_type='*/*'),
                1.0)

        def _scen_on_file_picked(self, ok, text_or_err):
            """Callback når filvelgeren er ferdig."""
            if not ok:
                if text_or_err != "Avbrutt":
                    self._scen_show_message(
                        "Kunne ikke lese fil",
                        text_or_err, is_error=True)
                return
            # Prøv å parse JSON-innhold
            try:
                data = json.loads(text_or_err)
            except json.JSONDecodeError as e:
                self._scen_show_message(
                    "Ugyldig JSON",
                    f"Fila er ikke gyldig JSON:\n{e}",
                    is_error=True)
                return
            if not isinstance(data, dict):
                self._scen_show_message(
                    "Feil format",
                    "Fila inneholder ikke et JSON-objekt "
                    "(trenger { ... }).",
                    is_error=True)
                return
            # Skriv til app-private sti
            try:
                os.makedirs(os.path.dirname(self.SCENARIO_FILE),
                            exist_ok=True)
                with open(self.SCENARIO_FILE, 'w',
                          encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log(f"Scenario valgt og lagret: "
                    f"{data.get('title', '?')}")
            except Exception as e:
                self._scen_show_message(
                    "Kunne ikke lagre",
                    f"Feil ved lagring:\n{e}",
                    is_error=True)
                return
            # Last og rendre
            self._scen_data = None
            self._scen_load()
            self._tool_render_sub()
            self._scen_show_message(
                "Scenario lastet",
                f"Valgt: {data.get('title', '(uten tittel)')}",
                is_error=False)

        def _scen_do_import(self):
            """Forsøk å importere scenario fra Documents-mappen."""
            ok, msg = self._scen_try_import()
            if ok:
                # Last inn den nyimporterte fila
                self._scen_data = None
                self._scen_load()
                self._tool_render_sub()
                # Vis suksessmelding som overlay
                self._scen_show_message(
                    "Import vellykket", msg, is_error=False)
            else:
                self._scen_show_message(
                    "Import feilet", msg, is_error=True)

        def _scen_show_message(self, title, msg, is_error=False):
            """Vis en melding som overlay."""
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(8),
                padding=dp(16),
                size_hint=(0.88, 0.5),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            overlay.add_widget(mklbl(
                title,
                color=RED if is_error else GOLD,
                size=14, bold=True, h=28))

            scroll = ScrollView()
            overlay.add_widget(scroll)
            body = mklbl(msg, color=TXT, size=11, wrap=True)
            scroll.add_widget(body)

            overlay.add_widget(mkbtn(
                "OK", self._scen_close_overlay,
                accent=True, size_hint_y=None, height=dp(44)))

            root = self.tool_area
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCm, Rectangle as GRm
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCm(rgba=[0, 0, 0, 0.6])
                dr = GRm(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            dim.bind(on_touch_down=lambda w, t:
                     self._scen_close_overlay() or True)

            self._scen_dim = dim
            self._scen_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _scen_show_error(self):
            """Vis feilmelding hvis scenario.json var ugyldig."""
            err = self._scen_data.get('_error', 'Ukjent feil')
            scroll = ScrollView()
            box = BoxLayout(orientation='vertical',
                            spacing=dp(8), padding=dp(16),
                            size_hint_y=None)
            box.bind(minimum_height=box.setter('height'))

            box.add_widget(mklbl(
                "Feil ved lesing av scenario.json",
                color=RED, size=14, bold=True, h=28))
            box.add_widget(mklbl(
                str(err), color=TXT, size=11, wrap=True))

            box.add_widget(mksep(8))
            box.add_widget(mklbl(
                "Mulige årsaker:",
                color=GOLD, size=12, bold=True, h=22))
            box.add_widget(mklbl(
                "• Filen er ikke gyldig JSON "
                "(sjekk på jsonlint.com)\n"
                "• Manglende skriverettigheter\n"
                "• Filen er tom eller korrupt",
                color=TXT, size=11, wrap=True))

            box.add_widget(mksep(6))
            box.add_widget(mklbl(
                "Filsti som brukes:",
                color=GOLD, size=11, bold=True, h=20))
            box.add_widget(mklbl(
                self.SCENARIO_FILE,
                color=GDIM, size=10, wrap=True))

            box.add_widget(mksep(10))
            box.add_widget(mkbtn(
                "Last inn på nytt",
                self._scen_reload, accent=True,
                size_hint_y=None, height=dp(44)))
            box.add_widget(mkbtn(
                "Importer fra Documents",
                self._scen_do_import,
                size_hint_y=None, height=dp(40)))

            scroll.add_widget(box)
            self.tool_area.add_widget(scroll)

        def _scen_reload(self):
            """Last scenario.json på nytt fra disk."""
            self._scen_data = None
            self._scen_load()
            self._tool_render_sub()

        def _scen_switch_view(self, view):
            self._scen_view = view
            self._tool_render_sub()

        def _scen_build_list(self, container, items,
                             subtitle_key, flag_key, empty_msg):
            """Bygg liste med checkbox-rader."""
            if not items:
                container.add_widget(mklbl(
                    empty_msg, color=DIM, size=11, wrap=True))
                return

            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4),
                           size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            for item in items:
                g.add_widget(self._scen_make_row(
                    item, subtitle_key, flag_key))

            scroll.add_widget(g)
            container.add_widget(scroll)

        def _scen_make_row(self, item, subtitle_key, flag_key):
            """Bygg en rad for en clue/timeline/beat."""
            done = bool(item.get(flag_key, False))
            row = RBox(orientation='horizontal',
                       bg_color=BG2 if not done else BTN,
                       size_hint_y=None, height=dp(64),
                       padding=[dp(8), dp(6)], spacing=dp(6),
                       radius=dp(10))

            # Toggle-knapp (venstre)
            tog = RBtn(
                text='[X]' if done else '[ ]',
                bg_color=BTNH if done else INPUT,
                color=GOLD if done else DIM,
                font_size=sp(14), bold=True,
                size_hint_x=None, width=dp(52))
            tog.bind(on_release=lambda b, it=item, fk=flag_key:
                     self._scen_toggle(it, fk))
            row.add_widget(tog)

            # Tekst-område (midten)
            mid = BoxLayout(orientation='vertical', spacing=dp(2))
            title_lb = Label(
                text=item.get('title', '?'),
                font_size=sp(12),
                color=DIM if done else GOLD,
                bold=True,
                halign='left', valign='middle')
            title_lb.bind(size=lambda w, v: setattr(
                w, 'text_size', (v[0], None)))
            mid.add_widget(title_lb)

            if subtitle_key:
                sub_val = item.get(subtitle_key, '')
                if sub_val:
                    sub_lb = Label(
                        text=sub_val,
                        font_size=sp(10),
                        color=DIM,
                        halign='left', valign='middle',
                        size_hint_y=None, height=dp(18))
                    sub_lb.bind(size=lambda w, v: setattr(
                        w, 'text_size', (v[0], None)))
                    mid.add_widget(sub_lb)

            row.add_widget(mid)

            # Info-knapp (høyre)
            desc = item.get('description', '')
            if desc:
                info_btn = RBtn(
                    text='i', bg_color=BTN, color=TXT,
                    font_size=sp(14), bold=True,
                    size_hint_x=None, width=dp(44))
                info_btn.bind(on_release=lambda b,
                              t=item.get('title', '?'),
                              d=desc:
                              self._scen_show_detail(t, d))
                row.add_widget(info_btn)

            return row

        def _scen_toggle(self, item, flag_key):
            """Bytt flagg og lagre."""
            item[flag_key] = not bool(item.get(flag_key, False))
            self._scen_save()
            self._tool_render_sub()

        def _scen_show_detail(self, title, desc):
            """Vis full beskrivelse som overlay."""
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(6),
                padding=dp(12),
                size_hint=(0.9, 0.7),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            hdr = BoxLayout(size_hint_y=None, height=dp(42),
                            spacing=dp(6))
            hdr.add_widget(mkbtn("Lukk", self._scen_close_overlay,
                                 danger=True, small=True,
                                 size_hint_x=0.3))
            hdr.add_widget(mklbl(title, color=GOLD, size=13, bold=True))
            overlay.add_widget(hdr)

            scroll = ScrollView()
            body = mklbl(desc, color=TXT, size=12, wrap=True)
            scroll.add_widget(body)
            overlay.add_widget(scroll)

            # Legg på FloatLayout-roten
            root = self.tool_area
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCs, Rectangle as GRs
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCs(rgba=[0, 0, 0, 0.6])
                dr = GRs(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))
            dim.bind(on_touch_down=lambda w, t:
                     self._scen_close_overlay() or True)

            self._scen_dim = dim
            self._scen_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _scen_close_overlay(self):
            ov = getattr(self, '_scen_overlay', None)
            dm = getattr(self, '_scen_dim', None)
            if ov and ov.parent:
                ov.parent.remove_widget(ov)
            if dm and dm.parent:
                dm.parent.remove_widget(dm)
            self._scen_overlay = None
            self._scen_dim = None

        def _scen_build_notes(self, container):
            """Bygg notat-visning."""
            box = BoxLayout(orientation='vertical', spacing=dp(4))
            notes = self._scen_data.get('notes', '')
            self._scen_notes_input = TextInput(
                text=notes, multiline=True,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD, font_size=sp(12),
                padding=[dp(8), dp(8)])
            box.add_widget(self._scen_notes_input)
            box.add_widget(mkbtn(
                "Lagre notater", self._scen_save_notes,
                accent=True, size_hint_y=None, height=dp(44)))
            container.add_widget(box)

        def _scen_save_notes(self):
            """Lagre notat-tekst."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            self._scen_data['notes'] = self._scen_notes_input.text
            self._scen_save()

        def _scen_confirm_reset(self):
            """Spør om bekreftelse før nullstilling av alle flagg."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(8),
                padding=dp(16),
                size_hint=(0.8, 0.4),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            overlay.add_widget(mklbl(
                "Nullstill fremdrift?",
                color=GOLD, size=14, bold=True, h=28))
            overlay.add_widget(mklbl(
                "Alle avkryssinger i ledetråder, tidslinje og "
                "plot-punkter blir nullstilt. Notater beholdes.",
                color=TXT, size=11, wrap=True))
            btns = BoxLayout(size_hint_y=None, height=dp(44),
                             spacing=dp(6))
            btns.add_widget(mkbtn(
                "Avbryt", self._scen_close_overlay,
                small=True, size_hint_x=0.5))
            btns.add_widget(mkbtn(
                "Nullstill", self._scen_reset_flags,
                danger=True, size_hint_x=0.5))
            overlay.add_widget(btns)

            root = self.tool_area
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                return
            fl = root.parent

            from kivy.graphics import Color as GCr, Rectangle as GRr
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCr(rgba=[0, 0, 0, 0.6])
                dr = GRr(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w, v: setattr(dr, 'pos', w.pos),
                     size=lambda w, v: setattr(dr, 'size', w.size))

            self._scen_dim = dim
            self._scen_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _scen_reset_flags(self):
            """Nullstill alle checkboxer."""
            if not self._scen_data or '_error' in self._scen_data:
                return
            for c in self._scen_data.get('clues', []):
                c['found'] = False
            for t in self._scen_data.get('timeline', []):
                t['triggered'] = False
            for b in self._scen_data.get('beats', []):
                b['done'] = False
            self._scen_save()
            self._scen_close_overlay()
            self._tool_render_sub()

        # ---------- VÅPEN ----------
        def _mk_weapons(self):
            """Hovedvisning for våpentabellen."""
            data = self.weapons_data
            cats = data.get("categories", {})

            if not data.get("weapons"):
                self._tool_action_bar.add_widget(
                    mklbl("Våpen", color=GOLD, size=14, bold=True))
                self.tool_area.clear_widgets()
                msg_box = BoxLayout(orientation='vertical',
                                    spacing=dp(8), padding=dp(20))
                msg_box.add_widget(mklbl(
                    "Ingen våpendata funnet.",
                    color=GOLD, size=14, bold=True, h=28))

                # Vis siste feilmelding hvis vi har en
                err = getattr(self, '_weap_last_error', None)
                if err:
                    msg_box.add_widget(mklbl(
                        "Feil:", color=RED, size=12, bold=True, h=22))
                    msg_box.add_widget(mklbl(
                        err, color=TXT, size=11, wrap=True))
                else:
                    msg_box.add_widget(mklbl(
                        "Legg weapons.json i:\n"
                        "/sdcard/Documents/EldritchPortal/",
                        color=DIM, size=11, wrap=True))

                msg_box.add_widget(mklbl(
                    f"Sti som sjekkes:\n{WEAPONS_FILE}",
                    color=DIM, size=10, wrap=True))

                msg_box.add_widget(mkbtn(
                    "Last inn på nytt",
                    self._weap_reload, accent=True,
                    size_hint_y=None, height=dp(42)))
                msg_box.add_widget(Widget())
                self.tool_area.add_widget(msg_box)
                return

            # Action-bar: søk + epoke + favoritt-toggle
            search_inp = TextInput(
                text=self._weap_search,
                hint_text='Søk…',
                font_size=sp(12), multiline=False,
                background_color=INPUT, foreground_color=TXT,
                cursor_color=GOLD,
                size_hint_x=0.45,
                padding=[dp(8), dp(8)])
            search_inp.bind(text=self._weap_on_search)
            self._tool_action_bar.add_widget(search_inp)

            era_sp = Spinner(
                text=self._weap_era_label(self._weap_era),
                values=['Alle epoker', '1920-tallet',
                        'Moderne', 'Gaslight'],
                size_hint_x=0.35,
                background_color=BTN, color=TXT,
                font_size=sp(11))
            era_sp.bind(text=self._weap_era_change)
            self._tool_action_bar.add_widget(era_sp)

            fav_tog = RToggle(
                text='*',
                state='down' if self._weap_fav_only else 'normal',
                bg_color=BTNH if self._weap_fav_only else BTN,
                color=GOLD if self._weap_fav_only else DIM,
                font_size=sp(14), bold=True,
                size_hint_x=0.2)
            fav_tog.bind(on_release=self._weap_toggle_fav_filter)
            self._tool_action_bar.add_widget(fav_tog)

            # Hovedområde
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical',
                          spacing=dp(4), padding=[dp(4), dp(4)])

            # Kategori-faner (horisontalt scroll)
            cat_scroll = ScrollView(size_hint_y=None, height=dp(40),
                                    do_scroll_y=False)
            cat_row = BoxLayout(size_hint_x=None, spacing=dp(4),
                                padding=[dp(2), 0])
            cat_row.bind(minimum_width=cat_row.setter('width'))

            cat_items = [('all', 'Alle')]
            cat_items += [(k, v) for k, v in cats.items()]
            for key, lbl in cat_items:
                active = (key == self._weap_cat)
                b = RBtn(
                    text=lbl,
                    bg_color=BTNH if active else BTN,
                    color=GOLD if active else TXT,
                    font_size=sp(11), bold=active,
                    size_hint_x=None, width=dp(90),
                    size_hint_y=None, height=dp(36))
                b.bind(on_release=lambda x, k=key:
                       self._weap_cat_switch(k))
                cat_row.add_widget(b)

            cat_scroll.add_widget(cat_row)
            p.add_widget(cat_scroll)

            # Våpenliste
            scroll = ScrollView()
            self._weap_list_grid = GridLayout(
                cols=1, spacing=dp(4),
                padding=[dp(2), dp(4)],
                size_hint_y=None)
            self._weap_list_grid.bind(
                minimum_height=self._weap_list_grid.setter('height'))
            scroll.add_widget(self._weap_list_grid)
            p.add_widget(scroll)

            self.tool_area.add_widget(p)
            self._weap_render_list()

        def _weap_reload(self):
            """Les inn weapons.json på nytt."""
            self._weap_do_load()
            self._tool_render_sub()

        def _weap_era_label(self, key):
            return {'all': 'Alle epoker',
                    '1920s': '1920-tallet',
                    'modern': 'Moderne',
                    'gaslight': 'Gaslight'}.get(key, 'Alle epoker')

        def _weap_era_change(self, inst, val):
            rev = {'Alle epoker': 'all',
                   '1920-tallet': '1920s',
                   'Moderne': 'modern',
                   'Gaslight': 'gaslight'}
            self._weap_era = rev.get(val, 'all')
            self._weap_render_list()

        def _weap_on_search(self, inst, val):
            self._weap_search = val.strip().lower()
            self._weap_render_list()

        def _weap_cat_switch(self, cat):
            self._weap_cat = cat
            # Rebuild fordi kategori-knapper må re-styles
            self._tool_render_sub()

        def _weap_toggle_fav_filter(self, inst):
            self._weap_fav_only = (inst.state == 'down')
            inst.bg_color = BTNH if self._weap_fav_only else BTN
            inst.color = GOLD if self._weap_fav_only else DIM
            self._weap_render_list()

        def _weap_filter(self):
            """Returner filtrert våpenliste."""
            weapons = self.weapons_data.get("weapons", [])
            out = []
            for w in weapons:
                # Kategori
                if self._weap_cat != 'all':
                    if w.get('category') != self._weap_cat:
                        continue
                # Epoke
                if self._weap_era != 'all':
                    eras = w.get('era', [])
                    if 'all' not in eras and self._weap_era not in eras:
                        continue
                # Favoritt
                if self._weap_fav_only:
                    if w.get('id') not in self.weap_favorites:
                        continue
                # Søk
                if self._weap_search:
                    s = self._weap_search
                    hay = (w.get('name', '') + ' ' +
                           w.get('description', '') + ' ' +
                           ' '.join(w.get('tags', []))).lower()
                    if s not in hay:
                        continue
                out.append(w)
            return out

        def _weap_render_list(self):
            """Bygg våpen-rad-listen basert på filter."""
            if not hasattr(self, '_weap_list_grid'):
                return
            self._weap_list_grid.clear_widgets()
            subs = self.weapons_data.get("subcategories", {})
            filtered = self._weap_filter()

            if not filtered:
                self._weap_list_grid.add_widget(mklbl(
                    "Ingen treff med gjeldende filter.",
                    color=DIM, size=12, h=40))
                return

            for w in filtered:
                self._weap_list_grid.add_widget(
                    self._weap_make_row(w, subs))

        def _weap_make_row(self, w, subs):
            """Bygg en kompakt våpen-rad (78dp høy, klikkbar)."""
            wid = w.get('id', '')
            is_fav = wid in self.weap_favorites

            row = RBox(orientation='horizontal',
                       bg_color=BG2,
                       size_hint_y=None, height=dp(78),
                       padding=[dp(8), dp(6)], spacing=dp(6),
                       radius=dp(10))

            # Venstre: info
            left = BoxLayout(orientation='vertical', spacing=dp(2))

            # Linje 1: navn + kategori-chip
            l1 = BoxLayout(size_hint_y=None, height=dp(22),
                           spacing=dp(6))
            name_lb = Label(
                text=w.get('name', '?'),
                font_size=sp(13), color=GOLD, bold=True,
                halign='left', valign='middle')
            name_lb.bind(size=lambda w_, v: setattr(
                w_, 'text_size', v))
            l1.add_widget(name_lb)

            sub_key = w.get('subcategory', '')
            sub_lbl = subs.get(sub_key, sub_key)
            if sub_lbl:
                chip = Label(
                    text=sub_lbl,
                    font_size=sp(9), color=DIM, bold=True,
                    size_hint_x=None, width=dp(80),
                    halign='right', valign='middle')
                chip.bind(size=lambda w_, v: setattr(
                    w_, 'text_size', v))
                l1.add_widget(chip)
            left.add_widget(l1)

            # Linje 2: ferdighet
            skill_lb = Label(
                text=w.get('skill', ''),
                font_size=sp(10), color=DIM,
                size_hint_y=None, height=dp(18),
                halign='left', valign='middle')
            skill_lb.bind(size=lambda w_, v: setattr(
                w_, 'text_size', v))
            left.add_widget(skill_lb)

            # Linje 3: skade | rekkevidde | magasin | feiling
            parts = []
            dmg = w.get('damage', '')
            if dmg:
                parts.append(f"Sk: {dmg}")
            rng = w.get('range', '')
            if rng and rng != 'berøring':
                parts.append(f"R: {rng}")
            ammo = w.get('ammo')
            if ammo:
                parts.append(f"Mag: {ammo}")
            malf = w.get('malfunction')
            if malf:
                parts.append(f"F: {malf}")

            stats_lb = Label(
                text='   '.join(parts),
                font_size=sp(10), color=TXT,
                size_hint_y=None, height=dp(20),
                halign='left', valign='middle')
            stats_lb.bind(size=lambda w_, v: setattr(
                w_, 'text_size', v))
            left.add_widget(stats_lb)

            row.add_widget(left)

            # Høyre: favoritt-knapp
            fav_btn = RBtn(
                text='*' if is_fav else 'o',
                bg_color=BTN,
                color=GOLD if is_fav else DIM,
                font_size=sp(18), bold=True,
                size_hint_x=None, width=dp(44),
                size_hint_y=None, height=dp(44),
                pos_hint={'center_y': 0.5})
            fav_btn.bind(on_release=lambda b, _id=wid:
                         self._weap_toggle_fav(_id))
            row.add_widget(fav_btn)

            # Hele raden (unntatt fav-knapp) klikkbar = åpne detalj
            def _on_touch(widget, touch, weap=w):
                if not widget.collide_point(*touch.pos):
                    return False
                # Ikke hvis fav-knappen er truffet
                if fav_btn.collide_point(*touch.pos):
                    return False
                self._weap_show_detail(weap)
                return True

            row.bind(on_touch_down=_on_touch)
            return row

        def _weap_toggle_fav(self, wid):
            """Bytt favoritt-status og lagre."""
            if wid in self.weap_favorites:
                self.weap_favorites.discard(wid)
            else:
                self.weap_favorites.add(wid)
            save_json(self.WEAPONS_FAV_FILE, list(self.weap_favorites))
            self._weap_render_list()

        def _weap_show_detail(self, w):
            """Vis detalj-overlay for ett våpen."""
            self._weap_close_overlay()
            labels = self.weapons_data.get("field_labels", {})
            subs = self.weapons_data.get("subcategories", {})
            cats = self.weapons_data.get("categories", {})

            overlay = RBox(
                bg_color=BG, radius=dp(16),
                orientation='vertical', spacing=dp(4),
                padding=dp(10),
                size_hint=(0.94, 0.88),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})

            # Header
            hdr = BoxLayout(size_hint_y=None, height=dp(42),
                            spacing=dp(6))
            hdr.add_widget(mkbtn("Lukk", self._weap_close_overlay,
                                 danger=True, small=True,
                                 size_hint_x=0.3))
            hdr.add_widget(mklbl(w.get('name', '?'),
                                 color=GOLD, size=14, bold=True))

            wid = w.get('id', '')
            is_fav = wid in self.weap_favorites
            fav_btn = mkbtn('*' if is_fav else 'o',
                            lambda: (self._weap_toggle_fav(wid),
                                     self._weap_show_detail(w)),
                            accent=is_fav, small=True,
                            size_hint_x=None)
            fav_btn.width = dp(50)
            hdr.add_widget(fav_btn)
            overlay.add_widget(hdr)

            # Breadcrumb
            cat_lbl = cats.get(w.get('category', ''), '')
            sub_lbl = subs.get(w.get('subcategory', ''), '')
            crumb = f"{cat_lbl}  >  {sub_lbl}" if sub_lbl else cat_lbl
            overlay.add_widget(mklbl(crumb, color=DIM, size=10, h=18))

            # Innhold i scroll
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(3),
                           padding=[dp(4), dp(4)], size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))

            # Nøkkel-stats i rutenett
            g.add_widget(mksep(4))
            stats_box = GridLayout(cols=2, spacing=dp(4),
                                   size_hint_y=None, height=dp(180))

            def _stat(lbl_text, val):
                if val is None or val == '':
                    return
                framed = FramedBox(orientation='vertical',
                                   padding=dp(4), spacing=dp(2))
                framed.add_widget(Label(
                    text=lbl_text, font_size=sp(10),
                    color=GOLD, bold=True,
                    size_hint_y=None, height=dp(16)))
                framed.add_widget(Label(
                    text=str(val), font_size=sp(12),
                    color=TXT, bold=True))
                stats_box.add_widget(framed)

            _stat(labels.get('skill', 'Ferdighet'),
                  w.get('skill', '—'))
            _stat(labels.get('damage', 'Skade'),
                  w.get('damage', '—'))

            db = w.get('uses_db')
            if db is True:
                db_text = 'Ja'
            elif db == 'half':
                db_text = 'Halv'
            else:
                db_text = 'Nei'
            _stat(labels.get('uses_db', 'Bruker DB'), db_text)

            _stat(labels.get('can_impale', 'Kan spidde'),
                  'Ja' if w.get('can_impale') else 'Nei')
            _stat(labels.get('range', 'Rekkevidde'),
                  w.get('range', '—'))
            _stat(labels.get('attacks', 'Angrep / runde'),
                  w.get('attacks', '—'))
            _stat(labels.get('ammo', 'Magasin'),
                  w.get('ammo', '—'))
            _stat(labels.get('malfunction', 'Feiling'),
                  w.get('malfunction', '—'))

            g.add_widget(stats_box)

            # Epoke og pris
            g.add_widget(mksep(6))
            meta = []
            eras = w.get('era', [])
            if eras:
                era_map = {'all': 'Alle', 'gaslight': 'Gaslight',
                           '1920s': '1920-tallet',
                           'modern': 'Moderne'}
                era_txt = ', '.join(era_map.get(e, e) for e in eras)
                meta.append(f"Epoke: {era_txt}")
            cost = w.get('cost_1920s')
            if cost:
                meta.append(f"Pris (1920): {cost}")
            avail = w.get('availability')
            if avail:
                meta.append(f"Tilgjengelighet: {avail}")
            if meta:
                g.add_widget(mklbl(
                    '   •   '.join(meta),
                    color=DIM, size=11, wrap=True))

            # Beskrivelse
            desc = w.get('description', '')
            if desc:
                g.add_widget(mksep(6))
                g.add_widget(mklbl(
                    labels.get('description', 'Beskrivelse'),
                    color=GOLD, size=12, bold=True, h=22))
                g.add_widget(mklbl(desc, color=TXT, size=12, wrap=True))

            # Pulp-notater
            pulp = w.get('pulp_notes', '')
            if pulp:
                g.add_widget(mksep(6))
                g.add_widget(mklbl(
                    labels.get('pulp_notes', 'Pulp-notater'),
                    color=GOLD, size=12, bold=True, h=22))
                g.add_widget(mklbl(pulp, color=TXT, size=12, wrap=True))

            # Tagger
            tags = w.get('tags', [])
            if tags:
                g.add_widget(mksep(6))
                g.add_widget(mklbl(
                    'Tagger:  ' + ', '.join(tags),
                    color=DIM, size=10, wrap=True))

            g.add_widget(mksep(30))
            scroll.add_widget(g)
            overlay.add_widget(scroll)

            # Legg overlay på FloatLayout-root (samme mønster som rules)
            root = self.content
            while root.parent and not isinstance(root.parent, FloatLayout):
                root = root.parent
            if not isinstance(root.parent, FloatLayout):
                # Fallback: legg direkte i tool_area
                self.tool_area.add_widget(overlay)
                self._weap_overlay = overlay
                return
            fl = root.parent

            from kivy.graphics import Color as GCd, Rectangle as GRd
            dim = Widget(size_hint=(1, 1))
            with dim.canvas:
                GCd(rgba=[0, 0, 0, 0.6])
                dr = GRd(pos=dim.pos, size=dim.size)
            dim.bind(pos=lambda w_, v: setattr(dr, 'pos', w_.pos),
                     size=lambda w_, v: setattr(dr, 'size', w_.size))
            dim.bind(on_touch_down=lambda w_, t:
                     self._weap_close_overlay() or True)

            self._weap_dim = dim
            self._weap_overlay = overlay
            fl.add_widget(dim)
            fl.add_widget(overlay)

        def _weap_close_overlay(self):
            """Lukk våpen-detalj-overlay."""
            if self._weap_overlay and self._weap_overlay.parent:
                parent = self._weap_overlay.parent
                parent.remove_widget(self._weap_overlay)
                if self._weap_dim and self._weap_dim.parent:
                    parent.remove_widget(self._weap_dim)
            self._weap_overlay = None
            self._weap_dim = None


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
