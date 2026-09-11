#!/usr/bin/env python3
"""Host complete 50-card lists from public OnePieceDB deck pages.

Reads the injected mainDeck ID array. Only writes a page when that dump is
1 hosted leader + 50 cards with no bans. Does not invent cards. Does not wipe
existing pages.
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
SITE = "https://onepiecedb.io"
DECK_HREF_RE = re.compile(r'href="(https://onepiecedb\.io/deck/[^"?#]+)"')
MAIN_RE = re.compile(r"mainDeck:\s*(\[[^\]]+\])")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DATE_RE = re.compile(r"(2026-\d{2}-\d{2})")
BY_RE = re.compile(r"\bby\s+([^<-]+?)(?:\s*-\s*OnePieceDB)?\s*$", re.I)
CARD_RE = re.compile(r"^((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})$")
LISTING = [
    f"{SITE}/deck-search?sort=Newest",
    f"{SITE}/deck-search?from=2026-08-01",
    f"{SITE}/format/op17",
    f"{SITE}/category/tournament-decks?tournament",
]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch(url: str, timeout: int = 22) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def clean(text: str) -> str:
    return " ".join((text or "").replace("&amp;", "&").split())


def collect_urls(slugs: dict[str, str]) -> list[str]:
    urls: list[str] = []
    pages = list(LISTING)
    for slug in slugs.values():
        pages.append(f"{SITE}/category/leader/{slug}")
    for page in pages:
        try:
            body = fetch(page)
        except Exception as exc:  # noqa: BLE001
            print("list fail", page, exc, flush=True)
            continue
        for href in DECK_HREF_RE.findall(body):
            if href not in urls:
                urls.append(href)
        print("opdb list", page.split(".io")[-1][:48], "urls", len(urls), flush=True)
        time.sleep(0.12)
    return urls


def counts_from_main(body: str) -> dict[str, int]:
    m = MAIN_RE.search(body)
    if not m:
        return {}
    try:
        arr = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}
    counts: dict[str, int] = {}
    for raw in arr:
        cid = str(raw).upper().split("_")[0]
        if CARD_RE.match(cid):
            counts[cid] = counts.get(cid, 0) + 1
    return counts


def parse_page(url: str, hosted: set[str], gen, commsrc) -> dict | None:
    body = fetch(url)
    counts = counts_from_main(body)
    lids = [cid for cid, n in counts.items() if cid in hosted and n == 1]
    lid = lids[0] if len(lids) == 1 else None
    if not lid:
        ones = [cid for cid, n in counts.items() if n == 1 and cid in hosted]
        lid = ones[0] if len(ones) == 1 else None
    main_n = sum(n for cid, n in counts.items() if cid != lid) if lid else 0
    banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
    title_html = TITLE_RE.search(body)
    title = clean(title_html.group(1) if title_html else url.rsplit("/", 1)[-1])
    title = title.replace(" - OnePieceDB", "").strip()
    player = "OnePieceDB"
    by = BY_RE.search(title)
    if by:
        player = by.group(1).strip() or player
    days = DATE_RE.findall(body)
    day = days[0] if days else ""
    print(url.rsplit("/", 1)[-1], lid or "-", "cards", main_n, "banned", banned, "day", day or "-", flush=True)
    if not lid or counts.get(lid) != 1 or main_n != 50 or banned:
        return None
    slug_tail = url.rstrip("/").rsplit("/", 1)[-1]
    item = {
        "leader": lid,
        "kind": "web",
        "player": player,
        "title": title or slug_tail,
        "subtitle": f"Public OnePieceDB list" + (f" · {day}" if day else ""),
        "source_url": url,
        "slug": gen.slugify(f"opdb-{slug_tail}")[:70],
        "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
        "cards": main_n,
    }
    if day:
        item["date"] = day
    return item


def collect_lists(gen, commsrc) -> list[dict]:
    hosted = {L["id"] for L in gen.LEADERS}
    print("=== OnePieceDB ===", flush=True)
    urls = collect_urls(commsrc.OPDL_SLUGS)
    print("opdb urls", len(urls), flush=True)
    found: list[dict] = []
    seen: set[str] = set()
    existing = existing_urls()
    for url in urls:
        if url in existing:
            print("skip known", url.rsplit("/", 1)[-1], flush=True)
            continue
        try:
            item = parse_page(url, hosted, gen, commsrc)
        except Exception as exc:  # noqa: BLE001
            print("fail", url, exc, flush=True)
            time.sleep(0.12)
            continue
        time.sleep(0.12)
        if item:
            commsrc.record(found, item, seen)
    log_path = ROOT / "data/onepiecedb-log.json"
    log_path.write_text(json.dumps({"hosted": found}, indent=2, ensure_ascii=False) + "\n")
    print("onepiecedb ready", len(found), "log", log_path, flush=True)
    return found


def existing_urls() -> set[str]:
    urls: set[str] = set()
    path = ROOT / "data/community-decks.json"
    if not path.exists():
        return urls
    data = json.loads(path.read_text())
    for rows in data.values():
        for row in rows or []:
            src = row.get("source_url") or ""
            if "onepiecedb.io" in src:
                urls.add(src)
    return urls


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    found = collect_lists(gen, commsrc)
    commsrc.write_lists(found)
    print("onepiecedb ingest done", flush=True)


if __name__ == "__main__":
    main()
