import os, sys, traceback

# Skriv logg FØR noe annet importeres
LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")

log("=== APP START ===")
log(f"Python: {sys.version}")
log(f"Platform: {sys.platform}")
log(f"CWD: {os.getcwd()}")

try:
    log("Importing kivy...")
    from kivy.app import App
    log("Importing Label...")
    from kivy.uix.label import Label
    log("Kivy imported OK")

    class TestApp(App):
        def build(self):
            log("build() called")
            return Label(text="Eldritch Portal fungerer!", font_size=40)

    log("Starting app...")
    TestApp().run()

except Exception as e:
    log(f"CRASH: {e}")
    log(traceback.format_exc())