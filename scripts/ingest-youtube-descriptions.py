#!/usr/bin/env python3
"""Pull complete 50-card lists from public YouTube descriptions only.

Does not invent cards from gameplay or related-video chrome.
"""

from __future__ import annotations

import importlib.util
import json
import re
import urllib.request
from pathlib import Path

spec = importlib.util.spec_from_file_location("commsrc", "/workspace/scripts/scrape-community-sources.py")
commsrc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commsrc)

UA = "Mozilla/5.0 (compatible; OnePieceDecklists/1.0; +https://onepiecedecklists.com)"
YT_RE = re.compile(r"(?:watch\?v=|/shorts/)([A-Za-z0-9_-]{11})")
DESC_RE = re.compile(
    r"(?:Deck List:|Decklist:|Deck Profile:)\\n((?:\\n?\d+x(?:OP|ST|EB|PRB)\d{2}-\d{3}|\\n?\d+xP-\d{3})+)",
    re.I,
)
SEED_VIDEOS = [
    "rlffBOdE4qs",  # Nightingale OP17 UP Luffy
    "-M5JW91P5BE",  # Egman UP Luffy / Mr.3
    "E-iESLJ8N_4",
    "7aCHDV0zuoI",
    "kKBHITaidrY",
    "KViquBQIsx0",
    "LQdWh4mzH1o",
    "4MyNT1IM0DE",
    "8tM5AofdVQ4",
    "CrLQZiTBCM4",
    "yF5NQsfwZWY",
    "N-NbpFcKcYo",
]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", "replace")


def unescape(s: str) -> str:
    return s.replace("\\u0026", "&").replace("\\/", "/").replace("\\n", "\n")


CHANNELS = [
    "@NightingaleTCG",
    "@MarinefordTCG",
    "@StrawHatPecan",
    "@BlaisePlaysTCG",
    "@JohnnyTCG",
    "@ArtressTCG",
    "@TheEgman",
    "@CardKaizoku",
    "@Chinoize",
    "@CapiamoOP",
]


def video_ids() -> list[str]:
    ids = list(SEED_VIDEOS)
    queries = (
        "OP17+decklist",
        "OP17+decklist&sp=CAI%253D",
        "OPTCG+decklist&sp=CAI%253D",
        "OP17+deck+profile+August+2026",
        "OP17+decklist+August+27+2026",
        "OP17+decklist+August+28+2026",
        "OP17+decklist+August+29+2026",
        "OP17+decklist+August+30+2026",
        "OP17+decklist+August+31+2026",
        "OP17+decklist+September+2026",
        "OP17+decklist+September+1+2026",
        "OP17+decklist+September+2+2026",
        "OP17+decklist+September+3+2026",
        "ChinoizeCup+104+decklist",
        "ChinoizeCup+105+decklist",
        "OPTCG+decklist+August+2026",
        "UP+Luffy+OP11-040+decklist",
        "Charlotte+Pudding+OP08-058+decklist",
        "OP17+UP+Luffy",
        "NightingaleTCG+UP+Luffy",
        "NightingaleTCG+OP17",
        "MarinefordTCG+OP17+decklist",
        "StrawHatPecan+OP17+decklist",
        "BlaisePlays+OP17+decklist",
        "Artress+OP17+decklist",
        "JohnnyTCG+OP17+decklist",
        "OP17+Kaido+decklist",
        "OP17+Rocks+decklist",
        "OP17+Linlin+decklist",
        "OP17+Shanks+decklist",
        "OP17+Newgate+decklist",
        "OP17+Mihawk+decklist",
        "OP17+Sabo+decklist",
        "OP17+Ace+decklist",
        "ST30+Luffy+Ace+decklist",
        "ChinoizeCup+decklist",
        "Utrecht+OP17+decklist",
    )
    for q in queries:
        html = fetch("https://www.youtube.com/results?search_query=" + q)
        for vid in YT_RE.findall(html):
            if vid not in ids:
                ids.append(vid)
        print("search", q[:48], "ids", len(ids), flush=True)
    for handle in CHANNELS:
        url = f"https://www.youtube.com/{handle}/videos"
        try:
            html = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print("channel fail", handle, exc, flush=True)
            continue
        before = len(ids)
        for vid in YT_RE.findall(html):
            if vid not in ids:
                ids.append(vid)
        print("channel", handle, "new", len(ids) - before, "ids", len(ids), flush=True)
    return ids


