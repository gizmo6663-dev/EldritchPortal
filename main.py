"""
Eldritch Portal - RPG Stemningsverktøy
=======================================
Bildegalleri med Chromecast-casting og musikkspiller.
Designet for å kjøre som APK via Buildozer.

Casting-arkitektur:
  - Lokal HTTP-server serverer filer til Chromecast
  - pychromecast håndterer oppdagelse og kontroll
  - Graceful fallback hvis casting ikke er tilgjengelig
"""

import os
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle

# ============================================================
#  PLATTFORMDETEKSJON
# ============================================================
IS_ANDROID = platform == 'android'
HAS_ANDROID_API = False

if IS_ANDROID:
    try:
        from android.permissions import request_permissions, Permission
        from android.storage import primary_external_storage_path
        HAS_ANDROID_API = True
    except ImportError:
        # Pydroid 3: android-modulen finnes men mangler full Kivy-integrasjon
        pass

# Chromecast-støtte (valgfri)
try:
    import pychromecast
    CAST_AVAILABLE = True
except ImportError:
    CAST_AVAILABLE = False


# ============================================================
#  KONFIGURASJON
# ============================================================
APP_TITLE = "Eldritch Portal"

# Mapper for innhold
if IS_ANDROID and HAS_ANDROID_API:
    _base = primary_external_storage_path()
    IMG_DIR = os.path.join(_base, "Documents", "EldritchPortal", "images")
    MUSIC_DIR = os.path.join(_base, "Documents", "EldritchPortal", "music")
elif IS_ANDROID:
    # Pydroid 3 fallback — /sdcard er tilgjengelig
    IMG_DIR = "/sdcard/Documents/EldritchPortal/images"
    MUSIC_DIR = "/sdcard/Documents/EldritchPortal/music"
else:
    # Desktop fallback
    IMG_DIR = os.path.join(os.path.expanduser("~"), "EldritchPortal", "images")
    MUSIC_DIR = os.path.join(os.path.expanduser("~"), "EldritchPortal", "music")

IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp')
AUDIO_EXT = ('.mp3', '.ogg', '.wav', '.flac')

# Fargepalett (Cthulhu-tema)
CLR_BG = (0.08, 0.08, 0.10, 1)
CLR_PANEL = (0.12, 0.13, 0.15, 1)
CLR_ACCENT = (0.75, 0.65, 0.20, 1)       # gull
CLR_ACCENT_DIM = (0.45, 0.40, 0.15, 1)
CLR_TEXT = (0.85, 0.82, 0.75, 1)
CLR_BTN = (0.18, 0.20, 0.22, 1)
CLR_BTN_ACTIVE = (0.30, 0.28, 0.12, 1)
CLR_DANGER = (0.6, 0.15, 0.15, 1)

HTTP_PORT = 8089  # port for lokal mediaserver


# ============================================================
#  LOKAL HTTP-SERVER (for å serve filer til Chromecast)
# ============================================================
class _QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler uten logg-spam."""
    def log_message(self, fmt, *args):
        pass  # stille


class MediaServer:
    """
    Kjører en enkel HTTP-server i en bakgrunnstråd.
    Chromecast henter bilder/musikk fra denne.
    """
    def __init__(self, directory, port=HTTP_PORT):
        self.directory = directory
        self.port = port
        self._httpd = None
        self._thread = None

    def start(self):
        if self._httpd:
            return
        os.makedirs(self.directory, exist_ok=True)
        handler = partial(_QuietHandler, directory=self.directory)
        try:
            self._httpd = HTTPServer(('0.0.0.0', self.port), handler)
            self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            self._thread.start()
        except OSError:
            self._httpd = None

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd = None

    @staticmethod
    def get_local_ip():
        """Finn telefonens lokale IP-adresse på nettverket."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_url(self, filepath):
        """Returner HTTP-URL for en lokal fil."""
        rel = os.path.relpath(filepath, self.directory)
        ip = self.get_local_ip()
        return f"http://{ip}:{self.port}/{rel}"


