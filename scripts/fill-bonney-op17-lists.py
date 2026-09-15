#!/usr/bin/env python3
"""Hunt remaining complete OP17-splash lists for every Jewelry Bonney leader.

Does not invent cards from photos. Does not wipe existing pages.
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
SINCE = "2026-08-01"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys_modules_set(name, mod)
    spec.loader.exec_module(mod)
    return mod


def sys_modules_set(name, mod):
    import sys

    sys.modules[name] = mod


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


def write_hubs(gen) -> None:
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


def youtube_items(commsrc) -> list[dict]:
    queries = [
        "EB04-001 Jewelry Bonney decklist OP17 youtube",
        "OP13-100 yellow Bonney decklist OP17 youtube",
        "OP07-019 green Bonney decklist OP17 youtube",
        "red yellow Bonney OP17 deck profile",
        "yellow Bonney OP17 decklist 4xOP17",
        "green Bonney OP17 decklist Shanks",
        "Jewelry Bonney OP17 decklist September 2026",
        "ジュエリーボニー OP17 デッキレシピ",
    ]
    video_ids: list[str] = []
    for q in queries:
        body = commsrc.ddg(q)
        for vid in commsrc.YOUTUBE_ID_RE.findall(body):
            if vid not in video_ids:
                video_ids.append(vid)
        time.sleep(0.2)
    print("youtube ids", len(video_ids), flush=True)
    found: list[dict] = []
    seen: set[str] = set()
    for vid in video_ids[:48]:
        url = f"https://www.youtube.com/watch?v={vid}"
        status, body = commsrc.fetch(f"https://r.jina.ai/{url}", timeout=20)
        counts = commsrc.parse_counts(body)
        lid = commsrc.leader_of(counts)
        print("yt", status, vid, "lines", len(counts), lid or "-", flush=True)
        if not lid or lid not in BONNEY_IDS or not commsrc.complete(counts, lid):
            time.sleep(0.12)
            continue
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        if not has_op17_raw(raw):
            print("skip yt no op17", vid, lid, flush=True)
            time.sleep(0.12)
            continue
        title = f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} YouTube list"
        m = re.search(r"(?im)^Title:\s*(.+)$", body)
        if m:
            title = m.group(1).strip()[:90]
        commsrc.record(
            found,
            {
                "leader": lid,
                "kind": "youtube",
                "player": "YouTube",
                "title": title,
                "subtitle": "YouTube deck profile from a public description",
                "source_url": url,
                "slug": commsrc.slug_for("yt", "youtube", f"{commsrc.TARGET_IDS[lid]}-{vid}"),
                "raw": raw,
                "cards": sum(n for cid, n in counts.items() if cid != lid),
            },
            seen,
        )
        time.sleep(0.12)
    return found


def reddit_items(hunt, commsrc) -> list[dict]:
    start = datetime.fromisoformat(SINCE).replace(tzinfo=timezone.utc)
    end = datetime.combine(date.today() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    after = int(start.timestamp())
    before = int(end.timestamp())
    found: list[dict] = []
    seen: set[str] = set()
    queries = [
        (
            "https://arctic-shift.photon-reddit.com/api/posts/search?"
            + urllib.parse.urlencode(
                {
                    "subreddit": "OnePieceTCG",
                    "query": "Bonney OR Bonnie OR EB04-001 OR OP13-100 OR OP07-019",
                    "after": after,
                    "before": before,
                    "limit": 100,
                }
            )
        ),
        (
            "https://arctic-shift.photon-reddit.com/api/comments/search?"
            + urllib.parse.urlencode(
                {
                    "subreddit": "OnePieceTCG",
                    "query": "Bonney OR OP13-100 OR EB04-001",
                    "after": after,
                    "before": before,
                    "limit": 200,
                }
            )
        ),
    ]
    for url in queries:
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
            text = "\n".join(str(post.get(k) or "") for k in ("title", "selftext", "body", "permalink", "url"))
            permalink = post.get("permalink") or post.get("id") or url
            counts = commsrc.parse_counts(text)
            lid = commsrc.leader_of(counts)
            if not lid or lid not in BONNEY_IDS or not commsrc.complete(counts, lid):
                continue
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            if not has_op17_raw(raw):
                continue
            created = post.get("created_utc") or post.get("created") or 0
            try:
                day = datetime.fromtimestamp(float(created), tz=timezone.utc).strftime("%Y-%m-%d")
            except (OSError, ValueError, TypeError, OverflowError):
                day = ""
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


def x_items(commsrc) -> list[dict]:
    queries = [
        "site:x.com EB04-001 Bonney 4xOP17",
        "site:x.com OP13-100 Bonney decklist OP17",
        "site:x.com OP07-019 Bonney decklist OP17",
        "Jewelry Bonney OP17 decklist 1xEB04-001",
        "Jewelry Bonney OP17 decklist 1xOP13-100",
    ]
    found: list[dict] = []
    seen: set[str] = set()
    urls: list[str] = []
    for q in queries:
        body = commsrc.ddg(q)
        for href in re.findall(r'https?://(?:x|twitter)\.com/[^"\s<>]+', body):
            if href not in urls:
                urls.append(href)
        time.sleep(0.2)
    print("x urls", len(urls), flush=True)
    for url in urls[:40]:
        status, body = commsrc.fetch(f"https://r.jina.ai/{url}", timeout=18)
        counts = commsrc.parse_counts(body)
        lid = commsrc.leader_of(counts)
        print("x", status, url[:70], lid or "-", "n", len(counts), flush=True)
        if not lid or lid not in BONNEY_IDS or not commsrc.complete(counts, lid):
            time.sleep(0.12)
            continue
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        if not has_op17_raw(raw):
            continue
        handle = "x"
        m = re.search(r"(?:x|twitter)\.com/([^/]+)", url)
        if m:
            handle = m.group(1)
        commsrc.record(
            found,
            {
                "leader": lid,
                "kind": "x",
                "player": handle,
                "title": f"{commsrc.TARGET_IDS[lid].replace('-', ' ').title()} - @{handle}",
                "subtitle": "List copied from a public X/Twitter post",
                "source_url": url.split("?")[0],
                "slug": commsrc.slug_for("x", handle, commsrc.TARGET_IDS[lid] + raw[-12:]),
                "raw": raw,
                "cards": sum(n for cid, n in counts.items() if cid != lid),
            },
            seen,
        )
        time.sleep(0.12)
    return found


def opdb_direct(opdb, gen, commsrc) -> list[dict]:
    hosted = {L["id"] for L in gen.LEADERS}
    extra = [
        "https://onepiecedb.io/category/leader/jewelry-bonney-op07-019",
        "https://onepiecedb.io/category/leader/jewelry-bonney-eb04-001",
        "https://onepiecedb.io/category/leader/jewelry-bonney-op13-100",
        "https://onepiecedb.io/format/op17/archetype/OP13-100/yellow",
        "https://onepiecedb.io/format/op17/archetype/EB04-001/red-yellow",
        "https://onepiecedb.io/format/op17/archetype/OP07-019/green",
    ]
    urls: list[str] = []
    for page in extra:
        try:
            body = opdb.fetch(page)
        except Exception as exc:  # noqa: BLE001
            print("opdb page fail", page, exc, flush=True)
            continue
        for href in opdb.DECK_HREF_RE.findall(body):
            if href not in urls:
                urls.append(href)
        print("opdb extra", page.split(".io")[-1][:48], "urls", len(urls), flush=True)
        time.sleep(0.12)
    found: list[dict] = []
    seen: set[str] = set()
    existing = opdb.existing_urls()
    for url in urls:
        if url in existing:
            print("skip known", url.rsplit("/", 1)[-1], flush=True)
            continue
        try:
            item = opdb.parse_page(url, hosted, gen, commsrc)
        except Exception as exc:  # noqa: BLE001
            print("fail", url, exc, flush=True)
            time.sleep(0.12)
            continue
        time.sleep(0.12)
        if item and item.get("leader") in BONNEY_IDS and has_op17_raw(item.get("raw") or ""):
            commsrc.record(found, item, seen)
    return found


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
        add(leader["page"])
    return rels


def restore_nested_list_footers() -> None:
    import subprocess

    diff = subprocess.check_output(["git", "diff", "--name-only", "--", "decklists"], text=True)
    restore = []
    keep_dirs = {f"decklists/{name}" for name in ("jewelry-bonney", "op13-bonney", "op07-bonney")}
    for rel in diff.splitlines():
        parts = Path(rel).parts
        if len(parts) < 3 or not rel.endswith(".html"):
            continue
        if str(Path(*parts[:2])) in keep_dirs:
            continue
        restore.append(rel)
    if restore:
        for i in range(0, len(restore), 200):
            subprocess.check_call(["git", "checkout", "--", *restore[i : i + 200]])
        print("restored nested list html", len(restore), flush=True)


def pin_css() -> None:
    for rel in ("index.html", "tier-list.html"):
        path = ROOT / rel
        if not path.exists():
            continue
        path.write_text(
            re.sub(
                r'href="/css/site\.css(?:\?[^"]*)?"',
                'href="/css/site.css?v=home-pro16"',
                path.read_text(),
            )
        )


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    hunt = load("hunt", "/workspace/scripts/hunt-window-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")

    print("=== Bonney hubs ===", flush=True)
    write_hubs(gen)

    found: list[dict] = []
    seen: set[str] = set()

    print("=== Limitless Bonney OP17 lists ===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in BONNEY_IDS}
    index = more.fetch_more(
        index,
        pages=40,
        only_ids=BONNEY_IDS,
        extra_limit=40,
        per_event=99,
        since="2026-07-15",
        require_op17=True,
    )
    more.save_index(index)
    more.rebuild_hubs(index, only_ids=BONNEY_IDS)

    print("=== OPDeckGuide all paths ===", flush=True)
    paths = opdeck.collect_paths()
    print("opdeck paths", len(paths), flush=True)
    for path in paths:
        item = opdeck.parse_page(path, comm, gen)
        time.sleep(0.08)
        if not item or item.get("leader") not in BONNEY_IDS:
            continue
        if not has_op17_raw(item.get("raw") or ""):
            print("skip no op17", item.get("slug"), flush=True)
            continue
        commsrc.record(found, item, seen)

    print("=== OPTCG.GG Bonney search ===", flush=True)
    hosted = {L["id"] for L in gen.LEADERS}
    seen_keys, seen_urls = optcggg.existing_index(gen)
    for q in ["Bonney", "Bonnie", "EB04-001", "OP13-100", "OP07-019"]:
        data = optcggg.get_json(
            f"{optcggg.API}/paginated?page=1&page_size=20&search={urllib.parse.quote(q)}"
        )
        rows = data.get("decklists") or []
        print("optcg.gg search", q, "n", len(rows), flush=True)
        for row in rows:
            day = (row.get("event_date") or "")[:10]
            if day and day < SINCE:
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
                print("fail", did, exc, flush=True)
                time.sleep(0.12)
                continue
            counts = optcggg.counts_from_deck(deck)
            lid = optcggg.leader_id(row, counts, hosted)
            main_n = sum(n for cid, n in counts.items() if cid != lid) if lid else 0
            banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
            player = (row.get("player") or "Unknown").strip() or "Unknown"
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            print("optcg.gg", player, lid or "-", "cards", main_n, "op17", "OP17-" in raw, flush=True)
            if not lid or lid not in BONNEY_IDS or counts.get(lid) != 1 or main_n != 50 or banned:
                time.sleep(0.1)
                continue
            if not has_op17_raw(raw):
                time.sleep(0.1)
                continue
            place = row.get("placement")
            place_bit = gen.ordinal(place) if isinstance(place, int) and place else "list"
            event = row.get("event_name") or "OPTCG.GG event"
            commsrc.record(
                found,
                {
                    "leader": lid,
                    "kind": "web",
                    "player": player,
                    "title": f"{player} - {event}",
                    "subtitle": f"Public OPTCG.GG list · {event} · {day}",
                    "source_url": source_url,
                    "slug": gen.slugify(f"optcggg-{place_bit}-{player}-{event}")[:70],
                    "raw": raw,
                    "cards": main_n,
                    "date": day,
                },
                seen,
            )
            seen_urls.add(source_url)
            time.sleep(0.1)

    print("=== OnePieceDB extra Bonney ===", flush=True)
    for item in opdb_direct(opdb, gen, commsrc):
        commsrc.record(found, item, seen)

    print("=== TCG PORTAL Bonney ===", flush=True)
    portal.SINCE = SINCE
    for item in portal.collect_lists(gen, commsrc):
        if item.get("leader") in BONNEY_IDS and has_op17_raw(item.get("raw") or ""):
            commsrc.record(found, item, seen)

    print("=== YouTube Bonney ===", flush=True)
    for item in youtube_items(commsrc):
        commsrc.record(found, item, seen)

    print("=== Reddit Bonney ===", flush=True)
    for item in reddit_items(hunt, commsrc):
        commsrc.record(found, item, seen)

    print("=== X Bonney ===", flush=True)
    for item in x_items(commsrc):
        commsrc.record(found, item, seen)

    print("=== write Bonney community lists ===", flush=True)
    commsrc.write_lists(found)
    (ROOT / "data/bonney-fill-log.json").write_text(
        json.dumps({"found": found}, indent=2, ensure_ascii=False) + "\n"
    )

    print("=== rebuild hubs / consensus / leaders page / pie / tier list ===", flush=True)
    index = more.load_index()
    more.rebuild_hubs(index, only_ids=BONNEY_IDS)
    analysis.main()
    tier.main()
    up.patch_home()
    up.patch_op17()
    pin_css()
    restore_nested_list_footers()
    pin_css()

    new_rels = list_rels(found, gen, before, index)
    update_sitemaps(new_rels)

    by_id = {L["id"]: L for L in gen.LEADERS}
    counts = {lid: op17_list_count(analysis, by_id[lid]) for lid in sorted(BONNEY_IDS)}
    summary = {
        "bonney_op17_lists": counts,
        "target_each": TARGET_EACH,
        "community_found": len(found),
        "limitless_new_index_rows": sum(len(index.get(lid) or []) - before.get(lid, 0) for lid in BONNEY_IDS),
    }
    (ROOT / "data/bonney-sep13-14-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("summary", json.dumps(summary), flush=True)
    print("bonney fill done", flush=True)


if __name__ == "__main__":
    main()
