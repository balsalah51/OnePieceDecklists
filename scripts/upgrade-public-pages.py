#!/usr/bin/env python3
"""Upgrade existing HTML with copy buttons, list stats, Format nav, and site.js.

Does not wipe list pages. Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

aspec = importlib.util.spec_from_file_location("analysis", "/workspace/scripts/add-leader-analysis.py")
ana = importlib.util.module_from_spec(aspec)
aspec.loader.exec_module(ana)

ROOT = gen.ROOT
LINE_RE = ana.LINE_RE
CSS_NEW = "/css/site.css?v=theme"
JS_NEW = "/js/site.js?v=theme"
TCG_VER = "tcg-quiet"
TCG_SCRIPTS = (
    f'  <script src="/js/tcgplayer-config.js?v={TCG_VER}"></script>\n'
    f'  <script src="/js/tcgplayer-ids.js?v={TCG_VER}"></script>\n'
    f'  <script src="/js/tcgplayer-names.js?v={TCG_VER}"></script>\n'
    f'  <script src="/js/tcgplayer.js?v={TCG_VER}"></script>\n'
)
TCG_SCRIPT_RE = re.compile(
    r'  <script src="/js/tcgplayer(?:-config|-ids|-names)?\.js(?:\?[^"]*)?"></script>\n'
)
NAV_LEADERS_SHOP = (
    '        <a href="/decklists/op17.html">Leaders</a>\n'
    '        <a href="/format.html">Format</a>\n'
    '        <a href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">Events</a>\n'
    '        <a href="/guides/">Guides</a>\n'
    '        <a href="/shop/">Shop</a>\n'
    '        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>'
)
NAV_LEADERS_SHOP_CURRENT = (
    '        <a href="/decklists/op17.html" aria-current="page">Leaders</a>\n'
    '        <a href="/format.html">Format</a>\n'
    '        <a href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">Events</a>\n'
    '        <a href="/guides/">Guides</a>\n'
    '        <a href="/shop/">Shop</a>\n'
    '        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>'
)
NAV_OLD_PATTERNS = [
    (
        '        <a href="/decklists/op17.html">OP17</a>\n        <a href="/#community">Community</a>',
        NAV_LEADERS_SHOP,
    ),
    (
        '        <a href="/decklists/op17.html">Leaders</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
        NAV_LEADERS_SHOP,
    ),
    (
        '        <a href="/decklists/op17.html">Leaders</a>\n        <a href="/format.html">Format</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
        NAV_LEADERS_SHOP,
    ),
    (
        '        <a href="/decklists/op17.html">Leaders</a>\n        <a href="/format.html">Format</a>\n        <a href="/shop/">Shop</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
        NAV_LEADERS_SHOP,
    ),
    (
        '        <a href="/decklists/op17.html" aria-current="page">OP17</a>\n        <a href="/#community">Community</a>',
        NAV_LEADERS_SHOP_CURRENT,
    ),
    (
        '        <a href="/decklists/op17.html" aria-current="page">Leaders</a>\n        <a href="/#community">Community</a>',
        NAV_LEADERS_SHOP_CURRENT,
    ),
    (
        '        <a href="/decklists/op17.html" aria-current="page">Leaders</a>\n        <a href="/format.html">Format</a>\n        <a href="/shop/">Shop</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
        NAV_LEADERS_SHOP_CURRENT,
    ),
    (
        '        <a href="/format.html">Format</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
        '        <a href="/format.html">Format</a>\n        <a href="/guides/">Guides</a>\n        <a href="/shop/">Shop</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
    ),
    (
        '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
        '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="/guides/">Guides</a>\n        <a href="/shop/">Shop</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
    ),
    (
        '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="/shop/">Shop</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
        '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="/guides/">Guides</a>\n        <a href="/shop/">Shop</a>\n        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>',
    ),
]


def patch_nav_and_assets(text: str) -> str:
    text = re.sub(r'href="/css/site\.css(?:\?[^"]*)?"', f'href="{CSS_NEW}"', text)
    for old, new in NAV_OLD_PATTERNS:
        text = text.replace(old, new)
    text = re.sub(r'src="/js/site\.js(?:\?[^"]*)?"', f'src="{JS_NEW}"', text)
    text = text.replace(">Copy for sim<", ">Copy to OP TCG SIM<")
    text = text.replace("for OPTCGSim.", "for OP TCG SIM.")
    if "/js/site.js" not in text:
        text = text.replace("</body>", f'  <script src="{JS_NEW}"></script>\n</body>')
    text = text.replace("pop.offsetWidth || 110", "pop.offsetWidth || 220")
    text = text.replace("pop.offsetHeight || 154", "pop.offsetHeight || 308")
    text = ensure_tcgplayer_scripts(text)
    return text


def strip_tcgplayer_scripts(text: str) -> str:
    return TCG_SCRIPT_RE.sub("", text)


def ensure_tcgplayer_scripts(text: str) -> str:
    text = strip_tcgplayer_scripts(text)
    if not any(
        mark in text
        for mark in (
            'class="text-deck"',
            'class="list-row"',
            'class="card-entry"',
            'id="mass-text"',
        )
    ):
        return text
    return text.replace("</body>", TCG_SCRIPTS + "</body>")


def grouped_from_counts(leader: dict, counts: dict[str, int], cache: dict) -> tuple[list[dict], dict]:
    items = [
        {
            "count": 1,
            "id": leader["id"],
            "name": cache.get(leader["id"], {}).get("name") or leader["name"],
            "group": "Leader",
        }
    ]
    for cid, n in counts.items():
        meta = cache.get(cid) or {}
        cat = (meta.get("category") or "character").lower()
        if cat == "event":
            group = "Events"
        elif cat == "stage":
            group = "Stages"
        else:
            group = "Characters"
        items.append({"count": n, "id": cid, "name": meta.get("name") or cid, "group": group})
    return items, cache


def upgrade_list_page(path: Path, leader: dict, cache: dict) -> None:
    text = path.read_text()
    counts = ana.parse_deck(path, leader["id"])
    if counts and "<!-- DECK_STATS -->" not in text:
        items, _ = grouped_from_counts(leader, counts, cache)
        stats = gen.render_deck_stats(items, cache)
        if stats:
            marker = '        <section class="text-deck">'
            if marker in text:
                text = text.replace(marker, stats + "\n" + marker, 1)
            else:
                text = text.replace("</h2>", "</h2>\n" + stats, 1)
    text = patch_nav_and_assets(text)
    path.write_text(text)


def meta_rows() -> list[tuple[dict, int]]:
    rows = []
    for leader in gen.LEADERS:
        d = ROOT / leader["dir"]
        n = len(list(d.glob("*.html"))) if d.exists() else 0
        rows.append((leader, n))
    rows.sort(key=lambda r: (-r[1], r[0]["name"]))
    return rows


def render_meta_strip(rows: list[tuple[dict, int]]) -> str:
    current = [(L, n) for L, n in rows if not L.get("nav_op17")]
    total = sum(n for _, n in current) or 1
    top = current[:8]
    lis = []
    for leader, n in top:
        share = 100.0 * n / total
        lis.append(
            f'            <li><a href="/{leader["page"]}">{leader["name"]}</a>'
            f'<span class="share">{n} lists · {share:.0f}%</span></li>'
        )
    return f"""        <section class="meta-strip" id="meta">
          <div class="section-title">
            <h3>Lists on this site</h3>
            <a href="/format.html">Format →</a>
          </div>
          <p class="muted format-note">Counts are 50-card pages hosted here, not Limitless points. English events are still OP16; OP17 English is 28 August 2026.</p>
          <ol>
{chr(10).join(lis)}
          </ol>
        </section>
