#!/usr/bin/env python3
"""Merge web + tournament lists on every leader hub.

One dated list, 30-at-a-time pagination, /leader/<key>/all pages with a
60-deck aggregate, and collapsed lazy card pictures.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import importlib.util

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

cspec = importlib.util.spec_from_file_location("commlists", "/workspace/scripts/add-community-lists.py")
comm = importlib.util.module_from_spec(cspec)
cspec.loader.exec_module(comm)

aspec = importlib.util.spec_from_file_location("leaderana", "/workspace/scripts/add-leader-analysis.py")
ana = importlib.util.module_from_spec(aspec)
aspec.loader.exec_module(ana)

sspec = importlib.util.spec_from_file_location("seocommon", "/workspace/scripts/seo_common.py")
seo = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(seo)

ROOT = gen.ROOT
SITE = "https://onepiecedecklists.com"
PAGE_SIZE = 30
AGGREGATE_WINDOW = 60
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
WEB_KINDS = {"youtube", "web", "x", "reddit"}
TOUR_KINDS = {"tournament", "featured", None, ""}

COMMUNITY_RE = re.compile(
    r"\s*<!-- COMMUNITY_DECKLISTS -->.*?<!-- /COMMUNITY_DECKLISTS -->\n?",
    re.S,
)
LISTS_RE = re.compile(
    r"\s*<!-- (?:COMMUNITY_DECKLISTS|TOURNAMENT_DECKLISTS|LEADER_LISTS) -->.*?"
    r"<!-- /(?:TOURNAMENT_DECKLISTS|LEADER_LISTS) -->\n?",
    re.S,
)
CARD_POOL_RE = re.compile(
    r"\s*<!-- CARD_POOL_HEADING -->.*?(?=\s*<!-- RELATED_LINKS -->)",
    re.S,
)
CARD_GRID_SECTION_RE = re.compile(
    r"\s*<section[^>]*>\s*<div class=\"section-title\">\s*"
    r"<h3>(?:Leader|Characters|Events|Stages)</h3>.*?</section>",
    re.S,
)
COLLECTION_LD_RE = re.compile(
    r'\s*<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"CollectionPage".*?</script>\n?',
    re.S,
)

HOST_LABELS = (
    ("play.limitlesstcg.com", "Limitless"),
    ("onepiece.limitlesstcg.com", "Limitless"),
    ("limitlesstcg.com", "Limitless"),
    ("optcg.gg", "OPTCG.GG"),
    ("opdeckguide.com", "OPDeckGuide"),
    ("onepiecedb.io", "OnePieceDB"),
    ("youtube.com", "YouTube"),
    ("youtu.be", "YouTube"),
    ("tcg-portal.jp", "TCG Portal"),
    ("twitter.com", "X"),
    ("x.com", "X"),
    ("reddit.com", "Reddit"),
    ("mercardop.jp", "Mercardop"),
    ("mabitcg.com", "Mabi TCG"),
    ("cardkaizoku.com", "Card Kaizoku"),
)


def all_href(leader: dict) -> str:
    return f"/leader/{leader['key']}/all/"


def all_path(leader: dict) -> Path:
    return ROOT / "leader" / leader["key"] / "all" / "index.html"


def hub_href(leader: dict) -> str:
    return "/" + leader["page"]


def site_label(url: str, kind: str | None, source: str) -> str:
    host = (urlparse(url or "").netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    for needle, label in HOST_LABELS:
        if needle in host:
            return label
    if kind == "youtube":
        return "YouTube"
    if kind == "x":
        return "X"
    if kind == "reddit":
        return "Reddit"
    if source == "tournament":
        return "Limitless"
    return "Web"


def tournament_id(url: str) -> str:
    m = re.search(r"/tournament/([^/]+)", url or "")
    return m.group(1) if m else ""


def norm_href(href: str) -> str:
    return (href or "").split("?")[0].rstrip("/").lower()


def player_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def extract_date(value: str) -> str:
    m = DATE_RE.search(value or "")
    return m.group(0) if m else ""


def load_json(name: str) -> dict:
    path = ROOT / "data" / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def load_starred() -> set[str]:
    path = ROOT / "data/starred-lists.json"
    if not path.exists():
        return set()
    try:
        rows = json.loads(path.read_text())
    except json.JSONDecodeError:
        return set()
    if not isinstance(rows, list):
        return set()
    return {norm_href(href) for href in rows if isinstance(href, str)}


def community_raw(leader: dict) -> list[dict]:
    rows = list(comm.COMMUNITY.get(leader["id"]) or [])
    extra = load_json("community-decks.json").get(leader["id"]) or []
    rows.extend(extra)
    return rows


def classify(kind: str | None) -> str | None:
    if kind == "sample":
        return None
    if kind in WEB_KINDS:
        return "web"
    if kind in TOUR_KINDS:
        return "tournament"
    return "web"


def entry_from_item(leader: dict, item: dict, default_source: str) -> dict | None:
    kind = item.get("kind")
    source = classify(kind)
    if source is None:
        return None
    if default_source == "web" and source == "tournament":
        source = "web"
    slug = item.get("slug") or ""
    href = item.get("href") or (f"/{leader['dir']}/{slug}.html" if slug else "")
    if not href:
        return None
    path = ROOT / href.lstrip("/")
    if not path.exists():
        return None
    date = item.get("date") or extract_date(item.get("subtitle") or "") or extract_date(item.get("title") or "")
    placing = item.get("placing")
    player = item.get("player") or ""
    event = item.get("tournament_name") or item.get("tournament") or ""
    source_url = item.get("source_url") or ""
    origin = site_label(source_url, kind, source)
    if source == "tournament":
        row = dict(item)
        row.setdefault("tournament_name", event or "Limitless event")
        title, subtitle = gen.list_heading(row, leader["name"])
        if not event:
            event = row.get("tournament_name") or ""
    else:
        title = item.get("title_override") or item.get("title") or slug
        subtitle = item.get("subtitle") or ""
        bits = [b for b in (origin, date) if b]
        if not subtitle:
            subtitle = " · ".join(bits)
        elif origin and origin.lower() not in subtitle.lower():
            subtitle = f"{subtitle} · {origin}"
    right = date or ("Tournament" if source == "tournament" else origin or "List")
    return {
        "slug": slug,
        "href": href,
        "title": title,
        "subtitle": subtitle,
        "date": date,
        "placing": placing,
        "player": player,
        "event": event,
        "kind": kind,
        "source": source,
        "origin": origin,
        "source_url": source_url,
        "path": str(path),
        "right": right,
    }


def collect_lists(leader: dict, tour_index: dict) -> list[dict]:
    rows: list[dict] = []
    for item in tour_index.get(leader["id"]) or []:
        row = entry_from_item(leader, item, "tournament")
        if row:
            rows.append(row)
    for item in community_raw(leader):
        row = entry_from_item(leader, item, "web")
        if row:
            rows.append(row)
    return dedupe_lists(rows)


def dedupe_lists(rows: list[dict]) -> list[dict]:
    rank = {"tournament": 0, "web": 1}
    ordered = sorted(rows, key=lambda r: (rank.get(r["source"], 9), r.get("href") or ""))
    seen: set[tuple] = set()
    out: list[dict] = []
    for row in ordered:
        keys = []
        href = norm_href(row.get("href") or "")
        slug = (row.get("slug") or "").lower()
        tid = tournament_id(row.get("source_url") or "")
        player = player_key(row.get("player") or "")
        date = row.get("date") or ""
        placing = "" if row.get("placing") is None else str(row.get("placing"))
        if href:
            keys.append(("h", href))
        if slug:
            keys.append(("s", slug))
        if tid and player:
            keys.append(("t", tid, player))
        if player and date:
            keys.append(("p", player, date, placing))
        if keys and any(k in seen for k in keys):
            continue
        for k in keys:
            seen.add(k)
        out.append(row)
    out.sort(key=lambda r: gen.date_sort_key(r), reverse=True)
    return out


def sim_for(leader: dict, row: dict, cache: dict[str, str]) -> str:
    href = row.get("href") or ""
    if href in cache:
        return cache[href]
    text = gen.sim_text_for_entry(leader, row)
    cache[href] = text
    return text


def row_payload(leader: dict, row: dict, sim_cache: dict[str, str], starred: set[str]) -> dict:
    placing = row.get("placing")
    href = row.get("href") or ""
    return {
        "href": href,
        "title": row["title"],
        "subtitle": row["subtitle"],
        "date": row.get("date") or "",
        "placing": "" if placing is None else str(placing),
        "source": row["source"],
        "origin": row.get("origin") or "",
        "right": row.get("right") or "View",
        "sim": gen.sim_compact(sim_for(leader, row, sim_cache)),
        "star": norm_href(href) in starred,
    }


def row_html(payload: dict) -> str:
    source = "tournament" if payload.get("source") == "tournament" else "web"
    tag = "Tournament" if source == "tournament" else "Web"
    tag_cls = "list-tag-tournament" if source == "tournament" else "list-tag-web"
    origin = payload.get("origin") or ""
    subtitle = payload.get("subtitle") or ""
    if origin and origin.lower() not in subtitle.lower():
        subtitle = f"{subtitle} · {origin}" if subtitle else origin
    copy_btn = gen.copy_sim_button(payload.get("sim") or "")
    placing = payload.get("placing") or ""
    date_s = payload.get("date") or ""
    star = (
        '<span class="new-list-mark" title="New" aria-label="New">*</span>'
        if payload.get("star")
        else ""
    )
    return f"""            <li class="list-row" data-date="{html.escape(date_s)}" data-placing="{html.escape(placing)}" data-source="{html.escape(source)}">
              <a class="item" href="{html.escape(payload.get('href') or '')}">
                <div>
                  <div class="list-row-title"><span class="list-tag {tag_cls}">{tag}</span> {html.escape(payload.get('title') or '')}{star}</div>
                  <div class="muted" style="font-size:13px">{html.escape(subtitle)}</div>
                </div>
                <div class="link">{html.escape(str(payload.get('right') or 'View'))} →</div>
              </a>
              {copy_btn}
            </li>"""


def aggregate_label(n_used: int, n_total: int, dmin: str, dmax: str) -> str:
    if n_total <= AGGREGATE_WINDOW:
        head = f"Top aggregate list: built from all {n_used} decks"
    else:
        head = f"Top aggregate list: built from the {n_used} most recent decks"
    if dmin and dmax and dmin == dmax:
        head += f" ({dmin})"
    elif dmin and dmax:
        head += f" ({dmin} to {dmax})"
    return head


def window_decks(leader: dict, rows: list[dict]) -> tuple[list[dict[str, int]], list[dict], str, str]:
    parsed: list[dict[str, int]] = []
    used_rows: list[dict] = []
    for row in rows[:AGGREGATE_WINDOW]:
        path = ROOT / row["href"].lstrip("/")
        if not path.exists():
            continue
        deck = ana.parse_deck(path, leader["id"])
        if not deck:
            continue
        parsed.append(deck)
        used_rows.append(row)
    dates = [r.get("date") or "" for r in used_rows if r.get("date")]
    dmin = min(dates) if dates else ""
    dmax = max(dates) if dates else ""
    return parsed, used_rows, dmin, dmax


def render_aggregate(leader: dict, picks: list, cache: dict, label: str) -> str:
    grouped, totals = ana.grouped_from_picks(leader, picks, cache)
    text_deck = gen.render_text_deck(grouped, cache, ["Leader", "Characters", "Events", "Stages"], totals)
    text_deck = text_deck.replace("<h3>Text list</h3>", f"<h3>{html.escape(label)}</h3>", 1)
    note = (
        '<p class="muted">Legal 50-card list from inclusion rate and average copies. '
        "Updates as newer lists land. Hover or tap a card name to see the picture.</p>"
    )
    text_deck = text_deck.replace(
        '<p class="muted">Hover or tap a card name to see the picture. Copy pastes <code>NxSET-NNN</code> lines for OP TCG SIM import.</p>',
        note,
        1,
    )
    text_deck = text_deck.replace(
        '<p class="muted">Hover or tap a card name to see the picture. Copy pastes <code>NxSET-NNN</code> for OPTCGSim.</p>',
        note,
        1,
    )
    text_deck = text_deck.replace(
        '<p class="muted">Hover or tap a card name to see the picture.</p>',
        note,
        1,
    )
    if "Legal 50-card list" not in text_deck:
        text_deck = text_deck.replace(
            '</div>\n          <div class="text-deck-cols">',
            f"</div>\n          {note}\n          <div class=\"text-deck-cols\">",
            1,
        )
    return text_deck


def lazy_images(markup: str) -> str:
    return re.sub(r"<img src=\"", "<img data-src=\"", markup)


def render_pictures(leader: dict, picks: list, cache: dict, label: str) -> str:
    grouped, _totals = ana.grouped_from_picks(leader, picks, cache)
    sections = []
    for group in ("Leader", "Characters", "Events", "Stages"):
        items = grouped.get(group) or []
        if not items:
            continue
        articles = []
        for item in items:
            meta = cache.get(item["id"]) or {}
            articles.append(lazy_images(gen.render_card_entry(item, meta)))
        sections.append(
            f"""        <section style="margin-top:22px">
          <div class="section-title">
            <h3>{html.escape(group)}</h3>
            <div class="muted">{len(items)} {'card' if len(items) == 1 else 'cards'}</div>
          </div>
          <div class="card-grid">
{chr(10).join(articles)}
          </div>
        </section>"""
        )
    if not sections:
        return ""
    return f"""        <!-- CARD_PICTURES -->
        <div id="leader-card-pictures" class="leader-card-pictures" hidden>
          <div class="section-title" style="margin-top:8px">
            <h3>Card pictures and descriptions</h3>
            <div class="muted">{html.escape(label)}</div>
          </div>
{chr(10).join(sections)}
        </div>
        <!-- /CARD_PICTURES -->"""


def render_actions(leader: dict, n_lists: int, has_pictures: bool) -> str:
    buttons = []
    if has_pictures:
        buttons.append(
            '<button type="button" class="leader-action-btn" data-show-card-pictures '
            'aria-expanded="false" aria-controls="leader-card-pictures">'
            '<span class="leader-action-label">Show card pictures and descriptions</span>'
            "</button>"
        )
    if n_lists > PAGE_SIZE:
        buttons.append(
            '<button type="button" class="leader-action-btn" data-show-more-lists>'
            "Show 30 more lists</button>"
        )
    if n_lists:
        buttons.append(
            f'<a class="leader-action-btn leader-action-link" href="{html.escape(all_href(leader))}">'
            "View all lists</a>"
        )
    if not buttons:
        return ""
    return f"""        <div class="leader-actions" role="group" aria-label="Leader list controls">
{chr(10).join("          " + b for b in buttons)}
        </div>"""


def render_hub_lists(leader: dict, payloads: list[dict], has_pictures: bool) -> str:
    visible = payloads[:PAGE_SIZE]
    rest = payloads[PAGE_SIZE:]
    rows = [row_html(p) for p in visible]
    rest_json = json.dumps(rest, ensure_ascii=True, separators=(",", ":"))
    rest_json = rest_json.replace("<", "\\u003c")
    extra = ""
    if rest:
        extra = (
            f'\n          <script type="application/json" id="leader-lists-more">'
            f"{rest_json}</script>"
        )
    n = len(payloads)
    actions = render_actions(leader, n, has_pictures)
    return f"""        <!-- LEADER_LISTS -->
        <section class="deck-index" data-leader-lists style="margin-top:22px">
          <div class="section-title">
            <h3>Decklists</h3>
            <div class="muted">{n} lists</div>
          </div>
          <p class="muted">Tournament and web lists in one list, newest first. Dates are the event or posted day, not the scrape day.</p>
          <ul class="list" data-leader-lists aria-label="{html.escape(leader['name'])} decklists">
{chr(10).join(rows) if rows else '            <li class="muted">No lists yet.</li>'}
          </ul>{extra}
{actions}
        </section>
        <!-- /LEADER_LISTS -->"""


def render_all_filters() -> str:
    return """          <div class="list-filters" data-all-filters>
            <input type="search" data-filter="q" placeholder="Search player, event, or site" aria-label="Search lists" />
            <label class="filter-date">From
              <input type="date" data-filter="from" aria-label="From date" />
            </label>
            <label class="filter-date">To
              <input type="date" data-filter="to" aria-label="To date" />
            </label>
            <select data-filter="source" aria-label="Source">
              <option value="">Any source</option>
              <option value="tournament">Tournament</option>
              <option value="web">Web</option>
            </select>
            <select data-filter="place" aria-label="Placement">
              <option value="">Any placement</option>
              <option value="top8">Top 8</option>
              <option value="win">1st only</option>
            </select>
            <button type="button" class="filter-clear" data-filter-clear>Clear filters</button>
          </div>
