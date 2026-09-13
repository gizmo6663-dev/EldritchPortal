# Eldritch Portal

**Keeper's Companion — en gratis, Kivy-basert app for Call of Cthulhu og Pulp Cthulhu. Android, PC og nettleser.**

Eldritch Portal er et lite hobbyprosjekt laget for spillere og Keepere som liker Lovecraftiske rollespill. Målet er å være et praktisk støtteverktøy ved bordet — noe som kan hjelpe med oversikt, lyd, bilder, kamp og scenariohåndtering.

Tema: **Abyssal Purple** — dyp lilla-svart, burgunder og dempet gull.
Versjon: **0.5.0** · Språk: Norsk · System: Call of Cthulhu / Pulp Cthulhu

### Tre måter å kjøre den på

| | Hva du får |
|---|---|
| **Android** | Full app: bilder, lyd, kamp, cast, karakterer, scenariobibliotek |
| **PC** (`python3 main.py`) | Samme app, samme kode — se [På PC](#på-pc) |
| **Nettleser** (`web/index.html`) | Keeper-konsollen: scenario, roller, fiendebank og kamptracker — se [I nettleseren](#i-nettleseren) |

---

## Innhold

- [Hva appen prøver å være](#hva-appen-prøver-å-være)
- [Funksjoner](#funksjoner)
- [Importer karakterer](#importer-karakterer)
- [Scenario-import og lagring](#scenario-import-og-lagring)
- [På PC](#på-pc)
- [Fiendebank](#fiendebank)
- [Roller og kamp](#roller-og-kamp)
- [Trusler og taktikk](#trusler-og-taktikk)
- [I nettleseren](#i-nettleseren)
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

## Skjermbilder

<table>
  <tr>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172144_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172144_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172152_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172152_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172157_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172157_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172200_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172200_Eldritch%20Portal.jpg" width="400"/></details></td>
  </tr>
  <tr>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172203_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172203_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172211_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172211_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172235_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172235_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172244_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172244_Eldritch%20Portal.jpg" width="400"/></details></td>
  </tr>
  <tr>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172312_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172312_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172317_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172317_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172322_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172322_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172326_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172326_Eldritch%20Portal.jpg" width="400"/></details></td>
  </tr>
  <tr>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172333_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172333_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td align="center"><details><summary><img src="screenshots/Screenshot_20260511_172346_Eldritch%20Portal.jpg" width="150"/></summary><img src="screenshots/Screenshot_20260511_172346_Eldritch%20Portal.jpg" width="400"/></details></td>
    <td></td>
    <td></td>
  </tr>
</table>

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
- Kan laste opp egen ambientfil via Android-filvelger
- Egen opplastet ambient kan loopes sømløst og stoppes fra samme fane
- Ingen opplasting eller egen medieserver nødvendig for selve lydutvalget

### 🗣️ Opplesing av spilløkter
Nettleserversjonen kan lese oppsummeringen av en spilløkt høyt. Knappen
**Les opp** ligger i sesjonskortet, og den har to motorer.

**Nevral (edge-tts) — den som høres bra ut**
Microsofts norske nevrale stemmer, gratis og uten nøkkel, men de krever
nett. Standard er `nb-NO-PernilleNeural`; mannsstemmen er
`nb-NO-FinnNeural`.

En nettside kan ikke snakke med Termux av seg selv. Løsningen er at
Termux — eller PC-en — serverer sida, så ligger appen og talesyntesen
på samme sted.

**På PC (enklest — Termux trengs ikke):**

```sh
pip install edge-tts
python3 tools/opplesing_server.py --apne
```

Windows: bruk `py` eller `python` i stedet for `python3`.

**I Termux:**

```sh
pkg install python git
pip install edge-tts
git clone https://github.com/gizmo6663-dev/EldritchPortal
cd EldritchPortal
termux-wake-lock                       # så Android ikke dreper den
python tools/opplesing_server.py --apne
```

Uten `--apne`: åpne `http://127.0.0.1:8765` i nettleseren selv. Termux
må stå og kjøre mens du bruker appen — bytt til nettleseren, ikke lukk
Termux.

**Servere fra PC og bruke telefonen:** start med `--alle` på PC-en og
åpne `http://<pc-ens-ip>:8765` på telefonen. Endepunktet er da åpent for
alle på nettet, så gjør det bare hjemme.

Da velger «Les opp» den nevrale motoren av seg selv, du får stemmevalg,
tempo og dybde i edge-tts sine egne enheter, og lyden kan lastes ned som
mp3. Samme tekst med samme innstillinger lages bare én gang og
mellomlagres. `--alle` slipper til andre maskiner i samme nett — bare på
et nett du stoler på, for endepunktet er åpent.

**Nettleserstemmen — den som alltid virker**
Brukes når serveren ikke er der. Den koster ingenting og virker uten
nett, men den bruker stemmene som ligger på maskinen, og de er ikke i
nærheten av de nevrale. Norske stemmer rangeres øverst, mannsstemmer
først.

**Tempo og dybde**
Roen skal komme av tempoet, ikke av tonehøyden: å skyve dybden ned gir
metallisk klang og grøtete konsonanter. Standard er derfor et lite hakk
langsommere og tonehøyde urørt — `-8 %` og `0 Hz` nevralt, `0,95` og
`1,0` i nettleseren.

**Uten server: `tools/opplesing.py`**
Lager mp3-en fra en eksportert fil i stedet.

```sh
python3 tools/opplesing.py ~/storage/downloads/sesjon-1-opplesing.txt --spill
```

Skriptet tar også markdown-eksporten direkte — det vasker bort
overskrifter, stjerner og lenker, skriver om `2026-09-13` til «13.
september 2026» og `11:43` til «klokka 11 43», slik at teksten leses som
tekst og ikke som tegn.

| Flagg | Gjør |
| --- | --- |
| `--spill` | spiller av med én gang (`termux-media-player`, `mpv`, `ffplay`) |
| `--tekst` | skriver ut hva som faktisk blir lest, uten å lage lyd |
| `--stemmer` | lister de norske stemmene tjenesten har |
| `-v`, `--tempo`, `--dybde` | stemme, `--rate` og `--pitch` for edge-tts |
| `--stemning` | rom og klang lagt på etterpå (se under) |
| `--drone` | en lav tone under stemmen, f.eks. `0.04` |

**Stemning — der kontrollen faktisk ligger**
Talesyntesen har knapper for fart og tonehøyde, og det er omtrent alt.
Det som gjør en opplesning alvorlig er hva som skjer etterpå: et rom
rundt stemmen, varme i bunnen, dempet topp, og et jevnt trykk. Det
gjøres med ffmpeg, og virker på hvilken som helst stemme.

| `--stemning` | Hva det er |
| --- | --- |
| `mork` | rolig og alvorlig. Lite rom, varme nedi, dempet topp |
| `krypt` | større og vått rom. Som en kjeller under vannlinja |
| `radio` | trådløsen i røykesalongen, 1936. Smalt bånd og trykk |

```sh
python3 tools/opplesing.py sesjon-1.md --stemning krypt --drone 0.04 --spill
```

Farten endres med `atempo`, som lar tonehøyden være i fred. Det er med
vilje — `asetrate` ville senket tonehøyden også, og det er nettopp det
som gir metallisk klang.

Krever ffmpeg: `pkg install ffmpeg` i Termux. Finnes den ikke, sier
skriptet fra og gir deg lyden uten stemning i stedet for å feile.

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
- Bibliotek med flere scenarier du bytter fritt mellom
- Elleve visninger: **Oversikt** · **Tidslinje** · **Scener** · **Spor** · **NPCer** · **Steder** · **Handouts** · **Regler** · **Notater** · **Sesjoner** · **Bibliotek**
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

### Biblioteket — du importerer én gang

Fra og med 0.5.0 er scenarioer ikke lenger én enkelt `scenario.json`-slot. Alt du importerer legges i et **bibliotek** i appens private lagring, og blir liggende der. Under **Verktøy → Scenario → Bibliotek** bytter du fritt mellom dem.

Innhold og fremdrift lagres i hver sin fil:

```
<user_data_dir>/
├── library.json          ← hvilke scenarioer som finnes, og hvilket som er aktivt
├── scenarios/<id>.json   ← det importerte innholdet, urørt
└── progress/<id>.json    ← avkryssinger, notater, egne notater, sesjoner
```

Det er grunnen til at du kan importere den samme fila på nytt — for eksempel en oppdatert versjon av scenarioet — uten å miste noe av det du har krysset av eller skrevet. Fremdriften kobles til elementenes `id`, ikke til fila.

Notater lagres av seg selv to sekunder etter siste tastetrykk, og flushes når appen legges i bakgrunnen.

### Feltene et scenario kan ha

| Felt | Innhold |
|---|---|
| `title`, `system`, `setting`, `tagline` | Metadata som vises på Oversikt |
| `player_pitch`, `keeper_summary` | Åpningstekst til spillerne, og hva som egentlig foregår |
| `keeper_brief` | `{title, body}` — korte kort med det viktigste å vite på forhånd |
| `timeline` | `{id, day, when, title, description, tag}` — grupperes per dag |
| `beats` | `{id, act, title, description, dialogue, roleplay}` — scener, grupperes per akt. `dialogue` er `[{who, line, note, source}]` der `source` er `"bok"` eller `"forslag"` |
| `clues` | `{id, title, where, roll, description}` |
| `npcs` | `{id, name, category, role, description, traits, quotes, stats, combat, skills, spells, special, sanity_loss, possessions, notes}` |
| `locations` | `{id, title, deck, description}` |
| `handouts` | `{id, title, description, read_aloud, aside}` — `read_aloud` vises i egen ramme til opplesning |
| `reference` | `{id, title, description}` — regler og skipsdata |

Toppnivået kan i tillegg ha `version` (se under). Alle elementer kan ha `connects_to: [id, ...]`, som blir klikkbare kryssreferanser. Mangler et element `id`, lager appen en stabil en selv.

`scenarios/slow-boat-to-china.json` i dette repoet er et komplett eksempel — hele Pulp Cthulhu-scenarioet *A Slow Boat to China*, med 29 hendelser, 17 scener, 18 spor, 26 NPCer, 14 steder, 3 handouts og 10 oppslagsartikler. Det følger med appen og ligger i biblioteket ved første oppstart. `scenarios/build_slow_boat.py` er skriptet som genererer det.

### Språk i scenariodata

Innholdet er på **norsk** — hendelser, scener, personbeskrivelser, replikker og handouts. **Spillmekaniske begreper står på engelsk**, slik de gjør i regelboka: ferdighetsnavn (`Spot Hidden`, `Fast Talk`), vanskegrader (`Hard`, `Extreme`), karakteristikker (`STR`, `POW`), formler (`Dominate`, `Consume Likeness`), terningnotasjon og `Sanity`. Egennavn og boktitler beholdes som de er.

### Oppdatering av innebygde scenarier

Feltet `version` styrer om et innebygd scenario skal byttes ut i biblioteket. Øker du tallet, henter appen inn det nye innholdet ved neste oppstart — **uten** å røre avkryssinger, notater eller sesjoner, siden fremdriften ligger i en egen fil og er koblet til elementenes `id`.

Derfor: **endre aldri en `id` i en oppdatering.** Gjør du det, mister brukeren fremdriften knyttet til det elementet. Titler kan trygt endres; id-er kan ikke.

---

## På PC

Appen kjører på Windows, macOS og Linux med samme kodebase:

```bash
pip install "kivy[base]"
python3 main.py
```

Datafilene havner i plattformens vanlige brukermappe i stedet for `/sdcard`:

| Plattform | Mappe |
|---|---|
| Windows | `%APPDATA%\EldritchPortal\` |
| macOS | `~/Library/Application Support/EldritchPortal/` |
| Linux | `~/.local/share/EldritchPortal/` |

Sett `ELDRITCH_DATA_DIR` for å styre den selv. Filvelgeren bruker Kivys egen dialog på PC, så **Velg fil** virker der også.

Røyktesten bygger hele grensesnittet uten skjerm:

```bash
xvfb-run -a python3 tests/smoke_test.py
```

Nettleserversjonen har sine egne funksjonstester. De kjører mot
`web/index.html` i en ekte Chromium med Playwright:

```bash
CHROMIUM_PATH=/sti/til/chromium python3 tests/web_test.py        # lagring og visninger
CHROMIUM_PATH=/sti/til/chromium python3 tests/combat_test.py     # kamptrackeren
CHROMIUM_PATH=/sti/til/chromium python3 tests/initiative_test.py # initiativflyten
CHROMIUM_PATH=/sti/til/chromium python3 tests/rules_test.py      # våpen, talenter, taktikk
CHROMIUM_PATH=/sti/til/chromium python3 tests/fightflow_test.py  # angrepsflyten og regelkjernen
CHROMIUM_PATH=/sti/til/chromium python3 tests/special_test.py    # spesialregler for skapninger
CHROMIUM_PATH=/sti/til/chromium python3 tests/editor_weapons_test.py  # våpen lagt på i editoren
```

---

## I nettleseren

`web/index.html` er en frittstående side — åpne den rett fra disk, eller legg den hvor som helst. Ingen server, ingen installasjon, virker offline.

Den inneholder Keeper-delen av appen:

- **Scenario** — bibliotek, tidslinje per dag, scener per akt med replikker og rollespillhjelp, spor med terningslag, NPC-statblokker, steder, handouts og regeloppslag
- **Roller** — spillere, NPCer og fiender i én liste, med filtrering per type. Alt kan opprettes, redigeres, dupliseres og slettes: karakteristikker, angrep, ferdigheter og fritekst
- **Fiendebank** — 73 skapninger med statblokker, som kan legges i rollelisten eller sendes rett i en kamp. 24 av dem har egne mekanismer lagt inn: tellere som rulles hver runde, regenerering, svake punkter og regler for hvilke våpen som i det hele tatt biter
- **Kamp** — huk av deltakere, skriv inn initiativet de slo, start kampen. Rundeteller, HP-sporing, tilstander, logg, og en angrepsflyt som tar deg fra våpen til mål til ferdig utregnet skade
- **Mitt** — autolagrende notater og sesjonslogg
- En d100-kaster med suksessgrader oppe i topplinja

Alt lagres i nettleseren. Publisert som artifact på claude.ai synkes fremdrift, notater og karakterer også mellom enheter — merket øverst til høyre sier hvilken av delene som gjelder.

Bygg den på nytt etter endringer i `web/template.html` eller i et scenario:

```bash
python3 web/build.py
```

Skriptet lager to filer fra samme kilde: `web/index.html` (komplett HTML-dokument) og `web/app.html` (samme side uten `<head>`/`<body>`, til publisering som artifact).


---

## Fiendebank

`bestiary/malleus-monstrorum.json` inneholder 73 skapninger med karakteristikker, angrep, rustning, ferdigheter, formler og Sanity-tap. Den bygges inn i nettleserversjonen og vises under **Fiendebank**.

Derfra kan en skapning enten legges i rollelisten — som en redigerbar kopi du kan gi eget navn og egne tall — eller sendes rett inn i en kamp.

### Hvordan den er laget

Statblokkene er hentet maskinelt ut av en tekstkonvertering av Malleus Monstrorum:

```bash
python3 scenarios/parse_malleus.py        # mm.txt  -> mm_blocks.json
python3 scenarios/build_bestiary.py mm_blocks.json
python3 web/build.py
```

Karakteristikkene i banken er **gjennomsnittet** av bokas terningformler, siden kamptrackeren trenger konkrete tall. De opprinnelige formlene ligger i `rolls`-feltet og vises i skapningens kort, så du kan slå selv hvis du vil ha variasjon mellom flere av samme sort.

> **Forbehold:** kilden er en OCR-konvertering. Tallene stemmer i de tilfellene som er kontrollert, men enkelte angrepslinjer kan ha blitt delt feil. Sjekk mot din egen utgave før en viktig kamp.

---

## Roller og kamp

Rollelisten skiller mellom tre typer, og typen styrer både gruppering, filter og fargekoding:

| Type | Brukes til |
|---|---|
| `pc` | Spillerkarakterer |
| `npc` | Navngitte biroller |
| `enemy` | Fiender og skapninger |

Eldre `characters.json` fra Android-appen leses uendret: feltet `type` (PC/NPC) leses som `kind`, og flate felter som `str`, `con` og `hp` løftes inn i et `stats`-objekt ved innlasting. Import slår sammen på navn, så den samme fila kan importeres flere ganger uten å lage duplikater.

### Våpen, talenter og regler

Nettleserversjonen bygger inn `weapons.json` (28 våpen) og et talentoppslag hentet fra Pulp Cthulhu (60 talenter).

Alle rollene i `characters.json` har fått våpnene sine lagt inn som angrep, hentet fra arkene deres. Damage bonus står ikke i skadefeltet — et slåsskampangrep er `1D3` med `uses_db`, ikke `1D3+1D4`, siden regelmotoren legger på bonusen selv.

**Våpen** legges på en rolle i karaktereditoren under *Angrep → + Legg til våpen*. I rollelisten går det også en snarvei rett dit: **+ Våpen** på raden åpner editoren med våpenlista framme, så man slipper å starte en kamp for å gi noen det de nettopp kjøpte. Da følger hele statblokka med: skade, om våpenet bruker damage bonus (helt eller halvt), om det kan spidde, feilingsverdi, rekkevidde, angrep per runde og magasin. Treffsjansen fylles automatisk fra rollens egen ferdighet når den finnes — våpenlista er norsk og karakterarkene ofte engelske, så `Håndvåpen` finner `Firearms (Handgun)`, `Nærkamp` finner `Fighting (Brawl)` og så videre.

Reglene som ligger i bunnen er Call of Cthulhu 7e med Pulp Cthulhu-tilleggene:

| Regel | Slik det er implementert |
|---|---|
| Suksessgrader | 01 kritisk · ≤ verdi/5 Extreme · ≤ verdi/2 Hard · ≤ verdi vanlig |
| Fumle | 100 alltid; 96–99 når ferdigheten er under 50 |
| Motsatte slag | Høyeste suksessnivå vinner. Står det likt, vinner høyest ferdighetsverdi; er også den lik, skjer ingenting |
| Spidding | Extreme eller kritisk med et spiddevåpen gir **maks** våpenskade **pluss** et nytt kast |
| Damage bonus | Legges bare til der våpenet bruker den; `uses_db: "half"` gir halv bonus rundet ned. Statblokker som skriver skaden som `1D6 + db` får den lagt til automatisk |
| Feiling | Er kastet ≥ våpenets feilingsverdi, svikter våpenet og angrepet går ikke gjennom |
| Haglegevær | Skade oppgitt som `4D6/2D6/1D6` regnes på nærmeste avstand |
| Rustning | Trekkes fra skaden før den settes på HP. Feltet kan være en hel setning fra Malleus — første tall brukes |
| Major wound | Halve maks-HP eller mer i ett slag. CON-slag eller bevisstløs; null HP med major wound er døende |
| Pulp-helter | Bruker **ikke** major wound. De dør av ett slag på maks HP, ligger for døden om halve maks HP også tar dem til null, og besvimer ellers på null. Halve maks HP i ett slag krever CON-slag for å holde seg våken |

**Angrepsflyten** kjører ett angrep fra ende til annen. Terningene slås ved bordet — appen tar imot tallet og gjør resten:

1. **Angrip** på en deltaker viser **bare det hen faktisk har**: våpnene som står på arket, under *Våpen og angrep*. Har deltakeren ikke noe nærkampangrep i det hele tatt, legges knyttneve, spark og hodestøt til som en sikkerhetsventil. Under *Annet* ligger *Manøver*, *Improvisert* (skriv inn navn, treffsjanse og skade selv) og *Plukk opp et annet våpen*, som åpner hele våpenlista — den er til når noen griper noe som ligger der, ikke noe man blar i hver gang. Hvert våpen kan også klikkes direkte i kampkortet.
2. **Mot hvem** lister de andre i kampen med HP, rustning, unnvikelse og tilstander.
3. **Oppgjøret** viser treffsjansen med grensene ved siden av (`kritisk 01 · ekstrem ≤10 · hard ≤25 · vanlig ≤50 · fumle ≥100`), og et felt du skriver slaget i. En «Slå»-knapp står ved siden av for NPCer og fiender du ikke gidder å slå for.
4. **Den som blir angrepet** velger selv: *Ingenting*, *Unnvik* eller *Slå tilbake* i nærkamp; *Dykk i dekning* mot skytevåpen — som stopper skuddet, men koster neste handling. Velger du *Slå tilbake*, plukker du hvilket våpen det slås tilbake med, og vinner forsvareren, er det angriperen som tar skaden.
5. **Resultatet** sier hvem som vant og hvorfor, og skaden er regnet ut: terningkast, spidding, damage bonus, rustning trukket fra, ny HP, og hva slaget fører til av major wound, bevisstløshet, døende eller død. «Bruk resultatet» setter det på HP-en, legger på tilstandene og skriver hele linja i kamploggen.

Manøver (grep, avvæpning, kast) og knockout-forsøk ligger i samme flyt, med Build-forskjellen vist som veiledning.

### Regler ved bordet

`Regler`-fanen har tre grupper: scenarioets egne oppslag, **regelbokser** fra bøkene, og **hele ferdighetslista**. Søkefeltet går på tvers av alle tre — søker du «dominate» får du både scenarioets slagoversikt og formelboksen.

Regelboksene ligger i `bestiary/keeper_rules.json` og `bestiary/talent_rules.json`, i samme form: `{id, title, source, sections: [{title, source, body}]}`.

| Boks | Dekker |
|---|---|
| **Galskap — når Sanity ryker** | Hva som utløser midlertidig og varig galskap, begge galskapsanfall-tabellene i sin helhet (1D10 sanntid og 1D10 sammendrag), pulp-forskjellene, og hva SAN 45 på to av spillerne betyr i praksis |
| **Formlene i dette scenarioet** | Dominate, Mindblast, Mental Suggestion, Consume Likeness, Graveyard Kiss, Gate, Pipes of Madness og Bind Flying Polyp — med tallene scenarioet faktisk bruker |
| **Vann, drukning og et skip som synker** | Når Swim slås, hvor lenge man holder pusten, kaldt vann som klokke, og hele slutten med livbåter og Sanity-belønninger |
| **Fall, ild, elektrisitet og syre** | Tallene taktikkortene forutsetter: fallskade, damp fra en brukket ledning, høyspent i et oversvømt rom, saltsyren i lasterom 7 |

Pluss de sju talentboksene fra før: psykiske krefter, weird science, Luck-bruk, å dykke i dekning, manøvrer og Build, flere skudd, og Sanity mot Mythos.

**Hver seksjon sier hvor den kommer fra.** `ordrett fra boka` er sitat fra en bok som finnes som tekst i prosjektet; `skrevet ut fra reglene` er skrevet ut fra regelverket fordi kapittelet ikke finnes i noen tekstutgave her; `fra scenarioet` er Slow Boat to China selv. Etiketten står ved siden av seksjonstittelen, ikke i en fotnote.

### Ferdighetsoppslag

`bestiary/skills.json` er hele ferdighetskapitlet fra Call of Cthulhu 7e — 53 ferdigheter med bokas egen beskrivelse, og eksemplene den gir på hva et Regular- og Hard-slag betyr for akkurat den ferdigheten.

**Ferdighetsnavnene på et karakterkort er klikkbare.** Oppslaget tåler skrivemåtene som faktisk står på arkene: `Mech. Repair` finner *Mechanical Repair*, `Science (Biology)` finner *Science*, `Fighting (Brawl)` finner *Fighting*. Alle ferdighetene på alle 27 rollene i prosjektet har et oppslag — det er en test på det.

Fila bygges med:

```bash
python3 scenarios/parse_skills.py coc.txt bestiary/skills.json
```

Boka er satt i to spalter, og konverteringen fletter dem sammen. Skriptet håndterer tre følger av det: sidetall og kolumnetitler midt i teksten, orddelingsbindestreker som falt bort (`deter mine` → `determine`, men bare når det sammensatte ordet finnes ellers i boka og er klart vanligere der), og to oppslag som støter i hverandre slik at begge tekstene havner under den andre.

### Halv og femtedel overalt

Et Hard-slag krever halve ferdigheten, et Extreme en femtedel. Begge står nå ved siden av verdien overalt der en rolles ferdigheter vises, akkurat som på karakterarket — så man slipper å regne i hodet når Keeperen ber om et hardt slag.

| Hvor | Hvordan |
|---|---|
| Karakterkortet | `Fighting (Brawl)  65%  32/13`, og det samme i karakteristikk-rutene: `STR 65 / 32/13` |
| Angrepstabellen | `Tentacle  85%  1D10  42/17` |
| NPC-kort og fiendebank | Ferdighetslinjene er fritekst, så tallene settes inn etter hver prosent: `Hide 30% (15/6), Track 35% (17/7)` |
| Editoren | Oppdateres mens du skriver, både for ferdigheter og for angrep |
| Android-appen | Samme steder: karakterkortet, ferdighetseditoren og NPC-statblokka |

Avrundingen er nedover, slik boka gjør det — statblokkene der skriver `Brawl 75% (37/15)`. Det er også nøyaktig den avrundingen appens egen regelmotor bruker når den bedømmer et kast, så det som står på kortet stemmer alltid med utfallet i kamptrackeren.

To detaljer: verdier det ikke slås mot — HP, MP, DB, Build, Move, Armor — får ingen tallpar, siden de bare ville vært støy. Og står tallene der fra før, slik statblokkene fra boka ofte har dem (`Brawl 60% (30/12)`), lar appen dem være i fred i stedet for å legge på et par til.

---

### Spesialregler for skapninger

Statblokkene i fiendebanken er hentet maskinelt ut av Malleus Monstrorum, og en tabell kan ikke si at en flying polyp danner nye tentakler hver runde, at en chthonian leger seg mellom rundene, eller at kuler ikke biter på en crawling one. Det står i `bestiary/abilities.json`, er skrevet for hånd, og kobles på skapninger og NPCer på id eller navn — også på en redigerbar kopi lagt i rollelisten.

| Type | Hva den gjør |
|---|---|
| `pool` | En teller som slås fra en terningformel. Hvert angrep tilknyttet den bruker opp én. Slås på nytt ved hvert rundeskifte |
| `limited` | N bruk per runde, nullstilles ved rundeskiftet |
| `regen` | Leger et fast antall eller en terningformel HP hver runde. `dies_at_zero` gjør at skapningen likevel dør om den først når null |
| `weakspot` | Et punkt som dreper på stedet. Enten en fast prosentsjanse per treff, eller et krav om at treffslaget er under en andel av egen ferdighet |
| `damage` | Hvilke våpen som biter. Hver regel matcher en skadetype (og eventuelt om treffet spiddet), og gir `normal`, `half`, `minimum`, `fixed` eller `immune` |
| `note` | Ren tekst — fixing attack, usynlighet, halegrep, dagslys |

24 skapninger har slike regler. Flying polyp er den mest omfattende:

- **Tentakler** — 2D6 slås ved starten av hver runde og vises som en teller på kampkortet. Hvert tentakkelangrep (85 %, 1D10) bruker opp én, og skaden går **rett på HP** — rustning teller ikke, fordi vesenet bare er halvveis materielt. Telleren kan også justeres for hånd eller slås om igjen.
- **Vindstøt** — én gang per runde, 70 %, skade lik damage bonus (5D6). Chipen blir grå når den er brukt.
- **Fixing attack** og **usynlighet** står som oppslag på kortet, med scenarioets avvik (polyppen i *A Slow Boat to China* er rasende og blir synlig).
- **Hva som biter** — 4 poeng rustning, og bare minste mulige skade fra fysiske våpen. Ild, elektrisitet, fortryllede våpen og formler gjør full skade.

I angrepsflyten dukker det opp to ekstra valg når målet har slike regler: **hva du treffer** (kroppen, eller en teller som tentaklene — da rives lemmet av i stedet for at HP-en går ned) og **skadetype**, forhåndsvalgt ut fra våpenet. Boka har ingen regel for å hugge tentakler av en polyp; den muligheten er lagt inn som en huskeregel for Keepere som vil kjøre det slik, og står merket som det.

**Talenter** i et karakterkort er klikkbare. Feltet er fritekst, så det deles på komma og hvert navn slås opp i talentboka. Talenter som finnes der er uthevet i gull; ukjente vises stiplet, med forslag til hva du kanskje mente. Oppslaget dekker fysiske, mentale, kamp- og diverse pulp-talenter samt insane talents.

Talenter skrives ofte med valget sitt hengt på — `Psychic Power: Telekinesis`, `Animal Companion (dog)`. Boka fører dem under grunnnavnet, så begge formene finner fram, og valget vises som en egen rad i kortet.

Flere talenter sier bare «see Psychic Powers, page 83» eller «may spend 10 Luck points». `bestiary/talent_rules.json` inneholder reglene de viser til, og talentkortet får en **Reglene bak**-rad som åpner dem:

| Regelboks | Dekker |
|---|---|
| Psykiske krefter | Kostnad i magic points, CON-slag når de tar slutt, vanskegrad — og alle fem kreftene: Clairvoyance, Divination, Medium, Psychometry, Telekinesis |
| Weird Science og dingser | Å bygge en dings, vanskegrad etter hva den gjør, hva som skjer når byggingen går galt, Mythos-teknologi |
| Å bruke Luck | Alle seks Luck-kjøpene for pulp-helter |
| Å dykke i dekning | Unnvikelse mot skytevåpen, undertrykkende ild, liggende |
| Manøvrer og Build | Build mot Build, og knockout-regelen fra Pulp Cthulhu |
| Flere skudd i samme runde | Straffeterning for flere skudd, og to våpen samtidig |
| Sanity og Cthulhu Mythos | Hardened, Mythos Knowledge og pulp-heltenes sårregler |

Har rollen valgt én av de psykiske kreftene, legges den seksjonen øverst i boksen og merkes «← valgt».

Talentboka bygges slik:

```bash
python3 scenarios/build_talents.py pulp.txt
python3 web/build.py
```

---

## Replikker og rollespill

Hver av de 17 scenene har to felter til: `dialogue` og `roleplay`.

`dialogue` er en liste med `{who, line, note, source}`. **`source` skiller kanon fra påfunn** — `"bok"` er ordrett fra *Slow Boat to China*, oversatt; `"forslag"` er skrevet for denne oppsetningen fordi boka ikke gir noe der. I appen får de to solid gullstrek og «fra boka», eller stiplet strek og «forslag», så Keeperen alltid vet hva hen leser.

`A Slow Boat to China` har **80 replikker, 45 av dem fra boka**. Boka trykker «sample phrases» for fjorten NPCer, pluss et knippe replikker inne i scenene — Chad Petersons presentasjon på landgangen, Dr. Soongs *«Hendelsen er høyst uheldig»*, Bates' *«englekoret har befalt meg»*, skapningens tilbud til tcho-tcho-ene, Sheng Tsins ed. Alle er med.

`roleplay` er ikke et sammendrag av scenen. Den sier hvordan den skal spilles: hvem som snakker først, hva NPCen vil ha ut av samtalen, hvilket slag som avgjør noe, og hva som skal skje hvis spillerne går en annen vei enn ventet. Den peker også på gruppas egne tall der det er relevant — at Astor ikke vil snakke med Beefcakes Credit Rating 3, at gruppa ikke har Psychoanalysis og derfor må bruke tid på Hawthorne i stedet.

Replikkene er søkbare: husker du bare en setning noen sa, finner søket scenen.

---

## Trusler og taktikk

Et scenario kan ha en `tactics`-seksjon: kort med **forslag** til hvordan en kveld kan gjøres vanskeligere eller mer levende. Det er bevisst ikke en hendelsesrekke — rekkefølge og bruk er Keeperens.

Hvert kort har `mechanic` (hva som skjer), `tactic` (hvordan det spilles) og `pressure` (én linje om hvorfor det biter på akkurat denne gruppa). Kortene kan krysses av som brukt og noteres i kamploggen.

`A Slow Boat to China` har **27 kort** i fire grupper:

| Gruppe | Hva det er |
|---|---|
| **Kampjustering** (8) | Hvordan en kamp settes opp, uten å blåse opp HP på noe: gi kampen en klokke, la rommet bestemme hvor mange som kan slåss, motstandere som trekker seg og kommer tilbake, grep i stedet for skade, mengde framfor størrelse, mørket som ressurs, tapp Luck før finalen, la rommet ta skade |
| **Motstander** (6) | Fiender som stiller andre spørsmål enn «hvor hardt slår du»: folk som overgir seg, noe som ikke kan slås men har en synlig utvei, noe som tar Sanity i stedet for HP, en beleiring, en fiende som har studert gruppa, og noen som skyter bedre enn dem |
| **Hendelse** (10) | Skipslivet, uavhengig av hovedplottet: mann over bord, kjelehavari, smugling i lasterom 3, feber på mellomdekket, løs last i storm, kortbordet, dyrene i lasterom 5, en blindpassasjer, et telegram hjemmefra, og en gammel arbeidsulykke ingen vil snakke om |
| **Keeper-notat** (3) | Prinsippet bak kortene, én spotlight-scene til hver spiller, og hvorfor skipet bør ha et liv utenfor jakten |

Ingen av kortene gir motstanderne flere HP. En kamp der spillerne treffer og treffer uten at noe skjer, føles ikke vanskelig — den føles kjedelig. Kortene begrenser i stedet hvor mange handlinger som teller, eller flytter spørsmålet vekk fra skade.

I taktikkvisningen finnes **Trekk et kort**, som henter et tilfeldig kort blant dem du ikke har brukt ennå, pluss én knapp per gruppe — trenger du en hendelse midt i en rolig dag, vil du ikke trekke et kort om beleiringstaktikk. **Trekk taktikk** finnes også i kampvisningen.

---

**Kamptrackeren** følger denne flyten:

1. **+ Legg til** åpner en liste over roller og fiendebank der du huker av alle du vil ha med. Hver rad har et antall, så «Ghoul × 4» blir fire deltakere med hvert sitt navn og hver sin HP.
2. Hver deltaker får et **initiativfelt** du skriver inn det som ble slått i. Feltet er forhåndsutfylt med DEX, så lista er brukbar med én gang hvis dere ikke slår for initiativ.
3. **Start kamp** setter rekkefølgen. Lista sorteres bevisst *ikke* mens du skriver — da ville radene hoppet rundt mens du gikk nedover dem. Er kampen alt i gang og du retter et tall, bruker du **Sorter på nytt**.

Når du trykker **Neste tur**, flyttes den som er ferdig nederst i lista og resten rykker opp. Den som har tur ligger dermed alltid øverst, merket «NÅ» og med en egen «Ferdig — neste tur»-knapp, så du slipper å lete deg nedover midt i en kamp. Rundetelleren viser hvor mange av deltakerne som har hatt tur.

Ved lik initiativverdi går den med skytevåpen klart først, deretter høyest DEX. Kampen lagres fortløpende, så sida kan lukkes midt i en runde.

Hver deltaker har et **Pulp**-flagg som avgjør hvilke sårregler som gjelder. Spillerkarakterer får det automatisk; NPCer og fiender ikke. Tilstandene på kortet viser bare det som faktisk gjelder — resten ligger bak **+ Tilstand**.

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
Dokumenter/EldritchPortal/     (delt mappe — legg egne filer her)
├── images/     ← bildebibliotek (undermapper støttes)
├── music/      ← lokale musikkspor
└── crash.log   ← feillogg
```

Karakterer, scenariobibliotek og fremdrift ligger i appens **private** lagring, ikke i den delte mappa. Det er med vilje: Android 13+ lar ikke apper skrive til `Documents`, så alt som lagres der ville gått tapt. Ligger det en `characters.json` i den delte mappa fra en eldre versjon, flyttes den inn automatisk ved første oppstart.

Våpendataene (`weapons.json`) er pakket med appen, så du trenger ikke legge til noen fil for å bruke Våpen-fanen. Det samme gjelder scenarioet *A Slow Boat to China*.

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

Appen bruker to mapper. Den **delte** er der du selv legger filer — `/sdcard/Documents/EldritchPortal/` på Android, plattformens brukermappe på PC (se [På PC](#på-pc)):

| Sti | Innhold |
|---|---|
| `images/` | Bildegalleri (undermapper støttes) |
| `music/` | Lokale musikkspor |
| `weapons.json` | *Valgfri* — overstyrer bundlet våpendata |
| `crash.log` | Feillogg for debugging |

Den **private** mappa (`user_data_dir`) er der appen selv lagrer. Alt som skal overleve en omstart ligger her, fordi Android 13+ ikke gir apper skrivetilgang til `Documents`:

| Sti | Innhold |
|---|---|
| `characters.json` | Karakterer og NPCer |
| `library.json` | Scenariobiblioteket, og hvilket scenario som er aktivt |
| `scenarios/<id>.json` | Importert scenarioinnhold |
| `progress/<id>.json` | Avkryssinger, notater og sesjoner per scenario |
| `weapons_favorites.json` | Favorittmerkede våpen |
| `session_draft.json` | Autolagret sesjonsutkast |

> **Merk:** i versjoner før 0.5.0 pekte `CHAR_FILE` på den delte mappa, og fordi lagringsfeil bare ble logget, forsvant karakterer og scenarioer stille ved omstart. En eksisterende `characters.json` og en gammel `scenario.json` migreres inn i privat lagring ved første oppstart etter oppgraderingen.

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
