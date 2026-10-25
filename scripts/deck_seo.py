"""Titles, descriptions, and DON!! text for a single decklist page."""

from __future__ import annotations

import html
import re


def deck_title(leader: str, event: str, placing: str, date: str) -> str:
    """<Leader> Decklist - <Event> <Placing> (<Date>)."""
    leader = (leader or "Leader").strip()
    bits = [part.strip() for part in (event, placing) if part and part.strip()]
    tail = " ".join(bits)
    day = (date or "").strip()[:10]
    if day:
        tail = f"{tail} ({day})" if tail else f"({day})"
    if tail:
        return f"{leader} Decklist - {tail}"
    return f"{leader} Decklist"


def deck_description(leader: str, event: str, placing: str, date: str) -> str:
    leader = (leader or "Leader").strip()
    where = (event or "").strip() or "a published event"
    extra = [part.strip() for part in (placing, (date or "").strip()[:10]) if part and part.strip()]
    body = f"{leader} OPTCG decklist - {where}"
    if extra:
        body += ", " + ", ".join(extra)
    body += ". Full card list for the ONE PIECE CARD GAME."
    return body[:300]


def stats_fallback(curve_titles: list[str], pills: list[str]) -> str:
    """Plain sentence for the DON!! curve and counter pills."""
    costs = []
    for title in curve_titles:
        text = html.unescape(title)
        match = re.search(r"(\d+\+?)\s*DON!!\s*·\s*(\d+)", text)
        if match and match.group(2) != "0":
            costs.append(f"{match.group(2)} at {match.group(1)} DON!!")
    curve = ", ".join(costs) if costs else "no cost data"
    counters = ", ".join(html.unescape(p).strip() for p in pills if p.strip()) or "no counter data"
    return f"DON!! curve: {curve}. Counters: {counters}."
