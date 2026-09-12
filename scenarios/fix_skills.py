# -*- coding: utf-8 -*-
"""Retter oppslagene der to-spalte-konverteringen blandet tekst.

parse_skills.py klarer det meste, men der to overskrifter støter i
hverandre havner nabooppslagets tekst midt i beskrivelsen, og
vanskegradene under «Opposing skill/Difficulty level:» kan bli
liggende i den andre spalten. Rettelsene her er skrevet av fra boka.
Kjøres én gang over bestiary/skills.json; den er idempotent.
"""
import collections
import io
import json
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "bestiary/skills.json"

DESC = {
 "Climb":
  "This skill allows a character to climb trees, walls and other vertical "
  "surfaces with or without ropes and climbing gear. The skill also "
  "encompasses rappeling. Conditions such as firmness of surface, available "
  "handholds, wind, visibility, rain, etc., may all affect the difficulty "
  "level. Failing this skill on the first roll indicates that the climb is "
  "perhaps beyond the investigator’s capability. Failing a pushed roll is "
  "likely to indicate a fall with resultant damage. One successful Climb roll "
  "should allow the investigator to complete the climb in almost all cases "
  "(rather than requiring repeated rolls). A challenging or longer climb "
  "should have an increased difficulty level.",
 "Medicine":
  "The user diagnoses and treats accidents, injuries, diseases, poisonings, "
  "etc., and makes public health recommendations. If an era has no good "
  "treatment for a malady, the effort is limited, uncertain, or inconclusive. "
  "The Medicine skill grants knowledge of a wide variety of drugs and potions, "
  "natural and man-made, and understanding of the side effects and "
  "contraindications. Treatment using the Medicine skill takes a minimum of "
  "one hour and can be delivered any time after damage is taken, but if this "
  "is not performed on the same day, the difficulty level is increased "
  "(requiring a Hard success). A person treated successfully with Medicine "
  "recovers 1D3 hit points (in addition to any First Aid they have received), "
  "except in the case of a dying character, who must initially receive "
  "successful First Aid to stabilize them before a Medicine roll is made. "
  "A character is limited to one treatment of First Aid and Medicine until "
  "further damage is taken (except in the case of a dying character who may "
  "require stabilizing with First Aid multiple times). Successful use of "
  "Medicine can rouse an unconscious person to consciousness. In treating "
  "Major Wounds, successful use of the Medicine skill provides the patient a "
  "Bonus die on their weekly recovery roll. The Keeper may grant automatic "
  "success for medical treatment in a contemporary, well-equipped hospital.",
}

SOCIAL = [
 "The difficulty level is based on the opposing factor — in this case the "
 "matching social skill (Charm, Fast Talk, Intimidate or Persuade) or "
 "Psychology, whichever is higher for the target.",
 "Regular difficulty: the opposing skill is below 50.",
 "Hard difficulty: the opposing skill is 50 or above.",
 "Extreme difficulty: the opposing skill is 90 or above.",
]

DIFF = {
 "Climb": ["Regular difficulty: plenty of handholds; perhaps a rope or "
           "drainpipe to climb.",
           "Hard difficulty: few handholds, or surfaces slick with rain."],
 "Medicine": ["Regular difficulty: diagnosis and treatment of standard "
              "medical ailments, with access to equipment (at least a "
              "doctor’s bag containing drugs and instruments) and a "
              "suitable environment.",
              "Hard difficulty: diagnosis and treatment in a dirty and "
              "unsafe environment, with the minimum of equipment."],
 "Charm": SOCIAL, "Fast Talk": SOCIAL,
 "Intimidate": SOCIAL, "Persuade": SOCIAL,
 "Dodge": ["As a combat skill, Dodge is used in an opposed roll and no "
           "difficulty level is set. It cannot be pushed."],
 "Fighting": ["As a combat skill, Fighting is used in an opposed roll and no "
              "difficulty level is set. It cannot be pushed."],
 "Firearms": ["As a combat skill, Firearms is used in an opposed roll and no "
              "difficulty level is set. It cannot be pushed."],
 "Language (Own)": ["Regular difficulty: to read or write at the level of an "
                    "educated speaker.",
                    "Hard difficulty: to grasp obscure, archaic or highly "
                    "technical usage."],
}

