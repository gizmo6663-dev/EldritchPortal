import os, sys, traceback, socket, threading, json, random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

LOG = "/sdcard/Documents/EldritchPortal/crash.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
def log(msg):
    with open(LOG, "a") as f: f.write(msg + "\n")
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
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.metrics import dp, sp
    log("Kivy imported OK")

    CAST_AVAILABLE = False
    try:
        import pychromecast; CAST_AVAILABLE = True
    except ImportError: pass

    USE_JNIUS = False; MediaPlayer = None
    if platform == 'android':
        try:
            from jnius import autoclass; MediaPlayer = autoclass('android.media.MediaPlayer')
            USE_JNIUS = True; log("Using Android MediaPlayer")
        except: pass

    BASE_DIR = "/sdcard/Documents/EldritchPortal"
    IMG_DIR = os.path.join(BASE_DIR, "images")
    MUSIC_DIR = os.path.join(BASE_DIR, "music")
    NPC_FILE = os.path.join(BASE_DIR, "npcs.json")
    TRACKER_FILE = os.path.join(BASE_DIR, "trackers.json")
    for d in [IMG_DIR, MUSIC_DIR]: os.makedirs(d, exist_ok=True)

    BG = [0.04, 0.04, 0.06, 1]
    BTN = [0.14, 0.15, 0.18, 1]
    GOLD = [0.85, 0.70, 0.22, 1]
    DIM = [0.45, 0.42, 0.38, 1]
    TXT = [0.75, 0.72, 0.65, 1]
    RED = [0.55, 0.15, 0.15, 1]
    GRN = [0.15, 0.45, 0.25, 1]
    IMG_EXT = ('.png','.jpg','.jpeg','.webp')
    HTTP_PORT = 8089

    AMBIENT_SOUNDS = [
        {"name":"--- Natur ---"}, 
        {"name":"Regn og torden","url":"https://archive.org/download/RainSound13/Gentle%20Rain%20and%20Thunder.mp3"},
        {"name":"Havboelger","url":"https://archive.org/download/naturesounds-soundtheraphy/Birds%20With%20Ocean%20Waves%20on%20the%20Beach.mp3"},
        {"name":"Nattregn","url":"https://archive.org/download/RainSound13/Night%20Rain%20Sound.mp3"},
        {"name":"Vind og storm","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/epic-storm-thunder-rainwindwaves-no-loops-106800.mp3"},
        {"name":"Nattlyder","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/ambience-crickets-chirping-in-very-light-rain-followed-by-gentle-rolling-thunder-10577.mp3"},
        {"name":"Havstorm","url":"https://archive.org/download/naturesounds-soundtheraphy/Sound%20Therapy%20-%20Sea%20Storm.mp3"},
        {"name":"Lett regn","url":"https://archive.org/download/naturesounds-soundtheraphy/Light%20Gentle%20Rain.mp3"},
        {"name":"Tordenstorm","url":"https://archive.org/download/RainSound13/Rain%20Sound%20with%20Thunderstorm.mp3"},
        {"name":"Urolig hav","url":"https://archive.org/download/RelaxingRainAndLoudThunderFreeFieldRecordingOfNatureSoundsForSleepOrMeditation/Relaxing%20Rain%20and%20Loud%20Thunder%20%28Free%20Field%20Recording%20of%20Nature%20Sounds%20for%20Sleep%20or%20Meditation%20Mp3%29.mp3"},
        {"name":"--- Horror ---"},
        {"name":"Skummel atmosfaere","url":"https://archive.org/download/creepy-music-sounds/Creepy%20music%20%26%20sounds.mp3"},
        {"name":"Uhyggelig drone","url":"https://archive.org/download/scary-sound-effects-8/Evil%20Demon%20Drone%20Movie%20Halloween%20Sounds.mp3"},
        {"name":"Mork spenning","url":"https://archive.org/download/scary-sound-effects-8/Dramatic%20Suspense%20Sound%20Effects.mp3"},
        {"name":"Horrorlyder","url":"https://archive.org/download/creepy-music-sounds/Horror%20Sound%20Effects.mp3"},
    ]

    def request_android_permissions():
        if platform != 'android': return
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES,
                Permission.READ_MEDIA_AUDIO, Permission.INTERNET, Permission.ACCESS_NETWORK_STATE,
                Permission.ACCESS_WIFI_STATE, Permission.CHANGE_WIFI_MULTICAST_STATE])
        except Exception as e: log(f"Perm fail: {e}")

    def load_json(path, default=None):
        try:
            with open(path,'r') as f: return json.load(f)
        except: return default if default is not None else []
    def save_json(path, data):
        try:
            with open(path,'w') as f: json.dump(data, f, indent=2, ensure_ascii=False)
        except: pass

    # === Enkel knapp ===
    def mkbtn(text, cb=None, accent=False, danger=False, small=False, **kw):
        b = Button(text=text, background_normal='', background_color=BTN,
                   color=GOLD if accent else (RED if danger else TXT),
                   bold=True, font_size=sp(12) if small else sp(14), **kw)
        if cb: b.bind(on_release=lambda x: cb())
        return b

    # === SERVER ===
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self,f,*a): pass
    class MediaServer:
        def __init__(self): self._httpd=None
        def start(self):
            if self._httpd: return
            try:
                h=partial(QuietHandler,directory=BASE_DIR)
                self._httpd=HTTPServer(('0.0.0.0',HTTP_PORT),h)
                threading.Thread(target=self._httpd.serve_forever,daemon=True).start()
            except: pass
        def stop(self):
            if self._httpd: self._httpd.shutdown(); self._httpd=None
        @staticmethod
        def ip():
            try: s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(("8.8.8.8",80)); r=s.getsockname()[0]; s.close(); return r
            except: return "127.0.0.1"
        def url(self,fp): return f"http://{self.ip()}:{HTTP_PORT}/{os.path.relpath(fp,BASE_DIR)}"

    # === CAST ===
    class CastMgr:
        def __init__(self): self.devices={}; self.cc=None; self.mc=None; self._br=None
        def scan(self,cb=None):
            if not CAST_AVAILABLE: return
            self.devices={}
            def _s():
                try: ccs,br=pychromecast.get_chromecasts(); self._br=br
                except: ccs=[]
                for c in ccs: self.devices[c.cast_info.friendly_name]=c
                if cb: Clock.schedule_once(lambda dt:cb(list(self.devices.keys())),0)
            threading.Thread(target=_s,daemon=True).start()
        def connect(self,name,cb=None):
            if name not in self.devices: return
            def _c():
                try: c=self.devices[name]; c.wait(); self.cc=c; self.mc=c.media_controller; ok=True
                except: ok=False
                if cb: Clock.schedule_once(lambda dt:cb(ok),0)
            threading.Thread(target=_c,daemon=True).start()
        def cast_img(self,url,cb=None):
            if not self.mc: return
            def _c():
                try: self.mc.play_media(url,'image/jpeg'); self.mc.block_until_active(); ok=True
                except: ok=False
                if cb: Clock.schedule_once(lambda dt:cb(ok),0)
            threading.Thread(target=_c,daemon=True).start()
        def disconnect(self):
            try:
                if self._br: self._br.stop_discovery()
                if self.cc: self.cc.disconnect()
            except: pass
            self.cc=None; self.mc=None

    # === PLAYERS ===
    class APlayer:
        def __init__(self): self.mp=None; self.is_playing=False; self._v=0.7
        def play(self,path):
            self.stop()
            try: self.mp=MediaPlayer(); self.mp.setDataSource(path); self.mp.setVolume(self._v,self._v); self.mp.prepare(); self.mp.start(); self.is_playing=True
            except: self.mp=None; self.is_playing=False
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying(): self.mp.stop()
                    self.mp.release()
                except: pass
                self.mp=None
            self.is_playing=False
        def pause(self):
            if self.mp and self.is_playing:
                try: self.mp.pause(); self.is_playing=False
                except: pass
        def resume(self):
            if self.mp and not self.is_playing:
                try: self.mp.start(); self.is_playing=True
                except: pass
        def vol(self,v):
            self._v=v
            if self.mp:
                try: self.mp.setVolume(v,v)
                except: pass

    class SPlayer:
        def __init__(self): self.mp=None; self.is_playing=False; self._v=0.5
        def play_url(self,url):
            self.stop()
            if not USE_JNIUS: return False
            def _s():
                try: self.mp=MediaPlayer(); self.mp.setDataSource(url); self.mp.setVolume(self._v,self._v); self.mp.prepare(); self.mp.start(); self.is_playing=True; log("Stream OK")
                except Exception as e:
                    log(f"Stream err: {e}")
                    if self.mp:
                        try: self.mp.release()
                        except: pass
                        self.mp=None
                    self.is_playing=False
            threading.Thread(target=_s,daemon=True).start(); return True
        def stop(self):
            if self.mp:
                try:
                    if self.mp.isPlaying(): self.mp.stop()
                    self.mp.release()
                except: pass
                self.mp=None
            self.is_playing=False
        def vol(self,v):
            self._v=v
            if self.mp:
                try: self.mp.setVolume(v,v)
                except: pass

    class FPlayer:
        def __init__(self):
            from kivy.core.audio import SoundLoader; self.SL=SoundLoader; self.snd=None; self.is_playing=False; self._v=0.7
        def play(self,path):
            self.stop(); self.snd=self.SL.load(path)
            if self.snd: self.snd.volume=self._v; self.snd.play(); self.is_playing=True
        def stop(self):
            if self.snd:
                try: self.snd.stop()
                except: pass
                self.snd=None
            self.is_playing=False
        def pause(self):
            if self.snd and self.is_playing: self.snd.stop(); self.is_playing=False
        def resume(self):
            if self.snd and not self.is_playing: self.snd.play(); self.is_playing=True
        def vol(self,v):
            self._v=v
            if self.snd: self.snd.volume=v

    # ============================================================
    class EldritchApp(App):
        def build(self):
            log("build() called"); Window.clearcolor=BG; self.title="Eldritch Portal"
            self.tracks=[]; self.ct=-1; self.sel_img=None; self.auto_cast=True
            self.cur_folder=IMG_DIR
            self.player=APlayer() if USE_JNIUS else FPlayer()
            self.streamer=SPlayer(); self.cast=CastMgr(); self.server=MediaServer()
            self.trackers=load_json(TRACKER_FILE,[]); self.inits=[]; self.npcs=load_json(NPC_FILE,[])

            root = BoxLayout(orientation='vertical', spacing=0)
            # Title
            root.add_widget(Label(text="ELDRITCH PORTAL", font_size=sp(18), color=GOLD, bold=True,
                                  size_hint_y=None, height=dp(40)))
            # Tabs
            tabs = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(2), padding=[dp(4),0])
            for key,txt in [('img','Bilder'),('mus','Musikk'),('amb','Ambient'),('tool','Verktoy'),('cast','Cast')]:
                b = ToggleButton(text=txt, group='tabs', state='down' if key=='img' else 'normal',
                    background_normal='', background_down='', background_color=BTN,
                    color=GOLD, bold=True, font_size=sp(13))
                b.bind(on_release=lambda x,k=key: self._tab(k)); tabs.add_widget(b)
            root.add_widget(tabs)
            # Content area
            self.content = BoxLayout(); root.add_widget(self.content)
            # Mini player
            mp = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4), padding=[dp(8),dp(2)])
            self.mp_lbl = Label(text="Ingen musikk", font_size=sp(11), color=DIM, size_hint_x=0.5, halign='left')
            self.mp_lbl.bind(size=self.mp_lbl.setter('text_size')); mp.add_widget(self.mp_lbl)
            mp.add_widget(mkbtn("Forr",self.prev_track,small=True,size_hint_x=None,width=dp(48)))
            self.mp_btn = mkbtn("Play",self.toggle_play,accent=True,small=True,size_hint_x=None,width=dp(48))
            mp.add_widget(self.mp_btn)
            mp.add_widget(mkbtn("Neste",self.next_track,small=True,size_hint_x=None,width=dp(48)))
            root.add_widget(mp)
            # Status
            self.status = Label(text="", font_size=sp(10), color=DIM, size_hint_y=None, height=dp(20))
            root.add_widget(self.status)

            self._tab('img'); log("UI built OK")
            Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
            Clock.schedule_once(lambda dt: self._init(), 3)
            return root

        def _init(self):
            self.server.start(); self._load_imgs(); self._load_tracks()
            self.status.text = f"IP: {MediaServer.ip()} | Cast: {'Ja' if CAST_AVAILABLE else 'Nei'}"

        # === TAB SWITCHING (build on demand) ===
        def _tab(self, k):
            self.content.clear_widgets()
            builders = {'img':self._mk_img,'mus':self._mk_mus,'amb':self._mk_amb,'cast':self._mk_cast,'tool':self._mk_tool}
            if k in builders: self.content.add_widget(builders[k]())

        # === BILDER ===
        def _mk_img(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4))
            self.preview = Image(size_hint_y=0.35, allow_stretch=True, keep_ratio=True)
            if self.sel_img: self.preview.source = self.sel_img
            p.add_widget(self.preview)
            self.img_lbl = Label(text="", font_size=sp(11), color=DIM, size_hint_y=None, height=dp(20))
            p.add_widget(self.img_lbl)
            nav = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4), padding=[dp(4),0])
            self.path_lbl = Label(text="", font_size=sp(10), color=DIM, size_hint_x=0.4)
            nav.add_widget(self.path_lbl)
            nav.add_widget(mkbtn("Tilbake",self.folder_up,small=True,size_hint_x=0.2))
            self.ac_btn = mkbtn("AC:PA",self._toggle_ac,accent=True,small=True,size_hint_x=0.2)
            nav.add_widget(self.ac_btn)
            nav.add_widget(mkbtn("Oppdater",self._load_imgs,small=True,size_hint_x=0.2))
            p.add_widget(nav)
            scroll = ScrollView(size_hint_y=0.4)
            self.img_grid = GridLayout(cols=3, spacing=dp(6), padding=dp(4), size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid); p.add_widget(scroll)
            self._load_imgs(); return p

        def _load_imgs(self):
            if not hasattr(self, 'img_grid'): return
            self.img_grid.clear_widgets()
            f = self.cur_folder
            rel = os.path.relpath(f, IMG_DIR) if f != IMG_DIR else ""
            if hasattr(self, 'path_lbl'): self.path_lbl.text = f"/{rel}/" if rel else "/"
            try:
                if not os.path.exists(f): return
                items = sorted(os.listdir(f))
                dirs = [d for d in items if os.path.isdir(os.path.join(f,d)) and not d.startswith('.')]
                imgs = [x for x in items if x.lower().endswith(IMG_EXT)]
                if hasattr(self, 'img_lbl'): self.img_lbl.text = f"{len(dirs)} mapper, {len(imgs)} bilder"
                for d in dirs:
                    b = mkbtn(f"[{d}]", lambda dn=d: self._enter(dn), accent=True, small=True, size_hint_y=None, height=dp(80))
                    self.img_grid.add_widget(b)
                for fn in imgs:
                    path = os.path.join(f, fn)
                    img = Image(source=path, allow_stretch=True, keep_ratio=True, size_hint_y=None, height=dp(110), mipmap=True)
                    btn = Button(background_color=[0,0,0,0], background_normal='', size_hint_y=None, height=dp(110))
                    btn.add_widget(img)
                    btn.bind(on_release=lambda x, p=path: self._sel_img(p))
                    self.img_grid.add_widget(btn)
            except Exception as e: log(f"load_imgs: {e}")

        def _enter(self, name): self.cur_folder = os.path.join(self.cur_folder, name); self._load_imgs()
        def folder_up(self):
            if self.cur_folder != IMG_DIR: self.cur_folder = os.path.dirname(self.cur_folder); self._load_imgs()
        def _sel_img(self, path):
            self.sel_img = path
            if hasattr(self, 'preview'): self.preview.source = path
            if hasattr(self, 'img_lbl'): self.img_lbl.text = os.path.basename(path); self.img_lbl.color = GOLD
            if self.auto_cast and self.cast.cc and self.cast.mc:
                if hasattr(self, 'img_lbl'): self.img_lbl.text = "Caster..."
                self.cast.cast_img(self.server.url(path), cb=lambda ok: self._cast_done(ok))
        def _cast_done(self, ok):
            if hasattr(self, 'img_lbl'):
                self.img_lbl.text = f"Castet: {os.path.basename(self.sel_img)}" if ok else "Feilet"
        def _toggle_ac(self):
            self.auto_cast = not self.auto_cast
            if hasattr(self, 'ac_btn'): self.ac_btn.text = f"AC:{'PA' if self.auto_cast else 'AV'}"

        # === MUSIKK ===
        def _mk_mus(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4))
            self.trk_lbl = Label(text="Velg et spor", font_size=sp(15), color=DIM, size_hint_y=None, height=dp(36), bold=True)
            p.add_widget(self.trk_lbl)
            ctrl = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
            ctrl.add_widget(mkbtn("Forr",self.prev_track,small=True))
            ctrl.add_widget(mkbtn("Play",self.toggle_play,accent=True))
            ctrl.add_widget(mkbtn("Neste",self.next_track,small=True))
            ctrl.add_widget(mkbtn("Stopp",self.stop_music,danger=True,small=True))
            p.add_widget(ctrl)
            vr = BoxLayout(size_hint_y=None, height=dp(32), padding=[dp(8),0])
            vr.add_widget(Label(text="Vol:", color=DIM, size_hint_x=0.1, font_size=sp(11)))
            sl = Slider(min=0, max=1, value=0.7, size_hint_x=0.9)
            sl.bind(value=lambda s,v: self.player.vol(v)); vr.add_widget(sl); p.add_widget(vr)
            scroll = ScrollView()
            self.trk_grid = GridLayout(cols=1, spacing=dp(3), padding=dp(4), size_hint_y=None)
            self.trk_grid.bind(minimum_height=self.trk_grid.setter('height'))
            scroll.add_widget(self.trk_grid); p.add_widget(scroll)
            self._load_tracks(); return p

        def _load_tracks(self):
            if not hasattr(self, 'trk_grid'): return
            self.trk_grid.clear_widgets(); self.tracks = []
            try:
                if not os.path.exists(MUSIC_DIR): return
                fl = sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                if hasattr(self, 'trk_lbl'): self.trk_lbl.text = f"{len(fl)} spor"
                for i,fn in enumerate(fl):
                    self.tracks.append(os.path.join(MUSIC_DIR,fn))
                    b = mkbtn(fn, lambda idx=i: self.play_track(idx), small=True, size_hint_y=None, height=dp(42))
                    b.halign='left'; self.trk_grid.add_widget(b)
            except Exception as e: log(f"load_tracks: {e}")

        def play_track(self, idx):
            if idx<0 or idx>=len(self.tracks): return
            self.ct=idx; self.player.play(self.tracks[idx]); n=os.path.basename(self.tracks[idx])
            if hasattr(self,'trk_lbl'): self.trk_lbl.text=f"Spiller: {n}"; self.trk_lbl.color=GOLD
            self.mp_lbl.text=n; self.mp_btn.text="Pause"
        def toggle_play(self):
            if not self.player.is_playing and self.ct<0:
                if self.tracks: self.play_track(0); return
            if self.player.is_playing: self.player.pause(); self.mp_btn.text="Play"
            else: self.player.resume(); self.mp_btn.text="Pause"
        def stop_music(self):
            self.player.stop(); self.mp_btn.text="Play"; self.mp_lbl.text="Stoppet"
            if hasattr(self,'trk_lbl'): self.trk_lbl.text="Stoppet"
        def next_track(self):
            if self.tracks: self.play_track((self.ct+1)%len(self.tracks))
        def prev_track(self):
            if self.tracks: self.play_track((self.ct-1)%len(self.tracks))

        # === AMBIENT ===
        def _mk_amb(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))
            p.add_widget(Label(text="Stemningslyder", font_size=sp(16), color=GOLD, bold=True, size_hint_y=None, height=dp(30)))
            scroll = ScrollView(size_hint_y=0.6)
            g = GridLayout(cols=1, spacing=dp(3), padding=dp(4), size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for snd in AMBIENT_SOUNDS:
                if 'url' not in snd:
                    g.add_widget(Label(text=snd['name'], font_size=sp(11), color=DIM, bold=True, size_hint_y=None, height=dp(24)))
                else:
                    g.add_widget(mkbtn(snd['name'], lambda u=snd['url'],n=snd['name']: self._play_amb(u,n), small=True, size_hint_y=None, height=dp(40)))
            scroll.add_widget(g); p.add_widget(scroll)
            p.add_widget(mkbtn("Stopp ambient", self._stop_amb, danger=True, size_hint_y=None, height=dp(40)))
            vr = BoxLayout(size_hint_y=None, height=dp(32), padding=[dp(8),0])
            vr.add_widget(Label(text="Vol:", color=DIM, size_hint_x=0.1, font_size=sp(11)))
            sl = Slider(min=0, max=1, value=0.5, size_hint_x=0.9)
            sl.bind(value=lambda s,v: self.streamer.vol(v)); vr.add_widget(sl); p.add_widget(vr)
            self.amb_lbl = Label(text="", font_size=sp(11), color=DIM, size_hint_y=None, height=dp(22))
            p.add_widget(self.amb_lbl); p.add_widget(Widget(size_hint_y=1)); return p

        def _play_amb(self, url, name):
            self._an=name; self._ac_cnt=0
            if hasattr(self,'amb_lbl'): self.amb_lbl.text=f"Laster: {name}..."
            if self.streamer.play_url(url): Clock.schedule_interval(self._poll_amb, 2)
        def _poll_amb(self, dt):
            self._ac_cnt += 1
            if self.streamer.is_playing:
                if hasattr(self,'amb_lbl'): self.amb_lbl.text=f"Spiller: {self._an}"; self.amb_lbl.color=GRN
                return False
            if self._ac_cnt >= 10:
                if hasattr(self,'amb_lbl'): self.amb_lbl.text=f"Feilet: {self._an}"; self.amb_lbl.color=RED
                return False
            if hasattr(self,'amb_lbl'): self.amb_lbl.text=f"Laster: {self._an} ({self._ac_cnt*2}s)..."
        def _stop_amb(self):
            self.streamer.stop()
            if hasattr(self,'amb_lbl'): self.amb_lbl.text="Stoppet"; self.amb_lbl.color=DIM

        # === CAST ===
        def _mk_cast(self):
            p = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
            if not CAST_AVAILABLE:
                p.add_widget(Label(text="Casting utilgjengelig\npychromecast mangler", font_size=sp(13), color=DIM))
                return p
            self.cast_lbl = Label(text="Ikke tilkoblet", font_size=sp(13), color=DIM, size_hint_y=None, height=dp(30))
            p.add_widget(self.cast_lbl)
            p.add_widget(mkbtn("Sok etter enheter", self._scan, accent=True, size_hint_y=None, height=dp(44)))
            self.cast_sp = Spinner(text="Velg enhet...", values=[], size_hint_y=None, height=dp(44), background_color=BTN, color=TXT)
            p.add_widget(self.cast_sp)
            r = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            r.add_widget(mkbtn("Koble til", self._conn, accent=True, size_hint_x=0.5))
            r.add_widget(mkbtn("Koble fra", self._disc, danger=True, size_hint_x=0.5))
            p.add_widget(r); p.add_widget(Widget(size_hint_y=1)); return p
        def _scan(self):
            if hasattr(self,'cast_lbl'): self.cast_lbl.text="Soker..."
            self.cast.scan(cb=self._on_devs)
        def _on_devs(self, names):
            if names and hasattr(self,'cast_sp'): self.cast_sp.values=names; self.cast_sp.text=names[0]
            if hasattr(self,'cast_lbl'): self.cast_lbl.text=f"Fant {len(names)}" if names else "Ingen funnet"
        def _conn(self):
            if not hasattr(self,'cast_sp'): return
            n=self.cast_sp.text
            if not n or n=="Velg enhet...": return
            if hasattr(self,'cast_lbl'): self.cast_lbl.text="Kobler til..."
            self.cast.connect(n, cb=lambda ok: self._on_conn(ok))
        def _on_conn(self, ok):
            if hasattr(self,'cast_lbl'): self.cast_lbl.text="Tilkoblet!" if ok else "Feilet"
        def _disc(self):
            self.cast.disconnect()
            if hasattr(self,'cast_lbl'): self.cast_lbl.text="Frakoblet"

        # === VERKTOY ===
        def _mk_tool(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4))
            tb = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
            tb.add_widget(mkbtn("NPC", lambda: self._show_tool('npc'), accent=True, size_hint_x=1/3))
            tb.add_widget(mkbtn("Tracker", lambda: self._show_tool('trk'), accent=True, size_hint_x=1/3))
            tb.add_widget(mkbtn("Initiativ", lambda: self._show_tool('ini'), accent=True, size_hint_x=1/3))
            p.add_widget(tb)
            self.tool_area = BoxLayout(); p.add_widget(self.tool_area)
            self._show_tool('npc'); return p

        def _show_tool(self, k):
            if not hasattr(self, 'tool_area'): return
            self.tool_area.clear_widgets()
            mk = {'npc':self._mk_npc, 'trk':self._mk_trk, 'ini':self._mk_ini}
            if k in mk: self.tool_area.add_widget(mk[k]())

        # NPC
        def _mk_npc(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))
            h = BoxLayout(size_hint_y=None, height=dp(32))
            h.add_widget(Label(text="NPC-referanse", font_size=sp(14), color=GOLD, bold=True, size_hint_x=0.6))
            h.add_widget(mkbtn("Last inn", lambda: self._fill_npc(), small=True, size_hint_x=0.4))
            p.add_widget(h)
            scroll = ScrollView()
            self.npc_grid = GridLayout(cols=1, spacing=dp(6), padding=dp(4), size_hint_y=None)
            self.npc_grid.bind(minimum_height=self.npc_grid.setter('height'))
            scroll.add_widget(self.npc_grid); p.add_widget(scroll)
            self._fill_npc(); return p

        def _fill_npc(self):
            self.npcs = load_json(NPC_FILE, [])
            if not hasattr(self, 'npc_grid'): return
            self.npc_grid.clear_widgets()
            if not self.npcs:
                self.npc_grid.add_widget(Label(text='Ingen NPC-er.\nOpprett npcs.json i\nDocuments/EldritchPortal/\n\n[{"name":"Navn","occ":"Yrke",\n"desc":"...","stats":"STR 60",\n"notes":"..."}]',
                    font_size=sp(10), color=DIM, size_hint_y=None, height=dp(140))); return
            for npc in self.npcs:
                nm=npc.get('name','?'); oc=npc.get('occ','')
                self.npc_grid.add_widget(Label(text=f"{nm} - {oc}" if oc else nm,
                    font_size=sp(13), color=GOLD, bold=True, size_hint_y=None, height=dp(22), halign='left'))
                for key in ['desc','stats','notes']:
                    txt=npc.get(key,'')
                    if txt:
                        l = Label(text=txt, font_size=sp(10), color=TXT if key=='desc' else DIM,
                            size_hint_y=None, halign='left', text_size=(Window.width-dp(32), None))
                        l.bind(texture_size=l.setter('size')); self.npc_grid.add_widget(l)
                self.npc_grid.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # TRACKER
        def _mk_trk(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))
            h = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
            h.add_widget(Label(text="Sanity & Luck", font_size=sp(14), color=GOLD, bold=True, size_hint_x=0.5))
            h.add_widget(mkbtn("+Spiller", self._add_trk, accent=True, small=True, size_hint_x=0.25))
            h.add_widget(mkbtn("Lagre", lambda: save_json(TRACKER_FILE, self.trackers), small=True, size_hint_x=0.25))
            p.add_widget(h)
            scroll = ScrollView()
            self.trk_grid = GridLayout(cols=1, spacing=dp(6), padding=dp(4), size_hint_y=None)
            self.trk_grid.bind(minimum_height=self.trk_grid.setter('height'))
            scroll.add_widget(self.trk_grid); p.add_widget(scroll)
            self._fill_trk(); return p

        def _fill_trk(self):
            if not hasattr(self, 'trk_grid'): return
            self.trk_grid.clear_widgets()
            if not self.trackers:
                self.trk_grid.add_widget(Label(text="Trykk +Spiller", font_size=sp(11), color=DIM, size_hint_y=None, height=dp(30))); return
            for i,t in enumerate(self.trackers):
                # Name row
                r0 = BoxLayout(size_hint_y=None, height=dp(28))
                ni = TextInput(text=t.get('name',''), font_size=sp(12), multiline=False, background_color=BTN, foreground_color=GOLD, size_hint_x=0.7, padding=[dp(4),dp(2)])
                ni.bind(text=lambda inst,val,idx=i: self._set_tname(idx,val)); r0.add_widget(ni)
                r0.add_widget(mkbtn("Fjern", lambda idx=i: self._rm_trk(idx), danger=True, small=True, size_hint_x=0.3))
                self.trk_grid.add_widget(r0)
                # SAN row
                for key,lbl in [('san','SAN'),('luck','LUCK')]:
                    row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(2))
                    row.add_widget(Label(text=f"{lbl}:", color=TXT, font_size=sp(11), bold=True, size_hint_x=0.14))
                    for d in [-5,-1]:
                        row.add_widget(mkbtn(str(d), lambda idx=i,k=key,delta=d: self._adj_trk(idx,k,delta), danger=True, small=True, size_hint_x=0.12))
                    val=t.get(key,0); mx=t.get('san_max',0) if key=='san' else None
                    vt=f"{val}/{mx}" if mx else str(val)
                    row.add_widget(Label(text=vt, font_size=sp(13), color=GOLD, bold=True, size_hint_x=0.22))
                    for d in [1,5]:
                        row.add_widget(mkbtn(f"+{d}", lambda idx=i,k=key,delta=d: self._adj_trk(idx,k,delta), accent=True, small=True, size_hint_x=0.12))
                    self.trk_grid.add_widget(row)
                self.trk_grid.add_widget(Widget(size_hint_y=None, height=dp(6)))

        def _add_trk(self):
            n=len(self.trackers)+1
            self.trackers.append({"name":f"Spiller {n}","san":65,"san_max":65,"luck":50})
            self._fill_trk(); save_json(TRACKER_FILE, self.trackers)
        def _rm_trk(self, i):
            if 0<=i<len(self.trackers): self.trackers.pop(i); self._fill_trk(); save_json(TRACKER_FILE, self.trackers)
        def _set_tname(self, i, name):
            if 0<=i<len(self.trackers): self.trackers[i]['name']=name
        def _adj_trk(self, i, key, delta):
            if 0<=i<len(self.trackers):
                t=self.trackers[i]; t[key]=max(0,t.get(key,0)+delta)
                if key=='san': t['san']=min(t['san'],t.get('san_max',99))
                self._fill_trk(); save_json(TRACKER_FILE, self.trackers)

        # INITIATIV
        def _mk_ini(self):
            p = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(4))
            h = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
            h.add_widget(Label(text="Initiativ (d20)", font_size=sp(14), color=GOLD, bold=True, size_hint_x=0.4))
            h.add_widget(mkbtn("Rull!", self._roll_ini, accent=True, small=True, size_hint_x=0.3))
            h.add_widget(mkbtn("Nullstill", lambda: self._clear_ini(), danger=True, small=True, size_hint_x=0.3))
            p.add_widget(h)
            ir = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
            self.ini_name = TextInput(hint_text="Navn", font_size=sp(11), multiline=False, background_color=BTN, foreground_color=TXT, size_hint_x=0.5, padding=[dp(4),dp(2)])
            ir.add_widget(self.ini_name)
            self.ini_dex = TextInput(hint_text="DEX", font_size=sp(11), multiline=False, background_color=BTN, foreground_color=TXT, size_hint_x=0.2, padding=[dp(4),dp(2)], input_filter='int')
            ir.add_widget(self.ini_dex)
            ir.add_widget(mkbtn("Legg til", self._add_ini, accent=True, small=True, size_hint_x=0.3))
            p.add_widget(ir)
            scroll = ScrollView()
            self.ini_grid = GridLayout(cols=1, spacing=dp(3), padding=dp(4), size_hint_y=None)
            self.ini_grid.bind(minimum_height=self.ini_grid.setter('height'))
            scroll.add_widget(self.ini_grid); p.add_widget(scroll)
            self._fill_ini(); return p

        def _add_ini(self):
            nm=self.ini_name.text.strip()
            if not nm: return
            dx=self.ini_dex.text.strip(); dx=int(dx) if dx.isdigit() else 0
            self.inits.append({"name":nm,"dex":dx,"roll":0,"total":0})
            self.ini_name.text=""; self.ini_dex.text=""; self._fill_ini()
        def _roll_ini(self):
            for c in self.inits: c['roll']=random.randint(1,20); c['total']=c['roll']+c['dex']
            self.inits.sort(key=lambda c:c['total'],reverse=True); self._fill_ini()
        def _clear_ini(self): self.inits=[]; self._fill_ini()
        def _fill_ini(self):
            if not hasattr(self,'ini_grid'): return
            self.ini_grid.clear_widgets()
            if not self.inits:
                self.ini_grid.add_widget(Label(text="Legg til og trykk Rull!", font_size=sp(11), color=DIM, size_hint_y=None, height=dp(30))); return
            for i,c in enumerate(self.inits):
                row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(2))
                row.add_widget(Label(text=f"#{i+1}", font_size=sp(11), color=DIM, bold=True, size_hint_x=0.08))
                row.add_widget(Label(text=c['name'], font_size=sp(12), color=TXT, size_hint_x=0.30))
                rt=f"d20={c['roll']}" if c['roll']>0 else "-"
                row.add_widget(Label(text=rt, font_size=sp(10), color=DIM, size_hint_x=0.18))
                row.add_widget(Label(text=f"+{c['dex']}" if c['dex'] else "", font_size=sp(10), color=DIM, size_hint_x=0.10))
                row.add_widget(Label(text=str(c['total']) if c['total']>0 else "-", font_size=sp(14), color=GOLD, bold=True, size_hint_x=0.14))
                row.add_widget(mkbtn("X", lambda idx=i: self._rm_ini(idx), danger=True, small=True, size_hint_x=0.12))
                self.ini_grid.add_widget(row)
        def _rm_ini(self, i):
            if 0<=i<len(self.inits): self.inits.pop(i); self._fill_ini()

        def on_stop(self):
            self.player.stop(); self.streamer.stop(); self.server.stop(); self.cast.disconnect()
            save_json(TRACKER_FILE, self.trackers)

    log("Starting app..."); EldritchApp().run()
except Exception as e: log(f"CRASH: {e}"); log(traceback.format_exc())
