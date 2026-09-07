#!/usr/bin/env python3
"""Pull new lists dated yesterday and today from Limitless, X, and public deck pages.

Does not wipe existing list pages. Rebuilds hubs, consensus lists, and the homepage.
"""

from __future__ import annotations

import importlib.util

SINCE = "2026-08-27"  # recrape window: 27 Aug through today
UP_LUFFY = "OP11-040"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_up_luffy_hub(gen) -> None:
    cache = gen.ensure_cards({UP_LUFFY}, gen.load_card_cache())
    leader = next(L for L in gen.LEADERS if L["id"] == UP_LUFFY)
    path = gen.ROOT / leader["page"]
    (gen.ROOT / leader["dir"]).mkdir(parents=True, exist_ok=True)
    if path.exists():
        print("hub exists", path)
        return
    path.write_text(gen.render_hub_page(leader, cache))
    print("wrote hub", path)


def main() -> None:
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")

    print("=== UP Luffy hub ===")
    write_up_luffy_hub(more.gen)

    print("=== Limitless Play since", SINCE, "===")
    index = more.load_index()
    index = more.fetch_more(
        index,
        pages=8,
        extra_limit=400,
        per_event=99,
        since=SINCE,
    )
    more.save_index(index)

    print("=== X / YouTube / OnePieceDB / weird sources ===")
    commsrc.main()

    print("=== Reddit / X photo transcripts ===")
    photos = load("photos", "/workspace/scripts/transcribe-deck-images.py")
    photos.main()

    index = more.load_index()
    more.rebuild_hubs(index)
    more.rewrite_sitemap()

    print("=== consensus aggregates ===")
    analysis.main()

    print("=== homepage / public pages ===")
    up.patch_home()
    up.patch_op17()
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")
    seo.main()
    print("=== TCGplayer buy scripts ===")
    buy = load("tcgbuy", "/workspace/scripts/add-tcgplayer-buy.py")
    buy.main()
    print("=== SEO internal links / on-page ===")
    seofix = load("seofix", "/workspace/scripts/enhance-seo.py")
    seofix.main()
    print("ingest done")


if __name__ == "__main__":
    main()
