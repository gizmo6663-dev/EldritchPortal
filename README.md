# Eldritch Portal

**Keeper-verktøy for Call of Cthulhu og Pulp Cthulhu — fullt støttet på Android.**

![Platform](https://img.shields.io/badge/platform-Android-green)
![System](https://img.shields.io/badge/system-CoC_7E_%2F_Pulp-purple)
![Lisens](https://img.shields.io/badge/lisens-MIT-blue)

Eldritch Portal er en alt-i-ett-app for Keepers som ønsker å samle sesjonsverktøyene sine på én telefon. Appen er laget for bruk **under pågående sesjoner** — optimalisert for raske oppslag, stemningssetting og håndtering av ferdighetskast under pågående etterforskninger.

## Funksjoner

- **Investigator-håndtering** — full støtte for CoC 7E og Pulp Cthulhu-karakterark (PC og NPC). Lagrer alle 50+ ferdigheter, de 8 karakteristikkene (STR, CON, SIZ, DEX, INT, POW, APP, EDU), samt HP, MP, Sanity og Luck. Pulp Talents, våpen og bakgrunn i egne felt.
- **Initiativ-tracker (DEX-basert)** — bygg rekkefølgen etter CoC-reglene. Trykk-og-velg fra 85+ CoC- og Pulp Cthulhu-skapninger (fra Kultist til Shoggoth), eller legg inn egendefinerte. Firearms-toggle for +50 DEX-bonus på håndvåpen.
- **Regelfane** — komplett CoC 7E + Pulp Cthulhu Keeper-referanse: ferdighetskast, suksessnivåer, pushed rolls, opposed rolls, Sanity-regler, kamp, forfølgelser, Pulp Luck Spend, Karakterskaping og mer.
- **Bildegalleri** — mappebasert galleri for scene-illustrasjoner, NPC-portretter, kart og handouts. Cast til Chromecast for visning på TV.
- **Musikkspiller** — spill av egen lokalmusikk med mini-player som følger deg mellom faner.
- **Ambient-avspilling** — 30+ forhåndsvalgte streamingkilder delt i Natur, Horror, Urban og Mytos-kategorier. Skaper atmosfære umiddelbart.
- **Chromecast-støtte** — send bilder og lyd til TV via lokal HTTP-server.

## Installasjon

**Ferdig APK:** Last ned siste bygg fra [Releases](https://github.com/gizmo6663-dev/EldritchPortal/releases). Du må tillate installasjon fra ukjente kilder på Android.

**Bygg selv:**
```bash
git clone https://github.com/gizmo6663-dev/EldritchPortal
cd EldritchPortal
# Via GitHub Actions: trigger "Build APK"-workflow manuelt
```

**Krav:** Android 5.0+ (API 21 eller høyere). Testet på Samsung Galaxy S25 Ultra.

## Bruk

Første gang du åpner appen, oppretter den `/sdcard/Documents/EldritchPortal/` med undermapper for bilder og musikk. Legg filer der for at de skal dukke opp i appen.

**Investigator-oppretting:**
1. Åpne *Karakter*-fanen, trykk *+ Ny*
2. Fyll inn grunninfo og de 8 karakteristikkene
3. Regn ut deriverte verdier (HP = (CON+SIZ)/10, MP = POW/5, SAN = POW, Luck rulles separat)
4. Trykk *Skills* og sett ferdighetsverdier. Cthulhu Mythos starter på 0, Credit Rating basert på yrke.

**Initiativ under kamp:**
1. Bytt til *Initiativ*-undertab
2. Trykk *+ Investigator* for å legge til lagrede karakterer (DEX trekkes automatisk)
3. Trykk *+ Skapning* og velg fra listen, eller skriv inn egendefinert
4. Huk av +50 for de som skyter med håndvåpen, trykk *Fullfør*
5. Det øverste kortet er aktiv — trykk på det for å avslutte turen

## Datalagring

Alle karakterer og egne filer ligger lokalt på telefonen. Ingenting sendes til nettet (utenom Chromecast, som kun sender til din egen TV).

Data-plassering:
- `/sdcard/Documents/EldritchPortal/characters.json` — lagrede Investigators og NPC-er
- `/sdcard/Documents/EldritchPortal/images/` — egne bilder og handouts
- `/sdcard/Documents/EldritchPortal/music/` — egne musikkfiler

## Teknisk

Skrevet i Python med Kivy-rammeverket. Android-ytelse via pyjnius (bruker Android MediaPlayer direkte for streaming). Bygges med Buildozer via python-for-android.

**Hovedavhengigheter:** kivy, pillow, pychromecast, zeroconf, pyjnius

## Bidra

Forslag og feilrapporter tas gjerne imot via [Issues](https://github.com/gizmo6663-dev/EldritchPortal/issues). Hvis du savner spesifikke Mythos-skapninger i initiativ-trackeren eller regler i regelfanen, skriv en issue.

## Lisens

MIT — se `LICENSE`-filen. Appen er utviklet privat og er ikke tilknyttet Chaosium Inc. Call of Cthulhu og Pulp Cthulhu er varemerker tilhørende Chaosium Inc. Regelhenvisningene i appen er omskrevne Keeper-referanser, ikke reproduksjon av regelteksten. Creatures og deres statistikker er basert på offentlig tilgjengelig CoC 7E/Pulp-materiale.

## Relaterte prosjekter

- **[Campaign Forge](https://github.com/gizmo6663-dev/CampaignForge)** — søsterapp for Dungeons & Dragons 5E (2024).
