#!/usr/bin/env python3
"""Host complete 50-card lists from public OPTCG.GG tournament pages.

Skips ChinoizeCup rows (those already come from Limitless). Only writes a page
when the public JSON is 1 hosted leader + 50 cards with no bans. Does not invent
cards. Does not wipe existing pages.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path("/workspace")
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com; public OPTCG list scrape)"
API = "https://www.optcg.gg/api/deck-lists"
SITE = "https://www.optcg.gg/deck-lists"
SKIP_EVENT_RE = re.compile(r"chinoize|versus cup", re.I)
LEADER_RE = re.compile(r"\[((?:OP|ST|EB|PRB)\d{2}-\d{3})\]")
CARD_RE = re.compile(r"^((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})$")
SINCE = "2026-08-01"
UNTIL = "2026-09-11"
MAX_PAGES = 70
PAGE_SIZE = 20
PER_EVENT = 40
TARGET = 220
DETAIL_CAP = 520


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def card_id(row: dict) -> str | None:
    raw = (row.get("base_id") or row.get("id") or "").upper()
    raw = raw.split("_")[0]
    if CARD_RE.match(raw):
        return raw
    return None


def counts_from_deck(deck: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in deck.get("cards") or []:
        cid = card_id(row)
        if not cid:
            continue
        counts[cid] = counts.get(cid, 0) + 1
    return counts


def leader_id(row: dict, counts: dict[str, int], hosted: set[str]) -> str | None:
    m = LEADER_RE.search(row.get("leader") or "")
    if m and m.group(1) in hosted and counts.get(m.group(1)) == 1:
        return m.group(1)
    hits = [cid for cid in counts if cid in hosted]
    if len(hits) == 1 and counts[hits[0]] == 1:
        return hits[0]
    return None


def existing_index(gen) -> tuple[set[tuple[str, str, str]], set[str]]:
    """Skip already hosted OPTCG.GG pages, including 1th vs 1st slug mismatches."""
    keys: set[tuple[str, str, str]] = set()
    urls: set[str] = set()
    for name in ("data/tournament-decks.json", "data/community-decks.json"):
        path = ROOT / name
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for lid, rows in data.items():
            for row in rows or []:
                src = (row.get("source_url") or "").rstrip("/")
                if src:
                    urls.add(src)
                player = gen.slugify(row.get("player") or "")
                day = (row.get("date") or "")[:10]
                if player and day:
                    keys.add((lid, player, day))
    return keys, urls


def collect_lists(gen, commsrc) -> list[dict]:
    hosted = {L["id"] for L in gen.LEADERS}
    seen_keys, seen_urls = existing_index(gen)
    found: list[dict] = []
    seen: set[str] = set()
    per_event: dict[str, int] = {}
    fetched = 0
    print("=== OPTCG.GG since", SINCE, "skip ChinoizeCup ===", flush=True)
    for page in range(1, MAX_PAGES + 1):
        if len(found) >= TARGET or fetched >= DETAIL_CAP:
            break
        data = get_json(f"{API}/paginated?page={page}&page_size={PAGE_SIZE}")
        batch = data.get("decklists") or []
        print("optcg.gg page", page, "batch", len(batch), "kept", len(found), flush=True)
        if not batch:
            break
        stop = False
        for row in batch:
            day = (row.get("event_date") or "")[:10]
            if day and day < SINCE:
                stop = True
                continue
            if not in_window(day):
                continue
            event = row.get("event_name") or "OPTCG.GG event"
            if SKIP_EVENT_RE.search(event):
                continue
            if per_event.get(event, 0) >= PER_EVENT:
                continue
            did = row.get("id") or ""
            if not did:
                continue
            source_url = f"{SITE}/{did}".rstrip("/")
            if source_url in seen_urls:
                continue
            if fetched >= DETAIL_CAP or len(found) >= TARGET:
                break
            fetched += 1
            try:
                deck = get_json(f"{API}/{did}")
            except Exception as exc:  # noqa: BLE001
                print("fail", did, exc, flush=True)
                time.sleep(0.15)
                continue
            counts = counts_from_deck(deck)
            lid = leader_id(row, counts, hosted)
            main_n = sum(n for cid, n in counts.items() if cid != lid) if lid else 0
            banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
            player = (row.get("player") or "Unknown").strip() or "Unknown"
            print(
                event,
                player,
                lid or "-",
                "cards",
                main_n,
                "banned",
                banned,
                flush=True,
            )
            if not lid or counts.get(lid) != 1 or main_n != 50 or banned:
                time.sleep(0.12)
                continue
            key = (lid, gen.slugify(player), day)
            if key in seen_keys or source_url in seen_urls:
                print("skip dup", player, lid, day, flush=True)
                time.sleep(0.12)
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
                "cards": main_n,
                "date": day,
            }
            before = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before:
                seen_keys.add(key)
                seen_urls.add(source_url)
                per_event[event] = per_event.get(event, 0) + 1
            time.sleep(0.12)
        if stop and page > 2:
            break
        time.sleep(0.1)
    log_path = ROOT / "data/optcggg-log.json"
    log_path.write_text(json.dumps({"hosted": found}, indent=2, ensure_ascii=False) + "\n")
    print("optcg.gg ready", len(found), "log", log_path, flush=True)
    return found


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    found = collect_lists(gen, commsrc)
    commsrc.write_lists(found)
    print("optcg.gg ingest done", flush=True)


if __name__ == "__main__":
    main()
