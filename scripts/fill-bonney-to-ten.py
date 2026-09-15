#!/usr/bin/env python3
"""Fill each Bonney hub toward 10 recent complete public lists.

Prefers dumps that already splash OP17 cards. Does not invent cards.
Does not wipe existing pages. Does not replace the split sitemap index.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
BONNEY_IDS = {"EB04-001", "OP13-100", "OP07-019"}
TARGET_EACH = 10
SINCE = "2026-07-15"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def list_count(leader: dict) -> int:
    folder = ROOT / leader["dir"]
    if not folder.exists():
        return 0
    return len(list(folder.glob("*.html")))


def op17_count(ana, leader: dict) -> int:
    folder = ROOT / leader["dir"]
    if not folder.exists():
        return 0
    n = 0
    for path in folder.glob("*.html"):
        parsed = ana.parse_deck(path, leader["id"])
        if parsed and ana._has_op17(parsed):
            n += 1
    return n


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
        if path.exists():
            path.write_text(
                re.sub(
                    r'href="/css/site\.css(?:\?[^"]*)?"',
                    'href="/css/site.css?v=home-pro16"',
                    path.read_text(),
                )
            )


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
        hubs.add(f"{SITE}/{Path(rel).parent}.html")
    core = (ROOT / "sitemap-core.xml").read_text()
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
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")
    by_id = {L["id"]: L for L in gen.LEADERS}

    found: list[dict] = []
    seen: set[str] = set()

    print("=== Limitless Bonney complete lists since", SINCE, "===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in BONNEY_IDS}
    index = more.fetch_more(
        index,
        pages=40,
        only_ids=BONNEY_IDS,
        extra_limit=12,
        per_event=99,
        since=SINCE,
        require_op17=False,
    )
    more.save_index(index)
    more.rebuild_hubs(index, only_ids=BONNEY_IDS)

    print("=== OnePieceDB leftover Bonney ===", flush=True)
    hosted = {L["id"] for L in gen.LEADERS}
    extra_urls = [
        "https://onepiecedb.io/deck/bonney-1984",
        "https://onepiecedb.io/deck/redyellow-bonney-by-akemitcg-1856",
        "https://onepiecedb.io/deck/yellow-jewelry-boney-2485",
        "https://onepiecedb.io/deck/jewelry-bonney-by-ace88-2436",
    ]
    existing = opdb.existing_urls()
    for url in extra_urls:
        if url in existing:
            print("skip known", url.rsplit("/", 1)[-1], flush=True)
            continue
        try:
            item = opdb.parse_page(url, hosted, gen, commsrc)
        except Exception as exc:  # noqa: BLE001
            print("fail", url, exc, flush=True)
            continue
        if item and item.get("leader") in BONNEY_IDS:
            if list_count(by_id[item["leader"]]) >= TARGET_EACH:
                print("skip already 10", item["leader"], flush=True)
                continue
            commsrc.record(found, item, seen)
        time.sleep(0.1)

    print("=== OPTCG.GG Bonney fill ===", flush=True)
    seen_keys, seen_urls = optcggg.existing_index(gen)
    rows = []
    seen_ids = set()
    for q in ["Bonney", "OP07-019", "EB04-001", "OP13-100"]:
        data = optcggg.get_json(
            f"{optcggg.API}/paginated?page=1&page_size=20&search={urllib.parse.quote(q)}"
        )
        for row in data.get("decklists") or []:
            did = row.get("id")
            if not did or did in seen_ids:
                continue
            seen_ids.add(did)
            rows.append(row)
    rows.sort(key=lambda row: (row.get("event_date") or ""), reverse=True)
    for row in rows:
        lid_hint = row.get("leader") or ""
        if not re.search(r"EB04-001|OP13-100|OP07-019", lid_hint):
            continue
        day = (row.get("event_date") or "")[:10]
        event = row.get("event_name") or "OPTCG.GG event"
        if optcggg.SKIP_EVENT_RE.search(event):
            continue
        did = row.get("id") or ""
        source_url = f"{optcggg.SITE}/{did}".rstrip("/")
        if source_url in seen_urls:
            continue
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
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        print("optcg.gg", day, lid or "-", main_n, player, flush=True)
        if not lid or lid not in BONNEY_IDS or counts.get(lid) != 1 or main_n != 50 or banned:
            time.sleep(0.08)
            continue
        pending = sum(1 for item in found if item.get("leader") == lid)
        if list_count(by_id[lid]) + pending >= TARGET_EACH:
            print("skip already 10", lid, flush=True)
            time.sleep(0.08)
            continue
        place = row.get("placement")
        place_bit = gen.ordinal(place) if isinstance(place, int) and place else "list"
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
        time.sleep(0.08)

    print("=== write community ===", flush=True)
    commsrc.write_lists(found)

    print("=== rebuild ===", flush=True)
    index = more.load_index()
    more.rebuild_hubs(index, only_ids=BONNEY_IDS)
    analysis.main()
    tier.main()
    up.patch_home()
    up.patch_op17()
    pin_css()
    restore_nested_list_footers()
    pin_css()

    rels = []
    for leader in gen.LEADERS:
        if leader["id"] not in BONNEY_IDS:
            continue
        rels.append(leader["page"])
        folder = ROOT / leader["dir"]
        if folder.exists():
            rels.extend(p.relative_to(ROOT).as_posix() for p in folder.glob("*.html"))
    update_sitemaps(rels)

    counts = {lid: list_count(by_id[lid]) for lid in sorted(BONNEY_IDS)}
    op17 = {lid: op17_count(analysis, by_id[lid]) for lid in sorted(BONNEY_IDS)}
    summary = {
        "bonney_lists": counts,
        "bonney_op17_lists": op17,
        "community_found": len(found),
        "limitless_new_index_rows": sum(len(index.get(lid) or []) - before.get(lid, 0) for lid in BONNEY_IDS),
    }
    (ROOT / "data/bonney-sep13-14-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("summary", json.dumps(summary), flush=True)
    print("bonney fill-to-ten done", flush=True)


if __name__ == "__main__":
    main()
