#!/usr/bin/env python3
"""Add hubs for unhosted leaders that have complete OP17-splash lists.

Only writes list pages whose 50-card dump includes at least one OP17 card.
Does not wipe existing leader pages.
"""

from __future__ import annotations

import importlib.util

NEW_IDS = {
    "OP13-004",
    "OP09-062",
    "OP14-080",
    "OP14-041",
    "OP12-081",
    "OP09-001",
    "OP05-098",
    "ST10-002",
    "OP09-061",
    "ST13-003",
    "OP12-040",
    "OP05-002",
    "EB04-001",
    "OP10-099",
    "OP07-059",
    "ST13-001",
    "OP05-041",
    "OP05-060",
    "OP07-079",
    "OP10-022",
    "OP06-022",
    "ST14-001",
    "EB02-010",
    "OP14-040",
    "OP12-041",
}


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_hubs(gen, cache: dict) -> None:
    for leader in gen.LEADERS:
        if leader["id"] not in NEW_IDS:
            continue
        path = gen.ROOT / leader["page"]
        (gen.ROOT / leader["dir"]).mkdir(parents=True, exist_ok=True)
        if path.exists():
            print("hub exists", path)
            continue
        path.write_text(gen.render_hub_page(leader, cache))
        print("wrote hub", path)


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    ana = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")

    cache = gen.ensure_cards(set(NEW_IDS), gen.load_card_cache())
    print("=== hubs ===")
    write_hubs(gen, cache)

    print("=== Limitless OP17-splash lists ===")
    index = more.load_index()
    index = more.fetch_more(
        index,
        pages=8,
        only_ids=NEW_IDS,
        extra_limit=40,
        per_event=8,
        since="2026-08-15",
        require_op17=True,
    )
    more.save_index(index)
    more.rebuild_hubs(index, only_ids=NEW_IDS)

    print("=== consensus ===")
    ana.main()

    print("=== homepage / guides ===")
    up.patch_home()
    up.patch_op17()
    seo.main()
    print("=== TCGplayer ===")
    buy = load("tcgbuy", "/workspace/scripts/add-tcgplayer-buy.py")
    buy.main()
    print("=== SEO ===")
    seofix = load("seofix", "/workspace/scripts/enhance-seo.py")
    seofix.main()
    print("op17 splash leaders done")


if __name__ == "__main__":
    main()
