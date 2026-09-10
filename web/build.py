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

    # </script> inne i JSON-en ville avsluttet script-taggen for tidlig.
    payload = json.dumps(scenarios, ensure_ascii=False,
                         separators=(",", ":")).replace("</", "<\\/")
    page = template.replace("/*__SCENARIOS__*/", payload)

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
    print(f"{len(scenarios)} scenario(er) bygget inn")


if __name__ == "__main__":
    main()
