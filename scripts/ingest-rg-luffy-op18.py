#!/usr/bin/env python3
"""RG Luffy lists from 2026-11-08+ plus OP18 leaders/lists.

Sources: Limitless, OPTCG.GG, OPDeckGuide, OnePieceDB, TCG Portal, Reddit.
Skips duplicates. Only writes legal 1+50 lists (Sleeptids OP18-093 may exceed 4).
Does not invent cards. Failed sources are logged and skipped.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import traceback
from datetime import date
from pathlib import Path

ROOT = Path("/workspace")
SINCE = "2026-11-08"
UNTIL = date.today().isoformat()
RG_LID = "OP13-001"
OP18_LIDS = (
    "OP18-001",
    "OP18-021",
    "OP18-022",
    "OP18-041",
    "OP18-060",
    "OP18-079",
)
STAR_PATH = ROOT / "data/starred-lists.json"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def safe_collect(label: str, fn) -> list:
    try:
        rows = list(fn() or [])
        print(label, "ok", len(rows), flush=True)
        return rows
    except Exception as exc:  # noqa: BLE001
        print(label, "FAIL", type(exc).__name__, exc, flush=True)
        traceback.print_exc()
        return []


def existing_html() -> set[str]:
    return {
        str(p.relative_to(ROOT))
        for p in (ROOT / "decklists").rglob("*.html")
        if p.name != "index.html"
    }


def color_key(meta: dict) -> str:
    raw = meta.get("color") or meta.get("colors") or ""
    if isinstance(raw, list):
        parts = [str(c).strip().lower() for c in raw if c]
    else:
        parts = [p.strip().lower() for p in re.split(r"[/,]+", str(raw)) if p.strip()]
    return "color-" + "-".join(parts) if parts else "color-red"


def add_op18_leaders(gen, cache: dict, modules: list) -> list[dict]:
    names = {
        "OP18-001": "Karoo",
        "OP18-021": "Franky",
        "OP18-022": "OP18 Luffy",
        "OP18-041": "Ms. All Sunday",
        "OP18-060": "Saint Gunko",
        "OP18-079": "Spandam",
    }
    keys = {
        "OP18-001": "karoo",
        "OP18-021": "franky-op18",
        "OP18-022": "op18-luffy",
        "OP18-041": "ms-all-sunday",
        "OP18-060": "saint-gunko",
        "OP18-079": "spandam",
    }
    extra = []
    for lid in OP18_LIDS:
        meta = cache.get(lid) or {}
        extra.append(
            {
                "id": lid,
                "key": keys[lid],
                "page": f"decklists/{keys[lid]}.html",
                "dir": f"decklists/{keys[lid]}",
                "name": names[lid],
                "color": color_key(meta),
                "crumb": ["/op18-lists.html", "OP18 lists"],
                "nav_op17": False,
                "pool_heading": "Card pictures",
                "pool_note": "English names and art from Limitless",
            }
        )
    nov = load("noveb05", str(ROOT / "scripts/ingest-nov-eb05.py"))
    nov.add_leaders(gen, extra, modules)
    return extra


def collect_optcg(gen, commsrc, optcggg, hosted: set[str]) -> list[dict]:
    seen_keys, seen_urls = optcggg.existing_index(gen)
    found: list[dict] = []
    seen: set[str] = set()
    for page in range(1, 25):
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
            event = row.get("event_name") or "OPTCG.GG event"
            if optcggg.SKIP_EVENT_RE.search(event):
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
                time.sleep(0.12)
                continue
            counts = optcggg.counts_from_deck(deck)
            lid = optcggg.leader_id(row, counts, hosted)
            if not lid or not gen.counts_are_legal(counts, lid):
                time.sleep(0.08)
                continue
            player = (row.get("player") or "Unknown").strip() or "Unknown"
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
            }
            commsrc.record(found, item, seen)
            seen_urls.add(source_url)
            time.sleep(0.08)
        print("optcg page", page, "kept", len(found), "old", page_old, flush=True)
        if page_old >= 18 and page > 2:
            break
        time.sleep(0.1)
    return found


def reddit_window(hunt, commsrc, gen, hosted: set[str]) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    try:
        rows = hunt.reddit_items(commsrc) if hasattr(hunt, "reddit_items") else []
    except Exception:
        rows = []
    for item in rows or []:
        if item.get("leader") not in hosted:
            continue
        if not in_window(item.get("date") or ""):
            continue
        counts = commsrc.parse_counts(item.get("raw") or "")
        if not gen.counts_are_legal(counts, item.get("leader")):
            continue
        commsrc.record(found, item, seen)
    return found


def main() -> None:
    fetch = load("fetchop18", str(ROOT / "scripts/fetch-op18-cards.py"))
    fetch.main()

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
    spoil = load("op18spoil", str(ROOT / "scripts/build-op18-spoilers.py"))
    lists = load("op18lists", str(ROOT / "scripts/build-op18-lists.py"))

    cache = gen.ensure_cards(set(OP18_LIDS), gen.load_card_cache())
    add_op18_leaders(gen, cache, [more, commsrc, optcggg, rh])
    hosted = {L["id"] for L in gen.LEADERS}
    target_ids = hosted

    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    portal.SINCE = SINCE
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL
    optcggg.SKIP_EVENT_RE = re.compile(r"chinoize|versus cup", re.I)

    before = existing_html()
    sources = {
        "limitless": 0,
        "optcg.gg": 0,
        "portal": 0,
        "opdb": 0,
        "opdeck": 0,
        "reddit": 0,
    }

    print("=== OPTCG.GG ===", flush=True)
    optcg_found = [
        item
        for item in safe_collect("optcg.gg", lambda: collect_optcg(gen, commsrc, optcggg, hosted))
        if gen.counts_are_legal(commsrc.parse_counts(item.get("raw") or ""), item.get("leader"))
    ]
    sources["optcg.gg"] = len(optcg_found)
    commsrc.write_lists(optcg_found)

    print("=== OPDeckGuide ===", flush=True)
    found: list[dict] = []
    seen: set[str] = set()
    for item in safe_collect("opdeck", lambda: opdeck.collect_lists(gen, commsrc) if hasattr(opdeck, "collect_lists") else []):
        if item.get("leader") not in hosted:
            continue
        if in_window(item.get("date") or "") and gen.counts_are_legal(
            commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            commsrc.record(found, item, seen)
            sources["opdeck"] += 1
    print("=== Reddit ===", flush=True)
    for item in safe_collect("reddit", lambda: reddit_window(hunt, commsrc, gen, hosted)):
        commsrc.record(found, item, seen)
        sources["reddit"] += 1
    print("=== TCG PORTAL ===", flush=True)
    for item in safe_collect("portal", lambda: portal.collect_lists(gen, commsrc)):
        if item.get("leader") not in hosted:
            continue
        if in_window(item.get("date") or "") and gen.counts_are_legal(
            commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            commsrc.record(found, item, seen)
            sources["portal"] += 1
    print("=== OnePieceDB ===", flush=True)
    for item in safe_collect("opdb", lambda: opdb.collect_lists(gen, commsrc) if hasattr(opdb, "collect_lists") else []):
        if item.get("leader") not in hosted:
            continue
        if in_window(item.get("date") or "") and gen.counts_are_legal(
            commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            commsrc.record(found, item, seen)
            sources["opdb"] += 1
    if found:
        commsrc.write_lists(found)

    print("=== Limitless Nov 8+ ===", flush=True)
    index = more.load_index()
    before_counts = {lid: len(index.get(lid) or []) for lid in target_ids}
    index = more.fetch_more(
        index,
        pages=8,
        only_ids=target_ids,
        extra_limit=400,
        per_event=200,
        since=SINCE,
        until=UNTIL,
        require_legal=True,
    )
    more.save_index(index)
    sources["limitless"] = sum(len(index.get(lid) or []) - before_counts.get(lid, 0) for lid in target_ids)
    print("limitless new", sources["limitless"], flush=True)

    after = existing_html()
    new_files = sorted(after - before)
    starred = ["/" + rel for rel in new_files]
    STAR_PATH.write_text(json.dumps(starred, indent=2) + "\n")
    print("starred", len(starred), flush=True)

    touched = {p.split("/")[1] for p in new_files if p.startswith("decklists/")}
    only_ids = {L["id"] for L in gen.LEADERS if L["key"] in touched or L["dir"].split("/")[-1] in touched}
    only_ids.add(RG_LID)
    only_ids.update(OP18_LIDS)
    print("=== rebuild hubs ===", sorted(only_ids), flush=True)
    rh.rebuild(only_ids=only_ids)
    try:
        spoil.main()
        lists.main()
        up.patch_home()
        for rel in ("index.html", "recent.html", "op18-spoilers.html", "op18-lists.html"):
            path = ROOT / rel
            if path.exists():
                path.write_text(seo.apply_theme_chrome(path.read_text()))
    except Exception as exc:  # noqa: BLE001
        print("rebuild FAIL", type(exc).__name__, exc, flush=True)
        traceback.print_exc()
    more.rewrite_sitemap()

    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "sources": sources,
        "starred": len(starred),
        "hrefs": starred,
        "op18_leaders": list(OP18_LIDS),
    }
    (ROOT / "data/rg-luffy-op18-ingest.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("ingest summary", json.dumps({k: summary[k] for k in ("window", "sources", "starred")}))
    print("rg luffy + op18 ingest done", flush=True)


if __name__ == "__main__":
    main()
