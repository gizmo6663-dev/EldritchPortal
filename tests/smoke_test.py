"""Røyktest uten skjerm: bygg appen og rendre alle scenariovisninger.

Kjøres slik (Linux; på Windows/macOS holder det med `python3` alene,
siden det finnes en skjerm):

    xvfb-run -a python3 tests/smoke_test.py

Appen får en egen, tom datamappe i systemets temp-område, så testen
aldri rører ekte karakterer eller scenarier.
"""
import os
import sys
import tempfile
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = tempfile.mkdtemp(prefix="eldritch-smoke-")
os.environ["ELDRITCH_DATA_DIR"] = os.path.join(DATA, "shared")
# user_data_dir kommer fra Kivy og utledes av hjemmemappa, så den må
# flyttes hit før Kivy importeres — ellers skriver testen i den ekte.
os.environ["HOME"] = DATA
os.environ["APPDATA"] = DATA
os.environ["XDG_CONFIG_HOME"] = os.path.join(DATA, "config")
# Kivy lager selve app-mappa med os.mkdir, ikke makedirs.
os.makedirs(os.environ["XDG_CONFIG_HOME"], exist_ok=True)
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

sys.path.insert(0, REPO)
os.chdir(REPO)

from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402

captured = {}
_orig_prepare = App._run_prepare


def fake_run(self):
    captured["app"] = self
    _orig_prepare(self)


App.run = fake_run

import main  # noqa: E402,F401

app = captured.get("app")
assert app is not None, "app never built"

failures = []


def pump(seconds=0.4):
    """Advance the Kivy clock far enough for animations and scheduled
    callbacks to actually fire."""
    import time as _t
    end = _t.time() + seconds
    while _t.time() < end:
        Clock.tick()
        _t.sleep(0.01)


def step(name, fn):
    try:
        fn()
        pump(0.05)
        print(f"  ok    {name}")
    except Exception as e:
        failures.append((name, e))
        print(f"  FAIL  {name}: {type(e).__name__}: {e}")
        traceback.print_exc()


print("\n== storage ==")
print("  CHAR_FILE     :", main.CHAR_FILE)
print("  scenarios dir :", app.SCEN_DIR)
lib = app._lib_load()
print("  library items :", [i["id"] for i in lib["items"]])
print("  active        :", lib["active"])
assert main.CHAR_FILE.startswith(app.user_data_dir), \
    "CHAR_FILE still outside app-private storage"
assert lib["items"], "bundled scenario was not seeded into the library"

print("\n== character persistence ==")
app.chars.append({"name": "Testperson", "type": "PC"})
main.save_json(main.CHAR_FILE, app.chars)
reloaded = main.load_json(main.CHAR_FILE, [])
assert any(c.get("name") == "Testperson" for c in reloaded), \
    "characters did not survive a save/load round trip"
print("  ok    characters survive save/load")

print("\n== scenario views ==")
step("open tool tab", lambda: (app._tab("tool"), pump(0.5)))
step("scenario subtab", lambda: app._tool_switch("scen"))

for view in ("overview", "timeline", "beats", "clues", "npcs",
             "locations", "handouts", "reference", "notes", "sessions",
             "library"):
    step(f"view {view}", lambda v=view: app._scen_switch_view(v))

print("\n== every checkable section round-trips ==")
app._scen_switch_view("clues")
data = app._scen_data
sid = app._scen_id
# Kryss av ett element i hver seksjon som har et avkryssings-felt.
checked = {}
for section, flag in app.FLAG_KEYS.items():
    items = data.get(section) or []
    if not items:
        continue
    app._scen_toggle(items[0], flag)
    checked[section] = (items[0]["id"], flag)
app._scen_data["notes"] = "Spillerne mistenker Hallander."
app._scen_data["npcs"][0]["user_notes"] = "Spillerne har møtt denne."
app._scen_save()

app._scen_data = None
app._scen_load()
for section, (item_id, flag) in checked.items():
    item = next(x for x in app._scen_data[section] if x["id"] == item_id)
    assert item.get(flag), f"{section}.{flag} was not persisted"
    print(f"  ok    {section}.{flag} persisted")
