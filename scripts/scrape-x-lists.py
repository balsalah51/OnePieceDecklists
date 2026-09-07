#!/usr/bin/env python3
"""Fetch public X posts for complete OPTCG 50-card ID lists.

Uses only public proxies (Jina reader, FxTwitter, DuckDuckGo HTML). Does not
log in, does not read DMs, and does not invent lists. Readable deck-builder
photos on in-window tweets are downloaded so a later pass can transcribe them.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com; public OPTCG list scrape)"
LINE_RE = re.compile(r"(?i)(\d+)\s*[x×]\s*((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})")
STATUS_RE = re.compile(
    r"(?:x\.com|twitter\.com|nitter\.[^/\s]+)/([A-Za-z0-9_]+)/status/(\d+)",
    re.I,
)
TWITTER_EPOCH_MS = 1288834974657
# Inclusive UTC window: 4 Sep through today.
DATE_START = "2026-09-04"
DATE_END = "2026-09-06"
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
    "OP12-061",
    "OP15-002",
    "OP16-079",
    "OP11-001",
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

# Public creator accounts that actually post OPTCG content.
HANDLES = [
    "MarinefordTCG",
    "StrawHatPecan",
    "BenSchumi7",
    "CardKaizoku",
    "BlaisePlays",
    "BlaisePlaysTCG",
    "NightingaleTCG",
    "michaelartress",
    "ONEPIECE_tcg_EN",
    "Silvers_D_Foxy",
    "LimitlessTCG",
    "OPtopdecks",
    "OPTCGAlert",
    "The_Egman",
    "Yonxlj",
    "KuroKumaTCG",
    "Chinoize_",
    "sormiltcg",
    "EgmanEvents",
    "JohnnyTCG",
    "CapiamoOP",
    "LeeZ_1111",
    "NBAPR",
    "BCGFest",
    "BandaiTCG",
    "BandaiCardGames",
]
HANDLE_SET = {h.lower() for h in HANDLES}

# Known public tweet IDs (FxTwitter can fetch these even when timelines 403).
SEED_TWEETS = {
    "2090634341244432826": "OPtopdecks",
    "2090450093782532258": "OPTCGAlert",
    "2090197490913902734": "Silvers_D_Foxy",
    "2089838271522320522": "The_Egman",
    "2089835508901810310": "Chinoize_",
    "2089448508684189741": "MarinefordTCG",
    "2088771006592663815": "MarinefordTCG",
    "2089597170316144997": "cardkaizoku",
    "2089491621176029306": "cardkaizoku",
    "2088505853402108192": "cardkaizoku",
    "2088365415928127503": "cardkaizoku",
    "2086926321696076196": "cardkaizoku",
    "2086756739634909242": "Yonxlj",
    "2086495197781770492": "Yonxlj",
    "2084950563146330449": "Yonxlj",
    "2084578215536816418": "KuroKumaTCG",
    "2088502410603815064": "ALA9250",
    "2088039197521408457": "EgmanEvents",
    "2089403698724184399": "NBAPR",
    "2076068504843735235": "sormiltcg",
}

SEARCHES = [
    f'site:x.com "4xOP17" since:{DATE_START}',
    f'site:x.com "1xOP17-001" since:{DATE_START}',
    f'site:x.com "1xOP17-039" since:{DATE_START}',
    f'site:x.com "1xOP17-079" since:{DATE_START}',
    f'site:x.com "1xOP11-040" since:{DATE_START}',
    f'site:x.com "1xOP08-058" since:{DATE_START}',
    f'site:x.com "1xOP16-001" since:{DATE_START}',
    f"site:x.com OP17 decklist since:{DATE_START}",
    f"site:x.com OPTCG decklist since:{DATE_START}",
    f"site:x.com ChinoizeCup since:{DATE_START}",
    f"site:x.com The_Egman decklist since:{DATE_START}",
    f"site:x.com Yonxlj deck-list since:{DATE_START}",
    f"site:x.com MarinefordTCG since:{DATE_START}",
    f"site:x.com CardKaizoku since:{DATE_START}",
    f"site:x.com ChinoizeCup #103 since:{DATE_START}",
    f"site:x.com ChinoizeCup #102 since:{DATE_START}",
    f"site:x.com NightingaleTCG decklist since:{DATE_START}",
    f"site:x.com StrawHatPecan decklist since:{DATE_START}",
    f"site:x.com BlaisePlays decklist since:{DATE_START}",
    'site:x.com "4xOP17"',
    'site:twitter.com "4xOP17-040"',
    "site:x.com ChinoizeCup #101 Winner",
    "site:x.com ChinoizeCup #100 Winner",
    "site:x.com ワンピカード デッキ since:2026-09-04",
    f"site:x.com Flame Flame decklist since:{DATE_START}",
    f'site:x.com "Flame-Flame Fruit" Utrecht since:{DATE_START}',
    f"site:x.com BCG Fest Utrecht decklist since:{DATE_START}",
    f"site:x.com Flame Flame Winner Robin since:{DATE_START}",
    f'site:x.com "4xOP17" since:{DATE_START}',
    "site:x.com ワンピカード 優勝 デッキ since:2026-09-04",
    "site:x.com 紫黄ロビン デッキ since:2026-09-04",
]


def log(*args) -> None:
    print(*args, flush=True)


def snowflake_to_date(sid: str) -> str:
    try:
        ms = (int(sid) >> 22) + TWITTER_EPOCH_MS
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


def in_window(day: str) -> bool:
    return bool(day) and DATE_START <= day[:10] <= DATE_END


def fetch(url: str, timeout: int = 10) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/json,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, body
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def fetch_bytes(url: str, timeout: int = 12) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read() if exc.fp else b""
        return exc.code, body
    except Exception:  # noqa: BLE001
        return 0, b""


def card_hits(text: str) -> list[tuple[int, str]]:
    return [(int(n), cid.upper()) for n, cid in LINE_RE.findall(text or "")]


def complete_lists(hits: list[tuple[int, str]]) -> list[dict]:
    if not hits:
        return []
    chunks: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for count, cid in hits:
        if count == 1 and cid in LEADERS and current:
            chunks.append(current)
            current = []
        current.append((count, cid))
    if current:
        chunks.append(current)
    out = []
    for chunk in chunks:
        leader = chunk[0][1] if chunk[0][1] in LEADERS else None
        main = chunk[1:] if leader else chunk
        total = sum(c for c, _ in main)
        if leader and 46 <= total <= 52:
            out.append(
                {
                    "leader": leader,
                    "cards": total,
                    "raw": " ".join(f"{c}x{i}" for c, i in chunk),
                }
            )
    return out


def extract_status_ids(text: str) -> list[tuple[str, str]]:
    found = []
    seen: set[tuple[str, str]] = set()
    for handle, sid in STATUS_RE.findall(text or ""):
        key = (handle, sid)
        if key not in seen:
            seen.add(key)
            found.append((handle, sid))
    return found


def tweet_blob(data: dict) -> str:
    tweet = data.get("tweet") or data
    parts = [tweet.get("text") or "", json.dumps(tweet.get("raw_text") or "")]
    media = tweet.get("media") or {}
    if isinstance(media, dict):
        for photo in media.get("photos") or []:
            if isinstance(photo, dict):
                parts.append(photo.get("altText") or photo.get("alt") or "")
                parts.append(photo.get("url") or "")
        for item in media.get("all") or []:
            if isinstance(item, dict):
                parts.append(item.get("altText") or "")
    quote = tweet.get("quote") or {}
    if isinstance(quote, dict):
        parts.append(quote.get("text") or "")
    return "\n".join(str(p) for p in parts)


def photo_urls(tweet: dict) -> list[str]:
    media = tweet.get("media") or {}
    urls: list[str] = []
    if not isinstance(media, dict):
        return urls
    for photo in media.get("photos") or []:
        if isinstance(photo, dict) and photo.get("url"):
            urls.append(photo["url"])
    return urls


def created_day(tweet: dict, sid: str) -> str:
    created = tweet.get("created_at") or tweet.get("date") or tweet.get("created_timestamp") or ""
    created_s = str(created)
    if re.match(r"\d{4}-\d{2}-\d{2}", created_s):
        return created_s[:10]
    if created_s.isdigit() and len(created_s) >= 10:
        try:
            return datetime.fromtimestamp(int(created_s[:10]), tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, ValueError, OverflowError):
            pass
    parsed = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}).+(\d{4})", created_s)
    if parsed:
        try:
            dt = datetime.strptime(f"{parsed.group(1)} {parsed.group(2)} {parsed.group(3)}", "%b %d %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return snowflake_to_date(sid)


def main() -> None:
    out: dict = {
        "window": {"start": DATE_START, "end": DATE_END, "tz": "UTC"},
        "profiles": [],
        "searches": [],
        "tweets": [],
        "in_window_tweets": [],
        "in_window_photos": [],
        "complete_lists": [],
        "partial_id_hits": [],
        "photo_only_outside_window": [],
        "notes": [],
    }
    status_ids = dict(SEED_TWEETS)

    for handle in HANDLES:
        url = f"https://r.jina.ai/https://x.com/{handle}"
        status, body = fetch(url, timeout=18)
        ids = extract_status_ids(body)
        hits = card_hits(body)
        lists = complete_lists(hits)
        row = {
            "handle": handle,
            "url": url,
            "status": status,
            "chars": len(body),
            "tweet_ids": [f"{h}/{s}" for h, s in ids],
            "card_lines": len(hits),
            "complete_lists": len(lists),
            "note": body[:120] if status in (0, 401, 403, 503) else "",
        }
        kept = [(h, s) for h, s in ids if h.lower() in HANDLE_SET or h.lower() == handle.lower()]
        row["tweet_ids"] = [f"{h}/{s}" for h, s in kept]
        out["profiles"].append(row)
        log("profile", status, len(kept), "ids", handle)
        for h, sid in kept:
            status_ids.setdefault(sid, h)
        out["complete_lists"].extend({"source": url, **item} for item in lists)
        if hits and not lists:
            out["partial_id_hits"].append({"source": url, "hits": hits[:40]})

    extra_urls = []
    for q in SEARCHES:
        extra_urls.append(
            ("ddg", q, "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q}))
        )
    for q in SEARCHES[:6]:
        extra_urls.append(
            ("bing", q, "https://www.bing.com/search?" + urllib.parse.urlencode({"q": q}))
        )
        extra_urls.append(
            (
                "jina-google",
                q,
                "https://r.jina.ai/http://www.google.com/search?" + urllib.parse.urlencode({"q": q}),
            )
        )
    for handle in ("Chinoize_", "MarinefordTCG", "NightingaleTCG", "The_Egman", "CardKaizoku"):
        extra_urls.append(("fx-user", handle, f"https://api.fxtwitter.com/{handle}"))
        extra_urls.append(("xcancel", handle, f"https://xcancel.com/{handle}"))
    extra_urls.extend(
        [
            ("yt-desc", "Iy8USsETmBk", "https://www.youtube.com/watch?v=Iy8USsETmBk"),
            ("yt-desc", "x1bRKDLBD28", "https://www.youtube.com/watch?v=x1bRKDLBD28"),
            ("yt-desc", "-8n9oqREEYE", "https://www.youtube.com/watch?v=-8n9oqREEYE"),
        ]
    )

    for kind, q, url in extra_urls:
        status, body = fetch(url, timeout=14)
        ids = extract_status_ids(body)
        # also catch bare status IDs next to handles in JSON/HTML
        for sid in re.findall(r"/status(?:es)?/(\d{15,20})", body or ""):
            handle_m = re.search(
                rf"([A-Za-z0-9_]{{2,20}})/status(?:es)?/{sid}", body or "", re.I
            )
            ids.append((handle_m.group(1) if handle_m else "unknown", sid))
        hits = card_hits(body)
        lists = complete_lists(hits)
        row = {
            "kind": kind,
            "query": q,
            "status": status,
            "chars": len(body),
            "tweet_ids": [f"{h}/{s}" for h, s in ids][:20],
            "card_lines": len(hits),
            "complete_lists": len(lists),
        }
        out["searches"].append(row)
        log("search", kind, status, len(ids), "ids", len(hits), "lines", str(q)[:40])
        for h, sid in ids:
            if h and h.lower() != "unknown":
                status_ids.setdefault(sid, h)
            else:
                status_ids.setdefault(sid, status_ids.get(sid, "unknown"))
        out["complete_lists"].extend({"source": q, **item} for item in lists)
        if hits:
            out["partial_id_hits"].append({"source": f"{kind}:{q}", "hits": hits[:12]})
        time.sleep(0.08)

    log("unique tweet ids", len(status_ids))
    media_dir = ROOT / "data/x-media"
    for sid, handle in status_ids.items():
        url = f"https://api.fxtwitter.com/{handle}/status/{sid}"
        status, body = fetch(url, timeout=12)
        data = {}
        try:
            data = json.loads(body) if body.lstrip().startswith("{") else {}
        except json.JSONDecodeError:
            data = {}
        blob = tweet_blob(data) if data else body
        hits = card_hits(blob)
        lists = complete_lists(hits)
        tweet = (data.get("tweet") or {}) if isinstance(data, dict) else {}
        day = created_day(tweet, sid)
        photos = photo_urls(tweet)
        row = {
            "handle": handle,
            "id": sid,
            "url": f"https://x.com/{handle}/status/{sid}",
            "http": status,
            "text": (tweet.get("text") or "")[:400],
            "created": day,
            "in_window": in_window(day),
            "card_lines": len(hits),
            "complete_lists": len(lists),
            "photos": photos,
        }
        log(
            "tweet",
            status,
            handle,
            sid,
            day,
            "window" if row["in_window"] else "old",
            "lines",
            len(hits),
            "pics",
            len(photos),
            (tweet.get("text") or "")[:72].replace("\n", " "),
        )
        text_l = (tweet.get("text") or "").lower()
        if handle.lower() not in HANDLE_SET and not hits and not photos:
            continue
        if (
            handle.lower() == "silvers_d_foxy"
            and "op17" not in text_l
            and "one piece" not in text_l
            and "optcg" not in text_l
        ):
            continue
        out["tweets"].append(row)
        if row["in_window"]:
            out["in_window_tweets"].append(row)
            for i, purl in enumerate(photos):
                st2, blob_b = fetch_bytes(purl)
                saved = ""
                if st2 == 200 and blob_b:
                    media_dir.mkdir(parents=True, exist_ok=True)
                    dest = media_dir / f"{handle}-{sid}-{i}.jpg"
                    dest.write_bytes(blob_b)
                    saved = str(dest)
                out["in_window_photos"].append(
                    {
                        "handle": handle,
                        "id": sid,
                        "url": row["url"],
                        "created": day,
                        "photo": purl,
                        "saved": saved,
                        "bytes": len(blob_b) if blob_b else 0,
                    }
                )
            out["complete_lists"].extend(
                {"source": row["url"], "handle": handle, "date": day, **item} for item in lists
            )
        elif photos and ("deck" in text_l or "list" in text_l or hits):
            out["photo_only_outside_window"].append(
                {
                    "handle": handle,
                    "id": sid,
                    "url": row["url"],
                    "created": day,
                    "photos": len(photos),
                    "text": (tweet.get("text") or "")[:180],
                }
            )
        if hits and not lists:
            out["partial_id_hits"].append({"source": row["url"], "hits": hits, "created": day})
        time.sleep(0.15)

    if not out["complete_lists"]:
        out["notes"].append(
            f"No complete 50-card NxSET-NNN lists on public X posts dated {DATE_START}–{DATE_END} UTC. "
            "Jina reader is blocked on x.com (403 AbuseAlleviationError). FxTwitter returns individual "
            "tweets when an ID is known, but not user timelines. DuckDuckGo site:x.com often 202s or "
            "returns older tweets that ignore since:. Nitter/xcancel/syndication/RSSHub did not yield "
            "timelines. List photos that *are* public (The_Egman 2089838271522320522 on 2026-08-18, "
            "Yonxlj Ace 2086756739634909242 on 2026-08-10, KuroKumaTCG Rocks 2084578215536816418 on "
            "2026-08-04) are outside the two-day window and were not hosted."
        )
    if not out["in_window_tweets"]:
        out["notes"].append(
            "Zero in-window tweet IDs were discovered. ChinoizeCup #101 (Limitless, 2026-08-25) and "
            "#100 (2026-08-24) almost certainly have winner posts on @Chinoize_, but those status IDs "
            "are not in public search indexes from this environment."
        )

    path = ROOT / "data/x-search-log.json"
    if path.exists():
        try:
            prev = json.loads(path.read_text())
        except json.JSONDecodeError:
            prev = {}
        if prev.get("hosted") and not out.get("hosted"):
            out["hosted"] = prev["hosted"]
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    log("in-window tweets", len(out["in_window_tweets"]))
    log("in-window photos", len(out["in_window_photos"]))
    log("complete X lists found", len(out["complete_lists"]))
    log("wrote", path)


if __name__ == "__main__":
    sys.exit(main() or 0)
