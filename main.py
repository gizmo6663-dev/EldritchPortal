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
    from kivy.core.audio import SoundLoader
    from kivy.utils import platform
    log("Kivy imported OK")

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

    class EldritchApp(App):
        def build(self):
            log("build() called")
            Window.clearcolor = CLR_BG
            self.title = "Eldritch Portal"
            self.sound = None
            self.tracks = []
            self.current_track = -1
            self.is_playing = False

            root = BoxLayout(orientation='vertical', spacing=0)

            # Fane-bar
            tab_bar = BoxLayout(size_hint_y=None, height=50, spacing=2, padding=[5,2])
            self.tab_img = ToggleButton(text="BILDER", group='tabs', state='down',
                background_normal='', background_color=CLR_BTN_ACTIVE, color=CLR_ACCENT, bold=True)
            self.tab_mus = ToggleButton(text="MUSIKK", group='tabs',
                background_normal='', background_color=CLR_BTN, color=CLR_TEXT, bold=True)
            self.tab_img.bind(on_release=lambda x: self.show_tab('images'))
            self.tab_mus.bind(on_release=lambda x: self.show_tab('music'))
            tab_bar.add_widget(self.tab_img)
            tab_bar.add_widget(self.tab_mus)
            root.add_widget(tab_bar)

            # Innholdsområde
            self.content = BoxLayout()
            self.img_panel = self._build_image_panel()
            self.mus_panel = self._build_music_panel()
            self.content.add_widget(self.img_panel)
            root.add_widget(self.content)

            # Statuslinje
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

            # Kontroller
            controls = BoxLayout(size_hint_y=None, height=55, spacing=10, padding=[20,5])
            for txt, cb in [("⏮", self.prev_track), ("▶", self.toggle_play),
                           ("⏭", self.next_track), ("⏹", self.stop_music)]:
                b = Button(text=txt, background_normal='', background_color=CLR_BTN,
                          color=CLR_TEXT, bold=True, font_size=20)
                b.bind(on_release=lambda x, f=cb: f())
                controls.add_widget(b)
                if txt == "▶":
                    self.btn_play = b
            panel.add_widget(controls)

            # Volum
            vol_row = BoxLayout(size_hint_y=None, height=40, padding=[20,0])
            vol_row.add_widget(Label(text="Vol:", color=CLR_TEXT, size_hint_x=0.15, font_size=13))
            self.vol_slider = Slider(min=0, max=1, value=0.7, size_hint_x=0.85)
            self.vol_slider.bind(value=self._on_volume)
            vol_row.add_widget(self.vol_slider)
            panel.add_widget(vol_row)

            # Sporliste
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
                               if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))])
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
                               if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
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
            self.stop_music()
            if idx < 0 or idx >= len(self.tracks):
                return
            self.current_track = idx
            path = self.tracks[idx]
            try:
                self.sound = SoundLoader.load(path)
                if self.sound:
                    self.sound.volume = self.vol_slider.value
                    self.sound.play()
                    self.is_playing = True
                    self.btn_play.text = "⏸"
                    self.track_label.text = f"▶ {os.path.basename(path)}"
                    log(f"Playing: {path}")
                else:
                    self.track_label.text = "Kunne ikke laste sporet"
                    log(f"SoundLoader returned None for {path}")
            except Exception as e:
                log(f"play_track error: {e}")
                self.track_label.text = f"Feil: {e}"

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

        def stop_music(self):
            if self.sound:
                self.sound.stop()
                self.sound.unload()
                self.sound = None
            self.is_playing = False
            self.btn_play.text = "▶"

        def next_track(self):
            if self.tracks:
                self.play_track((self.current_track + 1) % len(self.tracks))

        def prev_track(self):
            if self.tracks:
                self.play_track((self.current_track - 1) % len(self.tracks))

        def _on_volume(self, slider, value):
            if self.sound:
                self.sound.volume = value

        def on_stop(self):
            self.stop_music()

    log("Starting app...")
    EldritchApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())