#!/usr/bin/env python3
"""Bygg bestiary/talents.json — oppslagsverk over talenter.

Talentene hentes ut av Pulp Cthulhu-teksten, der de står i tabeller på
formen

    1

    **Keen Vision**: gain a bonus die to Spot Hidden rolls.

    2

    ...

Kjøres slik:

    python3 scenarios/build_talents.py pulp.txt
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "bestiary", "talents.json")

VERSION = 1

# Tabellene som skal leses, med hvilken gruppe de havner i.
# Tabellene er terningtabeller, så antallet rader er kjent på forhånd.
# Uten grensa leser parseren rett videre inn i brødteksten etterpå.
TABLES = [
    ("TABLE 3: PHYSICAL TALENTS", "Fysisk talent", "pulp", 10),
    ("TABLE 4: MENTAL TALENTS", "Mentalt talent", "pulp", 10),
    ("TABLE 5: COMBAT TALENTS", "Kamptalent", "pulp", 10),
    ("TABLE 6: MISCELLANEOUS TALENTS", "Diverse talent", "pulp", 10),
    ("TABLE 12: INSANE TALENTS", "Insane talent", "insane", 20),
]

# Et talent starter med **Navn**: eller **Navn:** og fortsetter til
# neste talent eller tabellslutt.
ENTRY = re.compile(r"^\*\*(?P<name>[^*]{2,60}?)[:：]?\*\*[:：]?\s*(?P<rest>.*)$")
# Tabellhodene står i samme fete form som talentnavnene, og ville ellers
# spist to plasser av radgrensa.
HEADER = re.compile(r"^(Roll|[A-Z][a-z]+ Talent|Talent)$")
STOP = re.compile(r"^(TABLE \d|-----|\[\*\*Page|\*\*Roll\*\*|"
                  r"\*\*[A-Z][a-z]+ Talent\*\*|CREATING PULP HEROES)")


def clean(text):
    s = text
    s = re.sub(r"\[([^\]]*)\]\(#\d+\)", r"\1", s)   # [lenketekst](#83)
    s = s.replace("\\!", "!").replace("\\*", "*")
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)   # **fet** -> fet
    s = s.replace("*", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def tidy_description(text):
    """Den siste raden i en tabell drar med seg sidefot og
    kolonnemarkører fra PDF-konverteringen. Kutt der."""
    s = text
    for marker in ("|", "-----", "[**Page", "**Page"):
        i = s.find(marker)
        if i > 0:
            s = s[:i]
    # Bokstaver spredt med mellomrom er ryggmargsteksten i margen.
    s = re.sub(r"(?:\b\w\s){4,}\w?\s*$", "", s)
    return s.strip(" .;,") + "."


def parse_table(lines, start, group, kind, limit):
    out = []
    current = None
    i = start
    # Les til neste tabelloverskrift som ikke er en fortsettelse.
    while i < len(lines):
        raw = lines[i].strip()
        i += 1
        if not raw:
            continue
        if raw.startswith("TABLE ") and i > start + 3:
            if "CONTINUED" in raw.upper():
                continue
            break
        m = ENTRY.match(raw)
        if m and not m.group("name").isdigit() \
                and not HEADER.match(m.group("name").strip()):
            if current:
                out.append(current)
                if len(out) >= limit:
                    return out
            current = {
                "name": clean(m.group("name")),
                "description": clean(m.group("rest")),
                "group": group,
                "kind": kind,
            }
            continue
        if current is not None:
            if STOP.match(raw) or raw.isdigit():
                continue
            current["description"] += " " + clean(raw)
    if current:
        out.append(current)
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "pulp.txt"
    lines = io.open(src, encoding="utf-8").read().split("\n")

    talents = []
    seen = set()
    for heading, group, kind, limit in TABLES:
        for idx, line in enumerate(lines):
            if line.strip().startswith(heading):
                for t in parse_table(lines, idx + 1, group, kind, limit):
                    key = t["name"].lower()
                    if key in seen or len(t["description"]) < 12:
                        continue
                    seen.add(key)
                    t["id"] = "tal-" + re.sub(r"[^a-z0-9]+", "-",
                                              key).strip("-")
                    t["description"] = tidy_description(t["description"])
                    talents.append(t)
                break

    talents.sort(key=lambda t: t["name"].lower())
    doc = {
        "id": "pulp-talents",
        "version": VERSION,
        "title": "Talenter",
        "source": "Pulp Cthulhu (Chaosium)",
        "note": "Talentbeskrivelsene er hentet maskinelt ut av "
                "regelboka og gjengis på engelsk, slik de står der.",
        "talents": talents,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)

    by_group = {}
    for t in talents:
        by_group[t["group"]] = by_group.get(t["group"], 0) + 1
    print("skrev", OUT)
    for g, n in sorted(by_group.items()):
        print(f"  {n:3d}  {g}")
    print(f"  {len(talents)} totalt, {os.path.getsize(OUT)/1024:.1f} kB")


if __name__ == "__main__":
    main()