# ============================================================
#  CHROMECAST-HÅNDTERING
# ============================================================
class CastManager:
    """
    Håndterer Chromecast-oppdagelse, tilkobling og mediekontroll.
    Fungerer kun hvis pychromecast er installert.
    """
    def __init__(self):
        self.devices = {}       # navn -> chromecast-objekt
        self.active_cast = None
        self.mc = None          # media controller
        self._browser = None
        self._discovering = False

    @property
    def available(self):
        return CAST_AVAILABLE

    def discover(self, callback=None):
        """Start oppdagelse av Chromecast-enheter."""
        if not CAST_AVAILABLE or self._discovering:
            return
        self._discovering = True
        self.devices = {}

        def _scan():
            try:
                chromecasts, browser = pychromecast.get_chromecasts()
                self._browser = browser
                for cc in chromecasts:
                    self.devices[cc.cast_info.friendly_name] = cc
            except Exception as e:
                print(f"Cast discovery feil: {e}")
            finally:
                self._discovering = False
                if callback:
                    Clock.schedule_once(lambda dt: callback(list(self.devices.keys())), 0)

        threading.Thread(target=_scan, daemon=True).start()

    def connect(self, device_name):
        """Koble til en navngitt Chromecast."""
        if device_name not in self.devices:
            return False
        try:
            cc = self.devices[device_name]
            cc.wait()
            self.active_cast = cc
            self.mc = cc.media_controller
            return True
        except Exception as e:
            print(f"Cast connect feil: {e}")
            return False

    def cast_image(self, url):
        """Vis et bilde på Chromecast via URL."""
        if not self.mc:
            return False
        try:
            self.mc.play_media(url, 'image/jpeg')
            self.mc.block_until_active()
            return True
        except Exception as e:
            print(f"Cast image feil: {e}")
            return False

    def cast_audio(self, url, title="Musikk"):
        """Spill lyd på Chromecast."""
        if not self.mc:
            return False
        try:
            self.mc.play_media(url, 'audio/mp3', title=title)
            self.mc.block_until_active()
            return True
        except Exception as e:
            print(f"Cast audio feil: {e}")
            return False

    def pause(self):
        if self.mc:
            self.mc.pause()

    def play(self):
        if self.mc:
            self.mc.play()

    def stop(self):
        if self.mc:
            self.mc.stop()

    def disconnect(self):
        if self._browser:
            self._browser.stop_discovery()
        if self.active_cast:
            self.active_cast.disconnect()
        self.active_cast = None
        self.mc = None


