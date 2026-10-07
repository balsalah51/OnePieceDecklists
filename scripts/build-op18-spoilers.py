#!/usr/bin/env python3
"""Write the static OP18 spoilers page from the revealed-card list."""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "op18-spoilers.html"
IMG = "https://cards.oplaytcg.com/OP18/en/{id}.webp"

# Public reveals as of 7 October 2026. English text follows spoiler
# translations. Kokoro and Mr. 9 are translated from the Japanese list.
CARDS = [
    {
        "id": "OP18-001",
        "name": "Karoo",
        "aliases": "Carue カルー",
        "kind": "leader",
        "rarity": "Leader",
        "colors": ["Red", "Blue"],
        "power": "5000",
        "life": "4",
        "attribute": "Strike",
        "types": ["Animal", "Alabasta"],
        "effect": "All of your Characters with both the {Animal} and {Alabasta} types gain [Rush] and +1000 power. [Once Per Turn] When your {Alabasta} type Character is K.O.'d, draw 1 card.",
        "image": True,
    },
    {
        "id": "OP18-003",
        "name": "Sea Cat",
        "aliases": "海ネコ",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Red"],
        "cost": "5",
        "power": "6000",
        "counter": "+2000",
        "attribute": "Wisdom",
        "types": ["Animal", "Alabasta"],
        "effect": "No effect.",
        "image": True,
    },
    {
        "id": "OP18-011",
        "name": "Nefertari Vivi",
        "aliases": "Vivi",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Red"],
        "cost": "2",
        "power": "0",
        "counter": "+1000",
        "attribute": "Wisdom",
        "types": ["Alabasta"],
        "effect": "All of your Characters with both the {Animal} and {Alabasta} types gain +1000 power. [Opponent's Turn] This Character gains [Blocker] and +6000 power.",
        "image": True,
    },
    {
        "id": "OP18-016",
        "name": "Monkey D. Luffy",
        "aliases": "Monkey.D.Luffy Alabasta",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Red"],
        "cost": "6",
        "power": "7000",
        "counter": "+1000",
        "attribute": "Strike",
        "types": ["Alabasta", "Straw Hat Crew"],
        "effect": "[Banish] [On K.O.] Play up to 1 {Alabasta} type Character card with 6000 power or less from your hand.",
        "image": True,
    },
    {
        "id": "OP18-017",
        "name": "Roronoa Zoro",
        "aliases": "Zoro",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Red"],
        "cost": "4",
        "power": "4000",
        "counter": "+1000",
        "attribute": "Slash",
        "types": ["Alabasta", "Straw Hat Crew"],
        "effect": "[Once Per Turn] If your {Alabasta} type Character would be removed from the field by your opponent's effect, you may give your Leader −2000 power during this turn instead. [When Attacking] Up to 1 of your {Alabasta} type Characters gains [Rush] during this turn.",
        "image": True,
    },
    {
        "id": "OP18-021",
        "name": "Franky",
        "aliases": "フランキー",
        "kind": "leader",
        "rarity": "Leader",
        "colors": ["Green", "Purple"],
        "power": "5000",
        "life": "4",
        "attribute": "Strike",
        "types": ["Water Seven", "Franky Family", "Straw Hat Crew"],
        "effect": "All Stage cards in your hand have a +3000 Counter. [Activate: Main] [Once Per Turn] DON!! −1: Play up to 1 Stage card with a cost of 5 or less from your hand.",
        "note": "Franky's first Leader. A parallel illustration is confirmed.",
        "image": True,
    },
    {
        "id": "OP18-022",
        "name": "Monkey D. Luffy",
        "aliases": "Monkey.D.Luffy Water Seven",
        "kind": "leader",
        "rarity": "Leader",
        "colors": ["Green"],
        "power": "5000",
        "life": "5",
        "attribute": "Strike",
        "types": ["Water Seven", "Straw Hat Crew"],
        "effect": "[DON!! x3] [When Attacking] [Once Per Turn] You may set this Leader as active. If you do, this Leader will not become active in your next Refresh Phase.",
        "image": True,
    },
    {
        "id": "OP18-024",
        "name": "Kokoro",
        "aliases": "ココロ",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Green"],
        "cost": "2",
        "power": "0",
        "counter": "+1000",
        "attribute": "Wisdom",
        "types": ["Fish-Man", "Water Seven"],
        "effect": "[Blocker] (After your opponent declares an attack, you may rest this card to make it the new target of the attack.) [End of Your Turn] You may trash this Character: Set your Leader as active.",
        "note": "Translated from the Japanese reveal. An English spoiler page for this number was not up yet.",
        "image": False,
    },
    {
        "id": "OP18-025",
        "name": "Gonbe",
        "aliases": "ゴンベ",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Green"],
        "cost": "1",
        "power": "0",
        "counter": "+1000",
        "attribute": "Wisdom",
        "types": ["Animal", "Water Seven"],
        "effect": "[End of Your Turn] If this Character is rested, set your Leader as active.",
        "image": True,
    },
    {
        "id": "OP18-028",
        "name": "Chimney",
        "aliases": "チムニー",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Green"],
        "cost": "2",
        "power": "0",
        "counter": "+1000",
        "attribute": "Wisdom",
        "types": ["Water Seven"],
        "effect": "[Activate: Main] You may rest 1 of your [Gonbe] and this Character: Set your [Monkey D. Luffy] Leader as active.",
        "image": True,
    },
    {
        "id": "OP18-031",
        "name": "Nico Robin",
        "aliases": "Robin comic super parallel",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Green"],
        "cost": "4",
        "power": "5000",
        "counter": "+1000",
        "attribute": "Wisdom",
        "types": ["Water Seven", "Straw Hat Crew"],
        "effect": "[Opponent's Turn] If your Character would be removed from the field by your opponent's effect, you may rest this Character instead. [End of Your Turn] Set up to 1 of your {Water Seven} type cards and up to 1 of your DON!! cards as active.",
        "note": "Super Parallel, the comic treatment. Its block icon is listed as X.",
        "image": True,
    },
    {
        "id": "OP18-034",
        "name": "Franky",
        "aliases": "フランキー character",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Green"],
        "cost": "6",
        "power": "7000",
        "attribute": "Strike",
        "types": ["Water Seven", "Franky Family", "Straw Hat Crew"],
        "effect": "[On Play] Play up to 1 {Franky Family} or {Straw Hat Crew} type card with a cost of 5 or less from your hand. Then, if you have a Stage with a cost of 5 or more, rest up to 1 of your opponent's Characters with a cost of 6 or less.",
        "image": True,
    },
    {
        "id": "OP18-041",
        "name": "Ms. All Sunday",
        "aliases": "Ms. All Sunday Nico Robin Baroque Works",
        "kind": "leader",
        "rarity": "Leader",
        "colors": ["Blue"],
        "power": "5000",
        "life": "5",
        "attribute": "Wisdom",
        "types": ["Baroque Works"],
        "effect": 'When your Character with a type including "Baroque Works" and 3000 base power or more is K.O.\'d, draw 1 card, and your opponent trashes 1 card from their hand.',
        "image": True,
    },
    {
        "id": "OP18-044",
        "name": "Mr. Beans & Miss Katherina",
        "aliases": "Mr.Beans Miss.Katherina",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Blue"],
        "cost": "3",
        "power": "4000",
        "counter": "+1000",
        "attribute": "Wisdom",
        "types": ["Baroque Works"],
        "effect": "[DON!! x1] This Character gains +1000 power. [On Play] Draw 1 card and trash 1 card from your hand.",
        "image": True,
    },
    {
        "id": "OP18-046",
        "name": "Mr. 0 & Ms. All Sunday",
        "aliases": "Crocodile Ms. All Sunday",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Blue"],
        "cost": "9",
        "power": "10000",
        "attribute": "Special / Wisdom",
        "types": ["The Seven Warlords of the Sea", "Baroque Works"],
        "effect": '[On Play] Draw 2 cards and give up to 2 rested DON!! cards to your Leader and all of your Characters. [On Your Opponent\'s Attack] You may trash 1 card from your hand: Your Leader with a type including "Baroque Works" becomes 7000 base power during this turn.',
        "image": True,
    },
    {
        "id": "OP18-048",
        "name": "Mr. 1 & Miss Doublefinger",
        "aliases": "Doublefinger",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Blue"],
        "cost": "6",
        "power": "6000",
        "attribute": "Slash",
        "types": ["Baroque Works"],
        "effect": '[Rush] [On Play] Play up to 1 Character card with a type including "Baroque Works" and a cost of 5 or less from your hand.',
        "image": True,
    },
    {
        "id": "OP18-055",
        "name": "Mr. 9 & Miss Wednesday",
        "aliases": "Vivi Wednesday",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Blue"],
        "cost": "3",
        "power": "4000",
        "counter": "+1000",
        "attribute": "Slash / Strike",
        "types": ["Baroque Works"],
        "effect": "[DON!! x1] This Character gains +1000 power. [On Play] Return up to 1 of your opponent's Characters with a cost of 2 or less to the owner's hand.",
        "note": "Translated from the Japanese reveal. An English spoiler page for this number was not up yet.",
        "image": False,
    },
    {
        "id": "OP18-056",
        "name": "Mr. 13 & Miss Friday",
        "aliases": "Mr.13 Ms.Friday",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Blue"],
        "cost": "2",
        "power": "3000",
        "counter": "+1000",
        "attribute": "Wisdom",
        "types": ["Animal", "Baroque Works"],
        "effect": '[DON!! x1] This Character gains +1000 power. [On Play] You may place 1 of your Characters with a type including "Baroque Works", other than this Character, at the bottom of your deck: Your opponent trashes 1 card from their hand.',
        "image": True,
    },
    {
        "id": "OP18-060",
        "name": "Saint Gunko",
        "aliases": "Gunko 軍子宮 Holy Knights",
        "kind": "leader",
        "rarity": "Leader",
        "colors": ["Purple", "Black"],
        "power": "5000",
        "life": "4",
        "attribute": "Special",
        "types": ["Celestial Dragons", "Holy Knights of God"],
        "effect": "[Once Per Turn] When a Character is played from your trash, draw 2 cards and trash 1 card from your hand. [Activate: Main] [Once Per Turn] You may trash 1 card from your hand: If you have a Character with 8000 base power or more, add up to 1 DON!! card as active from your DON!! deck.",
        "note": "Debut Leader. A parallel illustration is confirmed.",
        "image": True,
    },
    {
        "id": "OP18-061",
        "name": "Iceburg",
        "aliases": "Iceberg Galley-La",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Purple"],
        "cost": "2",
        "power": "0",
        "counter": "+1000",
        "attribute": "Special",
        "types": ["Water Seven", "Galley-La Company"],
        "effect": "[On Play] Look at 5 cards from the top of your deck; reveal up to a total of 2 Stage cards or {Water Seven} types cards and add them to your hand. Then, place the rest at the bottom of your deck in any order.",
        "image": True,
    },
    {
        "id": "OP18-065",
        "name": "Saint Gunko",
        "aliases": "Gunko super parallel God's Knights 軍子宮",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Purple"],
        "cost": "10",
        "power": "11000",
        "attribute": "?",
        "types": ["Celestial Dragons", "Holy Knights of God"],
        "effect": "[Blocker] [On Play] DON!! −1: Play up to 1 {Celestial Dragons} type Character card with 6000 power or less from your trash.",
        "note": "God's Knights Super Parallel, the 4th-anniversary treatment. The sample is purple, the attribute icon is ?, and the block icon is X. An earlier Japanese row printed this card as Black.",
        "image": True,
    },
    {
        "id": "OP18-066",
        "name": "Zambai",
        "aliases": "ザンバイ",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Purple"],
        "cost": "5",
        "power": "6000",
        "counter": "+1000",
        "attribute": "Slash",
        "types": ["Water Seven", "Franky Family"],
        "effect": "[Activate: Main] You may K.O. 1 of your Stages with a cost of 5 or less: This Character gains [Rush] during this turn.",
        "image": True,
    },
    {
        "id": "OP18-076",
        "name": "Shark Submerge 3",
        "aliases": "Shark Submerge III stage",
        "kind": "stage",
        "rarity": "Uncommon",
        "colors": ["Purple"],
        "cost": "5",
        "types": ["Straw Hat Crew"],
        "effect": "[On Play] Draw 1 card, then add up to 1 DON!! card as rested from your DON!! deck. [On Your Opponent's Attack] You may rest this Stage: Your Leader with 5000 power or less and up to 2 of your Characters gain +1000 power during this turn.",
        "image": True,
    },
    {
        "id": "OP18-078",
        "name": "Mini-Merry",
        "aliases": "Mini-Merry Mini Merry II ミニメリー号 stage",
        "kind": "stage",
        "rarity": "Uncommon",
        "colors": ["Purple"],
        "cost": "5",
        "types": ["Straw Hat Crew"],
        "effect": "[On Play] Draw 1 card, then add up to 1 DON!! card as rested from your DON!! deck. [Activate: Main] You may rest this Stage: Give up to a total of 4 of your Leader or Characters 1 rested DON!! card each.",
        "image": True,
    },
    {
        "id": "OP18-079",
        "name": "Spandam",
        "aliases": "スパンダム CP9",
        "kind": "leader",
        "rarity": "Leader",
        "colors": ["Black", "Yellow"],
        "power": "5000",
        "life": "4",
        "attribute": "Slash",
        "types": ["CP9"],
        "effect": '[Activate: Main] You may rest 2 of your DON!! cards and this Leader, and trash 1 card with a type including "CP" from your hand: Add up to 1 card from the top of your deck to the top of your Life cards.',
        "image": True,
    },
    {
        "id": "OP18-084",
        "name": "Gunko",
        "aliases": "Saint Gunko 軍子宮 Knights of God",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Black"],
        "cost": "1",
        "power": "2000",
        "attribute": "Special",
        "types": ["Celestial Dragons", "Knights of God"],
        "effect": "[On Play] Look at 4 cards from the top of your deck; reveal up to 1 {Knights of God} type card and add it to your hand. Then, place the rest into the trash. [Activate: Main] You may rest 4 of your DON!! cards: Play up to 1 {Knights of God} type Character card with a cost of 6 or less from your trash.",
        "note": "This print says Knights of God. Saint Gunko and Saint Shamrock print the same Japanese type as Holy Knights of God.",
        "image": True,
    },
    {
        "id": "OP18-086",
        "name": "Goldberg",
        "aliases": "New Giant Pirates",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Black"],
        "cost": "3",
        "power": "4000",
        "counter": "+1000",
        "attribute": "Strike",
        "types": ["Giant", "Elbaph", "New Giant Pirates"],
        "effect": "This Character gains +12 cost. [On K.O.] K.O. up to 1 of your opponent's Characters with a cost of 4 or less.",
        "image": True,
    },
    {
        "id": "OP18-089",
        "name": "Dorry",
        "aliases": "Giant Pirates",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Black"],
        "cost": "4",
        "power": "5000",
        "counter": "+2000",
        "attribute": "Slash",
        "types": ["Giant", "Elbaph", "Giant Pirates"],
        "effect": "This Character gains +12 cost. [On Play] You may trash 1 card from your hand: Your opponent trashes 1 card from their hand.",
        "image": True,
    },
    {
        "id": "OP18-093",
        "name": "MMA",
        "aliases": "Elbaph",
        "kind": "character",
        "rarity": "Rare",
        "colors": ["Black"],
        "cost": "9",
        "power": "3000",
        "counter": "+2000",
        "attribute": "Special",
        "types": ["Elbaph"],
        "effect": "You may include any number of this card in your deck. [Blocker] (After your opponent declares an attack, you may rest this card to make it the new target of the attack.)",
        "image": True,
    },
    {
        "id": "OP18-100",
        "name": "Khalifa",
        "aliases": "Kalifa CP9",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Yellow"],
        "cost": "6",
        "power": "7000",
        "counter": "+1000",
        "attribute": "Special",
        "types": ["CP9"],
        "effect": '[On Play] Draw 1 card and add up to 1 card with a type including "CP" from your hand, face-up, to the top or bottom of your Life cards. [Trigger] If your Leader has a type including "CP", draw 1 card and rest up to 1 of your opponent\'s Leader or Character cards.',
        "image": True,
    },
    {
        "id": "OP18-106",
        "name": "Doberman",
        "aliases": "Vice Admiral Navy",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Yellow"],
        "cost": "7",
        "power": "7000",
        "counter": "+2000",
        "attribute": "Slash",
        "types": ["Vice Admiral", "Navy"],
        "effect": "[Double Attack] (This card deals 2 damage.)",
        "image": True,
    },
    {
        "id": "OP18-112",
        "name": "Yamakaji",
        "aliases": "Vice Admiral Navy",
        "kind": "character",
        "rarity": "Common",
        "colors": ["Yellow"],
        "cost": "7",
        "power": "7000",
        "counter": "+2000",
        "attribute": "Slash",
        "types": ["Vice Admiral", "Navy"],
        "effect": "[Blocker] (After your opponent declares an attack, you may rest this card to make it the new target of the attack.)",
        "image": True,
    },
    {
        "id": "OP18-113",
        "name": "Rob Lucci",
        "aliases": "Lucci CP9",
        "kind": "character",
        "rarity": "Super Rare",
        "colors": ["Yellow"],
        "cost": "8",
        "power": "10000",
        "attribute": "Strike",
        "types": ["CP9"],
        "effect": '[On Play] / [On K.O.] Trash up to 1 card from the top of your opponent\'s Life cards. [Trigger] If your Leader has a type including "CP", draw 1 card and place up to 1 Character with a cost of 8 or less at the bottom of the owner\'s deck.',
        "image": True,
    },
    {
        "id": "OP18-119",
        "name": "Saint Shamrock",
        "aliases": "Figarland Shamrock シャムロック聖 Amano",
        "kind": "character",
        "rarity": "Secret Rare",
        "colors": ["Black"],
        "cost": "8",
        "power": "9000",
        "attribute": "Slash",
        "types": ["Celestial Dragons", "Holy Knights of God"],
        "effect": "[On K.O.] You may trash 1 card from your hand: Play this Character card from your trash. [Activate: Main] [Once Per Turn] If this Character was played this turn, play up to 1 {Holy Knights of God} type Character card with a cost of 6 or less from your trash.",
        "note": "Yoshitaka Amano drew a parallel and a foil-stamped parallel.",
        "image": True,
    },
]


