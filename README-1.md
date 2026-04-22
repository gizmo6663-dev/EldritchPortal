# Eldritch Portal

**Keeper's Companion — en Kivy-basert Android-app for Call of Cthulhu og Pulp Cthulhu**

Eldritch Portal er en tabletop-RPG-companion bygd spesielt for Lovecraftiske rollespill. Appen samler alt en Keeper trenger under spilløkta: bildebibliotek, stemningslyder, våpenoppslag, scenario-tracker og initiativ-tracker — alt i et mørkt, uhyggelig grensesnitt som passer til sjangeren. Telefonen kan caste bilder og kart til en TV via Chromecast slik at spillerne ser det du vil de skal se.

Tema: **Abyssal Purple** — dyp lilla-svart, burgunder og dempet gull.
Versjon: **0.3.3** · Språk: Norsk · System: Call of Cthulhu / Pulp Cthulhu

---

## Innhold

- [Funksjoner](#funksjoner)
- [Skjermbilder](#skjermbilder)
- [Kom i gang](#kom-i-gang)
- [Scenario-format](#scenario-format)
- [Mappestruktur på enheten](#mappestruktur-på-enheten)
- [Bygging](#bygging)
- [Teknisk arkitektur](#teknisk-arkitektur)
- [Konfigurasjon](#konfigurasjon)
- [Feilsøking](#feilsøking)
- [Veikart](#veikart)

---

## Funksjoner

Appen er delt i seks hovedfaner. Flere av dem har sub-faner for å holde komplekse funksjoner organisert:

### 🖼️ Bilder
- Galleri med mappenavigering for å organisere bilder per scenario eller kampanje
- Stor preview-ramme i gull — fade-inn-animasjon mellom bildebytter
- Tapp et bilde for å vise det; valgfritt auto-cast til TV samtidig
- Gjenkjenner `.png`, `.jpg`, `.jpeg`, `.webp`

### 🔊 Lyd
Kombinert fane med sub-fanene **Musikk** og **Ambient**:

**Musikk** — lokal avspilling
- Leser `.mp3`, `.ogg`, `.wav`, `.flac` fra `music/`-mappen
- Persistent mini-player nederst (Play/Pause/Neste/Forrige) som ikke forsvinner når du bytter fane
- Bruker Android MediaPlayer via `pyjnius` for stabil bakgrunnsavspilling

**Ambient** — stemningslyder strømmet fra Internet Archive
- Kategoriseringen inkluderer blant annet natur, storm, skog om natten, og spesielt horror/uhygge — perfekt for Cthulhu-stemning
- Separat volumkontroll fra musikken, så du kan mikse en regnfull natt med en uhyggelig drone i bakgrunnen
- Ingen opplasting nødvendig — lenkene peker rett på kuraterte public-domain-spor

### ⚔️ Kamp
Sub-faner for combat-støtte:

**Initiativ** — CoC/Pulp Cthulhu-tracker
- Legg til etterforskere og fiender fra karakter-lista, eller ad hoc
- DEX-basert initiativ-sortering (CoC-standard)
- Rundemåling med aktiv-deltaker-indikator
- HP-oppdatering direkte fra trackeren

**Kart** — battlemap for kamp-situasjoner
- Aktiveres automatisk når du har lagt til kamp-deltakere
- 16:9 canvas optimalisert for TV-casting
- Token-komposisjon via Pillow (PIL)

### 🧰 Verktøy
Sub-faner for spillforberedelse og oppslag:

**Karakterer** — etterforsker-kartotek
- CoC/Pulp Cthulhu-karakterark med ferdigheter, bakgrunn og notater
- PC og NPC skilles visuelt med ulik fargekoding
- Lagres i `characters.json` på enheten

**Våpen** — CoC-våpendatabase
- Bundlet `weapons.json` følger med APK-en (ingen ekstern fil nødvendig)
- Søk og filtrer etter kategori, favorittmerking
- Dekker klassiske CoC-epoker: 1920-tallets pulp, moderne osv.
- Overstyrbar: legg egen `weapons.json` i Documents-mappen hvis du vil utvide

**Scenario** — tracker for pre-skrevne scenarioer
- Les inn `scenario.json` med strukturert data fra scenarioet du kjører
- Fire visninger (sub-sub-faner): **Ledetråder** · **Tidslinje** · **Plot** · **Notater**
- Kryss av ledetråder etter hvert som spillerne finner dem, se tidslinjen utfolde seg
- Notater kan redigeres live under spilløkta
- Scenario-filen lagres i app-privat minne (unngår Android 13+ scoped storage-problem), med "Velg fil"- og "Importer"-knapper for å laste inn fra Documents

### 📖 Regler
- Sammenleggbar mappestruktur med CoC/Pulp Cthulhu-referanser
- Overlay-visning for regel-innhold — ingen nettilgang nødvendig
- Raskt oppslag midt i spilløkta

### 📺 Cast
- Oppdager Chromecast-enheter på lokalnett via mDNS
- Caster bilder og battlemaps direkte til TV
- Lokal HTTP-server (port 8089) serverer media til Chromecast
- Auto-cast: bilder caster automatisk når de vises hvis en enhet er tilkoblet

---

## Skjermbilder

*Skjermbilder legges til her.*

---

## Kom i gang

### Installasjon på enhet

1. Last ned siste `EldritchPortal.apk` fra [Releases](https://github.com/gizmo6663-dev/EldritchPortal/releases) eller fra GitHub Actions-artefakter
2. Tillat installering fra ukjente kilder i Android-innstillinger
3. Installer APK-en og start appen
4. Gi tillatelser til lagring og nettverk når du blir spurt
5. Restart appen så mappene faktisk opprettes

### Første oppstart

Ved første oppstart oppretter appen denne mappestrukturen automatisk:

```
Dokumenter/EldritchPortal/
├── images/     ← bildebibliotek (undermapper støttes)
├── music/      ← lokale musikkspor
├── characters.json  ← opprettes når du lager første karakter
└── scenario.json    ← valgfri, importeres via Scenario-fanen
```

Våpendataene (`weapons.json`) er pakket med appen, så du trenger ikke legge til noen fil for å bruke Våpen-fanen.

---

## Scenario-format

Scenario-fanen leser en `scenario.json` med følgende struktur:

```json
{
  "title": "Slow Boat to China",
  "system": "Pulp Cthulhu",
  "clues": [
    {"text": "Kapteinens dagbok nevner en mystisk passasjer",
     "where": "Kahytt 3", "found": false}
  ],
  "timeline": [
    {"text": "Kl. 22:00 — passasjeren forsvinner",
     "where": "Dekk 2", "found": false}
  ],
  "beats": [
    {"text": "Etterforskerne oppdager gjenstanden",
     "where": "Akt 2", "found": false}
  ],
  "notes": [
    {"text": "NPC X er faktisk forkledd...",
     "where": "Keeper", "found": false}
  ]
}
```

Felt:
- `title` — navn på scenarioet (vises i handlings-raden)
- `system` — spillsystemet (f.eks. "Call of Cthulhu", "Pulp Cthulhu")
- `clues`, `timeline`, `beats`, `notes` — lister med hver sin entry per element
  - `text` — innholdet som vises
  - `where` — kontekst (sted, akt, kapittel)
  - `found` — boolean som kan krysses av under spilløkta

Legg `scenario.json` i `Dokumenter/EldritchPortal/`, åpne Scenario-fanen og trykk **Last inn** eller **Velg fil**.

---

## Mappestruktur på enheten

Alle brukerdata ligger i `/sdcard/Documents/EldritchPortal/`:

| Sti | Innhold |
|---|---|
| `images/` | Bildegalleri (undermapper støttes) |
| `music/` | Lokale musikkspor |
| `characters.json` | Karakterer og NPCer |
| `scenario.json` | Scenario-data (importeres inn i app-privat minne) |
| `weapons.json` | *Valgfri* — overstyrer bundlet våpendata |
| `crash.log` | Feillogg for debugging |

I tillegg lagrer appen aktiv scenario-state i app-privat minne (`user_data_dir`) for å unngå scoped storage-restriksjoner i Android 13+.

---

## Bygging

Eldritch Portal bygges som Android APK via GitHub Actions. Workflow-en i `.github/workflows/build-apk.yml` bruker Buildozer inne i en Docker-container (`kivy/buildozer`).

### Bygg via GitHub Actions

1. Push endringer til `main`-branchen — bygging starter automatisk
2. Eller kjør workflow manuelt via **Actions → Build APK → Run workflow**
3. Bruk `clean_build: true`-input hvis du vil tvinge full rebuild
4. Last ned APK fra job-artefakter når workflow er ferdig

### Lokal bygging

```bash
pip install buildozer==1.5.0 cython==0.29.36
buildozer -v android debug
# APK havner i bin/
```

---

## Teknisk arkitektur

### Kjerne-klasser

- **`EldritchApp`** — hovedklasse, bygger UI, håndterer faner og state
- **`MediaServer`** — lokal HTTP-server for å serve media til Chromecast
- **`CastMgr`** — innpakning rundt `pychromecast` for enhetsoppdagelse og kontroll
- **`APlayer`** — Android MediaPlayer-wrapper (via `pyjnius`) for musikk
- **`SPlayer`** — streaming-spiller for ambient-lyder
- **`FPlayer`** — fallback-spiller for desktop/testing
- **`FilePicker`** — filvelger for scenario-import
- **`RBox`**, **`RBtn`**, **`RToggle`**, **`FramedBox`** — tilpassede widgets med bakgrunn/radius

### Designregler

- **All tilpasset bakgrunnstegning skjer i `canvas.before`** — aldri i `canvas` eller `canvas.after`. Tidligere versjoner hadde en `RenderContext`-stack-overflow-krasj som ble fikset ved å sentralisere all canvas-tegning her.
- **`markup=True`** er påkrevd på alle labels som bruker `[color]`-tags.
- **Mini-player er persistent** — den lever utenfor fane-content-området.
- **Sub-fane-state huskes** via `hasattr`-sjekker — du kommer tilbake til samme sub-fane du forlot.
- **Scoped storage-friendly**: våpendata er bundlet med APK, scenario lagres i `user_data_dir`, slik at appen fungerer også på Android 13+ uten omfattende lagringstillatelser.

### Avhengigheter

| Pakke | Rolle |
|---|---|
| `kivy` 2.3.0 | UI-rammeverk |
| `pyjnius` | Android MediaPlayer-binding |
| `pychromecast` | Chromecast-oppdagelse og kontroll |
| `zeroconf`, `ifaddr` | mDNS for Chromecast |
| `protobuf` | Chromecast-protokoll |
| `pillow` | Battlemap-komposisjon |
| `android` | Android plattform-API |

---

## Konfigurasjon

Viktige linjer i `buildozer.spec`:

```ini
requirements = python3,kivy==2.3.0,pillow,android,pyjnius,pychromecast,zeroconf,ifaddr,protobuf,cython<3.0

android.api = 34
android.minapi = 21
android.ndk = 25b
android.enable_androidx = True

# Inkluder weapons.json i APK
source.include_patterns = weapons.json

p4a.branch = v2024.01.21
```

**Pinning-notater:**
- `buildozer==1.5.0` — nyere versjoner har inkompatible argumenter med stabil p4a
- `cython==0.29.36` — Cython 3.x bryter med eldre Kivy-versjoner
- `p4a.branch = v2024.01.21` — tag-format med `v`-prefiks og ledende nuller er obligatorisk
- `android.enable_androidx = True` — uten denne prøver Gradle å hente fra jcenter.bintray.com (403)

---

## Feilsøking

### Appen krasjer ved oppstart
Sjekk `/sdcard/Documents/EldritchPortal/crash.log`. De vanligste årsakene er manglende tillatelser eller korrupt JSON-fil.

### Musikk spilles ikke
- Bekreft at filene ligger i `music/` og har støttet format (`.mp3`, `.ogg`, `.wav`, `.flac`)
- På noen enheter må appen restartes etter at lagringstillatelse er gitt

### Scenario vil ikke lastes
- Sjekk at `scenario.json` ligger i `Dokumenter/EldritchPortal/` og har riktig JSON-syntaks
- Android 13+ kan blokkere lesing fra Documents; bruk **"Velg fil"**-knappen for å åpne filvelger
- Scenarioet lagres deretter i app-privat minne og leses derfra ved neste oppstart

### Våpen-fanen er tom
- Fanen bruker bundlet `weapons.json` inni APK-en
- Hvis fanen er tom, sjekk at `source.include_patterns = weapons.json` er i `buildozer.spec`
- Du kan også plassere en egen `weapons.json` i `Dokumenter/EldritchPortal/` for å overstyre

### Chromecast finner ikke TV
- Telefonen og Chromecast må være på samme Wi-Fi
- HTTP-serveren bruker port 8089 — sjekk at den ikke er blokkert
- Statuslinjen nederst viser lokal IP og cast-tilgjengelighet

### Build-feil: "jcenter.bintray.com 403"
Legg til `android.enable_androidx = True` i `buildozer.spec` og kjør `clean_build`.

---

## Veikart

Mulige fremtidige funksjoner:

- [ ] Terningkast-verktøy (D100, bonus/penalty die)
- [ ] Sanity/Luck-tracker integrert i karakter-fanen
- [ ] Nedtellingstimer for rundetidsbegrensning
- [ ] Lydeffekter (one-shot): døråpning, skrik, skudd
- [ ] Handout-gallerivisning med dramatisk avsløring
- [ ] Eksport av scenario-notater etter spilløkt

---

## Testet på

- Samsung Galaxy S25 Ultra · Android 15

## Utvikling

Eldritch Portal er et hobbyprosjekt utviklet for en aktiv Pulp Cthulhu-kampanje. Bidrag og forslag tas imot via issues på GitHub.

**Repository:** [gizmo6663-dev/EldritchPortal](https://github.com/gizmo6663-dev/EldritchPortal)

**Relatert prosjekt:** [Campaign Forge](https://github.com/gizmo6663-dev/CampaignForge) — en D&D 5e-variant av samme arkitektur, med Emerald Grove-tema.
