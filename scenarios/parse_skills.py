# -*- coding: utf-8 -*-
"""Hent ferdighetskapitlet ut av Call of Cthulhu 7e (.docx konvertert
til tekst).

Kapittel 4 lister hver ferdighet som «Navn (base)», en beskrivelse, og
vanskegradene under «Opposing skill/Difficulty level:». Boka er satt i
to spalter, og konverteringen flettet spaltene sammen. Det gir tre
problemer, som hver har sin løsning her:

  1. Sidetall og kolumnetitler midt i teksten        -> NOISE
  2. Orddelingsbindestreker som falt bort             -> DEHYPH
  3. To overskrifter som støter i hverandre, slik at
     begge tekstene havner under den andre            -> COLLISION
"""
import collections
import io
import json
import re
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
LINES = io.open(SRC, encoding="utf-8").read().split("\n")

# Overskriftene står i flere former: «Jump (20%)»,
# «Language, Other (Specializations) (01%)», «Lore (01%) (Specializations)».
BASE = r'\d{1,2}\s*%?|EDU\s*%?|half DEX\s*%?|varies\s*%?'
HEAD = re.compile(
    r'^([A-Z][A-Za-z/,\'’ ()\-]{2,44}?)\s*'
    r'(?:\(Specializations\)\s*)?'
    r'\((' + BASE + r')\)'
    r'(?:\s*\(Specializations\))?'
    r'(?:\s*\[[^\]]+\])?\s*$')
NOISE = re.compile(r'^(\d{1,3}|chapter \d+: skills|call of cthulhu|'
                   r'table [IVX\d]+.*|skill list|skills?)$', re.I)

# Der to oppslag støter i hverandre: hvor teksten til den første
# begynner, og hvor teksten til den andre begynner. Er den andre None,
# finnes ikke teksten i denne konverteringen, og oppslaget droppes.
COLLISION = {
    "Accounting": ("Grants understanding of accountancy procedures", None),
    "Credit Rating": ("A measure of how prosperous",
                      "This skill reflects understanding of the inhuman"),
}