def e(value: str) -> str:
    return escape(value, quote=True)


def color_class(colors: list[str]) -> str:
    return "color-" + "-".join(c.lower() for c in colors)


def stats(card: dict) -> str:
    parts = []
    if card.get("cost"):
        parts.append(f"{card['cost']} cost")
    if card.get("power"):
        parts.append(f"{card['power']} power")
    if card.get("life"):
        parts.append(f"{card['life']} life")
    if card.get("counter"):
        parts.append(f"{card['counter']} counter")
    if card.get("attribute"):
        parts.append("attribute ?" if card["attribute"] == "?" else card["attribute"])
    if card.get("types"):
        parts.append(" / ".join(card["types"]))
    return " · ".join(parts)


def picture(card: dict, leader: bool = False) -> str:
    label = f"{card['name']} {card['id']}"
    if not card["image"]:
        return f'<div class="spoiler-missing" role="img" aria-label="{e(label)}">{e(card["id"])}</div>'
    img = (
        f'<img src="{IMG.format(id=card["id"])}" alt="{e(label)}" '
        f'width="300" height="419" loading="lazy" decoding="async" referrerpolicy="no-referrer" />'
    )
    if leader:
        return img
    return (
        f'<button type="button" class="spoiler-shot" data-spoiler-open '
        f'aria-label="Enlarge {e(label)}">{img}</button>'
    )


