import os, sys, traceback, socket, threading, math
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
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.relativelayout import RelativeLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.button import Button
    from kivy.uix.togglebutton import ToggleButton
    from kivy.uix.label import Label
    from kivy.uix.image import Image
    from kivy.uix.slider import Slider
    from kivy.uix.spinner import Spinner
    from kivy.uix.widget import Widget
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse, Triangle
    from kivy.animation import Animation
    from kivy.metrics import dp, sp
    from kivy.properties import NumericProperty
    log("Kivy imported OK")

    CAST_AVAILABLE = False
    try:
        import pychromecast
        CAST_AVAILABLE = True
        log("pychromecast imported OK")
    except ImportError as e:
        log(f"pychromecast not available: {e}")

    USE_JNIUS = False
    MediaPlayer = None
    if platform == 'android':
        try:
            from jnius import autoclass
            MediaPlayer = autoclass('android.media.MediaPlayer')
            USE_JNIUS = True
            log("Using Android MediaPlayer")
        except Exception as e:
            log(f"jnius import failed: {e}")

    IMG_DIR = "/sdcard/Documents/EldritchPortal/images"
    MUSIC_DIR = "/sdcard/Documents/EldritchPortal/music"
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(MUSIC_DIR, exist_ok=True)

    # === CTHULHU FARGEPALETT ===
    C_VOID = (0.02, 0.02, 0.04, 1)
    C_ABYSS = (0.05, 0.05, 0.08, 1)
    C_DEEP = (0.08, 0.08, 0.12, 1)
    C_SURFACE = (0.11, 0.12, 0.16, 1)
    C_RAISED = (0.15, 0.16, 0.20, 1)
    C_GOLD = (0.85, 0.70, 0.22, 1)
    C_GOLD_DIM = (0.50, 0.40, 0.14, 1)
    C_GOLD_BRIGHT = (1.0, 0.88, 0.40, 1)
    C_TEXT = (0.75, 0.72, 0.65, 1)
    C_TEXT_DIM = (0.45, 0.43, 0.38, 1)
    C_GREEN = (0.12, 0.40, 0.25, 1)
    C_BLOOD = (0.50, 0.10, 0.10, 1)
    C_TENTACLE = (0.20, 0.12, 0.28, 1)
    HTTP_PORT = 8089

    # === STEMNINGSLYDER (Internet Archive - direkte MP3-lenker) ===
    AMBIENT_SOUNDS = [
        {"name": "Regn og torden",
         "url": "https://archive.org/download/RainSound13/Gentle%20Rain%20and%20Thunder.mp3"},
        {"name": "Havboelger",
         "url": "https://archive.org/download/naturesounds-soundtheraphy/Birds%20With%20Ocean%20Waves%20on%20the%20Beach.mp3"},
        {"name": "Nattregn",
         "url": "https://archive.org/download/RainSound13/Night%20Rain%20Sound.mp3"},
        {"name": "Vind og storm",
         "url": "https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/epic-storm-thunder-rainwindwaves-no-loops-106800.mp3"},
        {"name": "Nattlyder (gresshopper)",
         "url": "https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/ambience-crickets-chirping-in-very-light-rain-followed-by-gentle-rolling-thunder-10577.mp3"},
        {"name": "Havstorm",
         "url": "https://archive.org/download/naturesounds-soundtheraphy/Sound%20Therapy%20-%20Sea%20Storm.mp3"},
        {"name": "Lett regn",
         "url": "https://archive.org/download/naturesounds-soundtheraphy/Light%20Gentle%20Rain.mp3"},
        {"name": "Tordenstorm",
         "url": "https://archive.org/download/RainSound13/Rain%20Sound%20with%20Thunderstorm.mp3"},
        {"name": "Skummel atmosfaere",
         "url": "https://archive.org/download/creepy-music-sounds/Creepy%20music%20%26%20sounds.mp3"},
        {"name": "Uhyggelig drone",
         "url": "https://archive.org/download/scary-sound-effects-8/Evil%20Demon%20Drone%20Movie%20Halloween%20Sounds.mp3"},
        {"name": "Mork spenning",
         "url": "https://archive.org/download/scary-sound-effects-8/Dramatic%20Suspense%20Sound%20Effects.mp3"},
        {"name": "Urolig hav",
         "url": "https://archive.org/download/RelaxingRainAndLoudThunderFreeFieldRecordingOfNatureSoundsForSleepOrMeditation/Relaxing%20Rain%20and%20Loud%20Thunder%20%28Free%20Field%20Recording%20of%20Nature%20Sounds%20for%20Sleep%20or%20Meditation%20Mp3%29.mp3"},
    ]

    def request_android_permissions():
        if platform != 'android':
            return
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES,
                Permission.READ_MEDIA_AUDIO, Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE, Permission.ACCESS_WIFI_STATE,
                Permission.CHANGE_WIFI_MULTICAST_STATE,
            ])
        except Exception as e:
            log(f"Permission request failed: {e}")

    # ============================================================
    #  ELDRITCH ANIMERTE WIDGETS
    # ============================================================

    class EldritchBG(Widget):
        _time = NumericProperty(0)
        def __init__(self, **kw):
            super().__init__(**kw)
            self.bind(pos=self._draw, size=self._draw)
            Clock.schedule_interval(self._tick, 1/15.0)
        def _tick(self, dt):
            self._time += dt
            self._draw()
        def _draw(self, *a):
            self.canvas.clear()
            w, h = self.size
            x0, y0 = self.pos
            if w < 1 or h < 1:
                return
            t = self._time
            with self.canvas:
                Color(*C_VOID)
                Rectangle(pos=self.pos, size=self.size)
                for i in range(3):
                    cx = x0 + w * (0.2 + i * 0.3)
                    cy = y0 + h * (0.3 + math.sin(t * 0.3 + i) * 0.1)
                    r = dp(40) + math.sin(t * 0.5 + i * 2) * dp(15)
                    alpha = 0.03 + math.sin(t * 0.4 + i) * 0.015
                    Color(C_TENTACLE[0], C_TENTACLE[1], C_TENTACLE[2], alpha)
                    Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
                for i in range(8):
                    seed = i * 137.5
                    px = x0 + ((seed + t * 8) % w)
                    py = y0 + ((seed * 2.3 + t * 5) % h)
                    alpha = 0.08 + math.sin(t + seed) * 0.04
                    sz = dp(1.5)
                    Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], alpha)
                    Ellipse(pos=(px, py), size=(sz, sz))

    class ElderSign(Widget):
        _glow = NumericProperty(0.3)
        def __init__(self, **kw):
            super().__init__(**kw)
            self.size_hint = (None, None)
            self.size = (dp(30), dp(30))
            self._anim()
            self.bind(pos=self._draw, size=self._draw)
        def _anim(self):
            a = Animation(_glow=0.7, d=2) + Animation(_glow=0.3, d=2)
            a.bind(on_progress=lambda *x: self._draw())
            a.bind(on_complete=lambda *x: self._anim())
            a.start(self)
        def _draw(self, *a):
            self.canvas.clear()
            cx, cy = self.x + self.width/2, self.y + self.height/2
            r = min(self.width, self.height) / 2.5
            with self.canvas:
                Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], self._glow * 0.5)
                Line(circle=(cx, cy, r), width=dp(1))
                Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], self._glow)
                for j in range(5):
                    a1 = math.radians(j * 72 - 90)
                    a2 = math.radians((j+2) * 72 - 90)
                    Line(points=[cx+r*0.9*math.cos(a1), cy+r*0.9*math.sin(a1),
                                 cx+r*0.9*math.cos(a2), cy+r*0.9*math.sin(a2)], width=dp(0.8))
                Color(C_GOLD_BRIGHT[0], C_GOLD_BRIGHT[1], C_GOLD_BRIGHT[2], self._glow)
                Ellipse(pos=(cx-dp(2), cy-dp(2)), size=(dp(4), dp(4)))

    class GoldDivider(Widget):
        def __init__(self, **kw):
            super().__init__(**kw)
            self.size_hint_y = None
            self.height = dp(12)
            self.bind(pos=self._draw, size=self._draw)
            Clock.schedule_once(lambda dt: self._draw(), 0)
        def _draw(self, *a):
            self.canvas.clear()
            w, cy = self.width, self.y + self.height/2
            cx = self.x + w/2
            with self.canvas:
                Color(*C_GOLD_DIM, 0.3)
                Rectangle(pos=(self.x + w*0.05, cy), size=(w*0.9, dp(1)))
                Color(*C_GOLD, 0.5)
                Rectangle(pos=(self.x + w*0.2, cy), size=(w*0.6, dp(1)))
                Color(*C_GOLD, 0.7)
                d = dp(4)
                Triangle(points=[cx, cy+d, cx-d, cy, cx, cy-d])
                Triangle(points=[cx, cy+d, cx+d, cy, cx, cy-d])

    class PulsingOrb(Widget):
        _pulse = NumericProperty(0.3)
        def __init__(self, color=C_GOLD, **kw):
            super().__init__(**kw)
            self.size_hint = (None, None)
            self.size = (dp(14), dp(14))
            self._color = color
            self._active = False
            self.bind(pos=self._draw, size=self._draw)
        def start(self):
            self._active = True
            self._go()
        def stop(self):
            self._active = False
            Animation.cancel_all(self, '_pulse')
            self._pulse = 0.2
            self._draw()
        def _go(self):
            if not self._active: return
            a = Animation(_pulse=1.0, d=1.2, t='in_out_sine') + Animation(_pulse=0.3, d=1.2, t='in_out_sine')
            a.bind(on_progress=lambda *x: self._draw())
            a.bind(on_complete=lambda *x: self._go())
            a.start(self)
        def _draw(self, *a):
            self.canvas.clear()
            cx, cy = self.x+self.width/2, self.y+self.height/2
            with self.canvas:
                Color(self._color[0], self._color[1], self._color[2], self._pulse*0.15)
                Ellipse(pos=(cx-self.width, cy-self.height), size=(self.width*2, self.height*2))
                Color(self._color[0], self._color[1], self._color[2], self._pulse*0.8)
                r = self.width*0.3
                Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))

    class ElButton(Button):
        _ba = NumericProperty(0.25)
        def __init__(self, accent=False, danger=False, **kw):
            super().__init__(**kw)
            self.background_normal = ''
            self.background_down = ''
            self.background_color = (0,0,0,0)
            self._accent = accent
            self._danger = danger
            self.color = C_GOLD if accent else ((0.8,0.3,0.3,1) if danger else C_TEXT)
            self.bold = True
            self.font_size = sp(14)
            self.bind(pos=self._draw, size=self._draw, state=self._on_state)
            Clock.schedule_once(lambda dt: self._draw(), 0)
        def _on_state(self, *a):
            target = 0.8 if self.state == 'down' else 0.25
            Animation(_ba=target, d=0.15).start(self)
            self.bind(_ba=lambda *x: self._draw())
        def _draw(self, *a):
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*C_SURFACE)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
                bc = C_GOLD if self._accent else (C_BLOOD if self._danger else C_GOLD_DIM)
                Color(bc[0], bc[1], bc[2], self._ba)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(5)), width=dp(0.8))

    class ElTab(ToggleButton):
        _bw = NumericProperty(0)
        def __init__(self, **kw):
            super().__init__(**kw)
            self.background_normal = ''
            self.background_down = ''
            self.background_color = (0,0,0,0)
            self.color = C_TEXT_DIM
            self.bold = True
            self.font_size = sp(15)
            self.bind(pos=self._draw, size=self._draw, state=self._on_state)
            Clock.schedule_once(lambda dt: self._on_state(), 0)
        def _on_state(self, *a):
            if self.state == 'down':
                self.color = C_GOLD
                Animation(_bw=self.width*0.5, d=0.3, t='out_cubic').start(self)
            else:
                self.color = C_TEXT_DIM
                Animation(_bw=0, d=0.2).start(self)
            self.bind(_bw=lambda *x: self._draw())
        def _draw(self, *a):
            self.canvas.after.clear()
            if self._bw > 1:
                bx = self.x + (self.width - self._bw)/2
                with self.canvas.after:
                    Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], 0.15)
                    RoundedRectangle(pos=(bx-dp(4), self.y), size=(self._bw+dp(8), dp(6)), radius=[dp(3)])
                    Color(*C_GOLD, 0.85)
                    RoundedRectangle(pos=(bx, self.y+dp(1)), size=(self._bw, dp(3)), radius=[dp(1.5)])

    class ImageCard(RelativeLayout):
        """Miniatyrbilde uten ramme, med mipmap for store filer."""
        def __init__(self, image_path, on_tap=None, **kw):
            super().__init__(**kw)
            self.size_hint_y = None
            self.height = dp(120)
            self.image_path = image_path
            self._on_tap = on_tap
            self.img = Image(source=image_path, allow_stretch=True, keep_ratio=True,
                           pos_hint={'center_x':0.5,'center_y':0.58}, size_hint=(0.92,0.72),
                           mipmap=True, nocache=True)
            self.add_widget(self.img)
            fname = os.path.basename(image_path)
            short = fname[:12]+".." if len(fname)>12 else fname
            self.add_widget(Label(text=short, font_size=sp(9), color=C_GOLD_DIM,
                                 pos_hint={'center_x':0.5,'y':0.0}, size_hint=(1,0.2)))
            btn = Button(background_color=(0,0,0,0), background_normal='',
                        pos_hint={'x':0,'y':0}, size_hint=(1,1))
            btn.bind(on_release=lambda x: self._on_tap(self.image_path) if self._on_tap else None)
            self.add_widget(btn)

    class MiniPlayer(BoxLayout):
        """Kompakt musikkontroll synlig paa alle faner."""
        def __init__(self, app_ref, **kw):
            super().__init__(**kw)
            self.app = app_ref
            self.orientation = 'horizontal'
            self.size_hint_y = None
            self.height = dp(48)
            self.padding = [dp(10), dp(4)]
            self.spacing = dp(8)
            self.bind(pos=self._dbg, size=self._dbg)
            self.track_lbl = Label(text="Ingen musikk", font_size=sp(12), color=C_TEXT_DIM,
                                  size_hint_x=0.5, halign='left', shorten=True, shorten_from='right')
            self.track_lbl.bind(size=self.track_lbl.setter('text_size'))
            self.add_widget(self.track_lbl)
            for txt, cb in [("Forr", self._prev), ("Play", self._toggle), ("Neste", self._next)]:
                b = Button(text=txt, font_size=sp(11), bold=True, size_hint_x=None, width=dp(52),
                          background_normal='', background_color=(0,0,0,0),
                          color=C_GOLD if txt=="Play" else C_TEXT_DIM)
                b.bind(on_release=lambda x, f=cb: f())
                self.add_widget(b)
                if txt == "Play": self.btn_play = b
            self.orb = PulsingOrb(color=C_GREEN)
            self.add_widget(self.orb)
        def _dbg(self, *a):
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*C_ABYSS)
                Rectangle(pos=self.pos, size=self.size)
                Color(*C_GOLD_DIM, 0.2)
                Line(points=[self.x, self.top, self.right, self.top], width=dp(0.5))
        def update(self, track_name=None, playing=False):
            if track_name:
                self.track_lbl.text = track_name
                self.track_lbl.color = C_GOLD if playing else C_TEXT
            self.btn_play.text = "Pause" if playing else "Play"
            if playing: self.orb.start()
            else: self.orb.stop()
        def _toggle(self): self.app.toggle_play()
        def _next(self): self.app.next_track()
        def _prev(self): self.app.prev_track()

    # ============================================================
    #  HTTP SERVER
    # ============================================================
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, f, *a): pass

    class MediaServer:
        def __init__(self, directory, port=HTTP_PORT):
            self.directory = directory
            self.port = port
            self._httpd = None
        def start(self):
            if self._httpd: return
            try:
                handler = partial(QuietHandler, directory=self.directory)
                self._httpd = HTTPServer(('0.0.0.0', self.port), handler)
                threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
                log(f"HTTP server started on port {self.port}")
            except Exception as e:
                log(f"HTTP server failed: {e}")
        def stop(self):
            if self._httpd: self._httpd.shutdown(); self._httpd = None
        @staticmethod
        def get_local_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]; s.close(); return ip
            except: return "127.0.0.1"
        def get_url(self, filepath):
            rel = os.path.relpath(filepath, self.directory)
            return f"http://{self.get_local_ip()}:{self.port}/{rel}"

    # ============================================================
    #  CAST MANAGER
    # ============================================================
    class CastManager:
        def __init__(self):
            self.devices = {}; self.active_cast = None; self.mc = None
            self._browser = None; self._scanning = False
        def discover(self, callback=None):
            if not CAST_AVAILABLE or self._scanning: return
            self._scanning = True; self.devices = {}
            def _scan():
                try:
                    ccs, browser = pychromecast.get_chromecasts()
                    self._browser = browser
                    for cc in ccs: self.devices[cc.cast_info.friendly_name] = cc
                except Exception as e: log(f"Cast scan error: {e}")
                finally:
                    self._scanning = False
                    if callback: Clock.schedule_once(lambda dt: callback(list(self.devices.keys())), 0)
            threading.Thread(target=_scan, daemon=True).start()
        def connect(self, name, callback=None):
            if name not in self.devices: return
            def _c():
                try:
                    cc = self.devices[name]; cc.wait()
                    self.active_cast = cc; self.mc = cc.media_controller
                    log(f"Cast: connected to {name}")
                    if callback: Clock.schedule_once(lambda dt: callback(True), 0)
                except Exception as e:
                    log(f"Cast connect error: {e}")
                    if callback: Clock.schedule_once(lambda dt: callback(False), 0)
            threading.Thread(target=_c, daemon=True).start()
        def cast_image(self, url, callback=None):
            if not self.mc: return
            def _c():
                try:
                    self.mc.play_media(url, 'image/jpeg'); self.mc.block_until_active()
                    log(f"Cast: image sent OK")
                    if callback: Clock.schedule_once(lambda dt: callback(True), 0)
                except Exception as e:
                    log(f"Cast image error: {e}")
                    if callback: Clock.schedule_once(lambda dt: callback(False), 0)
            threading.Thread(target=_c, daemon=True).start()
        def disconnect(self):
            try:
                if self._browser: self._browser.stop_discovery()
                if self.active_cast: self.active_cast.disconnect()
            except: pass
            self.active_cast = None; self.mc = None

    # ============================================================
    #  LYDSPILLERE
    # ============================================================
    class AndroidPlayer:
        def __init__(self): self.mp = None; self.is_playing = False; self._vol = 0.7
        def play(self, path):
            self.stop()
            try:
                self.mp = MediaPlayer(); self.mp.setDataSource(path)
                self.mp.setVolume(self._vol, self._vol); self.mp.prepare(); self.mp.start()
                self.is_playing = True
            except Exception as e: log(f"Player error: {e}"); self.mp = None; self.is_playing = False
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying(): self.mp.stop()
                    self.mp.release()
                except: pass
                self.mp = None
            self.is_playing = False
        def pause(self):
            if self.mp and self.is_playing:
                try: self.mp.pause(); self.is_playing = False
                except: pass
        def resume(self):
            if self.mp and not self.is_playing:
                try: self.mp.start(); self.is_playing = True
                except: pass
        def set_volume(self, v):
            self._vol = v
            if self.mp:
                try: self.mp.setVolume(v, v)
                except: pass

    class StreamPlayer:
        """Spiller for nettstreaming - synkron prepare i bakgrunnstraad."""
        def __init__(self): self.mp = None; self.is_playing = False; self._vol = 0.5
        def play_url(self, url):
            self.stop()
            if not USE_JNIUS:
                log("StreamPlayer: no jnius")
                return False
            def _stream():
                try:
                    log(f"StreamPlayer: loading {url}")
                    self.mp = MediaPlayer()
                    self.mp.setDataSource(url)
                    self.mp.setVolume(self._vol, self._vol)
                    self.mp.prepare()
                    self.mp.start()
                    self.is_playing = True
                    log(f"StreamPlayer: playing OK")
                except Exception as e:
                    log(f"StreamPlayer error: {e}")
                    if self.mp:
                        try: self.mp.release()
                        except: pass
                        self.mp = None
                    self.is_playing = False
            threading.Thread(target=_stream, daemon=True).start()
            return True
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying(): self.mp.stop()
                    self.mp.release()
                except: pass
                self.mp = None
            self.is_playing = False
        def set_volume(self, v):
            self._vol = v
            if self.mp:
                try: self.mp.setVolume(v, v)
                except: pass

    class FallbackPlayer:
        def __init__(self):
            from kivy.core.audio import SoundLoader
            self.SL = SoundLoader; self.sound = None; self.is_playing = False; self._vol = 0.7
        def play(self, path):
            self.stop()
            try:
                self.sound = self.SL.load(path)
                if self.sound: self.sound.volume = self._vol; self.sound.play(); self.is_playing = True
            except: pass
        def stop(self):
            if self.sound:
                try: self.sound.stop()
                except: pass
                self.sound = None
            self.is_playing = False
        def pause(self):
            if self.sound and self.is_playing: self.sound.stop(); self.is_playing = False
        def resume(self):
            if self.sound and not self.is_playing: self.sound.play(); self.is_playing = True
        def set_volume(self, v):
            self._vol = v
            if self.sound: self.sound.volume = v

    # ============================================================
    #  HOVEDAPP
    # ============================================================
    class EldritchApp(App):
        def build(self):
            log("build() called")
            Window.clearcolor = C_VOID
            self.title = "Eldritch Portal"
            self.tracks = []; self.current_track = -1; self.selected_image = None
            self.auto_cast = True
            self.player = AndroidPlayer() if USE_JNIUS else FallbackPlayer()
            self.stream_player = StreamPlayer()
            self.cast_mgr = CastManager()
            self.media_server = MediaServer("/sdcard/Documents/EldritchPortal", HTTP_PORT)

            root = FloatLayout()
            self.bg = EldritchBG(pos_hint={'x':0,'y':0}, size_hint=(1,1))
            root.add_widget(self.bg)
            main = BoxLayout(orientation='vertical', spacing=0, pos_hint={'x':0,'y':0}, size_hint=(1,1))

            # === TOPPSEKSJON ===
            top = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(105))
            title_row = BoxLayout(size_hint_y=None, height=dp(44), padding=[dp(12), dp(6)])
            title_row.add_widget(ElderSign())
            title_row.add_widget(Widget(size_hint_x=None, width=dp(8)))
            title_row.add_widget(Label(text="ELDRITCH PORTAL", font_size=sp(19), color=C_GOLD, bold=True, size_hint_x=0.7, halign='left'))
            self.top_orb = PulsingOrb(color=C_GOLD)
            ob = BoxLayout(size_hint_x=None, width=dp(30)); ob.add_widget(self.top_orb)
            title_row.add_widget(ob)
            top.add_widget(title_row)

            tab_bar = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(2), padding=[dp(8),0])
            self.tab_img = ElTab(text="Bilder", group='tabs', state='down')
            self.tab_mus = ElTab(text="Musikk", group='tabs')
            self.tab_amb = ElTab(text="Ambient", group='tabs')
            self.tab_cast = ElTab(text="Cast", group='tabs')
            self.tab_img.bind(on_release=lambda x: self.show_tab('images'))
            self.tab_mus.bind(on_release=lambda x: self.show_tab('music'))
            self.tab_amb.bind(on_release=lambda x: self.show_tab('ambient'))
            self.tab_cast.bind(on_release=lambda x: self.show_tab('cast'))
            for t in [self.tab_img, self.tab_mus, self.tab_amb, self.tab_cast]: tab_bar.add_widget(t)
            top.add_widget(tab_bar)
            top.add_widget(GoldDivider())
            main.add_widget(top)

            # === INNHOLD ===
            self.content = BoxLayout(padding=[dp(6), dp(4)])
            self.img_panel = self._build_image_panel()
            self.mus_panel = self._build_music_panel()
            self.amb_panel = self._build_ambient_panel()
            self.cast_panel = self._build_cast_panel()
            self.content.add_widget(self.img_panel)
            main.add_widget(self.content)

            # === MINI-PLAYER ===
            self.mini_player = MiniPlayer(app_ref=self)
            main.add_widget(self.mini_player)

            # === BUNN ===
            main.add_widget(GoldDivider())
            self.status = Label(text="", font_size=sp(10), color=C_TEXT_DIM, size_hint_y=None, height=dp(22), halign='center')
            self.status.bind(size=self.status.setter('text_size'))
            main.add_widget(self.status)
            root.add_widget(main)

            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init(), 3)
            return root

        # --- PANELER ---
        def _build_image_panel(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            self.preview = Image(size_hint_y=0.4, allow_stretch=True, keep_ratio=True)
            p.add_widget(self.preview)
            self.img_info = Label(text="Trykk bilde for aa vise og caste", font_size=sp(12), color=C_TEXT_DIM, size_hint_y=None, height=dp(22), halign='center')
            self.img_info.bind(size=self.img_info.setter('text_size'))
            p.add_widget(self.img_info)
            br = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6), padding=[dp(4),0])
            self.btn_ac = ElButton(text="Auto-Cast: PA", accent=True, size_hint_x=0.5)
            self.btn_ac.bind(on_release=lambda x: self._toggle_ac())
            br.add_widget(self.btn_ac)
            btn_ref = ElButton(text="Oppdater", size_hint_x=0.5)
            btn_ref.bind(on_release=lambda x: self.load_images())
            br.add_widget(btn_ref)
            p.add_widget(br)
            scroll = ScrollView(size_hint_y=0.4)
            self.img_grid = GridLayout(cols=3, spacing=dp(6), padding=dp(4), size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid)
            p.add_widget(scroll)
            return p

        def _build_music_panel(self):
            p = BoxLayout(orientation='vertical', spacing=dp(6))
            self.track_label = Label(text="Velg et spor", font_size=sp(16), color=C_TEXT_DIM, size_hint_y=None, height=dp(40), halign='center', bold=True)
            self.track_label.bind(size=self.track_label.setter('text_size'))
            p.add_widget(self.track_label)
            ctrl = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6), padding=[dp(8),0])
            for txt, cb in [("Forr", self.prev_track), ("Play", self.toggle_play), ("Neste", self.next_track), ("Stopp", self.stop_music)]:
                b = ElButton(text=txt, accent=(txt=="Play"))
                b.bind(on_release=lambda x, f=cb: f())
                ctrl.add_widget(b)
                if txt == "Play": self.btn_play = b
            p.add_widget(ctrl)
            vr = BoxLayout(size_hint_y=None, height=dp(36), padding=[dp(12),0])
            vr.add_widget(Label(text="Vol:", color=C_TEXT_DIM, size_hint_x=0.1, font_size=sp(12)))
            self.vol_slider = Slider(min=0, max=1, value=0.7, size_hint_x=0.9)
            self.vol_slider.bind(value=self._on_vol)
            vr.add_widget(self.vol_slider)
            p.add_widget(vr)
            p.add_widget(GoldDivider())
            scroll = ScrollView(size_hint_y=1)
            self.track_grid = GridLayout(cols=1, spacing=dp(3), padding=dp(4), size_hint_y=None)
            self.track_grid.bind(minimum_height=self.track_grid.setter('height'))
            scroll.add_widget(self.track_grid)
            p.add_widget(scroll)
            return p

        def _build_ambient_panel(self):
            p = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(4))
            p.add_widget(Label(text="Stemningslyder", font_size=sp(18), color=C_GOLD, bold=True, size_hint_y=None, height=dp(35)))
            p.add_widget(Label(text="Spilles samtidig med musikk", font_size=sp(11), color=C_TEXT_DIM, size_hint_y=None, height=dp(20)))
            scroll = ScrollView(size_hint_y=0.55)
            g = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for snd in AMBIENT_SOUNDS:
                b = ElButton(text=snd['name'], size_hint_y=None, height=dp(46))
                b.bind(on_release=lambda x, u=snd['url'], n=snd['name']: self._play_amb(u, n))
                g.add_widget(b)
            scroll.add_widget(g)
            p.add_widget(scroll)
            p.add_widget(GoldDivider())
            bs = ElButton(text="Stopp ambient", danger=True, size_hint_y=None, height=dp(44))
            bs.bind(on_release=lambda x: self._stop_amb())
            p.add_widget(bs)
            avr = BoxLayout(size_hint_y=None, height=dp(36), padding=[dp(12),0])
            avr.add_widget(Label(text="Vol:", color=C_TEXT_DIM, size_hint_x=0.1, font_size=sp(12)))
            self.amb_vol = Slider(min=0, max=1, value=0.5, size_hint_x=0.9)
            self.amb_vol.bind(value=lambda s, v: self.stream_player.set_volume(v))
            avr.add_widget(self.amb_vol)
            p.add_widget(avr)
            self.amb_status = Label(text="", font_size=sp(12), color=C_TEXT_DIM, size_hint_y=None, height=dp(25))
            p.add_widget(self.amb_status)
            p.add_widget(Widget(size_hint_y=1))
            return p

        def _build_cast_panel(self):
            p = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(8))
            if not CAST_AVAILABLE:
                self.cast_status = Label(text="Casting utilgjengelig\npychromecast mangler", font_size=sp(14), halign='center', color=C_TEXT_DIM)
                self.cast_status.bind(size=self.cast_status.setter('text_size'))
                p.add_widget(self.cast_status); p.add_widget(Widget(size_hint_y=1)); return p
            self.cast_status = Label(text="Ikke tilkoblet", font_size=sp(14), halign='center', color=C_TEXT_DIM, size_hint_y=None, height=dp(35))
            self.cast_status.bind(size=self.cast_status.setter('text_size'))
            p.add_widget(self.cast_status)
            self.cast_orb = PulsingOrb(color=C_GOLD)
            or_ = BoxLayout(size_hint_y=None, height=dp(20)); or_.add_widget(Widget()); or_.add_widget(self.cast_orb); or_.add_widget(Widget())
            p.add_widget(or_)
            bs = ElButton(text="Sok etter enheter", accent=True, size_hint_y=None, height=dp(48))
            bs.bind(on_release=lambda x: self._scan_cast())
            p.add_widget(bs)
            self.cast_spinner = Spinner(text="Velg enhet...", values=[], size_hint_y=None, height=dp(48), background_color=C_SURFACE, color=C_TEXT)
            p.add_widget(self.cast_spinner)
            br = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            bc = ElButton(text="Koble til", accent=True, size_hint_x=0.5)
            bc.bind(on_release=lambda x: self._connect_cast())
            br.add_widget(bc)
            bd = ElButton(text="Koble fra", danger=True, size_hint_x=0.5)
            bd.bind(on_release=lambda x: self._disconnect_cast())
            br.add_widget(bd)
            p.add_widget(br); p.add_widget(Widget(size_hint_y=1))
            return p

        # --- INIT ---
        def _init(self):
            self.media_server.start(); self.load_images(); self.load_tracks()
            ip = MediaServer.get_local_ip()
            self.status.text = f"IP: {ip}  |  Cast: {'Klar' if CAST_AVAILABLE else 'Nei'}"
            self.top_orb.start()

        def show_tab(self, tab):
            self.content.clear_widgets()
            panels = {'images': self.img_panel, 'music': self.mus_panel, 'ambient': self.amb_panel, 'cast': self.cast_panel}
            if tab in panels: self.content.add_widget(panels[tab])

        # === BILDER ===
        def load_images(self):
            log("load_images()")
            self.img_grid.clear_widgets()
            try:
                if not os.path.exists(IMG_DIR): return
                filer = sorted([f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))])
                self.img_info.text = f"{len(filer)} bilder"
                for fname in filer:
                    path = os.path.join(IMG_DIR, fname)
                    self.img_grid.add_widget(ImageCard(image_path=path, on_tap=self.select_image))
            except Exception as e: log(f"load_images error: {e}")

        def select_image(self, path):
            log(f"Selected image: {path}")
            try:
                self.preview.source = path; self.selected_image = path
                self.img_info.text = os.path.basename(path); self.img_info.color = C_GOLD
                if self.auto_cast and self.cast_mgr.active_cast and self.cast_mgr.mc:
                    url = self.media_server.get_url(path)
                    self.img_info.text = "Caster..."
                    self.cast_mgr.cast_image(url, callback=self._on_cast_res)
            except Exception as e: log(f"select error: {e}")

        def _toggle_ac(self):
            self.auto_cast = not self.auto_cast
            self.btn_ac.text = f"Auto-Cast: {'PA' if self.auto_cast else 'AV'}"
            self.btn_ac.color = C_GOLD if self.auto_cast else C_TEXT_DIM

        def _on_cast_res(self, ok):
            self.img_info.text = f"Castet: {os.path.basename(self.selected_image)}" if ok else "Casting feilet"
            self.img_info.color = C_GOLD if ok else C_BLOOD

        # === CAST ===
        def _scan_cast(self):
            if not CAST_AVAILABLE: return
            self.cast_status.text = "Soker..."; self.cast_orb.start()
            self.cast_mgr.discover(callback=self._on_devs)
        def _on_devs(self, names):
            self.cast_orb.stop()
            if names:
                self.cast_spinner.values = names; self.cast_spinner.text = names[0]
                self.cast_status.text = f"Fant {len(names)} enhet(er)"; self.cast_status.color = C_GOLD
            else: self.cast_status.text = "Ingen funnet"; self.cast_status.color = C_TEXT_DIM
        def _connect_cast(self):
            if not CAST_AVAILABLE: return
            name = self.cast_spinner.text
            if not name or name == "Velg enhet...": return
            self.cast_status.text = "Kobler til..."; self.cast_orb.start()
            self.cast_mgr.connect(name, callback=self._on_conn)
        def _on_conn(self, ok):
            if ok: self.cast_status.text = f"Tilkoblet: {self.cast_spinner.text}"; self.cast_status.color = C_GOLD; self.cast_orb.start()
            else: self.cast_status.text = "Feilet"; self.cast_status.color = C_BLOOD; self.cast_orb.stop()
        def _disconnect_cast(self):
            self.cast_mgr.disconnect(); self.cast_status.text = "Frakoblet"; self.cast_status.color = C_TEXT_DIM; self.cast_orb.stop()

        # === MUSIKK ===
        def load_tracks(self):
            log("load_tracks()")
            self.track_grid.clear_widgets(); self.tracks = []
            try:
                if not os.path.exists(MUSIC_DIR): return
                filer = sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                self.track_label.text = f"{len(filer)} spor"
                for i, fname in enumerate(filer):
                    self.tracks.append(os.path.join(MUSIC_DIR, fname))
                    b = ElButton(text=fname, size_hint_y=None, height=dp(46)); b.font_size = sp(12); b.halign = 'left'
                    b.bind(size=b.setter('text_size'))
                    b.bind(on_release=lambda x, idx=i: self.play_track(idx))
                    self.track_grid.add_widget(b)
            except Exception as e: log(f"load_tracks error: {e}")

        def play_track(self, idx):
            if idx < 0 or idx >= len(self.tracks): return
            self.current_track = idx; path = self.tracks[idx]
            self.player.play(path); name = os.path.basename(path)
            if self.player.is_playing:
                self.btn_play.text = "Pause"; self.track_label.text = f"Spiller: {name}"; self.track_label.color = C_GOLD
                self.mini_player.update(name, True)
            else: self.track_label.text = "Feil"; self.mini_player.update("Feil", False)

        def toggle_play(self):
            if not self.player.is_playing and self.current_track < 0:
                if self.tracks: self.play_track(0)
                return
            if self.player.is_playing:
                self.player.pause(); self.btn_play.text = "Play"; self.mini_player.update(playing=False)
            else:
                self.player.resume(); self.btn_play.text = "Pause"; self.mini_player.update(playing=True)

        def stop_music(self):
            self.player.stop(); self.btn_play.text = "Play"
            self.track_label.text = "Stoppet"; self.track_label.color = C_TEXT_DIM
            self.mini_player.update("Stoppet", False)

        def next_track(self):
            if self.tracks: self.play_track((self.current_track+1) % len(self.tracks))
        def prev_track(self):
            if self.tracks: self.play_track((self.current_track-1) % len(self.tracks))
        def _on_vol(self, s, v): self.player.set_volume(v)

        # === AMBIENT ===
        def _play_amb(self, url, name):
            log(f"Playing ambient: {name}")
            self.amb_status.text = f"Laster: {name}..."; self.amb_status.color = C_GOLD_DIM
            ok = self.stream_player.play_url(url)
            if ok:
                Clock.schedule_once(lambda dt: self._upd_amb(name), 6)
            else:
                self.amb_status.text = "Ikke tilgjengelig"; self.amb_status.color = C_BLOOD
        def _upd_amb(self, name):
            if self.stream_player.is_playing:
                self.amb_status.text = f"Spiller: {name}"; self.amb_status.color = C_GREEN
            else:
                self.amb_status.text = f"Feilet: {name}"; self.amb_status.color = C_BLOOD
        def _stop_amb(self):
            self.stream_player.stop(); self.amb_status.text = "Stoppet"; self.amb_status.color = C_TEXT_DIM

        def on_stop(self):
            self.player.stop(); self.stream_player.stop()
            self.media_server.stop(); self.cast_mgr.disconnect()

    log("Starting app...")
    EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())
