#!/usr/bin/env python3
"""Write shop pages.

Live Amazon sleeves, dice, playmats, deck boxes, and table extras are public
and indexed. Custom leaders stay unpublished (noindex, not linked).
"""

from __future__ import annotations

import html
from pathlib import Path

ROOT = Path("/workspace")
DISCORD = "https://discord.gg/adZ2WUQ3D"
CSS = "/css/site.css?v=theme"
SITE = "https://onepiecedecklists.com"

# Keep amzn.to URLs - they carry the Associates tag (opdl07-20).
SLEEVES = [
    {
        "name": "Dragon Shield Matte Jet",
        "blurb": "100 standard-size sleeves (63×88 mm). Black matte finish. Fits a 50-card OPTCG deck plus extras.",
        "url": "https://amzn.to/4qFzNrw",
        "img": "/img/shop/sleeve-jet.jpg",
    },
    {
        "name": "Dragon Shield Dual Matte Red / Gold",
        "blurb": "100 standard-size Dual Matte sleeves. Red face, gold back (ART15065).",
        "url": "https://amzn.to/46s2YVu",
        "img": "/img/shop/sleeve-red-gold.jpg",
    },
    {
        "name": "Dragon Shield Dual Matte Soul",
        "blurb": "100 standard-size Dual Matte sleeves. Metallic purple Dual Soul (ART15062).",
        "url": "https://amzn.to/4wMuTKw",
        "img": "/img/shop/sleeve-soul.jpg",
    },
    {
        "name": "Dragon Shield Matte Midnight Blue",
        "blurb": "100 standard-size matte sleeves. Midnight Blue finish. Fits a 50-card OPTCG deck plus extras.",
        "url": "https://amzn.to/4hSoJoD",
        "img": "/img/shop/sleeve-midnight.jpg",
    },
    {
        "name": "Dragon Shield Dual Matte Cobalt / Silver",
        "blurb": "100 standard-size Dual Matte sleeves. Cobalt face, silver back.",
        "url": "https://amzn.to/4wNVOFR",
        "img": "/img/shop/sleeve-cobalt-silver.jpg",
    },
    {
        "name": "Dragon Shield Matte Amethyst",
        "blurb": "100 standard-size matte sleeves. Amethyst purple finish.",
        "url": "https://amzn.to/3SSyuZM",
        "img": "/img/shop/sleeve-amethyst.jpg",
    },
    {
        "name": "Hard plastic toploaders (3×4, 200-pack)",
        "blurb": "Rigid 3×4 in. holders for singles, trades, and binder extras. Not for in-game play.",
        "url": "https://amzn.to/4ixZmZn",
        "img": "/img/shop/sleeve-toploaders.jpg",
    },
]

DICE = [
    {
        "name": "Power counter dice (+1000 / −1000)",
        "blurb": "32-piece set of +1000 to +6000 and −1000 to −6000 counters. Built for OPTCG power tracking.",
        "url": "https://amzn.to/46pbKUi",
        "img": "/img/shop/dice-power.jpg",
    },
    {
        "name": "Official One Piece Premium Dice Set",
        "blurb": "Licensed dice in a collectible Monkey D. Luffy tin. Official Eiichiro Oda / Shueisha merchandise.",
        "url": "https://amzn.to/4xEOaiF",
        "img": "/img/shop/dice-luffy.jpg",
    },
    {
        "name": "Yiotfandoll 16 mm D6 (blue / black)",
        "blurb": "10 acrylic 16 mm six-siders. A cheap table set for life, DON!!, or kitchen-table counters.",
        "url": "https://amzn.to/4gQtpdA",
        "img": "/img/shop/dice-acrylic.jpg",
    },
]

PLAYMATS = [
    {
        "name": "Custom TCG playmat with bag",
        "blurb": "Personalized playmat with play-zone options and a non-slip surface. Ships with a mat bag.",
        "url": "https://amzn.to/4hWBnD9",
        "img": "/img/shop/playmat-custom.jpg",
    },
    {
        "name": "One Piece skeleton playmat set",
        "blurb": "14×24 in. One Piece TCG playmat with two skull dice and a storage bag.",
        "url": "https://amzn.to/4ypjUbx",
        "img": "/img/shop/playmat-skeleton.jpg",
    },
]

DECK_BOXES = [
    {
        "name": "Wanted poster deck box",
        "blurb": "Wanted-poster themed box with commander display. Holds about 120 singles or 100 double-sleeved cards.",
        "url": "https://amzn.to/4xuKTlW",
        "img": "/img/shop/deckbox-wanted.jpg",
    },
    {
        "name": "4-pack magnetic deck boxes",
        "blurb": "Four magnetic boxes. Each holds 100+ double-sleeved cards - enough for several OPTCG lists.",
        "url": "https://amzn.to/3SSyyJ0",
        "img": "/img/shop/deckbox-4pack.jpg",
    },
    {
        "name": "MAKHISTORY Commander deck box",
        "blurb": "Magnetic deck case with dice tray, 35pt holder, and two dividers. Fits 100+ double-sleeved cards.",
        "url": "https://amzn.to/4gVNBuw",
        "img": "/img/shop/deckbox-makhistory.jpg",
    },
    {
        "name": "UAONO Commander deck box",
        "blurb": "Magnetic commander box. Fits 100 double-sleeved cards and a toploader.",
        "url": "https://amzn.to/4zVuIzE",
        "img": "/img/shop/deckbox-uaono.jpg",
    },
]