def leader_tile(card: dict) -> str:
    return (
        f'<a class="spoiler-leader {color_class(card["colors"])}" href="#{e(card["id"])}">'
        f"{picture(card, leader=True)}"
        f"<span>{e(card['name'])}<br>{e(card['id'])}</span></a>"
    )


def card_article(card: dict) -> str:
    colors = " ".join(c.lower() for c in card["colors"])
    query = " ".join(
        [
            card["id"],
            card["name"],
            card.get("aliases", ""),
            card["rarity"],
            card["kind"],
            " ".join(card["colors"]),
            " ".join(card.get("types") or []),
            card["effect"],
            card.get("note", ""),
        ]
    ).lower()
    note = ""
    if card.get("note"):
        note = f'<p class="spoiler-note">{e(card["note"])}</p>'
    return f"""<article class="spoiler-card {color_class(card["colors"])}" id="{e(card["id"])}" data-spoiler-card data-kind="{e(card["kind"])}" data-colors="{e(colors)}" data-q="{e(query)}">
            {picture(card)}
            <div class="spoiler-body">
              <div class="spoiler-kicker">
                <span class="spoiler-id">{e(card["id"])}</span>
                <span class="spoiler-pill">{e(card["rarity"])}</span>
                <span class="spoiler-pill">{" / ".join(card["colors"])}</span>
              </div>
              <h3>{e(card["name"])}</h3>
              <p class="spoiler-stats">{e(stats(card))}</p>
              <p class="spoiler-effect">{e(card["effect"])}</p>
              {note}
            </div>
          </article>"""


