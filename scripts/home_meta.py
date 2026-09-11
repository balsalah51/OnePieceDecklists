#!/usr/bin/env python3
"""Homepage popularity: top leaders, recent-set pie, and the all-lists page.

Recomputed whenever patch_home() runs after a scrape.
"""

from __future__ import annotations

import html
import importlib.util
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path("/workspace")
HOME_LEADER_COUNT = 10
POPULAR_WINDOW = 200
HOME_RECENT_VISIBLE = 25
HOME_RECENT_EXTRA = 25
RECENT_PAGE_LIMIT = 250
PIE_SCAN_LIMIT = 400
PIE_MAX_SLICES = 8
PIE_SMALL_PCT = 6.5
PIE_WIN_MIN_LISTS = 15
PIE_LABEL_MIN_PCT = 8.0
PIE_LABEL_MIN_GAP = 10.0
META_PATH = ROOT / "data/home-meta.json"

TILE = {
    "color-red": "#b71c1c",
    "color-green": "#2e7d32",
    "color-blue": "#1565c0",
    "color-purple": "#6a1b9a",
    "color-black": "#212121",
    "color-yellow": "#c9a227",
    "color-red-green": "#b71c1c",
    "color-blue-yellow": "#1565c0",
    "color-red-blue": "#b71c1c",
    "color-green-blue": "#2e7d32",
    "color-black-yellow": "#212121",
    "color-purple-yellow": "#6a1b9a",
    "color-red-black": "#b71c1c",
    "color-blue-purple": "#1565c0",
    "color-red-purple": "#b71c1c",
    "color-purple-black": "#6a1b9a",
    "color-red-yellow": "#b71c1c",
    "color-blue-black": "#1565c0",
    "color-green-yellow": "#2e7d32",
    "color-green-purple": "#2e7d32",
}


