#!/usr/bin/env python3
"""Host up to 200 new complete 50-card lists from public sources.

Only writes 1 hosted leader + 46–52 cards with no bans. Does not invent cards.
Does not wipe existing pages. Creates a Zoro hub if it is missing.
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
TARGET = 200
SINCE = "2026-08-20"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ensure_zoro_hub(gen, cache: dict) -> None:
    leader = next(L for L in gen.LEADERS if L["id"] == "OP12-020")
    path = ROOT / leader["page"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(gen.render_hub_page(leader, cache))
        print("wrote zoro hub", path, flush=True)


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
    core = (ROOT / "sitemap-core.xml").read_text()
    for loc in (f"{SITE}/", f"{SITE}/tier-list.html", f"{SITE}/recent.html", f"{SITE}/decklists/zoro.html"):
        if loc in core:
            core = re.sub(rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+", rf"\g<1>{today}", core)
        elif loc.endswith("zoro.html"):
            core = core.replace("</urlset>", f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n</urlset>")
    (ROOT / "sitemap-core.xml").write_text(core)
    idx = (ROOT / "sitemap.xml").read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    (ROOT / "sitemap.xml").write_text(idx)


def collect_optcg(gen, commsrc, optcggg, found: list[dict], seen: set[str]) -> None:
    hosted = {L["id"] for L in gen.LEADERS}
    seen_keys, seen_urls = optcggg.existing_index(gen)
    print("=== OPTCG.GG since", SINCE, "===", flush=True)
    listings = []
    have = set()
    for page in range(1, 18):
        if len(found) >= TARGET:
            return
        data = optcggg.get_json(f"{optcggg.API}/paginated?page={page}&page_size=40")
        batch = data.get("decklists") or []
        print("optcg page", page, "n", len(batch), flush=True)
        if not batch:
            break
        stop = False
        for row in batch:
            did = row.get("id")
            day = (row.get("event_date") or "")[:10]
            if not did or did in have:
                continue
            if day and day < SINCE:
                stop = True
                continue
            have.add(did)
            listings.append(row)
        if stop and page > 4:
            break
        time.sleep(0.05)
    for row in listings:
        if len(found) >= TARGET:
            return
        did = row.get("id") or ""
        event = row.get("event_name") or "OPTCG.GG event"
        if re.search(r"24-25|OP12 ENG", event):
            continue
        day = (row.get("event_date") or "")[:10]
        source_url = f"{optcggg.SITE}/{did}".rstrip("/")
        if source_url in seen_urls:
            continue
        try:
            deck = optcggg.get_json(f"{optcggg.API}/{did}")
        except Exception as exc:  # noqa: BLE001
            print("fail", did, exc, flush=True)
            continue
        counts = optcggg.counts_from_deck(deck)
        lid = optcggg.leader_id(row, counts, hosted)
        player = (row.get("player") or "Unknown").strip() or "Unknown"
        if not lid or counts.get(lid) != 1 or not commsrc.complete(counts, lid):
            time.sleep(0.05)
            continue
        key = (lid, gen.slugify(player), day)
        if key in seen_keys:
            continue
        place = row.get("placement")
        place_bit = gen.ordinal(place) if isinstance(place, int) and place > 0 else "list"
        title = f"{player} {place_bit} - {event}" if place_bit != "list" else f"{player} - {event}"
        commsrc.record(
            found,
            {
                "leader": lid,
                "kind": "web",
                "player": player,
                "title": title,
                "subtitle": f"Public OPTCG.GG list · {event} · {day}",
                "source_url": source_url,
                "slug": gen.slugify(f"optcggg-{place_bit}-{player}-{event}")[:70],
                "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                "cards": sum(n for cid, n in counts.items() if cid != lid),
                "date": day,
            },
            seen,
        )
        seen_keys.add(key)
        seen_urls.add(source_url)
        time.sleep(0.05)


def collect_opdeck(gen, commsrc, opdeck, found: list[dict], seen: set[str]) -> None:
    print("=== OPDeckGuide remaining ===", flush=True)
    opdeck._EXISTING_SLUGS = None
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    paths = opdeck.collect_paths()
    paths = list(dict.fromkeys(paths))
    print("opdeck paths", len(paths), flush=True)
    for path in paths:
        if len(found) >= TARGET:
            return
        slug = f"opdeck-{path.rstrip('/').split('/')[-1]}"[:70]
        if slug in opdeck.existing_slugs_cached():
            continue
        item = opdeck.parse_page(path, comm, gen)
        time.sleep(0.08)
        if not item:
            continue
        day = (item.get("date") or "")[:10]
        if day and day < SINCE:
            continue
        commsrc.record(found, item, seen)


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")
    canon = load("canon", "/workspace/scripts/fix-canonicals.py")

    cache = gen.ensure_cards({"OP12-020"}, gen.load_card_cache())
    ensure_zoro_hub(gen, cache)

    found: list[dict] = []
    seen: set[str] = set()
    collect_optcg(gen, commsrc, optcggg, found, seen)
    collect_opdeck(gen, commsrc, opdeck, found, seen)

    print("=== Limitless since", SINCE, "===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in {L["id"] for L in gen.LEADERS}}
    index = more.fetch_more(
        index,
        pages=18,
        extra_limit=120,
        per_event=28,
        since=SINCE,
        until=date.today().isoformat(),
    )
    more.save_index(index)
    after = {lid: len(index.get(lid) or []) for lid in before}
    lim_new = sum(max(0, after[lid] - before[lid]) for lid in before)
    print("limitless new", lim_new, flush=True)

    print("=== TCG PORTAL ===", flush=True)
    portal.SINCE = SINCE
    pfound = portal.collect_lists(gen, commsrc) if len(found) < TARGET else []
    room = TARGET - len(found)
    pfound = pfound[: max(0, room)]
    found = (found + pfound)[:TARGET]
    print("community candidates", len(found), flush=True)
    if found:
        commsrc.write_lists(found)

    index = more.load_index()
    more.rebuild_hubs(index)
    analysis.main()
    tier.main()
    up.patch_home()
    up.patch_op17()
    canon.main()
    rels = list_rels(found, gen)
    update_sitemaps(rels)
    summary = {
        "community": len(found),
        "limitless": lim_new,
        "portal": len(pfound),
        "pages": rels,
    }
    (ROOT / "data/two-hundred-lists-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("200-list ingest", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
