#!/usr/bin/env python3
"""Host new complete 50-card lists dated 2026-09-04 and later.

Sources: OPDeckGuide (including Utrecht / Flame Flame west lists), Limitless,
TCG PORTAL card-image recipes, Reddit, and public X posts. Only writes a page
when the source is 1 leader + 50 cards with no bans. Does not invent cards
from photos. Does not wipe existing list pages.
"""

from __future__ import annotations

import importlib.util
import json
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
SINCE = "2026-09-04"
UNTIL = "2026-09-06"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def dated(item: dict) -> bool:
    return in_window(item.get("date") or "")


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    hunt = load("hunt", "/workspace/scripts/hunt-window-lists.py")
    xmod = load("xlists", "/workspace/scripts/scrape-x-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")

    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    xmod.DATE_START = SINCE
    xmod.DATE_END = UNTIL
    portal.SINCE = SINCE
    found: list[dict] = []
    seen: set[str] = set()

    print("=== OPDeckGuide 9/4+ ===", flush=True)
    for item in hunt.opdeck_items(opdeck, commsrc):
        if dated(item):
            commsrc.record(found, item, seen)
        else:
            print("skip old opdeck", item.get("slug"), item.get("date"), flush=True)

    print("=== Reddit 9/4+ ===", flush=True)
    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    # Rebind the window used inside reddit_items via module globals.
    found.extend(reddit_window(hunt, commsrc))

    print("=== TCG PORTAL 9/4+ (card-image recipes) ===", flush=True)
    for item in portal.collect_lists(gen, commsrc):
        if dated(item):
            commsrc.record(found, item, seen)
        else:
            print("skip old portal", item.get("slug"), item.get("date"), flush=True)

    print("=== X / Flame Flame 9/4+ ===", flush=True)
    xmod.main()
    log_path = ROOT / "data/x-search-log.json"
    if log_path.exists():
        data = json.loads(log_path.read_text())
        for item in data.get("complete_lists") or []:
            raw = item.get("raw") or ""
            counts = commsrc.parse_counts(raw)
            lid = item.get("leader") or commsrc.leader_of(counts)
            if lid not in commsrc.TARGET_IDS or not commsrc.complete(counts, lid):
                continue
            day = (item.get("date") or "")[:10]
            if day and not in_window(day):
                print("skip old x", item.get("handle"), day, flush=True)
                continue
            if not day:
                continue
            handle = item.get("handle") or "x"
            url = item.get("source") or item.get("url") or f"https://x.com/{handle}"
            commsrc.record(
                found,
                {
                    "leader": lid,
                    "kind": "x",
                    "player": handle,
                    "title": f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} - @{handle}",
                    "subtitle": f"List copied from a public X/Twitter post · {day}",
                    "source_url": url if str(url).startswith("http") else f"https://x.com/{handle}",
                    "slug": commsrc.slug_for("x", handle, commsrc.TARGET_IDS[lid] + raw[-12:]),
                    "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                    "cards": sum(n for cid, n in counts.items() if cid != lid),
                    "date": day,
                },
                seen,
            )

    print("=== write community / image lists ===", flush=True)
    (ROOT / "data/sep4-community-log.json").write_text(
        json.dumps({"found": found, "window": {"start": SINCE, "end": UNTIL}}, indent=2, ensure_ascii=False)
        + "\n"
    )
    print("community complete lists", len(found), flush=True)
    commsrc.write_lists(found)

    print("=== Limitless Play since", SINCE, "===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in {L["id"] for L in gen.LEADERS}}
    index = more.fetch_more(
        index,
        pages=6,
        extra_limit=400,
        per_event=99,
        since=SINCE,
    )
    more.save_index(index)
    after = {lid: len(index.get(lid) or []) for lid in before}
    limitless_new = sum(after[lid] - before[lid] for lid in before)
    print("limitless new rows", limitless_new, flush=True)

    print("=== rebuild hubs / consensus / homepage / SEO ===", flush=True)
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
        "limitless_new_index_rows": limitless_new,
    }
    (ROOT / "data/sep4-ingest-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("ingest summary", json.dumps(summary), flush=True)
    print("sep4 ingest done", flush=True)


def reddit_window(hunt, commsrc) -> list[dict]:
    after = int(datetime(2026, 9, 4, tzinfo=timezone.utc).timestamp())
    before = int(datetime(2026, 9, 7, tzinfo=timezone.utc).timestamp())
    found: list[dict] = []
    seen: set[str] = set()
    endpoints = [
        (
            "https://arctic-shift.photon-reddit.com/api/posts/search?"
            + urllib.parse.urlencode(
                {"subreddit": "OnePieceTCG", "after": after, "before": before, "limit": 100}
            )
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            + urllib.parse.urlencode(
                {"subreddit": "OnePieceTCG", "after": after, "before": before, "limit": 200}
            )
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            + urllib.parse.urlencode(
                {
                    "q": "4xOP17 OR 1xOP17 OR decklist",
                    "subreddit": "OnePieceTCG",
                    "after": after,
                    "before": before,
                    "limit": 100,
                }
            )
        ),
        "https://www.reddit.com/r/OnePieceTCG/new.json?limit=50",
    ]
    for url in endpoints:
        status, body = hunt.fetch(url, timeout=22)
        print("reddit", status, url[:90], "chars", len(body), flush=True)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = data.get("data") or data.get("children") or []
            if isinstance(rows, dict):
                rows = rows.get("children") or []
        else:
            rows = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            post = row.get("data") if isinstance(row.get("data"), dict) else row
            created = post.get("created_utc") or post.get("created") or 0
            try:
                day = datetime.fromtimestamp(float(created), tz=timezone.utc).strftime("%Y-%m-%d")
            except (OSError, ValueError, TypeError, OverflowError):
                day = ""
            if day and not in_window(day):
                continue
            text = "\n".join(str(post.get(k) or "") for k in ("title", "selftext", "body", "permalink", "url"))
            permalink = post.get("permalink") or post.get("id") or url
            counts = commsrc.parse_counts(text)
            lid = commsrc.leader_of(counts)
            if not lid or not commsrc.complete(counts, lid):
                continue
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            item = {
                "leader": lid,
                "kind": "web",
                "player": "Reddit",
                "title": f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} Reddit list",
                "subtitle": f"Public r/OnePieceTCG list · {day or 'date unknown'}",
                "source_url": (
                    permalink if str(permalink).startswith("http") else "https://www.reddit.com" + str(permalink)
                ),
                "slug": commsrc.slug_for("reddit", "onepiecetcg", str(permalink))[:70],
                "raw": raw,
                "cards": sum(n for cid, n in counts.items() if cid != lid),
            }
            if day:
                item["date"] = day
                commsrc.record(found, item, seen)
        time.sleep(0.15)
    return found


if __name__ == "__main__":
    main()