def _mix_hex(a: str, b: str, t: float) -> str:
    def parts(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    ar, ag, ab = parts(a)
    br, bg, bb = parts(b)
    r = round(ar + (br - ar) * t)
    g = round(ag + (bg - ag) * t)
    bl = round(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


def unique_fill(color_key: str, used: set[str]) -> str:
    fill = TILE.get(color_key, "#6b6f73")
    if fill in used:
        fill = _mix_hex(fill, "#ffffff", 0.32)
    if fill in used:
        fill = _mix_hex(fill, "#000000", 0.18)
    used.add(fill)
    return fill

QTY_ID_RE = re.compile(
    r'<span class="qty">(\d+)x</span>.*?<span class="muted card-id">([^<]+)</span>',
    re.S,
)
OP_SET_RE = re.compile(r"^OP(\d{2})-")

spec = importlib.util.spec_from_file_location("genlists", ROOT / "scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

sspec = importlib.util.spec_from_file_location("seocommon", ROOT / "scripts/seo_common.py")
seo = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(seo)


def newest_rows(rows: list[dict], limit: int) -> list[dict]:
    return sorted(rows, key=gen.date_sort_key, reverse=True)[:limit]


def ranked_leaders(rows: list[dict], window: int = POPULAR_WINDOW, limit: int = HOME_LEADER_COUNT) -> list[dict]:
    counts: Counter[str] = Counter()
    by_id = {}
    for row in newest_rows(rows, window):
        leader = row.get("leader") or {}
        lid = leader.get("id")
        if not lid:
            continue
        counts[lid] += 1
        by_id[lid] = leader
    ordered = []
    for lid, n in counts.most_common():
        leader = dict(by_id[lid])
        leader["home_lists"] = n
        ordered.append(leader)
        if len(ordered) >= limit:
            break
    if len(ordered) < limit:
        have = {L["id"] for L in ordered}
        for leader in gen.LEADERS:
            if leader["id"] in have:
                continue
            extra = dict(leader)
            extra["home_lists"] = counts.get(leader["id"], 0)
            ordered.append(extra)
            if len(ordered) >= limit:
                break
    return ordered[:limit]


def load_tier_lookup() -> dict[str, dict]:
    path = ROOT / "data/tier-list.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    out = {}
    for row in data.get("leaders") or []:
        lid = row.get("id")
        if lid:
            out[lid] = row
    return out


def _card_ids(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    start = text.find('class="text-deck"')
    blob = text[start : start + 160000] if start >= 0 else ""
    if not blob:
        return []
    return [cid.strip() for _n, cid in QTY_ID_RE.findall(blob)]


def detect_latest_set(rows: list[dict]) -> str:
    best = 17
    for row in newest_rows(rows, PIE_SCAN_LIMIT):
        href = (row.get("href") or "").lstrip("/")
        if not href:
            continue
        for cid in _card_ids(ROOT / href):
            m = OP_SET_RE.match(cid)
            if m:
                best = max(best, int(m.group(1)))
    return f"OP{best:02d}"


def _placing(row: dict) -> int | None:
    placing = row.get("placing")
    if placing is None or placing == "":
        return None
    try:
        return int(placing)
    except (TypeError, ValueError):
        return None


def pie_slices(rows: list[dict], latest_set: str | None = None) -> dict:
    sample = newest_rows(rows, PIE_SCAN_LIMIT)
    cards_by_href: dict[str, list[str]] = {}
    best = 17
    for row in sample:
        href = (row.get("href") or "").lstrip("/")
        if not href:
            continue
        ids = _card_ids(ROOT / href)
        cards_by_href[href] = ids
        for cid in ids:
            m = OP_SET_RE.match(cid)
            if m:
                best = max(best, int(m.group(1)))
    latest_set = latest_set or f"OP{best:02d}"
    prefix = latest_set + "-"
    counts: Counter[str] = Counter()
    placed: Counter[str] = Counter()
    firsts: Counter[str] = Counter()
    by_id = {}
    scanned = 0
    matched = 0
    for row in sample:
        href = (row.get("href") or "").lstrip("/")
        if not href:
            continue
        scanned += 1
        ids = cards_by_href.get(href) or []
        if not ids or not any(cid.startswith(prefix) for cid in ids):
            continue
        leader = row.get("leader") or {}
        lid = leader.get("id")
        if not lid:
            continue
        matched += 1
        counts[lid] += 1
        placing = _placing(row)
        if placing is not None:
            placed[lid] += 1
            if placing == 1:
                firsts[lid] += 1
        by_id[lid] = leader
    total = sum(counts.values()) or 1
    ranked = counts.most_common()
    keep = ranked[:PIE_MAX_SLICES]
    rest = ranked[PIE_MAX_SLICES:]
    rest_n = sum(n for _lid, n in rest)
    tiers = load_tier_lookup()
    slices = []
    cursor = 0.0
    used_fills: set[str] = set()
    for lid, n in keep:
        leader = by_id[lid]
        pct = 100.0 * n / total
        start = cursor
        cursor += pct
        tier = tiers.get(lid) or {}
        slices.append(
            {
                "id": lid,
                "name": leader["name"],
                "href": "/" + leader["page"],
                "image": gen.card_image_url(lid),
                "color": leader.get("color") or "",
                "fill": unique_fill(leader.get("color") or "", used_fills),
                "count": n,
                "pct": pct,
                "start": start,
                "mid": start + pct / 2,
                "small": pct < PIE_SMALL_PCT,
                "tier": tier.get("tier") or "",
                "score": tier.get("score"),
            }
        )
    if rest_n:
        pct = 100.0 * rest_n / total
        slices.append(
            {
                "id": "",
                "name": "Other",
                "href": "/decklists/op17.html",
                "image": "",
                "color": "",
                "fill": "#8a8580",
                "count": rest_n,
                "pct": pct,
                "start": cursor,
                "mid": cursor + pct / 2,
                "small": True,
                "tier": "",
                "score": None,
            }
        )
    hole = None
    best_key = None
    for lid, n_placed in placed.items():
        if n_placed < PIE_WIN_MIN_LISTS:
            continue
        wins = firsts[lid]
        rate = wins / n_placed
        key = (rate, wins, n_placed)
        if best_key is None or key > best_key:
            best_key = key
            leader = by_id[lid]
            hole = {
                "id": lid,
                "name": leader["name"],
                "href": "/" + leader["page"],
                "image": gen.card_image_url(lid),
                "wins": wins,
                "lists": n_placed,
                "win_pct": 100.0 * rate,
            }
    if hole is None and keep:
        lid, n = keep[0]
        leader = by_id[lid]
        n_placed = placed[lid] or n
        hole = {
            "id": lid,
            "name": leader["name"],
            "href": "/" + leader["page"],
            "image": gen.card_image_url(lid),
            "wins": firsts[lid],
            "lists": n_placed,
            "win_pct": 100.0 * firsts[lid] / n_placed if n_placed else 0.0,
        }
    return {
        "set": latest_set,
        "scanned": scanned,
        "matched": matched,
        "total": matched,
        "slices": slices,
        "hole": hole,
    }


def save_meta(leaders: list[dict], pie: dict, window: int = POPULAR_WINDOW) -> None:
    payload = {
        "window": window,
        "home_leaders": [
            {"id": L["id"], "name": L["name"], "count": L.get("home_lists", 0)} for L in leaders
        ],
        "set": pie.get("set"),
        "pie_lists": pie.get("matched"),
        "pie": [
            {"id": s["id"], "name": s["name"], "count": s["count"], "pct": round(s["pct"], 1)}
            for s in pie.get("slices") or []
        ],
        "hole": (
            {
                "id": pie["hole"]["id"],
                "name": pie["hole"]["name"],
                "wins": pie["hole"]["wins"],
                "lists": pie["hole"]["lists"],
                "win_pct": round(pie["hole"]["win_pct"], 1),
            }
            if pie.get("hole")
            else None
        ),
    }
    META_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def _pct_label(pct: float) -> str:
    if pct >= 10:
        return f"{pct:.0f}%"
    return f"{pct:.1f}%"


def _short_pie_name(name: str) -> str:
    short = {
        "Monkey D. Luffy": "Luffy",
        "Portgas D. Ace": "Ace",
        "Rocks D. Xebec": "Rocks",
        "Charlotte Linlin": "Linlin",
        "Edward Newgate": "Newgate",
        "Boa Hancock": "Boa",
        "Dracule Mihawk": "Mihawk",
    }
    if name in short:
        return short[name]
    if len(name) > 12:
        return name.split()[0]
    return name


def _circle_gap(a: float, b: float) -> float:
    d = abs(a - b)
    return min(d, 100.0 - d)


def _pie_labels(slices: list[dict]) -> list[dict]:
    ranked = sorted(slices, key=lambda row: row.get("pct") or 0, reverse=True)
    keep: list[dict] = []
    for row in ranked:
        if (row.get("pct") or 0) < PIE_LABEL_MIN_PCT:
            continue
        if any(_circle_gap(row["mid"], placed["mid"]) < PIE_LABEL_MIN_GAP for placed in keep):
            continue
        keep.append(row)
    return keep


def _label_xy(mid: float) -> tuple[str, str]:
    theta = mid / 100.0 * 2 * math.pi
    radius = 37.5
    x = 50 + radius * math.sin(theta)
    y = 50 - radius * math.cos(theta)
    return f"{x:.2f}%", f"{y:.2f}%"


def _tier_label(slice_row: dict) -> str:
    letter = slice_row.get("tier") or ""
    score = slice_row.get("score")
    if letter and score is not None:
        return f"{html.escape(str(letter))} · {score:.0f}"
    if letter:
        return html.escape(str(letter))
    return "Unranked"


def pie_html(pie: dict) -> str:
    slices = pie.get("slices") or []
    if not slices:
        return ""
    latest = pie.get("set") or "OP17"
    stops = []
    gap = 0.28
    for i, row in enumerate(slices):
        start = row["start"] + (gap if i else 0)
        end = row["start"] + row["pct"] - (gap if i < len(slices) - 1 else 0)
        if end <= start:
            start, end = row["start"], row["start"] + row["pct"]
        stops.append(f"{row['fill']} {start:.2f}% {end:.2f}%")
    gradient = ", ".join(stops)
    names = []
    for row in _pie_labels(slices):
        left, top = _label_xy(row["mid"])
        tight = " meta-pie-on-tight" if row["pct"] < 12 else ""
        names.append(
            f'<a class="meta-pie-on{tight}" href="{html.escape(row["href"])}" '
            f'style="left:{left};top:{top}">{html.escape(_short_pie_name(row["name"]))}</a>'
        )
    names_html = "\n              ".join(names)
    legend = []
    for row in slices:
        if row.get("image"):
            face = (
                f'<img class="meta-pie-face" src="{html.escape(row["image"])}" '
                f'alt="" width="48" height="48" />'
            )
        else:
            face = '<span class="meta-pie-face meta-pie-face-empty" aria-hidden="true"></span>'
        legend.append(
            f"""            <li style="--slice:{html.escape(row["fill"])}">
              <span class="meta-pie-swatch" style="background:{html.escape(row["fill"])}"></span>
              {face}
              <span class="meta-pie-legend-copy">
                <a href="{html.escape(row["href"])}">{html.escape(row["name"])}</a>
                <span class="meta-pie-legend-tier">{_tier_label(row)}</span>
              </span>
              <span class="meta-pie-legend-pct">{html.escape(_pct_label(row["pct"]))}</span>
            </li>"""
        )
    return f"""        <section class="card home-panel home-meta-pie" id="meta-share">
          <p class="home-leaders-kicker">Format share</p>
          <div class="section-title">
            <h3>{html.escape(latest)} lists</h3>
            <a href="/tier-list.html">Tier list →</a>
          </div>
          <p class="muted home-recent-lede">Share of the newest hosted lists that play at least one {html.escape(latest)} card. Bigger slices get a name when it fits. The list beside the chart has every leader, percent, and tier score.</p>
          <div class="meta-pie-board">
            <div class="meta-pie-disk" style="background:conic-gradient({gradient})">
              <div class="meta-pie-hole" aria-hidden="true"></div>
              {names_html}
            </div>
            <ul class="meta-pie-legend" aria-label="{html.escape(latest)} list share">
{chr(10).join(legend)}
            </ul>
          </div>
        </section>
"""


def leader_cards_html(leaders: list[dict]) -> str:
    cards = []
    for leader in leaders:
        img = gen.card_image_url(leader["id"])
        cards.append(
            f"""            <a class="leader-card-link" href="/{leader["page"]}">
              <img src="{img}" alt="{html.escape(leader["name"])} leader card" />
              <div class="caption">{html.escape(leader["name"])}</div>
            </a>"""
        )
    return "\n".join(cards)


def collection_jsonld_items(leaders: list[dict]) -> list[dict]:
    items = []
    for i, leader in enumerate(leaders, start=1):
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": leader["name"],
                "url": seo.SITE + "/" + leader["page"],
            }
        )
    return items


def patch_home_jsonld(text: str, leaders: list[dict]) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "One Piece TCG Decklists (OPTCG) | One Piece Decklists",
        "description": "OPTCG decklists for the Bandai ONE PIECE CARD GAME. Leader pictures and recent 50-card lists.",
        "url": seo.SITE + "/",
        "inLanguage": "en",
        "isPartOf": {"@id": seo.SITE + "/#website"},
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": collection_jsonld_items(leaders),
            "numberOfItems": len(leaders),
        },
    }
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    script = f'<script type="application/ld+json">{blob}</script>'
    if '"@type":"CollectionPage"' in text.replace(" ", ""):
        text = re.sub(
            r'<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"CollectionPage".*?</script>',
            script,
            text,
            count=1,
        )
    return text


