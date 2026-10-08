#!/usr/bin/env python3
"""Write the static EB05 spoilers page from the revealed-card list."""

from html import escape
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eb05-spoilers.html"
CARDS = json.loads((ROOT / "scripts" / "eb05-cards.json").read_text(encoding="utf-8"))
IMG = "https://cards.oplaytcg.com/{set}/en/{id}.webp"
REPRINT_IMG = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/{set}/{id}_EN.webp"

# Returning Leaders keep their original numbers. Pictures are the original
# prints; Bandai has not posted the EB-05 illustrations to this CDN yet.
RETURNING_LEADERS = [
    {
        "id": "OP11-022",
        "name": "Shirahoshi",
        "colors": ["Green", "Yellow"],
        "detail": "Green/Yellow · 4 life · reprint with new EB-05 art",
    },
    {
        "id": "OP11-041",
        "name": "Nami",
        "colors": ["Blue", "Yellow"],
        "detail": "Blue/Yellow · reprint with new EB-05 art",
    },
    {
        "id": "OP13-100",
        "name": "Jewelry Bonney",
        "colors": ["Yellow"],
        "detail": "Yellow · reprint with new EB-05 art",
    },
    {
        "id": "OP14-041",
        "name": "Boa Hancock",
        "colors": ["Blue", "Yellow"],
        "detail": "Blue/Yellow · reprint with new EB-05 art",
    },
    {
        "id": "OP15-039",
        "name": "Rebecca",
        "colors": ["Blue"],
        "detail": "Blue · reprint with new EB-05 art",
    },
    {
        "id": "EB03-001",
        "name": "Nefeltari Vivi",
        "colors": ["Red", "Blue"],
        "detail": "Red/Blue · reprint with new EB-05 art",
    },
]

SP_CARDS = [
    {"id": "OP01-016", "name": "Nami", "detail": "Reprint · Rare · anime Heroines frame"},
    {"id": "EB05-006", "name": "Miss Buckingham Stussy", "detail": "New · Super Rare · magazine-cover SP"},
    {"id": "EB05-016", "name": "Nico Robin", "detail": "New · Super Rare · anime Heroines frame"},
    {"id": "OP14-033", "name": "Perona", "detail": "Reprint · Rare · magazine-cover SP"},
    {"id": "ST17-004", "name": "Boa Hancock", "detail": "Reprint · Super Rare · magazine-cover SP"},
    {"id": "EB05-031", "name": "Vinsmoke Reiju", "detail": "New · Rare · magazine-cover SP"},
    {"id": "OP17-081", "name": "Gerd", "detail": "Reprint · Rare · magazine-cover SP"},
    {"id": "OP17-109", "name": "Charlotte Pudding", "detail": "Reprint · Rare · magazine-cover SP"},
]


def img_src(card_id: str, reprint: bool = False) -> str:
    set_code = card_id.split("-", 1)[0]
    if reprint:
        return REPRINT_IMG.format(set=set_code, id=card_id)
    return IMG.format(set=set_code, id=card_id)


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
        parts.append(card["attribute"])
    if card.get("types"):
        parts.append(" / ".join(card["types"]))
    return " · ".join(parts)


def picture(card: dict, leader: bool = False, reprint: bool = False) -> str:
    cid = card["id"]
    label = f"{card['name']} {cid}"
    if not card.get("image", True):
        return f'<div class="spoiler-missing" role="img" aria-label="{e(label)}">{e(cid)}</div>'
    img = (
        f'<img src="{img_src(cid, reprint=reprint)}" alt="{e(label)}" '
        f'width="300" height="419" loading="lazy" decoding="async" referrerpolicy="no-referrer" />'
    )
    if leader:
        return img
    return (
        f'<button type="button" class="spoiler-shot" data-spoiler-open '
        f'aria-label="Enlarge {e(label)}">{img}</button>'
    )


