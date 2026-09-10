#!/usr/bin/env python3
"""Host complete lists from sources that are not Limitless.

OPTCG.GG (skips ChinoizeCup), TCG PORTAL shop battles, and OPDeckGuide.
Only writes a page when the source is 1 leader + 50 cards with no bans.
Does not invent cards from photos. Does not wipe existing list pages.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

ROOT = Path("/workspace")
SINCE = "2026-08-15"
UNTIL = date.today().isoformat()


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    hunt = load("hunt", "/workspace/scripts/hunt-window-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")

    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    portal.SINCE = SINCE
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL

    found: list[dict] = []
    seen: set[str] = set()

    print("=== OPTCG.GG (not ChinoizeCup) ===", flush=True)
    for item in optcggg.collect_lists(gen, commsrc):
        commsrc.record(found, item, seen)

    print("=== TCG PORTAL ===", flush=True)
    for item in portal.collect_lists(gen, commsrc):
        commsrc.record(found, item, seen)

    print("=== OPDeckGuide ===", flush=True)
    for item in hunt.opdeck_items(opdeck, commsrc):
        commsrc.record(found, item, seen)

    log_path = ROOT / "data/other-sources-log.json"
    log_path.write_text(
        json.dumps(
            {
                "window": {"start": SINCE, "end": UNTIL},
                "found": found,
                "hosts": sorted(
                    {
                        (item.get("source_url") or "").split("/")[2]
                        for item in found
                        if "://" in (item.get("source_url") or "")
                    }
                ),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print("complete lists", len(found), "log", log_path, flush=True)

    print("=== write community lists ===", flush=True)
    commsrc.write_lists(found)

    print("=== rebuild hubs / homepage / SEO ===", flush=True)
    index = more.load_index()
    more.rebuild_hubs(index)
    more.rewrite_sitemap()
    analysis.main()
    up.patch_home()
    up.patch_op17()
    seo.main()
    buy = load("tcgbuy", "/workspace/scripts/add-tcgplayer-buy.py")
    buy.main()
    seofix = load("seofix", "/workspace/scripts/enhance-seo.py")
    seofix.main()

    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "community_found": len(found),
        "community_slugs": [item.get("slug") for item in found],
        "hosts": sorted(
            {
                (item.get("source_url") or "").split("/")[2]
                for item in found
                if "://" in (item.get("source_url") or "")
            }
        ),
    }
    (ROOT / "data/other-sources-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("other-sources ingest done", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
