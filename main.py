import os, sys, traceback, socket, threading
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
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    log("Kivy imported OK")

    # Chromecast (valgfri)
    CAST_AVAILABLE = False
    try:
        import pychromecast
        CAST_AVAILABLE = True
        log("pychromecast imported OK")
    except ImportError as e:
        log(f"pychromecast not available: {e}")

    # Android MediaPlayer for musikk
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

    CLR_BG = (0.08, 0.08, 0.10, 1)
    CLR_ACCENT = (0.75, 0.65, 0.20, 1)
    CLR_TEXT = (0.85, 0.82, 0.75, 1)
    CLR_BTN = (0.18, 0.20, 0.22, 1)
    CLR_BTN_ACTIVE = (0.30, 0.28, 0.12, 1)
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

    # === HTTP SERVER ===
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

    # === CAST MANAGER ===
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

    # === LYDSPILLER ===
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

    # === APP ===
    class EldritchApp(App):
        def build(self):
            log("build() called")
            Window.clearcolor = CLR_BG
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

            # Fane-bar
            tab_bar = BoxLayout(size_hint_y=None, height=50, spacing=2, padding=[5, 2])
            self.tab_img = ToggleButton(text="BILDER", group='tabs', state='down',
                background_normal='', background_color=CLR_BTN_ACTIVE, color=CLR_ACCENT, bold=True)
            self.tab_mus = ToggleButton(text="MUSIKK", group='tabs',
                background_normal='', background_color=CLR_BTN, color=CLR_TEXT, bold=True)
            self.tab_cast = ToggleButton(text="CAST", group='tabs',
                background_normal='', background_color=CLR_BTN, color=CLR_TEXT, bold=True)
            self.tab_img.bind(on_release=lambda x: self.show_tab('images'))
            self.tab_mus.bind(on_release=lambda x: self.show_tab('music'))
            self.tab_cast.bind(on_release=lambda x: self.show_tab('cast'))
            tab_bar.add_widget(self.tab_img)
            tab_bar.add_widget(self.tab_mus)
            tab_bar.add_widget(self.tab_cast)
            root.add_widget(tab_bar)

            self.content = BoxLayout()
            self.img_panel = self._build_image_panel()
            self.mus_panel = self._build_music_panel()
            self.cast_panel = self._build_cast_panel()
            self.content.add_widget(self.img_panel)
            root.add_widget(self.content)

            self.status = Label(text="", size_hint_y=None, height=30,
                              font_size=12, color=CLR_TEXT)
            root.add_widget(self.status)

            log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init_content(), 3)
            return root

        def _build_image_panel(self):
            panel = BoxLayout(orientation='vertical', padding=10, spacing=8)
            panel.add_widget(Label(text="BILDER", font_size=20,
                color=CLR_ACCENT, size_hint_y=None, height=40, bold=True))

            self.preview = Image(size_hint_y=0.4, allow_stretch=True, keep_ratio=True)
            panel.add_widget(self.preview)

            self.img_info = Label(text="", size_hint_y=None, height=25, color=CLR_TEXT, font_size=13)
            panel.add_widget(self.img_info)

            # Knapper: Cast + Oppdater
            btn_row = BoxLayout(size_hint_y=None, height=45, spacing=10)
            btn_cast = Button(text="CAST TIL TV", size_hint_x=0.5,
                background_normal='', background_color=CLR_BTN, color=CLR_ACCENT, bold=True)
            btn_cast.bind(on_release=lambda x: self.cast_selected_image())
            btn_row.add_widget(btn_cast)
            btn_refresh = Button(text="OPPDATER", size_hint_x=0.5,
                background_normal='', background_color=CLR_BTN, color=CLR_TEXT, bold=True)
            btn_refresh.bind(on_release=lambda x: self.load_images())
            btn_row.add_widget(btn_refresh)
            panel.add_widget(btn_row)

            scroll = ScrollView(size_hint_y=0.35)
            self.img_grid = GridLayout(cols=3, spacing=8, padding=8, size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid)
            panel.add_widget(scroll)
            return panel

        def _build_music_panel(self):
            panel = BoxLayout(orientation='vertical', padding=10, spacing=8)
            panel.add_widget(Label(text="MUSIKK", font_size=20,
                color=CLR_ACCENT, size_hint_y=None, height=40, bold=True))

            self.track_label = Label(text="Ingen spor valgt", size_hint_y=None, height=35,
                color=CLR_TEXT, font_size=15)
            panel.add_widget(self.track_label)

            controls = BoxLayout(size_hint_y=None, height=55, spacing=10, padding=[20, 5])
            for txt, cb in [("Forr", self.prev_track), ("Play", self.toggle_play),
                           ("Neste", self.next_track), ("Stopp", self.stop_music)]:
                b = Button(text=txt, background_normal='', background_color=CLR_BTN,
                          color=CLR_TEXT, bold=True, font_size=16)
                b.bind(on_release=lambda x, f=cb: f())
                controls.add_widget(b)
                if txt == "Play":
                    self.btn_play = b
            panel.add_widget(controls)

            vol_row = BoxLayout(size_hint_y=None, height=40, padding=[20, 0])
            vol_row.add_widget(Label(text="Vol:", color=CLR_TEXT, size_hint_x=0.15, font_size=13))
            self.vol_slider = Slider(min=0, max=1, value=0.7, size_hint_x=0.85)
            self.vol_slider.bind(value=self._on_volume)
            vol_row.add_widget(self.vol_slider)
            panel.add_widget(vol_row)

            scroll = ScrollView(size_hint_y=1)
            self.track_grid = GridLayout(cols=1, spacing=5, padding=8, size_hint_y=None)
            self.track_grid.bind(minimum_height=self.track_grid.setter('height'))
            scroll.add_widget(self.track_grid)
            panel.add_widget(scroll)
            return panel

        def _build_cast_panel(self):
            panel = BoxLayout(orientation='vertical', padding=10, spacing=10)
            panel.add_widget(Label(text="CHROMECAST", font_size=20,
                color=CLR_ACCENT, size_hint_y=None, height=40, bold=True))

            if not CAST_AVAILABLE:
                panel.add_widget(Label(
                    text="Casting ikke tilgjengelig.\npychromecast mangler.",
                    color=CLR_TEXT, font_size=14, halign='center',
                    size_hint_y=None, height=80))
                # Vis server-IP uansett
                self.cast_status = Label(text="", color=CLR_TEXT,
                    font_size=13, size_hint_y=None, height=30)
                panel.add_widget(self.cast_status)
                panel.add_widget(Label(size_hint_y=1))  # spacer
                return panel

            self.cast_status = Label(text="Ikke tilkoblet", color=CLR_TEXT,
                font_size=14, size_hint_y=None, height=35)
            panel.add_widget(self.cast_status)

            btn_scan = Button(text="SOK ETTER ENHETER", size_hint_y=None, height=50,
                background_normal='', background_color=CLR_BTN, color=CLR_TEXT, bold=True)
            btn_scan.bind(on_release=lambda x: self._scan_cast())
            panel.add_widget(btn_scan)

            self.cast_spinner = Spinner(text="Velg enhet...", values=[],
                size_hint_y=None, height=50,
                background_color=CLR_BTN, color=CLR_TEXT)
            panel.add_widget(self.cast_spinner)

            btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
            btn_connect = Button(text="KOBLE TIL", size_hint_x=0.5,
                background_normal='', background_color=CLR_BTN, color=CLR_ACCENT, bold=True)
            btn_connect.bind(on_release=lambda x: self._connect_cast())
            btn_row.add_widget(btn_connect)
            btn_disconnect = Button(text="KOBLE FRA", size_hint_x=0.5,
                background_normal='', background_color=(0.4, 0.15, 0.15, 1), color=CLR_TEXT, bold=True)
            btn_disconnect.bind(on_release=lambda x: self._disconnect_cast())
            btn_row.add_widget(btn_disconnect)
            panel.add_widget(btn_row)

            panel.add_widget(Label(size_hint_y=1))  # spacer
            return panel

        def _init_content(self):
            self.media_server.start()
            self.load_images()
            self.load_tracks()
            ip = MediaServer.get_local_ip()
            self.status.text = f"IP: {ip} | Cast: {'Klar' if CAST_AVAILABLE else 'Utilgj.'}"

        def show_tab(self, tab):
            self.content.clear_widgets()
            tabs = {
                'images': (self.img_panel, self.tab_img),
                'music': (self.mus_panel, self.tab_mus),
                'cast': (self.cast_panel, self.tab_cast),
            }
            for name, (panel, btn) in tabs.items():
                if name == tab:
                    self.content.add_widget(panel)
                    btn.background_color = CLR_BTN_ACTIVE
                    btn.color = CLR_ACCENT
                else:
                    btn.background_color = CLR_BTN
                    btn.color = CLR_TEXT

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
                    btn = Button(text=fname[:15], size_hint_y=None, height=100,
                        background_normal='', background_color=CLR_BTN, color=CLR_TEXT)
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
            except Exception as e:
                log(f"select error: {e}")

        def cast_selected_image(self):
            if not self.selected_image:
                self.img_info.text = "Velg et bilde forst!"
                return
            if not self.cast_mgr.active_cast:
                self.img_info.text = "Koble til Chromecast forst (CAST-fanen)"
                return
            url = self.media_server.get_url(self.selected_image)
            self.img_info.text = "Caster..."
            log(f"Casting image: {url}")
            self.cast_mgr.cast_image(url, callback=self._on_cast_result)

        def _on_cast_result(self, success):
            if success:
                self.img_info.text = "Bilde castet!"
            else:
                self.img_info.text = "Casting feilet"

        # === CAST ===
        def _scan_cast(self):
            if not CAST_AVAILABLE:
                return
            self.cast_status.text = "Soker..."
            self.cast_mgr.discover(callback=self._on_devices_found)

        def _on_devices_found(self, names):
            if names:
                self.cast_spinner.values = names
                self.cast_spinner.text = names[0]
                self.cast_status.text = f"Fant {len(names)} enhet(er)"
            else:
                self.cast_status.text = "Ingen enheter funnet"

        def _connect_cast(self):
            if not CAST_AVAILABLE:
                return
            name = self.cast_spinner.text
            if name == "Velg enhet..." or not name:
                self.cast_status.text = "Velg en enhet forst"
                return
            self.cast_status.text = f"Kobler til {name}..."
            self.cast_mgr.connect(name, callback=self._on_connected)

        def _on_connected(self, success):
            if success:
                self.cast_status.text = f"Tilkoblet: {self.cast_spinner.text}"
            else:
                self.cast_status.text = "Tilkobling feilet"

        def _disconnect_cast(self):
            self.cast_mgr.disconnect()
            self.cast_status.text = "Frakoblet"

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
                    btn = Button(text=fname, size_hint_y=None, height=50,
                        background_normal='', background_color=CLR_BTN,
                        color=CLR_TEXT, halign='left', font_size=14)
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
            else:
                self.track_label.text = "Kunne ikke spille sporet"

        def toggle_play(self):
            if not self.player.is_playing and self.current_track < 0:
                if self.tracks:
                    self.play_track(0)
                return
            if self.player.is_playing:
                self.player.pause()
                self.btn_play.text = "Play"
            else:
                self.player.resume()
                self.btn_play.text = "Pause"

        def stop_music(self):
            self.player.stop()
            self.btn_play.text = "Play"
            self.track_label.text = "Stoppet"

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