def build_dehyphenator(text):
    """«deter mine» -> «determine», men bare når det er trygt.

    Ordparet limes bare sammen når det sammensatte ordet finnes minst
    tre ganger ellers i boka OG er klart vanligere der enn paret er.
    Da er det en orddeling, ikke to ord som tilfeldigvis står inntil
    hverandre.
    """
    low = text.lower()
    words = collections.Counter(re.findall(r"[a-z]{2,}", low))
    # Overlappende par: «moving cur rent» må gi både «moving cur» OG
    # «cur rent», ellers går halvparten av orddelingene tapt.
    pairs = collections.Counter(
        re.findall(r"(?=\b([a-z]{2,}) ([a-z]{2,})\b)", low))
    out = {}
    for (a, b), n in pairs.items():
        joined = a + b
        if words[joined] >= 2 and n <= max(1, words[joined] // 2) and n <= 4:
            out[a + " " + b] = joined
    return out


DEHYPH = build_dehyphenator("\n".join(LINES))


WORD = re.compile(r'^([^\w]*)([A-Za-z]{2,})([^\w]*)$')


def tidy(s):
    s = re.sub(r'(\w)-\s+(\w)', r'\1\2', s)          # bindestrek beholdt
    s = re.sub(r'\s+', ' ', s).strip()

    # Ord for ord, så «moving cur rent» også får limt «cur rent».
    # Et ord som ender på tegnsetting er slutten på noe og limes ikke.
    parts = s.split(" ")
    out = []
    i = 0
    while i < len(parts):
        a = WORD.match(parts[i])
        b = WORD.match(parts[i + 1]) if i + 1 < len(parts) else None
        if a and b and not a.group(3):
            rep = DEHYPH.get((a.group(2) + " " + b.group(2)).lower())
            if rep:
                if a.group(2)[0].isupper():
                    rep = rep.capitalize()
                out.append(a.group(1) + rep + b.group(3))
                i += 2
                continue
        out.append(parts[i])
        i += 1
    return " ".join(out)


def clean_block(lines):
    return [x.strip() for x in lines
            if x.strip() and not NOISE.match(x.strip())]


def parse_block(body):
    """Sorter linjene på hva de ER, ikke på hvor de står.

    Etter den første markøren er løpende tekst som regel en halv
    setning som har blåst inn fra nabospalten. Den hører ikke hjemme i
    beskrivelsen, så den kastes.
    """
    desc, diffs, spill = [], [], []
    push = cons = insane = None
    seen = False
    for line in body:
        if line.startswith("i "):
            diffs.append(line[2:].strip())
            seen = True
        elif line.startswith("Pushing examples"):
            push = push or line.split(":", 1)[-1]
            seen = True
        elif line.startswith("Sample Consequences"):
            cons = cons or line.split(":", 1)[-1]
            seen = True
        elif line.startswith("If an insane investigator"):
            insane = insane or line
            seen = True
        elif line.startswith(("Opposing skill", "Difficulty level")):
            seen = True
        elif not seen:
            desc.append(line)
        else:
            # Etter første markør er løpende tekst som regel en halv
            # setning fra nabospalten. Men noen oppslag — Dodge — har
            # markøren aller først, og da er all prosaen etter den
            # oppslagets egen. Den tas vare på som reserve.
            spill.append(line)
    if not desc and spill:
        desc = spill
    out = {"description": tidy(" ".join(desc)),
           "difficulty": [tidy(d) for d in diffs if d.strip().rstrip(":")]}
    if push:
        out["pushing"] = tidy(push)
    if cons:
        out["pushed_failure"] = tidy(cons)
    if insane:
        out["insane"] = tidy(insane)
    return out


def find(lines, marker, what):
    at = next((k for k, x in enumerate(lines) if x.startswith(marker)), None)
    if at is None:
        raise SystemExit(f"Fant ikke «{marker}» under {what} — teksten i "
                         f"boka har flyttet på seg. Sjekk COLLISION.")
    return at


start = next(i for i, l in enumerate(LINES)
             if l.strip().startswith("Accounting (05%)") and i > 1650)
heads = [(i, m.group(1).strip(), m.group(2).strip())
         for i, l in enumerate(LINES[start:], start)
         for m in [HEAD.match(l.strip())] if m]

parsed = {}
skip = set()
for n, (i, name, base) in enumerate(heads):
    if n in skip:
        continue
    stop = heads[n + 1][0] if n + 1 < len(heads) else min(i + 60, len(LINES))
    body = clean_block(LINES[i + 1:stop])

    if not body and name in COLLISION and n + 1 < len(heads):
        # Begge tekstene ligger under overskriften nedenfor.
        nxt_i, nxt_name = heads[n + 1][0], heads[n + 1][1]
        far = heads[n + 2][0] if n + 2 < len(heads) else min(nxt_i + 60,
                                                             len(LINES))
        joint = clean_block(LINES[nxt_i + 1:far])
        a_mark, b_mark = COLLISION[name]
        a_at = find(joint, a_mark, name)
        b_at = find(joint, b_mark, nxt_name) if b_mark else len(joint)
        body = joint[a_at:b_at]
        second = joint[b_at:]
        if second:
            parsed.setdefault(nxt_name, []).append(
                (heads[n + 1][2], parse_block(second)))
        skip.add(n + 1)

    if body:
        parsed.setdefault(name, []).append((base, parse_block(body)))

skills = []
for name, versions in parsed.items():
    base, best = max(versions, key=lambda v: len(v[1]["description"]))
    if len(best["description"]) < 60:
        continue
    b = base.replace(" ", "")
    entry = {"name": name,
             "base": b if b.endswith("%") or b in ("EDU", "halfDEX",
                                                   "varies") else b + "%"}
    entry.update(best)
    skills.append(entry)
skills.sort(key=lambda s: s["name"].lower())

# Navnene på karakterarkene er ikke alltid bokas navn.
ALIASES = {
    "Art and Craft": ["art/craft", "art and craft", "art"],
    "Electrical Repair": ["elec. repair", "elec repair"],
    "Mechanical Repair": ["mech. repair", "mech repair"],
    "Fighting": ["brawl", "slåsskamp", "nærkamp"],
    "Firearms": ["skytevåpen"],
    "Language (Own)": ["language (own)", "own language", "eget språk"],
    "Language, Other": ["language (other)", "other language", "language",
                        "språk", "annet språk"],
    "Lore": ["lore"],
    
    
    
    "Dodge": ["unnvikelse", "unnvik"],
    "Swim": ["svømming"],
    "Psychology": ["psykologi"],
    "Spot Hidden": ["spot"],
    "Language (Other)": ["other language", "language", "språk"],
}
for s in skills:
    if s["name"] in ALIASES:
        s["aliases"] = ALIASES[s["name"]]

doc = {
    "version": 1,
    "title": "Ferdigheter",
    "source": "Call of Cthulhu 7e, kapittel 4 (Chaosium)",
    "note": "Hentet maskinelt ut av regelboka. Beskrivelsen er bokas "
            "egen. «Vanskegrader» er eksemplene den gir på hva et "
            "Regular- og Hard-slag faktisk betyr for akkurat denne "
            "ferdigheten — det er som regel det man lurer på midt i en "
            "økt.",
    "skills": skills,
}
io.open(OUT, "w", encoding="utf-8").write(
    json.dumps(doc, ensure_ascii=False, indent=2))
print(len(skills), "ferdigheter ->", OUT)
