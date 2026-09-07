#!/usr/bin/env python3
"""Rebuild hubs, homepage, SEO, and analysis after the new-leader scrape."""

from __future__ import annotations

import importlib.util

spec = importlib.util.spec_from_file_location("morelists", "/workspace/scripts/add-more-tournament-lists.py")
more = importlib.util.module_from_spec(spec)
spec.loader.exec_module(more)

uspec = importlib.util.spec_from_file_location("upgrade", "/workspace/scripts/upgrade-public-pages.py")
up = importlib.util.module_from_spec(uspec)
uspec.loader.exec_module(up)

sspec = importlib.util.spec_from_file_location("seo", "/workspace/scripts/generate-seo-pages.py")
seo = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(seo)

aspec = importlib.util.spec_from_file_location("newleaders", "/workspace/scripts/add-new-leaders.py")
new = importlib.util.module_from_spec(aspec)
aspec.loader.exec_module(new)


def main() -> None:
    index = more.load_index()
    more.rebuild_hubs(index)
    up.main()
    seo.main()
    new.rebuild_new_analysis(new.gen.load_card_cache(), only_ids=new.NEW_IDS)
    more.rewrite_sitemap()
    print("finish done")


if __name__ == "__main__":
    main()
