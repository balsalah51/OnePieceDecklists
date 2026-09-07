#!/usr/bin/env python3
"""Host complete 50-card lists from Utrecht X photos and other Sep 3+ OP17 sources.

Does not invent cards. Does not run generate-tournament-lists.main() or
enhance-seo.main().
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path("/workspace")

# Verified from public sources. Quantities sum to 1 leader + 50 main.
LISTS = [
    {
        "leader": "OP15-058",
        "kind": "x",
        "player": "XIXO",
        "title": "Flame-Flame Fruit Coliseum Utrecht finals - XIXO Enel",
        "subtitle": "List read from the public BCG Fest Utrecht X deck graphic · 2026-09-04",
        "source_url": "https://pbs.twimg.com/media/HRZv9QwW8AI08wF?format=jpg&name=orig",
        "slug": "x-utrecht-coliseum-xixo-enel",
        "date": "2026-09-04",
        "raw": (
            "1xOP15-058 3xOP07-064 4xOP10-067 3xST10-010 3xOP15-071 3xOP05-077 "
            "1xOP09-077 4xOP15-061 2xOP15-066 4xOP12-071 4xOP15-067 3xOP15-074 "
            "4xOP15-075 4xOP15-076 4xOP15-077 4xOP15-078"
        ),
        "cards": 50,
        "photo": "data/x-media/HRZv9QwW8AI08wF.jpg",
    },
    {
        "leader": "OP17-058",
        "kind": "reddit",
        "player": "TwerkMasterFlex",
        "title": "Locals 1st - TwerkMasterFlex Kaido",
        "subtitle": "List from the public r/OnePieceTCG post · 2026-09-05",
        "source_url": "https://www.reddit.com/r/OnePieceTCG/comments/1w81q75/took_first_place_at_locals_with_kaido_heres_my/",
        "slug": "reddit-kaido-locals-1w81q75",
        "date": "2026-09-05",
        "raw": (
            "1xOP17-058 4xEB04-032 2xOP17-067 4xOP17-073 4xOP17-074 4xEB04-031 "
            "2xEB04-030 4xOP17-061 2xOP17-065 2xOP17-069 4xOP17-062 2xOP17-063 "
            "2xST34-004 4xOP15-078 2xOP17-076 4xOP07-077 4xOP07-076"
        ),
        "cards": 50,
    },
    {
        "leader": "OP14-080",
        "kind": "web",
        "player": "Million_X",
        "title": "Pirate Party Moria - Million_X",
        "subtitle": "Public CardKaizoku list from r/OnePieceTCG · 2026-09-04",
        "source_url": (
            "https://www.cardkaizoku.com/deckbuilder?view=deck&game=onepiece&deck="
            "1xOP14-080%7C4xOP14-104%7C2xOP15-080%7C4xOP14-102%7C4xOP14-109%7C"
            "4xOP14-111%7C4xOP14-110%7C4xOP15-079%7C4xOP15-090%7C2xOP12-112%7C"
            "4xOP13-113%7C4xOP17-109%7C2xOP17-111%7C4xOP17-116%7C4xOP14-089"
        ),
        "slug": "reddit-moria-pirate-party-1w6z9nf",
        "date": "2026-09-04",
        "raw": (
            "1xOP14-080 4xOP14-104 2xOP15-080 4xOP14-102 4xOP14-109 4xOP14-111 "
            "4xOP14-110 4xOP15-079 4xOP15-090 2xOP12-112 4xOP13-113 4xOP17-109 "
            "2xOP17-111 4xOP17-116 4xOP14-089"
        ),
        "cards": 50,
    },
]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    ana = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seofix", "/workspace/scripts/enhance-seo.py")

    needed = set()
    parsed = []
    for item in LISTS:
        counts = comm.parse_raw(item["raw"])
        needed.update(counts)
        parsed.append((item, counts))
    cache = gen.ensure_cards(needed, gen.load_card_cache())

    ready = []
    for item, counts in parsed:
        lid = item["leader"]
        main_n = sum(n for cid, n in counts.items() if cid != lid)
        banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
        missing = [cid for cid in counts if cid not in cache]
        print(
            item["slug"],
            "cards",
            main_n,
            "leader",
            counts.get(lid),
            "banned",
            banned,
            "missing",
            missing,
        )
        if counts.get(lid) != 1 or main_n != 50 or banned or missing:
            raise SystemExit(f"bad list {item['slug']}")
        ready.append(item)

    print("=== write Utrecht / Sep 3+ community lists ===")
    touched = commsrc.write_lists(ready)
    print("touched", sorted(touched))

    print("=== consensus ===")
    ana.main()

    print("=== homepage / sitemap ===")
    index = more.load_index()
    if touched:
        more.rebuild_hubs(index, only_ids=touched)
    seo.rewrite_sitemap(seo.href_lookup(seo.load_index()))
    up.patch_home()
    up.patch_op17()

    log_path = ROOT / "data/utrecht-sep3-x-log.json"
    log = {
        "hosted": [
            {
                "slug": item["slug"],
                "leader": item["leader"],
                "player": item["player"],
                "date": item["date"],
                "source_url": item["source_url"],
                "raw": item["raw"],
            }
            for item in ready
        ],
        "notes": [
            "Benjo PY Nico Robin winner photo (r/OnePieceTCG 1w7hs0u / i.redd.it/azut93u8pknh1.jpeg) "
            "matches the already-hosted submitted-flame-flame-winner-utrecht-2026-09-04 list; not duplicated.",
            "XIXO Enel list transcribed from the public BCG Fest Utrecht X graphic "
            "https://pbs.twimg.com/media/HRZv9QwW8AI08wF (linked from r/OnePieceTCG 1w7dwx2). "
            "Top 4 bracket (1w7dm2j) confirms Enel finalist XIXO. No OP17 cards in that list.",
            "Limitless Sep 3 OP17 events (Rumble #7, Dressrosa, UA weekly) already hosted. "
            "La LIGA 5 Sep 4 and Utrecht Vorbereitung have standings but no decklists.",
            "Flame-Flame Top 4 Ace (Rian) and Sabo (Borsaistrash) lists were requested in comments "
            "but no complete 50-card photo or ID dump was public.",
        ],
    }
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    print("wrote", log_path)


if __name__ == "__main__":
    main()
