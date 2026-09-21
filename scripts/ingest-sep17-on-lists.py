#!/usr/bin/env python3
"""Host complete 50-card lists dated 2026-09-17 through today (UTC).

Prioritizes Dallas Flame-Flame Fruit Coliseum NA Block A–D, then Dallas
Championship Finals, then every other public 9/17+ list. Sources: OPTCG.GG,
OPDeckGuide, OnePieceDB, Limitless, TCG PORTAL, Reddit, and public X posts.
Only writes a page when the source is 1 hosted leader + 46–52 cards with no
bans. Does not invent cards from photos. Does not wipe existing list pages.
Does not label Europe Utrecht Flame-Flame as Dallas.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import traceback
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
SINCE = "2026-09-17"
UNTIL = date.today().isoformat()
AMAZING_SINCE = "2026-09-01"
FLAME_NA_RE = re.compile(
    r"flame[\s-]*flame.*(?:\bna\b|north america|dallas)|(?:\bna\b|dallas).*flame",
    re.I,
)
DALLAS_EVENT_RE = re.compile(r"dallas", re.I)
EUROPE_FLAME_RE = re.compile(
    r"flame[\s-]*flame.*europe|europe.*flame[\s-]*flame|utrecht|jaarbeurs",
    re.I,
)


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def dated(item: dict) -> bool:
    return in_window(item.get("date") or "")


def event_priority(event: str) -> int:
    name = event or ""
    if EUROPE_FLAME_RE.search(name):
        return 99
    if FLAME_NA_RE.search(name):
        return 0
    if DALLAS_EVENT_RE.search(name):
        return 1
    return 2


def safe_collect(label: str, fn) -> list:
    try:
        rows = list(fn() or [])
        print(label, "ok", len(rows), flush=True)
        return rows
    except Exception as exc:  # noqa: BLE001
        print(label, "FAIL", type(exc).__name__, exc, flush=True)
        traceback.print_exc()
        return []


def collect_optcg_window(gen, commsrc, optcggg) -> list[dict]:
    """Fetch every complete 9/17+ OPTCG.GG list, Flame NA first."""
    hosted = {L["id"] for L in gen.LEADERS}
    seen_keys, seen_urls = optcggg.existing_index(gen)
    found: list[dict] = []
    seen: set[str] = set()
    per_event: dict[str, int] = {}
    listings: list[dict] = []
    stop_old = 0
    print("=== OPTCG.GG listings", SINCE, "to", UNTIL, "===", flush=True)
    for page in range(1, 25):
        data = optcggg.get_json(f"{optcggg.API}/paginated?page={page}&page_size=20")
        batch = data.get("decklists") or []
        print("optcg.gg page", page, "batch", len(batch), "listed", len(listings), flush=True)
        if not batch:
            break
        page_old = 0
        for row in batch:
            day = (row.get("event_date") or "")[:10]
            event = row.get("event_name") or "OPTCG.GG event"
            if day and day < SINCE:
                page_old += 1
                continue
            if not in_window(day):
                continue
            if EUROPE_FLAME_RE.search(event) or optcggg.SKIP_EVENT_RE.search(event):
                continue
            if not row.get("id"):
                continue
            listings.append(row)
        if page_old:
            stop_old += 1
        if stop_old >= 2:
            break
        time.sleep(0.08)

    listings.sort(key=lambda row: (event_priority(row.get("event_name") or ""), (row.get("placement") or 99), row.get("player") or ""))
    print(
        "optcg.gg listings in window",
        len(listings),
        "flame",
        sum(1 for row in listings if event_priority(row.get("event_name") or "") == 0),
        "dallas",
        sum(1 for row in listings if event_priority(row.get("event_name") or "") == 1),
        flush=True,
    )

    fetched = 0
    for row in listings:
        event = row.get("event_name") or "OPTCG.GG event"
        pri = event_priority(event)
        if pri > 1 and per_event.get(event, 0) >= 80:
            continue
        did = row.get("id") or ""
        day = (row.get("event_date") or "")[:10]
        source_url = f"{optcggg.SITE}/{did}".rstrip("/")
        if source_url in seen_urls:
            continue
        fetched += 1
        try:
            deck = optcggg.get_json(f"{optcggg.API}/{did}")
        except Exception as exc:  # noqa: BLE001
            print("fail", did, exc, flush=True)
            time.sleep(0.12)
            continue
        counts = optcggg.counts_from_deck(deck)
        lid = optcggg.leader_id(row, counts, hosted)
        main_n = sum(n for cid, n in counts.items() if cid != lid) if lid else 0
        banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
        player = (row.get("player") or "Unknown").strip() or "Unknown"
        print(event, player, lid or "-", "cards", main_n, "banned", banned, flush=True)
        if not lid or counts.get(lid) != 1 or banned:
            time.sleep(0.1)
            continue
        if not commsrc.complete(counts, lid):
            time.sleep(0.1)
            continue
        key = (lid, gen.slugify(player), day)
        if key in seen_keys or source_url in seen_urls:
            print("skip dup", player, lid, day, flush=True)
            time.sleep(0.1)
            continue
        place = row.get("placement")
        if isinstance(place, int) and place > 0:
            place_bit = gen.ordinal(place)
            title = f"{player} {place_bit} - {event}"
        else:
            place_bit = "list"
            title = f"{player} - {event}"
        item = {
            "leader": lid,
            "kind": "web",
            "player": player,
            "title": title,
            "subtitle": f"Public OPTCG.GG list · {event} · {day}",
            "source_url": source_url,
            "slug": gen.slugify(f"optcggg-{place_bit}-{player}-{event}")[:70],
            "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
            "cards": main_n,
            "date": day,
            "priority": pri,
        }
        before = len(found)
        commsrc.record(found, item, seen)
        if len(found) > before:
            seen_keys.add(key)
            seen_urls.add(source_url)
            per_event[event] = per_event.get(event, 0) + 1
        time.sleep(0.1)

    log_path = ROOT / "data/optcggg-sep17-log.json"
    log_path.write_text(
        json.dumps(
            {
                "window": {"start": SINCE, "end": UNTIL},
                "listed": len(listings),
                "fetched": fetched,
                "hosted": found,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print("optcg.gg ready", len(found), "fetched", fetched, "log", log_path, flush=True)
    return found


def list_rels_from_run(found: list[dict], gen, before: dict, index: dict) -> list[str]:
    by_id = {L["id"]: L for L in gen.LEADERS}
    rels: list[str] = []
    seen: set[str] = set()

    def add(rel: str) -> None:
        if rel in seen:
            return
        if (ROOT / rel).exists():
            seen.add(rel)
            rels.append(rel)

    for item in found:
        leader = by_id.get(item.get("leader") or "")
        slug = item.get("slug")
        if leader and slug:
            add(f"{leader['dir']}/{slug}.html")
    for lid, rows in index.items():
        leader = by_id.get(lid)
        if not leader:
            continue
        old_n = before.get(lid, 0)
        for row in (rows or [])[old_n:]:
            slug = row.get("slug")
            if slug:
                add(f"{leader['dir']}/{slug}.html")
    return rels


def update_sitemaps(new_rels: list[str]) -> None:
    today = date.today().isoformat()
    lists_path = ROOT / "sitemap-lists.xml"
    text = lists_path.read_text()
    existing = set(re.findall(r"<loc>([^<]+)</loc>", text))
    rows = []
    for rel in new_rels:
        loc = f"{SITE}/{rel}"
        if loc not in existing:
            rows.append(f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n")
    if rows:
        text = text.replace("</urlset>", "".join(rows) + "</urlset>")
        if not text.endswith("\n"):
            text += "\n"
        lists_path.write_text(text)
    print("sitemap-lists added", len(rows), flush=True)

    hubs = {f"{SITE}/", f"{SITE}/tier-list.html", f"{SITE}/recent.html"}
    for rel in new_rels:
        hub = str(Path(rel).parent) + ".html"
        hubs.add(f"{SITE}/{hub}")
    core_path = ROOT / "sitemap-core.xml"
    core = core_path.read_text()
    for loc in sorted(hubs):
        core = re.sub(
            rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+",
            rf"\g<1>{today}",
            core,
        )
    core_path.write_text(core)

    idx_path = ROOT / "sitemap.xml"
    idx = idx_path.read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx_path.write_text(idx)
    print("sitemap lastmod", today, "hubs", len(hubs), flush=True)


def bump_asset_versions() -> None:
    css_old = re.compile(r'href="/css/site\.css(?:\?[^"]*)?"')
    js_old = re.compile(r'src="/js/site\.js(?:\?[^"]*)?"')
    skip = {".git", "scripts", "node_modules", "discord-bot", "ballkeep"}
    n = 0
    for path in ROOT.rglob("*.html"):
        if any(part in path.parts for part in skip):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        next_text = css_old.sub('href="/css/site.css?v=home-pro18"', text)
        next_text = js_old.sub('src="/js/site.js?v=home-smooth"', next_text)
        if next_text != text:
            path.write_text(next_text)
            n += 1
    print("asset versions bumped", n, flush=True)


def reddit_window(hunt, commsrc) -> list[dict]:
    start = datetime.combine(date.fromisoformat(SINCE), datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(date.fromisoformat(UNTIL) + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    after = int(start.timestamp())
    before = int(end.timestamp())
    found: list[dict] = []
    seen: set[str] = set()
    endpoints = [
        (
            "https://arctic-shift.photon-reddit.com/api/posts/search?"
            + urllib.parse.urlencode(
                {"subreddit": "OnePieceTCG", "after": after, "before": before, "limit": 100}
            )
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            + urllib.parse.urlencode(
                {"subreddit": "OnePieceTCG", "after": after, "before": before, "limit": 200}
            )
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            + urllib.parse.urlencode(
                {
                    "q": "Flame Flame OR Dallas OR 4xOP17 OR decklist",
                    "subreddit": "OnePieceTCG",
                    "after": after,
                    "before": before,
                    "limit": 100,
                }
            )
        ),
        "https://www.reddit.com/r/OnePieceTCG/new.json?limit=50",
    ]
    for url in endpoints:
        status, body = hunt.fetch(url, timeout=22)
        print("reddit", status, url[:90], "chars", len(body), flush=True)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = data.get("data") or data.get("children") or []
            if isinstance(rows, dict):
                rows = rows.get("children") or []
        else:
            rows = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            post = row.get("data") if isinstance(row.get("data"), dict) else row
            created = post.get("created_utc") or post.get("created") or 0
            try:
                day = datetime.fromtimestamp(float(created), tz=timezone.utc).strftime("%Y-%m-%d")
            except (OSError, ValueError, TypeError, OverflowError):
                day = ""
            if day and not in_window(day):
                continue
            text = "\n".join(str(post.get(k) or "") for k in ("title", "selftext", "body", "permalink", "url"))
            permalink = post.get("permalink") or post.get("id") or url
            counts = commsrc.parse_counts(text)
            lid = commsrc.leader_of(counts)
            if not lid or not commsrc.complete(counts, lid):
                continue
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            item = {
                "leader": lid,
                "kind": "web",
                "player": "Reddit",
                "title": f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} Reddit list",
                "subtitle": f"Public r/OnePieceTCG list · {day or 'date unknown'}",
                "source_url": (
                    permalink if str(permalink).startswith("http") else "https://www.reddit.com" + str(permalink)
                ),
                "slug": commsrc.slug_for("reddit", "onepiecetcg", str(permalink))[:70],
                "raw": raw,
                "cards": sum(n for cid, n in counts.items() if cid != lid),
            }
            if day:
                item["date"] = day
                commsrc.record(found, item, seen)
        time.sleep(0.15)
    return found


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
    hunt = load("hunt", "/workspace/scripts/hunt-window-lists.py")
    xmod = load("xlists", "/workspace/scripts/scrape-x-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")

    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    xmod.DATE_START = SINCE
    xmod.DATE_END = UNTIL
    portal.SINCE = SINCE
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL
    optcggg.PER_EVENT = 99
    optcggg.TARGET = 500
    optcggg.DETAIL_CAP = 800
    optcggg.MAX_PAGES = 24
    found: list[dict] = []
    seen: set[str] = set()

    print("=== window", SINCE, "to", UNTIL, "===", flush=True)

    print("=== OPTCG.GG Flame NA first, then 9/17+ ===", flush=True)
    for item in safe_collect("optcg.gg", lambda: collect_optcg_window(gen, commsrc, optcggg)):
        commsrc.record(found, item, seen)

    print("=== OPDeckGuide ===", flush=True)
    for item in safe_collect("opdeck", lambda: hunt.opdeck_items(opdeck, commsrc)):
        if dated(item):
            commsrc.record(found, item, seen)
        else:
            print("skip old opdeck", item.get("slug"), item.get("date"), flush=True)

    print("=== Reddit ===", flush=True)
    found.extend(reddit_window(hunt, commsrc))

    print("=== TCG PORTAL ===", flush=True)
    for item in safe_collect("portal", lambda: portal.collect_lists(gen, commsrc)):
        if dated(item):
            commsrc.record(found, item, seen)
        else:
            print("skip old portal", item.get("slug"), item.get("date"), flush=True)

    print("=== OnePieceDB ===", flush=True)
    for item in safe_collect("opdb", lambda: opdb.collect_lists(gen, commsrc)):
        if dated(item) or not item.get("date"):
            commsrc.record(found, item, seen)
        else:
            print("skip old opdb", item.get("slug"), item.get("date"), flush=True)

    print("=== X ===", flush=True)
    try:
        xmod.main()
    except Exception as exc:  # noqa: BLE001
        print("x scrape FAIL", type(exc).__name__, exc, flush=True)
        traceback.print_exc()
    log_path = ROOT / "data/x-search-log.json"
    if log_path.exists():
        data = json.loads(log_path.read_text())
        for item in data.get("complete_lists") or []:
            raw = item.get("raw") or ""
            counts = commsrc.parse_counts(raw)
            lid = item.get("leader") or commsrc.leader_of(counts)
            if lid not in commsrc.TARGET_IDS or not commsrc.complete(counts, lid):
                continue
            day = (item.get("date") or "")[:10]
            if day and not in_window(day):
                print("skip old x", item.get("handle"), day, flush=True)
                continue
            if not day:
                continue
            handle = item.get("handle") or "x"
            url = item.get("source") or item.get("url") or f"https://x.com/{handle}"
            blob = f"{item.get('text') or ''} {handle} {url}"
            if EUROPE_FLAME_RE.search(blob) and not DALLAS_EVENT_RE.search(blob):
                print("skip europe x", handle, day, flush=True)
                continue
            commsrc.record(
                found,
                {
                    "leader": lid,
                    "kind": "x",
                    "player": handle,
                    "title": f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} - @{handle}",
                    "subtitle": f"List copied from a public X/Twitter post · {day}",
                    "source_url": url if str(url).startswith("http") else f"https://x.com/{handle}",
                    "slug": commsrc.slug_for("x", handle, commsrc.TARGET_IDS[lid] + raw[-12:]),
                    "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                    "cards": sum(n for cid, n in counts.items() if cid != lid),
                    "date": day,
                },
                seen,
            )

    print("=== write community lists ===", flush=True)
    (ROOT / "data/sep17-on-community-log.json").write_text(
        json.dumps({"found": found, "window": {"start": SINCE, "end": UNTIL}}, indent=2, ensure_ascii=False)
        + "\n"
    )
    print("community complete lists", len(found), flush=True)
    commsrc.write_lists(found)

    print("=== Limitless Play recent", SINCE, "to", UNTIL, "===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in {L["id"] for L in gen.LEADERS}}
    index = more.fetch_more(
        index,
        pages=12,
        extra_limit=400,
        per_event=99,
        since=SINCE,
        until=UNTIL,
    )
    more.save_index(index)
    after_recent = {lid: len(index.get(lid) or []) for lid in before}
    limitless_recent = sum(after_recent[lid] - before[lid] for lid in before)
    print("limitless recent rows", limitless_recent, flush=True)

    print("=== Limitless Play amazing top cuts", AMAZING_SINCE, "to", UNTIL, "===", flush=True)
    mid = {lid: len(index.get(lid) or []) for lid in before}
    index = more.fetch_more(
        index,
        pages=16,
        extra_limit=220,
        per_event=12,
        since=AMAZING_SINCE,
        until=UNTIL,
        max_placing=8,
    )
    more.save_index(index)
    after = {lid: len(index.get(lid) or []) for lid in before}
    limitless_amazing = sum(after[lid] - mid[lid] for lid in before)
    limitless_new = sum(after[lid] - before[lid] for lid in before)
    print("limitless amazing rows", limitless_amazing, "total new", limitless_new, flush=True)

    print("=== rebuild hubs / consensus / homepage pie / tier list ===", flush=True)
    more.rebuild_hubs(index)
    analysis.main()
    tier.main()
    up.patch_home()
    bump_asset_versions()
    new_rels = list_rels_from_run(found, gen, before, index)
    update_sitemaps(new_rels)

    flame_n = sum(1 for item in found if event_priority(item.get("title") or item.get("subtitle") or "") == 0)
    dallas_n = sum(1 for item in found if event_priority(item.get("title") or item.get("subtitle") or "") == 1)
    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "amazing_window": {"start": AMAZING_SINCE, "end": UNTIL},
        "community_found": len(found),
        "flame_na_found": flame_n,
        "dallas_finals_found": dallas_n,
        "community_slugs": [item.get("slug") for item in found],
        "limitless_recent_index_rows": limitless_recent,
        "limitless_amazing_index_rows": limitless_amazing,
        "limitless_new_index_rows": limitless_new,
        "sitemap_list_urls": new_rels,
    }
    (ROOT / "data/sep17-on-ingest-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("ingest summary", json.dumps(summary), flush=True)
    print("sep17-on ingest done", flush=True)


if __name__ == "__main__":
    main()
