#!/usr/bin/env python3
"""Bygg bestiary/malleus-monstrorum.json — fiendebanken.

Statblokkene er hentet ut av Malleus Monstrorum (Chaosium) og
normalisert til formatet appen bruker for fiender. Kilden er en
OCR-konvertering, så teksten renses en del underveis.

Kjøres mot en mellomfil laget av parse-steget:

    python3 scenarios/build_bestiary.py mm_blocks.json
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "bestiary", "malleus-monstrorum.json")

VERSION = 1

# Terningformel -> et representativt tall, brukt som utgangspunkt for
# HP og karakteristikker i kamptrackeren. Keeperen kan overstyre alt.
DICE = re.compile(r"^\s*(\d+)\s*D\s*(\d+)\s*(?:([+-])\s*(\d+))?\s*$", re.I)


def average_of(expr):
    """Gjennomsnitt av en terningformel, avrundet. Returner None hvis
    uttrykket ikke er en formel."""
    if not expr:
        return None
    m = DICE.match(expr.replace("\\", ""))
    if not m:
        return None
    count, sides = int(m.group(1)), int(m.group(2))
    total = count * (sides + 1) / 2.0
    if m.group(3):
        mod = int(m.group(4))
        total += mod if m.group(3) == "+" else -mod
    return int(round(total))


def first_number(text):
    """Første heltall i en streng som «17-18» eller «12-13 Av DB +0»."""
    if not text:
        return None
    m = re.search(r"\d+", str(text).replace("\\", ""))
    return int(m.group(0)) if m else None


def tidy(text):
    """Rydd OCR-artefakter ut av en tekstbit."""
    if not text:
        return ""
    s = str(text)
    s = s.replace("\\", "").replace("’", "'")
    s = re.sub(r"\s+", " ", s)
    # Ord som er delt over linjeskift i spaltene: «character- istically»
    s = re.sub(r"(\w)- (\w)", r"\1\2", s)
    return s.strip(" .;,")


# Et angrep ser ut som «Claw 35%» — et navn med stor forbokstav
# etterfulgt av en treffsjanse. Flere angrep står etter hverandre på
# samme linje, så de finnes ved å lete opp alle slike hoder og dele
# teksten mellom dem.
ATTACK_HEAD = re.compile(r"([A-Z][A-Za-z'’/\- ]{1,30}?)\s+(\d{1,3})%")


def split_weapons(text):
    """Del «Claw 35%, damage 1D6 + db Bite 35%, damage 1D6» i angrep."""
    s = tidy(text)
    if not s:
        return []
    heads = list(ATTACK_HEAD.finditer(s))
    if not heads:
        return [{"name": s, "skill": "", "damage": ""}] if s else []

    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(s)
        tail = s[m.end():end]
        tail = re.sub(r"^\s*,?\s*(damage\s*)?", "", tail, flags=re.I)
        out.append({
            "name": tidy(m.group(1)),
            "skill": m.group(2) + "%",
            "damage": tidy(tail),
        })
    return out


def norm_name(raw):
    """«BYAKHEE, the Star-Steeds» -> ('Byakhee', 'the Star-Steeds')."""
    s = tidy(raw)
    if "," in s:
        head, tail = s.split(",", 1)
    else:
        head, tail = s, ""
    head = head.strip()
    # Behold egennavn-stavemåte, men fjern ren majuskel-skriking.
    if head.isupper():
        head = " ".join(w.capitalize() if not re.match(r"^[A-Z]'", w) else w
                        for w in head.split())
        head = head.replace("Of", "of").replace("The", "the") \
                   .replace("From", "from").replace("And", "and")
        head = head[0].upper() + head[1:] if head else head
    return head, tidy(tail)


def build(blocks):
    seen = set()
    out = []
    for b in blocks:
        if not b.get("name"):
            continue
        name, subtitle = norm_name(b["name"])
        if not name or len(name) < 3:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        stats = {}
        rolls = {}
        for ch, vals in (b.get("stats") or {}).items():
            roll = tidy(vals[0]) if vals else ""
            avg = average_of(roll)
            if avg is None and len(vals) > 1:
                avg = first_number(vals[1])
            if avg is None:
                avg = first_number(roll)
            if avg is not None:
                stats[ch] = str(avg)
            if roll:
                rolls[ch] = roll

        hp = first_number(b.get("HP"))
        if hp is None and "CON" in stats and "SIZ" in stats:
            hp = (int(stats["CON"]) + int(stats["SIZ"])) // 10
        if hp:
            stats["HP"] = str(hp)
        if "POW" in stats:
            stats["MP"] = str(int(stats["POW"]) // 5)

        db = tidy(b.get("Av. Damage Bonus") or "")
        db = re.split(r"(?<=\S)\s(?=[A-Z][a-z])", db)[0] if db else ""
        if db:
            stats["DB"] = db.rstrip(".")
        move = tidy(b.get("Move") or "")
        if move:
            stats["Move"] = re.split(r"\s{2,}|(?<=\d)\s(?=[A-Z][a-z]{4,})",
                                     move)[0]

        entry = {
            "id": "mm-" + re.sub(r"[^a-z0-9]+", "-", key).strip("-"),
            "name": name,
            "subtitle": subtitle,
            "kind": "enemy",
            "category": "Mythos",
            "stats": stats,
            "rolls": rolls,
            "attacks": split_weapons(b.get("Weapons") or b.get("Weapon")),
            "armor": tidy(b.get("Armor")),
            "skills": tidy(b.get("Skills")),
            "spells": tidy(b.get("Spells")),
            "sanity_loss": tidy(b.get("Sanity Loss")
                                or b.get("Sanity Points")),
            "notes": tidy(b.get("Notes") or b.get("Note")),
        }
        # En oppføring uten både HP og angrep er en halvlest blokk, og
        # er ubrukelig i en kamptracker.
        if not entry["stats"].get("HP") and not entry["attacks"]:
            continue
        out.append(entry)
    out.sort(key=lambda e: e["name"].lower())
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "mm_blocks.json"
    blocks = json.load(io.open(src, encoding="utf-8"))
    creatures = build(blocks)

    doc = {
        "id": "malleus-monstrorum",
        "version": VERSION,
        "title": "Malleus Monstrorum",
        "system": "Call of Cthulhu",
        "source": "Malleus Monstrorum (Chaosium)",
        "note": "Statblokkene er hentet maskinelt ut av en "
                "OCR-konvertering av boka. Sjekk tall mot din egen "
                "utgave før du bruker dem i en viktig kamp — særlig "
                "angrepslinjer, som kan ha blitt delt feil.",
        "creatures": creatures,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)

    with_attacks = sum(1 for c in creatures if c["attacks"])
    with_hp = sum(1 for c in creatures if c["stats"].get("HP"))
    print(f"skrev {OUT}")
    print(f"  {len(creatures)} skapninger")
    print(f"  {with_hp} med HP, {with_attacks} med angrep")
    print(f"  {os.path.getsize(OUT) / 1024:.1f} kB")


if __name__ == "__main__":
    main()