LORE = (
 "[Uncommon] This skill represents a character’s expert understanding of a "
 "subject that falls outside the normal bounds of human knowledge. "
 "Specializations of Lore should be specific and unusual, such as Dream Lore, "
 "Necronomicon Lore, UFO Lore, Vampire Lore, Werewolf Lore or Yaddithian "
 "Lore. Where the Keeper wishes to test an investigator’s knowledge of "
 "something that falls within the bounds of one of these fields of Lore, but "
 "the investigator lacks the relevant Lore specialization, the Keeper may "
 "allow for another (more general) skill to be used but require a higher "
 "level of success. Lore skills are also used as a shorthand method of "
 "communicating the knowledge of a non-player character to the Keeper. In the "
 "main, knowledge is represented by the EDU characteristic and specific "
 "skills, such as History or Cthulhu Mythos. The Keeper should decide when "
 "the Lore skill should be incorporated into the game — usually only when a "
 "particular area of specialist knowledge is central to the campaign.")
DESC["Lore"] = LORE
DIFF["Lore"] = ["Regular difficulty: to recall what is common knowledge "
                "within that body of lore.",
                "Hard difficulty: to recall something obscure, or to use a "
                "more general skill (such as History) in place of the Lore "
                "specialization the investigator lacks."]

PUSH = {
 "Climb": "reassessing the climb; taking a longer route; straining "
          "one’s reach.",
 "Medicine": "consulting with colleagues; conducting further research; "
             "trying something experimental or more risky; performing some "
             "form of clinical experiment.",
 "Dodge": "Cannot be pushed.",
 "Fighting": "Cannot be pushed.",
 "Firearms": "Cannot be pushed.",
 "Persuade": "getting close and personal to advance your argument or appeal "
             "to the target’s reason; demonstrating through logical reasoning "
             "and examples, in detail; using carefully preplanned suggestion "
             "techniques to make the target as receptive as possible; putting "
             "on a grand show (staging, fireworks, free gifts, free drinks, "
             "bribes) to push your point of view front-and-center for a group "
             "of people. Remember that this is Persuade: if the investigator "
             "changes approach the Keeper may ask for a different skill — "
             "threats become Intimidate, befriending becomes Charm. Switching "
             "between them to gain a second roll still constitutes a pushed "
             "roll.",
 "Read Lips": "putting yourself in an obvious position and staring unsubtly "
              "at the target(s); filming the target (and thus likely to be "
              "observed filming the target).",
 "Artillery": "bringing the weapon to bear without a full crew, or firing "
              "faster than the detachment can safely serve it — the Keeper "
              "raises the difficulty level instead where no crew is present.",
 "Lore": "taking more time; consulting a rarer source or another expert.",
}

book = json.load(io.open(PATH, encoding="utf-8"),
                 object_pairs_hook=collections.OrderedDict)
by = {s["name"]: s for s in book["skills"]}
missing = [n for n in set(list(DESC) + list(DIFF) + list(PUSH))
           if n not in by]
if missing:
    raise SystemExit("ukjente ferdigheter: %s" % ", ".join(sorted(missing)))

for name, text in DESC.items():
    by[name]["description"] = text
# Lore fikk spesialiseringslista si feilplassert som vanskegrader.
FORCE_DIFF = {"Lore"}
for name, rows in DIFF.items():
    if name in FORCE_DIFF or not by[name].get("difficulty"):
        by[name]["difficulty"] = list(rows)
for name, text in PUSH.items():
    if not by[name].get("pushing"):
        by[name]["pushing"] = text

json.dump(book, io.open(PATH, "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("%d oppslag, %d uten vanskegrad igjen" % (
    len(book["skills"]),
    sum(1 for s in book["skills"] if not s.get("difficulty"))))
