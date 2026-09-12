# -*- coding: utf-8 -*-
"""Merker Pulp Cthulhu-seksjonene som kontrollert mot boka.

Fram til nå sto alt som hvilte på Pulp Cthulhu merket «ikke
kontrollert», fordi den boka ikke fantes som tekst. Den gjør den nå,
og hver seksjon er lest opp mot den. Dette skriptet setter de nye
kildestrengene med kapittel- og sidetall.
"""
import collections
import io
import json

def load(p):
    return json.load(io.open(p, encoding="utf-8"),
                     object_pairs_hook=collections.OrderedDict)

def save(p, d):
    json.dump(d, io.open(p, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

KEEPER = "bestiary/keeper_rules.json"
TALENT = "bestiary/talent_rules.json"

KEEPER_SRC = {
 "insanity": "Call of Cthulhu 7e kapittel 8, og Pulp Cthulhu "
             "kapittel 5: Pulp Sanity (s. 74–76)",
 "wounds":   "Call of Cthulhu 7e kapittel 6, og Pulp Cthulhu "
             "kapittel 4: Game System (s. 65–68)",
}
TALENT_SRC = {
 "psychic-powers":   "Pulp Cthulhu kapittel 6: Psychic Skills (s. 83–85), "
                     "og talentlista i kapittel 2 (s. 25)",
 "weird-science":    "Pulp Cthulhu kapittel 6: Weird Science (s. 86–87)",
 "luck-spends":      "Pulp Cthulhu kapittel 4: Using Luck (s. 60–62)",
 "dive-for-cover":   "Call of Cthulhu 7e kapittel 6, og Pulp Cthulhu "
                     "kapittel 4: Suppressing Fire (s. 65)",
 "manoeuvres":       "Call of Cthulhu 7e kapittel 6, og Pulp Cthulhu "
                     "kapittel 4: Knockouts (s. 65)",
 "multiple-shots":   "Call of Cthulhu 7e kapittel 6, og Pulp Cthulhu "
                     "kapittel 4: Dual-Wielding (s. 71)",
 "sanity-and-mythos": "Call of Cthulhu 7e kapittel 8, og Pulp Cthulhu "
                      "kapittel 2 (s. 25) og kapittel 4 (s. 65)",
}

k = load(KEEPER)
k["note"] = (
 "Oppslag man ellers må bla etter midt i en økt. Hver seksjon sier hvilken "
 "bok den kommer fra: «grunnboka» er Call of Cthulhu 7e og «Pulp Cthulhu» er "
 "pulp-boka — begge finnes som tekst her, og hver seksjon er lest opp mot "
 "sin egen bok. «scenarioet» er Slow Boat to China; «eget» er skrevet av meg "
 "til dette bordet. Der de to bøkene er uenige, gjelder Pulp Cthulhu — "
 "dette er et pulp-scenario, og de stedene er merket særskilt.")
for b in k["rules"]:
    if b["id"] in KEEPER_SRC:
        b["source"] = KEEPER_SRC[b["id"]]
save(KEEPER, k)

t = load(TALENT)
t["note"] = (
 "Talentreglene her er fra Pulp Cthulhu, og er nå lest opp mot boka. "
 "Seksjoner merket «grunnbok» er fra Call of Cthulhu 7e. Der en regel "
 "finnes i begge bøkene, og de er uenige, gjelder Pulp Cthulhu.")
for b in t["rules"]:
    if b["id"] in TALENT_SRC:
        b["source"] = TALENT_SRC[b["id"]]
save(TALENT, t)

miss = ([b["id"] for b in k["rules"] if "ikke kontrollert" in b.get("source", "")]
        + [b["id"] for b in t["rules"] if "ikke kontrollert" in b.get("source", "")])
if miss:
    raise SystemExit("står fortsatt som ukontrollert: %s" % ", ".join(miss))
print("kilder oppdatert: %d keeper-bokser, %d talentbokser"
      % (len(k["rules"]), len(t["rules"])))
