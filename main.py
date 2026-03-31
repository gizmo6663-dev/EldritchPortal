import os, sys, traceback

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")

log("=== APP START ===")

try:
    log("Importing kivy...")
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.image import Image
    from kivy.clock import Clock
    from kivy.core.window import Window
    log("Kivy imported OK")

    IMG_DIR = "/sdcard/Documents/EldritchPortal/images"
    os.makedirs(IMG_DIR, exist_ok=True)

    class TestApp(App):
        def build(self):
            log("build() called")
            Window.clearcolor = (0.08, 0.08, 0.10, 1)
            log("Window color set")

            root = BoxLayout(orientation='vertical', padding=10, spacing=10)
            log("Root layout created")

            root.add_widget(Label(
                text="ELDRITCH PORTAL",
                font_size=24, color=(0.75, 0.65, 0.2, 1),
                size_hint_y=None, height=50
            ))
            log("Header added")

            self.info = Label(text="Trykk OPPDATER", size_hint_y=None, height=30)
            root.add_widget(self.info)
            log("Info label added")

            btn = Button(text="OPPDATER", size_hint_y=None, height=50)
            btn.bind(on_release=lambda x: self.load_images())
            root.add_widget(btn)
            log("Button added")

            scroll = ScrollView(size_hint_y=0.5)
            self.grid = GridLayout(cols=3, spacing=8, padding=8, size_hint_y=None)
            self.grid.bind(minimum_height=self.grid.setter('height'))
            scroll.add_widget(self.grid)
            root.add_widget(scroll)
            log("Grid added")

            log("UI built OK")
            Clock.schedule_once(lambda dt: self.load_images(), 1)
            return root

        def load_images(self):
            log("load_images() called")
            self.grid.clear_widgets()
            try:
                filer = sorted([f for f in os.listdir(IMG_DIR)
                               if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))])
                log(f"Found {len(filer)} images")
                self.info.text = f"{len(filer)} bilder funnet"

                for fname in filer:
                    path = os.path.join(IMG_DIR, fname)
                    btn = Button(text=fname[:12], size_hint_y=None, height=120)
                    btn.bind(on_release=lambda x, p=path: self.select(p))
                    self.grid.add_widget(btn)
            except Exception as e:
                log(f"load_images error: {e}")
                self.info.text = f"Feil: {e}"

        def select(self, path):
            log(f"Selected: {path}")
            self.info.text = os.path.basename(path)

    log("Starting app...")
    TestApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())