# ============================================================
#  HJELPE-WIDGETS
# ============================================================
class StyledButton(Button):
    """Knapp med Cthulhu-stil."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = CLR_BTN
        self.color = CLR_TEXT
        self.bold = True
        self.font_size = '15sp'

    def on_press(self):
        self.background_color = CLR_BTN_ACTIVE

    def on_release(self):
        self.background_color = CLR_BTN


class HeaderLabel(Label):
    """Overskrift-label med gullfarget tekst."""
    def __init__(self, **kwargs):
        kwargs.setdefault('color', CLR_ACCENT)
        kwargs.setdefault('font_size', '20sp')
        kwargs.setdefault('bold', True)
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 50)
        super().__init__(**kwargs)


class StatusBar(Label):
    """Statuslinje nederst."""
    def __init__(self, **kwargs):
        kwargs.setdefault('color', CLR_TEXT)
        kwargs.setdefault('font_size', '13sp')
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 35)
        kwargs.setdefault('halign', 'center')
        super().__init__(**kwargs)
        self.bind(size=self.setter('text_size'))


# ============================================================
#  BILDEGALLERI
# ============================================================
class ImageGallery(BoxLayout):
    """
    Viser et rutenett med miniatyrbilder.
    Trykk på et bilde for å forhåndsvise og caste det.
    """
    def __init__(self, app_ref, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.app = app_ref
        self.images = []
        self.selected_path = None

        # Forhåndsvisning
        self.preview = AsyncImage(
            source='',
            size_hint=(1, 0.45),
            allow_stretch=True,
            keep_ratio=True,
        )
        self.add_widget(self.preview)

        # Info-label
        self.info = Label(
            text="Trykk på et bilde for å velge",
            color=CLR_TEXT, font_size='14sp',
            size_hint_y=None, height=30,
            halign='center',
        )
        self.info.bind(size=self.info.setter('text_size'))
        self.add_widget(self.info)

        # Knapper: Cast + Oppdater
        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=[10, 5])
        self.btn_cast = StyledButton(text="CAST TIL TV")
        self.btn_cast.bind(on_release=lambda x: self.cast_selected())
        btn_row.add_widget(self.btn_cast)

        btn_refresh = StyledButton(text="OPPDATER")
        btn_refresh.bind(on_release=lambda x: self.load_images())
        btn_row.add_widget(btn_refresh)
        self.add_widget(btn_row)

        # Bilde-rutenett i scrollview
        scroll = ScrollView(size_hint=(1, 0.40))
        self.grid = GridLayout(
            cols=3, spacing=8, padding=8,
            size_hint_y=None,
        )
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        self.add_widget(scroll)

    def load_images(self):
        """Last inn bilder fra IMG_DIR."""
        self.grid.clear_widgets()
        self.images = []

        os.makedirs(IMG_DIR, exist_ok=True)

        try:
            filer = sorted([
                f for f in os.listdir(IMG_DIR)
                if f.lower().endswith(IMG_EXT)
            ])
        except PermissionError:
            self.info.text = "Mangler tillatelse til å lese mappen"
            return

        if not filer:
            self.info.text = f"Ingen bilder i {IMG_DIR}"
            return

        self.info.text = f"{len(filer)} bilder funnet"

        for fname in filer:
            full_path = os.path.join(IMG_DIR, fname)
            self.images.append(full_path)

            # Miniatyr-knapp med bilde
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=160)

            img = AsyncImage(
                source=full_path,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(1, 0.8),
            )
            box.add_widget(img)

            # Kort filnavn under bildet
            short = fname[:15] + "…" if len(fname) > 15 else fname
            lbl = Label(
                text=short,
                font_size='11sp',
                color=CLR_TEXT,
                size_hint_y=0.2,
            )
            box.add_widget(lbl)

            # Gjør hele boksen klikkbar
            btn_overlay = Button(
                background_color=(0, 0, 0, 0),
                size_hint=(1, 1),
            )
            btn_overlay.bind(on_release=lambda x, p=full_path: self.select_image(p))

            container = FloatLayout(size_hint_y=None, height=160)
            box.pos_hint = {'x': 0, 'y': 0}
            box.size_hint = (1, 1)
            container.add_widget(box)
            container.add_widget(btn_overlay)

            self.grid.add_widget(container)

    def select_image(self, path):
        """Velg et bilde for forhåndsvisning."""
        self.selected_path = path
        self.preview.source = path
        self.info.text = f"Valgt: {os.path.basename(path)}"

    def cast_selected(self):
        """Cast valgt bilde til Chromecast."""
        if not self.selected_path:
            self.info.text = "Velg et bilde først!"
            return
        if not self.app.cast_mgr.active_cast:
            self.info.text = "Ikke koblet til Chromecast"
            return

        url = self.app.media_server.get_url(self.selected_path)
        self.info.text = f"Caster..."

        def _do_cast():
            ok = self.app.cast_mgr.cast_image(url)
            msg = "Bilde castet!" if ok else "Casting feilet"
            Clock.schedule_once(lambda dt: setattr(self.info, 'text', msg), 0)

        threading.Thread(target=_do_cast, daemon=True).start()


# ============================================================
#  MUSIKKSPILLER
# ============================================================
class MusicPlayer(BoxLayout):
    """Musikkspiller med lokal avspilling og casting."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.app = app_ref
        self.tracks = []
        self.current_idx = -1
        self.sound = None
        self.is_playing = False

        self.add_widget(HeaderLabel(text="♫ MUSIKK"))

        # Nåværende spor
        self.track_label = Label(
            text="Ingen spor lastet",
            color=CLR_TEXT, font_size='15sp',
            size_hint_y=None, height=40,
            halign='center',
        )
        self.track_label.bind(size=self.track_label.setter('text_size'))
        self.add_widget(self.track_label)

        # Kontrollknapper
        controls = BoxLayout(size_hint_y=None, height=55, spacing=10, padding=[20, 5])

        self.btn_prev = StyledButton(text="⏮")
        self.btn_prev.bind(on_release=lambda x: self.prev_track())
        controls.add_widget(self.btn_prev)

        self.btn_play = StyledButton(text="▶")
        self.btn_play.bind(on_release=lambda x: self.toggle_play())
        controls.add_widget(self.btn_play)

        self.btn_next = StyledButton(text="⏭")
        self.btn_next.bind(on_release=lambda x: self.next_track())
        controls.add_widget(self.btn_next)

        self.btn_stop = StyledButton(text="⏹")
        self.btn_stop.bind(on_release=lambda x: self.stop())
        controls.add_widget(self.btn_stop)

        self.add_widget(controls)

        # Volumkontroll
        vol_row = BoxLayout(size_hint_y=None, height=40, padding=[20, 0])
        vol_row.add_widget(Label(text="Vol:", color=CLR_TEXT, size_hint_x=0.15, font_size='13sp'))
        self.vol_slider = Slider(min=0, max=1, value=0.7, size_hint_x=0.85)
        self.vol_slider.bind(value=self._on_volume)
        vol_row.add_widget(self.vol_slider)
        self.add_widget(vol_row)

        # Cast-musikk-knapp
        self.btn_cast_music = StyledButton(
            text="CAST MUSIKK TIL TV",
            size_hint_y=None, height=45,
        )
        self.btn_cast_music.bind(on_release=lambda x: self.cast_current())
        self.add_widget(self.btn_cast_music)

        # Sporliste
        scroll = ScrollView(size_hint=(1, 1))
        self.track_grid = GridLayout(
            cols=1, spacing=5, padding=8,
            size_hint_y=None,
        )
        self.track_grid.bind(minimum_height=self.track_grid.setter('height'))
        scroll.add_widget(self.track_grid)
        self.add_widget(scroll)

    def load_tracks(self):
        """Skann musikkmappe for lydfiler."""
        self.track_grid.clear_widgets()
        self.tracks = []

        os.makedirs(MUSIC_DIR, exist_ok=True)

        try:
            filer = sorted([
                f for f in os.listdir(MUSIC_DIR)
                if f.lower().endswith(AUDIO_EXT)
            ])
        except PermissionError:
            self.track_label.text = "Mangler tillatelse"
            return

        if not filer:
            self.track_label.text = f"Ingen musikk i {MUSIC_DIR}"
            return

        self.track_label.text = f"{len(filer)} spor funnet"

        for i, fname in enumerate(filer):
            full_path = os.path.join(MUSIC_DIR, fname)
            self.tracks.append(full_path)

            btn = StyledButton(
                text=f"  {fname}",
                size_hint_y=None, height=45,
                halign='left',
            )
            btn.bind(size=btn.setter('text_size'))
            btn.bind(on_release=lambda x, idx=i: self.play_track(idx))
            self.track_grid.add_widget(btn)

    def play_track(self, idx):
        """Spill et bestemt spor."""
        if idx < 0 or idx >= len(self.tracks):
            return
        self.stop()
        self.current_idx = idx
        path = self.tracks[idx]
        self.sound = SoundLoader.load(path)
        if self.sound:
            self.sound.volume = self.vol_slider.value
            self.sound.play()
            self.is_playing = True
            self.btn_play.text = "⏸"
            self.track_label.text = f"▶ {os.path.basename(path)}"

    def toggle_play(self):
        if not self.sound:
            if self.tracks:
                self.play_track(0)
            return
        if self.is_playing:
            self.sound.stop()
            self.is_playing = False
            self.btn_play.text = "▶"
        else:
            self.sound.play()
            self.is_playing = True
            self.btn_play.text = "⏸"

    def stop(self):
        if self.sound:
            self.sound.stop()
            self.sound.unload()
            self.sound = None
        self.is_playing = False
        self.btn_play.text = "▶"

    def next_track(self):
        if self.tracks:
            self.play_track((self.current_idx + 1) % len(self.tracks))

    def prev_track(self):
        if self.tracks:
            self.play_track((self.current_idx - 1) % len(self.tracks))

    def _on_volume(self, slider, value):
        if self.sound:
            self.sound.volume = value

    def cast_current(self):
        """Cast nåværende spor til Chromecast."""
        if self.current_idx < 0 or self.current_idx >= len(self.tracks):
            self.track_label.text = "Velg et spor først!"
            return
        if not self.app.cast_mgr.active_cast:
            self.track_label.text = "Ikke koblet til Chromecast"
            return

        path = self.tracks[self.current_idx]
        url = self.app.media_server.get_url(path)
        title = os.path.basename(path)
        self.track_label.text = f"Caster {title}..."

        def _do():
            ok = self.app.cast_mgr.cast_audio(url, title=title)
            msg = f"Caster: {title}" if ok else "Casting feilet"
            Clock.schedule_once(lambda dt: setattr(self.track_label, 'text', msg), 0)

        threading.Thread(target=_do, daemon=True).start()


