#!/usr/bin/env python3
"""Bygg nettleserversjonen av Eldritch Portal.

Ett kildedokument (template.html) gir to filer:

  app.html    innholdet slik Artifact-verktøyet vil ha det (uten
              doctype/head/body — de legges på ved publisering)
  index.html  et komplett HTML-dokument som kan åpnes rett fra disk

Scenariene under ../scenarios legges inn i begge, så sida virker uten
nett og uten import.

    python3 web/build.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCENARIO_DIR = os.path.join(ROOT, "scenarios")
BESTIARY_DIR = os.path.join(ROOT, "bestiary")

SKELETON = """<!doctype html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{ color-scheme: light dark; }}
body {{ margin: 0; font: 14px system-ui, sans-serif; background: #faf9f7; }}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""


def main():
    with open(os.path.join(HERE, "template.html"), encoding="utf-8") as fh:
        template = fh.read()

    scenarios = []
    for name in sorted(os.listdir(SCENARIO_DIR)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(SCENARIO_DIR, name), encoding="utf-8") as fh:
            scenarios.append(json.load(fh))

    # Fiendebanken: slå sammen alle filer under bestiary/ til én bank.
    bestiary = {"creatures": []}
    if os.path.isdir(BESTIARY_DIR):
        for name in sorted(os.listdir(BESTIARY_DIR)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(BESTIARY_DIR, name),
                      encoding="utf-8") as fh:
                bank = json.load(fh)
            creatures = bestiary["creatures"] + bank.get("creatures", [])
            bestiary = dict(bank)
            bestiary["creatures"] = creatures

    def embed(obj):
        # </script> inne i JSON-en ville avsluttet script-taggen for tidlig.
        return json.dumps(obj, ensure_ascii=False,
                          separators=(",", ":")).replace("</", "<\\/")

    page = template.replace("/*__SCENARIOS__*/", embed(scenarios))
    page = page.replace("/*__BESTIARY__*/", embed(bestiary))

    app_path = os.path.join(HERE, "app.html")
    with open(app_path, "w", encoding="utf-8") as fh:
        fh.write(page)

    # Til frittstående bruk deles dokumentet i head- og body-innhold.
    marker = '<div class="shell">'
    head, body = page.split(marker, 1)
    index_path = os.path.join(HERE, "index.html")
    with open(index_path, "w", encoding="utf-8") as fh:
        fh.write(SKELETON.format(head=head.strip(), body=marker + body))

    for path in (app_path, index_path):
        print(f"{os.path.relpath(path, ROOT):20} "
              f"{os.path.getsize(path) / 1024:8.1f} kB")
    print(f"{len(scenarios)} scenario(er) og "
          f"{len(bestiary['creatures'])} skapninger bygget inn")


if __name__ == "__main__":
    main()
