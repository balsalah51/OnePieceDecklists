#!/usr/bin/env python3
"""One window and one set of leader counts for the homepage and the tier list.

Recent lists are a rolling window ending on today's date in America/New_York,
not on the newest hosted list. OPDL_RECENT_DAYS overrides the length (default
45). The homepage share chart, the Leaders row, the weekly meta note, and the
tier list's "recent" columns all read this module. Tier letters still come
from build-tier-list.aggregate; this file does not change those thresholds.
"""

from __future__ import annotations

import html
import importlib.util
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import source_meta

ROOT = Path("/workspace")
RECENT_DAYS = int(os.environ.get("OPDL_RECENT_DAYS", "45"))
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
ET = ZoneInfo("America/New_York")
STALE_AFTER = timedelta(hours=48)

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


def now_et(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(ET)
    if now.tzinfo is None:
        return now.replace(tzinfo=ET)
    return now.astimezone(ET)


def newest_list_day(rows: list[dict]) -> str:
    dated = [iso_date(r.get("date") or "") for r in rows]
    dated = [d for d in dated if d]
    return max(dated) if dated else ""


def newest_list_meta(rows: list[dict]) -> dict:
    """The newest dated list, plus how many other lists share that day."""
    best_day = ""
    same: list[dict] = []
    for row in rows:
        day = iso_date(row.get("date") or "")
        if not day:
            continue
        if day > best_day:
            best_day = day
            same = [row]
        elif day == best_day:
            same.append(row)
    if not same:
        return {}
    same.sort(key=lambda row: row.get("href") or "")
    chosen = same[0]
    event = (
        chosen.get("tournament_name")
        or chosen.get("tournament")
        or chosen.get("event")
        or chosen.get("title")
        or ""
    )
    return {
        "newest": best_day,
        "newest_event": event,
        "newest_region": chosen.get("region") or "",
        "newest_source": chosen.get("source") or "",
        "newest_href": chosen.get("href") or "",
        "newest_same_day": len(same),
    }


def window_bounds(
    rows: list[dict],
    *,
    days: int | None = None,
    today: date | None = None,
    now: datetime | None = None,
) -> dict:
    """Rolling window ending today in America/New_York.

    `today` and `now` are for tests. The newest hosted list is reported
    separately and does not move the end of the window.
    """
    days = RECENT_DAYS if days is None else int(days)
    clock = now_et(now)
    if today is not None and now is None:
        clock = datetime(today.year, today.month, today.day, 12, 0, tzinfo=ET)
    end = today or clock.date()
    start = end - timedelta(days=days)
    meta = newest_list_meta(rows)
    newest = meta.get("newest") or ""
    stale = True
    if newest:
        newest_start = datetime.fromisoformat(newest).replace(tzinfo=ET)
        stale = (clock - newest_start) > STALE_AFTER
    newest_label = pretty_date(newest) if newest else ""
    return {
        "days": days,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "label": f"{pretty_date(start.isoformat())} through {pretty_date(end.isoformat())}",
        "newest": newest,
        "newest_label": newest_label,
        "newest_event": meta.get("newest_event") or "",
        "newest_region": meta.get("newest_region") or "",
        "newest_source": meta.get("newest_source") or "",
        "newest_href": meta.get("newest_href") or "",
        "newest_same_day": meta.get("newest_same_day") or 0,
        "stale": stale,
        "timezone": "America/New_York",
    }


def freshness_html(bounds: dict) -> str:
    """Visible stamp. The warning shows when the newest list is over 48 hours old."""
    newest = bounds.get("newest_label") or "an unknown date"
    event = bounds.get("newest_event") or ""
    region = source_meta.REGION_LABEL.get(bounds.get("newest_region") or "", "")
    source = bounds.get("newest_source") or ""
    detail = ""
    if event:
        where = ", ".join(part for part in (region, source) if part)
        extra = ""
        same_day = int(bounds.get("newest_same_day") or 0)
        if same_day > 1:
            extra = f" {same_day} lists share this date."
        tail = f" ({where})" if where else ""
        detail = f" Newest list: {html.escape(event)}{html.escape(tail)}.{extra}"
    lines = [
        f'<p class="freshness" id="last-updated">Last updated {html.escape(newest)}.{detail}</p>'
    ]
    if bounds.get("stale"):
        lines.append(
            '<p class="freshness-stale" role="status">'
            f"Newest hosted list is {html.escape(newest)}, more than 48 hours ago "
            "(America/New_York). The recent window still ends today."
            "</p>"
        )
    return "\n".join(lines)


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
        if row.get("duplicate_of"):
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
            source_meta.apply_tags(row)
            add(leader, row)
        for item in community.get(lid) or []:
            row = {
                "slug": item.get("slug"),
                "href": item.get("href") or "",
                "player": item.get("player") or "Community",
                "tournament_name": item.get("event") or item.get("subtitle") or item.get("title") or "",
                "event": item.get("event") or "",
                "placing": item.get("placing"),
                "date": item.get("date") or "",
                "kind": item.get("kind") or "web",
                "title_override": item.get("title"),
                "subtitle": item.get("subtitle")
                or {"youtube": "YouTube list", "x": "X list", "web": "Community list"}.get(
                    item.get("kind"), "Community list"
                ),
                "source_url": item.get("source_url") or "",
                "source": item.get("source") or "",
                "region": item.get("region") or "",
                "format_era": item.get("format_era") or "",
                "sources": item.get("sources") or [],
                "duplicate_of": item.get("duplicate_of") or "",
                "leader": by_id.get(lid) or leader,
                "bucket": "community",
            }
            source_meta.apply_tags(row)
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
