import os, sys, traceback, socket, threading, math, time, random
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
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget
    from kivy.uix.stencilview import StencilView
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse, Triangle
    from kivy.graphics import PushMatrix, PopMatrix, Rotate, Scale
    from kivy.animation import Animation
    from kivy.metrics import dp, sp
    from kivy.properties import NumericProperty, ListProperty, BooleanProperty
    log("Kivy imported OK")

    # Chromecast
    CAST_AVAILABLE = False
    try:
        import pychromecast
        CAST_AVAILABLE = True
        log("pychromecast imported OK")
    except ImportError as e:
        log(f"pychromecast not available: {e}")

    # Android MediaPlayer
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
    C_GREEN_GLOW = (0.18, 0.55, 0.35, 0.6)
    C_BLOOD = (0.50, 0.10, 0.10, 1)
    C_TENTACLE = (0.20, 0.12, 0.28, 1)
    C_OCEAN = (0.08, 0.18, 0.25, 1)
    HTTP_PORT = 8089

    # === GRATIS STEMNINGSLYDER (Creative Commons / Public Domain) ===
    AMBIENT_SOUNDS = [
        {"name": "Regn og torden", "url": "https://upload.wikimedia.org/wikipedia/commons/4/4e/Thunderstorm.ogg"},
        {"name": "Havboelger", "url": "https://upload.wikimedia.org/wikipedia/commons/e/e2/Ocean_waves.ogg"},
        {"name": "Nattskog", "url": "https://upload.wikimedia.org/wikipedia/commons/f/f3/Crickets_chirping_at_night.ogg"},
        {"name": "Vind", "url": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Wind_noise.ogg"},
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
                Permission.CHANGE_WIFI_MULTICAST_STATE,
            ])
            log("Permissions requested")
        except Exception as e:
            log(f"Permission request failed: {e}")

    # ============================================================
    #  ELDRITCH ANIMERTE WIDGETS
    # ============================================================

    class EldritchBG(Widget):
        """Animert bakgrunn med sakte pulserende tentakel-moenstre."""
        _time = NumericProperty(0)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.bind(pos=self._draw, size=self._draw)
            Clock.schedule_interval(self._tick, 1/20.0)

        def _tick(self, dt):
            self._time += dt
            self._draw()

        def _draw(self, *args):
            self.canvas.clear()
            w, h = self.size
            x0, y0 = self.pos
            if w < 1 or h < 1:
                return
            with self.canvas:
                # Dyp bakgrunn
                Color(*C_VOID)
                Rectangle(pos=self.pos, size=self.size)
                # Subtile pulserende sirkler (eldritch portaler)
                t = self._time
                for i in range(3):
                    cx = x0 + w * (0.2 + i * 0.3)
                    cy = y0 + h * (0.3 + math.sin(t * 0.3 + i) * 0.1)
                    r = dp(40) + math.sin(t * 0.5 + i * 2) * dp(15)
                    alpha = 0.03 + math.sin(t * 0.4 + i) * 0.015
                    Color(C_TENTACLE[0], C_TENTACLE[1], C_TENTACLE[2], alpha)
                    Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
                # Sakte drivende partikler (elderstøv)
                for i in range(8):
                    seed = i * 137.5
                    px = x0 + (w * ((seed + t * 8) % w)) / w * w
                    py = y0 + (h * ((seed * 2.3 + t * 5) % h)) / h * h
                    alpha = 0.08 + math.sin(t + seed) * 0.04
                    sz = dp(1.5) + math.sin(t * 0.7 + seed) * dp(0.5)
                    Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], alpha)
                    Ellipse(pos=(px, py), size=(sz, sz))

    class ElderSign(Widget):
        """Tegner et animert Elder Sign-symbol."""
        _glow = NumericProperty(0.3)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.size_hint = (None, None)
            self.size = (dp(30), dp(30))
            self._animate()
            self.bind(pos=self._draw, size=self._draw)

        def _animate(self):
            a = Animation(_glow=0.7, duration=2) + Animation(_glow=0.3, duration=2)
            a.bind(on_progress=lambda *x: self._draw())
            a.bind(on_complete=lambda *x: self._animate())
            a.start(self)

        def _draw(self, *args):
            self.canvas.clear()
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            r = min(self.width, self.height) / 2.5
            with self.canvas:
                # Ytre sirkel
                Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], self._glow * 0.5)
                Line(circle=(cx, cy, r), width=dp(1))
                # Stjerneform (forenklet elder sign)
                Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], self._glow)
                for j in range(5):
                    angle = math.radians(j * 72 - 90)
                    x1 = cx + r * 0.9 * math.cos(angle)
                    y1 = cy + r * 0.9 * math.sin(angle)
                    angle2 = math.radians((j + 2) * 72 - 90)
                    x2 = cx + r * 0.9 * math.cos(angle2)
                    y2 = cy + r * 0.9 * math.sin(angle2)
                    Line(points=[x1, y1, x2, y2], width=dp(0.8))
                # Senterprikk
                Color(C_GOLD_BRIGHT[0], C_GOLD_BRIGHT[1], C_GOLD_BRIGHT[2], self._glow)
                Ellipse(pos=(cx - dp(2), cy - dp(2)), size=(dp(4), dp(4)))

    class GoldDivider(Widget):
        """Ornamental gull-skillelinje med elder signs."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.size_hint_y = None
            self.height = dp(12)
            self.bind(pos=self._draw, size=self._draw)
            Clock.schedule_once(lambda dt: self._draw(), 0)

        def _draw(self, *args):
            self.canvas.clear()
            w = self.width
            cx = self.x + w / 2
            cy = self.y + self.height / 2
            with self.canvas:
                # Fade linje venstre
                Color(*C_GOLD_DIM, 0.3)
                Rectangle(pos=(self.x + w * 0.05, cy), size=(w * 0.35, dp(1)))
                # Fade linje hoeyre
                Rectangle(pos=(self.x + w * 0.6, cy), size=(w * 0.35, dp(1)))
                # Sentral lys linje
                Color(*C_GOLD, 0.5)
                Rectangle(pos=(self.x + w * 0.2, cy), size=(w * 0.6, dp(1)))
                # Diamant i midten
                Color(*C_GOLD, 0.7)
                d = dp(4)
                Triangle(points=[cx, cy + d, cx - d, cy, cx, cy - d])
                Triangle(points=[cx, cy + d, cx + d, cy, cx, cy - d])

    class PulsingOrb(Widget):
        """Pulserende kule med glow-effekt."""
        _pulse = NumericProperty(0.4)

        def __init__(self, color=C_GOLD, **kwargs):
            super().__init__(**kwargs)
            self.size_hint = (None, None)
            self.size = (dp(14), dp(14))
            self._color = color
            self._active = False
            self.bind(pos=self._draw, size=self._draw)

        def start(self):
            self._active = True
            self._do_pulse()

        def stop(self):
            self._active = False
            Animation.cancel_all(self, '_pulse')
            self._pulse = 0.2
            self._draw()

        def _do_pulse(self):
            if not self._active:
                return
            a = Animation(_pulse=1.0, duration=1.2, t='in_out_sine')
            a += Animation(_pulse=0.3, duration=1.2, t='in_out_sine')
            a.bind(on_progress=lambda *x: self._draw())
            a.bind(on_complete=lambda *x: self._do_pulse())
            a.start(self)

        def _draw(self, *args):
            self.canvas.clear()
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            with self.canvas:
                # Ytre glow
                Color(self._color[0], self._color[1], self._color[2], self._pulse * 0.15)
                r_outer = self.width * 0.9
                Ellipse(pos=(cx - r_outer, cy - r_outer), size=(r_outer * 2, r_outer * 2))
                # Indre kule
                Color(self._color[0], self._color[1], self._color[2], self._pulse * 0.8)
                r_inner = self.width * 0.3
                Ellipse(pos=(cx - r_inner, cy - r_inner), size=(r_inner * 2, r_inner * 2))

    class ElButton(Button):
        """Stilisert knapp med gull-detaljer og trykk-animasjon."""
        _border_alpha = NumericProperty(0.25)

        def __init__(self, accent=False, danger=False, **kwargs):
            super().__init__(**kwargs)
            self.background_normal = ''
            self.background_down = ''
            self.background_color = (0, 0, 0, 0)
            self._accent = accent
            self._danger = danger
            if accent:
                self.color = C_GOLD
            elif danger:
                self.color = (0.8, 0.3, 0.3, 1)
            else:
                self.color = C_TEXT
            self.bold = True
            self.font_size = sp(14)
            self.bind(pos=self._draw, size=self._draw, state=self._on_state)
            Clock.schedule_once(lambda dt: self._draw(), 0)

        def _on_state(self, *args):
            if self.state == 'down':
                Animation(_border_alpha=0.8, duration=0.1).start(self)
            else:
                Animation(_border_alpha=0.25, duration=0.3).start(self)
            self.bind(_border_alpha=lambda *a: self._draw())

        def _draw(self, *args):
            self.canvas.before.clear()
            with self.canvas.before:
                if self.state == 'down':
                    Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], 0.1)
                else:
                    Color(*C_SURFACE)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
                bc = C_GOLD if self._accent else (C_BLOOD if self._danger else C_GOLD_DIM)
                Color(bc[0], bc[1], bc[2], self._border_alpha)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(5)),
                     width=dp(0.8))

    class ElTab(ToggleButton):
        """Stor fane-knapp med animert indikator."""
        _bar_width = NumericProperty(0)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.background_normal = ''
            self.background_down = ''
            self.background_color = (0, 0, 0, 0)
            self.color = C_TEXT_DIM
            self.bold = True
            self.font_size = sp(15)
            self.bind(pos=self._draw, size=self._draw, state=self._on_state)
            Clock.schedule_once(lambda dt: self._on_state(), 0)

        def _on_state(self, *args):
            if self.state == 'down':
                self.color = C_GOLD
                Animation(_bar_width=self.width * 0.5, duration=0.3, t='out_cubic').start(self)
            else:
                self.color = C_TEXT_DIM
                Animation(_bar_width=0, duration=0.2, t='in_cubic').start(self)
            self.bind(_bar_width=lambda *a: self._draw())

        def _draw(self, *args):
            self.canvas.after.clear()
            with self.canvas.after:
                if self._bar_width > 1:
                    bx = self.x + (self.width - self._bar_width) / 2
                    # Glow
                    Color(C_GOLD[0], C_GOLD[1], C_GOLD[2], 0.15)
                    RoundedRectangle(pos=(bx - dp(4), self.y),
                                    size=(self._bar_width + dp(8), dp(6)),
                                    radius=[dp(3)])
                    # Linje
                    Color(*C_GOLD, 0.85)
                    RoundedRectangle(pos=(bx, self.y + dp(1)),
                                    size=(self._bar_width, dp(3)),
                                    radius=[dp(1.5)])

    class ImageCard(RelativeLayout):
        """Miniatyrbilde-kort med ramme og trykk-effekt."""
        def __init__(self, image_path, on_tap=None, on_long=None, **kwargs):
            super().__init__(**kwargs)
            self.size_hint_y = None
            self.height = dp(110)
            self.image_path = image_path
            self._on_tap = on_tap

            # Bakgrunn
            with self.canvas.before:
                Color(*C_SURFACE)
                self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
                Color(*C_GOLD_DIM, 0.2)
                self._border = Line(rounded_rectangle=(0, 0, 10, 10, dp(6)), width=dp(0.6))
            self.bind(pos=self._update_bg, size=self._update_bg)

            # Bilde
            self.img = Image(source=image_path, allow_stretch=True, keep_ratio=True,
                           pos_hint={'center_x': 0.5, 'center_y': 0.55},
                           size_hint=(0.9, 0.7))
            self.add_widget(self.img)

            # Filnavn
            fname = os.path.basename(image_path)
            short = fname[:14] + ".." if len(fname) > 14 else fname
            self.label = Label(text=short, font_size=sp(10), color=C_TEXT_DIM,
                             pos_hint={'center_x': 0.5, 'y': 0.02},
                             size_hint=(1, 0.2))
            self.add_widget(self.label)

            # Usynlig knapp for trykk
            btn = Button(background_color=(0, 0, 0, 0), background_normal='',
                        pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
            btn.bind(on_release=self._tapped)
            self.add_widget(btn)

        def _update_bg(self, *args):
            self._bg.pos = self.pos
            self._bg.size = self.size
            self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(6))

        def _tapped(self, *args):
            # Kort glow-animasjon
            if self._on_tap:
                self._on_tap(self.image_path)

    # ============================================================
    #  MINI-PLAYER (synlig paa alle faner)
    # ============================================================
    class MiniPlayer(BoxLayout):
        """Kompakt musikkontroll som vises nederst paa alle faner."""
        def __init__(self, app_ref, **kwargs):
            super().__init__(**kwargs)
            self.app = app_ref
            self.orientation = 'horizontal'
            self.size_hint_y = None
            self.height = dp(48)
            self.padding = [dp(10), dp(4)]
            self.spacing = dp(8)

            self.bind(pos=self._draw_bg, size=self._draw_bg)

            # Spor-info
            self.track_lbl = Label(text="Ingen musikk", font_size=sp(12),
                                  color=C_TEXT_DIM, size_hint_x=0.5,
                                  halign='left', shorten=True, shorten_from='right')
            self.track_lbl.bind(size=self.track_lbl.setter('text_size'))
            self.add_widget(self.track_lbl)

            # Kontroller
            for txt, cb in [("Forr", self._prev), ("Play", self._toggle),
                           ("Neste", self._next)]:
                b = Button(text=txt, font_size=sp(11), bold=True, size_hint_x=None,
                          width=dp(52), background_normal='', background_color=(0, 0, 0, 0),
                          color=C_GOLD if txt == "Play" else C_TEXT_DIM)
                b.bind(on_release=lambda x, f=cb: f())
                self.add_widget(b)
                if txt == "Play":
                    self.btn_play = b

            # Orb
            self.orb = PulsingOrb(color=C_GREEN)
            self.add_widget(self.orb)

        def _draw_bg(self, *args):
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
            if playing:
                self.orb.start()
            else:
                self.orb.stop()

        def _toggle(self):
            self.app.toggle_play()

        def _next(self):
            self.app.next_track()

        def _prev(self):
            self.app.prev_track()

    # ============================================================
    #  HTTP SERVER
    # ============================================================
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

    class MediaServer:
        def __init__(self, directory, port=HTTP_PORT):
            self.directory = directory
            self.port = port
            self._httpd = None

        def start(self):
            if self._httpd:
                return
            try:
                handler = partial(QuietHandler, directory=self.directory)
                self._httpd = HTTPServer(('0.0.0.0', self.port), handler)
                t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
                t.start()
                log(f"HTTP server started on port {self.port}")
            except Exception as e:
                log(f"HTTP server failed: {e}")

        def stop(self):
            if self._httpd:
                self._httpd.shutdown()
                self._httpd = None

        @staticmethod
        def get_local_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"

        def get_url(self, filepath):
            rel = os.path.relpath(filepath, self.directory)
            ip = self.get_local_ip()
            return f"http://{ip}:{self.port}/{rel}"

    # ============================================================
    #  CAST MANAGER
    # ============================================================
    class CastManager:
        def __init__(self):
            self.devices = {}
            self.active_cast = None
            self.mc = None
            self._browser = None
            self._scanning = False

        def discover(self, callback=None):
            if not CAST_AVAILABLE or self._scanning:
                return
            self._scanning = True
            self.devices = {}
            def _scan():
                try:
                    chromecasts, browser = pychromecast.get_chromecasts()
                    self._browser = browser
                    for cc in chromecasts:
                        self.devices[cc.cast_info.friendly_name] = cc
                except Exception as e:
                    log(f"Cast scan error: {e}")
                finally:
                    self._scanning = False
                    if callback:
                        Clock.schedule_once(lambda dt: callback(list(self.devices.keys())), 0)
            threading.Thread(target=_scan, daemon=True).start()

        def connect(self, name, callback=None):
            if name not in self.devices:
                return
            def _connect():
                try:
                    cc = self.devices[name]
                    cc.wait()
                    self.active_cast = cc
                    self.mc = cc.media_controller
                    if callback:
                        Clock.schedule_once(lambda dt: callback(True), 0)
                except Exception as e:
                    log(f"Cast connect error: {e}")
                    if callback:
                        Clock.schedule_once(lambda dt: callback(False), 0)
            threading.Thread(target=_connect, daemon=True).start()

        def cast_image(self, url, callback=None):
            if not self.mc:
                return
            def _cast():
                try:
                    self.mc.play_media(url, 'image/jpeg')
                    self.mc.block_until_active()
                    if callback:
                        Clock.schedule_once(lambda dt: callback(True), 0)
                except Exception as e:
                    log(f"Cast image error: {e}")
                    if callback:
                        Clock.schedule_once(lambda dt: callback(False), 0)
            threading.Thread(target=_cast, daemon=True).start()

        def disconnect(self):
            try:
                if self._browser:
                    self._browser.stop_discovery()
                if self.active_cast:
                    self.active_cast.disconnect()
            except Exception:
                pass
            self.active_cast = None
            self.mc = None

    # ============================================================
    #  LYDSPILLERE
    # ============================================================
    class AndroidPlayer:
        def __init__(self):
            self.mp = None
            self.is_playing = False
            self._volume = 0.7

        def play(self, path):
            self.stop()
            try:
                self.mp = MediaPlayer()
                self.mp.setDataSource(path)
                self.mp.setVolume(self._volume, self._volume)
                self.mp.prepare()
                self.mp.start()
                self.is_playing = True
            except Exception as e:
                log(f"AndroidPlayer error: {e}")
                self.mp = None
                self.is_playing = False

        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying():
                        self.mp.stop()
                    self.mp.release()
                except Exception:
                    pass
                self.mp = None
            self.is_playing = False

        def pause(self):
            if self.mp and self.is_playing:
                try:
                    self.mp.pause()
                    self.is_playing = False
                except Exception:
                    pass

        def resume(self):
            if self.mp and not self.is_playing:
                try:
                    self.mp.start()
                    self.is_playing = True
                except Exception:
                    pass

        def set_volume(self, vol):
            self._volume = vol
            if self.mp:
                try:
                    self.mp.setVolume(vol, vol)
                except Exception:
                    pass

    class StreamPlayer:
        """Spiller for nettstreaming av lyd."""
        def __init__(self):
            self.mp = None
            self.is_playing = False
            self._volume = 0.5

        def play_url(self, url):
            self.stop()
            if not USE_JNIUS:
                log("StreamPlayer: no jnius, cannot stream")
                return False
            try:
                self.mp = MediaPlayer()
                self.mp.setDataSource(url)
                self.mp.setVolume(self._volume, self._volume)
                self.mp.prepareAsync()
                # Vent paa prepare (enkel polling)
                def _check(dt):
                    try:
                        if self.mp and not self.is_playing:
                            self.mp.start()
                            self.is_playing = True
                            log(f"StreamPlayer: streaming {url}")
                    except Exception:
                        pass
                Clock.schedule_once(_check, 3)
                return True
            except Exception as e:
                log(f"StreamPlayer error: {e}")
                return False

        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying():
                        self.mp.stop()
                    self.mp.release()
                except Exception:
                    pass
                self.mp = None
            self.is_playing = False

        def set_volume(self, vol):
            self._volume = vol
            if self.mp:
                try:
                    self.mp.setVolume(vol, vol)
                except Exception:
                    pass

    class FallbackPlayer:
        def __init__(self):
            from kivy.core.audio import SoundLoader
            self.SoundLoader = SoundLoader
            self.sound = None
            self.is_playing = False
            self._volume = 0.7

        def play(self, path):
            self.stop()
            try:
                self.sound = self.SoundLoader.load(path)
                if self.sound:
                    self.sound.volume = self._volume
                    self.sound.play()
                    self.is_playing = True
            except Exception:
                pass

        def stop(self):
            if self.sound:
                try:
                    self.sound.stop()
                except Exception:
                    pass
                self.sound = None
            self.is_playing = False

        def pause(self):
            if self.sound and self.is_playing:
                self.sound.stop()
                self.is_playing = False

        def resume(self):
            if self.sound and not self.is_playing:
                self.sound.play()
                self.is_playing = True

        def set_volume(self, vol):
            self._volume = vol
            if self.sound:
                self.sound.volume = vol

    # ============================================================
    #  HOVEDAPP
    # ============================================================
    class EldritchApp(App):
        def build(self):
            log("build() called")
            Window.clearcolor = C_VOID
            self.title = "Eldritch Portal"
            self.tracks = []
            self.current_track = -1
            self.selected_image = None
            self.auto_cast = True  # Cast ved trykk paa bilde

            if USE_JNIUS:
                self.player = AndroidPlayer()
            else:
                self.player = FallbackPlayer()
            self.stream_player = StreamPlayer()
            self.cast_mgr = CastManager()
            self.media_server = MediaServer(
                directory="/sdcard/Documents/EldritchPortal", port=HTTP_PORT)

            # === ROOT ===
            root = FloatLayout()

            # Animert bakgrunn
            self.bg = EldritchBG(pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
            root.add_widget(self.bg)

            # Hovedinnhold over bakgrunnen
            main = BoxLayout(orientation='vertical', spacing=0,
                           pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))

            # === TOPPSEKSJON ===
            top = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(105))

            # Tittelrad
            title_row = BoxLayout(size_hint_y=None, height=dp(44), padding=[dp(12), dp(6)])
            sign = ElderSign()
            title_row.add_widget(sign)
            title_row.add_widget(Widget(size_hint_x=None, width=dp(8)))
            title_row.add_widget(Label(text="ELDRITCH PORTAL", font_size=sp(19),
                                      color=C_GOLD, bold=True, size_hint_x=0.7, halign='left'))
            self.top_orb = PulsingOrb(color=C_GOLD)
            orb_box = BoxLayout(size_hint_x=None, width=dp(30))
            orb_box.add_widget(self.top_orb)
            title_row.add_widget(orb_box)
            top.add_widget(title_row)

            # Faner
            tab_bar = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(2),
                              padding=[dp(8), 0])
            self.tab_img = ElTab(text="Bilder", group='tabs', state='down')
            self.tab_mus = ElTab(text="Musikk", group='tabs')
            self.tab_amb = ElTab(text="Ambient", group='tabs')
            self.tab_cast = ElTab(text="Cast", group='tabs')
            self.tab_img.bind(on_release=lambda x: self.show_tab('images'))
            self.tab_mus.bind(on_release=lambda x: self.show_tab('music'))
            self.tab_amb.bind(on_release=lambda x: self.show_tab('ambient'))
            self.tab_cast.bind(on_release=lambda x: self.show_tab('cast'))
            tab_bar.add_widget(self.tab_img)
            tab_bar.add_widget(self.tab_mus)
            tab_bar.add_widget(self.tab_amb)
            tab_bar.add_widget(self.tab_cast)
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

            # === BUNNLINJE ===
            main.add_widget(GoldDivider())
            self.status = Label(text="", font_size=sp(10), color=C_TEXT_DIM,
                              size_hint_y=None, height=dp(22), halign='center')
            self.status.bind(size=self.status.setter('text_size'))
            main.add_widget(self.status)

            root.add_widget(main)

            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init_content(), 3)
            return root

        # --- PANELER ---
        def _build_image_panel(self):
            panel = BoxLayout(orientation='vertical', spacing=dp(6))

            # Forhåndsvisning
            self.preview = Image(size_hint_y=0.4, allow_stretch=True, keep_ratio=True)
            panel.add_widget(self.preview)

            self.img_info = Label(text="Trykk paa et bilde for aa vise og caste",
                                font_size=sp(12), color=C_TEXT_DIM, size_hint_y=None,
                                height=dp(22), halign='center')
            self.img_info.bind(size=self.img_info.setter('text_size'))
            panel.add_widget(self.img_info)

            # Knapper
            btn_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6),
                              padding=[dp(4), 0])
            self.btn_auto_cast = ElButton(text="Auto-Cast: PÅ", accent=True, size_hint_x=0.5)
            self.btn_auto_cast.bind(on_release=lambda x: self._toggle_auto_cast())
            btn_row.add_widget(self.btn_auto_cast)
            btn_refresh = ElButton(text="Oppdater", size_hint_x=0.5)
            btn_refresh.bind(on_release=lambda x: self.load_images())
            btn_row.add_widget(btn_refresh)
            panel.add_widget(btn_row)

            # Galleri med miniatyrbilder
            scroll = ScrollView(size_hint_y=0.4)
            self.img_grid = GridLayout(cols=3, spacing=dp(6), padding=dp(4), size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid)
            panel.add_widget(scroll)
            return panel

        def _build_music_panel(self):
            panel = BoxLayout(orientation='vertical', spacing=dp(6))

            # Naavarande spor
            self.track_label = Label(text="Velg et spor", font_size=sp(16),
                                   color=C_TEXT_DIM, size_hint_y=None, height=dp(40),
                                   halign='center', bold=True)
            self.track_label.bind(size=self.track_label.setter('text_size'))
            panel.add_widget(self.track_label)

            # Kontroller
            controls = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6),
                               padding=[dp(8), 0])
            for txt, cb in [("Forr", self.prev_track), ("Play", self.toggle_play),
                           ("Neste", self.next_track), ("Stopp", self.stop_music)]:
                b = ElButton(text=txt, accent=(txt == "Play"))
                b.bind(on_release=lambda x, f=cb: f())
                controls.add_widget(b)
                if txt == "Play":
                    self.btn_play = b
            panel.add_widget(controls)

            # Volum
            vol_row = BoxLayout(size_hint_y=None, height=dp(36), padding=[dp(12), 0])
            vol_row.add_widget(Label(text="Vol:", color=C_TEXT_DIM, size_hint_x=0.1,
                                    font_size=sp(12)))
            self.vol_slider = Slider(min=0, max=1, value=0.7, size_hint_x=0.9)
            self.vol_slider.bind(value=self._on_volume)
            vol_row.add_widget(self.vol_slider)
            panel.add_widget(vol_row)

            panel.add_widget(GoldDivider())

            # Sporliste
            scroll = ScrollView(size_hint_y=1)
            self.track_grid = GridLayout(cols=1, spacing=dp(3), padding=dp(4), size_hint_y=None)
            self.track_grid.bind(minimum_height=self.track_grid.setter('height'))
            scroll.add_widget(self.track_grid)
            panel.add_widget(scroll)
            return panel

        def _build_ambient_panel(self):
            panel = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(4))

            panel.add_widget(Label(text="Stemningslyder", font_size=sp(18),
                                  color=C_GOLD, bold=True, size_hint_y=None, height=dp(35)))
            panel.add_widget(Label(text="Gratis lyder fra nettet", font_size=sp(11),
                                  color=C_TEXT_DIM, size_hint_y=None, height=dp(20)))

            # Forhåndsdefinerte lyder
            scroll = ScrollView(size_hint_y=0.5)
            amb_grid = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            amb_grid.bind(minimum_height=amb_grid.setter('height'))

            for snd in AMBIENT_SOUNDS:
                row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
                btn = ElButton(text=snd['name'], size_hint_x=0.7)
                btn.bind(on_release=lambda x, u=snd['url'], n=snd['name']: self._play_ambient(u, n))
                row.add_widget(btn)
                amb_grid.add_widget(row)

            scroll.add_widget(amb_grid)
            panel.add_widget(scroll)

            panel.add_widget(GoldDivider())

            # Stopp ambient
            btn_stop = ElButton(text="Stopp ambient", danger=True,
                               size_hint_y=None, height=dp(44))
            btn_stop.bind(on_release=lambda x: self._stop_ambient())
            panel.add_widget(btn_stop)

            # Ambient volum
            avol_row = BoxLayout(size_hint_y=None, height=dp(36), padding=[dp(12), 0])
            avol_row.add_widget(Label(text="Vol:", color=C_TEXT_DIM, size_hint_x=0.1,
                                     font_size=sp(12)))
            self.amb_vol = Slider(min=0, max=1, value=0.5, size_hint_x=0.9)
            self.amb_vol.bind(value=lambda s, v: self.stream_player.set_volume(v))
            avol_row.add_widget(self.amb_vol)
            panel.add_widget(avol_row)

            # Status
            self.amb_status = Label(text="", font_size=sp(12), color=C_TEXT_DIM,
                                  size_hint_y=None, height=dp(25))
            panel.add_widget(self.amb_status)

            panel.add_widget(Widget(size_hint_y=1))
            return panel

        def _build_cast_panel(self):
            panel = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(8))

            if not CAST_AVAILABLE:
                self.cast_status = Label(text="Casting utilgjengelig\npychromecast mangler",
                    font_size=sp(14), halign='center', color=C_TEXT_DIM)
                self.cast_status.bind(size=self.cast_status.setter('text_size'))
                panel.add_widget(self.cast_status)
                panel.add_widget(Widget(size_hint_y=1))
                return panel

            self.cast_status = Label(text="Ikke tilkoblet", font_size=sp(14),
                                   halign='center', color=C_TEXT_DIM, size_hint_y=None,
                                   height=dp(35))
            self.cast_status.bind(size=self.cast_status.setter('text_size'))
            panel.add_widget(self.cast_status)

            self.cast_orb = PulsingOrb(color=C_GOLD)
            orb_row = BoxLayout(size_hint_y=None, height=dp(20))
            orb_row.add_widget(Widget())
            orb_row.add_widget(self.cast_orb)
            orb_row.add_widget(Widget())
            panel.add_widget(orb_row)

            btn_scan = ElButton(text="Sok etter enheter", accent=True,
                               size_hint_y=None, height=dp(48))
            btn_scan.bind(on_release=lambda x: self._scan_cast())
            panel.add_widget(btn_scan)

            self.cast_spinner = Spinner(text="Velg enhet...", values=[],
                size_hint_y=None, height=dp(48),
                background_color=C_SURFACE, color=C_TEXT)
            panel.add_widget(self.cast_spinner)

            btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            btn_connect = ElButton(text="Koble til", accent=True, size_hint_x=0.5)
            btn_connect.bind(on_release=lambda x: self._connect_cast())
            btn_row.add_widget(btn_connect)
            btn_disconnect = ElButton(text="Koble fra", danger=True, size_hint_x=0.5)
            btn_disconnect.bind(on_release=lambda x: self._disconnect_cast())
            btn_row.add_widget(btn_disconnect)
            panel.add_widget(btn_row)

            panel.add_widget(Widget(size_hint_y=1))
            return panel

        def _init_content(self):
            self.media_server.start()
            self.load_images()
            self.load_tracks()
            ip = MediaServer.get_local_ip()
            self.status.text = f"IP: {ip}  |  Cast: {'Klar' if CAST_AVAILABLE else 'Nei'}"
            self.top_orb.start()

        def show_tab(self, tab):
            self.content.clear_widgets()
            panels = {
                'images': self.img_panel,
                'music': self.mus_panel,
                'ambient': self.amb_panel,
                'cast': self.cast_panel,
            }
            if tab in panels:
                self.content.add_widget(panels[tab])

        # === BILDER ===
        def load_images(self):
            log("load_images()")
            self.img_grid.clear_widgets()
            try:
                if not os.path.exists(IMG_DIR):
                    return
                filer = sorted([f for f in os.listdir(IMG_DIR)
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
                self.img_info.text = f"{len(filer)} bilder - trykk for aa vise"
                for fname in filer:
                    path = os.path.join(IMG_DIR, fname)
                    card = ImageCard(image_path=path, on_tap=self.select_image)
                    self.img_grid.add_widget(card)
            except Exception as e:
                log(f"load_images error: {e}")

        def select_image(self, path):
            log(f"Selected image: {path}")
            try:
                self.preview.source = path
                self.selected_image = path
                self.img_info.text = os.path.basename(path)
                self.img_info.color = C_GOLD

                # Auto-cast hvis aktivert og tilkoblet
                if self.auto_cast and self.cast_mgr.active_cast:
                    url = self.media_server.get_url(path)
                    self.img_info.text = f"Caster {os.path.basename(path)}..."
                    self.cast_mgr.cast_image(url, callback=self._on_cast_result)
            except Exception as e:
                log(f"select error: {e}")

        def _toggle_auto_cast(self):
            self.auto_cast = not self.auto_cast
            self.btn_auto_cast.text = f"Auto-Cast: {'PA' if self.auto_cast else 'AV'}"
            self.btn_auto_cast._accent = self.auto_cast
            self.btn_auto_cast.color = C_GOLD if self.auto_cast else C_TEXT_DIM

        def _on_cast_result(self, success):
            if success:
                self.img_info.text = f"Castet: {os.path.basename(self.selected_image)}"
                self.img_info.color = C_GOLD
            else:
                self.img_info.text = "Casting feilet"
                self.img_info.color = C_BLOOD

        # === CAST ===
        def _scan_cast(self):
            if not CAST_AVAILABLE:
                return
            self.cast_status.text = "Soker..."
            self.cast_status.color = C_GOLD_DIM
            self.cast_orb.start()
            self.cast_mgr.discover(callback=self._on_devices_found)

        def _on_devices_found(self, names):
            self.cast_orb.stop()
            if names:
                self.cast_spinner.values = names
                self.cast_spinner.text = names[0]
                self.cast_status.text = f"Fant {len(names)} enhet(er)"
                self.cast_status.color = C_GOLD
            else:
                self.cast_status.text = "Ingen enheter funnet"
                self.cast_status.color = C_TEXT_DIM

        def _connect_cast(self):
            if not CAST_AVAILABLE:
                return
            name = self.cast_spinner.text
            if not name or name == "Velg enhet...":
                return
            self.cast_status.text = f"Kobler til {name}..."
            self.cast_orb.start()
            self.cast_mgr.connect(name, callback=self._on_connected)

        def _on_connected(self, success):
            if success:
                self.cast_status.text = f"Tilkoblet: {self.cast_spinner.text}"
                self.cast_status.color = C_GOLD
                self.cast_orb.start()
            else:
                self.cast_status.text = "Tilkobling feilet"
                self.cast_status.color = C_BLOOD
                self.cast_orb.stop()

        def _disconnect_cast(self):
            self.cast_mgr.disconnect()
            self.cast_status.text = "Frakoblet"
            self.cast_status.color = C_TEXT_DIM
            self.cast_orb.stop()

        # === MUSIKK ===
        def load_tracks(self):
            log("load_tracks()")
            self.track_grid.clear_widgets()
            self.tracks = []
            try:
                if not os.path.exists(MUSIC_DIR):
                    return
                filer = sorted([f for f in os.listdir(MUSIC_DIR)
                               if f.lower().endswith(('.mp3', '.ogg', '.wav', '.flac'))])
                self.track_label.text = f"{len(filer)} spor"
                for i, fname in enumerate(filer):
                    self.tracks.append(os.path.join(MUSIC_DIR, fname))
                    btn = ElButton(text=fname, size_hint_y=None, height=dp(46))
                    btn.font_size = sp(12)
                    btn.halign = 'left'
                    btn.bind(size=btn.setter('text_size'))
                    btn.bind(on_release=lambda x, idx=i: self.play_track(idx))
                    self.track_grid.add_widget(btn)
            except Exception as e:
                log(f"load_tracks error: {e}")

        def play_track(self, idx):
            if idx < 0 or idx >= len(self.tracks):
                return
            self.current_track = idx
            path = self.tracks[idx]
            self.player.play(path)
            name = os.path.basename(path)
            if self.player.is_playing:
                self.btn_play.text = "Pause"
                self.track_label.text = f"Spiller: {name}"
                self.track_label.color = C_GOLD
                self.mini_player.update(name, True)
            else:
                self.track_label.text = "Kunne ikke spille"
                self.mini_player.update("Feil", False)

        def toggle_play(self):
            if not self.player.is_playing and self.current_track < 0:
                if self.tracks:
                    self.play_track(0)
                return
            if self.player.is_playing:
                self.player.pause()
                self.btn_play.text = "Play"
                self.mini_player.update(playing=False)
            else:
                self.player.resume()
                self.btn_play.text = "Pause"
                self.mini_player.update(playing=True)

        def stop_music(self):
            self.player.stop()
            self.btn_play.text = "Play"
            self.track_label.text = "Stoppet"
            self.track_label.color = C_TEXT_DIM
            self.mini_player.update("Stoppet", False)

        def next_track(self):
            if self.tracks:
                self.play_track((self.current_track + 1) % len(self.tracks))

        def prev_track(self):
            if self.tracks:
                self.play_track((self.current_track - 1) % len(self.tracks))

        def _on_volume(self, slider, value):
            self.player.set_volume(value)

        # === AMBIENT ===
        def _play_ambient(self, url, name):
            log(f"Playing ambient: {name} - {url}")
            self.amb_status.text = f"Starter: {name}..."
            self.amb_status.color = C_GOLD_DIM
            ok = self.stream_player.play_url(url)
            if ok:
                Clock.schedule_once(lambda dt: self._update_amb_status(name), 4)
            else:
                self.amb_status.text = "Streaming ikke tilgjengelig"
                self.amb_status.color = C_BLOOD

        def _update_amb_status(self, name):
            if self.stream_player.is_playing:
                self.amb_status.text = f"Spiller: {name}"
                self.amb_status.color = C_GREEN
            else:
                self.amb_status.text = f"Laster: {name}..."

        def _stop_ambient(self):
            self.stream_player.stop()
            self.amb_status.text = "Stoppet"
            self.amb_status.color = C_TEXT_DIM

        def on_stop(self):
            self.player.stop()
            self.stream_player.stop()
            self.media_server.stop()
            self.cast_mgr.disconnect()

    log("Starting app...")
    EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())
