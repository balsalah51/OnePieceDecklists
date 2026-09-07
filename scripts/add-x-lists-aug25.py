#!/usr/bin/env python3
"""Host complete 50-card lists from public X photos posted 2026-08-25.

Card IDs are Limitless-verified from ChinoizeCup #101 (same event as the
@Chinoize_ photo post). Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import importlib.util
import json

TWEET = "https://x.com/Chinoize_/status/2092357744921612794"
DATE = "2026-08-25"

LISTS = [
    {
        "leader": "OP14-020",
        "kind": "x",
        "player": "MaGe",
        "title": "ChinoizeCup #101 1st - MaGe Mihawk",
        "subtitle": "List from the public X photo post @Chinoize_ · 2026-08-25 · IDs verified on Limitless",
        "source_url": TWEET,
        "slug": "x-chinoize-101-mage-mihawk",
        "date": DATE,
        "raw": (
            "1xOP14-020 4xOP07-022 4xOP12-034 4xST32-001 4xOP06-033 4xOP12-023 "
            "4xST32-002 4xOP17-031 4xOP13-031 1xOP06-035 4xOP17-022 4xOP01-055 "
            "3xOP06-038 2xOP14-037 2xOP08-036 2xOP14-039"
        ),
        "cards": 50,
    },
    {
        "leader": "OP15-058",
        "kind": "x",
        "player": "Wortaxx",
        "title": "ChinoizeCup #101 2nd - Wortaxx Enel",
        "subtitle": "List from the public X photo post @Chinoize_ · 2026-08-25 · IDs verified on Limitless",
        "source_url": TWEET,
        "slug": "x-chinoize-101-wortaxx-enel",
        "date": DATE,
        "raw": (
            "1xOP15-058 4xOP12-071 4xOP15-061 4xOP15-067 4xOP15-071 3xOP12-063 "
            "2xOP09-072 2xOP10-067 4xOP15-118 4xOP15-075 4xOP15-076 4xOP15-077 "
            "4xOP15-078 3xOP15-074 1xOP13-076 3xOP05-077"
        ),
        "cards": 50,
    },
    {
        "leader": "OP14-020",
        "kind": "x",
        "player": "Dearcan",
        "title": "ChinoizeCup #101 3rd - Dearcan Mihawk",
        "subtitle": "List from the public X photo post @Chinoize_ · 2026-08-25 · IDs verified on Limitless",
        "source_url": TWEET,
        "slug": "x-chinoize-101-dearcan-mihawk",
        "date": DATE,
        "raw": (
            "1xOP14-020 4xOP07-022 4xOP12-034 4xST32-001 4xOP06-033 4xOP12-023 "
            "4xOP14-033 4xST32-002 4xST32-003 2xOP06-035 4xOP17-022 4xOP01-055 "
            "4xOP06-038 1xOP13-040 1xOP08-036 2xOP14-039"
        ),
        "cards": 50,
    },
    {
        "leader": "OP17-039",
        "kind": "x",
        "player": "Corentin33",
        "title": "ChinoizeCup #101 4th - Corentin33 Rocks",
        "subtitle": "List from the public X photo post @Chinoize_ · 2026-08-25 · IDs verified on Limitless",
        "source_url": TWEET,
        "slug": "x-chinoize-101-corentin33-rocks",
        "date": DATE,
        "raw": (
            "1xOP17-039 4xOP08-051 2xOP17-050 3xOP17-045 4xOP17-054 4xOP17-044 "
            "4xOP17-046 3xOP17-042 4xOP17-049 4xOP17-040 4xOP17-048 4xOP17-118 "
            "4xOP17-055 4xOP17-056 2xEB02-030"
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
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")

    for item in LISTS:
        counts = comm.parse_raw(item["raw"])
        lid = item["leader"]
        main_n = sum(n for cid, n in counts.items() if cid != lid)
        banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
        print(item["slug"], "cards", main_n, "leader", counts.get(lid), "banned", banned)
        if counts.get(lid) != 1 or main_n != 50 or banned:
            raise SystemExit(f"bad list {item['slug']}")

    print("=== write X lists ===")
    commsrc.write_lists(LISTS)

    print("=== consensus ===")
    ana.main()

    print("=== homepage / sitemap / guides ===")
    more.rewrite_sitemap()
    up.patch_home()
    up.patch_op17()
    seo.main()

    log_path = gen.ROOT / "data/x-search-log.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    log["hosted"] = [
        {
            "slug": item["slug"],
            "leader": item["leader"],
            "player": item["player"],
            "date": item["date"],
            "source_url": item["source_url"],
            "raw": item["raw"],
        }
        for item in LISTS
    ]
    notes = log.get("notes") or []
    notes.append(
        "Hosted 4 complete 50-card lists from @Chinoize_ 2092357744921612794 "
        "(ChinoizeCup #101 top 4 photos, 2026-08-25). Card IDs taken from the "
        "matching Limitless standings, not from screenshot OCR. "
        "@ONEPIECE_tcg_EN LATAM Santiago graphics (2092160093517160585) are "
        "also in-window list photos, but overlay OCR did not produce a trustworthy "
        "50-card ID dump so those were not hosted. Sakazuki OP05-041 photo from "
        "@sormiltcg is a complete list but that leader is not a hub."
    )
    log["notes"] = notes
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    print("x ingest done")


if __name__ == "__main__":
    main()
