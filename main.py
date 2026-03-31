import os, sys, traceback

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
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    log("Kivy imported OK")

    # Bruk Android MediaPlayer via jnius i stedet for SoundLoader
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

    def request_android_permissions():
        if platform != 'android':
            return
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES,
                Permission.READ_MEDIA_AUDIO,
            ])
            log("Permissions requested")
        except Exception as e:
            log(f"Permission request failed: {e}")

    class AndroidPlayer:
        """Wrapper rundt Android MediaPlayer - stabil sporbytte."""
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
                except Exception as e:
                    log(f"AndroidPlayer pause error: {e}")

        def resume(self):
            if self.mp and not self.is_playing:
                try:
                    self.mp.start()
                    self.is_playing = True
                except Exception as e:
                    log(f"AndroidPlayer resume error: {e}")

        def set_volume(self, vol):
            self._volume = vol
            if self.mp:
                try:
                    self.mp.setVolume(vol, vol)
                except Exception:
                    pass

    class FallbackPlayer:
        """Fallback med SoundLoader for desktop."""
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

    class EldritchApp(App):
        def build(self):
            log("build() called")
            Window.clearcolor = CLR_BG
            self.title = "Eldritch Portal"
            self.tracks = []
            self.current_track = -1

            # Velg lydspiller basert paa plattform
            if USE_JNIUS:
                self.player = AndroidPlayer()
            else:
                self.player = FallbackPlayer()
            log(f"Player: {type(self.player).__name__}")

            root = BoxLayout(orientation='vertical', spacing=0)

            # Fane-bar
            tab_bar = BoxLayout(size_hint_y=None, height=50, spacing=2, padding=[5, 2])
            self.tab_img = ToggleButton(text="BILDER", group='tabs', state='down',
                background_normal='', background_color=CLR_BTN_ACTIVE, color=CLR_ACCENT, bold=True)
            self.tab_mus = ToggleButton(text="MUSIKK", group='tabs',
                background_normal='', background_color=CLR_BTN, color=CLR_TEXT, bold=True)
            self.tab_img.bind(on_release=lambda x: self.show_tab('images'))
            self.tab_mus.bind(on_release=lambda x: self.show_tab('music'))
            tab_bar.add_widget(self.tab_img)
            tab_bar.add_widget(self.tab_mus)
            root.add_widget(tab_bar)

            self.content = BoxLayout()
            self.img_panel = self._build_image_panel()
            self.mus_panel = self._build_music_panel()
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

            btn = Button(text="OPPDATER", size_hint_y=None, height=45,
                        background_normal='', background_color=CLR_BTN, color=CLR_TEXT, bold=True)
            btn.bind(on_release=lambda x: self.load_images())
            panel.add_widget(btn)

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

        def _init_content(self):
            self.load_images()
            self.load_tracks()

        def show_tab(self, tab):
            self.content.clear_widgets()
            if tab == 'images':
                self.content.add_widget(self.img_panel)
                self.tab_img.background_color = CLR_BTN_ACTIVE
                self.tab_img.color = CLR_ACCENT
                self.tab_mus.background_color = CLR_BTN
                self.tab_mus.color = CLR_TEXT
            else:
                self.content.add_widget(self.mus_panel)
                self.tab_mus.background_color = CLR_BTN_ACTIVE
                self.tab_mus.color = CLR_ACCENT
                self.tab_img.background_color = CLR_BTN
                self.tab_img.color = CLR_TEXT

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
                self.img_info.text = os.path.basename(path)
            except Exception as e:
                log(f"select error: {e}")

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

    log("Starting app...")
    EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())