#!/usr/bin/env python3
"""Host RG Luffy (OP13-001) lists dated 2026-11-08 or newer.

Sources: Limitless, OPTCG.GG, OPDeckGuide, OnePieceDB, TCG Portal, Reddit.
Skips duplicates. Only writes legal 1+50 / max 4 lists. Does not invent cards.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import traceback
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
SINCE = "2026-11-08"
UNTIL = date.today().isoformat()
LID = "OP13-001"
STAR_PATH = ROOT / "data/starred-lists.json"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def legal_counts(gen, counts: dict[str, int], lid: str | None) -> bool:
    if not lid or counts.get(lid) != 1:
        return False
    if any(cid in gen.BANNED_CARDS for cid in counts):
        return False
    main = 0
    for cid, n in counts.items():
        if cid == lid:
            continue
        if n < 1 or n > 4:
            return False
        main += n
    return main == 50


def safe_collect(label: str, fn) -> list:
    try:
        rows = list(fn() or [])
        print(label, "ok", len(rows), flush=True)
        return rows
    except Exception as exc:  # noqa: BLE001
        print(label, "FAIL", type(exc).__name__, exc, flush=True)
        traceback.print_exc()
        return []


def existing_stems() -> set[str]:
    d = ROOT / "decklists/rg-luffy"
    if not d.exists():
        return set()
    return {p.stem for p in d.glob("*.html")}


def collect_optcg(gen, commsrc, optcggg) -> list[dict]:
    hosted = {LID}
    seen_keys, seen_urls = optcggg.existing_index(gen)
    found: list[dict] = []
    seen: set[str] = set()
    for page in range(1, 20):
        data = optcggg.get_json(f"{optcggg.API}/paginated?page={page}&page_size=20")
        batch = data.get("decklists") or []
        if not batch:
            break
        page_old = 0
        for row in batch:
            day = (row.get("event_date") or "")[:10]
            if day and day < SINCE:
                page_old += 1
                continue
            if not in_window(day):
                continue
            did = row.get("id") or ""
            if not did:
                continue
            source_url = f"{optcggg.SITE}/{did}".rstrip("/")
            if source_url in seen_urls:
                continue
            try:
                deck = optcggg.get_json(f"{optcggg.API}/{did}")
            except Exception as exc:  # noqa: BLE001
                print("optcg fail", did, exc, flush=True)
                time.sleep(0.1)
                continue
            counts = optcggg.counts_from_deck(deck)
            lid = optcggg.leader_id(row, counts, hosted)
            if lid != LID or not legal_counts(gen, counts, lid):
                time.sleep(0.08)
                continue
            player = (row.get("player") or "Unknown").strip() or "Unknown"
            event = row.get("event_name") or "OPTCG.GG event"
            key = (lid, gen.slugify(player), day)
            if key in seen_keys:
                time.sleep(0.08)
                continue
            place = row.get("placement")
            place_bit = gen.ordinal(place) if isinstance(place, int) and place else "list"
            item = {
                "leader": lid,
                "kind": "web",
                "player": player,
                "title": f"{player} - {event}",
                "subtitle": f"Public OPTCG.GG list · {event} · {day}",
                "source_url": source_url,
                "slug": gen.slugify(f"optcggg-{place_bit}-{player}-{event}")[:70],
                "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                "cards": 50,
                "date": day,
                "placing": place if isinstance(place, int) else None,
            }
            before = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before:
                seen_keys.add(key)
                seen_urls.add(source_url)
            time.sleep(0.1)
        print("optcg page", page, "rg kept", len(found), "old", page_old, flush=True)
        if page_old:
            break
        time.sleep(0.08)
    return found


def reddit_window(hunt, commsrc, gen) -> list[dict]:
    after = int(datetime(2026, 11, 8, tzinfo=timezone.utc).timestamp())
    before = int(datetime(2026, 11, 13, tzinfo=timezone.utc).timestamp())
    found: list[dict] = []
    seen: set[str] = set()
    urls = [
        (
            "https://arctic-shift.photon-reddit.com/api/posts/search?"
            f"subreddit=OnePieceTCG&after={after}&before={before}&limit=100"
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            f"subreddit=OnePieceTCG&after={after}&before={before}&limit=200"
        ),
        "https://www.reddit.com/r/OnePieceTCG/new.json?limit=50",
    ]
    blobs: list[tuple[str, str, str]] = []
    for url in urls:
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
            text = "\n".join(str(post.get(k) or "") for k in ("title", "selftext", "body", "permalink", "url"))
            permalink = post.get("permalink") or post.get("id") or url
            blobs.append((str(permalink), day, text))
        time.sleep(0.12)
    for permalink, day, text in blobs:
        if day and not in_window(day):
            continue
        counts = commsrc.parse_counts(text)
        lid = commsrc.leader_of(counts)
        if lid != LID or not legal_counts(gen, counts, lid):
            continue
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        item = {
            "leader": lid,
            "kind": "web",
            "player": "Reddit",
            "title": "RG Luffy Reddit list",
            "subtitle": f"Public r/OnePieceTCG list · {day or 'date unknown'}",
            "source_url": permalink if str(permalink).startswith("http") else "https://www.reddit.com" + str(permalink),
            "slug": commsrc.slug_for("reddit", "onepiecetcg", permalink)[:70],
            "raw": raw,
            "cards": 50,
            "date": day,
        }
        commsrc.record(found, item, seen)
    return found


def main() -> None:
    gen = load("genlists", str(ROOT / "scripts/generate-tournament-lists.py"))
    more = load("morelists", str(ROOT / "scripts/add-more-tournament-lists.py"))
    commsrc = load("commsrc", str(ROOT / "scripts/scrape-community-sources.py"))
    optcggg = load("optcggg", str(ROOT / "scripts/add-optcggg-lists.py"))
    portal = load("portal", str(ROOT / "scripts/add-tcgportal-lists.py"))
    opdb = load("opdb", str(ROOT / "scripts/add-onepiecedb-lists.py"))
    opdeck = load("opdeck", str(ROOT / "scripts/add-opdeckguide-lists.py"))
    hunt = load("hunt", str(ROOT / "scripts/hunt-window-lists.py"))
    rh = load("rebuildhubs", str(ROOT / "scripts/rebuild-leader-hubs.py"))
    up = load("upgrade", str(ROOT / "scripts/upgrade-public-pages.py"))
    seo = load("seocommon", str(ROOT / "scripts/seo_common.py"))

    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    portal.SINCE = SINCE
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL
    optcggg.SKIP_EVENT_RE = re.compile(r"chinoize|versus cup", re.I)

    before = existing_stems()
    sources = {"limitless": 0, "optcg.gg": 0, "portal": 0, "opdb": 0, "opdeck": 0, "reddit": 0}
    found: list[dict] = []
    seen: set[str] = set()

    print("=== OPTCG.GG RG Luffy", SINCE, "===", flush=True)
    for item in safe_collect("optcg.gg", lambda: collect_optcg(gen, commsrc, optcggg)):
        before_n = len(found)
        commsrc.record(found, item, seen)
        if len(found) > before_n:
            sources["optcg.gg"] += 1

    print("=== OPDeckGuide ===", flush=True)
    for item in safe_collect("opdeck", lambda: hunt.opdeck_items(opdeck, commsrc)):
        if item.get("leader") != LID:
            continue
        if in_window(item.get("date") or "") and legal_counts(
            gen, commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            before_n = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before_n:
                sources["opdeck"] += 1

    print("=== Reddit ===", flush=True)
    for item in safe_collect("reddit", lambda: reddit_window(hunt, commsrc, gen)):
        before_n = len(found)
        commsrc.record(found, item, seen)
        if len(found) > before_n:
            sources["reddit"] += 1

    print("=== TCG PORTAL ===", flush=True)
    for item in safe_collect("portal", lambda: portal.collect_lists(gen, commsrc)):
        if item.get("leader") != LID:
            continue
        if in_window(item.get("date") or "") and legal_counts(
            gen, commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            before_n = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before_n:
                sources["portal"] += 1

    print("=== OnePieceDB RG Luffy ===", flush=True)
    def opdb_rg():
        hosted = {LID}
        slug = commsrc.OPDL_SLUGS.get(LID)
        pages = [
            f"https://onepiecedb.io/category/leader/{slug}" if slug else "",
        ]
        urls: list[str] = []
        for page in pages:
            if not page:
                continue
            try:
                body = opdb.fetch(page)
            except Exception as exc:  # noqa: BLE001
                print("opdb list fail", page, exc, flush=True)
                continue
            for href in opdb.DECK_HREF_RE.findall(body):
                if href not in urls:
                    urls.append(href)
            time.sleep(0.12)
        known = opdb.existing_urls()
        out: list[dict] = []
        seen_raw: set[str] = set()
        for url in urls:
            if url in known:
                continue
            try:
                item = opdb.parse_page(url, hosted, gen, commsrc)
            except Exception as exc:  # noqa: BLE001
                print("opdb fail", url, exc, flush=True)
                time.sleep(0.12)
                continue
            time.sleep(0.12)
            if not item or item.get("leader") != LID:
                continue
            day = item.get("date") or ""
            if day and not in_window(day):
                continue
            if not legal_counts(gen, commsrc.parse_counts(item.get("raw") or ""), LID):
                continue
            commsrc.record(out, item, seen_raw)
        return out

    for item in safe_collect("opdb", opdb_rg):
        before_n = len(found)
        commsrc.record(found, item, seen)
        if len(found) > before_n:
            sources["opdb"] += 1

    legal_found = [
        item
        for item in found
        if item.get("leader") == LID
        and legal_counts(gen, commsrc.parse_counts(item.get("raw") or ""), LID)
    ]
    print("=== write community RG Luffy ===", len(legal_found), flush=True)
    commsrc.write_lists(legal_found)

    print("=== Limitless RG Luffy ===", flush=True)
    index = more.load_index()
    before_n = len(index.get(LID) or [])
    index = more.fetch_more(
        index,
        pages=6,
        only_ids={LID},
        extra_limit=400,
        per_event=200,
        since=SINCE,
        until=UNTIL,
        require_legal=True,
    )
    more.save_index(index)
    sources["limitless"] = len(index.get(LID) or []) - before_n
    print("limitless new", sources["limitless"], flush=True)

    after = existing_stems()
    new_stems = sorted(after - before)
    starred = [f"/decklists/rg-luffy/{stem}.html" for stem in new_stems]
    STAR_PATH.write_text(json.dumps(starred, indent=2) + "\n")
    print("starred", len(starred), flush=True)

    print("=== rebuild RG Luffy hub ===", flush=True)
    rh.rebuild(only_ids={LID})
    try:
        up.patch_home()
        for rel in ("index.html", "recent.html"):
            path = ROOT / rel
            path.write_text(seo.apply_theme_chrome(path.read_text()))
    except Exception as exc:  # noqa: BLE001
        print("home patch FAIL", type(exc).__name__, exc, flush=True)
        traceback.print_exc()
    more.rewrite_sitemap()

    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "sources": sources,
        "community_legal": len(legal_found),
        "starred": len(starred),
        "hrefs": starred,
    }
    (ROOT / "data/rg-luffy-nov8-ingest.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("ingest summary", json.dumps({k: summary[k] for k in ("window", "sources", "community_legal", "starred")}))
    print("rg luffy nov8 ingest done", flush=True)


if __name__ == "__main__":
    main()
