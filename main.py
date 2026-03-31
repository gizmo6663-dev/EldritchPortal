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
    from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
    from kivy.animation import Animation
    from kivy.metrics import dp, sp
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
    CLR_VOID = (0.04, 0.04, 0.06, 1)        # dypeste bakgrunn
    CLR_DEEP = (0.07, 0.07, 0.10, 1)        # panel-bakgrunn
    CLR_SURFACE = (0.10, 0.11, 0.14, 1)     # kort/knapp-bakgrunn
    CLR_ELEVATED = (0.14, 0.15, 0.19, 1)    # hevet element
    CLR_GOLD = (0.82, 0.68, 0.21, 1)        # gull-aksent
    CLR_GOLD_DIM = (0.55, 0.45, 0.15, 1)    # dempet gull
    CLR_GOLD_GLOW = (0.95, 0.85, 0.35, 0.3) # gull-glow
    CLR_TEXT = (0.78, 0.75, 0.68, 1)         # hovedtekst
    CLR_TEXT_DIM = (0.50, 0.48, 0.42, 1)     # dempet tekst
    CLR_ELDRITCH = (0.15, 0.35, 0.25, 1)    # mystisk groenn
    CLR_BLOOD = (0.45, 0.12, 0.12, 1)       # moerk roed
    CLR_TENTACLE = (0.25, 0.18, 0.30, 1)    # mork lilla
    HTTP_PORT = 8089

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
    #  STILISERTE WIDGETS
    # ============================================================

    class ElGoldLine(Widget):
        """Horisontal gull-linje med fade paa endene."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.size_hint_y = None
            self.height = dp(2)
            self.bind(pos=self._draw, size=self._draw)
            Clock.schedule_once(lambda dt: self._draw(), 0)

        def _draw(self, *args):
            self.canvas.clear()
            with self.canvas:
                Color(*CLR_GOLD_DIM)
                Rectangle(pos=(self.x + self.width * 0.15, self.y),
                         size=(self.width * 0.7, dp(1)))
                Color(*CLR_GOLD, 0.6)
                Rectangle(pos=(self.x + self.width * 0.3, self.y),
                         size=(self.width * 0.4, dp(1)))

    class ElButton(Button):
        """Stilisert knapp med gull-kantlinje."""
        def __init__(self, accent=False, **kwargs):
            super().__init__(**kwargs)
            self.background_normal = ''
            self.background_down = ''
            self.background_color = (0, 0, 0, 0)
            self.color = CLR_GOLD if accent else CLR_TEXT
            self.bold = True
            self.font_size = sp(15)
            self._accent = accent
            self._base_color = CLR_GOLD if accent else CLR_TEXT
            self.bind(pos=self._draw, size=self._draw, state=self._draw)
            Clock.schedule_once(lambda dt: self._draw(), 0)

        def _draw(self, *args):
            self.canvas.before.clear()
            with self.canvas.before:
                # Bakgrunn
                if self.state == 'down':
                    Color(CLR_GOLD[0], CLR_GOLD[1], CLR_GOLD[2], 0.15)
                else:
                    Color(*CLR_SURFACE)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
                # Kantlinje
                if self._accent or self.state == 'down':
                    Color(*CLR_GOLD, 0.5)
                else:
                    Color(*CLR_GOLD_DIM, 0.3)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(6)),
                     width=dp(1))

    class ElTab(ToggleButton):
        """Fane-knapp med animert understreking."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.background_normal = ''
            self.background_down = ''
            self.background_color = (0, 0, 0, 0)
            self.color = CLR_TEXT_DIM
            self.bold = True
            self.font_size = sp(16)
            self._indicator_alpha = 0
            self.bind(pos=self._draw, size=self._draw, state=self._on_state)
            Clock.schedule_once(lambda dt: self._on_state(), 0)

        def _on_state(self, *args):
            if self.state == 'down':
                self.color = CLR_GOLD
                anim = Animation(_indicator_alpha=1, duration=0.3)
                anim.bind(on_progress=lambda *a: self._draw())
                anim.start(self)
            else:
                self.color = CLR_TEXT_DIM
                anim = Animation(_indicator_alpha=0, duration=0.3)
                anim.bind(on_progress=lambda *a: self._draw())
                anim.start(self)

        def _draw(self, *args):
            self.canvas.after.clear()
            with self.canvas.after:
                # Animert gull-linje under aktiv fane
                Color(CLR_GOLD[0], CLR_GOLD[1], CLR_GOLD[2], self._indicator_alpha * 0.9)
                bar_w = self.width * 0.6
                bar_x = self.x + (self.width - bar_w) / 2
                RoundedRectangle(pos=(bar_x, self.y + dp(2)),
                                size=(bar_w, dp(3)),
                                radius=[dp(1.5)])
                # Subtil glow
                Color(CLR_GOLD[0], CLR_GOLD[1], CLR_GOLD[2], self._indicator_alpha * 0.08)
                Rectangle(pos=self.pos, size=self.size)

    class ElHeader(Label):
        """Overskrift med gull-glow-effekt."""
        def __init__(self, **kwargs):
            kwargs.setdefault('color', CLR_GOLD)
            kwargs.setdefault('font_size', sp(22))
            kwargs.setdefault('bold', True)
            kwargs.setdefault('size_hint_y', None)
            kwargs.setdefault('height', dp(45))
            super().__init__(**kwargs)

    class ElLabel(Label):
        """Standard label med eldritch-stil."""
        def __init__(self, **kwargs):
            kwargs.setdefault('color', CLR_TEXT)
            kwargs.setdefault('font_size', sp(14))
            super().__init__(**kwargs)

    class ElPanel(BoxLayout):
        """Panel med subtil bakgrunn og ramme."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.bind(pos=self._draw, size=self._draw)
            Clock.schedule_once(lambda dt: self._draw(), 0)

        def _draw(self, *args):
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*CLR_DEEP)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
                Color(*CLR_GOLD_DIM, 0.15)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)),
                     width=dp(0.8))

    class PulsingDot(Widget):
        """Pulserende indikator for aktiv status."""
        def __init__(self, active_color=CLR_GOLD, **kwargs):
            super().__init__(**kwargs)
            self.size_hint = (None, None)
            self.size = (dp(12), dp(12))
            self._pulse = 0.5
            self._active = False
            self._color = active_color
            self._anim = None
            self.bind(pos=self._draw, size=self._draw)

        def start(self):
            self._active = True
            self._animate()

        def stop(self):
            self._active = False
            if self._anim:
                self._anim.cancel(self)
            self._pulse = 0.3
            self._draw()

        def _animate(self):
            if not self._active:
                return
            self._anim = Animation(_pulse=1.0, duration=1.0) + Animation(_pulse=0.3, duration=1.0)
            self._anim.bind(on_progress=lambda *a: self._draw())
            self._anim.bind(on_complete=lambda *a: self._animate())
            self._anim.start(self)

        def _draw(self, *args):
            self.canvas.clear()
            with self.canvas:
                Color(self._color[0], self._color[1], self._color[2], self._pulse * 0.3)
                Ellipse(pos=(self.x - dp(2), self.y - dp(2)),
                       size=(self.width + dp(4), self.height + dp(4)))
                Color(self._color[0], self._color[1], self._color[2], self._pulse)
                Ellipse(pos=self.pos, size=self.size)

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
                self._httpd = None

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
                    log("Cast: scanning...")
                    chromecasts, browser = pychromecast.get_chromecasts()
                    self._browser = browser
                    for cc in chromecasts:
                        name = cc.cast_info.friendly_name
                        self.devices[name] = cc
                        log(f"Cast: found {name}")
                except Exception as e:
                    log(f"Cast scan error: {e}")
                finally:
                    self._scanning = False
                    if callback:
                        names = list(self.devices.keys())
                        Clock.schedule_once(lambda dt: callback(names), 0)

            threading.Thread(target=_scan, daemon=True).start()

        def connect(self, name, callback=None):
            if name not in self.devices:
                return

            def _connect():
                try:
                    log(f"Cast: connecting to {name}")
                    cc = self.devices[name]
                    cc.wait()
                    self.active_cast = cc
                    self.mc = cc.media_controller
                    log(f"Cast: connected to {name}")
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
                    log(f"Cast: casting {url}")
                    self.mc.play_media(url, 'image/jpeg')
                    self.mc.block_until_active()
                    log("Cast: image sent OK")
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
            except Exception as e:
                log(f"Cast disconnect error: {e}")
            self.active_cast = None
            self.mc = None

    # ============================================================
    #  LYDSPILLER
    # ============================================================
    class AndroidPlayer:
        def __init__(self):
            self.mp = None
            self.is_playing = False
            self._volume = 0.7

        def play(self, path):
            log(f"AndroidPlayer.play: {path}")
            self.stop()
            try:
                self.mp = MediaPlayer()
                self.mp.setDataSource(path)
                self.mp.setVolume(self._volume, self._volume)
                self.mp.prepare()
                self.mp.start()
                self.is_playing = True
                log("AndroidPlayer: playing OK")
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
                except Exception as e:
                    log(f"AndroidPlayer stop error: {e}")
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
            except Exception as e:
                log(f"FallbackPlayer error: {e}")

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
            Window.clearcolor = CLR_VOID
            self.title = "Eldritch Portal"
            self.tracks = []
            self.current_track = -1
            self.selected_image = None

            if USE_JNIUS:
                self.player = AndroidPlayer()
            else:
                self.player = FallbackPlayer()
            log(f"Player: {type(self.player).__name__}")

            self.cast_mgr = CastManager()
            self.media_server = MediaServer(
                directory="/sdcard/Documents/EldritchPortal",
                port=HTTP_PORT
            )

            root = BoxLayout(orientation='vertical', spacing=0)

            # === TOPPBAR ===
            header_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100))
            # App-tittel
            title_row = BoxLayout(size_hint_y=None, height=dp(40), padding=[dp(15), dp(8)])
            title_row.add_widget(ElLabel(
                text="ELDRITCH PORTAL",
                font_size=sp(18), color=CLR_GOLD, bold=True,
                size_hint_x=0.7
            ))
            # Pulserende indikator
            self.status_dot = PulsingDot()
            dot_box = BoxLayout(size_hint_x=0.3)
            dot_box.add_widget(Widget())  # spacer
            dot_box.add_widget(self.status_dot)
            dot_box.add_widget(Widget(size_hint_x=0.3))  # spacer
            title_row.add_widget(dot_box)
            header_box.add_widget(title_row)

            # Fane-bar
            tab_bar = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(4), padding=[dp(10), 0])
            self.tab_img = ElTab(text="Bilder", group='tabs', state='down')
            self.tab_mus = ElTab(text="Musikk", group='tabs')
            self.tab_cast = ElTab(text="Cast", group='tabs')
            self.tab_img.bind(on_release=lambda x: self.show_tab('images'))
            self.tab_mus.bind(on_release=lambda x: self.show_tab('music'))
            self.tab_cast.bind(on_release=lambda x: self.show_tab('cast'))
            tab_bar.add_widget(self.tab_img)
            tab_bar.add_widget(self.tab_mus)
            tab_bar.add_widget(self.tab_cast)
            header_box.add_widget(tab_bar)
            header_box.add_widget(ElGoldLine())
            root.add_widget(header_box)

            # === INNHOLD ===
            self.content = BoxLayout(padding=[dp(8), dp(8)])
            self.img_panel = self._build_image_panel()
            self.mus_panel = self._build_music_panel()
            self.cast_panel = self._build_cast_panel()
            self.content.add_widget(self.img_panel)
            root.add_widget(self.content)

            # === BUNNLINJE ===
            bottom = BoxLayout(size_hint_y=None, height=dp(30), padding=[dp(10), 0])
            bottom.add_widget(ElGoldLine())
            root.add_widget(bottom)
            self.status = ElLabel(text="", font_size=sp(11), color=CLR_TEXT_DIM,
                                 size_hint_y=None, height=dp(25), halign='center')
            self.status.bind(size=self.status.setter('text_size'))
            root.add_widget(self.status)

            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init_content(), 3)
            return root

        def _build_image_panel(self):
            panel = BoxLayout(orientation='vertical', spacing=dp(8))

            # Forhåndsvisning med ramme
            preview_frame = ElPanel(orientation='vertical', padding=dp(4), size_hint_y=0.45)
            self.preview = Image(allow_stretch=True, keep_ratio=True)
            preview_frame.add_widget(self.preview)
            panel.add_widget(preview_frame)

            # Info
            self.img_info = ElLabel(text="Velg et bilde", size_hint_y=None, height=dp(25),
                                   font_size=sp(13), color=CLR_TEXT_DIM, halign='center')
            self.img_info.bind(size=self.img_info.setter('text_size'))
            panel.add_widget(self.img_info)

            # Knapper
            btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            btn_cast = ElButton(text="Cast til TV", accent=True, size_hint_x=0.5)
            btn_cast.bind(on_release=lambda x: self.cast_selected_image())
            btn_row.add_widget(btn_cast)
            btn_refresh = ElButton(text="Oppdater", size_hint_x=0.5)
            btn_refresh.bind(on_release=lambda x: self.load_images())
            btn_row.add_widget(btn_refresh)
            panel.add_widget(btn_row)

            # Galleri
            scroll = ScrollView(size_hint_y=0.35)
            self.img_grid = GridLayout(cols=3, spacing=dp(6), padding=dp(4), size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid)
            panel.add_widget(scroll)
            return panel

        def _build_music_panel(self):
            panel = BoxLayout(orientation='vertical', spacing=dp(8))

            # Naavarande spor
            now_playing = ElPanel(orientation='vertical', padding=dp(12),
                                 size_hint_y=None, height=dp(80))
            self.track_label = ElLabel(text="Ingen spor valgt", font_size=sp(15),
                                      color=CLR_TEXT, halign='center')
            self.track_label.bind(size=self.track_label.setter('text_size'))
            now_playing.add_widget(self.track_label)
            self.music_dot = PulsingDot(active_color=CLR_ELDRITCH)
            dot_row = BoxLayout(size_hint_y=None, height=dp(16))
            dot_row.add_widget(Widget())
            dot_row.add_widget(self.music_dot)
            dot_row.add_widget(Widget())
            now_playing.add_widget(dot_row)
            panel.add_widget(now_playing)

            # Kontroller
            controls = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(8),
                               padding=[dp(10), 0])
            for txt, cb in [("Forr", self.prev_track), ("Play", self.toggle_play),
                           ("Neste", self.next_track), ("Stopp", self.stop_music)]:
                is_play = (txt == "Play")
                b = ElButton(text=txt, accent=is_play)
                b.bind(on_release=lambda x, f=cb: f())
                controls.add_widget(b)
                if is_play:
                    self.btn_play = b
            panel.add_widget(controls)

            # Volum
            vol_row = BoxLayout(size_hint_y=None, height=dp(40), padding=[dp(15), 0])
            vol_row.add_widget(ElLabel(text="Vol:", size_hint_x=0.12, font_size=sp(13),
                                      color=CLR_TEXT_DIM))
            self.vol_slider = Slider(min=0, max=1, value=0.7, size_hint_x=0.88,
                                    cursor_size=(dp(20), dp(20)))
            self.vol_slider.bind(value=self._on_volume)
            vol_row.add_widget(self.vol_slider)
            panel.add_widget(vol_row)

            panel.add_widget(ElGoldLine())

            # Sporliste
            scroll = ScrollView(size_hint_y=1)
            self.track_grid = GridLayout(cols=1, spacing=dp(4), padding=dp(4), size_hint_y=None)
            self.track_grid.bind(minimum_height=self.track_grid.setter('height'))
            scroll.add_widget(self.track_grid)
            panel.add_widget(scroll)
            return panel

        def _build_cast_panel(self):
            panel = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

            # Status-panel
            status_panel = ElPanel(orientation='vertical', padding=dp(15),
                                  size_hint_y=None, height=dp(80))
            self.cast_dot = PulsingDot(active_color=CLR_GOLD)
            dot_row = BoxLayout(size_hint_y=None, height=dp(16))
            dot_row.add_widget(Widget())
            dot_row.add_widget(self.cast_dot)
            dot_row.add_widget(Widget())
            status_panel.add_widget(dot_row)

            if not CAST_AVAILABLE:
                self.cast_status = ElLabel(text="Casting utilgjengelig\npychromecast mangler",
                    font_size=sp(14), halign='center', color=CLR_TEXT_DIM)
            else:
                self.cast_status = ElLabel(text="Ikke tilkoblet",
                    font_size=sp(14), halign='center', color=CLR_TEXT_DIM)
            self.cast_status.bind(size=self.cast_status.setter('text_size'))
            status_panel.add_widget(self.cast_status)
            panel.add_widget(status_panel)

            if CAST_AVAILABLE:
                btn_scan = ElButton(text="Sok etter enheter", accent=True,
                                   size_hint_y=None, height=dp(50))
                btn_scan.bind(on_release=lambda x: self._scan_cast())
                panel.add_widget(btn_scan)

                self.cast_spinner = Spinner(text="Velg enhet...", values=[],
                    size_hint_y=None, height=dp(50),
                    background_color=CLR_SURFACE, color=CLR_TEXT)
                panel.add_widget(self.cast_spinner)

                btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
                btn_connect = ElButton(text="Koble til", accent=True, size_hint_x=0.5)
                btn_connect.bind(on_release=lambda x: self._connect_cast())
                btn_row.add_widget(btn_connect)
                btn_disconnect = ElButton(text="Koble fra", size_hint_x=0.5)
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
            cast_txt = "Cast klar" if CAST_AVAILABLE else "Cast utilgj."
            self.status.text = f"IP: {ip}  |  {cast_txt}"
            self.status_dot.start()

        def show_tab(self, tab):
            self.content.clear_widgets()
            tabs = {
                'images': (self.img_panel, self.tab_img),
                'music': (self.mus_panel, self.tab_mus),
                'cast': (self.cast_panel, self.tab_cast),
            }
            for name, (p, btn) in tabs.items():
                if name == tab:
                    self.content.add_widget(p)

        # === BILDER ===
        def load_images(self):
            log("load_images()")
            self.img_grid.clear_widgets()
            try:
                if not os.path.exists(IMG_DIR):
                    self.img_info.text = "Mappen finnes ikke!"
                    return
                filer = sorted([f for f in os.listdir(IMG_DIR)
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
                self.img_info.text = f"{len(filer)} bilder"
                for fname in filer:
                    path = os.path.join(IMG_DIR, fname)
                    btn = ElButton(text=fname[:15], size_hint_y=None, height=dp(80))
                    btn.font_size = sp(12)
                    btn.bind(on_release=lambda x, p=path: self.select_image(p))
                    self.img_grid.add_widget(btn)
            except Exception as e:
                log(f"load_images error: {e}")

        def select_image(self, path):
            log(f"Selected image: {path}")
            try:
                self.preview.source = path
                self.selected_image = path
                self.img_info.text = os.path.basename(path)
                self.img_info.color = CLR_GOLD
            except Exception as e:
                log(f"select error: {e}")

        def cast_selected_image(self):
            if not self.selected_image:
                self.img_info.text = "Velg et bilde forst!"
                self.img_info.color = CLR_BLOOD
                return
            if not self.cast_mgr.active_cast:
                self.img_info.text = "Koble til Chromecast (Cast-fanen)"
                self.img_info.color = CLR_BLOOD
                return
            url = self.media_server.get_url(self.selected_image)
            self.img_info.text = "Caster..."
            self.img_info.color = CLR_GOLD_DIM
            log(f"Casting image: {url}")
            self.cast_mgr.cast_image(url, callback=self._on_cast_result)

        def _on_cast_result(self, success):
            if success:
                self.img_info.text = "Bilde castet!"
                self.img_info.color = CLR_GOLD
            else:
                self.img_info.text = "Casting feilet"
                self.img_info.color = CLR_BLOOD

        # === CAST ===
        def _scan_cast(self):
            if not CAST_AVAILABLE:
                return
            self.cast_status.text = "Soker etter enheter..."
            self.cast_status.color = CLR_GOLD_DIM
            self.cast_dot.start()
            self.cast_mgr.discover(callback=self._on_devices_found)

        def _on_devices_found(self, names):
            self.cast_dot.stop()
            if names:
                self.cast_spinner.values = names
                self.cast_spinner.text = names[0]
                self.cast_status.text = f"Fant {len(names)} enhet(er)"
                self.cast_status.color = CLR_GOLD
            else:
                self.cast_status.text = "Ingen enheter funnet"
                self.cast_status.color = CLR_TEXT_DIM

        def _connect_cast(self):
            if not CAST_AVAILABLE:
                return
            name = self.cast_spinner.text
            if name == "Velg enhet..." or not name:
                self.cast_status.text = "Velg en enhet forst"
                return
            self.cast_status.text = f"Kobler til {name}..."
            self.cast_status.color = CLR_GOLD_DIM
            self.cast_dot.start()
            self.cast_mgr.connect(name, callback=self._on_connected)

        def _on_connected(self, success):
            if success:
                self.cast_status.text = f"Tilkoblet: {self.cast_spinner.text}"
                self.cast_status.color = CLR_GOLD
                self.cast_dot.start()
            else:
                self.cast_status.text = "Tilkobling feilet"
                self.cast_status.color = CLR_BLOOD
                self.cast_dot.stop()

        def _disconnect_cast(self):
            self.cast_mgr.disconnect()
            self.cast_status.text = "Frakoblet"
            self.cast_status.color = CLR_TEXT_DIM
            self.cast_dot.stop()

        # === MUSIKK ===
        def load_tracks(self):
            log("load_tracks()")
            self.track_grid.clear_widgets()
            self.tracks = []
            try:
                if not os.path.exists(MUSIC_DIR):
                    self.track_label.text = "Mappen finnes ikke!"
                    return
                filer = sorted([f for f in os.listdir(MUSIC_DIR)
                               if f.lower().endswith(('.mp3', '.ogg', '.wav', '.flac'))])
                self.track_label.text = f"{len(filer)} spor"
                for i, fname in enumerate(filer):
                    self.tracks.append(os.path.join(MUSIC_DIR, fname))
                    btn = ElButton(text=fname, size_hint_y=None, height=dp(48))
                    btn.font_size = sp(13)
                    btn.halign = 'left'
                    btn.bind(size=btn.setter('text_size'))
                    btn.bind(on_release=lambda x, idx=i: self.play_track(idx))
                    self.track_grid.add_widget(btn)
            except Exception as e:
                log(f"load_tracks error: {e}")

        def play_track(self, idx):
            log(f"play_track({idx})")
            if idx < 0 or idx >= len(self.tracks):
                return
            self.current_track = idx
            path = self.tracks[idx]
            self.player.play(path)
            if self.player.is_playing:
                self.btn_play.text = "Pause"
                self.track_label.text = f"Spiller: {os.path.basename(path)}"
                self.track_label.color = CLR_GOLD
                self.music_dot.start()
            else:
                self.track_label.text = "Kunne ikke spille sporet"
                self.track_label.color = CLR_BLOOD

        def toggle_play(self):
            if not self.player.is_playing and self.current_track < 0:
                if self.tracks:
                    self.play_track(0)
                return
            if self.player.is_playing:
                self.player.pause()
                self.btn_play.text = "Play"
                self.music_dot.stop()
            else:
                self.player.resume()
                self.btn_play.text = "Pause"
                self.music_dot.start()

        def stop_music(self):
            self.player.stop()
            self.btn_play.text = "Play"
            self.track_label.text = "Stoppet"
            self.track_label.color = CLR_TEXT_DIM
            self.music_dot.stop()

        def next_track(self):
            if self.tracks:
                self.play_track((self.current_track + 1) % len(self.tracks))

        def prev_track(self):
            if self.tracks:
                self.play_track((self.current_track - 1) % len(self.tracks))

        def _on_volume(self, slider, value):
            self.player.set_volume(value)

        def on_stop(self):
            self.player.stop()
            self.media_server.stop()
            self.cast_mgr.disconnect()

    log("Starting app...")
    EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())