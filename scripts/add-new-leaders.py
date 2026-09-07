#!/usr/bin/env python3
"""Add Doffy, Buggy, and Sengoku hubs and scrape Limitless lists.

Does not run generate-tournament-lists.main().
Does not wipe existing leader lists.
"""

from __future__ import annotations

import importlib.util
import json

NEW_IDS = {"OP14-060", "OP16-041", "OP16-060"}

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

mspec = importlib.util.spec_from_file_location("morelists", "/workspace/scripts/add-more-tournament-lists.py")
more = importlib.util.module_from_spec(mspec)
mspec.loader.exec_module(more)

aspec = importlib.util.spec_from_file_location("analysis", "/workspace/scripts/add-leader-analysis.py")
ana = importlib.util.module_from_spec(aspec)
aspec.loader.exec_module(ana)

ROOT = gen.ROOT
PAGES = 55
EXTRA_LIMIT = 80
PER_EVENT = 4


def write_stubs(cache: dict) -> None:
    for leader in gen.LEADERS:
        if leader["id"] not in NEW_IDS:
            continue
        path = ROOT / leader["page"]
        if path.exists():
            print("hub exists", path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        (ROOT / leader["dir"]).mkdir(parents=True, exist_ok=True)
        path.write_text(gen.render_hub_page(leader, cache))
        print("wrote hub", path)


def rebuild_new_analysis(cache: dict, only_ids: set[str] | None = None) -> None:
    cons_path = ROOT / "data/consensus-decks.json"
    cons = json.loads(cons_path.read_text()) if cons_path.exists() else {}
    target = only_ids or NEW_IDS
    for leader in gen.LEADERS:
        lid = leader["id"]
        if lid not in target:
            continue
        decks = []
        for path in sorted((ROOT / leader["dir"]).glob("*.html")):
            parsed = ana.parse_deck(path, lid)
            if parsed and not any(cid in gen.BANNED_CARDS for cid in parsed):
                decks.append(parsed)
        if not decks:
            print(lid, "no decks for consensus")
            continue
        picks = ana.consensus_list(decks)
        print(lid, "consensus from", len(decks), "lists")
        grouped, totals = ana.grouped_from_picks(leader, picks, cache)
        text_deck = gen.render_text_deck(grouped, cache, ["Leader", "Characters", "Events", "Stages"], totals)
        block = ana.analysis_block(leader, len(decks), ana.TAKES[lid], text_deck)
        page_path = ROOT / leader["page"]
        page = ana.inject(page_path.read_text(), block)
        page = ana.ensure_popup_js(page)
        if "/js/site.js" not in page:
            page = page.replace("</body>", '  <script src="/js/site.js?v=sim-copy"></script>\n</body>')
        page_path.write_text(page)
        cons[lid] = {
            "lists": len(decks),
            "cards": [{"id": cid, "count": count, "rate": round(rate, 3)} for cid, count, rate in picks],
        }
    cons_path.write_text(json.dumps(cons, indent=2) + "\n")


def main() -> None:
    cache = gen.ensure_cards(set(NEW_IDS), gen.load_card_cache())
    write_stubs(cache)
    index = more.load_index()
    index = more.fetch_more(
        index,
        pages=PAGES,
        only_ids=NEW_IDS,
        extra_limit=EXTRA_LIMIT,
        per_event=PER_EVENT,
    )
    more.save_index(index)
    more.rebuild_hubs(index, only_ids=NEW_IDS)
    cache = gen.load_card_cache()
    rebuild_new_analysis(cache)
    more.rewrite_sitemap()
    print("done")


if __name__ == "__main__":
    main()
