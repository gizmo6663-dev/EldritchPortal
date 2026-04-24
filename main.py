import os, sys, traceback, socket, threading, json, random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from kivy.clock import Clock

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
LOG_HISTORY_LIMIT = 3
os.makedirs(os.path.dirname(LOG), exist_ok=True)

# Rotate crash logs on startup so each launch gets a fresh log while
# keeping a small history for debugging.
try:
    for i in range(LOG_HISTORY_LIMIT, 0, -1):
        src = LOG if i == 1 else f"{LOG}.{i - 1}"
        dst = f"{LOG}.{i}"
        if os.path.exists(src):
            try:
                if os.path.exists(dst):
                    os.remove(dst)
            except Exception:
                pass
            os.replace(src, dst)
except Exception:
    pass

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
