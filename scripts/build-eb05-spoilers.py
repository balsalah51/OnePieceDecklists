#!/usr/bin/env python3
"""Write the static EB05 spoilers page from data/eb05-spoilers.json."""

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eb05-spoilers.html"
CARDS = json.loads((ROOT / "data" / "eb05-spoilers.json").read_text(encoding="utf-8"))
IMG = "https://cards.oplaytcg.com/EB05/en/{id}.webp"
FEATURED = [
    "EB05-010",
    "EB05-001",
    "EB05-006",
    "EB05-014",
    "EB05-016",
    "EB05-021",
    "EB05-034",
    "EB05-046",
    "EB05-052",
    "EB05-055",
    "EB05-061",
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
    if card.get("block"):
        parts.append(f"block {card['block']}")
    if card.get("attribute"):
        parts.append(card["attribute"])
    if card.get("types"):
        parts.append(" / ".join(card["types"]))
    return " · ".join(parts)


def picture(card: dict, featured: bool = False) -> str:
    label = f"{card['name']} {card['id']}"
    loading = "eager" if featured else "lazy"
    img = (
        f'<img src="{IMG.format(id=card["id"])}" alt="{e(label)}" '
        f'width="300" height="419" loading="{loading}" decoding="async" referrerpolicy="no-referrer" />'
    )
    if featured:
        return img
    return (
        f'<button type="button" class="spoiler-shot" data-spoiler-open '
        f'aria-label="Enlarge {e(label)}">{img}</button>'
    )


def feature_tile(card: dict) -> str:
    return (
        f'<a class="spoiler-leader {color_class(card["colors"])}" href="#{e(card["id"])}">'
        f"{picture(card, featured=True)}"
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
    by_id = {card["id"]: card for card in CARDS}
    count = len(CARDS)
    featured = "\n          ".join(feature_tile(by_id[cid]) for cid in FEATURED)
    articles = "\n          ".join(card_article(card) for card in CARDS)
    desc = (
        "EB05 spoilers for ONE PIECE CARD GAME Extra Booster Heroines Edition vol.2. "
        f"{count} revealed cards, including the new Nico Robin Leader and Secret Rare Nami. "
        "English release 30 October 2026."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>EB05 spoilers | Heroines Edition vol.2 | One Piece Decklists</title>
  <meta name="description" content="{e(desc)}" />
  <script id="opdl-theme-boot">
    (function(){{try{{var m=document.cookie.match(/(?:^|; )opdl-theme=([^;]*)/);var t=m&&decodeURIComponent(m[1]);if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();
  </script>
  <link rel="stylesheet" href="/css/site.css?v=eb05-spoilers2" />
  <link rel="canonical" href="https://onepiecedecklists.com/eb05-spoilers.html" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta name="googlebot" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta name="theme-color" content="#b71c1c" />
  <link rel="icon" href="https://onepiecedecklists.com/img/opdl-logo-192.png" type="image/png" sizes="192x192" />
  <link rel="apple-touch-icon" href="https://onepiecedecklists.com/img/opdl-logo-192.png" sizes="192x192" />
  <link rel="manifest" href="/site.webmanifest" />
  <link rel="search" type="application/opensearchdescription+xml" title="One Piece Decklists" href="/opensearch.xml" />
  <link rel="alternate" hreflang="en" href="https://onepiecedecklists.com/eb05-spoilers.html" />
  <link rel="alternate" hreflang="x-default" href="https://onepiecedecklists.com/eb05-spoilers.html" />
  <meta name="google-adsense-account" content="ca-pub-1074015774205047" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1074015774205047" crossorigin="anonymous"></script>
  <meta property="og:site_name" content="One Piece Decklists" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="EB05 spoilers | Heroines Edition vol.2 | One Piece Decklists" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="https://onepiecedecklists.com/eb05-spoilers.html" />
  <meta property="og:image" content="https://onepiecedecklists.com/img/opdl-hero.jpg" />
  <meta property="og:image:alt" content="EB05 spoilers | Heroines Edition vol.2" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="EB05 spoilers | Heroines Edition vol.2 | One Piece Decklists" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="https://onepiecedecklists.com/img/opdl-hero.jpg" />
  <meta name="twitter:image:alt" content="EB05 spoilers | Heroines Edition vol.2" />
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"https://onepiecedecklists.com/"}},{{"@type":"ListItem","position":2,"name":"EB05 spoilers","item":"https://onepiecedecklists.com/eb05-spoilers.html"}}]}}</script>
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"When does EB05 release?","acceptedAnswer":{{"@type":"Answer","text":"English EXTRA BOOSTER ONE PIECE Heroines Edition vol.2 releases 30 October 2026 at $4.99 a pack. Japan is 31 October 2026. Cards are tournament legal from the pre-release date in your region."}}}},{{"@type":"Question","name":"What is in EB05?","acceptedAnswer":{{"@type":"Answer","text":"EB-05 is an Extra Booster of heroine cards. The English product page lists 75+2 types. The Japanese page lists 7 Leaders, 29 Commons, 21 Rares, 9 Super Rares, 1 Secret Rare, 8 Special cards, and 2 DON!! cards."}}}},{{"@type":"Question","name":"Which EB05 leaders are revealed?","acceptedAnswer":{{"@type":"Answer","text":"Nico Robin is the new Leader, EB05-010, green and yellow, 5000 power and 4 life. Six earlier Leaders return with new art under their original numbers: Nefertari Vivi EB03-001, Shirahoshi OP11-022, Nami OP11-041, Jewelry Bonney OP13-100, Boa Hancock OP14-041, and Rebecca OP15-039."}}}},{{"@type":"Question","name":"Is the full EB05 card list out?","acceptedAnswer":{{"@type":"Answer","text":"No. This page shows 50 of the 61 new EB05 numbers revealed by 7 October 2026. EB05-003, 008, 015, 019, 026, 030, 032, 033, 041, 058, and 059 are still missing, and so are both DON!! cards. English wording can still change."}}}}]}}</script>
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
        <a href="/eb05-spoilers.html" aria-current="page">EB05</a>
        <a href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">Events</a>
        <a href="/guides/">Guides</a>
        <a href="/shop/">Shop</a>
        <a href="/search.html">Search</a>
        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>
      </nav>
    </header>
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / EB05 spoilers</div>
        <h2>EB05 spoilers</h2>
        <p>EXTRA BOOSTER -ONE PIECE HEROINES EDITION vol.2- [EB-05] releases in English on 30 October 2026. These are the new cards revealed by 7 October 2026, not the full 75+2 list. Wording follows the sample prints and can still change. Pictures are sample previews.</p>
        <div class="spoiler-facts">
          <div><strong>30 Oct 2026</strong><span>English release</span></div>
          <div><strong>$4.99</strong><span>Pack MSRP</span></div>
          <div><strong>75+2</strong><span>Card types</span></div>
          <div><strong>{count}</strong><span>New cards shown</span></div>
        </div>
        <p class="muted">Official product page: <a href="https://en.onepiece-cardgame.com/products/eb05.html">Heroines Edition vol.2 [EB-05]</a>. Japan is 31 October 2026. The Japanese page lists 7 Leaders, 29 Commons, 21 Rares, 9 Super Rares, 1 Secret Rare, 8 Special cards, and 2 DON!! cards. That is 61 new EB05 numbers, six returning Leaders, and the Special cards. Eleven numbers are still unrevealed: EB05-003, 008, 015, 019, 026, 030, 032, 033, 041, 058, and 059, plus both DON!! cards.</p>

        <section style="margin-top:22px" id="featured">
          <div class="section-title">
            <h3>Featured samples</h3>
            <div class="muted">New Leader, Super Rares, Secret Rare</div>
          </div>
          <div class="spoiler-leaders">
          {featured}
          </div>
        </section>

        <section style="margin-top:22px" id="leaders">
          <div class="section-title">
            <h3>Returning leaders</h3>
            <div class="muted">New art, original numbers</div>
          </div>
          <p>Six earlier Leaders come back with new EB05 artwork. They keep their original numbers and printed text. Those samples are not in the EB05 image set.</p>
          <ul class="text-leader-list">
            <li><span style="font-weight:800">Nefertari Vivi</span><span class="muted">EB03-001</span></li>
            <li><span style="font-weight:800">Shirahoshi</span><span class="muted">OP11-022</span></li>
            <li><a href="/decklists/nami.html">Nami</a><span class="muted">OP11-041 · decklists</span></li>
            <li><a href="/decklists/yellow-bonney.html">Jewelry Bonney</a><span class="muted">OP13-100 · decklists</span></li>
            <li><a href="/decklists/boa-hancock.html">Boa Hancock</a><span class="muted">OP14-041 · decklists</span></li>
            <li><span style="font-weight:800">Rebecca</span><span class="muted">OP15-039</span></li>
          </ul>
        </section>

        <section style="margin-top:22px" id="specials">
          <div class="section-title">
            <h3>Heroines Special cards</h3>
            <div class="muted">8 treatments</div>
          </div>
          <p>Three Special cards are new EB05 numbers and appear in the list below. Five keep an older number, so there is no EB05 sample for them.</p>
          <ul class="text-leader-list">
            <li><a href="#EB05-006">Miss Buckingham Stussy</a><span class="muted">EB05-006</span></li>
            <li><a href="#EB05-016">Nico Robin</a><span class="muted">EB05-016</span></li>
            <li><a href="#EB05-031">Vinsmoke Reiju</a><span class="muted">EB05-031</span></li>
            <li><span style="font-weight:800">Nami</span><span class="muted">OP01-016</span></li>
            <li><span style="font-weight:800">Perona</span><span class="muted">OP14-033</span></li>
            <li><span style="font-weight:800">Gerd</span><span class="muted">OP17-081</span></li>
            <li><span style="font-weight:800">Charlotte Pudding</span><span class="muted">OP17-109</span></li>
            <li><span style="font-weight:800">Boa Hancock</span><span class="muted">ST17-004</span></li>
          </ul>
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
              <button type="button" class="spoiler-chip" data-spoiler-kind="event" aria-pressed="false">Events</button>
            </div>
          </div>
          <p class="spoiler-empty muted" id="spoiler-empty" hidden>No revealed card matches that filter.</p>
          <div class="spoiler-grid">
          {articles}
          </div>
        </section>

        <section class="faq" id="faq">
          <div class="section-title">
            <h3>EB05 FAQ</h3>
            <div class="muted">Release facts</div>
          </div>
          <details>
            <summary>When does EB05 release?</summary>
            <p>English EXTRA BOOSTER ONE PIECE Heroines Edition vol.2 releases 30 October 2026 at $4.99 a pack. Japan is 31 October 2026. Cards are tournament legal from the pre-release date in your region.</p>
          </details>
          <details>
            <summary>What is in EB05?</summary>
            <p>EB-05 is an Extra Booster of heroine cards. The English product page lists 75+2 types. The Japanese page lists 7 Leaders, 29 Commons, 21 Rares, 9 Super Rares, 1 Secret Rare, 8 Special cards, and 2 DON!! cards.</p>
          </details>
          <details>
            <summary>Which EB05 leaders are revealed?</summary>
            <p>Nico Robin is the new Leader, EB05-010, green and yellow, 5000 power and 4 life. Six earlier Leaders return with new art under their original numbers: Nefertari Vivi EB03-001, Shirahoshi OP11-022, Nami OP11-041, Jewelry Bonney OP13-100, Boa Hancock OP14-041, and Rebecca OP15-039.</p>
          </details>
          <details>
            <summary>Is the full EB05 card list out?</summary>
            <p>No. This page shows 50 of the 61 new EB05 numbers revealed by 7 October 2026. EB05-003, 008, 015, 019, 026, 030, 032, 033, 041, 058, and 059 are still missing, and so are both DON!! cards. English wording can still change.</p>
          </details>
        </section>

        <section class="related-links" style="margin-top:22px">
          <div class="section-title">
            <h3>Related pages</h3>
            <div class="muted">Leaders in this set</div>
          </div>
          <ul class="list">
            <li>
              <a class="item" href="/decklists/nami.html">
                <div>
                  <div style="font-weight:700">Nami</div>
                  <div class="muted" style="font-size:13px">OP11-041 constructed hub</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
            <li>
              <a class="item" href="/decklists/yellow-bonney.html">
                <div>
                  <div style="font-weight:700">Yellow Bonney</div>
                  <div class="muted" style="font-size:13px">OP13-100 constructed hub</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
            <li>
              <a class="item" href="/decklists/boa-hancock.html">
                <div>
                  <div style="font-weight:700">Boa Hancock</div>
                  <div class="muted" style="font-size:13px">OP14-041 constructed hub</div>
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
      <a href="/tier-list.html">Tier List</a> · <a href="/guides/">Guides</a> · <a href="/decklists/op17.html">Leaders</a> · <a href="/eb05-spoilers.html">EB05</a> · <a href="/format.html">Format</a> · <a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a>
    </footer>
  </div>
  <dialog class="spoiler-dialog" id="spoiler-dialog" aria-label="Card image">
    <form method="dialog">
      <button type="submit" class="spoiler-dialog-close" data-spoiler-close>Close</button>
      <img id="spoiler-dialog-img" alt="" referrerpolicy="no-referrer" />
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
