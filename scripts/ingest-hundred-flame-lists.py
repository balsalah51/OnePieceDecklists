#!/usr/bin/env python3
"""Host up to 100 new complete Flame-Flame / Dallas-weekend 50-card lists.

Prioritizes Flame-Flame Fruit Coliseum, BCG Fest Dallas, and Dallas Nats
lists from OPTCG.GG and OPDeckGuide, then other complete 9/17+ public lists
to fill the 100. Only writes 1 hosted leader + 46–52 cards with no bans.
Does not invent cards. Does not wipe existing pages. Europe stays Europe.
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
TARGET = 100
FLAME_RE = re.compile(r"flame|coliseum|bcgfest|bcg-fest|dallas|nats-sep19", re.I)
EUROPE_RE = re.compile(r"europe|utrecht|jaarbeurs", re.I)


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def flame_score(text: str) -> int:
    blob = text or ""
    if re.search(r"flame[\s-]*flame|coliseum|bcgfest|bcg-fest", blob, re.I):
        return 0
    if re.search(r"dallas|nats-sep19", blob, re.I):
        return 1
    return 2


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
    core = (ROOT / "sitemap-core.xml").read_text()
    for loc in sorted(hubs):
        core = re.sub(
            rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+",
            rf"\g<1>{today}",
            core,
        )
    (ROOT / "sitemap-core.xml").write_text(core)
    idx = (ROOT / "sitemap.xml").read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    (ROOT / "sitemap.xml").write_text(idx)


def collect_optcg_flame(gen, commsrc, optcggg, found: list[dict], seen: set[str]) -> None:
    hosted = {L["id"] for L in gen.LEADERS}
    seen_keys, seen_urls = optcggg.existing_index(gen)
    print("=== OPTCG.GG search Flame / Coliseum ===", flush=True)
    listings = []
    have = set()
    for q in ("Flame", "Coliseum"):
        for page in range(1, 12):
            data = optcggg.get_json(f"{optcggg.API}/paginated?page={page}&page_size=40&search={q}")
            batch = data.get("decklists") or []
            print("optcg", q, "page", page, "n", len(batch), flush=True)
            if not batch:
                break
            for row in batch:
                did = row.get("id")
                event = row.get("event_name") or ""
                if not did or did in have:
                    continue
                if not FLAME_RE.search(event):
                    continue
                if re.search(r"24-25|OP12 ENG", event):
                    continue
                have.add(did)
                listings.append(row)
            time.sleep(0.06)
    listings.sort(key=lambda row: (flame_score(row.get("event_name") or ""), row.get("placement") or 99))
    for row in listings:
        if len(found) >= TARGET:
            return
        did = row.get("id") or ""
        event = row.get("event_name") or "OPTCG.GG event"
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
            print("skip incomplete", event, player, lid, flush=True)
            time.sleep(0.08)
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
        time.sleep(0.08)


def collect_opdeck(gen, commsrc, opdeck, found: list[dict], seen: set[str]) -> None:
    print("=== OPDeckGuide Flame / BCG Fest / 9/17+ ===", flush=True)
    opdeck.HUB_PAGES = (
        "https://opdeckguide.com/tournaments-decklists/",
        "https://opdeckguide.com/tournaments-decklists/op17-west/",
        "https://opdeckguide.com/tournaments-decklists/op17-east/",
        "https://opdeckguide.com/tournaments-decklists/op17-west",
        "https://opdeckguide.com/tournaments-decklists/op17-east",
    )
    opdeck._EXISTING_SLUGS = None
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    paths = opdeck.collect_paths()
    paths = list(dict.fromkeys(paths))
    paths.sort(key=lambda p: (flame_score(p), 0 if "op17-" in p else 1, p))
    print("opdeck paths", len(paths), flush=True)
    for path in paths:
        if len(found) >= TARGET:
            return
        item = opdeck.parse_page(path, comm, gen)
        time.sleep(0.1)
        if not item:
            continue
        day = (item.get("date") or "")[:10]
        blob = f"{path} {item.get('title') or ''} {item.get('subtitle') or ''}"
        if EUROPE_RE.search(blob) and not re.search(r"dallas|bcg|na\b", blob, re.I):
            if flame_score(blob) > 0 and day and day < "2026-09-17":
                continue
        if flame_score(blob) > 1 and day and day < "2026-09-17":
            continue
        commsrc.record(found, item, seen)


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    opdeck = load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")
    canon = load("canon", "/workspace/scripts/fix-canonicals.py")

    found: list[dict] = []
    seen: set[str] = set()
    collect_optcg_flame(gen, commsrc, optcggg, found, seen)
    collect_opdeck(gen, commsrc, opdeck, found, seen)
    found = found[:TARGET]
    print("complete candidates", len(found), flush=True)
    (ROOT / "data/hundred-flame-log.json").write_text(
        json.dumps({"found": found}, indent=2, ensure_ascii=False) + "\n"
    )
    commsrc.write_lists(found)
    index = more.load_index()
    more.rebuild_hubs(index)
    analysis.main()
    tier.main()
    up.patch_home()
    canon.main()
    rels = list_rels(found, gen)
    update_sitemaps(rels)
    flame_n = sum(1 for item in found if flame_score(f"{item.get('title')} {item.get('slug')}") == 0)
    dallas_n = sum(1 for item in found if flame_score(f"{item.get('title')} {item.get('slug')}") == 1)
    summary = {
        "new": len(found),
        "flame_or_bcg": flame_n,
        "dallas": dallas_n,
        "other": len(found) - flame_n - dallas_n,
        "slugs": [item.get("slug") for item in found],
        "pages": rels,
    }
    (ROOT / "data/hundred-flame-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("hundred flame ingest", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
