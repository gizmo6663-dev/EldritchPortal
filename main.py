import os, sys, traceback, socket, threading, json, random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")
log("=== APP START ===")

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
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
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.metrics import dp, sp
    from kivy.animation import Animation
    from kivy.graphics import Color, RoundedRectangle
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

    BASE_DIR = "/sdcard/Documents/EldritchPortal"
    IMG_DIR = os.path.join(BASE_DIR, "images")
    MUSIC_DIR = os.path.join(BASE_DIR, "music")
    CHAR_FILE = os.path.join(BASE_DIR, "characters.json")
    for d in [IMG_DIR, MUSIC_DIR]:
        os.makedirs(d, exist_ok=True)

    # Farger
    BG   = [0.05, 0.05, 0.07, 1]
    BG2  = [0.08, 0.08, 0.11, 1]
    BTN  = [0.13, 0.14, 0.18, 1]
    BTNH = [0.18, 0.19, 0.24, 1]
    GOLD = [0.90, 0.72, 0.20, 1]
    GDIM = [0.50, 0.40, 0.14, 1]
    TXT  = [0.78, 0.75, 0.68, 1]
    DIM  = [0.42, 0.40, 0.36, 1]
    RED  = [0.60, 0.18, 0.18, 1]
    GRN  = [0.18, 0.50, 0.28, 1]
    BLUE = [0.20, 0.35, 0.55, 1]
    IMG_EXT = ('.png','.jpg','.jpeg','.webp')
    HTTP_PORT = 8089

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

    def mkbtn(text, cb=None, accent=False, danger=False, small=False, **kw):
    c = GOLD if accent else (RED if danger else TXT)
    kw['font_size'] = sp(11) if small else sp(13)
    kw['background_color'] = BTN
    kw['color'] = c
    kw['bold'] = True
    kw['background_normal'] = ''
    b = Button(text=text, **kw)
    # Tegn avrundet bakgrunn med én gang
    b.bind(pos=update_rect, size=update_rect)
    # Tving første tegning ved å kalle update_rect manuelt
    Clock.schedule_once(lambda dt: update_rect(b, None), 0)
    if cb:
        b.bind(on_release=lambda x: cb())
    return b

    def update_rect(instance, value):
    instance.canvas.before.clear()
    with instance.canvas.before:
        Color(rgba=instance.background_color)
        RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(8)])
        
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
                        try:
                            self.mp.release()
                        except:
                            pass
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
                try:
                    self.snd.stop()
                except:
                    pass
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
            log("build() called")
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

            root = BoxLayout(orientation='vertical', spacing=0)
            root.add_widget(Widget(size_hint_y=None, height=dp(30)))

            tabs = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(2), padding=[dp(4),0])
            with tabs.canvas.before:
                Color(rgba=BTN)
                RoundedRectangle(pos=tabs.pos, size=tabs.size, radius=[dp(8)])
            self._tabs = {}
            for key, txt in [('img','Bilder'),('mus','Musikk'),('amb','Ambient'),('tool','Karakterer'),('cast','Cast')]:
                b = ToggleButton(text=txt, group='tabs', state='down' if key=='img' else 'normal',
                                 background_normal='', background_down='', font_size=sp(12), bold=True)
                b.bind(state=self._tab_color)
                b.bind(on_release=lambda x, k=key: self._tab(k))
                self._tab_color(b, b.state)
                tabs.add_widget(b)
                self._tabs[key] = b
            root.add_widget(tabs)

            self.content = BoxLayout()
            with self.content.canvas.before:
                Color(rgba=BG2)
                RoundedRectangle(pos=self.content.pos, size=self.content.size, radius=[dp(8)])
            root.add_widget(self.content)

            mp = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4), padding=[dp(6),dp(2)])
            mp.add_widget(Widget(size_hint_x=None, width=dp(2)))
            self.mp_lbl = Label(text="Ingen musikk", font_size=sp(10), color=DIM, size_hint_x=0.45, halign='left')
            self.mp_lbl.bind(size=self.mp_lbl.setter('text_size'))
            mp.add_widget(self.mp_lbl)
            for t, cb in [("<<", self.prev_track), (">>", self.next_track)]:
                mp.add_widget(mkbtn(t, cb, small=True, size_hint_x=None, width=dp(36)))
            self.mp_btn = mkbtn("Play", self.toggle_play, accent=True, small=True, size_hint_x=None, width=dp(50))
            mp.add_widget(self.mp_btn)
            root.add_widget(mp)

            self.status = Label(text="", font_size=sp(9), color=DIM, size_hint_y=None, height=dp(16))
            root.add_widget(self.status)

            self._tab('img')
            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init(), 3)
            return root

        def _tab_color(self, btn, state):
            if state == 'down':
                btn.background_color = BTNH
                btn.color = GOLD
            else:
                btn.background_color = BTN
                btn.color = DIM

        def _init(self):
            self.server.start()
            self._load_imgs()
            self._load_tracks()
            self.status.text = f"IP: {MediaServer.ip()}  |  Cast: {'Ja' if CAST_AVAILABLE else 'Nei'}"

        def _tab(self, k):
            self.content.clear_widgets()
            if k == 'img':
                self.content.add_widget(self._mk_img())
            elif k == 'mus':
                self.content.add_widget(self._mk_mus())
            elif k == 'amb':
                self.content.add_widget(self._mk_amb())
            elif k == 'tool':
                self.content.add_widget(self._mk_tool())
            elif k == 'cast':
                self.content.add_widget(self._mk_cast())

        # ---------- BILDER ----------
        def _mk_img(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4))
            self.preview = Image(size_hint_y=0.4, allow_stretch=True, keep_ratio=True)
            if self.sel_img:
                self.preview.source = self.sel_img
            p.add_widget(self.preview)
            p.add_widget(Label(text="ELDRITCH PORTAL", font_size=sp(15), color=GDIM, bold=True,
                               size_hint_y=None, height=dp(24)))
            self.img_lbl = Label(text="", font_size=sp(11), color=DIM, size_hint_y=None, height=dp(18))
            p.add_widget(self.img_lbl)
            nav = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4), padding=[dp(4),0])
            self.path_lbl = Label(text="", font_size=sp(9), color=DIM, size_hint_x=0.35)
            nav.add_widget(self.path_lbl)
            nav.add_widget(mkbtn("Opp", self.folder_up, small=True, size_hint_x=0.2))
            self.ac_btn = mkbtn("AC:PA", self._toggle_ac, accent=True, small=True, size_hint_x=0.25)
            nav.add_widget(self.ac_btn)
            nav.add_widget(mkbtn("Oppdater", self._load_imgs, small=True, size_hint_x=0.2))
            p.add_widget(nav)
            scroll = ScrollView(size_hint_y=0.4)
            self.img_grid = GridLayout(cols=3, spacing=dp(4), padding=dp(4), size_hint_y=None)
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
            if hasattr(self, 'path_lbl'):
                self.path_lbl.text = f"/{rel}" if rel else "/"
            try:
                if not os.path.exists(f):
                    return
                items = sorted(os.listdir(f))
                dirs = [d for d in items if os.path.isdir(os.path.join(f, d)) and not d.startswith('.')]
                imgs = [x for x in items if x.lower().endswith(IMG_EXT)]
                if hasattr(self, 'img_lbl'):
                    self.img_lbl.text = f"{len(dirs)} mapper, {len(imgs)} bilder"
                for d in dirs:
                    self.img_grid.add_widget(mkbtn(f"[{d}]", lambda dn=d: self._enter(dn), accent=True, small=True, size_hint_y=None, height=dp(70)))
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
            if hasattr(self, 'img_lbl'):
                self.img_lbl.text = os.path.basename(path)
                self.img_lbl.color = GOLD
            if not hasattr(self, 'preview'):
                return
            Animation.cancel_all(self.preview, 'opacity')
            fade_out = Animation(opacity=0, duration=0.3)
            def _swap(*a):
                self.preview.source = path
                Animation(opacity=1, duration=0.4).start(self.preview)
                if self.auto_cast and self.cast.cc and self.cast.mc:
                    if hasattr(self, 'img_lbl'):
                        self.img_lbl.text = "Caster..."
                    self.cast.cast_img(self.server.url(path), cb=lambda ok: self._cdone(ok))
            fade_out.bind(on_complete=_swap)
            fade_out.start(self.preview)

        def _cdone(self, ok):
            if hasattr(self, 'img_lbl'):
                self.img_lbl.text = "Castet!" if ok else "Feilet"

        def _toggle_ac(self):
            self.auto_cast = not self.auto_cast
            if hasattr(self, 'ac_btn'):
                self.ac_btn.text = f"AC:{'PA' if self.auto_cast else 'AV'}"

        # ---------- MUSIKK ----------
        def _mk_mus(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4))
            self.trk_lbl = Label(text="Velg et spor", font_size=sp(14), color=DIM, size_hint_y=None, height=dp(32), bold=True)
            p.add_widget(self.trk_lbl)
            ctrl = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
            ctrl.add_widget(mkbtn("<<", self.prev_track, small=True))
            ctrl.add_widget(mkbtn("Play", self.toggle_play, accent=True))
            ctrl.add_widget(mkbtn(">>", self.next_track, small=True))
            ctrl.add_widget(mkbtn("Stopp", self.stop_music, danger=True, small=True))
            p.add_widget(ctrl)
            vr = BoxLayout(size_hint_y=None, height=dp(28), padding=[dp(8),0])
            vr.add_widget(Label(text="Vol", color=DIM, size_hint_x=0.08, font_size=sp(10)))
            sl = Slider(min=0, max=1, value=0.7, size_hint_x=0.92)
            sl.bind(value=lambda s, v: self.player.vol(v))
            vr.add_widget(sl)
            p.add_widget(vr)
            scroll = ScrollView()
            self.trk_grid = GridLayout(cols=1, spacing=dp(3), padding=dp(4), size_hint_y=None)
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
                fl = sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                if hasattr(self, 'trk_lbl'):
                    self.trk_lbl.text = f"{len(fl)} spor"
                for i, fn in enumerate(fl):
                    self.tracks.append(os.path.join(MUSIC_DIR, fn))
                    btn = mkbtn(fn, lambda idx=i: self.play_track(idx), small=True, size_hint_y=None, height=dp(38))
                    btn.canvas.before.clear()
                    with btn.canvas.before:
                        Color(rgba=BTN)
                        RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(6)])
                    self.trk_grid.add_widget(btn)
            except Exception as e:
                log(f"load_tracks: {e}")

        def play_track(self, idx):
            if idx < 0 or idx >= len(self.tracks):
                return
            self.ct = idx
            self.player.play(self.tracks[idx])
            n = os.path.basename(self.tracks[idx])
            if hasattr(self, 'trk_lbl'):
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
            if hasattr(self, 'trk_lbl'):
                self.trk_lbl.text = "Stoppet"

        def next_track(self):
            if self.tracks:
                self.play_track((self.ct + 1) % len(self.tracks))

        def prev_track(self):
            if self.tracks:
                self.play_track((self.ct - 1) % len(self.tracks))

        # ---------- AMBIENT ----------
        def _mk_amb(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4))
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(3), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for snd in AMBIENT_SOUNDS:
                if 'url' not in snd:
                    g.add_widget(mklbl(snd['name'], color=GDIM, size=11, bold=True, h=22))
                else:
                    btn = mkbtn(snd['name'], lambda u=snd['url'], n=snd['name']: self._pa(u, n),
                                small=True, size_hint_y=None, height=dp(36))
                    btn.canvas.before.clear()
                    with btn.canvas.before:
                        Color(rgba=BTN)
                        RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(6)])
                    g.add_widget(btn)
            scroll.add_widget(g)
            p.add_widget(scroll)
            p.add_widget(mkbtn("Stopp ambient", self._sa, danger=True, size_hint_y=None, height=dp(36)))
            vr = BoxLayout(size_hint_y=None, height=dp(28), padding=[dp(8),0])
            vr.add_widget(Label(text="Vol", color=DIM, size_hint_x=0.08, font_size=sp(10)))
            sl = Slider(min=0, max=1, value=0.5, size_hint_x=0.92)
            sl.bind(value=lambda s, v: self.streamer.vol(v))
            vr.add_widget(sl)
            p.add_widget(vr)
            self.amb_lbl = mklbl("", color=DIM, size=11, h=18)
            p.add_widget(self.amb_lbl)
            p.add_widget(Widget(size_hint_y=1))
            return p

        def _pa(self, url, name):
            self._an = name
            self._ac = 0
            if hasattr(self, 'amb_lbl'):
                self.amb_lbl.text = f"Laster: {name}..."
            if self.streamer.play_url(url):
                Clock.schedule_interval(self._poll, 2)

        def _poll(self, dt):
            self._ac += 1
            if self.streamer.is_playing:
                if hasattr(self, 'amb_lbl'):
                    self.amb_lbl.text = f"Spiller: {self._an}"
                    self.amb_lbl.color = GRN
                return False
            if self._ac >= 10:
                if hasattr(self, 'amb_lbl'):
                    self.amb_lbl.text = f"Feilet: {self._an}"
                    self.amb_lbl.color = RED
                return False
            if hasattr(self, 'amb_lbl'):
                self.amb_lbl.text = f"Laster: {self._an} ({self._ac*2}s)..."
            return True

        def _sa(self):
            self.streamer.stop()
            if hasattr(self, 'amb_lbl'):
                self.amb_lbl.text = "Stoppet"
                self.amb_lbl.color = DIM

        # ---------- CAST ----------
        def _mk_cast(self):
            p = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
            if not CAST_AVAILABLE:
                p.add_widget(mklbl("Casting utilgjengelig\npychromecast mangler", color=DIM, size=13))
                return p
            self.cast_lbl = mklbl("Ikke tilkoblet", color=DIM, size=13, h=28)
            p.add_widget(self.cast_lbl)
            p.add_widget(mkbtn("Sok etter enheter", self._scan, accent=True, size_hint_y=None, height=dp(42)))
            self.cast_sp = Spinner(text="Velg enhet...", values=[], size_hint_y=None, height=dp(42),
                                   background_color=BTN, color=TXT)
            p.add_widget(self.cast_sp)
            r = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
            r.add_widget(mkbtn("Koble til", self._cn, accent=True))
            r.add_widget(mkbtn("Koble fra", self._dc, danger=True))
            p.add_widget(r)
            p.add_widget(Widget(size_hint_y=1))
            return p

        def _scan(self):
            if hasattr(self, 'cast_lbl'):
                self.cast_lbl.text = "Soker..."
            self.cast.scan(cb=self._od)

        def _od(self, n):
            if n and hasattr(self, 'cast_sp'):
                self.cast_sp.values = n
                self.cast_sp.text = n[0]
            if hasattr(self, 'cast_lbl'):
                self.cast_lbl.text = f"Fant {len(n)}" if n else "Ingen"

        def _cn(self):
            if not hasattr(self, 'cast_sp'):
                return
            n = self.cast_sp.text
            if not n or n == "Velg enhet...":
                return
            self.cast.connect(n, cb=lambda ok: setattr(self.cast_lbl, 'text', "Tilkoblet!" if ok else "Feilet") if hasattr(self, 'cast_lbl') else None)

        def _dc(self):
            self.cast.disconnect()
            if hasattr(self, 'cast_lbl'):
                self.cast_lbl.text = "Frakoblet"

        # ---------- KARAKTERER ----------
        def _mk_tool(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4))
            tb = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4), padding=[dp(4),0])
            tb.add_widget(mkbtn("+ Ny", self._new_char, accent=True, size_hint_x=0.35))
            tb.add_widget(mkbtn("Oppdater", self._show_list, small=True, size_hint_x=0.35))
            tb.add_widget(mklbl("Karakterer", color=GOLD, size=14, bold=True))
            p.add_widget(tb)
            self.tool_area = BoxLayout()
            p.add_widget(self.tool_area)
            self._show_list()
            return p

        def _show_list(self):
            if not hasattr(self, 'tool_area'):
                return
            self.tool_area.clear_widgets()
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            if not self.chars:
                g.add_widget(mklbl("Ingen karakterer ennaa.\nTrykk '+ Ny' for aa lage en.", color=DIM, size=12, h=50))
            else:
                for i, ch in enumerate(self.chars):
                    nm = ch.get('name', '?')
                    tp = ch.get('type', 'PC')
                    oc = ch.get('occ', '')
                    c = GRN if tp == 'PC' else GOLD
                    txt = f"[{tp}]  {nm}"
                    if oc:
                        txt += f"  -  {oc}"
                    row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
                    b = mkbtn(txt, lambda idx=i: self._view_char(idx), small=True, size_hint_x=0.72)
                    b.color = c
                    b.halign = 'left'
                    row.add_widget(b)
                    row.add_widget(mkbtn("Rediger", lambda idx=i: self._edit_char(idx), accent=True, small=True, size_hint_x=0.28))
                    g.add_widget(row)
            scroll.add_widget(g)
            self.tool_area.add_widget(scroll)

        def _view_char(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            ch = self.chars[idx]
            self.tool_area.clear_widgets()
            p = BoxLayout(orientation='vertical', spacing=dp(2), padding=dp(4))
            top = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4))
            top.add_widget(mkbtn("Tilbake", self._show_list, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Rediger", lambda: self._edit_char(idx), accent=True, small=True, size_hint_x=0.3))
            top.add_widget(mkbtn("Slett", lambda: self._del_char(idx), danger=True, small=True, size_hint_x=0.3))
            p.add_widget(top)
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(2), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            nm = ch.get('name', '?')
            tp = ch.get('type', 'PC')
            g.add_widget(mklbl(f"[{tp}]  {nm}", color=GOLD, size=18, bold=True, h=30))
            for key, lbl in CHAR_INFO:
                v = ch.get(key, '')
                if v and key not in ('name', 'type'):
                    g.add_widget(mklbl(f"{lbl}:  {v}", color=TXT, size=14, h=24))
            stats = ""
            for key, lbl in CHAR_STATS:
                v = ch.get(key, '')
                if v:
                    stats += f"{lbl} {v}   "
            if stats:
                g.add_widget(mklbl(stats.strip(), color=TXT, size=14, h=26))
            derived = ""
            for key, lbl in CHAR_DERIVED:
                v = ch.get(key, '')
                if v:
                    derived += f"{lbl} {v}   "
            if derived:
                g.add_widget(mklbl(derived.strip(), color=TXT, size=14, h=26))
            sk = ch.get('skills', {})
            if sk and isinstance(sk, dict):
                g.add_widget(mksep(4))
                g.add_widget(mklbl("FERDIGHETER", color=GOLD, size=13, bold=True, h=22))
                sk_txt = ""
                for sname, sval in sorted(sk.items()):
                    if sval:
                        sk_txt += f"{sname} {sval}   "
                if sk_txt:
                    g.add_widget(mklbl(sk_txt.strip(), color=TXT, size=13, wrap=True))
            for key, lbl in CHAR_TEXT:
                v = ch.get(key, '')
                if v:
                    g.add_widget(mksep(4))
                    g.add_widget(mklbl(lbl.upper(), color=GOLD, size=13, bold=True, h=22))
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
            p = BoxLayout(orientation='vertical', spacing=dp(2), padding=dp(4))
            top = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4))
            top.add_widget(mkbtn("Lagre", self._save_edit, accent=True, small=True, size_hint_x=0.35))
            top.add_widget(mkbtn("Avbryt", self._show_list, small=True, size_hint_x=0.35))
            top.add_widget(mkbtn("Skills", lambda: self._edit_skills(idx), small=True, size_hint_x=0.3))
            p.add_widget(top)
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(1), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            self._ei = {}
            g.add_widget(mklbl("GRUNNINFO", color=GOLD, size=12, bold=True, h=22))
            for key, lbl in CHAR_INFO:
                row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
                row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM, size_hint_x=0.3, halign='right'))
                if key == 'type':
                    w = Spinner(text=ch.get(key, 'PC'), values=['PC', 'NPC'],
                                background_color=BTN, color=GOLD, font_size=sp(11), size_hint_x=0.7)
                else:
                    w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                  background_color=BTN, foreground_color=TXT, size_hint_x=0.7, padding=[dp(4), dp(2)])
                self._ei[key] = w
                row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("KARAKTERISTIKKER", color=GOLD, size=12, bold=True, h=22))
            for i in range(0, len(CHAR_STATS), 2):
                row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
                for j in range(2):
                    if i + j < len(CHAR_STATS):
                        key, lbl = CHAR_STATS[i + j]
                        row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM, size_hint_x=0.15, halign='right'))
                        w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                      background_color=BTN, foreground_color=TXT, size_hint_x=0.35,
                                      padding=[dp(4), dp(2)], input_filter='int')
                        self._ei[key] = w
                        row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("HP / MP / SAN / LUCK", color=GOLD, size=12, bold=True, h=22))
            for i in range(0, len(CHAR_DERIVED), 2):
                row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
                for j in range(2):
                    if i + j < len(CHAR_DERIVED):
                        key, lbl = CHAR_DERIVED[i + j]
                        row.add_widget(Label(text=lbl, font_size=sp(10), color=DIM, size_hint_x=0.15, halign='right'))
                        w = TextInput(text=str(ch.get(key, '')), font_size=sp(12), multiline=False,
                                      background_color=BTN, foreground_color=TXT, size_hint_x=0.35,
                                      padding=[dp(4), dp(2)])
                        self._ei[key] = w
                        row.add_widget(w)
                g.add_widget(row)
            g.add_widget(mksep(4))
            g.add_widget(mklbl("NOTATER / UTSTYR", color=GOLD, size=12, bold=True, h=22))
            for key, lbl in CHAR_TEXT:
                g.add_widget(Label(text=lbl, font_size=sp(10), color=DIM, size_hint_y=None, height=dp(18), halign='left'))
                w = TextInput(text=str(ch.get(key, '')), font_size=sp(11), multiline=True,
                              background_color=BTN, foreground_color=TXT, size_hint_y=None, height=dp(60),
                              padding=[dp(4), dp(2)])
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
            p = BoxLayout(orientation='vertical', spacing=dp(2), padding=dp(4))
            top = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4))
            top.add_widget(mkbtn("Lagre skills", lambda: self._save_skills(idx), accent=True, small=True, size_hint_x=0.5))
            top.add_widget(mkbtn("Tilbake", lambda: self._edit_char(idx), small=True, size_hint_x=0.5))
            p.add_widget(top)
            p.add_widget(mklbl(f"Skills: {ch.get('name', '?')}", color=GOLD, size=13, bold=True, h=24))
            scroll = ScrollView()
            g = GridLayout(cols=1, spacing=dp(1), padding=dp(2), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            self._sk_inputs = {}
            for sname, sdefault in SKILLS:
                row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(2))
                is_spec = sname.endswith(':')
                if is_spec:
                    spec_key = sname
                    saved = sk.get(spec_key, '')
                    row.add_widget(Label(text=sname, font_size=sp(10), color=GDIM, size_hint_x=0.35, halign='right'))
                    w = TextInput(text=str(saved), hint_text=f"Spesifiser + verdi",
                                  font_size=sp(11), multiline=False, background_color=BTN, foreground_color=TXT,
                                  size_hint_x=0.65, padding=[dp(4), dp(2)])
                    self._sk_inputs[spec_key] = w
                    row.add_widget(w)
                else:
                    row.add_widget(Label(text=f"{sname} ({sdefault})", font_size=sp(10), color=DIM, size_hint_x=0.65, halign='left'))
                    val = sk.get(sname, '')
                    w = TextInput(text=str(val), hint_text=sdefault,
                                  font_size=sp(12), multiline=False, background_color=BTN, foreground_color=TXT,
                                  size_hint_x=0.35, padding=[dp(4), dp(2)], input_filter='int')
                    self._sk_inputs[sname] = w
                    row.add_widget(w)
                g.add_widget(row)
            scroll.add_widget(g)
            p.add_widget(scroll)
            self.tool_area.add_widget(p)

        def _save_skills(self, idx):
            if idx < 0 or idx >= len(self.chars):
                return
            sk = {}
            for sname, w in self._sk_inputs.items():
                v = w.text.strip()
                if v:
                    sk[sname] = v
            self.chars[idx]['skills'] = sk
            save_json(CHAR_FILE, self.chars)
            self._edit_char(idx)

        def _save_edit(self):
            if self.edit_idx is None or self.edit_idx >= len(self.chars):
                return
            ch = self.chars[self.edit_idx]
            for key in list(self._ei.keys()):
                w = self._ei[key]
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
