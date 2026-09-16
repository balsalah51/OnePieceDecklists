#!/usr/bin/env python3
"""Host Ammo Bubba's custom OP13 Yellow Bonney 50-card list.

Locked 4-ofs, then 2-ofs from the remaining requested lines using OP17
yellow Bonney list counts. Alt-art OP13-100 leader and Chinese 3rd
Anniversary DON!!. Does not wipe other list pages.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path("/workspace")
LEADER_ID = "OP13-100"
SLUG = "ammo-bubba"
HREF = f"/decklists/yellow-bonney/{SLUG}.html"
HUB = ROOT / "decklists/yellow-bonney.html"
ALT_LEADER = (
    "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP13/OP13-100_p1_EN.webp"
)
DON_IMG = "/img/cards/chinese-3rd-anniversary-don.jpg"

# Locked 4-ofs (36): 3c Pudding, TB Perona, Hogback, 1c 2k Streusen,
# 9c Rush Bonney, Lilith searcher, Shiryu, Devon, 0c event.
# Remaining 14: 2 each of Kid, Teach, Smoothie, S3G, Borsalino, 8c Moria,
# O-Nami. ST34 has no Kid reprint so Kid is ST36-005. Usopp and S-Snake
# stay out — 1-drops and 4-drops are already full (Lilith+Streusen, and
# Devon+Hogback+Perona). O-Nami is 2 not 4 so those 2-ofs still fit.
RAW = (
    "1xOP13-100 4xOP17-113 4xOP13-113 4xOP17-109 4xOP14-111 "
    "4xOP14-110 4xOP16-104 2xOP17-106 2xEB04-058 2xST36-005 4xOP16-108 "
    "2xOP17-114 2xOP14-104 2xOP16-119 4xOP13-108 4xOP06-115 2xOP06-101"
)

NOTES = """        <p>Custom 50-card Yellow Bonney list. Locked 4-ofs: 3-cost Charlotte Pudding, Thriller Bark Perona, Dr. Hogback, 1-cost 2k Streusen, 9-cost Rush Jewelry Bonney, Lilith searcher, Shiryu, Catarina Devon, and the 0-cost event. The rest is 2-ofs from requested lines using OP17 yellow Bonney list counts: starter Captain Kid (ST36-005; ST34 has no Kid), Teach, Smoothie, Sweet 3 Generals, Borsalino, 8-cost Gecko Moria, and O-Nami. O-Nami is 2 not 4 so Kid and Moria still fit. Usopp and S-Snake stay out — 1-drops and 4-drops are already full.</p>"""

DON_BLOCK = f"""        <section class="leader-block" style="margin-top:22px">
          <div class="section-title">
            <h3>DON!!</h3>
            <div class="muted">Chinese 3rd Anniversary</div>
          </div>
          <div class="card-grid">
        <article class="card-entry">
          <img src="{DON_IMG}" alt="Chinese 3rd Anniversary DON!! card, Jewelry Bonney and Bartholomew Kuma" loading="lazy" style="width:min(520px,100%);height:auto;max-width:100%" />
          <div>
            <div class="id">DON!! · Chinese 3rd Anniversary</div>
            <h4>Jewelry Bonney &amp; Bartholomew Kuma</h4>
            <div class="stats">Exclusive DON!! from the Chinese 3rd Anniversary gift box</div>
            <div class="text">Pink-border commemorative DON!! with Bonney and Kuma. Not part of the 50-card list. Table DON!! for this build.</div>
          </div>
        </article>
          </div>
        </section>
"""


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def use_alt_leader(text: str) -> str:
    return text.replace(
        "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP13/OP13-100_EN.webp",
        ALT_LEADER,
    )


def patch_page(path: Path) -> None:
    text = path.read_text()
    text = text.replace('href="/css/site.css?v=home-pro8"', 'href="/css/site.css?v=home-pro16"')
    text = text.replace('href="/css/site.css?v=home-pro2"', 'href="/css/site.css?v=home-pro16"')
    text = re.sub(
        r'(<p>Submitted 50-card list · 2026-09-16</p>\n)(?:        <p>Custom 50-card.*?</p>\n)?',
        r'\1' + NOTES + '\n',
        text,
        count=1,
        flags=re.S,
    )
    if "Custom 50-card Yellow Bonney list" not in text:
        text = text.replace(
            "<p>Submitted 50-card list · 2026-09-16</p>",
            "<p>Submitted 50-card list · 2026-09-16</p>\n" + NOTES,
            1,
        )
    if DON_IMG not in text:
        marker = '        <!-- DECK_STATS -->'
        if marker in text:
            text = text.replace(marker, DON_BLOCK + marker, 1)
        else:
            text = text.replace(
                '        <section class="text-deck">',
                DON_BLOCK + '        <section class="text-deck">',
                1,
            )
    text = text.replace(
        '<div class="muted">1 card</div>',
        '<div class="muted">Alt art · OP13-100</div>',
        1,
    )
    text = re.sub(
        r'<p class="muted" style="margin-top:22px">Community list from a public deck builder\..*?</p>',
        '<p class="muted" style="margin-top:22px">Custom submitted 50-card list. English card text from Limitless One Piece. Chinese 3rd Anniversary DON!! photo hosted on this site. Other images hosted by Limitless. Not affiliated with Bandai.</p>',
        text,
        count=1,
        flags=re.S,
    )
    text = use_alt_leader(text)
    path.write_text(text)


def restore_hub_css() -> None:
    text = HUB.read_text()
    text = text.replace('href="/css/site.css?v=home-pro8"', 'href="/css/site.css?v=home-pro16"')
    HUB.write_text(text)


def patch_search() -> None:
    path = ROOT / "search.html"
    text = path.read_text()
    entry = {
        "t": "Ammo Bubba",
        "n": "Ammo Bubba custom OP17 Yellow Bonney list · 2026-09-16",
        "h": HREF,
        "q": "Ammo Bubba Yellow Bonney OP13-100 Lilith Perona Hogback Shiryu Devon Streusen O-Nami",
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
                  <div style="font-weight:700">Ammo Bubba</div>
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
    marker = "  <url><loc>https://onepiecedecklists.com/decklists/yellow-bonney/nico-flame-basem.html</loc>"
    if marker not in text:
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
        "player": "Ammo Bubba",
        "title": "Ammo Bubba",
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
    locked = {
        "OP17-109": 4,
        "OP14-111": 4,
        "OP14-110": 4,
        "OP17-113": 4,
        "OP13-108": 4,
        "OP13-113": 4,
        "OP16-108": 4,
        "OP16-104": 4,
        "OP06-115": 4,
    }
    for cid, n in locked.items():
        if counts.get(cid) != n:
            raise SystemExit(f"locked {cid} want {n} got {counts.get(cid)}")
    if counts.get("OP07-099"):
        raise SystemExit("Usopp should not be in this 50")

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
    mine["player"] = "Ammo Bubba"
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
