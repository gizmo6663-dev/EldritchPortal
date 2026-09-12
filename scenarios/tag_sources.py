# -*- coding: utf-8 -*-
"""Setter ærlige kildemerker på hver seksjon i regelbankene.

Fire merker, og de sier hvilken BOK teksten kommer fra:

  grunnbok  Call of Cthulhu 7e. Den har jeg som tekst og har lest av.
  pulp      Pulp Cthulhu. Den har jeg IKKE som tekst; seksjonen er
            skrevet ned fra kjennskap til reglene og er ikke
            kontrollert mot boka.
  scenario  Slow Boat to China. PDF-en ligger i opplastingene.
  eget      Skrevet av meg til dette bordet.

Merkene kan kombineres med « + ».
"""
import collections
import io
import json

PULP_SECTIONS = {
    ("insanity", "Galskapsanfall i sanntid — 1D10"),
    ("insanity", "Galskapsanfall som sammendrag — 1D10"),
    ("insanity", "Pulp-forskjellene"),
}

def load(path):
    return json.load(io.open(path, encoding="utf-8"),
                     object_pairs_hook=collections.OrderedDict)

def save(path, data):
    json.dump(data, io.open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

KEEPER = "bestiary/keeper_rules.json"
TALENT = "bestiary/talent_rules.json"

# ---------------------------------------------------------------- keeper
k = load(KEEPER)
k["note"] = (
 "Oppslag man ellers må bla etter midt i en økt. Hver seksjon sier hvilken "
 "bok den kommer fra: «grunnboka» er Call of Cthulhu 7e, som jeg har som "
 "tekst og har lest av; «Pulp Cthulhu» har jeg IKKE som tekst, så de "
 "seksjonene er skrevet ned fra kjennskap til reglene og bør kontrolleres "
 "mot boka; «scenarioet» er Slow Boat to China; «eget» er skrevet av meg "
 "til dette bordet. Der de to bøkene er uenige, gjelder Pulp Cthulhu — "
 "dette er et pulp-scenario.")

for box in k["rules"]:
    for sec in box["sections"]:
        key = (box["id"], sec["title"])
        if key in PULP_SECTIONS:
            sec["source"] = "pulp"
        else:
            sec["source"] = (sec["source"]
                             .replace("verbatim", "grunnbok")
                             .replace("reconstructed", "eget"))

# Pulp-varsel øverst i hver boks som hviler på grunnboka.
WARN = {
 "insanity":
  "UTLØSERNE UNDER ER GRUNNBOKAS — Pulp Cthulhu bruker de samme: 5 poeng på "
  "ett slag gir midlertidig galskap, en femtedel av nåværende Sanity på én "
  "dag gir varig galskap. DET PULP ENDRER, er hva som skjer etterpå: egne "
  "anfallstabeller (de to neste seksjonene), insane talents, og raskere vei "
  "ut av varig galskap. Bruk pulp-tabellene, ikke grunnbokas.",
 "wounds":
  "PULP-HELTER TAR IKKE MAJOR WOUND. Det er den store forskjellen, og den er "
  "alt bygd inn i kamptrackeren — sjekk bare at pulp-haken står på alle fem "
  "heltene. Reglene under er grunnbokas, og de gjelder for NPC-er og fiender "
  "uten videre. FOR HELTENE: bruk dem til døende og førstehjelp, men vit at "
  "Pulp Cthulhu har egne, raskere regler for å komme seg etter skade. Jeg "
  "har ikke den boka som tekst og vil ikke finne på tall — slå opp "
  "skadekapittelet i Pulp Cthulhu før du bruker ukesslagene på en helt.",
 "chases":
  "Jaktreglene under er grunnbokas, og de er de samme reglene Pulp Cthulhu "
  "bygger på. Det pulp legger til, er talenter og Luck: en helt som bommer "
  "et fartsslag eller et hindringsslag kan bruke Luck på det, og flere "
  "talenter gir bonusterninger i jakt. Sjekk heltenes talenter før du "
  "kjører en jakt.",
 "hazards":
  "Tallene under er grunnbokas skadetabell, og den gjelder også i pulp. "
  "FORSKJELLEN I PULP er at helter kan bruke Luck til å slippe unna — se "
  "regelboksen «Å bruke Luck» — og at de ikke tar major wound av dem.",
 "water":
  "Drukningsreglene under er grunnbokas og gjelder også i pulp. "
  "MEN: en pulp-helt kan bruke Luck på CON-slagene, og på Swim-slaget. "
  "Regn med at heltene overlever hvis de vil bruke poeng på det — "
  "det er passasjerene og mannskapet som drukner.",
 "spells":
  "Formlene under er grunnbokas grimoire, og skapningen bruker dem som de "
  "står. Der scenarioet avviker, står begge deler, og da gjelder "
  "scenarioet.",
}
for box in k["rules"]:
    w = WARN.get(box["id"])
    if not w:
        continue
    first = box["sections"][0]
    if first.get("title") == "Pulp eller grunnbok?":
        first["body"] = w
        continue
    box["sections"].insert(0, collections.OrderedDict([
        ("title", "Pulp eller grunnbok?"), ("source", "eget"), ("body", w)]))
save(KEEPER, k)

# ---------------------------------------------------------------- talenter
t = load(TALENT)
t["note"] = (
 "Talentreglene her er fra Pulp Cthulhu, som jeg IKKE har som tekst i denne "
 "økta. De er skrevet ned fra kjennskap til reglene, ikke lest av fra boka, "
 "og de bør kontrolleres mot den før de avgjør noe viktig. Seksjoner merket "
 "«grunnbok» er derimot lest av fra Call of Cthulhu 7e.")

# Hvilken bok hver boks hviler på.
BOOK = {
 "psychic-powers": "pulp",
 "weird-science": "pulp",
 "luck-spends": "pulp",
 "dive-for-cover": "grunnbok",
 "manoeuvres": "grunnbok + pulp",
 "multiple-shots": "grunnbok + pulp",
 "sanity-and-mythos": "grunnbok + pulp",
}
# Sidetall jeg ikke kan kontrollere, ut.
SRC = {
 "psychic-powers": "Pulp Cthulhu — ikke kontrollert mot boka",
 "weird-science": "Pulp Cthulhu — ikke kontrollert mot boka",
 "luck-spends": "Pulp Cthulhu — ikke kontrollert mot boka",
 "dive-for-cover": "Call of Cthulhu 7e, kapittel 6",
 "manoeuvres": "Call of Cthulhu 7e kapittel 6, og Pulp Cthulhu "
               "— pulp-delen er ikke kontrollert mot boka",
 "multiple-shots": "Call of Cthulhu 7e kapittel 6, og Pulp Cthulhu "
                   "— pulp-delen er ikke kontrollert mot boka",
 "sanity-and-mythos": "Call of Cthulhu 7e kapittel 8, og Pulp Cthulhu "
                      "— pulp-delen er ikke kontrollert mot boka",
}
for box in t["rules"]:
    box["source"] = SRC.get(box["id"], box.get("source", ""))
    tag = BOOK.get(box["id"], "pulp")
    for sec in box["sections"]:
        sec.setdefault("source", tag)
save(TALENT, t)

n = sum(len(b["sections"]) for b in k["rules"])
m = sum(len(b["sections"]) for b in t["rules"])
print("keeper: %d bokser / %d seksjoner" % (len(k["rules"]), n))
print("talent: %d bokser / %d seksjoner" % (len(t["rules"]), m))
print("merker:", sorted({s["source"]
                         for d in (k, t) for b in d["rules"]
                         for s in b["sections"]}))
