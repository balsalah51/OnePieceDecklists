#!/usr/bin/env python3
"""Host the complete public EB05 lists that were posted with card IDs.

Does not invent cards. A list is written only when it is one hosted leader
plus 50 other cards and contains no banned card.
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path("/workspace")
TODAY = date.today().isoformat()
SITE = "https://onepiecedecklists.com"

LISTS = [
    {
        "leader": "EB05-010",
        "kind": "web",
        "player": "OPDeckGuide",
        "title": "Nico Robin EB05 Deck Guide",
        "subtitle": "OPDeckGuide · public EB05 pre-release list",
        "source_url": "https://opdeckguide.com/deck-guides/nico-robin-eb05/",
        "slug": "opdeck-nico-robin-eb05",
        "date": "2026-10-16",
        "raw": (
            "1xEB05-010 4xEB05-050 4xEB05-056 4xOP13-113 4xEB05-057 4xOP17-109 "
            "4xEB04-018 4xEB05-052 4xEB04-058 4xEB05-055 4xEB05-016 4xOP13-031 "
            "3xOP14-108 3xOP17-022"
        ),
    },
    {
        "leader": "EB05-010",
        "kind": "web",
        "player": "thohar88",
        "title": "EB05 Nico Robin list",
        "subtitle": "Reddit · public EB05 pre-release list",
        "source_url": "https://www.reddit.com/r/OnePieceTCG/comments/1wydz1o/eb05_nico_deck_list_help/",
        "slug": "reddit-thohar88-eb05-nico-robin",
        "date": "2026-10-05",
        "raw": (
            "1xEB05-010 4xEB05-050 4xEB05-056 3xOP15-104 4xEB05-057 4xEB05-012 "
            "3xEB05-051 4xOP17-109 4xEB05-052 4xEB05-053 2xOP15-113 4xOP18-031 "
            "4xEB05-055 4xEB05-016 2xEB03-055"
        ),
    },
    {
        "leader": "OP14-079",
        "kind": "web",
        "player": "Million_X",
        "title": "EB05 Crocodile list",
        "subtitle": "Reddit · public EB05 Baroque Works list",
        "source_url": "https://www.reddit.com/r/OnePieceTCG/comments/1wraufc/deck_recommendations_for_eb05op18/",
        "slug": "reddit-million-x-eb05-crocodile",
        "date": "2026-10-03",
        "raw": (
            "1xOP14-079 3xP-146 3xP-147 2xP-149 4xOP14-120 3xOP14-096 3xOP14-099 "
            "4xOP14-091 3xOP14-084 4xOP14-083 2xEB05-048 3xEB05-045 4xEB05-044 "
            "3xOP14-085 4xOP14-087 2xP-143 3xOP14-086"
        ),
    },
]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cache_card(card: dict, set_code: str) -> dict:
    colors = card.get("colors") or []
    if isinstance(colors, str):
        color = colors
    else:
        color = "/".join(colors)
    types = card.get("types") or card.get("traits") or []
    if types and isinstance(types[0], dict):
        types = [row.get("name") or row.get("code") or "" for row in types]
    kind = (card.get("kind") or card.get("type") or "character").lower()
    category = {"leader": "Leader", "character": "Character", "event": "Event", "stage": "Stage"}.get(
        kind, "Character"
    )
    counter = card.get("counter") or ""
    if isinstance(counter, int):
        counter = f"+{counter}" if counter else ""
    cid = card["id"] if "id" in card else card["code"]
    return {
        "id": cid,
        "name": card.get("name") or cid,
        "category": category,
        "color": color.title() if color.islower() else color,
        "life": str(card["life"]) if card.get("life") not in (None, "") else None,
        "cost": str(card["cost"]) if card.get("cost") not in (None, "") else None,
        "power": str(card["power"]) if card.get("power") not in (None, "") else None,
        "counter": counter or None,
        "attribute": card.get("attribute") or None,
        "types": " / ".join(types),
        "effect": card.get("effect") or "",
        "image": f"https://cards.oplaytcg.com/{set_code}/en/{cid}.webp",
        "source": f"https://oplaytcg.com/en/cards/{cid}",
    }


def seed_cache(gen) -> None:
    cache = gen.load_card_cache()
    eb05 = json.loads((ROOT / "scripts" / "eb05-cards.json").read_text())
    for card in eb05:
        cache[card["id"]] = cache_card(card, "EB05")
    op18 = json.loads(Path("/tmp/op18-new.json").read_text())
    for cid, card in op18.items():
        card = dict(card)
        card["id"] = cid
        cache[cid] = cache_card(card, "OP18")
    (ROOT / "data" / "card-cache.json").write_text(
        json.dumps(cache, indent=2, ensure_ascii=False) + "\n"
    )
    print("seeded cache", len(cache))


def update_sitemaps(rels: list[str]) -> None:
    lists_path = ROOT / "sitemap-lists.xml"
    text = lists_path.read_text()
    existing = set(re.findall(r"<loc>([^<]+)</loc>", text))
    rows = []
    for rel in rels:
        loc = f"{SITE}/{rel.lstrip('/')}"
        if loc not in existing:
            rows.append(f"  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod></url>\n")
    if rows:
        text = text.replace("</urlset>", "".join(rows) + "</urlset>")
        lists_path.write_text(text if text.endswith("\n") else text + "\n")
    print("sitemap-lists added", len(rows))

    core_path = ROOT / "sitemap-core.xml"
    core = core_path.read_text()
    core_locs = {
        f"{SITE}/",
        f"{SITE}/tier-list.html",
        f"{SITE}/recent.html",
        f"{SITE}/extra-grand-battle.html",
        f"{SITE}/eb05-spoilers.html",
        f"{SITE}/op18-spoilers.html",
        f"{SITE}/eb05-lists.html",
        f"{SITE}/decklists/eb05-nico-robin.html",
        f"{SITE}/decklists/crocodile.html",
    }
    for loc in core_locs:
        if loc in core:
            core = re.sub(
                rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+",
                rf"\g<1>{TODAY}",
                core,
            )
        else:
            core = core.replace(
                "</urlset>",
                f"  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod></url>\n</urlset>",
            )
    core_path.write_text(core)
    idx = (ROOT / "sitemap.xml").read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{TODAY}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{TODAY}", idx)
    (ROOT / "sitemap.xml").write_text(idx)


def main() -> None:
    gen = load("genlists", str(ROOT / "scripts" / "generate-tournament-lists.py"))
    comm = load("commlists", str(ROOT / "scripts" / "add-community-lists.py"))
    commsrc = load("commsrc", str(ROOT / "scripts" / "scrape-community-sources.py"))
    seed_cache(gen)
    found = []
    seen: set[str] = set()
    for item in LISTS:
        counts = comm.parse_raw(item["raw"])
        main_n = sum(n for cid, n in counts.items() if cid != item["leader"])
        print(item["slug"], "leader", item["leader"], "main", main_n, "unique", len(counts))
        if counts.get(item["leader"]) != 1 or main_n != 50:
            raise SystemExit(f"refusing incomplete list {item['slug']}")
        if any(cid in gen.BANNED_CARDS for cid in counts):
            raise SystemExit(f"banned card in {item['slug']}")
        item["cards"] = main_n
        commsrc.record(found, item, seen)
    touched = commsrc.write_lists(found)
    print("touched", sorted(touched))

    import runpy

    runpy.run_path(str(ROOT / "scripts" / "build-eb05-spoilers.py"), run_name="__main__")
    runpy.run_path(str(ROOT / "scripts" / "build-op18-spoilers.py"), run_name="__main__")
    runpy.run_path(str(ROOT / "scripts" / "build-eb05-lists.py"), run_name="__main__")

    rels = []
    for leader in gen.LEADERS:
        if leader["id"] not in touched and leader["id"] not in {"EB05-010", "OP14-079"}:
            continue
        hub = ROOT / leader["page"]
        if hub.exists():
            rels.append(leader["page"])
        for page in (ROOT / leader["dir"]).glob("*.html"):
            rels.append(page.relative_to(ROOT).as_posix())
    rels.append("eb05-lists.html")
    # New Limitless pages from this branch are untracked deck html files.
    import subprocess

    status = subprocess.check_output(["git", "status", "--porcelain", "decklists"], text=True)
    for line in status.splitlines():
        path = line[3:].strip()
        if path.endswith(".html"):
            rels.append(path)
    update_sitemaps(rels)


if __name__ == "__main__":
    main()
