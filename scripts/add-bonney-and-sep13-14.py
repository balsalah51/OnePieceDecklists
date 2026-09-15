#!/usr/bin/env python3
"""Add every Jewelry Bonney leader hub, host 10 recent OP17 lists each, and
ingest complete lists dated 13-14 Sep 2026.

Does not invent cards from photos. Does not wipe existing list pages.
Does not replace the split sitemap index.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
BONNEY_IDS = {"EB04-001", "OP13-100", "OP07-019"}
TARGET_EACH = 10
SINCE = "2026-09-13"
UNTIL = "2026-09-14"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


def dated(item: dict) -> bool:
    return in_window(item.get("date") or "")


def has_op17_raw(raw: str) -> bool:
    return "OP17-" in (raw or "").upper()


def op17_list_count(ana, leader: dict) -> int:
    folder = ROOT / leader["dir"]
    if not folder.exists():
        return 0
    n = 0
    for path in folder.glob("*.html"):
        parsed = ana.parse_deck(path, leader["id"])
        if parsed and ana._has_op17(parsed):
            n += 1
    return n


def write_bonney_hubs(gen) -> None:
    cache = gen.ensure_cards(set(BONNEY_IDS), gen.load_card_cache())
    for leader in gen.LEADERS:
        if leader["id"] not in BONNEY_IDS:
            continue
        (ROOT / leader["dir"]).mkdir(parents=True, exist_ok=True)
        path = ROOT / leader["page"]
        if path.exists():
            print("hub exists", path, flush=True)
            continue
        path.write_text(gen.render_hub_page(leader, cache))
        print("wrote hub", path, flush=True)


def fill_bonney(gen, commsrc, more, opdeck, hunt, ana, optcggg, opdb, portal) -> list[dict]:
    by_id = {L["id"]: L for L in gen.LEADERS}
    found: list[dict] = []
    seen: set[str] = set()

    print("=== Limitless Bonney OP17 lists ===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in BONNEY_IDS}
    index = more.fetch_more(
        index,
        pages=15,
        only_ids=BONNEY_IDS,
        extra_limit=12,
        per_event=99,
        since="2026-08-01",
        require_op17=True,
    )
    more.save_index(index)
    more.rebuild_hubs(index, only_ids=BONNEY_IDS)

    print("=== OPDeckGuide Bonney ===", flush=True)
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    paths = opdeck.collect_paths()
    print("opdeck paths", len(paths), flush=True)
    for path in paths:
        item = opdeck.parse_page(path, comm, gen)
        time.sleep(0.1)
        if not item or item.get("leader") not in BONNEY_IDS:
            continue
        if not has_op17_raw(item.get("raw") or ""):
            print("skip no op17", item.get("slug"), flush=True)
            continue
        commsrc.record(found, item, seen)

    print("=== OPTCG.GG Bonney ===", flush=True)
    optcggg.SINCE = "2026-08-01"
    optcggg.UNTIL = UNTIL
    for item in optcggg.collect_lists(gen, commsrc):
        if item.get("leader") in BONNEY_IDS and has_op17_raw(item.get("raw") or ""):
            commsrc.record(found, item, seen)

    print("=== OnePieceDB Bonney ===", flush=True)
    for item in opdb.collect_lists(gen, commsrc):
        if item.get("leader") in BONNEY_IDS and has_op17_raw(item.get("raw") or ""):
            commsrc.record(found, item, seen)

    print("=== TCG PORTAL Bonney ===", flush=True)
    portal.SINCE = "2026-08-01"
    for item in portal.collect_lists(gen, commsrc):
        if item.get("leader") in BONNEY_IDS and has_op17_raw(item.get("raw") or ""):
            commsrc.record(found, item, seen)

    print("=== write Bonney community lists ===", flush=True)
    commsrc.write_lists(found)
    for lid in sorted(BONNEY_IDS):
        leader = by_id[lid]
        print("bonney op17 lists", lid, op17_list_count(ana, leader), flush=True)
    return found


def scrape_sep13_14(gen, commsrc, more, opdeck, hunt, portal, optcggg, opdb, xmod) -> tuple[list[dict], dict, dict]:
    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    xmod.DATE_START = SINCE
    xmod.DATE_END = UNTIL
    portal.SINCE = SINCE
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL
    found: list[dict] = []
    seen: set[str] = set()
    print("=== window", SINCE, "to", UNTIL, "===", flush=True)

    print("=== OPDeckGuide 9/13-9/14 ===", flush=True)
    for item in hunt.opdeck_items(opdeck, commsrc):
        if dated(item):
            commsrc.record(found, item, seen)
        else:
            print("skip old opdeck", item.get("slug"), item.get("date"), flush=True)

    print("=== Reddit 9/13-9/14 ===", flush=True)
    found.extend(reddit_window(hunt, commsrc))

    print("=== TCG PORTAL 9/13-9/14 ===", flush=True)
    for item in portal.collect_lists(gen, commsrc):
        if dated(item):
            commsrc.record(found, item, seen)

    print("=== OnePieceDB 9/13-9/14 ===", flush=True)
    for item in opdb.collect_lists(gen, commsrc):
        if dated(item):
            commsrc.record(found, item, seen)

    print("=== OPTCG.GG 9/13-9/14 ===", flush=True)
    for item in optcggg.collect_lists(gen, commsrc):
        if dated(item):
            commsrc.record(found, item, seen)

    print("=== X 9/13-9/14 ===", flush=True)
    xmod.main()
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
            if not day or not in_window(day):
                continue
            handle = item.get("handle") or "x"
            url = item.get("source") or item.get("url") or f"https://x.com/{handle}"
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

    print("=== write 9/13-9/14 community lists ===", flush=True)
    (ROOT / "data/sep13-14-community-log.json").write_text(
        json.dumps({"found": found, "window": {"start": SINCE, "end": UNTIL}}, indent=2, ensure_ascii=False)
        + "\n"
    )
    commsrc.write_lists(found)

    print("=== Limitless 9/13-9/14 ===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in {L["id"] for L in gen.LEADERS}}
    index = more.fetch_more(
        index,
        pages=10,
        extra_limit=400,
        per_event=99,
        since=SINCE,
        until=UNTIL,
    )
    more.save_index(index)
    return found, before, index


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


def list_rels(found: list[dict], gen, before: dict, index: dict) -> list[str]:
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
    for leader in gen.LEADERS:
        if leader["id"] not in BONNEY_IDS:
            continue
        folder = ROOT / leader["dir"]
        if not folder.exists():
            continue
        for path in folder.glob("*.html"):
            add(path.relative_to(ROOT).as_posix())
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

    hubs = {f"{SITE}/", f"{SITE}/tier-list.html", f"{SITE}/decklists/op17.html"}
    for rel in new_rels:
        hub = str(Path(rel).parent) + ".html"
        hubs.add(f"{SITE}/{hub}")
    core_path = ROOT / "sitemap-core.xml"
    core = core_path.read_text()
    for loc in sorted(hubs):
        if f"<loc>{loc}</loc>" not in core and loc.endswith(".html"):
            core = core.replace(
                "</urlset>",
                f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n</urlset>",
            )
        core = re.sub(
            rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+",
            rf"\g<1>{today}",
            core,
        )
    core_path.write_text(core)

    idx = (ROOT / "sitemap.xml").read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    (ROOT / "sitemap.xml").write_text(idx)


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    hunt = load("hunt", "/workspace/scripts/hunt-window-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
    xmod = load("xlists", "/workspace/scripts/scrape-x-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")

    print("=== Bonney hubs ===", flush=True)
    write_bonney_hubs(gen)
    bonney_found = fill_bonney(gen, commsrc, more, opdeck, hunt, analysis, optcggg, opdb, portal)

    window_found, before, index = scrape_sep13_14(
        gen, commsrc, more, opdeck, hunt, portal, optcggg, opdb, xmod
    )

    print("=== rebuild hubs / consensus / leaders page / pie / tier list ===", flush=True)
    more.rebuild_hubs(index)
    analysis.main()
    tier.main()
    up.patch_home()
    up.patch_op17()
    tier_html = ROOT / "tier-list.html"
    if tier_html.exists():
        tier_html.write_text(
            re.sub(
                r'href="/css/site\.css(?:\?[^"]*)?"',
                'href="/css/site.css?v=home-pro16"',
                tier_html.read_text(),
            )
        )
    all_found = bonney_found + window_found
    new_rels = list_rels(all_found, gen, before, index)
    update_sitemaps(new_rels)

    by_id = {L["id"]: L for L in gen.LEADERS}
    counts = {lid: op17_list_count(analysis, by_id[lid]) for lid in sorted(BONNEY_IDS)}
    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "bonney_op17_lists": counts,
        "bonney_community_found": len(bonney_found),
        "window_community_found": len(window_found),
        "limitless_new_index_rows": sum(
            len(index.get(lid) or []) - before.get(lid, 0) for lid in before
        ),
    }
    (ROOT / "data/bonney-sep13-14-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("summary", json.dumps(summary), flush=True)
    print("bonney and sep13-14 ingest done", flush=True)


if __name__ == "__main__":
    main()
