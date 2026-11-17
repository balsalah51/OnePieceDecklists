#!/usr/bin/env python3
"""Write the static OP18 spoilers page from the revealed-card list."""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "op18-spoilers.html"


def _primary_nav(current: str) -> str:
    import importlib.util

    spec = importlib.util.spec_from_file_location("seocommon", ROOT / "scripts" / "seo_common.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.primary_nav_html(current=current)
IMG = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP18/{id}_EN.webp"
CARDS_PATH = ROOT / "data/op18-cards.json"


def load_cards() -> list[dict]:
    import json
    rows = json.loads(CARDS_PATH.read_text())
    cards = []
    for row in rows:
        cards.append(
            {
                "id": row["id"],
                "name": row.get("name") or row["id"],
                "aliases": row.get("aliases") or "",
                "kind": (row.get("kind") or "character").lower(),
                "rarity": row.get("rarity") or "",
                "colors": row.get("colors") or [],
                "cost": row.get("cost") or "",
                "power": row.get("power") or "",
                "life": row.get("life") or "",
                "counter": row.get("counter") or "",
                "attribute": row.get("attribute") or "",
                "types": row.get("types") or [],
                "effect": row.get("effect") or "No effect.",
                "note": row.get("note") or "",
                "image": bool(row.get("image", True)),
            }
        )
    return cards


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
    cards = load_cards()
    count = len(cards)
    leader_n = sum(1 for c in cards if c["kind"] == "leader")
    leaders = "\n          ".join(leader_tile(c) for c in cards if c["kind"] == "leader")
    articles = "\n          ".join(card_article(c) for c in cards)
    desc = (
        "OP18 card list for ONE PIECE CARD GAME booster The Dominance of God. "
        f"{count} numbered cards, including Franky, Saint Gunko, and Saint Shamrock. "
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
  <link rel="stylesheet" href="/css/site.css?v=op18-1" />
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
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"When does OP18 release?","acceptedAnswer":{{"@type":"Answer","text":"English OP-18 The Dominance of God releases 20 November 2026 at $4.99 a pack. Japan is later in November 2026. Cards become tournament legal 7 days after the release date in your region, and from the pre-release date at your store."}}}},{{"@type":"Question","name":"What is in OP18?","acceptedAnswer":{{"@type":"Answer","text":"OP-18 is BOOSTER PACK -THE DOMINANCE OF GOD-. Bandai lists 127 card types plus 1. The themes are Water Seven and the Holy Knights. Saint Gunko and Saint Shamrock debut, and Franky gets his first Leader card."}}}},{{"@type":"Question","name":"Which OP18 leaders are revealed?","acceptedAnswer":{{"@type":"Answer","text":"Six leaders are revealed: Karoo (OP18-001, red/blue), Franky (OP18-021, green/purple), Monkey D. Luffy (OP18-022, green), Ms. All Sunday (OP18-041, blue), Saint Gunko (OP18-060, purple/black), and Spandam (OP18-079, black/yellow)."}}}},{{"@type":"Question","name":"Is the full OP18 card list out?","acceptedAnswer":{{"@type":"Answer","text":"Yes. Bandai posted the numbered OP18-001 to OP18-119 list. This page uses that public list. Parallels and extras sit outside those 119 numbers. Sleeptids OP18-093 may be any number in a deck."}}}}]}}</script>
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
{_primary_nav("op18")}
    </header>
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / OP18 spoilers</div>
        <h2>OP18 spoilers</h2>
        <p>BOOSTER PACK -THE DOMINANCE OF GOD- [OP-18] is the Water Seven and Holy Knights set. English release is 20 November 2026. Bandai published the numbered card list. This page shows those {count} cards with English names, stats, and effects. Pictures are official/sample art from Limitless.</p>
        <div class="spoiler-facts">
          <div><strong>20 Nov 2026</strong><span>English release</span></div>
          <div><strong>$4.99</strong><span>Pack MSRP</span></div>
          <div><strong>127+1</strong><span>Card types</span></div>
          <div><strong>{count}</strong><span>Numbered cards</span></div>
        </div>
        <p class="muted">Official product page: <a href="https://en.onepiece-cardgame.com/products/op18.html">The Dominance of God [OP-18]</a>. Saint Gunko and Saint Shamrock debut. Franky gets his first Leader. Yoshitaka Amano drew parallels of Saint Shamrock and of Loki, who returns as an OP17-119 reprint.</p>

        <section style="margin-top:22px" id="leaders">
          <div class="section-title">
            <h3>Leaders</h3>
            <div class="muted">{leader_n} leaders</div>
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
            <h3>Card list</h3>
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
              <button type="button" class="spoiler-chip" data-spoiler-kind="event" aria-pressed="false">Events</button>
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
            <p>Yes. Bandai posted the numbered OP18-001 to OP18-119 list. This page uses that public list. The product still lists 127+1 types because parallels and extras are separate. Sleeptids OP18-093 may be any number in a deck.</p>
          </details>
        </section>

        <section class="related-links" style="margin-top:22px">
          <div class="section-title">
            <h3>Related pages</h3>
            <div class="muted">Current format</div>
          </div>
          <ul class="list">
            <li>
              <a class="item" href="/op18-lists.html">
                <div>
                  <div style="font-weight:700">OP18 decklists</div>
                  <div class="muted" style="font-size:13px">Hosted lists that include OP18 cards</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
            <li>
              <a class="item" href="/eb05-spoilers.html">
                <div>
                  <div style="font-weight:700">EB05 spoilers</div>
                  <div class="muted" style="font-size:13px">Heroines Edition vol.2 revealed cards</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
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
      <a href="/tier-list.html">Tier List</a> · <a href="/guides/">Guides</a> · <a href="/decklists/op17.html">Leaders</a> · <a href="/eb05-spoilers.html">EB05</a> · <a href="/op18-lists.html">OP18 lists</a> · <a href="/op18-spoilers.html">OP18</a> · <a href="/format.html">Format</a> · <a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a>
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
  <script src="/js/site.js?v=op18-1"></script>
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
    print(f"wrote {OUT} ({len(load_cards())} cards, {len(html)} bytes)")


if __name__ == "__main__":
    main()