def render() -> str:
    count = len(CARDS)
    leaders = "\n          ".join(leader_tile(c) for c in CARDS if c["kind"] == "leader")
    articles = "\n          ".join(card_article(c) for c in CARDS)
    desc = (
        "OP18 spoilers for ONE PIECE CARD GAME booster The Dominance of God. "
        f"{count} revealed cards, including Franky, Saint Gunko, and Saint Shamrock. "
        "English release 20 November 2026."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>OP18 spoilers | The Dominance of God | One Piece Decklists</title>
  <meta name="description" content="{e(desc)}" />
  <script id="opdl-theme-boot">
    (function(){{try{{var m=document.cookie.match(/(?:^|; )opdl-theme=([^;]*)/);var t=m&&decodeURIComponent(m[1]);if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();
  </script>
  <link rel="stylesheet" href="/css/site.css?v=op18-spoilers1" />
  <link rel="canonical" href="https://onepiecedecklists.com/op18-spoilers.html" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta name="googlebot" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta name="theme-color" content="#b71c1c" />
  <link rel="icon" href="https://onepiecedecklists.com/img/opdl-logo-192.png" type="image/png" sizes="192x192" />
  <link rel="apple-touch-icon" href="https://onepiecedecklists.com/img/opdl-logo-192.png" sizes="192x192" />
  <link rel="manifest" href="/site.webmanifest" />
  <link rel="search" type="application/opensearchdescription+xml" title="One Piece Decklists" href="/opensearch.xml" />
  <link rel="alternate" hreflang="en" href="https://onepiecedecklists.com/op18-spoilers.html" />
  <link rel="alternate" hreflang="x-default" href="https://onepiecedecklists.com/op18-spoilers.html" />
  <meta name="google-adsense-account" content="ca-pub-1074015774205047" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1074015774205047" crossorigin="anonymous"></script>
  <meta property="og:site_name" content="One Piece Decklists" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="OP18 spoilers | The Dominance of God | One Piece Decklists" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="https://onepiecedecklists.com/op18-spoilers.html" />
  <meta property="og:image" content="https://onepiecedecklists.com/img/opdl-hero.jpg" />
  <meta property="og:image:alt" content="OP18 spoilers | The Dominance of God" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="OP18 spoilers | The Dominance of God | One Piece Decklists" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="https://onepiecedecklists.com/img/opdl-hero.jpg" />
  <meta name="twitter:image:alt" content="OP18 spoilers | The Dominance of God" />
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"https://onepiecedecklists.com/"}},{{"@type":"ListItem","position":2,"name":"OP18 spoilers","item":"https://onepiecedecklists.com/op18-spoilers.html"}}]}}</script>
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"When does OP18 release?","acceptedAnswer":{{"@type":"Answer","text":"English OP-18 The Dominance of God releases 20 November 2026 at $4.99 a pack. Japan is later in November 2026. Cards become tournament legal 7 days after the release date in your region, and from the pre-release date at your store."}}}},{{"@type":"Question","name":"What is in OP18?","acceptedAnswer":{{"@type":"Answer","text":"OP-18 is BOOSTER PACK -THE DOMINANCE OF GOD-. Bandai lists 127 card types plus 1. The themes are Water Seven and the Holy Knights. Saint Gunko and Saint Shamrock debut, and Franky gets his first Leader card."}}}},{{"@type":"Question","name":"Which OP18 leaders are revealed?","acceptedAnswer":{{"@type":"Answer","text":"Six leaders are revealed: Karoo (OP18-001, red/blue), Franky (OP18-021, green/purple), Monkey D. Luffy (OP18-022, green), Ms. All Sunday (OP18-041, blue), Saint Gunko (OP18-060, purple/black), and Spandam (OP18-079, black/yellow)."}}}},{{"@type":"Question","name":"Is the full OP18 card list out?","acceptedAnswer":{{"@type":"Answer","text":"No. This page lists the cards revealed by 7 October 2026. The full 127+1 list is not public yet, and English wording can still change before Bandai posts the official card list."}}}}]}}</script>
</head>
<body>
  <div class="wrap wrap-spoilers">
    <header>
      <a class="brand" href="/">
        <img class="logo" src="/img/opdl-avatar.png" width="56" height="56" alt="One Piece Decklists" />
        <div>
          <h1>One Piece Decklists</h1>
          <div class="subtitle">OPTCG decklists</div>
        </div>
      </a>
      <div class="theme-toggle" role="group" aria-label="Color theme">
        <button type="button" class="theme-toggle-btn" data-theme-set="light" aria-pressed="true">Light</button>
        <button type="button" class="theme-toggle-btn" data-theme-set="dark" aria-pressed="false">Dark</button>
      </div>
      <nav aria-label="Primary">
        <a href="/tier-list.html">Tier List</a>
        <a href="/#recent">Recent lists</a>
        <a href="/decklists/op17.html">Leaders</a>
        <a href="/format.html">Format</a>
        <a href="/op18-spoilers.html" aria-current="page">OP18</a>
        <a href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">Events</a>
        <a href="/guides/">Guides</a>
        <a href="/shop/">Shop</a>
        <a href="/search.html">Search</a>
        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>
      </nav>
    </header>
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / OP18 spoilers</div>
        <h2>OP18 spoilers</h2>
        <p>BOOSTER PACK -THE DOMINANCE OF GOD- [OP-18] is the Water Seven and Holy Knights set. English release is 20 November 2026. These are the cards revealed by 7 October 2026, not the full 127+1 list. Wording follows the sample prints and can still change. Pictures are sample previews.</p>
        <div class="spoiler-facts">
          <div><strong>20 Nov 2026</strong><span>English release</span></div>
          <div><strong>$4.99</strong><span>Pack MSRP</span></div>
          <div><strong>127+1</strong><span>Card types</span></div>
          <div><strong>{count}</strong><span>Revealed here</span></div>
        </div>
        <p class="muted">Official product page: <a href="https://en.onepiece-cardgame.com/products/op18.html">The Dominance of God [OP-18]</a>. Saint Gunko and Saint Shamrock debut. Franky gets his first Leader. Yoshitaka Amano drew parallels of Saint Shamrock and of Loki, who returns as an OP17-119 reprint.</p>

        <section style="margin-top:22px" id="leaders">
          <div class="section-title">
            <h3>Revealed leaders</h3>
            <div class="muted">6 so far</div>
          </div>
          <div class="spoiler-leaders">
          {leaders}
          </div>
        </section>

        <section style="margin-top:22px" id="chase">
          <div class="section-title">
            <h3>Chase treatments</h3>
            <div class="muted">Parallels called out with the reveals</div>
          </div>
          <ul class="text-leader-list">
            <li><a href="#OP18-119">Saint Shamrock</a><span class="muted">OP18-119 SEC · Amano parallel and foil</span></li>
            <li><span style="font-weight:800">Loki</span><span class="muted">OP17-119 reprint · Amano parallel and foil</span></li>
            <li><a href="#OP18-031">Nico Robin</a><span class="muted">OP18-031 SR · comic Super Parallel</span></li>
            <li><a href="#OP18-065">Saint Gunko</a><span class="muted">OP18-065 SR · God's Knights Super Parallel</span></li>
          </ul>
          <p class="muted">Loki stays the black OP17-119 Secret Rare already in the game: 6 cost, 8000 power, +12 cost, +3000 power on the opponent's turn, and on play it K.O.s opposing Characters with a total cost of 4 or less. The new part is the Amano artwork in this pack.</p>
        </section>

        <section style="margin-top:22px" id="cards">
          <div class="section-title">
            <h3>Revealed cards</h3>
            <div class="muted" id="spoiler-count">{count} cards</div>
          </div>
          <div class="spoiler-filters">
            <label class="site-search-label" for="spoiler-q">Filter the revealed list</label>
            <input class="spoiler-search" id="spoiler-q" type="search" placeholder="Name, number, color, or type" autocomplete="off" />
            <div class="spoiler-chips" role="group" aria-label="Color">
              <button type="button" class="spoiler-chip" data-spoiler-color="" aria-pressed="true">All colors</button>
              <button type="button" class="spoiler-chip" data-spoiler-color="red" aria-pressed="false">Red</button>
              <button type="button" class="spoiler-chip" data-spoiler-color="green" aria-pressed="false">Green</button>
              <button type="button" class="spoiler-chip" data-spoiler-color="blue" aria-pressed="false">Blue</button>
              <button type="button" class="spoiler-chip" data-spoiler-color="purple" aria-pressed="false">Purple</button>
              <button type="button" class="spoiler-chip" data-spoiler-color="black" aria-pressed="false">Black</button>
              <button type="button" class="spoiler-chip" data-spoiler-color="yellow" aria-pressed="false">Yellow</button>
            </div>
            <div class="spoiler-chips" role="group" aria-label="Card type">
              <button type="button" class="spoiler-chip" data-spoiler-kind="" aria-pressed="true">All types</button>
              <button type="button" class="spoiler-chip" data-spoiler-kind="leader" aria-pressed="false">Leaders</button>
              <button type="button" class="spoiler-chip" data-spoiler-kind="character" aria-pressed="false">Characters</button>
              <button type="button" class="spoiler-chip" data-spoiler-kind="stage" aria-pressed="false">Stages</button>
            </div>
          </div>
          <p class="spoiler-empty muted" id="spoiler-empty" hidden>No revealed card matches that filter.</p>
          <div class="spoiler-grid">
          {articles}
          </div>
        </section>

        <section class="faq" id="faq">
          <div class="section-title">
            <h3>OP18 FAQ</h3>
            <div class="muted">Release facts</div>
          </div>
          <details>
            <summary>When does OP18 release?</summary>
            <p>English OP-18 The Dominance of God releases 20 November 2026 at $4.99 a pack. Japan is later in November 2026. Cards become tournament legal 7 days after the release date in your region, and from the pre-release date at your store.</p>
          </details>
          <details>
            <summary>What is in OP18?</summary>
            <p>OP-18 is BOOSTER PACK -THE DOMINANCE OF GOD-. Bandai lists 127 card types plus 1. The themes are Water Seven and the Holy Knights. Saint Gunko and Saint Shamrock debut, and Franky gets his first Leader card.</p>
          </details>
          <details>
            <summary>Which OP18 leaders are revealed?</summary>
            <p>Six leaders are revealed: Karoo (OP18-001, red/blue), Franky (OP18-021, green/purple), Monkey D. Luffy (OP18-022, green), Ms. All Sunday (OP18-041, blue), Saint Gunko (OP18-060, purple/black), and Spandam (OP18-079, black/yellow).</p>
          </details>
          <details>
            <summary>Is the full OP18 card list out?</summary>
            <p>No. This page lists the cards revealed by 7 October 2026. The full 127+1 list is not public yet, and English wording can still change before Bandai posts the official card list.</p>
          </details>
        </section>

        <section class="related-links" style="margin-top:22px">
          <div class="section-title">
            <h3>Related pages</h3>
            <div class="muted">Current format</div>
          </div>
          <ul class="list">
            <li>
              <a class="item" href="/decklists/op17.html">
                <div>
                  <div style="font-weight:700">OP17 leaders</div>
                  <div class="muted" style="font-size:13px">Current constructed hubs</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
            <li>
              <a class="item" href="/tier-list.html">
                <div>
                  <div style="font-weight:700">OP17 tier list</div>
                  <div class="muted" style="font-size:13px">What is winning before OP18</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
            <li>
              <a class="item" href="/format.html">
                <div>
                  <div style="font-weight:700">Format and banlist</div>
                  <div class="muted" style="font-size:13px">Standard legality</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
          </ul>
        </section>
      </div>
    </main>
    <footer>
      © <span id="year"></span> One Piece Decklists - Fan site, not affiliated with Bandai.
      <a href="/tier-list.html">Tier List</a> · <a href="/guides/">Guides</a> · <a href="/decklists/op17.html">Leaders</a> · <a href="/op18-spoilers.html">OP18</a> · <a href="/format.html">Format</a> · <a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a>
    </footer>
  </div>
  <dialog class="spoiler-dialog" id="spoiler-dialog" aria-label="Card image">
    <form method="dialog">
      <button type="submit" class="spoiler-dialog-close" data-spoiler-close>Close</button>
      <img id="spoiler-dialog-img" alt="" />
      <p id="spoiler-dialog-cap"></p>
    </form>
  </dialog>
  <script>
    document.getElementById("year").textContent = new Date().getFullYear();
  </script>
  <script src="/js/site.js?v=home-smooth"></script>
  <script>
    (function () {{
      var cards = Array.prototype.slice.call(document.querySelectorAll("[data-spoiler-card]"));
      var q = document.getElementById("spoiler-q");
      var count = document.getElementById("spoiler-count");
      var empty = document.getElementById("spoiler-empty");
      var color = "";
      var kind = "";
      function apply() {{
        var needle = (q.value || "").trim().toLowerCase();
        var n = 0;
        cards.forEach(function (card) {{
          var ok = true;
          var colors = " " + (card.getAttribute("data-colors") || "") + " ";
          if (color && colors.indexOf(" " + color + " ") < 0) ok = false;
          if (kind && card.getAttribute("data-kind") !== kind) ok = false;
          if (needle && (card.getAttribute("data-q") || "").indexOf(needle) < 0) ok = false;
          card.hidden = !ok;
          if (ok) n += 1;
        }});
        count.textContent = n + (n === 1 ? " card" : " cards");
        empty.hidden = n !== 0;
      }}
      function bind(attr, set) {{
        document.querySelectorAll("[" + attr + "]").forEach(function (btn) {{
          btn.addEventListener("click", function () {{
            set(btn.getAttribute(attr) || "");
            document.querySelectorAll("[" + attr + "]").forEach(function (other) {{
              other.setAttribute("aria-pressed", other === btn ? "true" : "false");
            }});
            apply();
          }});
        }});
      }}
      bind("data-spoiler-color", function (value) {{ color = value; }});
      bind("data-spoiler-kind", function (value) {{ kind = value; }});
      q.addEventListener("input", apply);

      var dialog = document.getElementById("spoiler-dialog");
      var shot = document.getElementById("spoiler-dialog-img");
      var cap = document.getElementById("spoiler-dialog-cap");
      document.querySelectorAll("[data-spoiler-open]").forEach(function (btn) {{
        btn.addEventListener("click", function () {{
          var img = btn.querySelector("img");
          if (!img || !dialog.showModal) return;
          shot.src = img.getAttribute("src");
          shot.alt = img.alt;
          cap.textContent = img.alt;
          dialog.showModal();
        }});
      }});
      dialog.addEventListener("click", function (event) {{
        if (event.target === dialog) dialog.close();
      }});
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    html = render()
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(CARDS)} cards, {len(html)} bytes)")


if __name__ == "__main__":
    main()