def write_recent_page(rows_html: str, count: int) -> None:
    title = "Recent OPTCG decklists | One Piece Decklists"
    desc = "Newest 50-card One Piece TCG lists hosted on One Piece Decklists, newest first."
    url = seo.SITE + "/recent.html"
    nav = seo.primary_nav_html(current="recent")
    crumbs = seo.breadcrumb_jsonld([("Home", "/"), ("Recent lists", "/recent.html")])
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}" />
{seo.THEME_BOOT_SCRIPT}  <link rel="stylesheet" href="/css/site.css?v={seo.CSS_VER}" />
  <link rel="canonical" href="{html.escape(url)}" />
{seo.google_head_tags(url)}{seo.social_tags(title, desc, url, seo.DEFAULT_OG)}{crumbs}</head>
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
      <div class="theme-toggle" role="group" aria-label="Color theme">
        <button type="button" class="theme-toggle-btn" data-theme-set="light" aria-pressed="true">Light</button>
        <button type="button" class="theme-toggle-btn" data-theme-set="dark" aria-pressed="false">Dark</button>
      </div>
{nav}
    </header>
    <main class="single home" role="main">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Recent lists</div>
        <h2>Recent lists</h2>
        <p>Newest complete 50-card pages on this site. Search if you need an older result.</p>
        <form class="site-search" method="get" action="/search.html" role="search">
          <label class="site-search-label" for="recent-q">Search OPTCG decklists</label>
          <div class="site-search-row">
            <input id="recent-q" type="search" name="q" placeholder="Leader, player, or event" aria-label="Search OPTCG decklists" />
            <button type="submit">Search</button>
          </div>
        </form>
      </div>
      <section class="card home-panel home-recent" id="recent">
        <div class="section-title">
          <h3>All recent lists</h3>
          <div class="muted">{count} lists</div>
        </div>
        <div class="recent-cols" aria-hidden="true">
          <span></span>
          <span>List</span>
          <span>Event</span>
          <span>Date</span>
        </div>
        <ul class="recent-list" aria-label="Recent decklists">
{rows_html}
        </ul>
      </section>
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
    (ROOT / "recent.html").write_text(page)
    core = ROOT / "sitemap-core.xml"
    if core.exists() and "recent.html" not in core.read_text():
        text = core.read_text()
        text = text.replace(
            "</urlset>",
            "  <url><loc>https://onepiecedecklists.com/recent.html</loc></url>\n</urlset>",
            1,
        )
        core.write_text(text)
