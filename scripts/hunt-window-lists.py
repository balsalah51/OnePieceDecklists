#!/usr/bin/env python3
"""Collect 8/27+ complete lists from OPDeckGuide, Reddit, and extra public pages.

Does not invent cards. Does not wipe existing pages. Writes only complete 50-card lists.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com; public OPTCG list scrape)"
SINCE = "2026-08-27"
UNTIL = "2026-09-03"
LINE_RE = re.compile(r"(?i)(\d+)\s*[x×]\s*((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})")


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch(url: str, timeout: int = 18) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, body
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def reddit_items(commsrc) -> list[dict]:
    after = int(datetime(2026, 8, 27, tzinfo=timezone.utc).timestamp())
    before = int(datetime(2026, 9, 3, tzinfo=timezone.utc).timestamp())
    found: list[dict] = []
    seen: set[str] = set()
    endpoints = [
        (
            "https://arctic-shift.photon-reddit.com/api/posts/search?"
            + urllib.parse.urlencode(
                {
                    "subreddit": "OnePieceTCG",
                    "after": after,
                    "before": before,
                    "limit": 100,
                }
            )
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            + urllib.parse.urlencode(
                {
                    "subreddit": "OnePieceTCG",
                    "after": after,
                    "before": before,
                    "limit": 200,
                }
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
        "https://old.reddit.com/r/OnePieceTCG/new/.rss",
    ]
    blobs: list[tuple[str, str, str]] = []
    for url in endpoints:
        status, body = fetch(url, timeout=22)
        print("reddit", status, url[:90], "chars", len(body), flush=True)
        day = ""
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
        if rows:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                post = row.get("data") if isinstance(row.get("data"), dict) else row
                created = post.get("created_utc") or post.get("created") or 0
                try:
                    day = datetime.fromtimestamp(float(created), tz=timezone.utc).strftime("%Y-%m-%d")
                except (OSError, ValueError, TypeError, OverflowError):
                    day = ""
                text = "\n".join(
                    str(post.get(k) or "")
                    for k in ("title", "selftext", "body", "permalink", "url")
                )
                permalink = post.get("permalink") or post.get("id") or url
                blobs.append((str(permalink), day, text))
        else:
            blobs.append((url, "", body))
        time.sleep(0.15)
    for permalink, day, text in blobs:
        if day and not in_window(day):
            continue
        counts = commsrc.parse_counts(text)
        lid = commsrc.leader_of(counts)
        if not lid or not commsrc.complete(counts, lid):
            continue
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        slug_src = permalink if isinstance(permalink, str) else "reddit"
        item = {
            "leader": lid,
            "kind": "web",
            "player": "Reddit",
            "title": f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} Reddit list",
            "subtitle": f"Public r/OnePieceTCG list · {day or 'date unknown'}",
            "source_url": (
                permalink
                if str(permalink).startswith("http")
                else "https://www.reddit.com" + str(permalink)
            ),
            "slug": commsrc.slug_for("reddit", "onepiecetcg", slug_src)[:70],
            "raw": raw,
            "cards": sum(n for cid, n in counts.items() if cid != lid),
        }
        if day:
            item["date"] = day
        commsrc.record(found, item, seen)
    return found


def opdeck_items(opdeck, commsrc) -> list[dict]:
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    paths = opdeck.collect_paths()
    print("opdeck paths", len(paths), flush=True)
    found: list[dict] = []
    seen: set[str] = set()
    for path in paths:
        item = opdeck.parse_page(path, comm, gen)
        time.sleep(0.1)
        if not item:
            continue
        day = (item.get("date") or "")[:10]
        if day and not in_window(day):
            print("skip old opdeck", path, day, flush=True)
            continue
        commsrc.record(found, item, seen)
    return found


def main() -> None:
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    found: list[dict] = []
    print("=== OPDeckGuide 8/27+ ===", flush=True)
    found.extend(opdeck_items(opdeck, commsrc))
    print("=== Reddit 8/27+ ===", flush=True)
    found.extend(reddit_items(commsrc))
    Path("/workspace/data/window-hunt-log.json").write_text(
        json.dumps({"found": found}, indent=2, ensure_ascii=False) + "\n"
    )
    print("window hunt complete lists", len(found), flush=True)
    commsrc.write_lists(found)
    print("window hunt done", flush=True)


if __name__ == "__main__":
    main()