EXTRAS = [
    {
        "name": "Koonie USB desk fan",
        "blurb": "Small quiet USB fan for long events. Strong airflow, adjustable, folds for the bag.",
        "url": "https://amzn.to/4cc2lD5",
        "img": "/img/shop/extra-desk-fan.jpg",
    },
]


def nav_html(current: str) -> str:
    def item(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if key == current else ""
        extra = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        return f'        <a href="{href}"{cur}{extra}>{label}</a>'

    return "\n".join(
        [
            item("/tier-list.html", "Tier List", "tier"),
            item("/#recent", "Recent lists", "recent"),
            item("/decklists/op17.html", "Leaders", "leaders"),
            item("/format.html", "Format", "format"),
            item("https://en.onepiece-cardgame.com/events/", "Events", "events"),
            item("/guides/", "Guides", "guides"),
            item("/shop/", "Shop", "shop"),
            item("/search.html", "Search", "search"),
            item(DISCORD, "Discord", "discord"),
        ]
    )


def product_card(item: dict) -> str:
    name = html.escape(item["name"])
    blurb = html.escape(item["blurb"])
    url = html.escape(item["url"], quote=True)
    img = html.escape(item["img"], quote=True)
    return f"""          <article class="shop-card">
            <a class="shop-photo-link" href="{url}" target="_blank" rel="sponsored noopener noreferrer">
              <img class="shop-photo" src="{img}" alt="{name}" />
            </a>
            <div style="font-weight:800">{name}</div>
            <p class="shop-note">{blurb}</p>
            <a class="shop-buy" href="{url}" target="_blank" rel="sponsored noopener noreferrer">View on Amazon</a>
          </article>"""


def product_grid(items: list[dict]) -> str:
    return '        <div class="shop-grid">\n' + "\n".join(product_card(p) for p in items) + "\n        </div>"


def section(title: str, href: str, note: str, items: list[dict]) -> str:
    return f"""        <div class="section-title" style="margin-top:28px">
          <h3>{html.escape(title)}</h3>
          <a href="{html.escape(href, quote=True)}">All {html.escape(title.lower())} →</a>
        </div>
        <p class="muted">{html.escape(note)}</p>
{product_grid(items)}"""


def chrome(title: str, desc: str, canonical: str, body: str, *, indexable: bool, amazon: bool) -> str:
    robots = "" if indexable else '  <meta name="robots" content="noindex, nofollow" />\n'
    canon = f'  <link rel="canonical" href="{html.escape(canonical, quote=True)}" />\n' if indexable else ""
    amazon_line = (
        "      As an Amazon Associate I earn from qualifying purchases.\n"
        if amazon
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}" />
{robots}{canon}  <script id="opdl-theme-boot">
    (function(){{try{{var m=document.cookie.match(/(?:^|; )opdl-theme=([^;]*)/);var t=m&&decodeURIComponent(m[1]);if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();
  </script>
  <link rel="stylesheet" href="{CSS}" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1074015774205047" crossorigin="anonymous"></script>
</head>
<body>
  <div class="wrap">
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
{nav_html("shop")}
      </nav>
    </header>
    <main class="single">
      <div class="card hero">
{body}
      </div>
    </main>
    <footer>
      © <span id="year"></span> One Piece Decklists - Fan site, not affiliated with Bandai or Shueisha.
{amazon_line}      <a href="/tier-list.html">Tier List</a> · <a href="/guides/">Guides</a> · <a href="/decklists/op17.html">Leaders</a> · <a href="/format.html">Format</a> · <a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a> · <a href="{DISCORD}" target="_blank" rel="noopener">Discord</a>
    </footer>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script src="/js/site.js?v=theme"></script>
</body>
</html>
"""


def write(rel: str, title: str, desc: str, canonical: str, body: str, *, indexable: bool, amazon: bool = False) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(chrome(title, desc, canonical, body, indexable=indexable, amazon=amazon))
    print("wrote", rel, "indexable" if indexable else "unpublished")


index_body = f"""        <div class="crumb"><a href="/">Home</a> / Shop</div>
        <h2>Shop</h2>
        <p>Sleeves, dice, playmats, deck boxes, and a table extra. Open Amazon for live price and stock.</p>
{section("Sleeves", "/shop/sleeves.html", "Standard 63×88 mm Dragon Shield packs plus hard toploaders for singles.", SLEEVES)}
{section("Dice", "/shop/dice.html", "Power counters, the official Luffy tin, and a cheap acrylic D6 set.", DICE)}
{section("Playmats", "/shop/playmats.html", "A custom mat with bag and a One Piece skeleton playmat set.", PLAYMATS)}
{section("Deck boxes", "/shop/deck-boxes.html", "Magnetic boxes for sleeved OPTCG lists, including a wanted-poster case.", DECK_BOXES)}
{section("Table extras", "/shop/extras.html", "Small gear for long events.", EXTRAS)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>"""

sleeves_body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="/shop/">Shop</a> / Sleeves</div>
        <h2>Sleeves</h2>
        <p>Dragon Shield standard-size packs (63×88 mm) and hard toploaders for singles. Open Amazon for live price and stock.</p>
{product_grid(SLEEVES)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>"""

dice_body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="/shop/">Shop</a> / Dice</div>
        <h2>Dice</h2>
        <p>Power counters and table dice. Check your locals if custom dice are allowed in official events. Open Amazon for live price and stock.</p>
{product_grid(DICE)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>"""

playmats_body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="/shop/">Shop</a> / Playmats</div>
        <h2>Playmats</h2>
        <p>Playmats for OPTCG and other TCGs. Open Amazon for live price and stock.</p>
{product_grid(PLAYMATS)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>"""

deck_boxes_body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="/shop/">Shop</a> / Deck boxes</div>
        <h2>Deck boxes</h2>
        <p>Magnetic cases for sleeved OPTCG lists. Open Amazon for live price and stock.</p>
{product_grid(DECK_BOXES)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>"""

extras_body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="/shop/">Shop</a> / Table extras</div>
        <h2>Table extras</h2>
        <p>Small gear for long events. Open Amazon for live price and stock.</p>
{product_grid(EXTRAS)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>"""

custom_body = f"""        <div class="crumb"><a href="/">Home</a> / Shop / Custom leaders</div>
        <h2>Custom leaders</h2>
        <p>This category is not on the public shop. Custom leader prints are paused.</p>
        <p class="muted">The live shop is <a href="/shop/">sleeves, dice, playmats, and deck boxes</a> on Amazon.</p>
        <a class="discord" href="{DISCORD}" style="margin-top:18px">Ask on Discord</a>"""


def ensure_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text()
    added = 0
    for url in (
        f"{SITE}/shop/",
        f"{SITE}/shop/sleeves.html",
        f"{SITE}/shop/dice.html",
        f"{SITE}/shop/playmats.html",
        f"{SITE}/shop/deck-boxes.html",
        f"{SITE}/shop/extras.html",
    ):
        if url not in text:
            text = text.replace("</urlset>", f"  <url><loc>{url}</loc></url>\n</urlset>", 1)
            added += 1
    if added:
        path.write_text(text)
    print("sitemap shop urls", "added" if added else "present")


def main() -> None:
    write(
        "shop/index.html",
        "Shop | Sleeves, dice, playmats, deck boxes | One Piece Decklists",
        "OPTCG sleeves, dice, playmats, and deck boxes via Amazon.",
        f"{SITE}/shop/",
        index_body,
        indexable=True,
        amazon=True,
    )
    write(
        "shop/sleeves.html",
        "Dragon Shield sleeves | One Piece Decklists shop",
        "Standard 63×88 mm Dragon Shield sleeves and toploaders for OPTCG.",
        f"{SITE}/shop/sleeves.html",
        sleeves_body,
        indexable=True,
        amazon=True,
    )
    write(
        "shop/dice.html",
        "OPTCG dice | One Piece Decklists shop",
        "Power counter dice and One Piece dice via Amazon.",
        f"{SITE}/shop/dice.html",
        dice_body,
        indexable=True,
        amazon=True,
    )
    write(
        "shop/playmats.html",
        "OPTCG playmats | One Piece Decklists shop",
        "One Piece TCG playmats via Amazon.",
        f"{SITE}/shop/playmats.html",
        playmats_body,
        indexable=True,
        amazon=True,
    )
    write(
        "shop/deck-boxes.html",
        "OPTCG deck boxes | One Piece Decklists shop",
        "Magnetic deck boxes for sleeved One Piece TCG lists via Amazon.",
        f"{SITE}/shop/deck-boxes.html",
        deck_boxes_body,
        indexable=True,
        amazon=True,
    )
    write(
        "shop/extras.html",
        "Table extras | One Piece Decklists shop",
        "Small table gear for OPTCG events via Amazon.",
        f"{SITE}/shop/extras.html",
        extras_body,
        indexable=True,
        amazon=True,
    )
    write(
        "shop/custom-leaders.html",
        "Custom leaders | One Piece Decklists shop",
        "Custom OPTCG leader prints. Not currently in the public shop.",
        f"{SITE}/shop/custom-leaders.html",
        custom_body,
        indexable=False,
    )
    ensure_sitemap()
    print("shop pages ready")


if __name__ == "__main__":
    main()