"""


def render_all_body(
    leader: dict,
    payloads: list[dict],
    aggregate_html: str,
    label: str,
) -> str:
    crumb_href, crumb_label = leader["crumb"]
    rows = [row_html(p) for p in payloads]
    n = len(payloads)
    return f"""        <div class="crumb"><a href="/">Home</a> / <a href="{html.escape(crumb_href)}">{html.escape(crumb_label)}</a> / <a href="{html.escape(hub_href(leader))}">{html.escape(leader['name'])}</a> / All lists</div>
        <p class="leader-back"><a href="{html.escape(hub_href(leader))}">← Back to {html.escape(leader['name'])} leader page</a></p>
        <h2>All {html.escape(leader['name'])} lists</h2>
        <p class="muted">{n} lists, newest first. Same merged tournament and web order as the leader page.</p>
        <section class="leader-aggregate" style="margin-top:22px">
{aggregate_html if aggregate_html else f'          <p class="muted">{html.escape(label)}</p>'}
        </section>
        <section class="deck-index leader-all" style="margin-top:22px">
          <div class="section-title">
            <h3>Every list</h3>
            <div class="muted">{n} lists</div>
          </div>
{render_all_filters() if n else ""}          <ul class="list" data-leader-all-lists aria-label="All {html.escape(leader['name'])} lists">
{chr(10).join(rows) if rows else '            <li class="muted">No lists yet.</li>'}
          </ul>
        </section>"""


def patch_all_head(page: str, title: str, desc: str, canon: str) -> str:
    page = re.sub(r"<title>[^<]*</title>", f"<title>{html.escape(title)}</title>", page, count=1)
    page = re.sub(
        r'<meta name="description" content="[^"]*" />',
        f'<meta name="description" content="{html.escape(desc, quote=True)}" />',
        page,
        count=1,
    )
    page = re.sub(
        r'<link rel="canonical" href="[^"]+" />',
        f'<link rel="canonical" href="{html.escape(canon, quote=True)}" />',
        page,
        count=1,
    )
    for prop, value in (
        ("og:url", canon),
        ("og:title", title),
        ("og:description", desc),
        ("og:image:alt", title),
    ):
        page = re.sub(
            rf'<meta property="{prop}" content="[^"]*" />',
            f'<meta property="{prop}" content="{html.escape(value, quote=True)}" />',
            page,
            count=1,
        )
    for prop, value in (("twitter:title", title), ("twitter:description", desc), ("twitter:image:alt", title)):
        page = re.sub(
            rf'<meta name="{prop}" content="[^"]*" />',
            f'<meta name="{prop}" content="{html.escape(value, quote=True)}" />',
            page,
            count=1,
        )
    page = re.sub(
        r'<link rel="alternate" hreflang="en" href="[^"]+" />',
        f'<link rel="alternate" hreflang="en" href="{html.escape(canon, quote=True)}" />',
        page,
        count=1,
    )
    page = re.sub(
        r'<link rel="alternate" hreflang="x-default" href="[^"]+" />',
        f'<link rel="alternate" hreflang="x-default" href="{html.escape(canon, quote=True)}" />',
        page,
        count=1,
    )
    crumb = (
        '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
        '{"@type":"ListItem","position":1,"name":"Home","item":"' + SITE + '/"},'
        '{"@type":"ListItem","position":2,"name":"Leaders","item":"' + SITE + '/decklists/op17.html"},'
        '{"@type":"ListItem","position":3,"name":' + json.dumps(title) + ',"item":"' + canon + '"}]}'
    )
    page = re.sub(
        r'<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"BreadcrumbList".*?</script>',
        f'<script type="application/ld+json">{crumb}</script>',
        page,
        count=1,
    )
    page = COLLECTION_LD_RE.sub("\n", page, count=1)
    return page


def write_all_page(leader: dict, hub_html: str, body: str, title: str, desc: str) -> None:
    canon = SITE + all_href(leader)
    page = hub_html
    page = patch_all_head(page, title, desc, canon)
    page = re.sub(
        r'<main class="single">.*?</main>',
        '<main class="single">\n      <div class="card hero">\n' + body + "\n      </div>\n    </main>",
        page,
        count=1,
        flags=re.S,
    )
    page = seo.apply_theme_chrome(page)
    out = all_path(leader)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)


def strip_old_blocks(page: str) -> str:
    page = ana.BLOCK_RE.sub("\n", page)
    page = re.sub(
        r"\s*<!-- LEADER_STRATEGY -->.*?<!-- /LEADER_STRATEGY -->\n?",
        "\n",
        page,
        count=1,
        flags=re.S,
    )
    page = COMMUNITY_RE.sub("\n", page)
    page = LISTS_RE.sub("\n", page)
    page = CARD_POOL_RE.sub("\n", page)
    page = CARD_GRID_SECTION_RE.sub("", page)
    page = re.sub(
        r"\s*<!-- CARD_PICTURES -->.*?<!-- /CARD_PICTURES -->\n?",
        "\n",
        page,
        count=1,
        flags=re.S,
    )
    page = re.sub(
        r"\s*<div class=\"leader-actions\"[^>]*>.*?</div>\n?",
        "\n",
        page,
        flags=re.S,
    )
    return page


def rebuild_one(
    leader: dict,
    tour_index: dict,
    cache: dict,
    sim_cache: dict[str, str],
    consensus_out: dict,
    starred: set[str],
) -> dict:
    page_path = ROOT / leader["page"]
    if not page_path.exists():
        print("skip missing hub", page_path)
        return {"page": leader["page"], "lists": 0, "deduped": 0}
    rows = collect_lists(leader, tour_index)
    payloads = [row_payload(leader, row, sim_cache, starred) for row in rows]
    parsed, used_rows, dmin, dmax = window_decks(leader, rows)
    label = aggregate_label(len(parsed), len(rows), dmin, dmax)
    picks = ana.consensus_list(parsed) if parsed else []
    aggregate_html = render_aggregate(leader, picks, cache, label) if picks else ""
    pictures = render_pictures(leader, picks, cache, label) if picks else ""
    take = ana.TAKES.get(leader["id"]) or (
        f"{leader['name']} ({leader['id']}) lists on this site are hosted public constructed lists."
    )
    analysis = ""
    if picks:
        op17_n = sum(1 for deck in parsed if ana._has_op17(deck))
        analysis = ana.analysis_block(leader, len(parsed), take, aggregate_html, op17_n)
        analysis = analysis.replace("<h3>Consensus list</h3>", f"<h3>{html.escape(label)}</h3>", 1)
        analysis = analysis.replace("<h3>Text list</h3>", f"<h3>{html.escape(label)}</h3>", 1)
        analysis = re.sub(
            r'<p class="muted">Averaged from .*?</p>',
            f'<p class="muted">{html.escape(label)}. Legal 50-card list from inclusion rate and average copies.</p>',
            analysis,
            count=1,
        )
    lists_html = render_hub_lists(leader, payloads, bool(pictures))
    block = "\n".join(x for x in (analysis, lists_html, pictures) if x)

    page = strip_old_blocks(page_path.read_text())
    if "<!-- RELATED_LINKS -->" in page:
        page = page.replace("<!-- RELATED_LINKS -->", block + "\n        <!-- RELATED_LINKS -->", 1)
    else:
        page = gen.insert_section(page, block, "")
    page = seo.apply_theme_chrome(page)
    page_path.write_text(page)

    title = f"All {leader['name']} lists | One Piece Decklists"
    desc = (
        f"Every {leader['name']} decklist on One Piece Decklists, newest first, "
        f"with a top aggregate list from the {min(len(rows), AGGREGATE_WINDOW) or 0} most recent decks."
    )
    all_body = render_all_body(leader, payloads, aggregate_html, label)
    write_all_page(leader, page, all_body, title, desc)

    consensus_out[leader["id"]] = {
        "lists": len(parsed),
        "window": min(len(rows), AGGREGATE_WINDOW),
        "from": dmin,
        "to": dmax,
        "cards": [{"id": cid, "count": count, "rate": round(rate, 3)} for cid, count, rate in picks],
    }
    return {
        "page": leader["page"],
        "lists": len(payloads),
        "window": len(parsed),
        "all": all_href(leader),
    }


def rebuild(only_ids: set[str] | None = None) -> None:
    cache = gen.load_card_cache()
    tour_index = load_json("tournament-decks.json")
    sim_cache: dict[str, str] = {}
    consensus_out: dict = {}
    starred = load_starred()
    leaders = [L for L in gen.LEADERS if only_ids is None or L["id"] in only_ids]
    for leader in leaders:
        info = rebuild_one(leader, tour_index, cache, sim_cache, consensus_out, starred)
        print("hub", info["page"], "lists", info.get("lists"), "agg", info.get("window"), flush=True)
    path = ROOT / "data/consensus-decks.json"
    if only_ids is None or not path.exists():
        path.write_text(json.dumps(consensus_out, indent=2) + "\n")
    else:
        current = load_json("consensus-decks.json")
        current.update(consensus_out)
        path.write_text(json.dumps(current, indent=2) + "\n")
    print("done", len(leaders), "hubs")


def main() -> None:
    rebuild()
    more_spec = importlib.util.spec_from_file_location("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    more = importlib.util.module_from_spec(more_spec)
    more_spec.loader.exec_module(more)
    more.rewrite_sitemap()


if __name__ == "__main__":
    main()