def lists_from_html(html: str) -> list[tuple[str, dict[str, int]]]:
    text = unescape(html)
    found = []
    seen = set()
    # Prefer an explicit Deck List block in the description.
    for m in DESC_RE.finditer(html):
        block = unescape(m.group(1))
        counts = commsrc.parse_counts(block)
        lid = commsrc.leader_of(counts)
        if lid and commsrc.complete(counts, lid):
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            if raw not in seen:
                seen.add(raw)
                found.append((lid, counts))
    if found:
        return found
    # Fallback: first complete leader-headed chunk near "Deck List" in the unescaped page.
    idx = text.lower().find("deck list")
    if idx < 0:
        idx = text.lower().find("decklist")
    window = text[idx : idx + 2500] if idx >= 0 else ""
    counts = commsrc.parse_counts(window)
    lid = commsrc.leader_of(counts)
    if lid and commsrc.complete(counts, lid):
        found.append((lid, counts))
    return found


def title_of(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).replace(" - YouTube", "").strip()[:90]


MONTHS = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def publish_day(html: str) -> str:
    m = re.search(r'"publishDate"\s*:\s*"(20\d{2}-\d{2}-\d{2})', html)
    if m:
        return m.group(1)
    m = re.search(r'"uploadDate"\s*:\s*"(20\d{2}-\d{2}-\d{2})', html)
    if m:
        return m.group(1)
    m = re.search(
        r'"dateText"\s*:\s*\{[^}]*"simpleText"\s*:\s*"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s*(20\d{2})"',
        html,
        re.I,
    )
    if m:
        return f"{m.group(3)}-{MONTHS[m.group(1)[:3].lower()]}-{int(m.group(2)):02d}"
    m = re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s*(20\d{2})",
        html,
    )
    if m:
        return f"{m.group(3)}-{MONTHS[m.group(1)[:3].lower()]}-{int(m.group(2)):02d}"
    return ""


def main() -> None:
    found: list[dict] = []
    seen: set[str] = set()
    ids = video_ids()
    print("scanning", min(len(ids), 180), "videos", flush=True)
    for vid in ids[:180]:
        url = f"https://www.youtube.com/watch?v={vid}"
        try:
            html = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print("fail", vid, exc, flush=True)
            continue
        title = title_of(html)
        day = publish_day(html)
        lists = lists_from_html(html)
        print(vid, "lists", len(lists), day or "-", title[:70], flush=True)
        if day and day < "2026-08-27":
            continue
        for lid, counts in lists:
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            item = {
                "leader": lid,
                "kind": "youtube",
                "player": "YouTube",
                "title": title or f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} YouTube list",
                "subtitle": "YouTube deck profile from a public description",
                "source_url": url,
                "slug": commsrc.slug_for("yt", "youtube", f"{commsrc.TARGET_IDS[lid]}-{vid}"),
                "raw": raw,
                "cards": sum(n for cid, n in counts.items() if cid != lid),
            }
            if day:
                item["date"] = day
                item["subtitle"] = f"YouTube deck profile from a public description · {day}"
            commsrc.record(found, item, seen)
    # Known description list that the block regex already should catch; keep as backup.
    backup = {
        "leader": "OP11-040",
        "kind": "youtube",
        "player": "NightingaleTCG",
        "title": "OP17 UP Luffy gets TWO new 9 costs - Nightingale",
        "subtitle": "YouTube deck profile · also on X @BenSchumi7",
        "source_url": "https://www.youtube.com/watch?v=rlffBOdE4qs",
        "slug": commsrc.slug_for("yt", "nightingale", "up-luffy-rlffBOdE4qs"),
        "raw": (
            "1xOP11-040 4xOP13-043 3xOP16-056 3xOP17-046 4xOP11-054 4xOP06-119 "
            "4xOP05-067 4xOP17-074 4xST18-001 4xEB01-061 4xP-107 2xOP17-064 "
            "2xOP17-065 4xOP09-078 4xOP11-080"
        ),
        "cards": 50,
    }
    commsrc.record(found, backup, seen)
    egman = {
        "leader": "OP11-040",
        "kind": "youtube",
        "player": "ArtressTCG",
        "title": "Mr.3 Brings Back UP Luffy - Artress",
        "subtitle": "YouTube + EgmanEvents deck builder",
        "source_url": "https://www.youtube.com/watch?v=-M5JW91P5BE",
        "slug": commsrc.slug_for("yt", "artress", "up-luffy-m5jw91p5be"),
        "raw": (
            "1xOP11-040 1xOP15-047 4xOP06-119 4xP-107 4xOP07-051 2xOP07-064 "
            "4xST18-001 4xOP11-054 2xP-053 2xEB03-034 4xOP16-056 4xOP09-078 "
            "4xOP11-080 2xOP14-077 4xOP08-076 1xOP06-058 4xEB01-061"
        ),
        "cards": 50,
    }
    commsrc.record(found, egman, seen)
    Path("/workspace/data/youtube-desc-log.json").write_text(
        json.dumps({"found": found}, indent=2, ensure_ascii=False) + "\n"
    )
    print("complete youtube description lists", len(found), flush=True)
    commsrc.write_lists(found)
    print("youtube ingest done", flush=True)


if __name__ == "__main__":
    main()
