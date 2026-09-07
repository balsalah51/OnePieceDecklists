"""Load card cache + consensus lists and format Discord posts."""

from __future__ import annotations

import json
import re
from collections import defaultdict

from .config import LEADERS, REPO_ROOT, SITE_URL, site_url


def display_name(name: str) -> str:
    if not name:
        return ""
    s = re.sub(r"\.D\.", " D. ", name)
    s = re.sub(r"(?<!D)\.", " ", s)
    return " ".join(s.split())


def load_json(path) -> dict:
    return json.loads(path.read_text())


def load_card_cache() -> dict:
    cache: dict = {}
    op17 = REPO_ROOT / "data/op17-cards.json"
    other = REPO_ROOT / "data/other-leaders.json"
    extra = REPO_ROOT / "data/card-cache.json"
    if op17.exists():
        cache.update(load_json(op17))
    if other.exists():
        payload = load_json(other)
        cache.update(payload.get("cards") or {})
        cache.update(payload.get("leaders") or {})
    if extra.exists():
        cache.update(load_json(extra))
    return cache


def load_consensus() -> dict:
    path = REPO_ROOT / "data/consensus-decks.json"
    if not path.exists():
        return {}
    return load_json(path)


def card_name(cache: dict, cid: str) -> str:
    meta = cache.get(cid) or {}
    return display_name(meta.get("name") or cid)


def card_group(cache: dict, cid: str) -> str:
    cat = str((cache.get(cid) or {}).get("category") or "character").lower()
    if cat == "event":
        return "Events"
    if cat == "stage":
        return "Stages"
    if cat == "leader":
        return "Leader"
    return "Characters"


def consensus_lines(leader: dict, cache: dict, consensus: dict) -> tuple[list[str], int, int]:
    entry = consensus.get(leader["id"]) or {}
    cards = entry.get("cards") or []
    lists_n = int(entry.get("lists") or 0)
    groups: dict[str, list[str]] = defaultdict(list)
    total = 0
    groups["Leader"].append(f"`1x` {card_name(cache, leader['id'])} · `{leader['id']}`")
    for card in cards:
        cid = card["id"]
        count = int(card["count"])
        rate = float(card.get("rate") or 0)
        total += count
        pct = f"{round(rate * 100)}%"
        line = f"`{count}x` {card_name(cache, cid)} · `{cid}` · {pct}"
        groups[card_group(cache, cid)].append(line)
    lines: list[str] = []
    for group in ("Leader", "Characters", "Events", "Stages"):
        if not groups[group]:
            continue
        lines.append(f"**{group}**")
        lines.extend(groups[group])
        lines.append("")
    return lines, total, lists_n


def format_consensus_embed(leader: dict, cache: dict, consensus: dict) -> dict:
    """Plain dict so tests do not need discord.py."""
    lines, total, lists_n = consensus_lines(leader, cache, consensus)
    body = "\n".join(lines).strip()
    if len(body) > 3900:
        body = body[:3890] + "\n…"
    src = f"Averaged from {lists_n} list{'s' if lists_n != 1 else ''} on the site, filled to 50 cards."
    if lists_n == 0:
        src = "No consensus file yet for this leader. Check the site page."
        body = leader["take"]
    return {
        "title": f"Consensus list · {leader['name']}",
        "url": site_url(leader),
        "description": f"{leader['take']}\n\n{src}\n\n{body}",
        "color": leader["color"],
        "footer": f"OPDL consensus · {leader['id']} · {total} cards",
        "image": leader["image"],
    }


def format_text_list(leader: dict, cache: dict, consensus: dict) -> str:
    """Copy-paste 50-card list."""
    entry = consensus.get(leader["id"]) or {}
    cards = entry.get("cards") or []
    rows = [f"1x{leader['id']}"]
    for card in cards:
        rows.append(f"{int(card['count'])}x{card['id']}")
    header = f"{leader['name']} consensus - {SITE_URL}{leader['page']}"
    block = header + "\n" + "\n".join(rows)
    if len(block) > 1900:
        block = block[:1890] + "\n…"
    return f"```\n{block}\n```"


def all_planned_messages(cache: dict | None = None, consensus: dict | None = None) -> list[dict]:
    cache = cache if cache is not None else load_card_cache()
    consensus = consensus if consensus is not None else load_consensus()
    return [
        {
            "leader": L,
            "embed": format_consensus_embed(L, cache, consensus),
            "text_list": format_text_list(L, cache, consensus),
        }
        for L in LEADERS
    ]


def leader_ids_on_site() -> set[str]:
    return {L["id"] for L in LEADERS}
