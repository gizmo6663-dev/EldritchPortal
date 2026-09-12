# -*- coding: utf-8 -*-
"""Bygger bestiary/spells.json — formlene som faktisk kan bli kastet i
A Slow Boat to China, som strukturerte data i stedet for løpetekst.

Poenget er at Keeperen skal kunne velge «Dominate» i kamptrackeren på
samme måte som et våpen, og se med én gang hva den koster, hva som
avgjør den, og om kasteren har nok igjen.

Feltene:
  cost_mp / cost_san / cost_pow   tall eller terningstreng
  opposed                         "POW" når det kreves motsatt slag
  casting_time                    tekst — noen er øyeblikkelige, andre tar døgn
  in_combat                       True når den kan brukes som en handling i kamp
  effect                          hva som skjer, kort nok til å leses høyt
  at_table                        hva Keeperen trenger å vite, for dette bordet
  source                          grunnbok | scenario
"""
import collections
import io
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "bestiary", "spells.json")


def spell(sid, name, **kw):
    s = collections.OrderedDict()
    s["id"] = sid
    s["name"] = name
    for k in ("who", "alt_names", "cost_mp", "cost_san", "cost_pow",
              "casting_time", "opposed", "range", "duration",
              "in_combat", "effect", "at_table", "source", "page"):
        if k in kw:
            s[k] = kw[k]
    return s


