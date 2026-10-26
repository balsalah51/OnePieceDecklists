#!/usr/bin/env python3
"""Source name, region, and format era for a hosted list.

Region comes from the site that published the list, or from a Japan marker
in the event name. Format era is a set code the event title itself states
(for example "[OP17]" or "[EB05]"). Lists with no stated set stay "unlabeled".
Nothing here invents a format from the cards in the deck.
"""

from __future__ import annotations

import html
import re
from collections import Counter
from urllib.parse import urlparse

JP_HOSTS = {
    "tcg-portal.jp",
    "mercardop.jp",
    "cardkaizoku.com",
    "deckbuilder.cardkaizoku.com",
}
EN_HOSTS = {
    "play.limitlesstcg.com",
    "onepiece.limitlesstcg.com",
    "limitlesstcg.com",
    "optcg.gg",
    "opdeckguide.com",
    "onepiecedb.io",
}
NAMES = {
    "play.limitlesstcg.com": "Limitless",
    "onepiece.limitlesstcg.com": "Limitless",
    "limitlesstcg.com": "Limitless",
    "optcg.gg": "OPTCG.GG",
    "opdeckguide.com": "OPDeckGuide",
    "onepiecedb.io": "OnePieceDB",
    "tcg-portal.jp": "TCG Portal",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "reddit.com": "Reddit",
    "x.com": "X",
    "pbs.twimg.com": "X",
    "mabitcg.com": "Mabi TCG",
    "mercardop.jp": "Mercari OP",
    "cardkaizoku.com": "Card Kaizoku",
    "deckbuilder.cardkaizoku.com": "Card Kaizoku",
    "onepiecedecklists.com": "One Piece Decklists",
}
REGION_LABEL = {"english": "English", "japanese": "Japanese", "other": "Other"}
JP_NAME = re.compile(
    r"(\bJP\b|日本|フラッグシップ|チャンピオンシップ|店内|店舗|\[JP\]|\bJapanese\b)",
    re.I,
)
SET_RE = re.compile(
    r"\[(OP\d+|EB\d+|ST\d+)\]|(?<![A-Z0-9])((?:OP|EB)\d{2})(?!\d)",
    re.I,
)

_failures: list[dict] = []


def reset_failures() -> None:
    _failures.clear()


def note_failure(source: str, reason: str, item: str = "") -> None:
    _failures.append({"source": source, "item": item, "reason": str(reason)})
    print(f"SOURCE FAIL {source} {item} {reason}", flush=True)


def take_failures() -> list[dict]:
    out = list(_failures)
    _failures.clear()
    return out


