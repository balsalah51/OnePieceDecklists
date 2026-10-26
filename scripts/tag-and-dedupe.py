#!/usr/bin/env python3
"""Tag every hosted list and collapse the same player, event, and card list.

Keeps one row for the stats. The other pages stay up and point at it, and
every copy lists each source that published that list.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import source_meta

ROOT = Path("/workspace")
CARD_RE = re.compile(
    r'<span class="qty">(\d+)x</span>\s*<span class="card-title">.*?</span>\s*'
    r'<span class="muted card-id">([A-Z0-9]+-\d+)</span>',
    re.S,
)
H2_RE = re.compile(r"<h2>(.*?)</h2>", re.S)
SUB_RE = re.compile(r"<h2>.*?</h2>\s*<p>(.*?)</p>", re.S)
P_RE = re.compile(r'(<p class="muted" style="margin-top:22px">)(.*?)(</p>)', re.S)
SOURCE_LINK_RE = re.compile(r"\s*Source:\s*<a href=\"[^\"]*\">[^<]*</a>\.?", re.S)
SPAN_RE = re.compile(r'<span class="list-sources">.*?</span>', re.S)
STOP = {
    "the", "a", "an", "of", "and", "cup", "one", "piece", "tcg", "op",
    "tournament", "list", "deck", "decklist", "by", "place", "public",
}


def load_map(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def norm_player(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\b\d+(?:st|nd|rd|th)\b", " ", text, flags=re.I)
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def event_tokens(value: str) -> set[str]:
    words = re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).split()
    return {word for word in words if word not in STOP and len(word) > 2 and not word.isdigit()}


def dates_close(a: str, b: str) -> bool:
    if not a or not b:
        return True
    try:
        return abs((date.fromisoformat(a) - date.fromisoformat(b)).days) <= 2
    except ValueError:
        return False


def squash_event(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def events_match(a: str, b: str) -> bool:
    """Same event title, or one title contains the other without dropping a number."""
    left, right = squash_event(a), squash_event(b)
    if not left or not right or len(left) < 8 or len(right) < 8:
        return False
    if left == right:
        return True
    shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
    if len(shorter) < 12 or shorter not in longer:
        return False
    extra = longer.replace(shorter, " ", 1)
    extra = re.sub(r"\b(?:op|eb|st|prb)\d+\b", " ", extra)
    extra = re.sub(r"\b20\d{2}\b", " ", extra)
    if re.search(r"\d", extra):
        return False
    return True


def parse_page(text: str) -> dict:
    cards = tuple(sorted((cid, int(qty)) for qty, cid in CARD_RE.findall(text)))
    h2 = html.unescape(H2_RE.search(text).group(1)).strip() if H2_RE.search(text) else ""
    sub = html.unescape(SUB_RE.search(text).group(1)).strip() if SUB_RE.search(text) else ""
    sub = re.sub(r"<[^>]+>", "", sub)
    return {"cards": cards, "h2": h2, "subtitle_text": sub}


def player_and_event(row: dict, page: dict) -> tuple[str, str]:
    player = (row.get("player") or "").strip()
    event = (row.get("tournament") or row.get("tournament_name") or row.get("event") or "").strip()
    h2 = page.get("h2") or ""
    sub = page.get("subtitle_text") or ""
    if not player and " - " in h2:
        left, right = h2.split(" - ", 1)
        if right and (right.lower() in sub.lower() or not event):
            player = left.strip()
            if not event:
                event = right.strip()
    if not event:
        parts = [part.strip() for part in sub.split("·")]
        dated = [part for part in parts if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", part)]
        if len(dated) >= 2:
            event = dated[-1]
        elif dated:
            event = dated[0]
    if not event:
        event = (row.get("title") or h2 or "").strip()
    return player, event


def keep_key(row: dict) -> tuple:
    host = row.get("source_host") or ""
    placing = row.get("placing")
    has_place = 0 if isinstance(placing, int) or (isinstance(placing, str) and placing.isdigit()) else 1
    return (
        0 if host == "play.limitlesstcg.com" else 1,
        has_place,
        0 if row.get("date") else 1,
        row.get("href") or "",
    )


def cluster(rows: list[dict]) -> None:
    buckets: dict[tuple, list[dict]] = {}
    for row in rows:
        player = norm_player(row.get("_player") or "")
        cards = row.get("_cards") or ()
        copies = sum(n for _cid, n in cards)
        if not player or copies < 40:
            continue
        buckets.setdefault((player, cards), []).append(row)
    for group in buckets.values():
        if len(group) < 2:
            continue
        parent = list(range(len(group)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if not dates_close((group[i].get("date") or "")[:10], (group[j].get("date") or "")[:10]):
                    continue
                if not events_match(group[i].get("_event") or "", group[j].get("_event") or ""):
                    continue
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri
        groups: dict[int, list[dict]] = {}
        for i, row in enumerate(group):
            groups.setdefault(find(i), []).append(row)
        for members in groups.values():
            if len(members) < 2:
                continue
            keeper = min(members, key=keep_key)
            sources = []
            seen = set()
            for member in members:
                for src in member.get("sources") or []:
                    key = ((src.get("name") or ""), (src.get("url") or "").rstrip("/"))
                    if key in seen:
                        continue
                    seen.add(key)
                    sources.append({"name": src.get("name") or "", "url": src.get("url") or ""})
            keeper["sources"] = sources
            keeper.pop("duplicate_of", None)
            eras = [member.get("format_era") or "" for member in members]
            labeled = next((era for era in eras if era and era != "unlabeled"), "")
            if labeled:
                keeper["format_era"] = labeled
            for member in members:
                if member is keeper:
                    continue
                member["sources"] = sources
                member["region"] = keeper.get("region") or member.get("region")
                member["format_era"] = keeper.get("format_era") or member.get("format_era")
                member["duplicate_of"] = keeper.get("href") or ""


def patch_html(path: Path, row: dict) -> bool:
    if not path.exists():
        return False
    text = path.read_text()
    attr = source_meta.attribution_html(row)
    match = P_RE.search(text)
    if not match:
        return False
    body = match.group(2)
    if SPAN_RE.search(body):
        body = SPAN_RE.sub(attr, body, count=1)
    else:
        body = SOURCE_LINK_RE.sub(" " + attr + " ", body, count=1)
        if "list-sources" not in body:
            body = body.rstrip() + " " + attr
    new = text[: match.start()] + match.group(1) + body + match.group(3) + text[match.end() :]
    if new != text:
        path.write_text(new)
    return True


def unresolved_cards(rows: list[dict], cache: dict) -> list[str]:
    missing = set()
    for row in rows:
        for cid, _n in row.get("_cards") or ():
            card = cache.get(cid)
            if not card or not (card.get("name") or "").strip():
                missing.add(cid)
    return sorted(missing)


def main(write: bool = True) -> dict:
    tournament = load_map(ROOT / "data/tournament-decks.json")
    community = load_map(ROOT / "data/community-decks.json")
    cache_path = ROOT / "data/card-cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    flat: list[dict] = []
    for lid, rows in tournament.items():
        for row in rows or []:
            row["_bucket"] = "tournament"
            row["_leader"] = lid
            flat.append(row)
    for lid, rows in community.items():
        for row in rows or []:
            row["_bucket"] = "community"
            row["_leader"] = lid
            flat.append(row)

    unreadable = 0
    for row in flat:
        href = row.get("href") or ""
        path = ROOT / href.lstrip("/")
        page = {"cards": (), "h2": "", "subtitle_text": ""}
        if path.exists():
            try:
                page = parse_page(path.read_text())
            except OSError:
                unreadable += 1
        else:
            unreadable += 1
        player, event = player_and_event(row, page)
        if player and not row.get("player"):
            row["player"] = player
        if event and row.get("_bucket") == "community":
            row["event"] = event
        row["_player"] = player
        row["_event"] = event
        row["_cards"] = page["cards"]
        source_meta.apply_tags(row)

    for row in flat:
        row.pop("duplicate_of", None)
    cluster(flat)
    dupes = sum(1 for row in flat if row.get("duplicate_of"))
    missing = unresolved_cards(flat, cache)
    counted = [row for row in flat if not row.get("duplicate_of")]

    if write:
        patched = 0
        missed = 0
        for row in flat:
            href = row.get("href") or ""
            path = ROOT / href.lstrip("/")
            if patch_html(path, row):
                patched += 1
            elif path.exists():
                missed += 1
        for rows in list(tournament.values()) + list(community.values()):
            for row in rows or []:
                row.pop("_bucket", None)
                row.pop("_leader", None)
                row.pop("_player", None)
                row.pop("_event", None)
                row.pop("_cards", None)
        (ROOT / "data/tournament-decks.json").write_text(
            json.dumps(tournament, indent=2, ensure_ascii=False) + "\n"
        )
        (ROOT / "data/community-decks.json").write_text(
            json.dumps(community, indent=2, ensure_ascii=False) + "\n"
        )
        (ROOT / "data/unresolved-cards.json").write_text(
            json.dumps({"cards": missing, "count": len(missing)}, indent=2) + "\n"
        )
        inventory = {
            "rows": len(flat),
            "duplicates": dupes,
            "unique": len(flat) - dupes,
            "counts": source_meta.count_rows(counted),
            "unresolved_cards": missing,
        }
        (ROOT / "data/source-inventory.json").write_text(
            json.dumps(inventory, indent=2, ensure_ascii=False) + "\n"
        )
    else:
        patched = 0
        missed = 0

    summary = {
        "rows": len(flat),
        "unique": len(flat) - dupes,
        "duplicates": dupes,
        "patched": patched,
        "attribution_misses": missed,
        "unreadable": unreadable,
        "unresolved": missing,
        "counts": source_meta.count_rows(counted),
    }
    print(json.dumps({k: summary[k] for k in ("rows", "duplicates", "patched", "attribution_misses", "unreadable")}, indent=2))
    print("by source", summary["counts"]["by_source"])
    print("by region", summary["counts"]["by_region"])
    shown = 0
    for row in flat:
        if not row.get("duplicate_of"):
            continue
        print(
            "DUP",
            row.get("source"),
            row.get("_player") or row.get("player"),
            "|",
            (row.get("_event") or "")[:70],
            "->",
            row.get("duplicate_of"),
        )
        shown += 1
        if shown >= 40:
            break
    return summary


if __name__ == "__main__":
    import sys

    main(write="--dry-run" not in sys.argv)
