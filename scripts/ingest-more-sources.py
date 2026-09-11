#!/usr/bin/env python3
"""Host complete lists from many public sources that are not Limitless.

OnePieceDB, OPDeckGuide (OP16 and OP17), OPTCG.GG (skips ChinoizeCup),
TCG PORTAL shop battles, and public r/OnePieceTCG text dumps.
Only writes a page when the source is 1 leader + 50 cards with no bans.
Does not invent cards from photos. Does not wipe existing list pages.
"""

from __future__ import annotations

import importlib.util
import json
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path("/workspace")
SINCE = "2026-08-01"
UNTIL = date.today().isoformat()


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def reddit_window(hunt, commsrc) -> list[dict]:
    start = datetime.fromisoformat(SINCE).replace(tzinfo=timezone.utc)
    end = datetime.combine(date.today() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    after = int(start.timestamp())
    before = int(end.timestamp())
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
            main_n = sum(n for cid, n in counts.items() if cid != lid)
            if main_n != 50:
                continue
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            item = {
                "leader": lid,
                "kind": "reddit",
                "player": "Reddit",
                "title": f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} Reddit list",
                "subtitle": f"Public r/OnePieceTCG list · {day or 'date unknown'}",
                "source_url": (
                    permalink if str(permalink).startswith("http") else "https://www.reddit.com" + str(permalink)
                ),
                "slug": commsrc.slug_for("reddit", "onepiecetcg", str(permalink))[:70],
                "raw": raw,
                "cards": main_n,
            }
            if day:
                item["date"] = day
                commsrc.record(found, item, seen)
        time.sleep(0.15)
    return found


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
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

    print("=== OnePieceDB ===", flush=True)
    for item in opdb.collect_lists(gen, commsrc):
        commsrc.record(found, item, seen)

    print("=== OPDeckGuide OP16+OP17 ===", flush=True)
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    for path in opdeck.collect_paths():
        item = opdeck.parse_page(path, comm, gen)
        time.sleep(0.1)
        if item:
            commsrc.record(found, item, seen)

    print("=== TCG PORTAL ===", flush=True)
    for item in portal.collect_lists(gen, commsrc):
        commsrc.record(found, item, seen)

    print("=== OPTCG.GG (not ChinoizeCup) ===", flush=True)
    for item in optcggg.collect_lists(gen, commsrc):
        commsrc.record(found, item, seen)

    print("=== Reddit ===", flush=True)
    for item in reddit_window(hunt, commsrc):
        commsrc.record(found, item, seen)

    log_path = ROOT / "data/more-sources-log.json"
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
    (ROOT / "data/more-sources-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("more-sources ingest done", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
