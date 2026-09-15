#!/usr/bin/env python3
"""Host Basem's custom OP09 Nico Robin 50-card list.

Starts from the OP17 consensus on decklists/nico-robin.html, adds the requested
cards, and drops 5 copies that OP17 Robin lists already cut most often.
Does not wipe existing list pages. Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path("/workspace")
SLUG = "nico-flame-basem"
HREF = f"/decklists/nico-robin/{SLUG}.html"
ALT_LEADER = (
    "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP09/OP09-062_p1_EN.webp"
)
DON_IMG = "/img/cards/chinese-3rd-anniversary-don.jpg"

# Consensus 50 minus the 5 most-cut copies across 152 OP17 Robin lists:
#   -2 OP12-112 Baby 5 (82/152 lists play 0)
#   -1 EB04-058 Borsalino (mode is 2, consensus was 3)
#   -1 OP17-110 Perospero (mode is 2, consensus was 3)
#   -1 ST34-003 Brulee (41 lists play 0; avg 2.27 vs consensus 3)
# Then +1 OP09-119 purple Secret Rare Luffy, +2 ST36-005 Captain Kid,
# +2 OP11-067 Charlotte Katakuri.
RAW = (
    "1xOP09-062 2xST34-003 4xOP17-113 4xOP17-107 4xOP17-109 4xOP17-074 "
    "4xOP17-102 2xEB04-058 4xOP17-106 4xOP17-114 2xOP17-110 3xOP16-119 "
    "4xOP17-112 4xOP09-078 1xOP09-119 2xST36-005 2xOP11-067"
)

NOTES = """        <p>Custom 50-card list from the OP17 consensus on this hub. Adds 1 purple Secret Rare Monkey.D.Luffy (OP09-119), 2 starter Captain Kid (ST36-005), and 2 Charlotte Katakuri (OP11-067). To make room, drops the 5 copies OP17 Robin lists already trim most often: both Baby 5, 1 Borsalino, 1 Perospero, and 1 Brulee.</p>"""

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
        "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP09/OP09-062_EN.webp",
        ALT_LEADER,
    )


def patch_page(path: Path) -> None:
    text = path.read_text()
    text = text.replace('href="/css/site.css?v=home-pro8"', 'href="/css/site.css?v=home-pro16"')
    text = text.replace('href="/css/site.css?v=home-pro2"', 'href="/css/site.css?v=home-pro16"')
    if "Custom 50-card list from the OP17 consensus" not in text:
        text = text.replace(
            "<p>Submitted 50-card list · 2026-09-15</p>",
            "<p>Submitted 50-card list · 2026-09-15</p>\n" + NOTES,
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
        '<div class="muted">Alt art · OP09-062</div>',
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


def patch_search() -> None:
    path = ROOT / "search.html"
    text = path.read_text()
    entry = {
        "t": "Nico Flame Basem",
        "n": "Basem custom OP17 Robin list · 2026-09-15",
        "h": HREF,
        "q": "Nico Flame Basem Nico Robin OP09-062 Basem custom list Captain Kid Katakuri Secret Rare Luffy",
    }
    m = re.search(
        r'(<script type="application/json" id="search-lists">)(.*?)(</script>)',
        text,
        re.S,
    )
    if not m:
        raise SystemExit("search-lists json missing")
    blob = json.loads(m.group(2))
    if not any(row.get("h") == HREF for row in blob):
        blob.insert(0, entry)
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
    if HREF not in text.split('id="search-lists"', 1)[0]:
        # Prefer the Recent lists group if present.
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
    line = f'  <url><loc>{loc}</loc><lastmod>2026-09-15</lastmod></url>\n'
    marker = "  <url><loc>https://onepiecedecklists.com/decklists/nico-robin/opdb-nico-robin-by-benjo-2354.html</loc>"
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
        "leader": "OP09-062",
        "kind": "web",
        "player": "Basem",
        "title": "Nico Flame Basem",
        "subtitle": "Submitted 50-card list · 2026-09-15",
        "source_url": f"https://onepiecedecklists.com{HREF}",
        "slug": SLUG,
        "date": "2026-09-15",
        "raw": RAW,
        "cards": 50,
    }
    counts = commsrc.comm.parse_raw(RAW)
    main_n = sum(n for cid, n in counts.items() if cid != "OP09-062")
    if counts.get("OP09-062") != 1 or main_n != 50:
        raise SystemExit(f"bad list leader={counts.get('OP09-062')} cards={main_n}")

    page_path = ROOT / "decklists/nico-robin" / f"{SLUG}.html"
    if page_path.exists():
        page_path.unlink()
    comm = json.loads((ROOT / "data/community-decks.json").read_text())
    rows = comm.get("OP09-062") or []
    comm["OP09-062"] = [row for row in rows if row.get("slug") != SLUG]
    (ROOT / "data/community-decks.json").write_text(
        json.dumps(comm, indent=2, ensure_ascii=False) + "\n"
    )

    commsrc.write_lists([item])

    leader = next(L for L in gen.LEADERS if L["id"] == "OP09-062")
    cache = gen.load_card_cache()
    up.upgrade_list_page(page_path, leader, cache)
    patch_page(page_path)

    index = seo.load_index()
    by_href = seo.href_lookup(index)
    seo.patch_file(page_path, index, by_href)
    seo.patch_file(ROOT / "decklists/nico-robin.html", index, by_href)
    patch_page(page_path)  # keep alt-art + DON after SEO head rewrite
    patch_search()
    patch_sitemap()
    print("done", page_path)


if __name__ == "__main__":
    main()
