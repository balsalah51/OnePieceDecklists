#!/usr/bin/env python3
"""Host a large batch of yellow OP05 Enel lists, then more complete lists.

Limitless standings only. Each list is one hosted leader plus at least
MIN_CARDS cards and no banned cards. Does not invent cards or wipe pages.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
from datetime import date
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
ENEL_ID = "OP05-098"
ENEL_LIMIT = 200
ENEL_PER_EVENT = 6
GENERAL_LIMIT = 8
GENERAL_PER_EVENT = 3


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch_all_tournaments(gen) -> list:
    seen = []
    ids = set()
    for page in range(1, 81):
        batch = gen.http_json(
            f"https://play.limitlesstcg.com/api/tournaments?game=OP&limit=40&page={page}"
        )
        if not batch:
            print("page", page, "empty", flush=True)
            break
        added = 0
        for tourney in batch:
            tid = tourney.get("id")
            if not tid or tid in ids:
                continue
            ids.add(tid)
            seen.append(tourney)
            added += 1
        dates = [(t.get("date") or "")[:10] for t in batch]
        print(
            "page",
            page,
            "new",
            added,
            "unique",
            len(seen),
            "span",
            dates[0],
            dates[-1],
            flush=True,
        )
    return seen


def fetch_standings(gen, tournaments: list[dict], target_ids: set[str]) -> dict[str, list]:
    """Slow standings fetch with a checkpoint so a 429 restart can resume."""
    progress_path = Path("/tmp/enel-standings-progress.json")
    done_ids = set()
    by_leader: dict[str, list] = {lid: [] for lid in target_ids}
    if progress_path.exists():
        saved = json.loads(progress_path.read_text())
        done_ids = set(saved.get("done") or [])
        for lid, rows in (saved.get("by_leader") or {}).items():
            if lid in by_leader:
                by_leader[lid].extend(rows)
        print("resume done", len(done_ids), flush=True)
    skip_re = re.compile(r"\b(draft|sealed)\b", re.I)
    eligible = [
        t
        for t in tournaments
        if t.get("id")
        and t["id"] not in done_ids
        and not skip_re.search(t.get("name") or "")
        and (t.get("date") or "")[:4] >= "2023"
    ]
    print("standings remaining", len(eligible), flush=True)

    def one(tourney: dict) -> tuple[str, list[tuple[str, dict]]]:
        tid = tourney["id"]
        time.sleep(0.45)
        try:
            standings = gen.http_json(f"https://play.limitlesstcg.com/api/tournaments/{tid}/standings")
        except Exception as exc:  # noqa: BLE001
            print("standings fail", tid, exc, flush=True)
            return tid, []
        found = []
        for row in standings or []:
            dl = row.get("decklist") or {}
            leader = dl.get("leader") or {}
            if not leader.get("set"):
                continue
            lid = gen.card_id(leader["set"], leader.get("number"))
            if lid not in target_ids:
                continue
            found.append(
                (
                    lid,
                    {
                        "tournament_id": tid,
                        "tournament_name": tourney.get("name") or "Limitless event",
                        "format": tourney.get("format") or "",
                        "date": (tourney.get("date") or "")[:10],
                        "players": tourney.get("players") or 0,
                        "player": row.get("name") or "Unknown",
                        "placing": row.get("placing"),
                        "record": row.get("record") or {},
                        "decklist": dl,
                        "source_url": f"https://play.limitlesstcg.com/tournament/{tid}/standings",
                        "kind": "tournament",
                    },
                )
            )
        return tid, found

    processed = 0
    # Two workers stay under the Limitless rate limit.
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(one, t) for t in eligible]
        for fut in as_completed(futures):
            tid, found = fut.result()
            done_ids.add(tid)
            for lid, entry in found:
                by_leader.setdefault(lid, []).append(entry)
            processed += 1
            if processed % 25 == 0:
                progress_path.write_text(
                    json.dumps({"done": sorted(done_ids), "by_leader": by_leader})
                )
                print(
                    f"  processed {processed}/{len(eligible)} enel raw {len(by_leader.get(ENEL_ID) or [])}",
                    flush=True,
                )
    progress_path.write_text(json.dumps({"done": sorted(done_ids), "by_leader": by_leader}))
    return by_leader


def write_planned(gen, more, index: dict, leaders: list, planned: dict) -> None:
    cache = gen.load_card_cache()
    needed = set()
    for rows in planned.values():
        for entry in rows:
            for item in gen.flatten_cards(entry["decklist"]):
                needed.add(item["id"])
    cache = gen.ensure_cards(needed, cache)
    for leader in leaders:
        fresh = planned.get(leader["id"]) or []
        if not fresh:
            continue
        out_dir = ROOT / leader["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        for entry in fresh:
            page = gen.render_deck_page(leader, entry, cache)
            (out_dir / f"{entry['slug']}.html").write_text(page)
            index.setdefault(leader["id"], []).append(more.index_row(entry))


def list_rels(gen, before: dict, index: dict) -> list[str]:
    by_id = {L["id"]: L for L in gen.LEADERS}
    rels = []
    for lid, rows in index.items():
        leader = by_id.get(lid)
        if not leader:
            continue
        old_n = before.get(lid, 0)
        for row in (rows or [])[old_n:]:
            slug = row.get("slug")
            if not slug:
                continue
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
    idx = (ROOT / "sitemap.xml").read_text()
    idx = re.sub(r"(sitemap-core.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    idx = re.sub(r"(sitemap-lists.xml</loc><lastmod>)[^<]+", rf"\g<1>{today}", idx)
    (ROOT / "sitemap.xml").write_text(idx)


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    tier = load("tierlist", "/workspace/scripts/build-tier-list.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")

    index = more.load_index()
    before = {L["id"]: len(index.get(L["id"]) or []) for L in gen.LEADERS}
    print("yellow enel already hosted", before.get(ENEL_ID, 0), flush=True)
    tournaments = fetch_all_tournaments(gen)
    print("tournaments", len(tournaments), flush=True)
    target = {L["id"] for L in gen.LEADERS}
    by_leader = fetch_standings(gen, tournaments, target)
    leaders = list(gen.LEADERS)
    planned: dict[str, list] = {}
    for leader in leaders:
        lid = leader["id"]
        raw = by_leader.get(lid) or []
        if lid == ENEL_ID:
            fresh = more.pick_fresh(
                leader,
                raw,
                index,
                extra_limit=ENEL_LIMIT,
                per_event=ENEL_PER_EVENT,
            )
        else:
            fresh = more.pick_fresh(
                leader,
                raw,
                index,
                extra_limit=GENERAL_LIMIT,
                per_event=GENERAL_PER_EVENT,
            )
        planned[lid] = fresh
        if fresh or lid == ENEL_ID:
            print(lid, "new", len(fresh), "raw", len(raw), flush=True)
    write_planned(gen, more, index, leaders, planned)
    more.save_index(index)
    after = {lid: len(index.get(lid) or []) for lid in before}
    changed = {lid for lid in before if after[lid] > before[lid]}
    enel_new = after.get(ENEL_ID, 0) - before.get(ENEL_ID, 0)
    general_new = sum(after[lid] - before[lid] for lid in before) - enel_new
    print("enel new", enel_new, "general new", general_new, "leaders", len(changed), flush=True)
    if changed:
        more.rebuild_hubs(index, only_ids=changed)
    tier.patch_all_pages = lambda: 0
    tier.main()
    up.patch_home()
    rels = list_rels(gen, before, index)
    update_sitemaps(rels)
    summary = {
        "enel_id": ENEL_ID,
        "enel_new": enel_new,
        "enel_total": after.get(ENEL_ID, 0),
        "general_new": general_new,
        "hosted": len(rels),
        "changed_leaders": sorted(changed),
    }
    (ROOT / "data/yellow-enel-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print("DONE", json.dumps({"enel_new": enel_new, "general_new": general_new, "hosted": len(rels)}), flush=True)


if __name__ == "__main__":
    main()
