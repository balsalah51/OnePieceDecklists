#!/usr/bin/env python3
"""One window and one set of leader counts for the homepage and the tier list.

Recent lists are a rolling window ending on the newest hosted list date.
OPDL_RECENT_DAYS overrides the length (default 45). The homepage share chart,
the Leaders row, the weekly meta note, and the tier list's "recent" columns
all read this module. Tier letters still come from build-tier-list.aggregate;
this file does not change those thresholds.
"""

from __future__ import annotations

import importlib.util
import os
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path("/workspace")
RECENT_DAYS = int(os.environ.get("OPDL_RECENT_DAYS", "45"))
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")

# Different printed leaders that share a character name. Do not merge them.
TWINS: dict[str, dict] = {
    "OP09-062": {
        "label": "OP09 Nico Robin",
        "also": "EB05-010",
        "note": "Purple/yellow OP09-062 Nico Robin. Not green/yellow EB05-010.",
    },
    "EB05-010": {
        "label": "EB05 Nico Robin",
        "also": "OP09-062",
        "note": "Green/yellow EB05-010 Nico Robin. Not purple/yellow OP09-062.",
    },
    "OP15-058": {
        "label": "OP15 Enel",
        "also": "OP05-098",
        "note": "Purple OP15-058 Enel. Not yellow OP05-098 Enel.",
    },
    "OP05-098": {
        "label": "OP05 Enel",
        "also": "OP15-058",
        "note": "Yellow OP05-098 Enel. Not purple OP15-058 Enel.",
    },
    "OP17-020": {
        "label": "OP17 Shanks",
        "also": "OP09-001",
        "note": "Green OP17-020 Shanks. Not red OP09-001 Shanks.",
    },
    "OP09-001": {
        "label": "OP09 Shanks",
        "also": "OP17-020",
        "note": "Red OP09-001 Shanks. Not green OP17-020 Shanks.",
    },
}

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gen = _load("genlists_fm", ROOT / "scripts/generate-tournament-lists.py")
_event = _load("eventdisplay_fm", ROOT / "scripts/event_display.py")


def public_name(leader: dict) -> str:
    twin = TWINS.get(leader.get("id") or "")
    if twin:
        return twin["label"]
    return leader.get("name") or ""


def pretty_date(raw: str) -> str:
    match = DATE_RE.match(raw or "")
    if not match:
        return raw or ""
    year, month, day = match.group(1).split("-")
    return f"{int(day)} {MONTHS[int(month) - 1]} {year}"


def iso_date(raw: str) -> str:
    match = DATE_RE.match(raw or "")
    return match.group(1) if match else ""


def window_bounds(rows: list[dict], *, days: int | None = None) -> dict:
    """Rolling window ending on the newest real list date in rows."""
    days = RECENT_DAYS if days is None else int(days)
    dated = [iso_date(r.get("date") or "") for r in rows]
    dated = [d for d in dated if d]
    if not dated:
        end = date.today()
        start = end - timedelta(days=days)
    else:
        end = date.fromisoformat(max(dated))
        start = end - timedelta(days=days)
    return {
        "days": days,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "label": f"{pretty_date(start.isoformat())} through {pretty_date(end.isoformat())}",
    }


def in_window(rows: list[dict], bounds: dict) -> list[dict]:
    start = bounds["start"]
    end = bounds["end"]
    kept = []
    for row in rows:
        day = iso_date(row.get("date") or "")
        if day and start <= day <= end:
            kept.append(row)
    return kept


def hosted_rows() -> list[dict]:
    """Tournament and community lists whose HTML is actually on disk.

    Sample lists and test events are left out. A href that appears in both
    files is counted once, tournament row first.
    """
    import json

    index_path = ROOT / "data/tournament-decks.json"
    comm_path = ROOT / "data/community-decks.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    community = json.loads(comm_path.read_text()) if comm_path.exists() else {}
    by_id = {L["id"]: L for L in _gen.LEADERS}
    rows: list[dict] = []
    seen: set[str] = set()

    def add(leader: dict, row: dict) -> None:
        href = row.get("href") or ""
        if not href or href in seen:
            return
        if row.get("kind") == "sample":
            return
        if not (ROOT / href.lstrip("/")).exists():
            return
        if _event.is_test_row(row):
            return
        seen.add(href)
        rows.append(row)

    for leader in _gen.LEADERS:
        lid = leader["id"]
        for item in index.get(lid) or []:
            row = dict(item)
            row["leader"] = leader
            row["tournament_name"] = row.get("tournament_name") or row.get("tournament") or ""
            row["bucket"] = "tournament"
            add(leader, row)
        for item in community.get(lid) or []:
            row = {
                "slug": item.get("slug"),
                "href": item.get("href") or "",
                "player": item.get("player") or "Community",
                "tournament_name": item.get("subtitle") or item.get("title") or "",
                "placing": item.get("placing"),
                "date": item.get("date") or "",
                "kind": item.get("kind") or "web",
                "title_override": item.get("title"),
                "subtitle": item.get("subtitle")
                or {"youtube": "YouTube list", "x": "X list", "web": "Community list"}.get(
                    item.get("kind"), "Community list"
                ),
                "leader": by_id.get(lid) or leader,
                "bucket": "community",
            }
            add(leader, row)
    return rows


def _placing(row: dict) -> int | None:
    placing = row.get("placing")
    if isinstance(placing, int):
        return placing
    if placing is None or placing == "":
        return None
    try:
        return int(placing)
    except (TypeError, ValueError):
        return None


def empty_stats(leader: dict) -> dict:
    return {
        "lists": 0,
        "wins": 0,
        "top8": 0,
        "top4": 0,
        "recent_lists": 0,
        "recent_wins": 0,
        "recent_top8": 0,
        "community": 0,
        "best": None,
        "href": "/" + leader["page"],
    }


def leader_stats(rows: list[dict], bounds: dict) -> dict[str, dict]:
    """All-time and in-window counts, keyed by leader id.

    recent_* is the rolling window. The tier list's own vote uses those
    fields. lists/wins/top8 stay all hosted lists, not only the window.
    """
    out = {L["id"]: empty_stats(L) for L in _gen.LEADERS}
    start = bounds["start"]
    for row in rows:
        leader = row.get("leader") or {}
        lid = leader.get("id")
        if lid not in out:
            continue
        stats = out[lid]
        stats["lists"] += 1
        if row.get("bucket") == "community":
            stats["community"] += 1
        placing = _placing(row)
        if placing is not None:
            if placing == 1:
                stats["wins"] += 1
            if placing <= 8:
                stats["top8"] += 1
            if placing <= 4:
                stats["top4"] += 1
            best = stats["best"]
            if best is None or placing < best:
                stats["best"] = placing
        day = iso_date(row.get("date") or "")
        if not day or day < start or day > bounds["end"]:
            continue
        stats["recent_lists"] += 1
        if placing is not None:
            if placing == 1:
                stats["recent_wins"] += 1
            if placing <= 8:
                stats["recent_top8"] += 1
    return out


def count_leaders(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        lid = (row.get("leader") or {}).get("id")
        if lid:
            counts[lid] += 1
    return dict(counts)


def twin_html(leader: dict) -> str:
    twin = TWINS.get(leader.get("id") or "")
    if not twin:
        return ""
    by_id = {L["id"]: L for L in _gen.LEADERS}
    other = by_id.get(twin["also"])
    if not other:
        return ""
    other_label = public_name(other)
    return (
        f'<p class="leader-twin">{twin["note"]} '
        f'<a href="/{other["page"]}">{other_label} ({other["id"]})</a> '
        f"is a different leader.</p>"
    )
