#!/usr/bin/env python3
"""Host additional complete Flame-Flame lists from public OPTCG.GG pages.

Prioritizes Dallas / NA Coliseum lists, then Dallas Championship Finals, then
unhosted Europe Flame-Flame lists (kept labeled Europe). Only writes a page
when the source is 1 hosted leader + 46–52 cards with no bans. Does not invent
cards. Does not wipe existing pages. Does not label Europe as Dallas.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
from datetime import date
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
FLAME_RE = re.compile(r"flame[\s-]*flame|coliseum", re.I)
DALLAS_RE = re.compile(r"dallas", re.I)
EUROPE_RE = re.compile(r"europe|utrecht|jaarbeurs", re.I)
NA_RE = re.compile(r"\bna\b|north america|dallas", re.I)


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def event_priority(event: str) -> int:
    name = event or ""
    if NA_RE.search(name) and FLAME_RE.search(name):
        return 0
    if DALLAS_RE.search(name):
        return 1
    if FLAME_RE.search(name) and EUROPE_RE.search(name):
        return 2
    if FLAME_RE.search(name):
        return 3
    return 9


def list_rels(found: list[dict], gen) -> list[str]:
    by_id = {L["id"]: L for L in gen.LEADERS}
    rels = []
    for item in found:
        leader = by_id.get(item.get("leader") or "")
        slug = item.get("slug")
        if leader and slug:
            rel = f"{leader['dir']}/{slug}.html"
            if (ROOT / rel).exists():
                rels.append(rel)
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
        hubs.add(f"{SITE}/{Path(rel).parent}.html")
    core_path = ROOT / "sitemap-core.xml"
    core = core_path.read_text()
    for loc in sorted(hubs):
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


def collect_flame(gen, commsrc, optcggg) -> list[dict]:
    hosted = {L["id"] for L in gen.LEADERS}
    seen_keys, seen_urls = optcggg.existing_index(gen)
    listings: list[dict] = []
    old_pages = 0
    print("=== OPTCG.GG flame listings ===", flush=True)
    for page in range(1, 20):
        data = optcggg.get_json(f"{optcggg.API}/paginated?page={page}&page_size=40")
        batch = data.get("decklists") or []
        print("page", page, "batch", len(batch), "listed", len(listings), flush=True)
        if not batch:
            break
        page_old = 0
        for row in batch:
            event = row.get("event_name") or ""
            day = (row.get("event_date") or "")[:10]
            if event_priority(event) >= 9:
                if day and day < "2026-09-04":
                    page_old += 1
                continue
            if not row.get("id"):
                continue
            listings.append(row)
        if page_old == len(batch):
            old_pages += 1
            if old_pages >= 2:
                break
        time.sleep(0.08)

    listings.sort(key=lambda row: (event_priority(row.get("event_name") or ""), row.get("placement") or 99))
    print("flame listings", len(listings), flush=True)

    found: list[dict] = []
    seen: set[str] = set()
    fetched = 0
    for row in listings:
        event = row.get("event_name") or "OPTCG.GG event"
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
            time.sleep(0.1)
            continue
        counts = optcggg.counts_from_deck(deck)
        lid = optcggg.leader_id(row, counts, hosted)
        main_n = sum(n for cid, n in counts.items() if cid != lid) if lid else 0
        banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
        player = (row.get("player") or "Unknown").strip() or "Unknown"
        print(event, player, lid or "-", "cards", main_n, "banned", banned, flush=True)
        if not lid or counts.get(lid) != 1 or banned or not commsrc.complete(counts, lid):
            time.sleep(0.1)
            continue
        key = (lid, gen.slugify(player), day)
        if key in seen_keys:
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
            "priority": event_priority(event),
        }
        before = len(found)
        commsrc.record(found, item, seen)
        if len(found) > before:
            seen_keys.add(key)
            seen_urls.add(source_url)
        time.sleep(0.1)

    (ROOT / "data/more-flame-optcggg-log.json").write_text(
        json.dumps({"fetched": fetched, "hosted": found}, indent=2, ensure_ascii=False) + "\n"
    )
    print("new flame ready", len(found), "fetched", fetched, flush=True)
    return found


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")

    found = collect_flame(gen, commsrc, optcggg)
    print("=== write ===", flush=True)
    commsrc.write_lists(found)
    index = more.load_index()
    more.rebuild_hubs(index)
    analysis.main()
    tier.main()
    up.patch_home()
    rels = list_rels(found, gen)
    update_sitemaps(rels)
    summary = {
        "new": len(found),
        "na": sum(1 for item in found if item.get("priority") == 0),
        "dallas_finals": sum(1 for item in found if item.get("priority") == 1),
        "europe": sum(1 for item in found if item.get("priority") == 2),
        "slugs": [item.get("slug") for item in found],
        "pages": rels,
    }
    (ROOT / "data/more-flame-ingest-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("more flame ingest", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
