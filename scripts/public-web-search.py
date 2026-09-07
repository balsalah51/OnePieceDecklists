#!/usr/bin/env python3
"""Probe public pages for complete OPTCG 50-card ID lists.

Does not log into Facebook, X DMs, or YouTube comments. Does not invent lists.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("/workspace")
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"
LINE_RE = re.compile(r"(?i)(\d+)\s*[x×]\s*((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})")
LEADERS = {
    "OP17-001",
    "OP17-020",
    "OP17-039",
    "OP17-058",
    "OP17-079",
    "OP17-099",
    "OP13-001",
    "OP11-041",
    "OP14-020",
    "OP16-001",
    "OP15-058",
    "OP11-062",
    "OP13-079",
    "OP13-002",
    "OP16-022",
    "OP16-080",
    "OP15-002",
    "OP16-079",
    "OP14-060",
    "OP16-041",
    "OP16-060",
    "OP11-040",
    "OP08-058",
    "OP13-004",
    "OP09-062",
    "OP14-080",
    "OP14-041",
    "OP12-081",
    "OP09-001",
    "OP05-098",
    "ST10-002",
    "OP09-061",
    "ST13-003",
    "OP12-040",
    "OP05-002",
    "EB04-001",
    "OP10-099",
    "OP07-059",
    "ST13-001",
    "OP05-041",
    "OP05-060",
    "OP07-079",
    "OP10-022",
    "OP06-022",
    "ST14-001",
    "EB02-010",
    "OP14-040",
    "OP12-041",
    "ST30-001",
}

QUERIES = [
    "OP17 Edward Newgate decklist 4x OP17-001",
    "OP17 Shanks decklist OP17-020 youtube",
    "OP17 Rocks D Xebec decklist OP17-039",
    "OP17 Kaido decklist OP17-058",
    "OP17 Monkey D Luffy decklist OP17-079",
    "OP17 Charlotte Linlin decklist OP17-099",
    "RG Luffy OP13-001 decklist",
    "Nami OP11-041 decklist",
    "Mihawk OP14-020 decklist",
    "One Piece TCG OP17 deck profile youtube comments",
    "site:reddit.com/r/OnePieceTCG OP17 decklist",
    "site:twitter.com OP17 Rocks decklist",
    "OP17 Rocks facebook group decklist",
    "one piece tcg forum OP17 kaido list",
    "egmanevents OP17 deckbuilder",
    "limitless OP17 tournament decklist",
    "onepiecetopdecks OP17",
    "MarinefordTCG OP17 newgate list",
    "StrawHatPecan OP17 shanks list",
    "JohnnyTCG OP17 rocks list",
    "CardKaizoku OP17 xebec",
    "ArtressTCG OP17 kaido",
    "OP17 whitebeard 50 card list",
    "OP17 big mom linlin 50 card",
    "one piece tcg sim OP17 decklist paste",
    "UP Luffy OP11-040 decklist",
    "Blue Purple Luffy OP11-040 OP17 decklist",
    "Charlotte Pudding OP08-058 decklist",
    "Purple Yellow Pudding OP08 decklist",
    "site:mabitcg.com OP17 decklist",
    "site:opmetagame.com OP11-040",
    "site:onepiecetopdecks.com OP17",
]

PUBLIC_PAGES = [
    "https://play.limitlesstcg.com/decks?game=OP",
    "https://onepiece.limitlesstcg.com/",
    "https://onepiecetopdecks.com/",
    "https://deckbuilder.egmanevents.com/",
]


def fetch(url: str, timeout: int = 18) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def extract_lists(text: str) -> list[dict]:
    found = []
    for m in LINE_RE.finditer(text or ""):
        found.append((int(m.group(1)), m.group(2).upper()))
    if not found:
        return []
    # Split into leader-headed chunks when a 1x leader appears.
    chunks = []
    current = []
    for count, cid in found:
        if count == 1 and cid in LEADERS and current:
            chunks.append(current)
            current = []
        current.append((count, cid))
    if current:
        chunks.append(current)
    out = []
    for chunk in chunks:
        if not chunk:
            continue
        leader = chunk[0][1] if chunk[0][1] in LEADERS else None
        main = chunk[1:] if leader else chunk
        total = sum(c for c, _ in main)
        if leader and total == 50:
            raw = " ".join(f"{c}x{i}" for c, i in chunk)
            out.append({"leader": leader, "cards": total, "raw": raw})
    return out


def main() -> None:
    log = []
    hits = []
    for i, q in enumerate(QUERIES, 1):
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
        row = {"n": i, "query": q, "url": url, "ok": False, "lists": 0, "note": ""}
        try:
            html = fetch(url)
            lists = extract_lists(html)
            row["ok"] = True
            row["lists"] = len(lists)
            row["note"] = f"chars {len(html)}"
            hits.extend({"source": q, **item} for item in lists)
        except Exception as exc:  # noqa: BLE001
            row["note"] = f"{type(exc).__name__}: {exc}"
        log.append(row)
        print(f"search {i:02d}", row["ok"], row["lists"], q[:60], row["note"][:80])

    for url in PUBLIC_PAGES:
        row = {"n": len(log) + 1, "query": url, "url": url, "ok": False, "lists": 0, "note": ""}
        try:
            html = fetch(url)
            lists = extract_lists(html)
            row["ok"] = True
            row["lists"] = len(lists)
            row["note"] = f"chars {len(html)}"
            hits.extend({"source": url, **item} for item in lists)
        except Exception as exc:  # noqa: BLE001
            row["note"] = f"{type(exc).__name__}: {exc}"
        log.append(row)
        print("page", row["ok"], row["lists"], url, row["note"][:80])

    out = {"searches": log, "complete_lists": hits}
    path = ROOT / "data/public-search-log.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("complete public lists found", len(hits))
    print("wrote", path)


if __name__ == "__main__":
    main()
