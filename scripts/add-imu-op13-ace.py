#!/usr/bin/env python3
"""Create Imu and OP13 Ace hub pages. OP16 Ace stays the red OP16-001 page."""

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
NEW_IDS = {"OP13-079", "OP13-002"}
BLURBS = {
    "OP13-079": "Black OP13 Imu. You cannot play 2-cost or higher events. At the start of the game you may play a Mary Geoise stage, then trash Celestial Dragons or a card from hand to draw.",
    "OP13-002": "Red/Blue OP13 Portgas D. Ace. 3 life, 6000 power. Trash a card to give −2000, then draw when you take damage or a 6000-power character is K.O.'d. Not the red OP16 Ace.",
}


def write_hub(leader: dict, card: dict) -> None:
    name = leader["name"]
    full = gen.display_name(card.get("name") or leader["name"])
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
    if card.get("attribute") and str(card.get("attribute")).strip() not in {"", "?"}:
        pills.append(card["attribute"])
    if types and str(types).strip() not in {"", "?"}:
        pills.append(types)
    pill_html = "\n              ".join(f'<span class="pill">{html.escape(p)}</span>' for p in pills)
    note = {
        "OP13-079": "Black OP13 Imu. Not OP17 Elbaph Luffy.",
        "OP13-002": "Red/blue OP13-002. The red OP16 Ace page is separate.",
    }.get(leader["id"], "Current-format leader.")
    body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="{html.escape(crumb_href)}">{html.escape(crumb_label)}</a> / {html.escape(name)}</div>
        <div class="leader-hero">
          <img src="{html.escape(img)}" alt="{html.escape(full)} leader" />
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
        f"{full} - {color} leader page and tournament lists."[:160],
        leader["color"],
        leader["nav_op17"],
        body,
    )
    path = ROOT / leader["page"]
    path.write_text(page)
    print("hub page", path)


def main() -> None:
    cache = gen.ensure_cards(NEW_IDS, gen.load_card_cache())
    for leader in gen.LEADERS:
        if leader["id"] not in NEW_IDS:
            continue
        card = cache.get(leader["id"]) or {}
        write_hub(leader, card)
    print("hubs ready")


if __name__ == "__main__":
    main()