def leader_tile(card: dict, href: str | None = None, extra: str = "", reprint: bool = False) -> str:
    target = href or f"#{card['id']}"
    caption = extra or f"{e(card['name'])}<br>{e(card['id'])}"
    return (
        f'<a class="spoiler-leader {color_class(card["colors"])}" href="{e(target)}">'
        f"{picture({**card, 'image': True}, leader=True, reprint=reprint)}"
        f"<span>{caption}</span></a>"
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
    new_leaders = [c for c in CARDS if c["kind"] == "leader"]
    leader_tiles = [leader_tile(c) for c in new_leaders]
    for row in RETURNING_LEADERS:
        leader_tiles.append(
            leader_tile(
                row,
                href="#returning",
                extra=f"{e(row['name'])}<br>{e(row['id'])} reprint",
                reprint=True,
            )
        )
    leaders = "\n          ".join(leader_tiles)
    articles = "\n          ".join(card_article(c) for c in CARDS)
    returning_lis = "\n            ".join(
        f'<li><span style="font-weight:800">{e(r["name"])}</span>'
        f'<span class="muted">{e(r["id"])} · {e(r["detail"])}</span></li>'
        for r in RETURNING_LEADERS
    )
    sp_lis = []
    for row in SP_CARDS:
        if row["id"].startswith("EB05-"):
            sp_lis.append(
                f'<li><a href="#{e(row["id"])}">{e(row["name"])}</a>'
                f'<span class="muted">{e(row["id"])} · {e(row["detail"])}</span></li>'
            )
        else:
            sp_lis.append(
                f'<li><span style="font-weight:800">{e(row["name"])}</span>'
                f'<span class="muted">{e(row["id"])} · {e(row["detail"])}</span></li>'
            )
    sp_html = "\n            ".join(sp_lis)
    desc = (
        "EB05 spoilers for ONE PIECE CARD GAME Extra Booster Heroines Edition vol.2. "
        f"{count} revealed cards, including Nico Robin's new Leader and Secret Rare Nami. "
        "English release 30 October 2026."
    )
    faq_when = (
        "English EB-05 Extra Booster ONE PIECE HEROINES EDITION vol.2 releases 30 October 2026 "
        "at $4.99 a pack. Japan is 31 October 2026. Cards become tournament legal 7 days after "
        "the release date in your region, and from the pre-release date at your store."
    )
    faq_what = (
        "EB-05 is EXTRA BOOSTER -ONE PIECE HEROINES EDITION vol.2-. Bandai lists 75 card types "
        "plus 2 DON!! cards: 7 Leaders, 29 Commons, 21 Rares, 9 Super Rares, 1 Secret Rare, "
        "and 8 Special cards. The theme is heroine characters. Nico Robin debuts as a Leader."
    )
    faq_leaders = (
        "Seven Leaders: new Nico Robin (EB05-010, green/yellow), plus reprints with new art of "
        "Shirahoshi (OP11-022), Nami (OP11-041), Jewelry Bonney (OP13-100), Boa Hancock "
        "(OP14-041), Rebecca (OP15-039), and Nefeltari Vivi (EB03-001)."
    )
    faq_full = (
        f"No. This page lists the {count} EB05-numbered cards revealed by 8 October 2026. "
        "Unrevealed numbers are omitted. English wording can still change before Bandai posts "
        "the official card list. A purple 1-cost Nico Robin has been shown without a confirmed number."
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
  <link rel="stylesheet" href="/css/site.css?v=eb05-spoilers1" />
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
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"When does EB05 release?","acceptedAnswer":{{"@type":"Answer","text":"{e(faq_when)}"}}}},{{"@type":"Question","name":"What is in EB05?","acceptedAnswer":{{"@type":"Answer","text":"{e(faq_what)}"}}}},{{"@type":"Question","name":"Which EB05 leaders are in the set?","acceptedAnswer":{{"@type":"Answer","text":"{e(faq_leaders)}"}}}},{{"@type":"Question","name":"Is the full EB05 card list out?","acceptedAnswer":{{"@type":"Answer","text":"{e(faq_full)}"}}}}]}}</script>
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
        <a href="/op18-spoilers.html">OP18</a>
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
        <p>EXTRA BOOSTER -ONE PIECE HEROINES EDITION vol.2- [EB-05] is the second Heroines extra booster. English release is 30 October 2026. These are the {count} EB05-numbered cards revealed by 8 October 2026, not the full 75+2 list. Unrevealed numbers are left off. Wording follows the sample prints and can still change. Pictures are sample previews.</p>
        <div class="spoiler-facts">
          <div><strong>30 Oct 2026</strong><span>English release</span></div>
          <div><strong>$4.99</strong><span>Pack MSRP</span></div>
          <div><strong>75+2</strong><span>Card types</span></div>
          <div><strong>{count}</strong><span>Revealed here</span></div>
        </div>
        <p class="muted">Official product page: <a href="https://en.onepiece-cardgame.com/products/eb05.html">ONE PIECE HEROINES EDITION vol.2 [EB-05]</a>. Nico Robin debuts as a Leader. Six earlier heroine Leaders return with new art. Japan is 31 October 2026.</p>

        <section style="margin-top:22px" id="leaders">
          <div class="section-title">
            <h3>Leaders</h3>
            <div class="muted">1 new · 6 reprints</div>
          </div>
          <div class="spoiler-leaders">
          {leaders}
          </div>
        </section>

        <section style="margin-top:22px" id="returning">
          <div class="section-title">
            <h3>Returning leaders</h3>
            <div class="muted">Original numbers, new EB-05 illustrations</div>
          </div>
          <ul class="text-leader-list">
            {returning_lis}
          </ul>
          <p class="muted">The six reprints keep the card numbers already in Standard. The tiles above use the original prints because the EB-05 illustrations are not on the public card CDN yet. Effects are unchanged from those numbers.</p>
        </section>

        <section style="margin-top:22px" id="chase">
          <div class="section-title">
            <h3>Chase treatments</h3>
            <div class="muted">Specials and parallels called out with the reveals</div>
          </div>
          <ul class="text-leader-list">
            <li><a href="#EB05-061">Nami</a><span class="muted">EB05-061 SEC · parallel reported</span></li>
            <li><a href="#EB05-014">Shirahoshi</a><span class="muted">EB05-014 SR · manga treatment reported</span></li>
            <li><a href="#EB05-010">Nico Robin</a><span class="muted">EB05-010 Leader · manga Super Parallel reported</span></li>
            <li><a href="#EB05-055">Nami</a><span class="muted">EB05-055 SR · several parallels reported</span></li>
          </ul>
          <p class="muted">A purple 1-cost Nico Robin has been shown without a confirmed card number, so it is not in the grid below.</p>
        </section>

        <section style="margin-top:22px" id="sp">
          <div class="section-title">
            <h3>Special cards</h3>
            <div class="muted">All 8 SP treatments from the reveals</div>
          </div>
          <ul class="text-leader-list">
            {sp_html}
          </ul>
          <p class="muted">Five of the eight keep older numbers. The three new SPs are treatments of EB05-006, EB05-016, and EB05-031, already in the revealed list.</p>
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
            <p>{e(faq_when)}</p>
          </details>
          <details>
            <summary>What is in EB05?</summary>
            <p>{e(faq_what)}</p>
          </details>
          <details>
            <summary>Which EB05 leaders are in the set?</summary>
            <p>{e(faq_leaders)}</p>
          </details>
          <details>
            <summary>Is the full EB05 card list out?</summary>
            <p>{e(faq_full)}</p>
          </details>
        </section>

        <section class="related-links" style="margin-top:22px">
          <div class="section-title">
            <h3>Related pages</h3>
            <div class="muted">Current format and the next booster</div>
          </div>
          <ul class="list">
            <li>
              <a class="item" href="/op18-spoilers.html">
                <div>
                  <div style="font-weight:700">OP18 spoilers</div>
                  <div class="muted" style="font-size:13px">The Dominance of God revealed cards</div>
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
                  <div class="muted" style="font-size:13px">What is winning before EB05</div>
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
      <a href="/tier-list.html">Tier List</a> · <a href="/guides/">Guides</a> · <a href="/decklists/op17.html">Leaders</a> · <a href="/eb05-spoilers.html">EB05</a> · <a href="/op18-spoilers.html">OP18</a> · <a href="/format.html">Format</a> · <a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a>
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
