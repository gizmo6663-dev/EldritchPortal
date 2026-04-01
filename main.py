import os, sys, traceback, socket, threading, math, json, random
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
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse, Triangle
    from kivy.animation import Animation
    from kivy.metrics import dp, sp
    from kivy.properties import NumericProperty
    log("Kivy imported OK")

    CAST_AVAILABLE = False
    try:
        import pychromecast; CAST_AVAILABLE = True; log("pychromecast imported OK")
    except ImportError as e: log(f"pychromecast not available: {e}")

    USE_JNIUS = False; MediaPlayer = None
    if platform == 'android':
        try:
            from jnius import autoclass; MediaPlayer = autoclass('android.media.MediaPlayer')
            USE_JNIUS = True; log("Using Android MediaPlayer")
        except Exception as e: log(f"jnius import failed: {e}")

    BASE_DIR = "/sdcard/Documents/EldritchPortal"
    IMG_DIR = os.path.join(BASE_DIR, "images")
    MUSIC_DIR = os.path.join(BASE_DIR, "music")
    NPC_FILE = os.path.join(BASE_DIR, "npcs.json")
    TRACKER_FILE = os.path.join(BASE_DIR, "trackers.json")
    for d in [IMG_DIR, MUSIC_DIR]: os.makedirs(d, exist_ok=True)

    C_VOID=(0.02,0.02,0.04,1); C_ABYSS=(0.05,0.05,0.08,1); C_DEEP=(0.08,0.08,0.12,1)
    C_SURFACE=(0.11,0.12,0.16,1); C_RAISED=(0.15,0.16,0.20,1)
    C_GOLD=(0.85,0.70,0.22,1); C_GOLD_DIM=(0.50,0.40,0.14,1); C_GOLD_BRIGHT=(1.0,0.88,0.40,1)
    C_TEXT=(0.75,0.72,0.65,1); C_TEXT_DIM=(0.45,0.43,0.38,1)
    C_GREEN=(0.12,0.40,0.25,1); C_BLOOD=(0.50,0.10,0.10,1); C_TENTACLE=(0.20,0.12,0.28,1)
    HTTP_PORT = 8089; IMG_EXT = ('.png','.jpg','.jpeg','.webp')

    AMBIENT_SOUNDS = [
        {"cat": "Natur og vaer"},
        {"name":"Regn og torden","url":"https://archive.org/download/RainSound13/Gentle%20Rain%20and%20Thunder.mp3"},
        {"name":"Havboelger","url":"https://archive.org/download/naturesounds-soundtheraphy/Birds%20With%20Ocean%20Waves%20on%20the%20Beach.mp3"},
        {"name":"Nattregn","url":"https://archive.org/download/RainSound13/Night%20Rain%20Sound.mp3"},
        {"name":"Vind og storm","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/epic-storm-thunder-rainwindwaves-no-loops-106800.mp3"},
        {"name":"Nattlyder","url":"https://archive.org/download/rain-sounds-gentle-rain-thunderstorms/ambience-crickets-chirping-in-very-light-rain-followed-by-gentle-rolling-thunder-10577.mp3"},
        {"name":"Havstorm","url":"https://archive.org/download/naturesounds-soundtheraphy/Sound%20Therapy%20-%20Sea%20Storm.mp3"},
        {"name":"Lett regn","url":"https://archive.org/download/naturesounds-soundtheraphy/Light%20Gentle%20Rain.mp3"},
        {"name":"Tordenstorm","url":"https://archive.org/download/RainSound13/Rain%20Sound%20with%20Thunderstorm.mp3"},
        {"name":"Urolig hav","url":"https://archive.org/download/RelaxingRainAndLoudThunderFreeFieldRecordingOfNatureSoundsForSleepOrMeditation/Relaxing%20Rain%20and%20Loud%20Thunder%20%28Free%20Field%20Recording%20of%20Nature%20Sounds%20for%20Sleep%20or%20Meditation%20Mp3%29.mp3"},
        {"cat": "Horror og mystikk"},
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
        except Exception as e: log(f"Permission request failed: {e}")

    def load_json(path, default=None):
        try:
            with open(path,'r') as f: return json.load(f)
        except: return default if default is not None else []

    def save_json(path, data):
        try:
            with open(path,'w') as f: json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e: log(f"save_json error: {e}")

    # === WIDGETS ===
    class EldritchBG(Widget):
        _time = NumericProperty(0)
        def __init__(self, **kw):
            super().__init__(**kw); self.bind(pos=self._draw, size=self._draw)
            Clock.schedule_interval(self._tick, 1/15.0)
        def _tick(self, dt): self._time += dt; self._draw()
        def _draw(self, *a):
            self.canvas.clear(); w,h = self.size; x0,y0 = self.pos
            if w<1 or h<1: return
            t = self._time
            with self.canvas:
                Color(*C_VOID); Rectangle(pos=self.pos, size=self.size)
                for i in range(3):
                    cx=x0+w*(0.2+i*0.3); cy=y0+h*(0.3+math.sin(t*0.3+i)*0.1)
                    r=dp(40)+math.sin(t*0.5+i*2)*dp(15)
                    Color(C_TENTACLE[0],C_TENTACLE[1],C_TENTACLE[2],0.03+math.sin(t*0.4+i)*0.015)
                    Ellipse(pos=(cx-r,cy-r), size=(r*2,r*2))
                for i in range(8):
                    seed=i*137.5; px=x0+((seed+t*8)%w); py=y0+((seed*2.3+t*5)%h)
                    Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],0.08+math.sin(t+seed)*0.04)
                    Ellipse(pos=(px,py), size=(dp(1.5),dp(1.5)))

    class ElderSign(Widget):
        _glow = NumericProperty(0.3)
        def __init__(self, **kw):
            super().__init__(**kw); self.size_hint=(None,None); self.size=(dp(30),dp(30))
            self._anim(); self.bind(pos=self._draw, size=self._draw)
        def _anim(self):
            a=Animation(_glow=0.7,d=2)+Animation(_glow=0.3,d=2)
            a.bind(on_progress=lambda *x:self._draw(), on_complete=lambda *x:self._anim()); a.start(self)
        def _draw(self, *a):
            self.canvas.clear(); cx,cy=self.x+self.width/2,self.y+self.height/2; r=min(self.width,self.height)/2.5
            with self.canvas:
                Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],self._glow*0.5); Line(circle=(cx,cy,r),width=dp(1))
                Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],self._glow)
                for j in range(5):
                    a1,a2=math.radians(j*72-90),math.radians((j+2)*72-90)
                    Line(points=[cx+r*0.9*math.cos(a1),cy+r*0.9*math.sin(a1),cx+r*0.9*math.cos(a2),cy+r*0.9*math.sin(a2)],width=dp(0.8))
                Color(C_GOLD_BRIGHT[0],C_GOLD_BRIGHT[1],C_GOLD_BRIGHT[2],self._glow)
                Ellipse(pos=(cx-dp(2),cy-dp(2)),size=(dp(4),dp(4)))

    class GoldDivider(Widget):
        def __init__(self, **kw):
            super().__init__(**kw); self.size_hint_y=None; self.height=dp(12)
            self.bind(pos=self._draw, size=self._draw); Clock.schedule_once(lambda dt:self._draw(),0)
        def _draw(self, *a):
            self.canvas.clear(); w=self.width; cy=self.y+self.height/2; cx=self.x+w/2
            with self.canvas:
                Color(*C_GOLD_DIM,0.3); Rectangle(pos=(self.x+w*0.05,cy),size=(w*0.9,dp(1)))
                Color(*C_GOLD,0.5); Rectangle(pos=(self.x+w*0.2,cy),size=(w*0.6,dp(1)))
                Color(*C_GOLD,0.7); d=dp(4)
                Triangle(points=[cx,cy+d,cx-d,cy,cx,cy-d]); Triangle(points=[cx,cy+d,cx+d,cy,cx,cy-d])

    class PulsingOrb(Widget):
        _pulse = NumericProperty(0.3)
        def __init__(self, color=C_GOLD, **kw):
            super().__init__(**kw); self.size_hint=(None,None); self.size=(dp(14),dp(14))
            self._color=color; self._active=False; self.bind(pos=self._draw, size=self._draw)
        def start(self): self._active=True; self._go()
        def stop(self): self._active=False; Animation.cancel_all(self,'_pulse'); self._pulse=0.2; self._draw()
        def _go(self):
            if not self._active: return
            a=Animation(_pulse=1.0,d=1.2,t='in_out_sine')+Animation(_pulse=0.3,d=1.2,t='in_out_sine')
            a.bind(on_progress=lambda *x:self._draw(), on_complete=lambda *x:self._go()); a.start(self)
        def _draw(self, *a):
            self.canvas.clear(); cx,cy=self.x+self.width/2,self.y+self.height/2
            with self.canvas:
                Color(self._color[0],self._color[1],self._color[2],self._pulse*0.15)
                Ellipse(pos=(cx-self.width,cy-self.height),size=(self.width*2,self.height*2))
                Color(self._color[0],self._color[1],self._color[2],self._pulse*0.8)
                r=self.width*0.3; Ellipse(pos=(cx-r,cy-r),size=(r*2,r*2))

    class ElButton(Button):
        _ba = NumericProperty(0.25)
        def __init__(self, accent=False, danger=False, small=False, **kw):
            super().__init__(**kw); self.background_normal=''; self.background_down=''; self.background_color=(0,0,0,0)
            self._accent=accent; self._danger=danger
            self.color=C_GOLD if accent else ((0.8,0.3,0.3,1) if danger else C_TEXT)
            self.bold=True; self.font_size=sp(12) if small else sp(14)
            self.bind(pos=self._draw, size=self._draw, state=self._on_state)
            Clock.schedule_once(lambda dt:self._draw(),0)
        def _on_state(self, *a):
            Animation(_ba=0.8 if self.state=='down' else 0.25,d=0.15).start(self)
            self.bind(_ba=lambda *x:self._draw())
        def _draw(self, *a):
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*C_SURFACE); RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(5)])
                bc=C_GOLD if self._accent else (C_BLOOD if self._danger else C_GOLD_DIM)
                Color(bc[0],bc[1],bc[2],self._ba)
                Line(rounded_rectangle=(self.x,self.y,self.width,self.height,dp(5)),width=dp(0.8))

    class ElTab(ToggleButton):
        _bw = NumericProperty(0)
        def __init__(self, **kw):
            super().__init__(**kw); self.background_normal=''; self.background_down=''; self.background_color=(0,0,0,0)
            self.color=C_TEXT_DIM; self.bold=True; self.font_size=sp(13)
            self.bind(pos=self._draw, size=self._draw, state=self._on_state)
            Clock.schedule_once(lambda dt:self._on_state(),0)
        def _on_state(self, *a):
            if self.state=='down': self.color=C_GOLD; Animation(_bw=self.width*0.5,d=0.3,t='out_cubic').start(self)
            else: self.color=C_TEXT_DIM; Animation(_bw=0,d=0.2).start(self)
            self.bind(_bw=lambda *x:self._draw())
        def _draw(self, *a):
            self.canvas.after.clear()
            if self._bw>1:
                bx=self.x+(self.width-self._bw)/2
                with self.canvas.after:
                    Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],0.15)
                    RoundedRectangle(pos=(bx-dp(4),self.y),size=(self._bw+dp(8),dp(6)),radius=[dp(3)])
                    Color(*C_GOLD,0.85)
                    RoundedRectangle(pos=(bx,self.y+dp(1)),size=(self._bw,dp(3)),radius=[dp(1.5)])

    def _frame(w, *a):
        w.canvas.before.clear()
        with w.canvas.before:
            Color(*C_SURFACE); RoundedRectangle(pos=w.pos,size=w.size,radius=[dp(4)])
            Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],0.2)
            Line(rounded_rectangle=(w.x,w.y,w.width,w.height,dp(4)),width=dp(0.6))

    class ImageCard(RelativeLayout):
        def __init__(self, image_path, on_tap=None, **kw):
            super().__init__(**kw); self.size_hint_y=None; self.height=dp(130)
            self.image_path=image_path; self._on_tap=on_tap
            self.bind(pos=self._df, size=self._df)
            self.img=Image(source=image_path, allow_stretch=True, keep_ratio=True,
                pos_hint={'center_x':0.5,'center_y':0.58}, size_hint=(0.85,0.68), mipmap=True, nocache=True)
            self.add_widget(self.img)
            fn=os.path.basename(image_path); short=fn[:12]+".." if len(fn)>12 else fn
            self.add_widget(Label(text=short,font_size=sp(9),color=C_GOLD_DIM,pos_hint={'center_x':0.5,'y':0.0},size_hint=(1,0.15)))
            btn=Button(background_color=(0,0,0,0),background_normal='',pos_hint={'x':0,'y':0},size_hint=(1,1))
            btn.bind(on_release=lambda x:self._on_tap(self.image_path) if self._on_tap else None)
            self.add_widget(btn); Clock.schedule_once(lambda dt:self._df(),0)
        def _df(self, *a):
            self.canvas.before.clear(); m=dp(4)
            with self.canvas.before:
                Color(*C_ABYSS); RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(3)])
                Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],0.6)
                Line(rounded_rectangle=(self.x+m,self.y+m,self.width-m*2,self.height-m*2,dp(2)),width=dp(1.2))
                Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],0.25)
                Line(rounded_rectangle=(self.x+m+dp(3),self.y+m+dp(3),self.width-m*2-dp(6),self.height-m*2-dp(6),dp(1)),width=dp(0.6))

    class FolderCard(RelativeLayout):
        def __init__(self, folder_name, on_tap=None, **kw):
            super().__init__(**kw); self.size_hint_y=None; self.height=dp(100)
            self.folder_name=folder_name; self._on_tap=on_tap
            self.bind(pos=self._d, size=self._d)
            self.add_widget(Label(text="[mappe]",font_size=sp(22),color=C_GOLD_DIM,pos_hint={'center_x':0.5,'center_y':0.65}))
            short=folder_name[:14]+".." if len(folder_name)>14 else folder_name
            self.add_widget(Label(text=short,font_size=sp(10),color=C_GOLD,pos_hint={'center_x':0.5,'y':0.05},size_hint=(1,0.2)))
            btn=Button(background_color=(0,0,0,0),background_normal='',pos_hint={'x':0,'y':0},size_hint=(1,1))
            btn.bind(on_release=lambda x:self._on_tap(self.folder_name) if self._on_tap else None)
            self.add_widget(btn); Clock.schedule_once(lambda dt:self._d(),0)
        def _d(self, *a):
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*C_SURFACE); RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(4)])
                Color(C_GOLD[0],C_GOLD[1],C_GOLD[2],0.3)
                Line(rounded_rectangle=(self.x+dp(2),self.y+dp(2),self.width-dp(4),self.height-dp(4),dp(3)),width=dp(0.8))

    class MiniPlayer(BoxLayout):
        def __init__(self, app_ref, **kw):
            super().__init__(**kw); self.app=app_ref; self.orientation='horizontal'
            self.size_hint_y=None; self.height=dp(48); self.padding=[dp(10),dp(4)]; self.spacing=dp(8)
            self.bind(pos=self._bg, size=self._bg)
            self.track_lbl=Label(text="Ingen musikk",font_size=sp(12),color=C_TEXT_DIM,size_hint_x=0.5,halign='left',shorten=True,shorten_from='right')
            self.track_lbl.bind(size=self.track_lbl.setter('text_size')); self.add_widget(self.track_lbl)
            for txt,cb in [("Forr",self._prev),("Play",self._toggle),("Neste",self._next)]:
                b=Button(text=txt,font_size=sp(11),bold=True,size_hint_x=None,width=dp(52),background_normal='',background_color=(0,0,0,0),color=C_GOLD if txt=="Play" else C_TEXT_DIM)
                b.bind(on_release=lambda x,f=cb:f()); self.add_widget(b)
                if txt=="Play": self.btn_play=b
            self.orb=PulsingOrb(color=C_GREEN); self.add_widget(self.orb)
        def _bg(self, *a):
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*C_ABYSS); Rectangle(pos=self.pos,size=self.size)
                Color(*C_GOLD_DIM,0.2); Line(points=[self.x,self.top,self.right,self.top],width=dp(0.5))
        def update(self, track_name=None, playing=False):
            if track_name: self.track_lbl.text=track_name; self.track_lbl.color=C_GOLD if playing else C_TEXT
            self.btn_play.text="Pause" if playing else "Play"
            if playing: self.orb.start()
            else: self.orb.stop()
        def _toggle(self): self.app.toggle_play()
        def _next(self): self.app.next_track()
        def _prev(self): self.app.prev_track()

    # === SERVER + CAST ===
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self,f,*a): pass
    class MediaServer:
        def __init__(self,directory,port=HTTP_PORT): self.directory=directory; self.port=port; self._httpd=None
        def start(self):
            if self._httpd: return
            try:
                h=partial(QuietHandler,directory=self.directory); self._httpd=HTTPServer(('0.0.0.0',self.port),h)
                threading.Thread(target=self._httpd.serve_forever,daemon=True).start(); log(f"HTTP server on {self.port}")
            except Exception as e: log(f"HTTP server failed: {e}")
        def stop(self):
            if self._httpd: self._httpd.shutdown(); self._httpd=None
        @staticmethod
        def get_local_ip():
            try: s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
            except: return "127.0.0.1"
        def get_url(self,fp): return f"http://{self.get_local_ip()}:{self.port}/{os.path.relpath(fp,self.directory)}"
    class CastManager:
        def __init__(self): self.devices={}; self.active_cast=None; self.mc=None; self._browser=None; self._scanning=False
        def discover(self,cb=None):
            if not CAST_AVAILABLE or self._scanning: return
            self._scanning=True; self.devices={}
            def _s():
                try: ccs,br=pychromecast.get_chromecasts(); self._browser=br
                except Exception as e: log(f"Cast scan: {e}")
                else:
                    for cc in ccs: self.devices[cc.cast_info.friendly_name]=cc
                self._scanning=False
                if cb: Clock.schedule_once(lambda dt:cb(list(self.devices.keys())),0)
            threading.Thread(target=_s,daemon=True).start()
        def connect(self,name,cb=None):
            if name not in self.devices: return
            def _c():
                try: cc=self.devices[name]; cc.wait(); self.active_cast=cc; self.mc=cc.media_controller; ok=True
                except: ok=False
                if cb: Clock.schedule_once(lambda dt:cb(ok),0)
            threading.Thread(target=_c,daemon=True).start()
        def cast_image(self,url,cb=None):
            if not self.mc: return
            def _c():
                try: self.mc.play_media(url,'image/jpeg'); self.mc.block_until_active(); ok=True
                except: ok=False
                if cb: Clock.schedule_once(lambda dt:cb(ok),0)
            threading.Thread(target=_c,daemon=True).start()
        def disconnect(self):
            try:
                if self._browser: self._browser.stop_discovery()
                if self.active_cast: self.active_cast.disconnect()
            except: pass
            self.active_cast=None; self.mc=None

    # === PLAYERS ===
    class AndroidPlayer:
        def __init__(self): self.mp=None; self.is_playing=False; self._vol=0.7
        def play(self,path):
            self.stop()
            try: self.mp=MediaPlayer(); self.mp.setDataSource(path); self.mp.setVolume(self._vol,self._vol); self.mp.prepare(); self.mp.start(); self.is_playing=True
            except Exception as e: log(f"Player error: {e}"); self.mp=None; self.is_playing=False
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
        def set_volume(self,v):
            self._vol=v
            if self.mp:
                try: self.mp.setVolume(v,v)
                except: pass
    class StreamPlayer:
        def __init__(self): self.mp=None; self.is_playing=False; self._vol=0.5
        def play_url(self,url):
            self.stop()
            if not USE_JNIUS: return False
            def _s():
                try: self.mp=MediaPlayer(); self.mp.setDataSource(url); self.mp.setVolume(self._vol,self._vol); self.mp.prepare(); self.mp.start(); self.is_playing=True; log("StreamPlayer: playing OK")
                except Exception as e:
                    log(f"StreamPlayer error: {e}")
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
        def set_volume(self,v):
            self._vol=v
            if self.mp:
                try: self.mp.setVolume(v,v)
                except: pass
    class FallbackPlayer:
        def __init__(self):
            from kivy.core.audio import SoundLoader as SL; self.SL=SL; self.sound=None; self.is_playing=False; self._vol=0.7
        def play(self,path):
            self.stop()
            try: self.sound=self.SL.load(path);
            except: pass
            if self.sound: self.sound.volume=self._vol; self.sound.play(); self.is_playing=True
        def stop(self):
            if self.sound:
                try: self.sound.stop()
                except: pass
                self.sound=None
            self.is_playing=False
        def pause(self):
            if self.sound and self.is_playing: self.sound.stop(); self.is_playing=False
        def resume(self):
            if self.sound and not self.is_playing: self.sound.play(); self.is_playing=True
        def set_volume(self,v):
            self._vol=v
            if self.sound: self.sound.volume=v

    # ============================================================
    #  HOVEDAPP
    # ============================================================
    class EldritchApp(App):
        def build(self):
            log("build() called"); Window.clearcolor=C_VOID; self.title="Eldritch Portal"
            self.tracks=[]; self.current_track=-1; self.selected_image=None; self.auto_cast=True
            self.current_folder=IMG_DIR
            self.player=AndroidPlayer() if USE_JNIUS else FallbackPlayer()
            self.stream_player=StreamPlayer(); self.cast_mgr=CastManager()
            self.media_server=MediaServer(BASE_DIR,HTTP_PORT)
            self.tracker_data=load_json(TRACKER_FILE,[]); self.initiative_list=[]; self.npc_data=load_json(NPC_FILE,[])

            root=FloatLayout()
            self.bg=EldritchBG(pos_hint={'x':0,'y':0},size_hint=(1,1)); root.add_widget(self.bg)
            main=BoxLayout(orientation='vertical',spacing=0,pos_hint={'x':0,'y':0},size_hint=(1,1))
            top=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(105))
            tr=BoxLayout(size_hint_y=None,height=dp(44),padding=[dp(12),dp(6)])
            tr.add_widget(ElderSign()); tr.add_widget(Widget(size_hint_x=None,width=dp(8)))
            tr.add_widget(Label(text="ELDRITCH PORTAL",font_size=sp(19),color=C_GOLD,bold=True,size_hint_x=0.7,halign='left'))
            self.top_orb=PulsingOrb(color=C_GOLD)
            ob=BoxLayout(size_hint_x=None,width=dp(30)); ob.add_widget(self.top_orb); tr.add_widget(ob)
            top.add_widget(tr)
            tb=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(2),padding=[dp(4),0])
            for key,txt in [('img','Bilder'),('mus','Musikk'),('amb','Ambient'),('tool','Verktoy'),('cast','Cast')]:
                t=ElTab(text=txt,group='tabs',state='down' if key=='img' else 'normal')
                t.bind(on_release=lambda x,k=key:self.show_tab(k)); tb.add_widget(t)
            top.add_widget(tb); top.add_widget(GoldDivider()); main.add_widget(top)
            self.content=BoxLayout(padding=[dp(6),dp(4)])
            self.panels={'img':self._bp_img(),'mus':self._bp_mus(),'amb':self._bp_amb(),'cast':self._bp_cast(),'tool':self._bp_tools()}
            self.content.add_widget(self.panels['img']); main.add_widget(self.content)
            self.mini_player=MiniPlayer(app_ref=self); main.add_widget(self.mini_player)
            main.add_widget(GoldDivider())
            self.status=Label(text="",font_size=sp(10),color=C_TEXT_DIM,size_hint_y=None,height=dp(22),halign='center')
            self.status.bind(size=self.status.setter('text_size')); main.add_widget(self.status)
            root.add_widget(main); log("UI built OK")
            Clock.schedule_once(lambda dt:request_android_permissions(),0.5)
            Clock.schedule_once(lambda dt:self._init(),3); return root

        def show_tab(self,k):
            self.content.clear_widgets()
            if k in self.panels: self.content.add_widget(self.panels[k])
        def _init(self):
            self.media_server.start(); self.load_images(); self.load_tracks()
            self.status.text=f"IP: {MediaServer.get_local_ip()}  |  Cast: {'Klar' if CAST_AVAILABLE else 'Nei'}"; self.top_orb.start()

        # === BILDER ===
        def _bp_img(self):
            p=BoxLayout(orientation='vertical',spacing=dp(6))
            self.preview=Image(size_hint_y=0.35,allow_stretch=True,keep_ratio=True); p.add_widget(self.preview)
            self.img_info=Label(text="Trykk bilde for aa vise",font_size=sp(12),color=C_TEXT_DIM,size_hint_y=None,height=dp(22),halign='center')
            self.img_info.bind(size=self.img_info.setter('text_size')); p.add_widget(self.img_info)
            br=BoxLayout(size_hint_y=None,height=dp(38),spacing=dp(4),padding=[dp(4),0])
            self.path_label=Label(text="images/",font_size=sp(10),color=C_TEXT_DIM,size_hint_x=0.4,halign='left',shorten=True,shorten_from='left')
            self.path_label.bind(size=self.path_label.setter('text_size')); br.add_widget(self.path_label)
            for txt,cb in [("Tilbake",self.folder_up),("AC:PA",None),("Oppdater",lambda:self.load_images())]:
                b=ElButton(text=txt,small=True,accent=(txt=="AC:PA"),size_hint_x=0.2)
                if txt=="AC:PA": self.btn_ac=b; b.bind(on_release=lambda x:self._toggle_ac())
                elif cb: b.bind(on_release=lambda x,f=cb:f())
                br.add_widget(b)
            p.add_widget(br)
            scroll=ScrollView(size_hint_y=0.4)
            self.img_grid=GridLayout(cols=3,spacing=dp(6),padding=dp(4),size_hint_y=None)
            self.img_grid.bind(minimum_height=self.img_grid.setter('height'))
            scroll.add_widget(self.img_grid); p.add_widget(scroll); return p

        def load_images(self):
            self.img_grid.clear_widgets(); f=self.current_folder
            rel=os.path.relpath(f,IMG_DIR) if f!=IMG_DIR else ""
            self.path_label.text=f"images/{rel}/" if rel else "images/"
            try:
                if not os.path.exists(f): return
                items=sorted(os.listdir(f))
                dirs=[d for d in items if os.path.isdir(os.path.join(f,d)) and not d.startswith('.')]
                imgs=[x for x in items if x.lower().endswith(IMG_EXT)]
                self.img_info.text=f"{len(dirs)} mapper, {len(imgs)} bilder"
                for d in dirs: self.img_grid.add_widget(FolderCard(folder_name=d,on_tap=self.enter_folder))
                for fn in imgs: self.img_grid.add_widget(ImageCard(image_path=os.path.join(f,fn),on_tap=self.select_image))
            except Exception as e: log(f"load_images error: {e}")
        def enter_folder(self,name): self.current_folder=os.path.join(self.current_folder,name); self.load_images()
        def folder_up(self):
            if self.current_folder!=IMG_DIR: self.current_folder=os.path.dirname(self.current_folder); self.load_images()
        def select_image(self,path):
            try:
                self.preview.source=path; self.selected_image=path; self.img_info.text=os.path.basename(path); self.img_info.color=C_GOLD
                if self.auto_cast and self.cast_mgr.active_cast and self.cast_mgr.mc:
                    self.img_info.text="Caster..."; self.cast_mgr.cast_image(self.media_server.get_url(path),callback=self._ocr)
            except Exception as e: log(f"select error: {e}")
        def _toggle_ac(self):
            self.auto_cast=not self.auto_cast; self.btn_ac.text=f"AC:{'PA' if self.auto_cast else 'AV'}"
            self.btn_ac.color=C_GOLD if self.auto_cast else C_TEXT_DIM
        def _ocr(self,ok):
            self.img_info.text=f"Castet: {os.path.basename(self.selected_image)}" if ok else "Feilet"
            self.img_info.color=C_GOLD if ok else C_BLOOD

        # === MUSIKK ===
        def _bp_mus(self):
            p=BoxLayout(orientation='vertical',spacing=dp(6))
            self.track_label=Label(text="Velg et spor",font_size=sp(16),color=C_TEXT_DIM,size_hint_y=None,height=dp(40),halign='center',bold=True)
            self.track_label.bind(size=self.track_label.setter('text_size')); p.add_widget(self.track_label)
            ctrl=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(6),padding=[dp(8),0])
            for txt,cb in [("Forr",self.prev_track),("Play",self.toggle_play),("Neste",self.next_track),("Stopp",self.stop_music)]:
                b=ElButton(text=txt,accent=(txt=="Play")); b.bind(on_release=lambda x,f=cb:f()); ctrl.add_widget(b)
                if txt=="Play": self.btn_play=b
            p.add_widget(ctrl)
            vr=BoxLayout(size_hint_y=None,height=dp(36),padding=[dp(12),0])
            vr.add_widget(Label(text="Vol:",color=C_TEXT_DIM,size_hint_x=0.1,font_size=sp(12)))
            self.vol_slider=Slider(min=0,max=1,value=0.7,size_hint_x=0.9); self.vol_slider.bind(value=self._ov)
            vr.add_widget(self.vol_slider); p.add_widget(vr); p.add_widget(GoldDivider())
            scroll=ScrollView(size_hint_y=1)
            self.track_grid=GridLayout(cols=1,spacing=dp(3),padding=dp(4),size_hint_y=None)
            self.track_grid.bind(minimum_height=self.track_grid.setter('height'))
            scroll.add_widget(self.track_grid); p.add_widget(scroll); return p
        def load_tracks(self):
            self.track_grid.clear_widgets(); self.tracks=[]
            try:
                if not os.path.exists(MUSIC_DIR): return
                fl=sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3','.ogg','.wav','.flac'))])
                self.track_label.text=f"{len(fl)} spor"
                for i,fn in enumerate(fl):
                    self.tracks.append(os.path.join(MUSIC_DIR,fn))
                    b=ElButton(text=fn,size_hint_y=None,height=dp(46)); b.font_size=sp(12); b.halign='left'
                    b.bind(size=b.setter('text_size'),on_release=lambda x,idx=i:self.play_track(idx)); self.track_grid.add_widget(b)
            except Exception as e: log(f"load_tracks error: {e}")
        def play_track(self,idx):
            if idx<0 or idx>=len(self.tracks): return
            self.current_track=idx; self.player.play(self.tracks[idx]); n=os.path.basename(self.tracks[idx])
            if self.player.is_playing: self.btn_play.text="Pause"; self.track_label.text=f"Spiller: {n}"; self.track_label.color=C_GOLD; self.mini_player.update(n,True)
            else: self.track_label.text="Feil"; self.mini_player.update("Feil",False)
        def toggle_play(self):
            if not self.player.is_playing and self.current_track<0:
                if self.tracks: self.play_track(0); return
            if self.player.is_playing: self.player.pause(); self.btn_play.text="Play"; self.mini_player.update(playing=False)
            else: self.player.resume(); self.btn_play.text="Pause"; self.mini_player.update(playing=True)
        def stop_music(self): self.player.stop(); self.btn_play.text="Play"; self.track_label.text="Stoppet"; self.track_label.color=C_TEXT_DIM; self.mini_player.update("Stoppet",False)
        def next_track(self):
            if self.tracks: self.play_track((self.current_track+1)%len(self.tracks))
        def prev_track(self):
            if self.tracks: self.play_track((self.current_track-1)%len(self.tracks))
        def _ov(self,s,v): self.player.set_volume(v)

        # === AMBIENT ===
        def _bp_amb(self):
            p=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(4))
            p.add_widget(Label(text="Stemningslyder",font_size=sp(18),color=C_GOLD,bold=True,size_hint_y=None,height=dp(35)))
            scroll=ScrollView(size_hint_y=0.55)
            g=GridLayout(cols=1,spacing=dp(4),padding=dp(4),size_hint_y=None)
            g.bind(minimum_height=g.setter('height'))
            for snd in AMBIENT_SOUNDS:
                if 'cat' in snd:
                    l=Label(text=snd['cat'].upper(),font_size=sp(12),color=C_GOLD_DIM,bold=True,size_hint_y=None,height=dp(28),halign='left')
                    l.bind(size=l.setter('text_size')); g.add_widget(l)
                else:
                    b=ElButton(text=snd['name'],size_hint_y=None,height=dp(44))
                    b.bind(on_release=lambda x,u=snd['url'],n=snd['name']:self._pa(u,n)); g.add_widget(b)
            scroll.add_widget(g); p.add_widget(scroll); p.add_widget(GoldDivider())
            bs=ElButton(text="Stopp ambient",danger=True,size_hint_y=None,height=dp(44))
            bs.bind(on_release=lambda x:self._sa()); p.add_widget(bs)
            avr=BoxLayout(size_hint_y=None,height=dp(36),padding=[dp(12),0])
            avr.add_widget(Label(text="Vol:",color=C_TEXT_DIM,size_hint_x=0.1,font_size=sp(12)))
            self.amb_vol=Slider(min=0,max=1,value=0.5,size_hint_x=0.9)
            self.amb_vol.bind(value=lambda s,v:self.stream_player.set_volume(v)); avr.add_widget(self.amb_vol)
            p.add_widget(avr)
            self.amb_status=Label(text="",font_size=sp(12),color=C_TEXT_DIM,size_hint_y=None,height=dp(25))
            p.add_widget(self.amb_status); p.add_widget(Widget(size_hint_y=1)); return p
        def _pa(self,url,name):
            self.amb_status.text=f"Laster: {name}..."; self.amb_status.color=C_GOLD_DIM
            self._an=name; self._ac=0
            if self.stream_player.play_url(url): Clock.schedule_interval(self._poll_a,2)
            else: self.amb_status.text="Ikke tilgjengelig"; self.amb_status.color=C_BLOOD
        def _poll_a(self,dt):
            self._ac+=1
            if self.stream_player.is_playing: self.amb_status.text=f"Spiller: {self._an}"; self.amb_status.color=C_GREEN; return False
            if self._ac>=10: self.amb_status.text=f"Feilet: {self._an}"; self.amb_status.color=C_BLOOD; return False
            self.amb_status.text=f"Laster: {self._an} ({self._ac*2}s)..."
        def _sa(self): self.stream_player.stop(); self.amb_status.text="Stoppet"; self.amb_status.color=C_TEXT_DIM

        # === CAST ===
        def _bp_cast(self):
            p=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(8))
            if not CAST_AVAILABLE:
                self.cast_status=Label(text="Casting utilgjengelig\npychromecast mangler",font_size=sp(14),halign='center',color=C_TEXT_DIM)
                self.cast_status.bind(size=self.cast_status.setter('text_size'))
                p.add_widget(self.cast_status); p.add_widget(Widget(size_hint_y=1)); return p
            self.cast_status=Label(text="Ikke tilkoblet",font_size=sp(14),halign='center',color=C_TEXT_DIM,size_hint_y=None,height=dp(35))
            self.cast_status.bind(size=self.cast_status.setter('text_size')); p.add_widget(self.cast_status)
            self.cast_orb=PulsingOrb(color=C_GOLD)
            o=BoxLayout(size_hint_y=None,height=dp(20)); o.add_widget(Widget()); o.add_widget(self.cast_orb); o.add_widget(Widget()); p.add_widget(o)
            bs=ElButton(text="Sok etter enheter",accent=True,size_hint_y=None,height=dp(48))
            bs.bind(on_release=lambda x:self._sc()); p.add_widget(bs)
            self.cast_spinner=Spinner(text="Velg enhet...",values=[],size_hint_y=None,height=dp(48),background_color=C_SURFACE,color=C_TEXT)
            p.add_widget(self.cast_spinner)
            br=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
            bc=ElButton(text="Koble til",accent=True,size_hint_x=0.5); bc.bind(on_release=lambda x:self._cc()); br.add_widget(bc)
            bd=ElButton(text="Koble fra",danger=True,size_hint_x=0.5); bd.bind(on_release=lambda x:self._dc()); br.add_widget(bd)
            p.add_widget(br); p.add_widget(Widget(size_hint_y=1)); return p
        def _sc(self):
            if not CAST_AVAILABLE: return
            self.cast_status.text="Soker..."; self.cast_orb.start(); self.cast_mgr.discover(cb=self._od)
        def _od(self,names):
            self.cast_orb.stop()
            if names: self.cast_spinner.values=names; self.cast_spinner.text=names[0]; self.cast_status.text=f"Fant {len(names)}"; self.cast_status.color=C_GOLD
            else: self.cast_status.text="Ingen funnet"; self.cast_status.color=C_TEXT_DIM
        def _cc(self):
            n=self.cast_spinner.text
            if not n or n=="Velg enhet...": return
            self.cast_status.text="Kobler til..."; self.cast_orb.start(); self.cast_mgr.connect(n,cb=self._oc)
        def _oc(self,ok):
            if ok: self.cast_status.text=f"Tilkoblet: {self.cast_spinner.text}"; self.cast_status.color=C_GOLD; self.cast_orb.start()
            else: self.cast_status.text="Feilet"; self.cast_status.color=C_BLOOD; self.cast_orb.stop()
        def _dc(self): self.cast_mgr.disconnect(); self.cast_status.text="Frakoblet"; self.cast_status.color=C_TEXT_DIM; self.cast_orb.stop()

        # === VERKTOY ===
        def _bp_tools(self):
            p=BoxLayout(orientation='vertical',spacing=dp(4))
            tb=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(4),padding=[dp(4),0])
            for key,txt in [('npc','NPC'),('trk','Tracker'),('ini','Initiativ')]:
                b=ElButton(text=txt,accent=True,size_hint_x=1/3)
                b.bind(on_release=lambda x,k=key:self._st(k)); tb.add_widget(b)
            p.add_widget(tb); p.add_widget(GoldDivider())
            self.tc=BoxLayout()
            self.tp={'npc':self._bp_npc(),'trk':self._bp_trk(),'ini':self._bp_ini()}
            self.tc.add_widget(self.tp['npc']); p.add_widget(self.tc); return p
        def _st(self,k):
            self.tc.clear_widgets()
            if k in self.tp: self.tc.add_widget(self.tp[k])

        # --- NPC ---
        def _bp_npc(self):
            p=BoxLayout(orientation='vertical',spacing=dp(4),padding=dp(4))
            h=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(4))
            h.add_widget(Label(text="NPC-referanse",font_size=sp(15),color=C_GOLD,bold=True,size_hint_x=0.6))
            rb=ElButton(text="Last inn",small=True,size_hint_x=0.4); rb.bind(on_release=lambda x:self._ln()); h.add_widget(rb)
            p.add_widget(h)
            p.add_widget(Label(text="Fil: npcs.json",font_size=sp(10),color=C_TEXT_DIM,size_hint_y=None,height=dp(16)))
            scroll=ScrollView()
            self.npc_grid=GridLayout(cols=1,spacing=dp(6),padding=dp(4),size_hint_y=None)
            self.npc_grid.bind(minimum_height=self.npc_grid.setter('height'))
            scroll.add_widget(self.npc_grid); p.add_widget(scroll)
            Clock.schedule_once(lambda dt:self._ln(),0.5); return p
        def _ln(self):
            self.npc_data=load_json(NPC_FILE,[]); self.npc_grid.clear_widgets()
            if not self.npc_data:
                self.npc_grid.add_widget(Label(text="Ingen NPC-er.\nOpprett npcs.json:\n[{\"name\":\"Navn\",\n  \"occ\":\"Yrke\",\n  \"desc\":\"...\",\n  \"stats\":\"STR 60\",\n  \"notes\":\"...\"}]",
                    font_size=sp(11),color=C_TEXT_DIM,size_hint_y=None,height=dp(160),halign='center')); return
            for npc in self.npc_data:
                card=BoxLayout(orientation='vertical',size_hint_y=None,padding=dp(6),spacing=dp(2))
                nm=npc.get('name','?'); oc=npc.get('occ','')
                card.add_widget(Label(text=f"{nm} - {oc}" if oc else nm,font_size=sp(14),color=C_GOLD,bold=True,size_hint_y=None,height=dp(24),halign='left'))
                for key,col in [('desc',C_TEXT),('stats',C_TEXT_DIM),('notes',C_GOLD_DIM)]:
                    txt=npc.get(key,'')
                    if txt:
                        l=Label(text=txt,font_size=sp(10),color=col,size_hint_y=None,halign='left',text_size=(Window.width-dp(40),None))
                        l.bind(texture_size=l.setter('size')); card.add_widget(l)
                card.bind(minimum_height=card.setter('height'))
                wrap=BoxLayout(size_hint_y=None,padding=dp(2))
                wrap.bind(pos=lambda w,*a:_frame(w),size=lambda w,*a:_frame(w))
                wrap.add_widget(card); wrap.bind(minimum_height=wrap.setter('height'))
                self.npc_grid.add_widget(wrap)

        # --- TRACKER ---
        def _bp_trk(self):
            p=BoxLayout(orientation='vertical',spacing=dp(4),padding=dp(4))
            h=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(4))
            h.add_widget(Label(text="Sanity & Luck",font_size=sp(15),color=C_GOLD,bold=True,size_hint_x=0.5))
            ab=ElButton(text="+Spiller",accent=True,small=True,size_hint_x=0.25); ab.bind(on_release=lambda x:self._at()); h.add_widget(ab)
            sb=ElButton(text="Lagre",small=True,size_hint_x=0.25); sb.bind(on_release=lambda x:self._svt()); h.add_widget(sb)
            p.add_widget(h)
            scroll=ScrollView()
            self.trk_grid=GridLayout(cols=1,spacing=dp(8),padding=dp(4),size_hint_y=None)
            self.trk_grid.bind(minimum_height=self.trk_grid.setter('height'))
            scroll.add_widget(self.trk_grid); p.add_widget(scroll)
            Clock.schedule_once(lambda dt:self._rt(),0.5); return p
        def _rt(self):
            self.trk_grid.clear_widgets()
            if not self.tracker_data:
                self.trk_grid.add_widget(Label(text="Trykk +Spiller",font_size=sp(12),color=C_TEXT_DIM,size_hint_y=None,height=dp(40))); return
            for i,t in enumerate(self.tracker_data):
                card=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(110),padding=dp(6),spacing=dp(3))
                r1=BoxLayout(size_hint_y=None,height=dp(28))
                ni=TextInput(text=t.get('name',''),font_size=sp(13),multiline=False,background_color=C_SURFACE,foreground_color=C_GOLD,size_hint_x=0.7,padding=[dp(6),dp(4)])
                ni.bind(text=lambda inst,val,idx=i:self._stn(idx,val)); r1.add_widget(ni)
                rb=ElButton(text="Fjern",danger=True,small=True,size_hint_x=0.3); rb.bind(on_release=lambda x,idx=i:self._rmt(idx)); r1.add_widget(rb)
                card.add_widget(r1)
                for key,lbl in [('san','SAN'),('luck','LUCK')]:
                    row=BoxLayout(size_hint_y=None,height=dp(34),spacing=dp(4))
                    row.add_widget(Label(text=f"{lbl}:",color=C_TEXT,font_size=sp(12),bold=True,size_hint_x=0.15))
                    for d in [-5,-1]:
                        b=ElButton(text=str(d),danger=True,small=True,size_hint_x=0.12)
                        b.bind(on_release=lambda x,idx=i,k=key,delta=d:self._adj(idx,k,delta)); row.add_widget(b)
                    val=t.get(key,0); mx=t.get('san_max',0) if key=='san' else None
                    vt=f"{val}/{mx}" if mx is not None else str(val)
                    row.add_widget(Label(text=vt,font_size=sp(14),color=C_GOLD,bold=True,size_hint_x=0.25,halign='center'))
                    for d in [1,5]:
                        b=ElButton(text=f"+{d}",accent=True,small=True,size_hint_x=0.12)
                        b.bind(on_release=lambda x,idx=i,k=key,delta=d:self._adj(idx,k,delta)); row.add_widget(b)
                    card.add_widget(row)
                wrap=BoxLayout(size_hint_y=None,height=dp(115),padding=dp(2))
                wrap.bind(pos=lambda w,*a:_frame(w),size=lambda w,*a:_frame(w))
                wrap.add_widget(card); self.trk_grid.add_widget(wrap)
        def _at(self):
            n=len(self.tracker_data)+1
            self.tracker_data.append({"name":f"Spiller {n}","san":65,"san_max":65,"luck":50}); self._rt(); self._svt()
        def _rmt(self,i):
            if 0<=i<len(self.tracker_data): self.tracker_data.pop(i); self._rt(); self._svt()
        def _stn(self,i,name):
            if 0<=i<len(self.tracker_data): self.tracker_data[i]['name']=name
        def _adj(self,i,key,delta):
            if 0<=i<len(self.tracker_data):
                t=self.tracker_data[i]; t[key]=max(0,t.get(key,0)+delta)
                if key=='san': t['san']=min(t['san'],t.get('san_max',99))
                self._rt(); self._svt()
        def _svt(self): save_json(TRACKER_FILE,self.tracker_data)

        # --- INITIATIV ---
        def _bp_ini(self):
            p=BoxLayout(orientation='vertical',spacing=dp(4),padding=dp(4))
            h=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(4))
            h.add_widget(Label(text="Initiativ (d20)",font_size=sp(15),color=C_GOLD,bold=True,size_hint_x=0.4))
            rr=ElButton(text="Rull!",accent=True,small=True,size_hint_x=0.25); rr.bind(on_release=lambda x:self._ri()); h.add_widget(rr)
            cr=ElButton(text="Nullstill",danger=True,small=True,size_hint_x=0.35); cr.bind(on_release=lambda x:self._ci()); h.add_widget(cr)
            p.add_widget(h)
            ir=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(4))
            self.ini_name=TextInput(hint_text="Navn...",font_size=sp(12),multiline=False,background_color=C_SURFACE,foreground_color=C_TEXT,size_hint_x=0.5,padding=[dp(6),dp(4)])
            ir.add_widget(self.ini_name)
            self.ini_dex=TextInput(hint_text="DEX",font_size=sp(12),multiline=False,background_color=C_SURFACE,foreground_color=C_TEXT,size_hint_x=0.2,padding=[dp(6),dp(4)],input_filter='int')
            ir.add_widget(self.ini_dex)
            ab=ElButton(text="Legg til",accent=True,small=True,size_hint_x=0.3); ab.bind(on_release=lambda x:self._ai()); ir.add_widget(ab)
            p.add_widget(ir); p.add_widget(GoldDivider())
            scroll=ScrollView()
            self.ini_grid=GridLayout(cols=1,spacing=dp(4),padding=dp(4),size_hint_y=None)
            self.ini_grid.bind(minimum_height=self.ini_grid.setter('height'))
            scroll.add_widget(self.ini_grid); p.add_widget(scroll); return p
        def _ai(self):
            nm=self.ini_name.text.strip()
            if not nm: return
            dx=self.ini_dex.text.strip(); dx=int(dx) if dx.isdigit() else 0
            self.initiative_list.append({"name":nm,"dex":dx,"roll":0,"total":0})
            self.ini_name.text=""; self.ini_dex.text=""; self._rfi()
        def _ri(self):
            for c in self.initiative_list: c['roll']=random.randint(1,20); c['total']=c['roll']+c['dex']
            self.initiative_list.sort(key=lambda c:c['total'],reverse=True); self._rfi()
        def _ci(self): self.initiative_list=[]; self._rfi()
        def _rfi(self):
            self.ini_grid.clear_widgets()
            if not self.initiative_list:
                self.ini_grid.add_widget(Label(text="Legg til deltakere og trykk Rull!",font_size=sp(12),color=C_TEXT_DIM,size_hint_y=None,height=dp(40))); return
            for i,c in enumerate(self.initiative_list):
                row=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4),padding=[dp(6),0])
                row.bind(pos=lambda w,*a:self._dir(w),size=lambda w,*a:self._dir(w))
                row.add_widget(Label(text=f"#{i+1}",font_size=sp(12),color=C_GOLD_DIM,bold=True,size_hint_x=0.08))
                row.add_widget(Label(text=c['name'],font_size=sp(13),color=C_TEXT,size_hint_x=0.32,halign='left'))
                rt=f"d20={c['roll']}" if c['roll']>0 else "-"
                row.add_widget(Label(text=rt,font_size=sp(11),color=C_GOLD_DIM,size_hint_x=0.2))
                row.add_widget(Label(text=f"+{c['dex']}" if c['dex']>0 else "",font_size=sp(11),color=C_TEXT_DIM,size_hint_x=0.1))
                tc=C_GOLD if c['total']>0 else C_TEXT_DIM
                row.add_widget(Label(text=str(c['total']) if c['total']>0 else "-",font_size=sp(16),color=tc,bold=True,size_hint_x=0.15))
                xb=ElButton(text="X",danger=True,small=True,size_hint_x=0.15)
                xb.bind(on_release=lambda x,idx=i:self._rmc(idx)); row.add_widget(xb)
                self.ini_grid.add_widget(row)
        def _dir(self,w):
            w.canvas.before.clear()
            with w.canvas.before: Color(*C_SURFACE,0.5); RoundedRectangle(pos=w.pos,size=w.size,radius=[dp(3)])
        def _rmc(self,i):
            if 0<=i<len(self.initiative_list): self.initiative_list.pop(i); self._rfi()

        def on_stop(self):
            self.player.stop(); self.stream_player.stop(); self.media_server.stop(); self.cast_mgr.disconnect(); self._svt()

    log("Starting app..."); EldritchApp().run()
except Exception as e: log(f"CRASH: {e}"); log(traceback.format_exc())
