#!/usr/bin/env python3
"""Build Extra Grand Battle hub, recent, and tier pages from hosted EXTRA lists.

Does not invent lists. Uses only pages already on the site that match Extra Grand
Battle (Limitless format EXTRA / [EGB] ChinoizeCup).
"""

from __future__ import annotations

import html
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
EGB_RECENT_HOME = 40
EGB_RECENT_PAGE = 250
EGB_TIER_PATH = ROOT / "data/egb-tier.json"
EGB_META_PATH = ROOT / "data/egb-meta.json"


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = load("genlists", str(ROOT / "scripts/generate-tournament-lists.py"))
seo = load("seocommon", str(ROOT / "scripts/seo_common.py"))
home_meta = load("homemeta", str(ROOT / "scripts/home_meta.py"))
up = load("upgrade", str(ROOT / "scripts/upgrade-public-pages.py"))
egb = load("egbcommon", str(ROOT / "scripts/egb_common.py"))
tierlib = load("tierlist", str(ROOT / "scripts/build-tier-list.py"))


def collect_egb_rows() -> list[dict]:
    rows = [row for row in up.collect_home_lists() if egb.is_egb(row)]
    rows.sort(key=gen.date_sort_key, reverse=True)
    return rows


def egb_stats(rows: list[dict]) -> dict[str, dict]:
    by_id: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        lid = (row.get("leader") or {}).get("id")
        if lid:
            by_id[lid].append(row)
    out = {}
    for L in gen.LEADERS:
        lid = L["id"]
        lists = by_id.get(lid) or []

        def place(xs, n):
            return sum(1 for x in xs if isinstance(x.get("placing"), int) and x["placing"] <= n)

        def wins(xs):
            return sum(1 for x in xs if x.get("placing") == 1)

        out[lid] = {
            "lists": len(lists),
            "wins": wins(lists),
            "top8": place(lists, 8),
            "top4": place(lists, 4),
            "recent_lists": len(lists),
            "recent_wins": wins(lists),
            "recent_top8": place(lists, 8),
            "community": 0,
            "best": min((x.get("placing") for x in lists if isinstance(x.get("placing"), int)), default=None),
            "href": "/" + L["page"],
        }
    return out


def egb_tiers(stats: dict[str, dict]) -> list[dict]:
    ranked = []
    for L in gen.LEADERS:
        lid = L["id"]
        s = stats.get(lid) or {}
        if not s.get("lists"):
            continue
        score = (
            s["wins"] * 6
            + s["top8"] * 1.4
            + min(s["lists"], 80) * 0.12
        )
        if score >= 22:
            letter = "S"
        elif score >= 10:
            letter = "A"
        elif score >= 4:
            letter = "B"
        elif score >= 1.5:
            letter = "C"
        else:
            letter = "D"
        ranked.append(
            {
                "id": lid,
                "name": L["name"],
                "href": "/" + L["page"],
                "image": tierlib.leader_img(lid),
                "color": L.get("color") or "",
                "color_label": tierlib.color_name(L),
                "tier": letter,
                "score": round(score, 2),
                "sources": 1,
                "votes": {letter: 1},
                **s,
            }
        )
    order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
    ranked.sort(key=lambda r: (order[r["tier"]], -r["score"], -r["recent_top8"], -r["lists"], r["name"]))
    return ranked