def host_of(url: str) -> str:
    if "://" not in (url or ""):
        return ""
    host = (urlparse(url).netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def source_name(url: str) -> str:
    host = host_of(url)
    if host in NAMES:
        return NAMES[host]
    return host or "Unknown"


def region_of(url: str, event_text: str) -> str:
    host = host_of(url)
    if host in JP_HOSTS or JP_NAME.search(event_text or ""):
        return "japanese"
    if host in EN_HOSTS:
        return "english"
    return "other"


def format_era(event_text: str, format_field: str = "") -> str:
    """Set code printed in the event title, or EXTRA/CUSTOM from Limitless."""
    text = f"{event_text or ''} {format_field or ''}"
    found: list[str] = []
    for match in SET_RE.finditer(text):
        code = (match.group(1) or match.group(2) or "").upper()
        if code and code not in found:
            found.append(code)
    if found:
        return " + ".join(found[:3])
    fmt = (format_field or "").strip().upper()
    if fmt in {"EXTRA", "CUSTOM"}:
        return fmt
    return "unlabeled"


def apply_tags(row: dict) -> dict:
    url = row.get("source_url") or ""
    event = (
        row.get("event")
        or row.get("tournament")
        or row.get("tournament_name")
        or row.get("title")
        or ""
    )
    row["source"] = source_name(url) if url else (row.get("source") or "Unknown")
    row["source_host"] = host_of(url)
    row["region"] = region_of(url, event)
    row["format_era"] = format_era(event, row.get("format") or "")
    sources = []
    seen = set()
    for src in row.get("sources") or []:
        if not isinstance(src, dict):
            continue
        key = (src.get("name") or "", (src.get("url") or "").rstrip("/"))
        if not key[0] and not key[1]:
            continue
        if key in seen:
            continue
        seen.add(key)
        sources.append({"name": src.get("name") or source_name(src.get("url") or ""), "url": src.get("url") or ""})
    primary = (row["source"], url.rstrip("/"))
    if url and primary not in seen:
        sources.insert(0, {"name": row["source"], "url": url})
    row["sources"] = sources
    return row


def credit_label(row: dict) -> str:
    names: list[str] = []
    for src in row.get("sources") or []:
        name = (src.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    if not names and row.get("source"):
        names.append(row["source"])
    bits = []
    if names:
        bits.append(", ".join(names))
    region = REGION_LABEL.get(row.get("region") or "", "")
    if region:
        bits.append(region)
    era = row.get("format_era") or ""
    if era:
        bits.append(era)
    return " · ".join(bits)


def attribution_html(row: dict) -> str:
    region = REGION_LABEL.get(row.get("region") or "", "Other")
    era = row.get("format_era") or "unlabeled"
    links = []
    sources = row.get("sources") or []
    if not sources and row.get("source_url"):
        sources = [{"name": row.get("source") or source_name(row["source_url"]), "url": row["source_url"]}]
    for src in sources:
        name = src.get("name") or "Source"
        url = src.get("url") or ""
        if url:
            links.append(f'<a href="{html.escape(url, quote=True)}">{html.escape(name)}</a>')
        else:
            links.append(html.escape(name))
    same = ""
    canonical = row.get("duplicate_of") or ""
    if canonical:
        same = f' Same list as <a href="{html.escape(canonical, quote=True)}">this page</a>.'
    joined = ", ".join(links) if links else html.escape(row.get("source") or "Unknown")
    return (
        f'<span class="list-sources">Region: {html.escape(region)}. '
        f"Format: {html.escape(era)}. "
        f"Sources: {joined}.{same}</span>"
    )


def count_rows(rows: list[dict]) -> dict:
    by_source: Counter[str] = Counter()
    by_region: Counter[str] = Counter()
    by_source_region: Counter[tuple[str, str]] = Counter()
    unique = 0
    for row in rows:
        if row.get("duplicate_of"):
            continue
        unique += 1
        region = row.get("region") or "other"
        by_region[region] += 1
        names: list[str] = []
        for src in row.get("sources") or []:
            name = (src.get("name") or "").strip()
            if name and name not in names:
                names.append(name)
        if not names:
            names = [row.get("source") or "Unknown"]
        for name in names:
            by_source[name] += 1
            by_source_region[(name, region)] += 1
    return {
        "lists": unique,
        "by_source": dict(by_source.most_common()),
        "by_region": {key: by_region.get(key, 0) for key in ("english", "japanese", "other")},
        "by_source_region": [
            {"source": source, "region": region, "lists": n}
            for (source, region), n in sorted(by_source_region.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
    }


def counts_html(rows: list[dict]) -> str:
    counts = count_rows(rows)
    source_rows = []
    for name, n in counts["by_source"].items():
        source_rows.append(f"<li>{html.escape(name)}: {n}</li>")
    region_bits = []
    for key in ("english", "japanese", "other"):
        region_bits.append(f"{REGION_LABEL[key]} {counts['by_region'].get(key, 0)}")
    return (
        '<section class="card home-panel" id="source-counts">'
        '<div class="section-title"><h2>Lists by source</h2>'
        f'<div class="muted">{counts["lists"]} lists after de-dupe</div></div>'
        "<p class=\"muted\">A list that came from two places counts under each source. "
        "English-format lists are the ones in the share chart and the tier list. "
        "Japanese-format lists stay labeled and are not mixed into those rates. "
        f"Regions: {html.escape(', '.join(region_bits))}.</p>"
        f"<ul>{''.join(source_rows)}</ul>"
        "</section>"
    )
