#!/usr/bin/env python3
"""Host new November 2026 EB-05 constructed lists from public sources.

Only writes 1 leader + 50 main-deck cards with max 4 copies and no bans.
Skips duplicates already in tournament-decks.json / community-decks.json.
Does not invent cards. Failed sources are logged and skipped.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import traceback
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
SINCE = "2026-11-01"
UNTIL = date.today().isoformat()
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"
EB05_MAX = 61
OPLAY = "https://cards.oplaytcg.com/EB05/en/{cid}.webp"
LIMITLESS = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/EB05/{cid}_EN.webp"
BANDAI = "https://en.onepiece-cardgame.com/images/cardlist/card/{cid}.png"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def legal_counts(gen, counts: dict[str, int], lid: str | None) -> bool:
    if not lid or counts.get(lid) != 1:
        return False
    if any(cid in gen.BANNED_CARDS for cid in counts):
        return False
    main = 0
    for cid, n in counts.items():
        if n < 1:
            return False
        if cid == lid:
            if n != 1:
                return False
            continue
        if n > 4:
            return False
        main += n
    return main == 50


def color_key(meta: dict) -> str:
    raw = meta.get("color") or meta.get("colors") or ""
    if isinstance(raw, list):
        parts = [str(c).strip().lower() for c in raw if c]
    else:
        parts = [p.strip().lower() for p in re.split(r"[/,]+", str(raw)) if p.strip()]
    return "color-" + "-".join(parts) if parts else "color-red"


def leader_stub(gen, lid: str, cache: dict) -> dict:
    meta = cache.get(lid) or {}
    name = meta.get("name") or lid
    key = gen.slugify(f"{name}-{lid}")[:40]
    return {
        "id": lid,
        "key": key,
        "page": f"decklists/{key}.html",
        "dir": f"decklists/{key}",
        "name": name,
        "color": color_key(meta),
        "crumb": ["/eb05-lists.html", "EB05 lists"],
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    }


def add_leaders(gen, extra: list[dict], modules: list) -> None:
    known = {L["id"] for L in gen.LEADERS}
    path = ROOT / "data/extra-leaders.json"
    existing = json.loads(path.read_text()) if path.exists() else []
    by_id = {row.get("id"): row for row in existing if row.get("id")}
    for row in extra:
        lid = row["id"]
        by_id[lid] = row
        if lid in known:
            continue
        gen.LEADERS.append(row)
        known.add(lid)
        (ROOT / row["dir"]).mkdir(parents=True, exist_ok=True)
        hub = ROOT / row["page"]
        if not hub.exists():
            cache = gen.ensure_cards({lid}, gen.load_card_cache())
            hub.write_text(gen.render_hub_page(row, cache))
            print("hub", hub, flush=True)
    path.write_text(json.dumps(list(by_id.values()), indent=2, ensure_ascii=False) + "\n")
    for mod in modules:
        g = getattr(mod, "gen", None)
        if g is not None:
            g._load_extra_leaders()
            if hasattr(mod, "TARGET_IDS"):
                for L in g.LEADERS:
                    mod.TARGET_IDS[L["id"]] = L["key"]
        if hasattr(mod, "LEADERS") and g is not None and mod.LEADERS is not g.LEADERS:
            have = {L["id"] for L in mod.LEADERS}
            for L in g.LEADERS:
                if L["id"] not in have:
                    mod.LEADERS.append(L)
        if hasattr(mod, "BY_ID") and g is not None:
            mod.BY_ID = {L["id"]: L for L in g.LEADERS}
        if hasattr(mod, "TARGET_IDS") and g is None:
            for row in extra:
                mod.TARGET_IDS[row["id"]] = row["key"]


def safe_collect(label: str, fn) -> list:
    try:
        rows = list(fn() or [])
        print(label, "ok", len(rows), flush=True)
        return rows
    except Exception as exc:  # noqa: BLE001
        print(label, "FAIL", type(exc).__name__, exc, flush=True)
        traceback.print_exc()
        return []


def download_url(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/webp,image/png,image/*"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
        if not data or len(data) < 400:
            return False
        if "html" in ctype:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:  # noqa: BLE001
        return False


def download_eb05_images() -> dict:
    ids = [f"EB05-{n:03d}" for n in range(1, EB05_MAX + 1)]
    extra_path = ROOT / "scripts/eb05-cards.json"
    if extra_path.exists():
        for row in json.loads(extra_path.read_text()):
            cid = row.get("id")
            if cid and cid not in ids:
                ids.append(cid)
    out_dir = ROOT / "img/cards/EB05"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    failed = []
    for cid in ids:
        dest = out_dir / f"{cid}.webp"
        if dest.exists() and dest.stat().st_size > 400:
            saved += 1
            continue
        ok = False
        for url in (OPLAY.format(cid=cid), LIMITLESS.format(cid=cid)):
            if download_url(url, dest):
                ok = True
                break
        png = out_dir / f"{cid}.png"
        if not ok and download_url(BANDAI.format(cid=cid), png):
            dest.write_bytes(png.read_bytes())
            png.unlink(missing_ok=True)
            ok = dest.exists() and dest.stat().st_size > 400
        if ok:
            saved += 1
        else:
            failed.append(cid)
            print("eb05 image fail", cid, flush=True)
        time.sleep(0.03)
    summary = {"saved": saved, "failed": failed, "ids": len(ids)}
    (ROOT / "data/eb05-image-log.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("eb05 images", summary, flush=True)
    return summary


def discover_nov_leaders(gen) -> list[str]:
    hosted = {L["id"] for L in gen.LEADERS}
    counts: Counter[str] = Counter()
    legal: Counter[str] = Counter()
    for page in range(1, 6):
        rows = gen.http_json(f"https://play.limitlesstcg.com/api/tournaments?game=OP&limit=40&page={page}") or []
        if not rows:
            break
        stop = False
        for tourney in rows:
            day = (tourney.get("date") or "")[:10]
            if day and day < SINCE:
                stop = True
                continue
            if not in_window(day):
                continue
            try:
                standings = gen.http_json(
                    f"https://play.limitlesstcg.com/api/tournaments/{tourney['id']}/standings"
                ) or []
            except Exception as exc:  # noqa: BLE001
                print("standings fail", tourney.get("id"), exc, flush=True)
                continue
            for row in standings:
                dl = row.get("decklist") or {}
                leader = dl.get("leader") or {}
                if not leader.get("set"):
                    continue
                lid = gen.card_id(leader["set"], leader.get("number"))
                counts[lid] += 1
                if gen.deck_is_legal(dl):
                    legal[lid] += 1
        if stop:
            break
    missing = [lid for lid, n in legal.most_common() if lid not in hosted and n > 0]
    print("nov leaders hosted legal", {lid: legal[lid] for lid in hosted if legal[lid]}, flush=True)
    print("nov leaders unhosted legal", {lid: legal[lid] for lid in missing}, flush=True)
    return missing


def reddit_nov(hunt, commsrc) -> list[dict]:
    after = int(datetime(2026, 11, 1, tzinfo=timezone.utc).timestamp())
    before = int(datetime(2026, 11, 9, tzinfo=timezone.utc).timestamp())
    found: list[dict] = []
    seen: set[str] = set()
    urls = [
        (
            "https://arctic-shift.photon-reddit.com/api/posts/search?"
            f"subreddit=OnePieceTCG&after={after}&before={before}&limit=100"
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            f"subreddit=OnePieceTCG&after={after}&before={before}&limit=200"
        ),
        "https://www.reddit.com/r/OnePieceTCG/new.json?limit=50",
    ]
    blobs: list[tuple[str, str, str]] = []
    for url in urls:
        status, body = hunt.fetch(url, timeout=22)
        print("reddit nov", status, url[:90], "chars", len(body), flush=True)
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
            text = "\n".join(str(post.get(k) or "") for k in ("title", "selftext", "body", "permalink", "url"))
            permalink = post.get("permalink") or post.get("id") or url
            blobs.append((str(permalink), day, text))
        time.sleep(0.12)
    for permalink, day, text in blobs:
        if day and not in_window(day):
            continue
        counts = commsrc.parse_counts(text)
        lid = commsrc.leader_of(counts)
        if not legal_counts(gen_mod, counts, lid):
            continue
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        item = {
            "leader": lid,
            "kind": "web",
            "player": "Reddit",
            "title": f"{commsrc.TARGET_IDS.get(lid, lid).replace('-', ' ').title()} Reddit list",
            "subtitle": f"Public r/OnePieceTCG list · {day or 'date unknown'}",
            "source_url": permalink if str(permalink).startswith("http") else "https://www.reddit.com" + str(permalink),
            "slug": commsrc.slug_for("reddit", "onepiecetcg", permalink)[:70],
            "raw": raw,
            "cards": 50,
            "date": day,
        }
        commsrc.record(found, item, seen)
    return found


gen_mod = None


def collect_optcg(gen, commsrc, optcggg) -> list[dict]:
    hosted = {L["id"] for L in gen.LEADERS}
    seen_keys, seen_urls = optcggg.existing_index(gen)
    found: list[dict] = []
    seen: set[str] = set()
    for page in range(1, 12):
        data = optcggg.get_json(f"{optcggg.API}/paginated?page={page}&page_size=20")
        batch = data.get("decklists") or []
        if not batch:
            break
        page_old = 0
        for row in batch:
            day = (row.get("event_date") or "")[:10]
            if day and day < SINCE:
                page_old += 1
                continue
            if not in_window(day):
                continue
            did = row.get("id") or ""
            if not did:
                continue
            source_url = f"{optcggg.SITE}/{did}".rstrip("/")
            if source_url in seen_urls:
                continue
            try:
                deck = optcggg.get_json(f"{optcggg.API}/{did}")
            except Exception as exc:  # noqa: BLE001
                print("optcg fail", did, exc, flush=True)
                time.sleep(0.1)
                continue
            counts = optcggg.counts_from_deck(deck)
            lid = optcggg.leader_id(row, counts, hosted)
            if not legal_counts(gen, counts, lid):
                time.sleep(0.08)
                continue
            player = (row.get("player") or "Unknown").strip() or "Unknown"
            event = row.get("event_name") or "OPTCG.GG event"
            key = (lid, gen.slugify(player), day)
            if key in seen_keys:
                time.sleep(0.08)
                continue
            place = row.get("placement")
            place_bit = gen.ordinal(place) if isinstance(place, int) and place else "list"
            item = {
                "leader": lid,
                "kind": "web",
                "player": player,
                "title": f"{player} - {event}",
                "subtitle": f"Public OPTCG.GG list · {event} · {day}",
                "source_url": source_url,
                "slug": gen.slugify(f"optcggg-{place_bit}-{player}-{event}")[:70],
                "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                "cards": 50,
                "date": day,
                "placing": place if isinstance(place, int) else None,
            }
            before = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before:
                seen_keys.add(key)
                seen_urls.add(source_url)
            time.sleep(0.1)
        if page_old:
            break
        time.sleep(0.08)
    return found


def rewrite_branding() -> None:
    skip = {".git", "scripts", "node_modules", "discord-bot", "ballkeep"}
    n = 0
    css_old = re.compile(r'href="/css/site\.css(?:\?[^"]*)?"')
    js_old = re.compile(r'src="/js/site\.js(?:\?[^"]*)?"')
    oplay = re.compile(r"https://cards\.oplaytcg\.com/EB05/en/(EB05-\d{3})\.webp")
    for path in ROOT.rglob("*.html"):
        if any(part in path.parts for part in skip):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        next_text = text.replace('nav-chip">OP17 Standard', 'nav-chip">EB-05 Meta')
        next_text = next_text.replace(
            '<div class="subtitle">OPTCG decklists</div>',
            '<div class="subtitle">EB-05 Meta</div>',
        )
        next_text = css_old.sub('href="/css/site.css?v=home-banner27"', next_text)
        next_text = js_old.sub('src="/js/site.js?v=banner27"', next_text)

        def local_eb05(match: re.Match) -> str:
            cid = match.group(1)
            local = ROOT / "img" / "cards" / "EB05" / f"{cid}.webp"
            if local.exists():
                return f"/img/cards/EB05/{cid}.webp"
            return match.group(0)

        next_text = oplay.sub(local_eb05, next_text)
        if next_text != text:
            path.write_text(next_text)
            n += 1
    print("branding/html rewrites", n, flush=True)


def main() -> None:
    global gen_mod
    gen = load("genlists", str(ROOT / "scripts/generate-tournament-lists.py"))
    gen_mod = gen
    more = load("morelists", str(ROOT / "scripts/add-more-tournament-lists.py"))
    commsrc = load("commsrc", str(ROOT / "scripts/scrape-community-sources.py"))
    optcggg = load("optcggg", str(ROOT / "scripts/add-optcggg-lists.py"))
    portal = load("portal", str(ROOT / "scripts/add-tcgportal-lists.py"))
    opdb = load("opdb", str(ROOT / "scripts/add-onepiecedb-lists.py"))
    opdeck = load("opdeck", str(ROOT / "scripts/add-opdeckguide-lists.py"))
    hunt = load("hunt", str(ROOT / "scripts/hunt-window-lists.py"))
    analysis = load("analysis", str(ROOT / "scripts/add-leader-analysis.py"))
    tier = load("tierlist", str(ROOT / "scripts/build-tier-list.py"))
    up = load("upgrade", str(ROOT / "scripts/upgrade-public-pages.py"))

    print("=== EB05 images ===", flush=True)
    images = download_eb05_images()

    print("=== discover November leaders ===", flush=True)
    missing = discover_nov_leaders(gen)
    if missing:
        cache = gen.ensure_cards(set(missing), gen.load_card_cache())
        extra = [leader_stub(gen, lid, cache) for lid in missing]
        add_leaders(gen, extra, [commsrc, more, analysis, up, tier, optcggg, portal, opdb])

    portal.SINCE = SINCE
    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL
    optcggg.SKIP_EVENT_RE = re.compile(r"^\b$")
    optcggg.TARGET = 250
    optcggg.PER_EVENT = 80

    found: list[dict] = []
    seen: set[str] = set()
    sources = {"limitless": 0, "optcg.gg": 0, "portal": 0, "opdb": 0, "opdeck": 0, "reddit": 0}

    print("=== OPTCG.GG November ===", flush=True)
    optcg_rows = safe_collect("optcg.gg", lambda: collect_optcg(gen, commsrc, optcggg))
    for item in optcg_rows:
        before = len(found)
        commsrc.record(found, item, seen)
        if len(found) > before:
            sources["optcg.gg"] += 1

    print("=== OPDeckGuide ===", flush=True)
    for item in safe_collect("opdeck", lambda: hunt.opdeck_items(opdeck, commsrc)):
        if in_window(item.get("date") or "") and legal_counts(
            gen, commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            before = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before:
                sources["opdeck"] += 1

    print("=== Reddit ===", flush=True)
    for item in safe_collect("reddit", lambda: reddit_nov(hunt, commsrc)):
        before = len(found)
        commsrc.record(found, item, seen)
        if len(found) > before:
            sources["reddit"] += 1

    print("=== TCG PORTAL ===", flush=True)
    for item in safe_collect("portal", lambda: portal.collect_lists(gen, commsrc)):
        if in_window(item.get("date") or "") and legal_counts(
            gen, commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            before = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before:
                sources["portal"] += 1

    print("=== OnePieceDB ===", flush=True)
    for item in safe_collect("opdb", lambda: opdb.collect_lists(gen, commsrc)):
        day = item.get("date") or ""
        if (in_window(day) or not day) and legal_counts(
            gen, commsrc.parse_counts(item.get("raw") or ""), item.get("leader")
        ):
            before = len(found)
            commsrc.record(found, item, seen)
            if len(found) > before:
                sources["opdb"] += 1

    print("=== write community lists ===", flush=True)
    legal_found = [
        item
        for item in found
        if legal_counts(gen, commsrc.parse_counts(item.get("raw") or ""), item.get("leader"))
    ]
    commsrc.write_lists(legal_found)
    print("community legal lists", len(legal_found), flush=True)

    print("=== Limitless November ===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in {L["id"] for L in gen.LEADERS}}
    index = more.fetch_more(
        index,
        pages=8,
        extra_limit=500,
        per_event=200,
        since=SINCE,
        until=UNTIL,
        require_legal=True,
    )
    more.save_index(index)
    after = {lid: len(index.get(lid) or []) for lid in before}
    sources["limitless"] = sum(after.get(lid, 0) - before.get(lid, 0) for lid in before)
    print("limitless new", sources["limitless"], flush=True)

    print("=== rebuild ===", flush=True)
    more.rebuild_hubs(index)
    analysis.main()
    tier.main()
    up.patch_home()
    more.rewrite_sitemap()
    rewrite_branding()

    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "sources": sources,
        "community_legal": len(legal_found),
        "images": images,
        "new_total": sources["limitless"] + len(legal_found),
    }
    (ROOT / "data/nov-eb05-ingest-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("ingest summary", json.dumps(summary), flush=True)
    print("nov-eb05 ingest done", flush=True)


if __name__ == "__main__":
    main()