def chrome(title: str, desc: str, rel: str, current: str, crumbs: list[tuple[str, str]], body: str) -> str:
    url = seo.SITE + "/" + rel
    nav = seo.primary_nav_html(current=current)
    crumbs_json = seo.breadcrumb_jsonld(crumbs)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}" />
{seo.THEME_BOOT_SCRIPT}  <link rel="stylesheet" href="/css/site.css?v={seo.CSS_VER}" />
  <link rel="canonical" href="{html.escape(url)}" />
{seo.google_head_tags(url)}{seo.social_tags(title, desc, url, seo.DEFAULT_OG)}{crumbs_json}</head>
<body>
  <div class="wrap wrap-home">
    <header>
      <a class="brand" href="/">
        {seo.BRAND_LOGO_HTML}
        <div>
          <h1>One Piece Decklists</h1>
          <div class="subtitle">OPTCG decklists</div>
        </div>
      </a>
{seo.THEME_TOGGLE_HTML}{nav}
    </header>
    <main class="single home" role="main">
{body}
    </main>
    <footer>
      © <span id="year"></span> One Piece Decklists - Built with community in mind.
{seo.FOOTER_LINKS}
    </footer>
  </div>
  <script src="/js/site.js?v={seo.JS_VER}"></script>
  <script>document.getElementById("year").textContent = new Date().getFullYear();</script>
</body>
</html>
"""


def write_hub(rows: list[dict], pie: dict, featured: list[dict], leaders: list[dict]) -> None:
    recent = home_meta.newest_rows(rows, EGB_RECENT_HOME)
    visible = 20
    extra_n = max(0, len(recent) - visible)
    count_label = f"{visible} of {len(recent)}" if extra_n else f"{len(recent)} lists"
    if extra_n:
        more_btn = f"""          <div class="recent-more-row">
            <button type="button" class="recent-more-btn" data-recent-more>Show {extra_n} more</button>
            <a class="recent-all-link" href="/extra-grand-battle-recent.html">All Extra Grand Battle lists →</a>
          </div>"""
    else:
        more_btn = """          <div class="recent-more-row">
            <a class="recent-all-link" href="/extra-grand-battle-recent.html">All Extra Grand Battle lists →</a>
          </div>"""
    pie_block = home_meta.pie_html(
        pie,
        kicker="Extra Grand Battle share",
        heading="EGB lists",
        more_href="/extra-grand-battle-tier.html",
        more_label="EGB tier list →",
        lede="Share of hosted Extra Grand Battle lists that play at least one OP17 card. The hole is the leader converting best in EXTRA cups.",
        other_href="/extra-grand-battle.html",
    )
    featured_block = home_meta.featured_html(
        featured,
        recent_href="/extra-grand-battle-recent.html",
        recent_label="All EGB lists →",
        kicker="EXTRA top cuts",
        heading="Extra Grand Battle results",
        lede="First through fourth from hosted Extra Grand Battle cups. One list per leader when we can.",
    )
    cards = home_meta.leader_cards_html(leaders)
    body = f"""      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Extra Grand Battle</div>
        <h2>Extra Grand Battle</h2>
        <p>Online EXTRA constructed cups — mostly [EGB] ChinoizeCup Wednesdays. These lists keep Block 1 cards that Standard rotated out. Standard OP17 stays on the homepage. This page only counts complete Extra Grand Battle 50-card lists hosted here.</p>
      </div>
        <nav class="home-big3" aria-label="Extra Grand Battle sections">
          <a class="home-big home-big-tier" href="/extra-grand-battle-tier.html">
            <span class="home-big-title">EGB Tier List</span>
            <span class="home-big-note">S through D from Extra Grand Battle lists on this site</span>
          </a>
          <a class="home-big home-big-recent" href="#recent">
            <span class="home-big-title">EGB Recent</span>
            <span class="home-big-note">Newest EXTRA 50-card results</span>
          </a>
          <a class="home-big home-big-leaders" href="#leaders">
            <span class="home-big-title">EGB Leaders</span>
            <span class="home-big-note">Most posted Extra Grand Battle leaders</span>
          </a>
        </nav>
{featured_block}
{pie_block}
        <section class="home-leaders-flow" id="leaders">
          <div class="home-leaders-intro">
            <p class="home-leaders-kicker">Popular in EXTRA</p>
            <div class="home-leaders-intro-row">
              <h3>Leaders</h3>
              <a href="/decklists/op17.html">All leader pages →</a>
            </div>
          </div>
          <div class="card home-panel home-leaders-grid">
            <div class="leader-cards home-cards" aria-label="Extra Grand Battle leader pictures">
{cards}
            </div>
          </div>
        </section>
        <section class="card home-panel home-recent" id="recent">
          <p class="home-leaders-kicker">EXTRA results</p>
          <div class="section-title">
            <h3>Recent Extra Grand Battle lists</h3>
            <div class="muted">{count_label}</div>
          </div>
          <p class="muted home-recent-lede">Newest hosted EXTRA lists first.</p>
          <div class="recent-cols" aria-hidden="true">
            <span></span>
            <span>List</span>
            <span>Event</span>
            <span>Date</span>
          </div>
          <ul class="recent-list" aria-label="Recent Extra Grand Battle decklists">
{up.recent_rows_html(recent, hide_after=visible)}
          </ul>
{more_btn}
        </section>
