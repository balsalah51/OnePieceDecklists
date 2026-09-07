#!/usr/bin/env python3
"""Create Ace / Enel / Katakuri hub pages and fill them with unique Limitless lists."""

from __future__ import annotations

import html
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

aspec = importlib.util.spec_from_file_location("more", "/workspace/scripts/add-more-tournament-lists.py")
more = importlib.util.module_from_spec(aspec)
aspec.loader.exec_module(more)

ROOT = gen.ROOT
NEW_IDS = {"OP16-001", "OP15-058", "OP11-062"}
BLURBS = {
    "OP16-001": "Red OP16 Portgas D. Ace. Once per turn, give Rush to a Monkey D. Luffy character or a Whitebeard Pirates character with 8000 power or more.",
    "OP15-058": "Purple OP15 Enel. Your DON!! deck is 6 cards. From turn two you ramp DON!! and rest the opponent's board.",
    "OP11-062": "Purple OP11 Charlotte Katakuri. Once per turn on attack or on your opponent's attack, DON!! −1 to look at the top of their deck and gain power.",
}


def write_hub(leader: dict, card: dict) -> None:
    name = gen.display_name(card.get("name") or leader["name"])
    color = card.get("color") or ""
    types = card.get("types") or ""
    effect = card.get("effect") or ""
    img = card.get("image") or gen.card_image_url(leader["id"])
    crumb_href, crumb_label = leader["crumb"]
    pills = [
        f"{color} Leader" if color else "Leader",
        leader["id"],
    ]
    if card.get("life"):
        pills.append(f"{card['life']} Life")
    if card.get("power"):
        pills.append(f"{card['power']} Power")
    if card.get("attribute"):
        pills.append(card["attribute"])
    if types:
        pills.append(types)
    pill_html = "\n              ".join(f'<span class="pill">{html.escape(p)}</span>' for p in pills)
    note = {
        "OP16-001": "Red OP16 Ace. The red/blue OP13 Ace page is separate.",
        "OP15-058": "Purple OP15 Enel. Not yellow OP05 Enel.",
        "OP11-062": "Purple OP11 Katakuri. Not yellow OP17 Linlin.",
    }.get(leader["id"], "Current-format leader.")
    body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="{html.escape(crumb_href)}">{html.escape(crumb_label)}</a> / {html.escape(name)}</div>
        <div class="leader-hero">
          <img src="{html.escape(img)}" alt="{html.escape(name)} leader" />
          <div>
            <h2>{html.escape(name)}</h2>
            <p>{html.escape(BLURBS[leader['id']])}</p>
            <div class="stat-row">
              {pill_html}
            </div>
            <div class="effect">{html.escape(effect)}</div>
            <p class="muted" style="margin-top:12px">{html.escape(note)}</p>
          </div>
        </div>

        <!-- TOURNAMENT_DECKLISTS -->
        <section class="deck-index" style="margin-top:22px">
          <div class="section-title">
            <h3>Tournament decklists</h3>
            <div class="muted">0 lists</div>
          </div>
          <p class="muted">Fetching Limitless lists for this leader.</p>
        </section>
        <!-- /TOURNAMENT_DECKLISTS -->
"""
    page = gen.page_chrome(
        f"{name} decklist",
        f"{name} - {color} leader page and tournament lists."[:160],
        leader["color"],
        leader["nav_op17"],
        body,
    )
    path = ROOT / leader["page"]
    path.write_text(page)
    print("hub page", path)


def fetch_new(index: dict) -> dict:
    target_ids = NEW_IDS
    print("fetching tournament pages for new leaders")
    tournaments = more.fetch_tournament_pages(pages=8)
    print("tournaments", len(tournaments))
    by_leader = gen.fetch_standings(tournaments, target_ids)
    cache = gen.load_card_cache()
    needed = set()
    planned = {}
    for leader in gen.LEADERS:
        lid = leader["id"]
        if lid not in target_ids:
            continue
        have = more.existing_stems(leader)
        picked = gen.select_lists(by_leader.get(lid) or [], limit=40)
        fresh = []
        for entry in picked:
            slug = gen.planned_slug(entry)
            if slug in have:
                continue
            href = f"/{leader['dir']}/{slug}.html"
            entry = dict(entry)
            entry["slug"] = slug
            entry["href"] = href
            fresh.append(entry)
            have.add(slug)
            for item in gen.flatten_cards(entry["decklist"]):
                needed.add(item["id"])
            if len(fresh) >= 32:
                break
        planned[lid] = fresh
        print(lid, "new unique", len(fresh), "raw", len(by_leader.get(lid) or []))
    cache = gen.ensure_cards(needed, cache)
    for leader in gen.LEADERS:
        lid = leader["id"]
        fresh = planned.get(lid) or []
        if not fresh:
            continue
        out_dir = ROOT / leader["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        for entry in fresh:
            page = gen.render_deck_page(leader, entry, cache)
            (out_dir / f"{entry['slug']}.html").write_text(page)
            index.setdefault(lid, []).append(more.index_row(entry))
    return index


def main() -> None:
    cache = gen.ensure_cards(NEW_IDS, gen.load_card_cache())
    for leader in gen.LEADERS:
        if leader["id"] not in NEW_IDS:
            continue
        card = cache.get(leader["id"]) or {}
        write_hub(leader, card)
    index = more.load_index()
    index = fetch_new(index)
    more.save_index(index)
    more.rebuild_hubs(index)
    print("done")


if __name__ == "__main__":
    main()
