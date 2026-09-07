#!/usr/bin/env python3
"""Append extra unique Limitless tournament lists and rebuild leader hub HTML.

Does not wipe community list pages. Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import importlib.util

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

cspec = importlib.util.spec_from_file_location("commlists", "/workspace/scripts/add-community-lists.py")
comm = importlib.util.module_from_spec(cspec)
cspec.loader.exec_module(comm)

ROOT = gen.ROOT
SITE = "https://onepiecedecklists.com"
EXTRA_LIMIT = 80
PAGES = 70
PER_PAGE = 40
PER_EVENT = 4
HUB_BLOCK_RE = re.compile(
    r"        <!-- (?:COMMUNITY_DECKLISTS|TOURNAMENT_DECKLISTS) -->.*?        <!-- /TOURNAMENT_DECKLISTS -->",
    re.S,
)
NEWGATE_TOURNAMENT = """        <!-- TOURNAMENT_DECKLISTS -->
        <section class="deck-index" style="margin-top:22px">
          <div class="section-title">
            <h3>Tournament decklists</h3>
            <div class="muted">0 lists</div>
          </div>
          <p class="muted">No Limitless standings for this leader yet. Community lists are above.</p>
        </section>
        <!-- /TOURNAMENT_DECKLISTS -->"""


def load_index() -> dict:
    path = ROOT / "data/tournament-decks.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_index(index: dict) -> None:
    (ROOT / "data/tournament-decks.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")


def existing_stems(leader: dict) -> set[str]:
    d = ROOT / leader["dir"]
    if not d.exists():
        return set()
    return {p.stem for p in d.glob("*.html")}


def known_results(leader: dict, index: dict) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for item in index.get(leader["id"]) or []:
        player = (item.get("player") or "").strip().lower()
        url = item.get("source_url") or ""
        m = re.search(r"/tournament/([^/]+)/", url)
        if m and player:
            keys.add((m.group(1), player))
    return keys


def prune_duplicate_lists(index: dict) -> dict:
    cleaned: dict[str, list] = {}
    for leader in gen.LEADERS:
        lid = leader["id"]
        items = index.get(lid) or []
        stems = existing_stems(leader)
        kept = []
        seen = set()
        for item in items:
            slug = item.get("slug") or ""
            kind = item.get("kind")
            path = ROOT / leader["dir"] / f"{slug}.html"
            if kind == "sample":
                if path.exists():
                    path.unlink()
                    print("removed sample", path)
                continue
            if slug.endswith("-2") and slug[:-2] in stems:
                if path.exists():
                    path.unlink()
                    print("removed duplicate", path)
                continue
            if slug in seen:
                continue
            if not path.exists():
                continue
            if gen.page_has_banned(path.read_text()):
                path.unlink()
                print("removed banned", path)
                continue
            seen.add(slug)
            kept.append(item)
        cleaned[lid] = kept
        print(lid, "kept", len(kept), "of", len(items))
    return cleaned


def community_entries(leader: dict) -> list[dict]:
    out = []
    seen = set()
    static = list(comm.COMMUNITY.get(leader["id"], []))
    extra_path = ROOT / "data/community-decks.json"
    if extra_path.exists():
        extra = json.loads(extra_path.read_text()).get(leader["id"]) or []
        static.extend(extra)
    for item in static:
        slug = item.get("slug") or ""
        href = item.get("href") or f"/{leader['dir']}/{slug}.html"
        if slug in seen:
            continue
        if not (ROOT / href.lstrip("/")).exists():
            continue
        seen.add(slug)
        out.append(
            {
                "href": href,
                "title": item.get("title") or slug,
                "subtitle": item.get("subtitle") or "",
                "kind": item.get("kind"),
                "slug": slug,
                "date": item.get("date") or "",
            }
        )
    out.sort(key=gen.date_sort_key, reverse=True)
    return out


def tournament_entries(leader: dict, items: list[dict]) -> list[dict]:
    out = []
    for item in items:
        kind = item.get("kind")
        if kind in ("sample", "youtube", "web", "x"):
            continue
        slug = item.get("slug") or ""
        path = ROOT / leader["dir"] / f"{slug}.html"
        if not path.exists():
            continue
        entry = dict(item)
        entry["tournament_name"] = entry.get("tournament_name") or entry.get("tournament") or "Limitless event"
        out.append(entry)
    return out


def rebuild_hubs(index: dict, only_ids: set[str] | None = None) -> None:
    for leader in gen.LEADERS:
        if only_ids is not None and leader["id"] not in only_ids:
            continue
        lid = leader["id"]
        page_path = ROOT / leader["page"]
        if not page_path.exists():
            print("skip missing hub", page_path)
            continue
        page = page_path.read_text()
        comm_lists = community_entries(leader)
        tour_lists = tournament_entries(leader, index.get(lid) or [])
        tour_lists.sort(key=gen.date_sort_key, reverse=True)
        if lid == "OP17-001" and not tour_lists:
            tournament_html = NEWGATE_TOURNAMENT
        else:
            tournament_html = gen.render_index_section(leader, tour_lists)
        if comm_lists:
            combined = comm.community_section(leader, comm_lists, tournament_html)
        else:
            combined = tournament_html
        page = re.sub(
            r"        <!-- COMMUNITY_DECKLISTS -->.*?        <!-- /COMMUNITY_DECKLISTS -->\n?",
            "",
            page,
            count=1,
            flags=re.S,
        )
        m = HUB_BLOCK_RE.search(page)
        if m:
            page = page[: m.start()] + combined + page[m.end() :]
        else:
            page = gen.insert_section(page, combined, gen.render_pool_heading(leader))
        page_path.write_text(page)
        print(
            "hub",
            leader["page"],
            "community",
            len(comm_lists),
            "tournament",
            len(tour_lists),
        )


def index_row(entry: dict) -> dict:
    return {
        "slug": entry["slug"],
        "href": entry["href"],
        "player": entry.get("player"),
        "tournament": entry.get("tournament_name"),
        "placing": entry.get("placing"),
        "date": entry.get("date"),
        "kind": entry.get("kind"),
        "source_url": entry.get("source_url"),
    }


def fetch_tournament_pages(pages: int = PAGES, per_page: int = PER_PAGE) -> list:
    seen = []
    ids = set()
    for page in range(1, pages + 1):
        batch = gen.http_json(
            f"https://play.limitlesstcg.com/api/tournaments?game=OP&limit={per_page}&page={page}"
        )
        added = 0
        for tourney in batch or []:
            tid = tourney.get("id")
            if not tid or tid in ids:
                continue
            ids.add(tid)
            seen.append(tourney)
            added += 1
        print("page", page, "new", added, "unique", len(seen))
    return seen


def pick_fresh(
    leader: dict,
    entries: list[dict],
    index: dict,
    extra_limit: int = EXTRA_LIMIT,
    per_event: int = PER_EVENT,
    require_op17: bool = False,
) -> list[dict]:
    have = existing_stems(leader)
    known = known_results(leader, index)
    per_event_counts: dict[str, int] = {}
    fresh = []
    def pick_key(entry: dict) -> tuple:
        # Prefer lists that already splash an OP17 card, then the usual quality order.
        has_op17 = 0 if gen.deck_has_op17(entry.get("decklist") or {}) else 1
        return (has_op17,) + gen.quality_key(entry)

    for entry in sorted(entries, key=pick_key):
        if entry.get("kind") == "sample":
            continue
        dl = entry.get("decklist") or {}
        if gen.count_cards(dl) < gen.MIN_CARDS:
            continue
        if gen.deck_has_banned(dl):
            continue
        if require_op17 and not gen.deck_has_op17(dl):
            continue
        player = (entry.get("player") or "").strip().lower()
        tid = entry.get("tournament_id") or ""
        if tid and player and (tid, player) in known:
            continue
        if per_event_counts.get(tid, 0) >= per_event:
            continue
        slug = gen.unique_slug(entry, have)
        href = f"/{leader['dir']}/{slug}.html"
        row = dict(entry)
        row["slug"] = slug
        row["href"] = href
        fresh.append(row)
        if tid and player:
            known.add((tid, player))
        per_event_counts[tid] = per_event_counts.get(tid, 0) + 1
        if len(fresh) >= extra_limit:
            break
    return fresh


def fetch_more(
    index: dict,
    pages: int = PAGES,
    only_ids: set[str] | None = None,
    extra_limit: int | None = None,
    per_event: int | None = None,
    since: str | None = None,
    require_op17: bool = False,
) -> dict:
    target_ids = only_ids or {L["id"] for L in gen.LEADERS}
    leaders = [L for L in gen.LEADERS if L["id"] in target_ids]
    limit = EXTRA_LIMIT if extra_limit is None else extra_limit
    event_cap = PER_EVENT if per_event is None else per_event
    print("fetching tournament pages", pages, "extra_limit", limit, "per_event", event_cap, "since", since)
    tournaments = fetch_tournament_pages(pages=pages)
    if since:
        tournaments = [t for t in tournaments if (t.get("date") or "")[:10] >= since]
        print("kept since", since, len(tournaments))
    print("tournaments", len(tournaments), "scanning", sorted(target_ids))
    by_leader = gen.fetch_standings(tournaments, target_ids)
    cache = gen.load_card_cache()
    needed = set()
    planned: dict[str, list] = {}
    for leader in leaders:
        lid = leader["id"]
        fresh = pick_fresh(
            leader,
            by_leader.get(lid) or [],
            index,
            extra_limit=limit,
            per_event=event_cap,
            require_op17=require_op17,
        )
        planned[lid] = fresh
        for entry in fresh:
            for item in gen.flatten_cards(entry["decklist"]):
                needed.add(item["id"])
        print(lid, "new lists", len(fresh), "raw", len(by_leader.get(lid) or []))
    cache = gen.ensure_cards(needed, cache)
    for leader in leaders:
        lid = leader["id"]
        fresh = planned.get(lid) or []
        if not fresh:
            continue
        out_dir = ROOT / leader["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        for entry in fresh:
            page = gen.render_deck_page(leader, entry, cache)
            (out_dir / f"{entry['slug']}.html").write_text(page)
            index.setdefault(lid, []).append(index_row(entry))
    return index


def rewrite_sitemap() -> None:
    skip = {".git", "scripts", "node_modules", "discord-bot"}
    skip_files = {"shop/custom-leaders.html"}
    urls = []
    for p in sorted(ROOT.rglob("*.html")):
        if any(part in p.parts for part in skip):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in skip_files:
            continue
        if rel.endswith("index.html"):
            url = SITE + "/" if rel == "index.html" else SITE + "/" + rel[: -len("index.html")]
        else:
            url = SITE + "/" + rel
        urls.append(url)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        lines.append(f"  <url><loc>{url}</loc></url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n")
    print("sitemap", len(urls))


def main() -> None:
    index = load_index()
    index = fetch_more(index, pages=PAGES)
    save_index(index)
    rebuild_hubs(index)
    rewrite_sitemap()
    print("done")


if __name__ == "__main__":
    main()
