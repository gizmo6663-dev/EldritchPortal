[app]

# Appnavn og pakke
title = Eldritch Portal
package.name = eldritchportal
package.domain = org.rpg

# Kildekode
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Versjon
version = 0.1

# =============================================================
#  KRAV - NB: rekkefølge og versjonering er viktig!
# =============================================================
# Fase 1: Uten casting (bruk denne linjen først for å verifisere at APK bygger)
requirements = python3,kivy==2.3.0,pillow,android

# Fase 2: Med casting (bytt til denne når Fase 1 fungerer)
# requirements = python3,kivy==2.3.0,pillow,android,pychromecast==14.0.1,zeroconf==0.131.0,ifaddr==0.2.0,protobuf==4.25.3,casttube

# =============================================================
#  ANDROID-INNSTILLINGER
# =============================================================

# API-nivåer (viktig for S25 Ultra med Android 15)
android.api = 34
android.minapi = 26
android.ndk = 25b

# Arkitektur (S25 Ultra bruker arm64)
android.archs = arm64-v8a

# Tillatelser (alle som trengs for bilder, musikk og nettverkscast)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_MULTICAST_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_AUDIO,READ_MEDIA_VIDEO

# Skjerm og orientering
orientation = portrait
fullscreen = 0

# Android-spesifikke flagg
android.accept_sdk_license = True
android.skip_update = False

# Tillat lagring på ekstern lagring (viktig for å lese bilder/musikk)
android.private_storage = False

# =============================================================
#  PYTHON-FOR-ANDROID INNSTILLINGER
# =============================================================

# Bruk nyeste p4a for best Android 15-støtte
# p4a.branch - bruker standard (stabil) versjon
p4a.bootstrap = sdl2

# Tving ren Python-modus for protobuf (unngår C-kompileringsproblemer)
# Avkommenter denne linjen for Fase 2 (med casting)
# p4a.setup_py_extra_args = --set-env PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# =============================================================
#  APP-METADATA
# =============================================================
# Ikon og splash (legg egne filer i prosjektmappen)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# Logg (nyttig for feilsøking - sett til 2 for produksjon)
log_level = 2

# =============================================================
#  BYGG-INNSTILLINGER
# =============================================================
[buildozer]
log_level = 2
warn_on_root = 1
