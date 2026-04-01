import os, sys, traceback, socket, threading, json, random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
def log(msg):
    with open(LOG, "a") as f: f.write(msg + "\n")
log("=== APP START (V2 - Optimized) ===")

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.button import Button
    from kivy.uix.togglebutton import ToggleButton
    from kivy.uix.label import Label
    from kivy.uix.image import Image, AsyncImage
    from kivy.uix.slider import Slider
    from kivy.uix.spinner import Spinner
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.metrics import dp, sp
    from kivy.animation import Animation
    from kivy.graphics import Color, RoundedRectangle
    from kivy.core.text import LabelBase
    log("Kivy imports OK")

    # --- KONFIGURASJON OG FARGER ---
    BASE_DIR = "/sdcard/Documents/EldritchPortal"
    FONT_DIR = os.path.join(BASE_DIR, "fonts")
    os.makedirs(FONT_DIR, exist_ok=True)
    
    # Registrer den tilpassede fonten
    FONT_PATH = os.path.join(FONT_DIR, "main.ttf")
    LabelBase.register(name="MainFont", fn_regular=FONT_PATH)

    BG      = [0.04, 0.04, 0.06, 1]
    BG_CARD = [0.08, 0.08, 0.12, 1]  # Lysere for karakterkort
    BTN     = [0.12, 0.13, 0.18, 1]
    BTNH    = [0.18, 0.20, 0.28, 1]
    GOLD    = [0.90, 0.72, 0.20, 1]
    TXT     = [0.85, 0.82, 0.75, 1]
    DIM     = [0.45, 0.43, 0.40, 1]
    RED     = [0.65, 0.15, 0.15, 1]
    GRN     = [0.20, 0.55, 0.30, 1]
    
    IMG_EXT = ('.png','.jpg','.jpeg','.webp')
    HTTP_PORT = 8089

    # [Resten av AMBIENT_SOUNDS, SKILLS etc. er uendret fra din original]
    AMBIENT_SOUNDS = [
        {"name":"--- Natur ---"},
        {"name":"Regn og torden","url":"https://archive.org/download/RainSound13/Gentle%20Rain%20and%20Thunder.mp3"},
        {"name":"Havboelger","url":"https://archive.org/download/naturesounds-soundtheraphy/Birds%20With%20Ocean%20Waves%20on%20the%20Beach.mp3"},
        {"name":"--- Horror ---"},
        {"name":"Skummel atmosfaere","url":"https://archive.org/download/creepy-music-sounds/Creepy%20music%20%26%20sounds.mp3"},
    ]
    CHAR_INFO = [("name","Navn"), ("type","Type"), ("occ","Yrke"), ("archetype","Arketype")]
    CHAR_STATS = [("str","STR"), ("con","CON"), ("siz","SIZ"), ("dex","DEX"), ("int","INT"), ("pow","POW"), ("app","APP"), ("edu","EDU")]
    CHAR_DERIVED = [("hp","HP"), ("mp","MP"), ("san","SAN"), ("luck","Luck")]
    CHAR_TEXT = [("backstory","Bakgrunn"), ("notes","Notater")]

    # --- HJELPEFUNKSJONER ---
    def update_rect(instance, value):
        """Oppdaterer canvas-bakgrunnen når størrelse/posisjon endres"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(rgba=instance.background_color)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(8)])

    def mkbtn(text, cb=None, accent=False, danger=False, small=False, **kw):
        c = GOLD if accent else (RED if danger else TXT)
        b = Button(text=text, background_normal='', background_color=BTN,
                   color=c, bold=True, font_size=sp(11) if small else sp(13),
                   font_name="MainFont", **kw)
        b.bind(pos=update_rect, size=update_rect)
        if cb: b.bind(on_release=lambda x: cb())
        return b

    def mklbl(text, color=TXT, size=12, bold=False, h=None, wrap=False):
        kw = {'text':text, 'font_size':sp(size), 'color':color, 'bold':bold, 'font_name':"MainFont"}
        if h: kw['size_hint_y'] = None; kw['height'] = dp(h)
        l = Label(**kw)
        if wrap:
            l.halign = 'left'; l.text_size = (Window.width - dp(32), None)
            l.size_hint_y = None; l.bind(texture_size=l.setter('size'))
        return l

    # [MediaServer, CastMgr, Player-klasser forblir de samme for stabilitet]
    # ... (Hoppet over for korthets skyld, men behold dine originale her) ...
    # (Legger inn koden din for Players/Server/Cast her i din faktiske fil)

    class EldritchApp(App):
        def build(self):
            Window.clearcolor = BG
            self.title = "Eldritch Portal"
            self.auto_cast = True
            self.cur_folder = os.path.join(BASE_DIR, "images")
            self.chars = [] # Lastes i _init
            
            # Dummy-initialisering av spillere (Bruk dine faktiske klasser her)
            self.player = None 
            self.streamer = None
            self.cast = None
            self.server = None

            root = BoxLayout(orientation='vertical')
            root.add_widget(Widget(size_hint_y=None, height=dp(35))) # Notch spacer

            # Tabs
            self.tab_holder = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4), padding=[dp(4),0])
            for key, txt in [('img','Bilder'),('mus','Musikk'),('amb','Ambient'),('tool','Karakterer'),('cast','Cast')]:
                btn = ToggleButton(text=txt, group='tabs', state='down' if key=='img' else 'normal',
                                  background_normal='', background_down='', font_name="MainFont")
                btn.bind(on_release=lambda x, k=key: self._tab(k))
                self.tab_holder.add_widget(btn)
            root.add_widget(self.tab_holder)

            # Content Area med Fade-effekt
            self.content = BoxLayout(padding=dp(8))
            root.add_widget(self.content)

            # Mini-status
            self.status = Label(text="System klar", font_size=sp(10), color=DIM, size_hint_y=None, height=dp(20), font_name="MainFont")
            root.add_widget(self.status)

            Clock.schedule_once(lambda dt: self._tab('img'), 0.1)
            return root

        def _tab(self, k):
            """Bytter fane med en lett fade-animasjon for å unngå krasj ved tunge UI-skift"""
            anim = Animation(opacity=0, duration=0.15)
            def _change(*args):
                self.content.clear_widgets()
                if k == 'img': self.content.add_widget(self._mk_img())
                elif k == 'tool': self.content.add_widget(self._mk_tool())
                # ... legg til de andre fanene her ...
                Animation(opacity=1, duration=0.2).start(self.content)
            
            anim.bind(on_complete=_change)
            anim.start(self.content)

        # --- BILDE-MODUL (Bruker AsyncImage) ---
        def _mk_img(self):
            p = BoxLayout(orientation='vertical', spacing=dp(8))
            self.preview = AsyncImage(size_hint_y=0.4, allow_stretch=True)
            p.add_widget(self.preview)
            
            scroll = ScrollView()
            grid = GridLayout(cols=3, spacing=dp(6), size_hint_y=None)
            grid.bind(minimum_height=grid.setter('height'))
            
            # Effektiv lasting av thumbnails
            if os.path.exists(self.cur_folder):
                for fn in os.listdir(self.cur_folder):
                    if fn.lower().endswith(IMG_EXT):
                        full_path = os.path.join(self.cur_folder, fn)
                        # AsyncImage laster bilder i bakgrunnen - ingen UI-freeze!
                        btn = AsyncImage(source=full_path, size_hint_y=None, height=dp(100))
                        btn.bind(on_touch_down=lambda w, t, path=full_path: self._sel_img(path) if w.collide_point(*t.pos) else None)
                        grid.add_widget(btn)
            
            scroll.add_widget(grid)
            p.add_widget(scroll)
            return p

        def _sel_img(self, path):
            self.preview.source = path

        # --- KARAKTER-MODUL (Kort-design) ---
        def _mk_tool(self):
            p = BoxLayout(orientation='vertical', spacing=dp(8))
            header = BoxLayout(size_hint_y=None, height=dp(40))
            header.add_widget(mklbl("ETTERFORSKERE", size=16, bold=True, color=GOLD))
            header.add_widget(mkbtn("+ NY", cb=None, accent=True, size_hint_x=0.3))
            p.add_widget(header)

            scroll = ScrollView()
            grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, padding=[0, dp(10)])
            grid.bind(minimum_height=grid.setter('height'))

            # Eksempel på "Kort"
            for i in range(5):
                card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(12))
                card.background_color = BG_CARD
                card.bind(pos=update_rect, size=update_rect) # Gir avrundede hjørner
                
                card.add_widget(mklbl("Karakternavn Her", bold=True, size=14, color=GOLD))
                card.add_widget(mklbl("Yrke: Antikvar  |  HP: 12", size=11, color=TXT))
                
                grid.add_widget(card)

            scroll.add_widget(grid)
            p.add_widget(scroll)
            return p

    if __name__ == '__main__':
        EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())