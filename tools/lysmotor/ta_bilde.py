import asyncio, os, sys
from playwright.async_api import async_playwright
side, ut = sys.argv[1], sys.argv[2]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"),
                                    args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1400, "height": 1100})
        feil = []
        pg.on("pageerror", lambda e: feil.append(str(e)))
        pg.on("console", lambda m: feil.append(m.text) if m.type == "error" else None)
        await pg.goto("file://" + side)
        for _ in range(60):
            t = await pg.title()
            if t: break
            await pg.wait_for_timeout(200)
        print("tittel:", await pg.title(), "| feil:", feil or "ingen")
        el = await pg.query_selector("#ut")
        await el.screenshot(path=ut)
        await b.close()
asyncio.run(main())
