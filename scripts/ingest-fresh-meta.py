#!/usr/bin/env python3
"""Scrape new complete lists, then rebuild the homepage pie and tier list.

Only writes 1 hosted leader + 46–52 cards with no bans. Does not invent cards.
Does not wipe existing pages. Rebuilds only hubs that gained lists.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
SINCE = (date.today() - timedelta(days=5)).isoformat()
LIMITLESS_SINCE = "2026-08-20"
UNTIL = date.today().isoformat()


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    for loc in (f"{SITE}/", f"{SITE}/tier-list.html", f"{SITE}/recent.html"):
        if loc in core:
            core = re.sub(rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+", rf"\g<1>{today}", core)
    (ROOT / "sitemap-core.xml").write_text(core)
    idx = (ROOT / "sitemap.xml").read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    (ROOT / "sitemap.xml").write_text(idx)


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    canon = load("canon", "/workspace/scripts/fix-canonicals.py")
    ingest200 = load("ingest200", "/workspace/scripts/ingest-200-lists.py")

    ingest200.SINCE = SINCE
    ingest200.TARGET = 80
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL
    portal.SINCE = SINCE

    found: list[dict] = []
    seen: set[str] = set()
    print("=== window community", SINCE, "limitless", LIMITLESS_SINCE, "to", UNTIL, "===", flush=True)

    ingest200.collect_optcg(gen, commsrc, optcggg, found, seen)
    ingest200.collect_opdeck(gen, commsrc, opdeck, found, seen)

    print("=== TCG PORTAL ===", flush=True)
    pfound = portal.collect_lists(gen, commsrc)
    for item in pfound:
        commsrc.record(found, item, seen)
    print("community candidates", len(found), flush=True)
    if found:
        commsrc.write_lists(found)

    print("=== OnePieceDB ===", flush=True)
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
    for item in opdb.collect_lists(gen, commsrc):
        day = (item.get("date") or "")[:10]
        if day and day < LIMITLESS_SINCE:
            print("skip old opdb", item.get("slug"), day, flush=True)
            continue
        commsrc.record(found, item, seen)
    if found:
        commsrc.write_lists(found)
        print("community after opdb", len(found), flush=True)

    print("=== Limitless since", LIMITLESS_SINCE, "===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in {L["id"] for L in gen.LEADERS}}
    index = more.fetch_more(
        index,
        pages=24,
        extra_limit=400,
        per_event=80,
        since=LIMITLESS_SINCE,
        until=UNTIL,
    )
    more.save_index(index)
    after = {lid: len(index.get(lid) or []) for lid in before}
    changed = {lid for lid in before if after[lid] > before[lid]}
    comm_ids = {item.get("leader") for item in found if item.get("leader")}
    changed |= {lid for lid in comm_ids if lid}
    lim_new = sum(after[lid] - before[lid] for lid in before)
    print("limitless new", lim_new, "changed leaders", sorted(changed), flush=True)

    if changed:
        more.rebuild_hubs(index, only_ids=changed)
    analysis.main()
    tier.main()
    up.patch_home()
    up.patch_op17()
    canon.main()
    rels = list_rels(found, gen, before, index)
    update_sitemaps(rels)
    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "community": len(found),
        "limitless": lim_new,
        "changed_leaders": sorted(changed),
        "pages": rels,
    }
    (ROOT / "data/fresh-meta-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("fresh-meta ingest", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
