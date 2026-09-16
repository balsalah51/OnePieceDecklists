#!/usr/bin/env python3
"""Host 5 themed OP13 Yellow Bonney 50-card lists, all with Catarina Devon.

1. Thriller Bark
2. 10-cost Linlin
3. Thriller Bark / Linlin hybrid
4. Blackbeard (Shiryu/Teach)
5. Egghead search

Does not wipe other list pages. Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path("/workspace")
LEADER_ID = "OP13-100"
HUB = ROOT / "decklists/yellow-bonney.html"
DATE = "2026-09-16"

DECKS = [
    {
        "slug": "thriller-bark-devon",
        "title": "Thriller Bark Devon",
        "subtitle": f"Thriller Bark theme · {DATE}",
        "q": "Thriller Bark Devon Yellow Bonney OP13-100 Perona Hogback Moria Kumacy Cindry",
        "notes": (
            "        <p>Thriller Bark Yellow Bonney 50 with 4 Catarina Devon. "
            "4 Kumacy, 4 Victoria Cindry, 4 Perona, 4 Dr. Hogback, and 4 Gecko Moria, "
            "plus 2 Absalom. Lilith and 9-cost Rush Bonney search and close. "
            "Pudding, Borsalino, Shiryu, Teach, and Sweet 3 Generals fill from OP17 yellow Bonney lists.</p>"
        ),
        "raw": (
            "1xOP13-100 4xOP14-102 4xOP13-113 4xOP14-109 2xOP14-100 4xOP17-109 "
            "4xOP16-104 4xOP14-110 4xOP14-111 2xEB04-058 2xOP16-108 2xOP17-114 "
            "4xOP14-104 2xOP16-119 4xOP13-108 4xOP06-115"
        ),
        "must": {"OP16-104": 4, "OP14-111": 4, "OP14-110": 4, "OP14-104": 4},
    },
    {
        "slug": "linlin-10c-devon",
        "title": "10-Cost Linlin",
        "subtitle": f"Charlotte Linlin 10c theme · {DATE}",
        "q": "10-Cost Linlin Devon Yellow Bonney OP13-100 OP17-112 Streusen Smoothie Oven",
        "notes": (
            "        <p>10-cost Charlotte Linlin Yellow Bonney 50 with 4 Catarina Devon. "
            "4 OP17-112 Linlin plus the 4000-power Trigger bodies she pumps: Daifuku, Oven, "
            "Smoothie, Sweet 3 Generals, and Pudding. Streusen searches Big Mom. "
            "Lilith and 9-cost Rush Bonney stay in; Perospero, Teach, Borsalino, and the 0-cost "
            "event follow OP17 yellow Bonney counts.</p>"
        ),
        "raw": (
            "1xOP13-100 4xOP13-113 4xOP17-113 4xOP17-107 4xOP17-109 4xOP16-104 "
            "4xOP17-102 2xEB04-058 4xOP17-106 4xOP17-114 2xOP17-110 2xOP16-119 "
            "4xOP13-108 4xOP17-112 4xOP06-115"
        ),
        "must": {"OP16-104": 4, "OP17-112": 4, "OP17-113": 4, "OP17-114": 4},
    },
    {
        "slug": "thriller-linlin-hybrid",
        "title": "Thriller Bark / Linlin Hybrid",
        "subtitle": f"Hybrid theme · {DATE}",
        "q": "Thriller Bark Linlin Hybrid Devon Yellow Bonney OP13-100 Perona Hogback Moria OP17-112",
        "notes": (
            "        <p>Hybrid Yellow Bonney 50 with 4 Catarina Devon. Thriller Bark half is "
            "4 Perona, 4 Hogback, 4 Gecko Moria, and 2 Kumacy. Linlin half is 4 10-cost Linlin, "
            "4 Streusen, 4 Pudding, 4 Sweet 3 Generals, and 2 Daifuku / 2 Smoothie. "
            "Lilith and 9-cost Rush Bonney tie the triggers together; Teach and Borsalino from list counts.</p>"
        ),
        "raw": (
            "1xOP13-100 2xOP14-102 4xOP13-113 4xOP17-113 4xOP17-109 2xOP17-107 "
            "4xOP16-104 4xOP14-110 4xOP14-111 2xEB04-058 2xOP17-106 4xOP17-114 "
            "4xOP14-104 2xOP16-119 4xOP13-108 4xOP17-112"
        ),
        "must": {
            "OP16-104": 4,
            "OP14-111": 4,
            "OP14-110": 4,
            "OP14-104": 4,
            "OP17-112": 4,
        },
    },
    {
        "slug": "blackbeard-devon",
        "title": "Blackbeard Devon",
        "subtitle": f"Shiryu and Teach theme · {DATE}",
        "q": "Blackbeard Devon Yellow Bonney OP13-100 Shiryu Teach Catarina Devon",
        "notes": (
            "        <p>Blackbeard-splash Yellow Bonney 50 with 4 Catarina Devon, 4 Shiryu, and "
            "4 Marshall D. Teach. The rest is the OP17 yellow Bonney core: Lilith, 9-cost Rush Bonney, "
            "Pudding, Streusen, Sweet 3 Generals, Smoothie, Oven, Daifuku, 2 Borsalino, and the 0-cost event.</p>"
        ),
        "raw": (
            "1xOP13-100 4xOP13-113 4xOP17-113 4xOP17-107 4xOP17-109 4xOP16-104 "
            "4xOP17-102 2xEB04-058 4xOP17-106 4xOP16-108 4xOP17-114 4xOP16-119 "
            "4xOP13-108 4xOP06-115"
        ),
        "must": {"OP16-104": 4, "OP16-108": 4, "OP16-119": 4},
    },
    {
        "slug": "egghead-search-devon",
        "title": "Egghead Search",
        "subtitle": f"Egghead search theme · {DATE}",
        "q": "Egghead Search Devon Yellow Bonney OP13-100 Lilith Usopp S-Snake Rush Bonney",
        "notes": (
            "        <p>Egghead-search Yellow Bonney 50 with 4 Catarina Devon. "
            "4 Lilith, 4 1-cost 2k Usopp, 4 S-Snake, and 4 9-cost Rush Bonney. "
            "Big Mom draw and Trigger bodies (Pudding, Streusen, Oven, Smoothie, Sweet 3 Generals) "
            "plus 2 Shiryu, 2 Teach, 2 Borsalino, and the 0-cost event from OP17 yellow Bonney lists.</p>"
        ),
        "raw": (
            "1xOP13-100 4xOP13-113 4xOP07-099 4xOP17-113 4xOP17-109 4xOP13-114 "
            "4xOP16-104 4xOP17-102 2xEB04-058 4xOP17-106 2xOP16-108 4xOP17-114 "
            "2xOP16-119 4xOP13-108 4xOP06-115"
        ),
        "must": {"OP16-104": 4, "OP13-113": 4, "OP07-099": 4, "OP13-114": 4, "OP13-108": 4},
    },
]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def href_for(slug: str) -> str:
    return f"/decklists/yellow-bonney/{slug}.html"


def patch_page(path: Path, notes: str, subtitle: str) -> None:
    text = path.read_text()
    text = text.replace('href="/css/site.css?v=home-pro8"', 'href="/css/site.css?v=home-pro16"')
    text = text.replace('href="/css/site.css?v=home-pro2"', 'href="/css/site.css?v=home-pro16"')
    text = re.sub(
        rf'(<p>{re.escape(subtitle)}</p>\n)(?:        <p>.*?</p>\n)?',
        r"\1" + notes + "\n",
        text,
        count=1,
        flags=re.S,
    )
    if notes.strip()[3:20] not in text:
        text = text.replace(
            f"<p>{subtitle}</p>",
            f"<p>{subtitle}</p>\n" + notes,
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
    HUB.write_text(
        HUB.read_text().replace(
            'href="/css/site.css?v=home-pro8"',
            'href="/css/site.css?v=home-pro16"',
        )
    )


def patch_search(commsrc) -> None:
    path = ROOT / "search.html"
    text = path.read_text()
    m = re.search(
        r'(<script type="application/json" id="search-lists">)(.*?)(</script>)',
        text,
        re.S,
    )
    if not m:
        raise SystemExit("search-lists json missing")
    blob = json.loads(m.group(2))
    # Insert newest-first, so iterate reversed then insert at 0.
    for spec in reversed(DECKS):
        href = href_for(spec["slug"])
        entry = {
            "t": spec["title"],
            "n": spec["subtitle"],
            "h": href,
            "q": spec["q"],
        }
        existing = next((i for i, row in enumerate(blob) if row.get("h") == href), None)
        if existing is None:
            blob.insert(0, entry)
        else:
            blob[existing] = entry
            blob.insert(0, blob.pop(existing))
    new = json.dumps(blob, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    text = text[: m.start(2)] + new + text[m.end(2) :]
    for spec in reversed(DECKS):
        href = href_for(spec["slug"])
        entry_q = spec["q"]
        li = f'''            <li data-q="{entry_q}">
              <a class="item" href="{href}">
                <div>
                  <div style="font-weight:700">{spec["title"]}</div>
                  <div class="muted" style="font-size:13px">{spec["subtitle"]}</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
'''
        text = re.sub(
            rf'<li data-q="[^"]*">(\s*<a class="item" href="{re.escape(href)}")',
            f'<li data-q="{entry_q}">\\1',
            text,
            count=1,
        )
        if href not in text.split('id="search-lists"', 1)[0]:
            needle = '<section class="search-group" data-search-group>\n          <div class="section-title">\n            <h3>Recent lists</h3>'
            idx = text.find(needle)
            if idx != -1:
                ul = text.find('<ul class="list">', idx)
                if ul != -1:
                    insert_at = text.find("\n", ul) + 1
                    text = text[:insert_at] + li + text[insert_at:]
    path.write_text(text)
    print("search patched")


def patch_sitemap() -> None:
    path = ROOT / "sitemap-lists.xml"
    text = path.read_text()
    marker = "  <url><loc>https://onepiecedecklists.com/decklists/yellow-bonney/ammo-bubba.html</loc>"
    if marker not in text:
        marker = "  <url><loc>https://onepiecedecklists.com/decklists/yellow-bonney/nico-flame-basem.html</loc>"
    if marker not in text:
        raise SystemExit("sitemap marker missing")
    block = ""
    for spec in DECKS:
        loc = f"https://onepiecedecklists.com{href_for(spec['slug'])}"
        if loc in text:
            continue
        block += f"  <url><loc>{loc}</loc><lastmod>{DATE}</lastmod></url>\n"
    if block:
        text = text.replace(marker, block + marker, 1)
        path.write_text(text)
        print("sitemap patched")
    else:
        print("sitemap already has all theme lists")


def main() -> None:
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seofix", "/workspace/scripts/enhance-seo.py")
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")

    items = []
    slugs = []
    for spec in DECKS:
        counts = commsrc.comm.parse_raw(spec["raw"])
        main_n = sum(n for cid, n in counts.items() if cid != LEADER_ID)
        if counts.get(LEADER_ID) != 1 or main_n != 50:
            raise SystemExit(f"{spec['slug']} bad list leader={counts.get(LEADER_ID)} cards={main_n}")
        for cid, n in spec["must"].items():
            if counts.get(cid) != n:
                raise SystemExit(f"{spec['slug']} {cid} want {n} got {counts.get(cid)}")
        slug = spec["slug"]
        slugs.append(slug)
        href = href_for(slug)
        items.append(
            {
                "leader": LEADER_ID,
                "kind": "web",
                "player": "",
                "title": spec["title"],
                "subtitle": spec["subtitle"],
                "source_url": f"https://onepiecedecklists.com{href}",
                "slug": slug,
                "date": DATE,
                "raw": spec["raw"],
                "cards": 50,
            }
        )
        page_path = ROOT / "decklists/yellow-bonney" / f"{slug}.html"
        if page_path.exists():
            page_path.unlink()

    comm = json.loads((ROOT / "data/community-decks.json").read_text())
    rows = comm.get(LEADER_ID) or []
    comm[LEADER_ID] = [row for row in rows if row.get("slug") not in slugs]
    (ROOT / "data/community-decks.json").write_text(
        json.dumps(comm, indent=2, ensure_ascii=False) + "\n"
    )

    commsrc.write_lists(items)

    comm = json.loads((ROOT / "data/community-decks.json").read_text())
    rows = comm.get(LEADER_ID) or []
    by_slug = {row.get("slug"): row for row in rows}
    themed = []
    for spec in DECKS:
        row = by_slug.get(spec["slug"])
        if row is None:
            raise SystemExit(f"missing community row {spec['slug']}")
        themed.append(row)
    rest = [row for row in rows if row.get("slug") not in slugs]
    comm[LEADER_ID] = themed + rest
    (ROOT / "data/community-decks.json").write_text(
        json.dumps(comm, indent=2, ensure_ascii=False) + "\n"
    )
    index = more.load_index()
    more.rebuild_hubs(index, only_ids={LEADER_ID})

    leader = next(L for L in gen.LEADERS if L["id"] == LEADER_ID)
    cache = gen.load_card_cache()
    seo_index = seo.load_index()
    by_href = seo.href_lookup(seo_index)
    for spec in DECKS:
        page_path = ROOT / "decklists/yellow-bonney" / f"{spec['slug']}.html"
        up.upgrade_list_page(page_path, leader, cache)
        patch_page(page_path, spec["notes"], spec["subtitle"])
        seo.patch_file(page_path, seo_index, by_href)
        patch_page(page_path, spec["notes"], spec["subtitle"])
    seo.patch_file(HUB, seo_index, by_href)
    restore_hub_css()
    patch_search(commsrc)
    patch_sitemap()
    print("done", slugs)


if __name__ == "__main__":
    main()