assert app._scen_data["npcs"][0].get("user_notes"), \
    "per-item notes were not persisted"
print("  ok    per-item notes persisted")

prog = app._prog_load(sid)
assert prog["flags"], "flag was not written to the progress file"
assert prog["notes"], "notes were not written to the progress file"

print("\n== progress survives re-import ==")
data = app._scen_data
first_clue = data["clues"][0]

# Re-import the same file, exactly as picking it again would.
fresh = main.load_json(os.path.join(REPO, "scenarios",
                                    "slow-boat-to-china.json"), None)
app._lib_add(app._ensure_ids(fresh))
app._scen_data = None
app._scen_load()
still = app._scen_data
assert still["clues"][0].get("found"), \
    "re-import wiped the checked clue"
assert still["notes"] == "Spillerne mistenker Hallander.", \
    "re-import wiped the notes"
print("  ok    checkmarks and notes survive a re-import")

print("\n== a bundled update replaces content but keeps progress ==")
# Simuler en eldre installasjon: gammel 'seeded'-liste, og et innhold
# med lavere versjon enn det som ligger i appen.
lib = app._lib_load()
bundle_name = "slow-boat-to-china.json"
lib["seeded"] = [bundle_name]          # gammelt listeformat
app._lib_save(lib)
stale = main.load_json(app._lib_content_path(sid), None)
stale["title"] = "Utdatert tittel"
stale["version"] = 1
main.save_json(app._lib_content_path(sid), stale)

before = app._prog_load(sid)
app._lib_seed_bundled()
app._scen_data = None
app._scen_load()
after = app._prog_load(sid)

assert app._scen_data["title"] != "Utdatert tittel", \
    "the bundled update did not replace the stale content"
assert after["flags"] == before["flags"], \
    "the bundled update clobbered the saved checkmarks"
assert after["notes"] == before["notes"], \
    "the bundled update clobbered the saved notes"
seeded = app._lib_load()["seeded"]
assert isinstance(seeded, dict) and seeded.get(bundle_name) == \
    main.load_json(os.path.join(REPO, "scenarios", bundle_name), {})["version"], \
    "the seeded version was not recorded"
print("  ok    content updated, progress kept, version recorded")

print("\n== the scenario reads as Norwegian ==")
first_beat = app._scen_data["beats"][0]
assert "Akt" in first_beat["act"], f"act not translated: {first_beat['act']}"
assert app._scen_data["handouts"][0].get("read_aloud"), \
    "handout is missing its read-aloud text"
print("  ok    act =", first_beat["act"])
print("  ok    handout 1 has read_aloud")

print("\n== detail overlays ==")
step("clue detail", lambda: app._scen_show_detail(
    data["clues"][0]["title"], data["clues"][0]["description"],
    data["clues"][0]))
step("close overlay", app._scen_close_overlay)
step("npc statblock", lambda: app._scen_show_npc(data["npcs"][0]))
step("close overlay", app._scen_close_overlay)
step("handout detail", lambda: app._scen_show_detail(
    data["handouts"][0]["title"], data["handouts"][0]["description"],
    data["handouts"][0]))
step("close overlay", app._scen_close_overlay)
step("reference detail", lambda: app._scen_show_detail(
    data["reference"][0]["title"], data["reference"][0]["description"],
    data["reference"][0]))
step("close overlay", app._scen_close_overlay)

print("\n== notes autosave ==")
app._scen_switch_view("notes")
app._scen_notes_input.text = "Autolagringstest"
pump(0.2)
step("flush pending", app._flush_pending)
assert app._prog_load(sid)["notes"] == "Autolagringstest", \
    "autosave did not reach disk"
print("  ok    notes autosave reaches disk")

print("\n== other tabs still build ==")
for tab in ("img", "snd", "cmb", "rules", "cast", "tool"):
    step(f"tab {tab}", lambda t=tab: (app._tab(t), pump(0.5)))

print("\n== scenario switching ==")
step("library view", lambda: app._scen_switch_view("library"))

if failures:
    print(f"\n{len(failures)} FAILURES")
    sys.exit(1)
print("\nALL OK")
