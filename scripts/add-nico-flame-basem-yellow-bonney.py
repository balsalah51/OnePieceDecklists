#!/usr/bin/env python3
"""Host Basem's custom OP13 Yellow Bonney 50-card list.

Starts from the submitted SIM 50 (Big Mom + Blackbeard splash), adds 4
1-cost Lilith (OP13-113), and drops 4 copies OP17 yellow Bonney lists
already play lowest: 2 Charlotte Perospero and 2 Borsalino.
Does not wipe other list pages. Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path("/workspace")
LEADER_ID = "OP13-100"
SLUG = "nico-flame-basem"
HREF = f"/decklists/yellow-bonney/{SLUG}.html"
HUB = ROOT / "decklists/yellow-bonney.html"

# Submitted 50 from the SIM screenshot, then +4 OP13-113 Lilith.
# Cuts from 4 OP17 yellow Bonney lists on this hub (excluding the OPDB
# outlier): Perospero is 0/0/0/3, Borsalino is 2/2/4/0. Drop 2 of each.
# Keep the 4 Devon / 4 Shiryu / 2 Teach splash from the screenshot.
RAW = (
    "1xOP13-100 4xOP13-113 4xOP17-113 4xOP17-107 4xOP17-109 "
    "4xOP17-102 2xEB04-058 4xOP17-106 4xOP17-114 2xOP17-110 "
    "4xOP16-104 4xOP16-108 2xOP16-119 4xOP13-108 4xOP17-112"
)

NOTES = """        <p>Custom 50-card list from the submitted Yellow Bonney 50. Adds 4 1-cost Lilith (OP13-113). To stay at 50, drops 2 Charlotte Perospero and 2 Borsalino — those are the copies OP17 yellow Bonney lists on this hub already play lowest. Keeps 4 Catarina Devon, 4 Shiryu, and 2 Marshall D. Teach from the screenshot.</p>"""


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def patch_page(path: Path) -> None:
    text = path.read_text()
    text = text.replace('href="/css/site.css?v=home-pro8"', 'href="/css/site.css?v=home-pro16"')
    text = text.replace('href="/css/site.css?v=home-pro2"', 'href="/css/site.css?v=home-pro16"')
    text = re.sub(
        r'(<p>Submitted 50-card list · 2026-09-16</p>\n)(?:        <p>Custom 50-card list.*?</p>\n)?',
        r'\1' + NOTES + '\n',
        text,
        count=1,
        flags=re.S,
    )
    if "Custom 50-card list" not in text:
        text = text.replace(
            "<p>Submitted 50-card list · 2026-09-16</p>",
            "<p>Submitted 50-card list · 2026-09-16</p>\n" + NOTES,
            1,
        )
    text = re.sub(
        r'<p class="muted" style="margin-top:22px">Community list from a public deck builder\..*?</p>',
        '<p class="muted" style="margin-top:22px">Custom submitted 50-card list. English card text from Limitless One Piece. Images hosted by Limitless. Not affiliated with Bandai.</p>',
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text)


def restore_hub_css() -> None:
    text = HUB.read_text()
    text = text.replace('href="/css/site.css?v=home-pro8"', 'href="/css/site.css?v=home-pro16"')
    HUB.write_text(text)


def patch_search() -> None:
    path = ROOT / "search.html"
    text = path.read_text()
    entry = {
        "t": "Nico Flame Basem",
        "n": "Basem custom OP17 Yellow Bonney list · 2026-09-16",
        "h": HREF,
        "q": "Nico Flame Basem Yellow Bonney OP13-100 Basem custom list Lilith Streusen Shiryu Devon Borsalino",
    }
    m = re.search(
        r'(<script type="application/json" id="search-lists">)(.*?)(</script>)',
        text,
        re.S,
    )
    if not m:
        raise SystemExit("search-lists json missing")
    blob = json.loads(m.group(2))
    existing = next((i for i, row in enumerate(blob) if row.get("h") == HREF), None)
    if existing is None:
        blob.insert(0, entry)
    else:
        blob[existing] = entry
    new = json.dumps(blob, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    text = text[: m.start(2)] + new + text[m.end(2) :]
    li = f'''            <li data-q="{entry["q"]}">
              <a class="item" href="{HREF}">
                <div>
                  <div style="font-weight:700">Nico Flame Basem</div>
                  <div class="muted" style="font-size:13px">{entry["n"]}</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
'''
    text = re.sub(
        rf'<li data-q="[^"]*">(\s*<a class="item" href="{re.escape(HREF)}")',
        f'<li data-q="{entry["q"]}">\\1',
        text,
        count=1,
    )
    if HREF not in text.split('id="search-lists"', 1)[0]:
        needle = '<section class="search-group" data-search-group>\n          <div class="section-title">\n            <h3>Recent lists</h3>'
        idx = text.find(needle)
        if idx != -1:
            ul = text.find("<ul class=\"list\">", idx)
            if ul != -1:
                insert_at = text.find("\n", ul) + 1
                text = text[:insert_at] + li + text[insert_at:]
        else:
            extra_ul = re.search(r'(<ul class="list" data-extra-results></ul>\s*</section>\s*)', text)
            if extra_ul:
                text = text[: extra_ul.end(1)] + "\n" + li + text[extra_ul.end(1) :]
    path.write_text(text)
    print("search patched")


def patch_sitemap() -> None:
    path = ROOT / "sitemap-lists.xml"
    text = path.read_text()
    loc = f"https://onepiecedecklists.com{HREF}"
    if loc in text:
        print("sitemap already has", loc)
        return
    line = f'  <url><loc>{loc}</loc><lastmod>2026-09-16</lastmod></url>\n'
    marker = "  <url><loc>https://onepiecedecklists.com/decklists/yellow-bonney/opdeck-bonney-op17-east-ogre-greenlake-sep13-aldo-wijaya.html</loc>"
    if marker not in text:
        raise SystemExit("sitemap marker missing")
    text = text.replace(marker, line + marker, 1)
    path.write_text(text)
    print("sitemap patched")


def main() -> None:
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seofix", "/workspace/scripts/enhance-seo.py")
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")

    item = {
        "leader": LEADER_ID,
        "kind": "web",
        "player": "Basem",
        "title": "Nico Flame Basem",
        "subtitle": "Submitted 50-card list · 2026-09-16",
        "source_url": f"https://onepiecedecklists.com{HREF}",
        "slug": SLUG,
        "date": "2026-09-16",
        "raw": RAW,
        "cards": 50,
    }
    counts = commsrc.comm.parse_raw(RAW)
    main_n = sum(n for cid, n in counts.items() if cid != LEADER_ID)
    if counts.get(LEADER_ID) != 1 or main_n != 50:
        raise SystemExit(f"bad list leader={counts.get(LEADER_ID)} cards={main_n}")
    if counts.get("OP13-113") != 4:
        raise SystemExit("need 4 Lilith")

    page_path = ROOT / "decklists/yellow-bonney" / f"{SLUG}.html"
    if page_path.exists():
        page_path.unlink()
    comm = json.loads((ROOT / "data/community-decks.json").read_text())
    rows = comm.get(LEADER_ID) or []
    comm[LEADER_ID] = [row for row in rows if row.get("slug") != SLUG]
    (ROOT / "data/community-decks.json").write_text(
        json.dumps(comm, indent=2, ensure_ascii=False) + "\n"
    )

    commsrc.write_lists([item])

    comm = json.loads((ROOT / "data/community-decks.json").read_text())
    rows = comm.get(LEADER_ID) or []
    mine = next((row for row in rows if row.get("slug") == SLUG), None)
    if mine is None:
        raise SystemExit("community row missing")
    mine["player"] = "Basem"
    comm[LEADER_ID] = [mine] + [row for row in rows if row.get("slug") != SLUG]
    (ROOT / "data/community-decks.json").write_text(
        json.dumps(comm, indent=2, ensure_ascii=False) + "\n"
    )
    index = more.load_index()
    more.rebuild_hubs(index, only_ids={LEADER_ID})

    leader = next(L for L in gen.LEADERS if L["id"] == LEADER_ID)
    cache = gen.load_card_cache()
    up.upgrade_list_page(page_path, leader, cache)
    patch_page(page_path)

    index = seo.load_index()
    by_href = seo.href_lookup(index)
    seo.patch_file(page_path, index, by_href)
    seo.patch_file(HUB, index, by_href)
    patch_page(page_path)
    restore_hub_css()
    patch_search()
    patch_sitemap()
    print("done", page_path)


if __name__ == "__main__":
    main()
