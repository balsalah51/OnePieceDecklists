#!/usr/bin/env python3
"""Host every complete public 50-card list dated the last 3 days.

Sources: Limitless (no per-event cap), OPTCG.GG, OPDeckGuide, OnePieceDB,
TCG PORTAL, Reddit. Only writes 1 hosted leader + 46–52 cards with no bans.
Does not invent cards. Does not wipe existing pages. Rebuilds Extra Grand Battle.
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
UNTIL = date.today().isoformat()
SINCE = (date.today() - timedelta(days=3)).isoformat()
TARGET = 1000


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_window(day: str) -> bool:
    return bool(day) and SINCE <= day[:10] <= UNTIL


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
    for loc in (
        f"{SITE}/",
        f"{SITE}/tier-list.html",
        f"{SITE}/recent.html",
        f"{SITE}/extra-grand-battle.html",
    ):
        if loc in core:
            core = re.sub(rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+", rf"\g<1>{today}", core)
    (ROOT / "sitemap-core.xml").write_text(core)
    idx = (ROOT / "sitemap.xml").read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    (ROOT / "sitemap.xml").write_text(idx)


def reddit_window(hunt, commsrc) -> list[dict]:
    start = datetime.combine(date.fromisoformat(SINCE), datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(date.fromisoformat(UNTIL) + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    after = int(start.timestamp())
    before = int(end.timestamp())
    found: list[dict] = []
    seen: set[str] = set()
    import time
    import urllib.parse

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
        time.sleep(0.12)
    return found


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    optcggg = load("optcggg", "/workspace/scripts/add-optcggg-lists.py")
    portal = load("portal", "/workspace/scripts/add-tcgportal-lists.py")
    opdb = load("opdb", "/workspace/scripts/add-onepiecedb-lists.py")
    hunt = load("hunt", "/workspace/scripts/hunt-window-lists.py")
    analysis = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    egbbuild = load("egbbuild", "/workspace/scripts/build-egb.py")

    hunt.SINCE = SINCE
    hunt.UNTIL = UNTIL
    portal.SINCE = SINCE
    optcggg.SINCE = SINCE
    optcggg.UNTIL = UNTIL

    found: list[dict] = []
    seen: set[str] = set()
    print("=== super last 3 days", SINCE, "to", UNTIL, "target", TARGET, "===", flush=True)

    print("=== OPDeckGuide ===", flush=True)
    for item in hunt.opdeck_items(opdeck := load("opdeck", "/workspace/scripts/add-opdeckguide-lists.py"), commsrc):
        if in_window(item.get("date") or ""):
            commsrc.record(found, item, seen)
        else:
            print("skip old opdeck", item.get("slug"), item.get("date"), flush=True)

    print("=== Reddit ===", flush=True)
    found.extend(reddit_window(hunt, commsrc))

    print("=== TCG PORTAL ===", flush=True)
    for item in portal.collect_lists(gen, commsrc):
        if in_window(item.get("date") or ""):
            commsrc.record(found, item, seen)

    print("=== OnePieceDB ===", flush=True)
    for item in opdb.collect_lists(gen, commsrc):
        day = item.get("date") or ""
        if not day or in_window(day):
            commsrc.record(found, item, seen)
        else:
            print("skip old opdb", item.get("slug"), day, flush=True)

    print("=== OPTCG.GG ===", flush=True)
    for item in optcggg.collect_lists(gen, commsrc):
        if in_window(item.get("date") or ""):
            commsrc.record(found, item, seen)

    print("community candidates", len(found), flush=True)
    if found:
        commsrc.write_lists(found)

    print("=== Limitless since", SINCE, "no per-event cap ===", flush=True)
    index = more.load_index()
    before = {lid: len(index.get(lid) or []) for lid in {L["id"] for L in gen.LEADERS}}
    index = more.fetch_more(
        index,
        pages=12,
        extra_limit=2000,
        per_event=999,
        since=SINCE,
        until=UNTIL,
    )
    more.save_index(index)
    after = {lid: len(index.get(lid) or []) for lid in before}
    changed = {lid for lid in before if after[lid] > before[lid]}
    changed |= {item.get("leader") for item in found if item.get("leader")}
    changed.discard(None)
    lim_new = sum(after[lid] - before[lid] for lid in before)
    print("limitless new", lim_new, "changed leaders", sorted(changed), flush=True)

    if changed:
        more.rebuild_hubs(index, only_ids=changed)
    analysis.main()
    # Refresh Standard tier content without rewriting every HTML footer.
    tier.patch_all_pages = lambda: 0
    tier.main()
    up.patch_home()
    up.patch_op17()
    print("=== Extra Grand Battle section ===", flush=True)
    egbbuild.main()
    rels = list_rels(found, gen, before, index)
    update_sitemaps(rels)
    summary = {
        "window": {"start": SINCE, "end": UNTIL},
        "target": TARGET,
        "community": len(found),
        "limitless": lim_new,
        "hosted": len(rels),
        "changed_leaders": sorted(changed),
        "pages": rels,
    }
    (ROOT / "data/last-3-days-1000-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print("super last-3-days ingest", json.dumps({"hosted": len(rels), "limitless": lim_new, "community": len(found)}), flush=True)


if __name__ == "__main__":
    main()