SPELLS = [
    # ---------------------------------------------------------- skapningen
    spell("spell-dominate", "Dominate",
          who="Crawling One",
          alt_names="Command of the Wizard · The Chant of Possession · "
                    "Baleful Influence",
          cost_mp=1, cost_san=1,
          casting_time="Øyeblikkelig",
          opposed="POW",
          range="10 meter, én person om gangen",
          duration="Til neste kamprunde er over — må kastes på nytt",
          in_combat=True,
          effect="Offeret adlyder kasterens ordrer uten unntak, men bare "
                 "til neste kamprunde er over. Kan kastes på nytt så mange "
                 "ganger kasteren makter, og hver ny kasting er "
                 "øyeblikkelig, så kontrollen kan holdes ubrutt. Ordren må "
                 "være forståelig for offeret, og formelen BRYTES om ordren "
                 "strider mot offerets grunnleggende natur.",
          at_table="Skapningens viktigste verktøy. Den bruker den på Bunny "
                   "Bates fra 7. desember, og på Martin Aimesworthy i "
                   "stedet om Bates blir tatt eller drept.\n\n"
                   "HULLET SPILLERNE KAN UTNYTTE: dette er ikke en "
                   "fjernkontroll den kan slå på og gå fra. Skal den styre "
                   "Bates gjennom en scene, må den være innenfor ti meter "
                   "og bruke handlingen sin på det, runde etter runde — og "
                   "det koster 1 Sanity hver gang. Får heltene Bates VEKK "
                   "fra skapningen, slipper kontrollen av seg selv.\n\n"
                   "Den som er dominert, husker det som «stemmer».",
          source="grunnbok", page="s. 254"),

    spell("spell-mindblast", "Mindblast",
          who="Crawling One",
          alt_names="Curse of Enfeeblement · Wave of Doom · "
                    "Abyss of the Mind's Eye",
          cost_mp=10, cost_san="1D3",
          casting_time="Øyeblikkelig",
          opposed="POW",
          range="Synsvidde",
          duration="Umiddelbar, med etterdønninger i dagevis",
          in_combat=True,
          effect="Offeret rammes av et forferdelig mentalt angrep: mister "
                 "5 SANITY POINTS og blir MIDLERTIDIG GAL — rett på, uten "
                 "INT-slag, og med et galskapsanfall først. Kan slite med "
                 "flashbacks og mareritt i dagene etterpå.",
          at_table="Langt farligere enn det høres ut. Beefcake og Walther "
                   "har SAN 45; fem poeng er ikke mye, men anfallet kommer "
                   "uansett, og under anfallet er helten ute av spillerens "
                   "kontroll i 1D10 runder midt i en kamp. Og fordi "
                   "ethvert videre Sanity-tap under den påfølgende "
                   "galskapen gir et NYTT anfall, kan én Mindblast tidlig "
                   "i finalen gjøre at helten er ute resten av scenen.\n\n"
                   "Gjør ingen HP-skade — verken rustning, HP eller våpen "
                   "hjelper. Skapningen har 18 MP og kan kaste den ÉN gang "
                   "på en full lading. Bruk den når en kamp går for lett.",
          source="grunnbok", page="s. 260"),

    spell("spell-mental-suggestion", "Mental Suggestion",
          who="Crawling One",
          alt_names="Domination of the Will · Mesmerise · Bend Will · "
                    "Implant Suggestion",
          cost_mp="5 / 10 / 15 MP etter hvor farlig forslaget er",
          cost_san="1D3 / 2D3 / 3D3 Sanity",
          casting_time="3 runder — kan avbrytes",
          opposed="POW",
          range="Synlig for det blotte øye",
          duration="Én runde per poeng INT kasteren har",
          in_combat=True,
          effect="Kasteren fremsier formelen og SIER forslaget høyt. "
                 "Offeret utfører det og tror det var hens eget.\n"
                 "  Ufarlig (slipp våpenet, gi meg pengene): 5 MP, 1D3 SAN.\n"
                 "  Risikabelt, men ikke mot personens natur (sett fyr på "
                 "lasterommet): 10 MP, 2D3 SAN.\n"
                 "  Farlig eller selvmorderisk (drep en av vennene dine): "
                 "15 MP, 3D3 SAN.\n"
                 "EKSTREME FORSLAG som innebærer død eller stor skade "
                 "krever ET NYTT motsatt POW-slag like før handlingen "
                 "faktisk utføres — offeret kan altså våkne i døra.",
          at_table="Skapningen har INT 90, så varigheten er nitti runder — "
                   "hele resten av kampen. Er heltens INT høyere enn "
                   "kasterens, må kasteren vinne et nytt POW-slag hvert "
                   "tiende runde; ingen i gruppa har INT over 90, så det "
                   "unntaket gjelder ikke.\n\n"
                   "Bruk den til å få en helt til å gå feil vei, åpne feil "
                   "dør eller la være å se på noe — ikke til full kontroll. "
                   "Mer ubehagelig, og vanskeligere å oppdage. Men merk at "
                   "et farlig forslag er 15 av skapningens 18 MP.",
          source="grunnbok", page="s. 260"),

    spell("spell-consume-likeness", "Consume Likeness",
          who="Crawling One",
          alt_names="The Snake Skin Cloak · The Valusian Mantle · "
                    "The Gift of Yig",
          cost_mp="10 MP per seks timer",
          cost_san="1D20 Sanity per offer",
          cost_pow="5 POW permanent",
          casting_time="Flere døgn",
          range="Berøring — offeret må være nylig dødt",
          duration="Varig, til kasteren mister hit points",
          in_combat=False,
          effect="Kasteren tar skikkelsen til en nylig død person. Offeret "
                 "kan ikke avvike mer enn 15 SIZ. Skikkelsen holder for "
                 "øye, kamera og røntgen.\n"
                 "SKYGGEN FORBLIR KASTERENS EGEN — en skarp iakttaker kan "
                 "se det.\n"
                 "MISTER KASTEREN ETT ELLER FLERE HIT POINTS, faller den "
                 "tilbake til sin egen form. Å gå fra påtatt til egen form "
                 "tar 20 sekunder; motsatt vei 1D3 minutter.",
          at_table="ÉN ENESTE TREFFENDE KULE AVSLØRER SKAPNINGEN, uansett "
                   "hvem den utgir seg for å være. Det er gull verdt — "
                   "fortell spillerne det gjennom et Cthulhu Mythos-slag, "
                   "så får du en scene der noen må våge å skyte på en de "
                   "tror er en venn.\n\n"
                   "SCENARIOET AVVIKER på to punkter, og der gjelder "
                   "scenarioet: en ny skikkelse bruker 48 TIMER på å "
                   "utvikle stemmebånd (derfor måtte den forlate Petersons "
                   "skikkelse da Virginia ventet at han skulle snakke), og "
                   "den kan bytte mellom ferdige skikkelser på ÉN "
                   "kamprunde.\n\n"
                   "Fem skikkelser: Almacan, Haseye Adikai, Du Zeming, "
                   "Martin Dungass, Chad Peterson.",
          source="grunnbok + scenario", page="s. 250"),

    spell("spell-graveyard-kiss", "Graveyard Kiss",
          who="Crawling One",
          alt_names="Create Zombie-variant",
          cost_san="1D10", cost_pow="5 POW permanent per zombie",
          casting_time="1 døgn per lik",
          range="Berøring",
          duration="Til kasteren dør",
          in_combat=False,
          effect="Liket må ha nok kjøtt igjen til å kunne bevege seg. "
                 "Kasteren legger en unse av sitt eget blod i munnen på "
                 "liket, kysser leppene og «puster en del av seg selv» inn "
                 "i kroppen. Zombien tar imot ENKLE ORDRER, og kan over tid "
                 "lære mer sammensatte.\n"
                 "DØR KASTEREN, blir zombien inaktiv og råtner bort.\n"
                 "ANTALLSGRENSE: kasterens POW delt på fem.",
          at_table="Valgfri, for høyt pulp-nivå. Skapningen har POW 90 og "
                   "kan altså styre ATTEN zombier samtidig.\n\n"
                   "SCENARIOETS VARIANT: skapningen legger en del av "
                   "insektmassen sin i munnen på liket i stedet for blod. "
                   "Vekkede zombier kan lage FLERE: insekter hopper fra "
                   "munnen deres og inn i munnen på dem de dreper.\n\n"
                   "Som skrevet har den fem zombier. Vanlige zombier er "
                   "lite utfordring for en pulp-helt — men som MOOKS går de "
                   "ut på halve HP, så en horde blir spennende i stedet for "
                   "lang. Merk prisen: 5 POW permanent per zombie. Fem "
                   "zombier har kostet skapningen 25 POW.",
          source="grunnbok + scenario", page="s. 249"),

    spell("spell-gate", "Gate",
          who="Crawling One",
          cost_mp="MP lik en femtedel av POW-en porten ble laget med",
          cost_san="1 Sanity per tur",
          cost_pow="POW etter avstand — 15 for under 10 000 miles",
          casting_time="Én time per POW brukt — 15 timer for Shanghai",
          range="Porten står der den er laget",
          duration="Varig",
          in_combat=False,
          effect="En dør mellom to steder. Å lage den koster permanent POW "
                 "etter avstand; å bruke den koster magic points lik en "
                 "femtedel av POW-en, pluss 1 Sanity per tur. Returreisen "
                 "koster det samme.\n"
                 "TABELL (POW å lage / MP å reise / avstand):\n"
                 "   5 / 1 / 160 km · 10 / 2 / 1 000 miles\n"
                 "  15 / 3 / 10 000 miles · 20 / 4 / 100 000 miles\n"
                 "HVEM SOM HELST kan gå gjennom, med mindre den er laget "
                 "med en nøkkel — et ord eller en gest.",
          at_table="Skapningens fluktplan: en port til Shanghai, der den "
                   "slutter seg til Eight Fortunes Mutual Aid Society.\n\n"
                   "TALLENE DU TRENGER: under 10 000 miles, altså 15 POW å "
                   "lage, 15 TIMER å åpne, og 3 MP + 1 Sanity å gå "
                   "gjennom.\n\n"
                   "DETTE ER IKKE EN FORMEL SPILLERNE KAN HINDRE MED ET "
                   "SLAG. Det er en tidsfrist på femten timer. Og har "
                   "skapningen ikke lagt inn nøkkel, kan HELTENE følge "
                   "etter — 3 MP og 1 Sanity hver. Det er en fullt mulig "
                   "slutt på scenarioet.",
          source="grunnbok + scenario", page="s. 256"),

    # ---------------------------------------------------------- scenarioets egne
    spell("spell-pipes-of-madness", "Pipes of Leng — virkningen på mennesker",
          who="Crawling One (gjennom maskinen)",
          cost_mp="Ingen MP — maskinen gjør arbeidet",
          casting_time="Så lenge skapningen spiller",
          range="30 meter",
          in_combat=True,
          effect="Alle innenfor 30 meter som hører musikken, må slå Sanity. "
                 "De som ryker, mister forstanden midlertidig — husk "
                 "INT-slaget, se regelboksen «Galskap».",
          at_table="I praksis betyr det at lasterom 7 er et rom man ikke "
                   "kan stå i og tenke klart.\n\n"
                   "MERK: dette er en ANNEN ting enn det maskinen gjør mot "
                   "Mythos-vesener. Mot dem sender den ut bølger som "
                   "trekker dem til seg — og gjør dem rasende, fordi "
                   "maskinen ikke virker som den skal.\n\n"
                   "Pipes of Leng står ikke i grunnbokas grimoire. Alt her "
                   "kommer fra scenarioteksten.",
          source="scenario"),

    # ---------------------------------------------------------- heltenes
    spell("spell-bind-flying-polyp", "Bind Flying Polyp",
          who="Heltene — står i Book of Red Jade",
          cost_san=1,
          casting_time="Én runde",
          opposed="POW",
          range="90 meter",
          in_combat=True,
          effect="KASTEREN KAN IKKE VÆRE I KAMP med vesenet, og må være "
                 "innenfor 90 meter.\n"
                 "MOTSATT POW-SLAG mot polyppens POW 80. Dette slaget KAN "
                 "IKKE PUSHES.\n"
                 "BONUSTERNING: kasteren kan investere magic points "
                 "tilsvarende en femtedel av vesenets POW — altså 16 — for "
                 "å få en bonusterning.\n"
                 "LYKKES DET, faller polyppen under kasterens kommando og "
                 "kan beordres ned i dypet igjen.",
          at_table="DEN ENE FORMELEN SPILLERNE SELV KAN KOMME TIL Å KASTE. "
                   "Står i Book of Red Jade, som de må ta fra skapningen "
                   "først — eller få tilbake til dr. Soong, som kan "
                   "oversette den.\n\n"
                   "SJANSESPILLET: de vet ikke polyppens POW. Et vellykket "
                   "Cthulhu Mythos-slag gir riktig antall (16). Franz har "
                   "Mythos 10, og det er hans øyeblikk.\n\n"
                   "16 MP er mer enn noen i gruppa har — Franz har 18, og "
                   "er den eneste som klarer det uten å ta resten fra HP.",
          source="scenario"),

    spell("spell-powder-ibn-ghazi", "Powder of Ibn-Ghazi",
          who="Heltene — står i Book of Red Jade",
          cost_mp="1 MP per dose",
          casting_time="2 døgns forberedelse, 1 runde å bruke",
          range="Kastet eller blåst over målet",
          duration="Ti hjerteslag",
          in_combat=True,
          effect="Gjør magisk usynlige ting synlige. Pulveret blåses fra et "
                 "rør eller kastes over målet. Det som pudres, holder seg "
                 "synlig i høyst ti hjerteslag.\n"
                 "Virker på auraen rundt en Gate, på linjene fra et sted "
                 "som er forberedt for å tilkalle en Mythos-gud, og på "
                 "skapninger som normalt er usynlige.",
          at_table="DENNE ER VERDT Å LEGGE MERKE TIL. Flying Polyp kan bli "
                   "USYNLIG for 1 magic point per runde — og usynlig "
                   "bruker den riktignok ikke tentakler, men den er nesten "
                   "umulig å treffe.\n\n"
                   "Har heltene pulveret, har de et svar. To døgns "
                   "forberedelse betyr at de må ha begynt FØR finalen, så "
                   "dette er en belønning for å ha lest boka tidlig.\n\n"
                   "Står i Book of Red Jade-lista. Keeperen bestemmer de "
                   "tre spesialingrediensene — på et skip midt i "
                   "Stillehavet er akkurat det en scene i seg selv.",
          source="grunnbok", page="s. 261"),

    spell("spell-flesh-ward", "Flesh Ward",
          who="Heltene — står i Book of Red Jade",
          cost_mp="Valgfritt antall MP", cost_san="1D4",
          casting_time="5 runder",
          range="Kasteren selv eller én valgt person",
          duration="Til den er brukt opp",
          in_combat=True,
          effect="Beskyttelse mot fysiske angrep. Hvert magic point gir "
                 "1D6 poeng RUSTNING mot ikke-magiske angrep. "
                 "Beskyttelsen slites ned etter hvert som den stopper "
                 "skade: har man 12 poeng og blir truffet for 8, står det "
                 "4 igjen.",
          at_table="Står i Book of Red Jade. Fem runder å kaste betyr at "
                   "den må kastes FØR kampen, ikke i den.\n\n"
                   "MOT POLYPPEN ER DEN SVAK: tentaklene gjør 1D10 som går "
                   "rett på HP og ignorerer rustning. Mot skapningens kniv "
                   "og pistol, derimot, er den utmerket.",
          source="grunnbok", page="s. 259"),
]

data = collections.OrderedDict()
data["version"] = 1
data["title"] = "Formler"
data["note"] = ("Formlene som kan bli kastet i dette scenarioet, med det "
                "som trengs for å kaste dem. «grunnbok» er Call of Cthulhu "
                "7e kapittel 12; «scenario» er Slow Boat to China. "
                "Formler merket «i kamp» kan velges som handling i "
                "kamptrackeren.")
data["spells"] = SPELLS

json.dump(data, io.open(OUT, "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("%d formler -> %s" % (len(SPELLS), os.path.normpath(OUT)))
print("i kamp:", sum(1 for s in SPELLS if s.get("in_combat")))