# ============================================================
#  CAST-PANEL (enhetsstyring)
# ============================================================
class CastPanel(BoxLayout):
    """Panel for å oppdage og koble til Chromecast-enheter."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)
        self.app = app_ref

        self.add_widget(HeaderLabel(text="CHROMECAST"))

        if not CAST_AVAILABLE:
            self.add_widget(Label(
                text="pychromecast ikke installert.\n"
                     "Casting er deaktivert.\n\n"
                     "Installer med:\n  pip install pychromecast",
                color=CLR_TEXT, font_size='14sp',
                halign='center',
            ))
            return

        # Status
        self.status = Label(
            text="Ikke tilkoblet",
            color=CLR_ACCENT_DIM, font_size='14sp',
            size_hint_y=None, height=35,
        )
        self.add_widget(self.status)

        # Søk-knapp
        self.btn_scan = StyledButton(
            text="SØK ETTER ENHETER",
            size_hint_y=None, height=50,
        )
        self.btn_scan.bind(on_release=lambda x: self.scan())
        self.add_widget(self.btn_scan)

        # Enhetsliste
        self.device_spinner = Spinner(
            text="Velg enhet...",
            values=[],
            size_hint_y=None, height=50,
            background_color=CLR_BTN,
            color=CLR_TEXT,
        )
        self.add_widget(self.device_spinner)

        # Koble til / fra
        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.btn_connect = StyledButton(text="KOBLE TIL")
        self.btn_connect.bind(on_release=lambda x: self.connect())
        btn_row.add_widget(self.btn_connect)

        self.btn_disconnect = StyledButton(text="KOBLE FRA")
        self.btn_disconnect.background_color = CLR_DANGER
        self.btn_disconnect.bind(on_release=lambda x: self.disconnect())
        btn_row.add_widget(self.btn_disconnect)
        self.add_widget(btn_row)

        # Spacer
        self.add_widget(Label(size_hint_y=1))

    def scan(self):
        self.status.text = "Søker etter enheter..."
        self.btn_scan.text = "SØKER..."
        self.btn_scan.disabled = True
        self.app.cast_mgr.discover(callback=self._on_devices_found)

    def _on_devices_found(self, names):
        self.btn_scan.disabled = False
        self.btn_scan.text = "SØK ETTER ENHETER"
        if names:
            self.device_spinner.values = names
            self.device_spinner.text = names[0]
            self.status.text = f"Fant {len(names)} enhet(er)"
        else:
            self.status.text = "Ingen enheter funnet"

    def connect(self):
        name = self.device_spinner.text
        if name == "Velg enhet..." or not name:
            self.status.text = "Velg en enhet først"
            return
        self.status.text = f"Kobler til {name}..."

        def _do():
            ok = self.app.cast_mgr.connect(name)
            msg = f"Koblet til: {name}" if ok else "Tilkobling feilet"
            color = CLR_ACCENT if ok else CLR_DANGER
            Clock.schedule_once(lambda dt: self._update_status(msg, color), 0)

        threading.Thread(target=_do, daemon=True).start()

    def _update_status(self, msg, color):
        self.status.text = msg
        self.status.color = color

    def disconnect(self):
        self.app.cast_mgr.disconnect()
        self.status.text = "Frakoblet"
        self.status.color = CLR_ACCENT_DIM


# ============================================================
#  HOVEDAPP
# ============================================================
class EldritchPortalApp(App):
    def build(self):
        self.title = APP_TITLE

        # Sett opp bakgrunnsfarge
        Window.clearcolor = CLR_BG

        # Initialiser casting og mediaserver
        self.cast_mgr = CastManager()
        self.media_server = MediaServer(
            directory=os.path.dirname(IMG_DIR),  # serve hele EldritchPortal-mappen
            port=HTTP_PORT,
        )

        # Be om Android-tillatelser (feiler gracefully i Pydroid)
        if IS_ANDROID and HAS_ANDROID_API:
            try:
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.READ_MEDIA_IMAGES,
                    Permission.READ_MEDIA_AUDIO,
                    Permission.INTERNET,
                    Permission.ACCESS_NETWORK_STATE,
                    Permission.ACCESS_WIFI_STATE,
                    Permission.CHANGE_WIFI_MULTICAST_STATE,
                ])
            except Exception as e:
                print(f"Tillatelser feilet (Pydroid?): {e}")

        # Hovedlayout
        root = BoxLayout(orientation='vertical', spacing=0)

        # --- Toppbar med faner ---
        tab_bar = BoxLayout(size_hint_y=None, height=50, spacing=2, padding=[5, 2])

        self.tab_images = ToggleButton(
            text="BILDER", group='tabs', state='down',
            background_color=CLR_BTN_ACTIVE,
            background_normal='',
            color=CLR_ACCENT,
            bold=True,
        )
        self.tab_music = ToggleButton(
            text="MUSIKK", group='tabs',
            background_color=CLR_BTN,
            background_normal='',
            color=CLR_TEXT,
            bold=True,
        )
        self.tab_cast = ToggleButton(
            text="CAST", group='tabs',
            background_color=CLR_BTN,
            background_normal='',
            color=CLR_TEXT,
            bold=True,
        )

        self.tab_images.bind(on_release=lambda x: self.show_tab('images'))
        self.tab_music.bind(on_release=lambda x: self.show_tab('music'))
        self.tab_cast.bind(on_release=lambda x: self.show_tab('cast'))

        tab_bar.add_widget(self.tab_images)
        tab_bar.add_widget(self.tab_music)
        tab_bar.add_widget(self.tab_cast)
        root.add_widget(tab_bar)

        # --- Innholdspaneler ---
        self.gallery = ImageGallery(app_ref=self)
        self.music = MusicPlayer(app_ref=self)
        self.cast_panel = CastPanel(app_ref=self)

        self.content_area = BoxLayout()
        self.content_area.add_widget(self.gallery)
        root.add_widget(self.content_area)

        # --- Statuslinje ---
        self.status_bar = StatusBar(text=f"Bilder: {IMG_DIR}")
        root.add_widget(self.status_bar)

        # Start mediaserver og last innhold
        Clock.schedule_once(lambda dt: self._init_content(), 1.5)

        return root

    def _init_content(self):
        """Initialiser innhold etter at appen har startet."""
        self.media_server.start()
        self.gallery.load_images()
        self.music.load_tracks()

        ip = MediaServer.get_local_ip()
        cast_status = "Cast klar" if CAST_AVAILABLE else "Cast utilgj."
        self.status_bar.text = f"IP: {ip} | {cast_status}"

    def show_tab(self, tab_name):
        """Bytt mellom faner."""
        self.content_area.clear_widgets()
        tabs = {
            'images': (self.gallery, self.tab_images),
            'music': (self.music, self.tab_music),
            'cast': (self.cast_panel, self.tab_cast),
        }
        for name, (widget, btn) in tabs.items():
            if name == tab_name:
                self.content_area.add_widget(widget)
                btn.background_color = CLR_BTN_ACTIVE
                btn.color = CLR_ACCENT
            else:
                btn.background_color = CLR_BTN
                btn.color = CLR_TEXT

    def on_stop(self):
        """Rydd opp ved avslutning."""
        self.media_server.stop()
        self.cast_mgr.disconnect()
        if self.music.sound:
            self.music.stop()


# ============================================================
if __name__ == '__main__':
    import traceback
    _crash_log = "/sdcard/Documents/EldritchPortal/crash.log"
    os.makedirs(os.path.dirname(_crash_log), exist_ok=True)
    try:
        EldritchPortalApp().run()
    except Exception:
        err = traceback.format_exc()
        print(err)
        try:
            with open(_crash_log, "w") as f:
                f.write(err)
        except Exception:
            pass
        raise