"""


def color_label(leader: dict) -> str:
    raw = (leader.get("color") or "").replace("color-", "")
    return "/".join(part.capitalize() for part in raw.split("-") if part)


def leader_list_html(rows: list[tuple[dict, int]]) -> str:
    by_id = {L["id"]: n for L, n in rows}
    items = []
    for leader in gen.LEADERS:
        bits = []
        if leader.get("nav_op17"):
            bits.append("OP17")
        bits.append(color_label(leader))
        bits.append(leader["id"])
        n = by_id.get(leader["id"], 0)
        if n:
            bits.append(f"{n} lists")
        elif leader.get("nav_op17"):
            bits.append("preview")
        items.append(
            f"""            <li>
              <a href="/{leader["page"]}">{leader["name"]}</a>
              <span class="muted">{" · ".join(bits)}</span>
            </li>"""
        )
    return "\n".join(items)


RECENT_LIMIT = 100


def collect_home_lists() -> list[dict]:
    index_path = ROOT / "data/tournament-decks.json"
    comm_path = ROOT / "data/community-decks.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    community = json.loads(comm_path.read_text()) if comm_path.exists() else {}
    rows = []
    seen = set()
    for leader in gen.LEADERS:
        for item in index.get(leader["id"]) or []:
            href = item.get("href") or ""
            if item.get("kind") == "sample" or not href:
                continue
            if not (ROOT / href.lstrip("/")).exists():
                continue
            if href in seen:
                continue
            seen.add(href)
            row = dict(item)
            row["leader"] = leader
            row["tournament_name"] = row.get("tournament_name") or row.get("tournament") or ""
            rows.append(row)
        for item in community.get(leader["id"]) or []:
            href = item.get("href") or ""
            if not href or href in seen:
                continue
            if not (ROOT / href.lstrip("/")).exists():
                continue
            seen.add(href)
            rows.append(
                {
                    "slug": item.get("slug"),
                    "href": href,
                    "player": item.get("player") or "Community",
                    "tournament_name": item.get("subtitle") or item.get("title") or "",
                    "placing": None,
                    "date": item.get("date") or "",
                    "kind": item.get("kind") or "web",
                    "title_override": item.get("title"),
                    "subtitle": item.get("subtitle")
                    or {"youtube": "YouTube list", "x": "X list", "web": "Community list"}.get(
                        item.get("kind"), "Community list"
                    ),
                    "leader": leader,
                }
            )
    return rows


def source_bucket(row: dict) -> str:
    key = f"{row.get('href') or ''} {row.get('slug') or ''}"
    if "optcggg-" in key:
        return "optcggg"
    if "opdeck-" in key:
        return "opdeck"
    if "tcgportal-" in key:
        return "tcgportal"
    if (row.get("kind") or "") in {"web", "youtube", "x", "reddit"}:
        return "community"
    return "tournament"


def is_community_list(row: dict) -> bool:
    return source_bucket(row) != "tournament"


def pick_recent_lists(rows: list[dict], limit: int = RECENT_LIMIT) -> list[dict]:
    """Round-robin public sources so Limitless does not own the homepage."""
    buckets: dict[str, list[dict]] = {
        "opdeck": [],
        "tournament": [],
        "optcggg": [],
        "tcgportal": [],
        "community": [],
    }
    for row in sorted(rows, key=gen.date_sort_key, reverse=True):
        buckets[source_bucket(row)].append(row)
    order = [name for name in ("opdeck", "tournament", "optcggg", "tcgportal", "community") if buckets[name]]
    index = {name: 0 for name in order}
    picked: list[dict] = []
    seen: set[str] = set()
    while len(picked) < limit:
        progressed = False
        for name in order:
            i = index[name]
            bucket = buckets[name]
            while i < len(bucket):
                row = bucket[i]
                i += 1
                href = row.get("href") or ""
                if not href or href in seen:
                    continue
                seen.add(href)
                picked.append(row)
                progressed = True
                break
            index[name] = i
            if len(picked) >= limit:
                break
        if not progressed:
            break
    return picked[:limit]


def recent_rows_html(rows: list[dict]) -> str:
    items = []
    for entry in rows:
        leader = entry["leader"]
        title, subtitle = gen.list_heading(entry, leader["name"])
        when = entry.get("date") or gen.ordinal(entry.get("placing")) or "List"
        img = gen.card_image_url(leader["id"])
        items.append(
            f"""            <li>
              <a class="recent-item {html.escape(leader['color'])}" href="{html.escape(entry['href'])}">
                <img class="recent-leader" src="{html.escape(img)}" alt="{html.escape(leader['name'])}" />
                <div class="recent-copy">
                  <div class="who">{html.escape(title)}</div>
                  <div class="muted meta">{html.escape(subtitle)}</div>
                </div>
                <div class="when">{html.escape(str(when))}</div>
              </a>
            </li>"""
        )
    return "\n".join(items)


def render_home_body() -> str:
    cards = leader_cards_html()
    recent = pick_recent_lists(collect_home_lists())
    nico = gen.card_image_url("OP09-062")
    return f"""        <!-- HOME_BODY -->
        <section class="home-splash" aria-label="One Piece Decklists">
          <img class="home-splash-bg" src="/img/opdl-hero.jpg" alt="One Piece Decklists, an OPTCG decklist site" />
          <a class="home-splash-luffy" href="/decklists/nico-robin.html">
            <img src="{nico}" alt="Nico Robin" />
          </a>
          <div class="home-splash-bar">
            <h2>One Piece Decklists</h2>
            <p>OPTCG decklists. Jump a section, or keep scrolling into the leaders.</p>
          </div>
        </section>

        <a class="events-banner" id="events" href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">
          <div>
            <div class="kicker">Official Bandai site</div>
            <div class="title">ONE PIECE CARD GAME events</div>
            <div class="muted" style="color:rgba(255,255,255,0.82);margin-top:4px">Championships, regionals, Treasure Cups, and store tournaments</div>
          </div>
          <div class="go">Official events →</div>
        </a>

        <nav class="home-big3" aria-label="Main sections">
          <a class="home-big home-big-tier" href="/tier-list.html">
            <span class="home-big-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2.1 13.85 5.2h-3.7L12 2.1Z"/>
                <rect x="10.15" y="5.35" width="3.7" height="1.85" rx="0.4"/>
                <path d="M9 20.6V8.9h6v11.7H9Z"/>
                <path d="M3.6 20.6v-6.4H9v6.4H3.6Z" opacity=".88"/>
                <path d="M15 20.6v-4.7h5.4v4.7H15Z" opacity=".72"/>
              </svg>
            </span>
            <span class="home-big-title">Tier List</span>
            <span class="home-big-note">OP17 S through D with leader pictures</span>
          </a>
          <a class="home-big home-big-recent" href="#recent">
            <span class="home-big-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                <path d="M8 7h11M8 12h11M8 17h11M4 7h.01M4 12h.01M4 17h.01"/>
              </svg>
            </span>
            <span class="home-big-title">Recent Lists</span>
            <span class="home-big-note">Newest 50-card results from every leader</span>
          </a>
          <a class="home-big home-big-leaders" href="#leaders">
            <span class="home-big-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="5" width="12" height="16" rx="2"/>
                <rect x="9" y="3" width="12" height="16" rx="2"/>
              </svg>
            </span>
            <span class="home-big-title">Leaders</span>
            <span class="home-big-note">Every leader picture on this site</span>
          </a>
          <a class="home-big home-big-shop" href="/shop/">
            <span class="home-big-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8h12l-1 12H7L6 8Z"/>
                <path d="M9 8V7a3 3 0 0 1 6 0v1"/>
              </svg>
            </span>
            <span class="home-big-title">Shop</span>
            <span class="home-big-note">Sleeves, dice, playmats, and deck boxes</span>
          </a>
          <a class="home-big home-big-discord" href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">
            <span class="home-big-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.3 5.2A17.4 17.4 0 0 0 14.9 4l-.2.4a15.2 15.2 0 0 1 3.6 1.1c-3.3-1.5-6.6-1.5-9.8 0 .4-.2.9-.4 1.3-.6l-.2-.4A17.3 17.3 0 0 0 4.7 5.2C1.9 9.4 1.1 13.5 1.5 17.5a17.7 17.7 0 0 0 5.4 2.7l.7-1.1a11.5 11.5 0 0 1-2.1-1l.2-.1c1.6.7 3.3 1.2 5.1 1.2s3.5-.4 5.1-1.2l.2.1a11.5 11.5 0 0 1-2.1 1l.7 1.1a17.7 17.7 0 0 0 5.4-2.7c.5-4.6-.7-8.7-3.8-12.3ZM8.8 14.8c-1 0-1.9-.9-1.9-2s.8-2 1.9-2 1.9.9 1.9 2-.8 2-1.9 2Zm6.4 0c-1 0-1.9-.9-1.9-2s.8-2 1.9-2 1.9.9 1.9 2-.8 2-1.9 2Z"/>
              </svg>
            </span>
            <span class="home-big-title">Discord</span>
            <span class="home-big-note">Talk lists, flair, and the crew</span>
          </a>
        </nav>

        <section class="home-leaders-flow" id="leaders">
          <div class="home-leaders-intro">
            <p class="home-leaders-kicker">The crew</p>
            <div class="home-leaders-intro-row">
              <div>
                <h3>Leaders</h3>
                <p>Pick a picture. Each page has lists for that leader. Character names live in the <a href="/guides/">guides</a>.</p>
              </div>
              <a href="/decklists/op17.html">All leader pages →</a>
            </div>
          </div>
          <div class="card home-panel home-leaders-grid">
            <div class="leader-cards home-cards" aria-label="All leader card pictures">
{cards}
            </div>
          </div>
        </section>

        <section class="card home-panel" id="recent">
          <div class="section-title">
            <h3>Recent lists</h3>
            <div class="muted">{len(recent)} lists</div>
          </div>
          <p class="muted">Newest first. OPTCG.GG, OPDeckGuide, TCG PORTAL, and other public lists mixed with tournament results.</p>
          <ul class="recent-list" aria-label="Recent decklists">
{recent_rows_html(recent)}
          </ul>
        </section>
        <!-- /HOME_BODY -->"""


def leader_cards_html() -> str:
    cards = []
    for leader in gen.LEADERS:
        img = gen.card_image_url(leader["id"])
        cards.append(
            f"""            <a class="leader-card-link" href="/{leader["page"]}">
              <img src="{img}" alt="{leader["name"]} leader card" />
              <div class="caption">{leader["name"]}</div>
            </a>"""
        )
    return "\n".join(cards)


def patch_home() -> None:
    path = ROOT / "index.html"
    text = path.read_text()
    body = render_home_body()
    text = text.replace(
        '    <main class="single">\n      <div class="card hero" role="main">\n',
        '    <main class="single home" role="main">\n',
    )
    text = text.replace(
        '        <!-- /HOME_BODY -->\n      </div>\n    </main>',
        '        <!-- /HOME_BODY -->\n    </main>',
    )
    if "<!-- HOME_BODY -->" in text:
        text = re.sub(
            r"        <!-- HOME_BODY -->.*?        <!-- /HOME_BODY -->",
            body,
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = re.sub(
            r"        <h2>One Piece Decklists</h2>.*?(?=\n      </div>\n    </main>)",
            body,
            text,
            count=1,
            flags=re.S,
        )
    text = text.replace('href="/#decklists"', 'href="/#recent"')
    text = text.replace(
        '        <a href="/#recent" aria-current="page">Recent lists</a>\n        <a href="/decklists/op17.html">Leaders</a>',
        '        <a href="#recent">Recent lists</a>\n        <a href="#leaders">Leaders</a>',
    )
    text = text.replace(
        '        <a href="/#recent">Recent lists</a>\n        <a href="/decklists/op17.html">Leaders</a>',
        '        <a href="#recent">Recent lists</a>\n        <a href="#leaders">Leaders</a>',
    )
    text = patch_nav_and_assets(text)
    path.write_text(text)
    print("home leaders", len(gen.LEADERS), "recent", RECENT_LIMIT)


def patch_op17() -> None:
    path = ROOT / "decklists/op17.html"
    text = path.read_text()
    rows = meta_rows()
    n = len(gen.LEADERS)
    text = patch_nav_and_assets(text)
    text = re.sub(r'<div class="muted">\d+ leaders</div>', f'<div class="muted">{n} leaders</div>', text, count=1)
    ol = '          <ol class="text-leader-list" aria-label="All leader pages">\n' + leader_list_html(rows) + "\n          </ol>"
    text = re.sub(
        r'          <ol class="text-leader-list" aria-label="All leader pages">.*?</ol>',
        ol,
        text,
        count=1,
        flags=re.S,
    )
    grid = '          <div class="leader-cards" aria-label="All leader card pictures">\n' + leader_cards_html() + "\n          </div>"
    text = re.sub(
        r'          <div class="leader-cards" aria-label="All leader card pictures">.*?</div>',
        grid,
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text)
    print("leaders page", n)


def main() -> None:
    cache = gen.load_card_cache()
    for leader in gen.LEADERS:
        hub = ROOT / leader["page"]
        if hub.exists():
            hub.write_text(patch_nav_and_assets(hub.read_text()))
        d = ROOT / leader["dir"]
        if not d.exists():
            continue
        for path in d.glob("*.html"):
            upgrade_list_page(path, leader, cache)
    patch_home()
    patch_op17()
    # leftover html (guides, format)
    for path in ROOT.rglob("*.html"):
        if any(p in path.parts for p in (".git", "scripts", "node_modules", "shop", "discord-bot", "ballkeep")):
            continue
        text = path.read_text()
        new = patch_nav_and_assets(text)
        if new != text:
            path.write_text(new)
    print("upgraded html")


if __name__ == "__main__":
    main()