"""
    page = chrome(
        "Extra Grand Battle decklists | One Piece Decklists",
        "Extra Grand Battle (EXTRA) One Piece TCG lists with a dedicated pie, tier list, and recent results.",
        "extra-grand-battle.html",
        "egb",
        [("Home", "/"), ("Extra Grand Battle", "/extra-grand-battle.html")],
        body,
    )
    (ROOT / "extra-grand-battle.html").write_text(page)


def write_recent(rows: list[dict]) -> None:
    page_rows = home_meta.newest_rows(rows, EGB_RECENT_PAGE)
    body = f"""      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/extra-grand-battle.html">Extra Grand Battle</a> / Recent</div>
        <h2>Recent Extra Grand Battle lists</h2>
        <p>Newest complete EXTRA 50-card pages hosted here. Standard lists stay on the main recent page.</p>
      </div>
      <section class="card home-panel home-recent" id="recent">
        <div class="section-title">
          <h3>All Extra Grand Battle lists</h3>
          <div class="muted">{len(page_rows)} lists</div>
        </div>
        <div class="recent-cols" aria-hidden="true">
          <span></span>
          <span>List</span>
          <span>Event</span>
          <span>Date</span>
        </div>
        <ul class="recent-list" aria-label="Extra Grand Battle decklists">
{up.recent_rows_html(page_rows)}
        </ul>
      </section>
"""
    page = chrome(
        "Recent Extra Grand Battle decklists | One Piece Decklists",
        "Newest Extra Grand Battle (EXTRA) One Piece TCG 50-card lists hosted on One Piece Decklists.",
        "extra-grand-battle-recent.html",
        "egb",
        [
            ("Home", "/"),
            ("Extra Grand Battle", "/extra-grand-battle.html"),
            ("Recent", "/extra-grand-battle-recent.html"),
        ],
        body,
    )
    (ROOT / "extra-grand-battle-recent.html").write_text(page)


def write_tier(rows: list[dict], ranked: list[dict]) -> None:
    board = tierlib.render_board(ranked)
    table = tierlib.render_table(ranked).replace(
        "Recent = 2026-08-20 onward, covering the OP17 English window",
        "Counts are Extra Grand Battle lists only",
    ).replace("This site's lists in the mix", "Extra Grand Battle lists on this site")
    today = date.today().isoformat()
    s_names = [r["name"] for r in ranked if r["tier"] == "S"]
    intro = (
        "This board uses only Extra Grand Battle lists hosted here: EXTRA cups such as "
        "[EGB] ChinoizeCup. Wins and top eights in those events set the order. "
        "It is not the Standard OP17 tier list."
    )
    if s_names:
        lead = ", ".join(s_names[:-1]) + " and " + s_names[-1] if len(s_names) > 1 else s_names[0]
        intro = f"{lead} sit in S for Extra Grand Battle. {intro}"
    body = f"""      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/extra-grand-battle.html">Extra Grand Battle</a> / Tier list</div>
        <h2>Extra Grand Battle tier list</h2>
        <p>{html.escape(intro)}</p>
        <p class="muted">Updated {today}. Leader pictures link to the 50-card lists on this site.</p>
        <div class="tier-board" aria-label="Extra Grand Battle leader tier list">
{board}
        </div>
{table}
      </div>
