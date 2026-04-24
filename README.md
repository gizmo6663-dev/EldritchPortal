# Eldritch Portal

**Keeper's Companion — en gratis, Kivy-basert Android-app for Call of Cthulhu og Pulp Cthulhu**

Eldritch Portal er et lite hobbyprosjekt laget for spillere og Keepere som liker Lovecraftiske rollespill. Målet er å være et praktisk støtteverktøy ved bordet — noe som kan hjelpe med oversikt, lyd, bilder, kamp og scenariohåndtering.

Tema: **Abyssal Purple** — dyp lilla-svart, burgunder og dempet gull.
Versjon: **0.3.3** · Språk: Norsk · System: Call of Cthulhu / Pulp Cthulhu

---

## Innhold

- [Hva appen prøver å være](#hva-appen-prøver-å-være)
- [Funksjoner](#funksjoner)
- [Importer karakterer](#importer-karakterer)
- [Scenario-import og lagring](#scenario-import-og-lagring)
- [Kom i gang](#kom-i-gang)
- [Mappestruktur på enheten](#mappestruktur-på-enheten)
- [Scenario-format](#scenario-format)
- [Scenario-mal for PDF → scenario.json](#scenario-mal-for-pdf--scenariojson)
- [Bygging](#bygging)
- [Teknisk arkitektur](#teknisk-arkitektur)
- [Konfigurasjon](#konfigurasjon)
- [Feilsøking](#feilsøking)
- [Veikart](#veikart)

---

## Hva appen prøver å være

Eldritch Portal er laget som et gratis hjelpemiddel for folk som spiller Call of Cthulhu og Pulp Cthulhu. Det er ikke et kommersielt produkt, og det er ikke laget av et profesjonelt team. Det er et lite verktøy jeg har bygget fordi jeg selv trengte noe som gjorde bordspillet litt enklere.

Jeg prøver derfor å beskrive funksjonene så ærlig som mulig: hva appen faktisk gjør, og hva den er ment å støtte under spilløkta.

---

## Funksjoner

Appen er delt i seks hovedfaner. Flere av dem har sub-faner for å holde ting ryddig:

### 🖼️ Bilder
- Bildegalleri med mappenavigering, slik at bilder kan sorteres per scenario eller kampanje
- Stor preview-ramme med animasjon mellom bildebytter
- Tapp et bilde for å vise det; valgfri auto-cast til TV når Chromecast er koblet til
- Støtter `.png`, `.jpg`, `.jpeg` og `.webp`

### 🔊 Lyd
Kombinert fane med sub-fanene **Musikk** og **Ambient**:

**Musikk** — lokale filer
- Leser `.mp3`, `.ogg`, `.wav` og `.flac` fra `music/`-mappen
- Mini-player nederst som blir værende når du bytter fane
- Bruker Android MediaPlayer via `pyjnius` på Android

**Ambient** — stemningslyder fra Internet Archive
- Utvalg av natur, storm, nattlyder og horror/uhygge
- Egen volumkontroll som kan brukes separat fra musikken
- Ingen opplasting eller egen medieserver nødvendig for selve lydutvalget

### ⚔️ Kamp
Sub-faner for kampstøtte:

**Initiativ** — CoC/Pulp Cthulhu-tracker
- Legg til etterforskere og fiender fra karakterlisten, eller legg inn en deltaker manuelt
- DEX-basert initiativ-sortering
- Rundevisning med aktiv deltaker markert
- HP kan vises i trackeren

**Kart** — battlemap for kamp
- Aktiveres når du har lagt til deltakere i initiativlisten
- 16:9-tilpasset kartvisning laget for TV-casting
- Token-plassering og enkel flytting på rutenett

### 🧰 Verktøy
Sub-faner for forberedelse og oppslag:

**Karakterer** — etterforsker-kartotek
- CoC/Pulp Cthulhu-karakterark med ferdigheter, bakgrunn og notater
- PC og NPC skilles visuelt med ulike farger
- Lagres i `characters.json` på enheten

**Våpen** — CoC-våpenoversikt
- Bundlet `weapons.json` følger med appen
- Søk, filtrering og favorittmerking
- Dekker flere epoker, blant annet 1920-tallet og moderne tid
- Kan overstyres med egen `weapons.json` i Documents-mappen hvis du ønsker det

**Scenario** — scenariohåndtering og fremdrift
- Leser inn en `scenario.json` med strukturert data
- Fire visninger: **Ledetråder** · **Tidslinje** · **Plot** · **Notater**
- Kryss av ting etter hvert som de skjer i spillet
- Notater kan redigeres underveis
- Scenarioet kan importeres og lagres i appens private lagring, som er nyttig på Android 13+ der vanlig filtilgang kan være begrenset

### 📖 Regler
- Sammenleggbar referanseliste med CoC/Pulp Cthulhu-innhold
- Overlay-visning for regeltekst
- Gjort for raskt oppslag under spilløkta, uten å være avhengig av internett

### 📺 Cast
- Oppdager Chromecast-enheter på lokalnett via mDNS
- Caster bilder og battlemaps til TV når en enhet er tilgjengelig
- Lokal HTTP-server på port 8089 serverer media til casting
- Auto-cast kan sende bilder automatisk når de vises

---

## Importer karakterer

Karakterer-fanen har en egen **Importer**-knapp i handlingsraden øverst (ved siden av **+ Ny** og **Oppdater**). Med den kan du laste inn én eller flere karakterer fra en `.json`-fil — uten å gå via scenario-fanen.

### Slik importerer du

1. Åpne **Verktøy → Karakterer**
2. Trykk **Importer** i handlingsraden
3. Velg en `.json`-fil fra Androids filvelger (Documents, Downloads, Drive, osv.)
4. En forhåndsvisning viser antall og navn på karakterene som ble funnet
5. Velg **Slå sammen** eller **Erstatt**

### Støttede JSON-formater

**Alternativ 1 — bare liste:**

```json
[
  {
    "name": "Captain Harrow",
    "type": "NPC",
    "occ": "Ship Captain",
    "dex": 45,
    "hp": 12,
    "san": 60,
    "notes": "Vet mer enn han innrømmer.",
    "skills": { "Listen": "40", "Intimidate": "35" }
  },
  {
    "name": "Dr. Marlowe",
    "type": "PC",
    "occ": "Physician",
    "dex": 55,
    "hp": 10,
    "san": 65,
    "skills": { "Medicine": "70", "First Aid": "60" }
  },
  {
    "name": "Kultist",
    "type": "Fiende",
    "dex": 55,
    "hp": 11,
    "notes": "Kultmedlem.",
    "skills": { "Fighting": "45" }
  }
]
```

**Alternativ 2 — wrapper-objekt** (scenario-pakke-format):

```json
{
  "format": "eldritchportal-scenario-pack",
  "version": 1,
  "scenario": { "title": "Slow Boat to China", "system": "Pulp Cthulhu" },
  "characters": [
    {
      "name": "Captain Harrow",
      "type": "NPC",
      "occ": "Ship Captain",
      "dex": 45,
      "hp": 12,
      "san": 60,
      "notes": "Vet mer enn han innrømmer.",
      "skills": { "Listen": "40", "Intimidate": "35" }
    }
  ]
}
```

Kun `name` og `type` er nødvendig per karakter. Alt annet er valgfritt.

Gyldige `type`-verdier: `"PC"`, `"NPC"`, `"Fiende"`. Importøren normaliserer automatisk varianter som `"enemy"`, `"fiend"`, `"foe"`, `"villain"`, `"monster"` og `"creature"` til `"Fiende"`, og ukjente verdier til `"PC"`.

### Slå sammen vs. erstatt

| Valg | Resultat |
|---|---|
| **Slå sammen** | De importerte karakterene legges til i eksisterende roster |
| **Erstatt** | Eksisterende roster slettes og erstattes med de importerte |

Bruk **Slå sammen** når du legger til karakterer i en pågående kampanje.
Bruk **Erstatt** når du starter et nytt scenario og vil ha en ren roster.

### Karakterfelt som bevares

Importøren bevarer disse feltene:

- Grunninfo: `name`, `type`, `occ`, `archetype`, `age`, `residence`, `birthplace`
- Karakteristikker: `str`, `con`, `siz`, `dex`, `int`, `pow`, `app`, `edu`
- Avledede: `hp`, `mp`, `san`, `luck`, `db`, `build`, `move`, `dodge`
- Tekst: `weapons`, `talents`, `backstory`, `notes`
- Ferdigheter: `skills` (som `{ "Feltnavn": "verdi" }`-objekt)
- Ekstra (scenario-pakke): `initiative`, `token`

Oppføringer uten `name` hoppes over automatisk.

### Bruke eksporterte filer og Claude-genererte pakker

Du kan importere:
- Karakterfiler eksportert fra andre Eldritch Portal-installasjoner
- Scenario-pakker generert av Claude eller andre AI-verktøy

For å be Claude lage en karakterpakke, bruk dette i prompten din:

```text
Generer en JSON-liste med karakterer for Eldritch Portal-appen.
Bruk dette formatet:

[
  {
    "name": "Karakternavn",
    "type": "PC | NPC | Fiende",
    "occ": "Yrke",
    "dex": 45,
    "hp": 10,
    "san": 60,
    "notes": "Keepernotater",
    "skills": { "Feltnavn": "verdi" }
  }
]

Output kun gyldig JSON. Ingen forklaring utenfor JSON-en.
Bruk kun "PC", "NPC" eller "Fiende" som type-verdi.
Ukjente felt: bruk tom streng "".
```

---

## Scenario-import og lagring

Scenario-funksjonen er laget for å gjøre det litt enklere å holde orden på et pre-skrevne scenario mens dere spiller.

Det finnes to måter å få inn et scenario på:

### 1. Velg fil
Dette er den enkleste metoden.
- Trykk **Velg fil**
- Bruk Androids filvelger til å finne `scenario.json`
- Du kan velge fra for eksempel Documents, Downloads, Google Drive eller minnekort
- Ingen ekstra lagringstillatelser er nødvendig for denne metoden

### 2. Importer fra Documents
Hvis appen har tilgang til alle filer, kan du også bruke **Importer fra Documents**.
- Legg `scenario.json` i `Dokumenter/EldritchPortal/`
- Trykk **Importer fra Documents**
- Scenarioet kopieres inn i appens private lagring

Når et scenario er importert eller valgt, lagres det i appens private lagring (`user_data_dir`). Det gjør at scenarioet vanligvis er lettere å bruke videre på Android, også når direkte lesing fra Documents ikke er tilgjengelig.

Scenarioet støtter disse feltene:
- `clues` for ledetråder
- `timeline` for hendelser i rekkefølge
- `beats` for plotpunkter
- `notes` for keepernotater

---

## Kom i gang

### Installasjon på enhet

1. Last ned siste `EldritchPortal.apk` fra [Releases](https://github.com/gizmo6663-dev/EldritchPortal/releases) eller fra GitHub Actions-artefakter
2. Tillat installering fra ukjente kilder i Android-innstillinger
3. Installer APK-en og start appen
4. Gi tillatelser til lagring og nettverk når du blir spurt
5. Start appen på nytt hvis du vil være sikker på at mappene opprettes

### Første oppstart

Ved første oppstart oppretter appen denne mappestrukturen automatisk:

```
Dokumenter/EldritchPortal/
├── images/     ← bildebibliotek (undermapper støttes)
├── music/      ← lokale musikkspor
├── characters.json  ← opprettes når du lager første karakter
└── scenario.json    ← valgfri, kan importeres via Scenario-fanen
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

## Scenario-mal for PDF → scenario.json

Kopier dette inn i Claude eller DeepSeek sammen med PDF-en av scenarioet. Be AI-en fylle ut en komplett `scenario.json` som kan lagres i riktig mappe og importeres i appen.

```text
You are helping create a scenario import file for the GitHub repository `gizmo6663-dev/EldritchPortal`.

Task:
Read the attached PDF scenario and convert it into a scenario file that can be saved into the correct folder in the repository and imported by the app.

What to do:
1. Extract all scenario content from the PDF.
2. Convert it into the exact scenario file format used by EldritchPortal.
3. Preserve the scenario’s structure, headings, objectives, encounter details, rules text, and any other game data as faithfully as possible.
4. Output the finished file content only, with no explanation unless something is truly missing from the PDF.

Important:
- Do not summarize or rewrite the scenario in prose.
- Do not leave placeholders unless the PDF does not contain the information.
- If the repository has an existing scenario schema, naming convention, or folder structure, follow it exactly.
- If the PDF contains tables, bullets, or special formatting, convert them into the project’s required structured format.
- If the file requires metadata, include it.
- If there are images, maps, or other assets in the PDF, only reference them if the project format supports them.
- Make the output directly usable as a file the user can place in the correct scenarios folder and import.

If the format is unclear:
- Infer the correct structure from the project’s existing scenario files and documentation.
- Prefer consistency with the repository over guessing.

Output rules:
- Return only the final scenario file content.
- If multiple files are needed, output each one separately with a clear filename label.
```

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
|
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

- **All tilpasset bakgrunnstegning skjer i `canvas.before`** — aldri i `canvas` eller `canvas.after`. Tidligere versjoner hadde en `RenderContext`-stack-overflow-krasj som ble fikset ved å senke antallet samtidige lag.
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
- På noen enheter må appen startes på nytt etter at lagringstillatelse er gitt

### Scenario vil ikke lastes
- Sjekk at `scenario.json` ligger i `Dokumenter/EldritchPortal/` og har riktig JSON-syntaks
- På Android 13+ kan det være enklest å bruke **Velg fil**-knappen i stedet for direkte lesing fra Documents
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
