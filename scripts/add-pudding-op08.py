#!/usr/bin/env python3
"""Add purple/yellow OP08 Charlotte Pudding and host the r/OnePieceTCG list.

Does not run generate-tournament-lists.main().
Does not wipe existing leader lists.
Does not scrape Limitless.
"""

from __future__ import annotations

import importlib.util
import json

PUDDING = "OP08-058"
RAW = (
    "1xOP08-058 4xOP11-070 4xST34-003 4xOP08-062 4xOP05-073 1xOP08-064 "
    "4xOP08-063 3xPRB02-010 4xOP11-067 4xOP03-112 4xOP17-109 4xOP17-103 "
    "4xOP17-114 2xOP03-113 4xOP03-114"
)


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_hub(gen) -> None:
    cache = gen.ensure_cards({PUDDING}, gen.load_card_cache())
    leader = next(L for L in gen.LEADERS if L["id"] == PUDDING)
    path = gen.ROOT / leader["page"]
    (gen.ROOT / leader["dir"]).mkdir(parents=True, exist_ok=True)
    if path.exists():
        print("hub exists", path)
        return
    path.write_text(gen.render_hub_page(leader, cache))
    print("wrote hub", path)


def rebuild_pudding_analysis(gen, ana) -> None:
    cache = gen.load_card_cache()
    leader = next(L for L in gen.LEADERS if L["id"] == PUDDING)
    decks = []
    for path in sorted((gen.ROOT / leader["dir"]).glob("*.html")):
        parsed = ana.parse_deck(path, PUDDING)
        if parsed and not any(cid in gen.BANNED_CARDS for cid in parsed):
            decks.append(parsed)
    if not decks:
        print(PUDDING, "no decks for consensus")
        return
    picks = ana.consensus_list(decks)
    print(PUDDING, "consensus from", len(decks), "lists")
    grouped, totals = ana.grouped_from_picks(leader, picks, cache)
    text_deck = gen.render_text_deck(grouped, cache, ["Leader", "Characters", "Events", "Stages"], totals)
    op17_n = sum(1 for d in decks if ana._has_op17(d))
    block = ana.analysis_block(leader, len(decks), ana.TAKES[PUDDING], text_deck, op17_n)
    page_path = gen.ROOT / leader["page"]
    page = ana.inject(page_path.read_text(), block)
    page = ana.ensure_popup_js(page)
    if "/js/site.js" not in page:
        page = page.replace("</body>", '  <script src="/js/site.js?v=sim-copy"></script>\n</body>')
    page_path.write_text(page)
    cons_path = gen.ROOT / "data/consensus-decks.json"
    cons = json.loads(cons_path.read_text()) if cons_path.exists() else {}
    cons[PUDDING] = {
        "lists": len(decks),
        "cards": [{"id": cid, "count": count, "rate": round(rate, 3)} for cid, count, rate in picks],
    }
    cons_path.write_text(json.dumps(cons, indent=2) + "\n")


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    ana = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")

    counts = comm.parse_raw(RAW)
    main_n = sum(n for cid, n in counts.items() if cid != PUDDING)
    print("pudding cards", main_n, "leader", counts.get(PUDDING))
    if counts.get(PUDDING) != 1 or main_n != 50:
        raise SystemExit(f"expected 1 leader + 50 cards, got {counts.get(PUDDING)} + {main_n}")

    print("=== Pudding hub ===")
    write_hub(gen)

    print("=== r/OnePieceTCG list ===")
    commsrc.write_lists(
        [
            {
                "leader": PUDDING,
                "kind": "web",
                "player": "r/OnePieceTCG",
                "title": "Purple/Yellow Pudding - r/OnePieceTCG",
                "subtitle": "Community screenshot from r/OnePieceTCG · 2026-08-24",
                "source_url": "https://www.reddit.com/r/OnePieceTCG/s/wjyx7BRKbb",
                "slug": "reddit-pudding-wjyx7brkbb",
                "raw": RAW,
                "date": "2026-08-24",
                "cards": 50,
            }
        ]
    )

    print("=== consensus ===")
    rebuild_pudding_analysis(gen, ana)

    print("=== homepage / leaders / sitemap / guides ===")
    more.rewrite_sitemap()
    up.patch_home()
    up.patch_op17()
    seo.main()
    print("pudding ingest done")


if __name__ == "__main__":
    main()