"""
    page = chrome(
        "Extra Grand Battle tier list | One Piece Decklists",
        "Extra Grand Battle (EXTRA) One Piece TCG tier list built from hosted EXTRA cup lists.",
        "extra-grand-battle-tier.html",
        "egb",
        [
            ("Home", "/"),
            ("Extra Grand Battle", "/extra-grand-battle.html"),
            ("Tier list", "/extra-grand-battle-tier.html"),
        ],
        body,
    )
    (ROOT / "extra-grand-battle-tier.html").write_text(page)


def patch_core_nav() -> None:
    needle = '        <a href="/tier-list.html">Tier List</a>\n        <a href="/#recent">Recent lists</a>'
    repl = (
        '        <a href="/tier-list.html">Tier List</a>\n'
        '        <a href="/extra-grand-battle.html">Extra Grand Battle</a>\n'
        '        <a href="/#recent">Recent lists</a>'
    )
    for rel in ("index.html", "format.html", "search.html", "decklists/op17.html", "tier-list.html", "recent.html"):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text()
        if "/extra-grand-battle.html" not in text:
            text = text.replace(needle, repl)
            text = text.replace(
                '        <a href="/tier-list.html">Tier List</a>\n        <a href="/recent.html">Recent lists</a>',
                '        <a href="/tier-list.html">Tier List</a>\n'
                '        <a href="/extra-grand-battle.html">Extra Grand Battle</a>\n'
                '        <a href="/recent.html">Recent lists</a>',
            )
        path.write_text(text)


def update_sitemaps() -> None:
    today = date.today().isoformat()
    core = ROOT / "sitemap-core.xml"
    if not core.exists():
        return
    text = core.read_text()
    for rel in (
        "extra-grand-battle.html",
        "extra-grand-battle-tier.html",
        "extra-grand-battle-recent.html",
    ):
        loc = f"{SITE}/{rel}"
        row = f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n"
        if loc in text:
            text = text.replace(
                f"<url><loc>{loc}</loc><lastmod>",
                f"<url><loc>{loc}</loc><lastmod>",
            )
            import re

            text = re.sub(
                rf"(<url><loc>{re.escape(loc)}</loc><lastmod>)[^<]+",
                rf"\g<1>{today}",
                text,
            )
        else:
            text = text.replace("</urlset>", row + "</urlset>")
    core.write_text(text)


def main() -> None:
    rows = collect_egb_rows()
    stats = egb_stats(rows)
    ranked = egb_tiers(stats)
    payload = {
        "updated": date.today().isoformat(),
        "format": "EXTRA",
        "list_count": len(rows),
        "leaders": ranked,
    }
    EGB_TIER_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    pie = home_meta.pie_slices(rows, tier_path=EGB_TIER_PATH)
    featured = home_meta.featured_rows(rows)
    leaders = home_meta.ranked_leaders(rows)
    EGB_META_PATH.write_text(
        json.dumps(
            {
                "updated": date.today().isoformat(),
                "lists": len(rows),
                "leaders": [{"id": L["id"], "name": L["name"], "count": L.get("home_lists", 0)} for L in leaders],
                "pie": [
                    {"id": s["id"], "name": s["name"], "count": s["count"], "pct": round(s["pct"], 1)}
                    for s in pie.get("slices") or []
                ],
            },
            indent=2,
        )
        + "\n"
    )
    write_hub(rows, pie, featured, leaders)
    write_recent(rows)
    write_tier(rows, ranked)
    patch_core_nav()
    update_sitemaps()
    print("egb lists", len(rows), "leaders", len(leaders), "tier", len(ranked), flush=True)
    by = Counter((row.get("leader") or {}).get("name") or "?" for row in rows)
    print("egb top", by.most_common(8), flush=True)


if __name__ == "__main__":
    main()
