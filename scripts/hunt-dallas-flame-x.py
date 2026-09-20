#!/usr/bin/env python3
"""Hunt public Dallas Flame-Flame Fruit Coliseum lists and host complete 50s.

Meticulous X/search pass for BCG Fest Dallas (19-20 Sep 2026). Only writes a
page when the source is 1 hosted leader + 50 cards with no bans. Skips Europe
Utrecht Flame-Flame lists. Does not invent cards from photos. Does not wipe
existing pages.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com; public OPTCG list scrape)"
SINCE = "2026-09-18"
UNTIL = "2026-09-21"
TWITTER_EPOCH_MS = 1288834974657
LINE_RE = re.compile(r"(?i)(\d+)\s*[x×]\s*((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})")
STATUS_RE = re.compile(r"(?:x\.com|twitter\.com)/([A-Za-z0-9_]+)/status/(\d+)", re.I)
EUROPE_RE = re.compile(
    r"utrecht|europe|benjo|xixo\b|world'?s first|block [abcd]\b|jaarbeurs",
    re.I,
)
DALLAS_RE = re.compile(
    r"dallas|bcg fest|bcgfest|north america|kay bailey|play!?\s*tcg",
    re.I,
)
FLAME_RE = re.compile(r"flame[\s-]?flame|coliseum", re.I)

HANDLES = [
    "ONEPIECE_tcg_EN",
    "BandaiTCG",
    "BandaiCardGames",
    "The_Egman",
    "EgmanEvents",
    "CardKaizoku",
    "MarinefordTCG",
    "OPtopdecks",
    "OPTCGAlert",
    "PlayTCGOfficial",
    "JohnnyTCG",
    "StrawHatPecan",
    "Vampyrgaming",
    "felixvp10",
    "PleaseBanYellow",
    "fedemeco_",
    "LukaTCG",
    "RobertoOPTCG",
]

SEED_TWEETS = {
    # Official EN account posts the Europe graphic under this series title;
    # keep the ID so Dallas follow-ups in the same thread are discoverable.
    "2095985462720500200": "ONEPIECE_tcg_EN",
    "2095986697037107308": "ONEPIECE_tcg_EN",
}

QUERIES = [
    'site:x.com Dallas "Flame-Flame" since:2026-09-18',
    'site:x.com Dallas "Flame Flame" since:2026-09-18',
    'site:x.com "Flame-Flame Fruit Coliseum" Dallas',
    'site:x.com "BCG Fest Dallas" decklist',
    'site:x.com "BCG Fest" Dallas winner',
    'site:x.com Dallas OPTCG decklist since:2026-09-18',
    'site:x.com Dallas "top cut" OPTCG',
    'site:x.com from:ONEPIECE_tcg_EN Dallas',
    'site:x.com from:The_Egman Dallas',
    'site:x.com from:CardKaizoku Dallas',
    'site:x.com from:OPtopdecks Dallas',
    'site:x.com from:OPTCGAlert Dallas',
    'site:x.com from:MarinefordTCG Dallas',
    'site:x.com from:felixvp10',
    'site:x.com "Flame-Flame Fruit Coliseum: Decklists"',
    "Dallas Flame-Flame Fruit Coliseum decklist",
    "Dallas Flame Flame Coliseum top 8 decklist",
]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def log(*args) -> None:
    print(*args, flush=True)


def snowflake_day(sid: str) -> str:
    try:
        ms = (int(sid) >> 22) + TWITTER_EPOCH_MS
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


def fetch(url: str, timeout: int = 16) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, body
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def dallas_flame(text: str) -> bool:
    blob = text or ""
    if EUROPE_RE.search(blob) and not DALLAS_RE.search(blob):
        return False
    return bool(DALLAS_RE.search(blob) and FLAME_RE.search(blob))


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    xscrape = load("xscrape", "/workspace/scripts/scrape-x-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
    hosted = {L["id"] for L in gen.LEADERS}

    out = {
        "window": {"start": SINCE, "end": UNTIL},
        "searches": [],
        "profiles": [],
        "pages": [],
        "tweets": [],
        "optcggg": [],
        "hosted": [],
        "notes": [],
    }
    status_ids = dict(SEED_TWEETS)
    found: list[dict] = []
    seen: set[str] = set()

    for q in QUERIES:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
        st, body = fetch(url, 16)
        ids = STATUS_RE.findall(body)
        out["searches"].append({"q": q, "status": st, "chars": len(body), "ids": [f"{h}/{s}" for h, s in ids[:16]]})
        log("ddg", st, len(ids), "ids", q[:64])
        for handle, sid in ids:
            status_ids.setdefault(sid, handle)
        time.sleep(0.15)

    for handle in HANDLES:
        url = f"https://r.jina.ai/https://x.com/{handle}"
        st, body = fetch(url, 18)
        ids = STATUS_RE.findall(body)
        out["profiles"].append({"handle": handle, "status": st, "chars": len(body), "ids": len(ids)})
        log("jina", st, handle, "ids", len(ids))
        for h, sid in ids:
            status_ids.setdefault(sid, h)
        time.sleep(0.12)

    for q in (
        "Dallas Flame since:2026-09-18",
        "from:ONEPIECE_tcg_EN since:2026-09-18",
        '"Flame-Flame Fruit Coliseum: Decklists"',
        "BCG Fest Dallas decklist",
    ):
        url = "https://r.jina.ai/https://x.com/search?q=" + urllib.parse.quote(q) + "&src=typed_query&f=live"
        st, body = fetch(url, 18)
        ids = STATUS_RE.findall(body)
        out["pages"].append({"url": url, "status": st, "chars": len(body), "ids": [f"{h}/{s}" for h, s in ids[:16]]})
        log("jina-search", st, len(ids), "ids", q[:50])
        for handle, sid in ids:
            status_ids.setdefault(sid, handle)
        time.sleep(0.12)

    # OPTCG.GG newest pages: keep only Dallas Flame-Flame.
    for page in range(1, 8):
        st, body = fetch(f"https://www.optcg.gg/api/deck-lists/paginated?page={page}&page_size=40")
        try:
            rows = (json.loads(body).get("decklists") or []) if st == 200 else []
        except json.JSONDecodeError:
            rows = []
        log("optcg.gg", page, st, len(rows))
        for row in rows:
            event = row.get("event_name") or ""
            day = (row.get("event_date") or "")[:10]
            blob = f"{event} {row.get('player') or ''} {day}"
            out["optcggg"].append({"event": event, "date": day, "player": row.get("player"), "dallas_flame": dallas_flame(blob)})
            if not dallas_flame(blob):
                continue
            if day and day < "2026-09-18":
                continue
            did = row.get("id") or ""
            if not did:
                continue
            try:
                deck = optcggg.get_json(f"{optcggg.API}/{did}")
            except Exception as exc:  # noqa: BLE001
                log("optcg detail fail", did, exc)
                continue
            counts = optcggg.counts_from_deck(deck)
            lid = optcggg.leader_id(row, counts, hosted)
            main_n = sum(n for cid, n in counts.items() if cid != lid) if lid else 0
            banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
            player = (row.get("player") or "Unknown").strip() or "Unknown"
            log("optcg dallas?", event, player, lid, "cards", main_n)
            if not lid or counts.get(lid) != 1 or main_n != 50 or banned:
                continue
            commsrc.record(
                found,
                {
                    "leader": lid,
                    "kind": "web",
                    "player": player,
                    "title": f"{player} - {event}",
                    "subtitle": f"Public OPTCG.GG list · {event} · {day}",
                    "source_url": f"{optcggg.SITE}/{did}",
                    "slug": gen.slugify(f"optcggg-{gen.ordinal(row.get('placement')) if isinstance(row.get('placement'), int) else 'list'}-{player}-{event}")[:70],
                    "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                    "cards": main_n,
                    "date": day,
                },
                seen,
            )
        time.sleep(0.08)

    # OnePieceDB newest titles.
    try:
        opdb_body = opdb.fetch("https://onepiecedb.io/deck-search?sort=Newest")
        for href, name in re.findall(
            r'href="(https://onepiecedb\.io/deck/[^"]+)"[^>]*>([^<]{0,160})', opdb_body
        ):
            blob = f"{href} {name}"
            if dallas_flame(blob) or DALLAS_RE.search(blob):
                out["notes"].append({"opdb": href, "name": name.strip()[:120]})
    except Exception as exc:  # noqa: BLE001
        log("opdb fail", exc)

    # Reddit.
    st, red = fetch("https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=OnePieceTCG&limit=80")
    try:
        posts = json.loads(red).get("data") or []
    except json.JSONDecodeError:
        posts = []
    for post in posts:
        title = post.get("title") or ""
        selftext = post.get("selftext") or ""
        blob = f"{title}\n{selftext}"
        if not (DALLAS_RE.search(blob) or FLAME_RE.search(blob)):
            continue
        created = post.get("created_utc") or 0
        try:
            day = datetime.fromtimestamp(int(created), tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, ValueError, TypeError):
            day = ""
        permalink = post.get("permalink") or ""
        out["notes"].append({"reddit": title[:160], "date": day, "dallas_flame": dallas_flame(blob)})
        hits = xscrape.card_hits(blob)
        lists = xscrape.complete_lists(hits)
        if dallas_flame(blob) and lists and in_window(day):
            for item in lists:
                commsrc.record(
                    found,
                    {
                        "leader": item["leader"],
                        "kind": "reddit",
                        "player": post.get("author") or "Reddit",
                        "title": title[:90] or "Dallas Flame-Flame Reddit list",
                        "subtitle": f"Public r/OnePieceTCG list · {day}",
                        "source_url": f"https://www.reddit.com{permalink}",
                        "slug": gen.slugify(f"reddit-dallas-flame-{post.get('id')}-{item['leader']}")[:70],
                        "raw": item["raw"],
                        "cards": item["cards"],
                        "date": day,
                    },
                    seen,
                )

    log("unique tweet ids", len(status_ids))
    for sid, handle in status_ids.items():
        url = f"https://api.fxtwitter.com/{handle}/status/{sid}"
        st, body = fetch(url, 12)
        data = {}
        try:
            data = json.loads(body) if body.lstrip().startswith("{") else {}
        except json.JSONDecodeError:
            data = {}
        tweet = (data.get("tweet") or {}) if isinstance(data, dict) else {}
        day = xscrape.created_day(tweet, sid) or snowflake_day(sid)
        text = tweet.get("text") or ""
        blob = xscrape.tweet_blob(data) if data else body
        hits = xscrape.card_hits(blob)
        lists = xscrape.complete_lists(hits)
        row = {
            "handle": handle,
            "id": sid,
            "url": f"https://x.com/{handle}/status/{sid}",
            "http": st,
            "created": day,
            "in_window": in_window(day),
            "dallas_flame": dallas_flame(f"{text} {blob}"),
            "europe": bool(EUROPE_RE.search(text)),
            "text": text[:280],
            "photos": xscrape.photo_urls(tweet),
            "complete_lists": len(lists),
        }
        out["tweets"].append(row)
        log(
            "tweet",
            st,
            handle,
            sid,
            day,
            "dallas" if row["dallas_flame"] else ("eu" if row["europe"] else "-"),
            "lists",
            len(lists),
            text[:60].replace("\n", " "),
        )
        if row["dallas_flame"] and lists and (in_window(day) or not row["europe"]):
            if row["europe"] and not in_window(day):
                continue
            for item in lists:
                commsrc.record(
                    found,
                    {
                        "leader": item["leader"],
                        "kind": "x",
                        "player": tweet.get("author", {}).get("name") or handle,
                        "title": f"{handle} - Dallas Flame-Flame Fruit Coliseum",
                        "subtitle": f"List from the public X post · {day}",
                        "source_url": row["url"],
                        "slug": gen.slugify(f"x-dallas-flame-{handle}-{sid}")[:70],
                        "raw": item["raw"],
                        "cards": item["cards"],
                        "date": day,
                    },
                    seen,
                )
        time.sleep(0.08)

    if not found:
        out["notes"].append(
            "No complete 1+50 Dallas Flame-Flame lists were public on X, OPTCG.GG, "
            "OnePieceDB, or r/OnePieceTCG at scrape time. Day 3 finals stream "
            "https://www.youtube.com/watch?v=DLUyxqx8jG0 was live; official EN "
            "decklist graphics for Europe landed the evening of that event and "
            "Dallas lists are expected the same way after the champion is crowned."
        )

    log_path = ROOT / "data/dallas-flame-x-log.json"
    log_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    log("dallas candidates", len(found), "log", log_path)
    touched = commsrc.write_lists(found)
    out["hosted"] = [item["slug"] for item in found]
    log_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    if touched:
        up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
        up.patch_home()
        log("rebuilt home, hubs", sorted(touched))
    print("dallas flame hunt done", flush=True)


if __name__ == "__main__":
    main()
