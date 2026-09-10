"""Hent statblokker ut av Malleus Monstrorum-teksten."""
import io
import json
import re

SRC = "mm.txt"
lines = [l.rstrip() for l in io.open(SRC, encoding="utf-8")]

CHARS = ["STR", "CON", "SIZ", "INT", "POW", "DEX", "APP", "EDU"]

# Kjennetegn på at en ny monsteroppføring har begynt. Uten dette
# fortsetter «Skills:» og «Sanity Loss:» rett inn i neste oppslag.
NEXT_ENTRY = re.compile(
    r"^[A-Z][A-Z'’’\- ]{3,}\s*,"                 # ROVDYR, undertittel
    r"|(Lesser|Greater)\s+(Independent|Servitor)\s+Race"
    r"|^[A-Z][A-Z'’’\- ]{5,}$"                   # ren majuskellinje
)

# Et statblokk-anker: en linje som er nøyaktig **STR** og har en
# terningformel like etter.
anchors = []
for i, l in enumerate(lines):
    if l.strip() == "**STR**":
        anchors.append(i)

print("STR-ankere:", len(anchors))


def clean(s):
    s = re.sub(r"\*+", "", s).strip()
    return s


def read_block(start):
    """Les et statblokk fra **STR** og nedover."""
    out = {"stats": {}, "raw": []}
    i = start
    n = len(lines)
    field = None
    buf = []

    def flush():
        if field and buf:
            out[field] = " ".join(buf).strip()

    while i < n:
        raw = lines[i]
        s = clean(raw)
        if not s:
            i += 1
            continue
        out["raw"].append(s)

        # Karakteristikk: **STR** / 5D6 / 17-18
        if s in CHARS and i + 1 < n:
            key = s
            vals = []
            j = i + 1
            while j < n and len(vals) < 2:
                v = clean(lines[j])
                if not v:
                    j += 1
                    continue
                if v in CHARS or v.startswith(("Move", "HP", "Av.", "Weapons",
                                               "Armor", "Spells", "Skills",
                                               "Sanity", "SAN")):
                    break
                vals.append(v)
                j += 1
            out["stats"][key] = vals
            i = j
            continue

        m = re.match(r"^(Move|HP|Av\. Damage Bonus|Weapons?|Armor|Spells|"
                     r"Skills|Sanity Loss|Sanity Points|Notes?)\s*:?\s*(.*)$", s)
        if m:
            flush()
            field = m.group(1)
            buf = [m.group(2)] if m.group(2) else []
            i += 1
            continue

        if field in ("Weapons", "Weapon", "Armor", "Spells", "Skills",
                     "Sanity Loss", "Notes", "Note", "Av. Damage Bonus",
                     "Move", "HP"):
            # Fortsettelseslinje for gjeldende felt — men stopp før
            # neste monster, ellers renner beskrivelsen dit over i
            # dette feltet.
            if NEXT_ENTRY.search(s) or s.startswith("MALLEUS"):
                break
            buf.append(s)
            i += 1
            if field == "Sanity Loss" and s.endswith("."):
                break
            continue
        break

    flush()
    return out, i


SKIP = {"char.", "rolls", "averages", "rolls/average", "roll", "average",
        "Av. DB:", "Damage Bonus:"}
FIELD_RE = re.compile(r"^(Sanity Loss|Skills|Spells|Armor|Weapons?|Move|HP|"
                      r"Av\.|Avg\.|Notes?)\b")


def find_name(idx):
    """Navnet står i fete linjer rett over statblokka — men ombrekkes
    ofte over to eller tre linjer, så de må settes sammen igjen."""
    parts = []
    k = idx - 1
    seen_any = False
    # Hver linje i markdownen er skilt av tomme linjer, så de må hoppes
    # over — ikke behandles som slutten på navnet.
    while k >= 0 and idx - k < 40:
        s = lines[k].strip()
        if not s:
            k -= 1
            continue
        t = clean(s)
        is_bold = s.startswith("**") and s.endswith("**")
        if not is_bold or t in SKIP or t in CHARS or FIELD_RE.match(t) \
                or len(t) < 2 or t.isdigit():
            if seen_any:
                break
            k -= 1
            continue
        parts.append(t)
        seen_any = True
        # En linje som starter med stor forbokstav og inneholder komma
        # eller er ren majuskel, er som regel starten på navnet.
        if re.match(r"^[A-Z][A-Z'’\- ]{3,}", t):
            break
        k -= 1
    if not parts:
        return None
    return " ".join(reversed(parts)).strip()


entries = []
for a in anchors:
    name = find_name(a)
    block, end = read_block(a)
    entries.append({"name": name, "line": a, **block})

print("blokker lest:", len(entries))
named = [e for e in entries if e["name"]]
print("med navn:", len(named))
for e in entries[:6]:
    print("-", e["name"], "| stats:", list(e["stats"].keys()),
          "| HP:", e.get("HP"), "| W:", (e.get("Weapons") or "")[:60])

json.dump(entries, io.open("mm_blocks.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("skrev mm_blocks.json")
