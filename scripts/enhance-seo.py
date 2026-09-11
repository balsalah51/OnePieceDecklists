#!/usr/bin/env python3
"""Patch public HTML for Google Search crawl, sitelinks search, and on-page SEO.

Does not wipe decklist pages. Safe to re-run.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

sspec = importlib.util.spec_from_file_location("seocommon", "/workspace/scripts/seo_common.py")
seo = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(seo)

gspec = importlib.util.spec_from_file_location("seopages", "/workspace/scripts/generate-seo-pages.py")
seopages = importlib.util.module_from_spec(gspec)
gspec.loader.exec_module(seopages)

ROOT = gen.ROOT
SITE = seo.SITE
LEADERS = gen.LEADERS
BY_ID = {L["id"]: L for L in LEADERS}
BY_PAGE = {L["page"]: L for L in LEADERS}
BY_DIR = {L["dir"]: L for L in LEADERS}

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"', re.I)
CANON_RE = re.compile(r'\s*<link rel="canonical" href="[^"]*"\s*/?>', re.I)
OG_RE = re.compile(
    r'\s*<meta\s+(?:property="(?:og|article):[^"]*"|name="twitter:[^"]*")[^>]*/?>',
    re.I,
)
JSONLD_RE = re.compile(r'\s*<script type="application/ld\+json">.*?</script>', re.S | re.I)
ROBOTS_META_RE = re.compile(r'\s*<meta name="(?:robots|googlebot)" content="[^"]*"\s*/?>', re.I)
ICON_RE = re.compile(
    r'\s*<link rel="(?:icon|shortcut icon|apple-touch-icon|manifest|search|alternate)"[^>]*/?>',
    re.I,
)
THEME_RE = re.compile(r'\s*<meta name="theme-color" content="[^"]*"\s*/?>', re.I)
ADSENSE_RE = re.compile(
    r"\s*<script[^>]*adsbygoogle\.js[^>]*>\s*</script>",
    re.I,
)
ADSENSE_META_RE = re.compile(
    r'\s*<meta\s+name="google-adsense-account"[^>]*/?>',
    re.I,
)
IMG_RE = re.compile(r"<img\b([^>]*)>", re.I)
SKIP_PARTS = {".git", "scripts", "node_modules", "discord-bot", "ballkeep"}
SKIP_FILES = {"shop/custom-leaders.html", "shop/buy-list.html"}
CORE_RELS = {
    "index.html",
    "format.html",
    "privacy.html",
    "search.html",
    "recent.html",
    "tier-list.html",
    "decklists/op17.html",
}


def log(*args) -> None:
    print(*args, flush=True)


def load_index() -> dict:
    path = ROOT / "data/tournament-decks.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def public_html() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        if any(part in p.parts for part in SKIP_PARTS):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP_FILES:
            continue
        out.append(p)
    return out


def leader_for_path(rel: str) -> dict | None:
    if rel in BY_PAGE:
        return BY_PAGE[rel]
    for L in LEADERS:
        if rel.startswith(L["dir"] + "/"):
            return L
    return None


def href_for_entry(leader: dict, entry: dict) -> str:
    return entry.get("href") or f"/{leader['dir']}/{entry['slug']}.html"


def event_siblings(index: dict, leader: dict, slug: str, limit: int = 5) -> list[tuple[str, str, str]]:
    rows = index.get(leader["id"]) or []
    current = next((r for r in rows if r.get("slug") == slug), None)
    if not current:
        return []
    event = (current.get("tournament") or "").strip()
    if not event:
        return []
    out = []
    for r in rows:
        if r.get("slug") == slug:
            continue
        if (r.get("tournament") or "").strip() != event:
            continue
        other = BY_ID.get(leader["id"])
        if not other:
            continue
        player = r.get("player") or "List"
        place = r.get("placing")
        place_s = f"{place}" if place is not None else "list"
        out.append((href_for_entry(leader, r), f"{player} - {leader['name']}", f"{event} · {place_s}"))
        if len(out) >= limit:
            break
    return out


def other_leaders_same_event(index: dict, leader: dict, slug: str, limit: int = 4) -> list[tuple[str, str, str]]:
    rows = index.get(leader["id"]) or []
    current = next((r for r in rows if r.get("slug") == slug), None)
    if not current:
        return []
    event = (current.get("tournament") or "").strip()
    date_s = (current.get("date") or "")[:10]
    if not event:
        return []
    out = []
    seen = set()
    for lid, items in index.items():
        if lid == leader["id"]:
            continue
        L = BY_ID.get(lid)
        if not L:
            continue
        for r in items:
            if (r.get("tournament") or "").strip() != event:
                continue
            if date_s and (r.get("date") or "")[:10] != date_s:
                continue
            if lid in seen:
                continue
            seen.add(lid)
            player = r.get("player") or L["name"]
            out.append((href_for_entry(L, r), f"{player} - {L['name']}", f"Same event · {L['name']}"))
            break
        if len(out) >= limit:
            break
    return out


def related_leader_rows(leader: dict) -> list[str]:
    rows = []
    for lid in seo.RELATED_LEADERS.get(leader["id"], []):
        other = BY_ID.get(lid)
        if not other or other["id"] == leader["id"]:
            continue
        rows.append(
            seo.list_row(
                "/" + other["page"],
                f"{other['name']} decklists",
                f"{other['id']} · related constructed leader",
            )
        )
    return rows


def character_siblings(slug: str, limit: int = 8) -> list[str]:
    rows = []
    for name, cslug in seo.crew_siblings(slug, seopages.CHARACTERS, limit=limit):
        rows.append(
            seo.list_row(
                f"/guides/characters/{cslug}.html",
                name,
                "Same OPTCG family · character guide",
            )
        )
    return rows


def topic_siblings(slug: str, limit: int = 8) -> list[str]:
    topics = seopages.TOPICS
    idx = next((i for i, t in enumerate(topics) if t["slug"] == slug), None)
    if idx is None:
        return []
    rows = []
    n = len(topics)
    for off in range(1, n):
        other = topics[(idx + off) % n]
        if other["slug"] == slug:
            continue
        rows.append(
            seo.list_row(
                f"/guides/{other['slug']}.html",
                other["h2"],
                "More One Piece TCG guides",
            )
        )
        if len(rows) >= limit:
            break
    return rows


def deck_related_html(rel: str, index: dict) -> str:
    leader = leader_for_path(rel)
    if not leader:
        return ""
    slug = Path(rel).stem
    rows: list[str] = []
    rows.append(
        seo.list_row(
            "/" + leader["page"],
            f"More {leader['name']} lists",
            f"{leader['id']} hub · every 50-card list for this leader",
        )
    )
    guide = seo.LEADER_GUIDE.get(leader["key"])
    if guide:
        rows.append(
            seo.list_row(
                f"/guides/characters/{guide}.html",
                f"{leader['name']} character guide",
                "Names, crew, and related OPTCG leaders",
            )
        )
    for href, title, note in event_siblings(index, leader, slug):
        rows.append(seo.list_row(href, title, note))
    for href, title, note in other_leaders_same_event(index, leader, slug):
        rows.append(seo.list_row(href, title, note))
    rows.extend(related_leader_rows(leader)[:3])
    rows.append(seo.list_row("/tier-list.html", "OP17 tier list", "Aggregated S through D with leader pictures"))
    rows.append(seo.list_row("/format.html", "OPTCG format and banlist", "Standard rules, banned cards, rotation"))
    rows.append(seo.list_row("/shop/sleeves.html", "Sleeves for a 50-card list", "Shop · Dragon Shield packs"))
    return seo.related_section("Related pages", "More lists and guides", rows)


def hub_related_html(leader: dict) -> str:
    rows = related_leader_rows(leader)
    rows.append(seo.list_row("/tier-list.html", "OP17 tier list", "Aggregated S through D with leader pictures"))
    rows.append(seo.list_row("/decklists/op17.html", "All leader pages", "Every constructed leader on this site"))
    guide = seo.LEADER_GUIDE.get(leader["key"])
    if guide:
        rows.append(
            seo.list_row(
                f"/guides/characters/{guide}.html",
                f"{leader['name']} character guide",
                "Crew names mapped to this leader",
            )
        )
    rows.append(seo.list_row("/guides/", "One Piece TCG guides", "Topics and character pages"))
    if leader.get("key") == "mihawk":
        rows.insert(
            1,
            seo.list_row(
                "/guides/op17-mihawk-matchups.html",
                "Which decks beat OP17 Mihawk",
                "Limitless pairings · Robin, Ace, Sabo",
            ),
        )
    if leader.get("key") == "nico-robin":
        rows.insert(
            1,
            seo.list_row(
                "/guides/nico-robin-strategy.html",
                "Nico Robin strategy",
                "OP17 curve, Big Mom splash, Mihawk matchup",
            ),
        )
    if leader.get("key") == "sabo":
        rows.insert(
            1,
            seo.list_row(
                "/guides/sabo-strategy.html",
                "Sabo strategy",
                "OP17 Elbaph curve, mulligan, 52.1% vs Mihawk",
            ),
        )
    if leader.get("key") == "rocks-d-xebec":
        rows.insert(
            1,
            seo.list_row(
                "/guides/rocks-d-xebec-strategy.html",
                "Rocks D. Xebec strategy",
                "Even/odd Rocks Pirates curve · 33.6% vs Mihawk",
            ),
        )
    if leader.get("key") == "portgas-d-ace":
        rows.insert(
            1,
            seo.list_row(
                "/guides/portgas-d-ace-strategy.html",
                "Portgas D. Ace strategy",
                "Rush Whitebeard curve, mulligan, 57.8% vs Mihawk",
            ),
        )
    rows.append(seo.list_row("/format.html", "Format and banlist", "Standard constructed rules"))
    rows.append(seo.list_row("/tier-list.html", "OP17 tier list", "Aggregated S through D with leader pictures"))
    rows.append(seo.list_row("/#recent", "Recent lists", "Newest 50-card results"))
    return seo.related_section("Related pages", "Other leaders and guides", rows)


def shop_related_html(rel: str) -> str:
    rows = []
    for href, label in seo.SHOP_PAGES:
        target = "shop/index.html" if href == "/shop/" else href.lstrip("/")
        if target == rel:
            continue
        rows.append(seo.list_row(href, label, "Amazon shop · OPTCG table gear"))
    rows.append(seo.list_row("/decklists/op17.html", "Leader decklists", "50-card OPTCG lists"))
    return seo.related_section("Also in the shop", "Other gear pages", rows)


def character_related_extra(slug: str) -> str:
    rows = character_siblings(slug)
    if not rows:
        return ""
    rows.append(seo.list_row("/guides/characters/", "All character guides", "Every name mapped to an OPTCG list"))
    return seo.related_section("Related character guides", "Same crew or constructed family", rows)


STRATEGY_RELATED = {
    "nico-robin-strategy": [
        ("/decklists/nico-robin.html", "Nico Robin decklists", "Every hosted 50-card Robin list"),
        ("/guides/op17-mihawk-matchups.html", "Which decks beat OP17 Mihawk", "Robin is 58.8% in 80 games"),
        ("/guides/sabo-strategy.html", "Sabo strategy", "Elbaph midrange"),
        ("/guides/rocks-d-xebec-strategy.html", "Rocks D. Xebec strategy", "Blue Rocks Pirates"),
        ("/guides/portgas-d-ace-strategy.html", "Portgas D. Ace strategy", "Red Whitebeard Rush"),
    ],
    "sabo-strategy": [
        ("/decklists/sabo.html", "Sabo decklists", "Every hosted 50-card Sabo list"),
        ("/guides/op17-mihawk-matchups.html", "Which decks beat OP17 Mihawk", "Sabo is 52.1% in 165 games"),
        ("/guides/nico-robin-strategy.html", "Nico Robin strategy", "Yellow ramp into Linlin"),
        ("/guides/rocks-d-xebec-strategy.html", "Rocks D. Xebec strategy", "The other Tier 1 midrange"),
        ("/guides/portgas-d-ace-strategy.html", "Portgas D. Ace strategy", "Rush that races a slow Saul"),
    ],
    "rocks-d-xebec-strategy": [
        ("/decklists/op17/rocks-d-xebec.html", "Rocks D. Xebec decklists", "Every hosted 50-card Rocks list"),
        ("/guides/op17-mihawk-matchups.html", "Which decks beat OP17 Mihawk", "Rocks is 33.6% in 149 games"),
        ("/guides/sabo-strategy.html", "Sabo strategy", "The other Tier 1 midrange"),
        ("/guides/portgas-d-ace-strategy.html", "Portgas D. Ace strategy", "Rush Newgate"),
        ("/guides/nico-robin-strategy.html", "Nico Robin strategy", "Yellow 10-costs"),
    ],
    "portgas-d-ace-strategy": [
        ("/decklists/portgas-d-ace.html", "Portgas D. Ace decklists", "Every hosted 50-card Ace list"),
        ("/guides/op17-mihawk-matchups.html", "Which decks beat OP17 Mihawk", "Ace is 57.8% in 45 games"),
        ("/guides/sabo-strategy.html", "Sabo strategy", "The midrange Ace races"),
        ("/guides/rocks-d-xebec-strategy.html", "Rocks D. Xebec strategy", "A tough midrange seat"),
        ("/guides/nico-robin-strategy.html", "Nico Robin strategy", "Yellow 10-costs Ace would rather not see"),
    ],
    "op17-mihawk-matchups": [
        ("/guides/nico-robin-strategy.html", "Nico Robin strategy", "The volume hawk hunter"),
        ("/guides/sabo-strategy.html", "Sabo strategy", "52.1% vs Mihawk"),
        ("/guides/portgas-d-ace-strategy.html", "Portgas D. Ace strategy", "57.8% vs Mihawk"),
        ("/guides/rocks-d-xebec-strategy.html", "Rocks D. Xebec strategy", "The hard Slash seat"),
        ("/decklists/mihawk.html", "Mihawk decklists", "The rest/control list itself"),
    ],
}


def topic_related_extra(slug: str) -> str:
    curated = STRATEGY_RELATED.get(slug)
    if curated:
        rows = [seo.list_row(href, title, note) for href, title, note in curated]
        rows.append(seo.list_row("/guides/", "All guides", "Strategy, colors, and the two primers"))
        return seo.related_section("Keep reading", "Other strategy pages and lists", rows)
    rows = topic_siblings(slug, limit=4)
    rows.append(seo.list_row("/guides/", "All guides", "Strategy, colors, and the two primers"))
    rows.append(seo.list_row("/decklists/op17.html", "All leader pages", "Constructed OPTCG hubs"))
    return seo.related_section("Keep reading", "Nearby guide pages", rows)


def insert_related(text: str, block: str) -> str:
    if not block:
        return text
    text = seo.strip_related(text)
    markers = [
        '        <p class="muted" style="margin-top:22px">',
        '        <p class="muted" style="margin-top:18px">',
        '        <p class="amazon-disclosure-line">',
        "        <!-- CARD_POOL_HEADING -->",
        "      </div>\n    </main>",
    ]
    for mark in markers:
        if mark in text:
            return text.replace(mark, block + mark, 1)
    return text.replace("</main>", block + "    </main>", 1)


def page_title_desc(text: str, rel: str) -> tuple[str, str]:
    tm = TITLE_RE.search(text)
    dm = DESC_RE.search(text)
    title = html.unescape(tm.group(1).strip()) if tm else ""
    desc = html.unescape(dm.group(1).strip()) if dm else ""
    h2 = re.search(r"<h2>(.*?)</h2>", text, re.S)
    h2t = re.sub(r"<[^>]+>", "", h2.group(1)).strip() if h2 else ""
    first_p = re.search(r"<p>(.*?)</p>", text, re.S)
    ptxt = re.sub(r"<[^>]+>", " ", first_p.group(1) if first_p else "")
    ptxt = re.sub(r"\s+", " ", ptxt).strip()

    leader = leader_for_path(rel)
    if rel in BY_PAGE and leader:
        title = f"{leader['name']} OPTCG decklists ({leader['id']}) | One Piece Decklists"
        desc = desc or f"{leader['name']} 50-card One Piece TCG lists. Open tournament and community decks for {leader['id']}."
    elif leader and rel.startswith(leader["dir"] + "/"):
        if title in ("Home", "Untitled", "") or len(title) < 8:
            title = h2t or title or "OPTCG decklist"
        if "OPTCG" not in title and "One Piece Decklists" not in title:
            title = f"{title} | OPTCG"
        if not desc:
            desc = f"{leader['name']} OPTCG decklist. {ptxt}"[:160]
    elif rel == "index.html":
        title = title or "One Piece TCG Decklists (OPTCG) | One Piece Decklists"
        desc = desc or "OPTCG decklists for the Bandai ONE PIECE CARD GAME. Leader pictures and recent 50-card lists."
    elif not title or title in ("Home", "Untitled"):
        title = f"{h2t or 'One Piece TCG'} | One Piece Decklists"
    if not desc:
        desc = (ptxt or title)[:160]
    if len(desc) > 170:
        desc = desc[:157].rstrip() + "…"
    return title, desc


def list_item_pairs(text: str, limit: int = 20) -> list[tuple[str, str]]:
    out = []
    for m in re.finditer(
        r'<a class="item" href="([^"]+)">\s*<div>\s*<div style="font-weight:700">([^<]+)</div>',
        text,
    ):
        out.append((html.unescape(m.group(2).strip()), m.group(1)))
        if len(out) >= limit:
            break
    if out:
        return out
    for m in re.finditer(r'<a class="leader-card-link" href="([^"]+)">\s*<img[^>]*alt="([^"]+)"', text):
        out.append((html.unescape(m.group(2).replace(" leader card", "").strip()), m.group(1)))
        if len(out) >= limit:
            break
    return out


def extra_jsonld(rel: str, title: str, desc: str, url: str, image: str, text: str, by_href: dict) -> str:
    chunks = []
    if rel == "index.html":
        chunks.append(seo.jsonld_script(seo.website_jsonld()))
        items = list_item_pairs(text, 24)
        if items:
            chunks.append(seo.jsonld_script(seo.collection_jsonld(title=title, desc=desc, url=url, items=items)))
        return "".join(chunks)
    if rel == "format.html":
        chunks.append(seo.jsonld_script(seo.faq_jsonld(seo.FORMAT_FAQ)))
        return "".join(chunks)
    if rel == "search.html":
        chunks.append(
            seo.jsonld_script(
                {
                    "@context": "https://schema.org",
                    "@type": "SearchResultsPage",
                    "name": title,
                    "url": url,
                    "isPartOf": {"@id": SITE + "/#website"},
                }
            )
        )
        return "".join(chunks)
    leader = leader_for_path(rel)
    if leader and rel == leader["page"]:
        items = list_item_pairs(text)
        chunks.append(
            seo.jsonld_script(seo.collection_jsonld(title=title, desc=desc, url=url, items=items or [(leader["name"], "/" + leader["page"])]))
        )
        return "".join(chunks)
    if leader and rel.startswith(leader["dir"] + "/"):
        rec = by_href.get(rel) or by_href.get("/" + rel)
        date_s = (rec.get("date") if rec else None) or None
        author = rec.get("player") if rec else None
        chunks.append(
            seo.jsonld_script(
                seo.article_jsonld(
                    title=title,
                    desc=desc,
                    url=url,
                    image=image,
                    date=date_s,
                    author=author,
                    about=leader["name"],
                )
            )
        )
        return "".join(chunks)
    if rel in ("decklists/op17.html", "guides/index.html", "guides/characters/index.html") or rel.startswith("shop/"):
        items = list_item_pairs(text)
        if items:
            chunks.append(seo.jsonld_script(seo.collection_jsonld(title=title, desc=desc, url=url, items=items)))
        return "".join(chunks)
    return ""


def ensure_head(text: str, rel: str, title: str, desc: str, by_href: dict) -> str:
    url = seo.canonical_url(rel)
    image = seo.og_image_for(rel, LEADERS)
    crumbs = seo.parse_crumbs(text)
    if crumbs[-1][1] == "":
        crumbs[-1] = (crumbs[-1][0], url.replace(SITE, "") or "/")
    indexable = "noindex" not in (ROBOTS_META_RE.search(text).group(0).lower() if ROBOTS_META_RE.search(text) else "")
    rec = by_href.get(rel) or by_href.get("/" + rel)
    date_s = (rec.get("date") if rec else "") or ""
    date_meta = ""
    if date_s:
        date_meta = (
            f'  <meta property="article:published_time" content="{html.escape(date_s)}" />\n'
            f'  <meta property="article:modified_time" content="{html.escape(date_s)}" />\n'
        )
    extras = (
        f'  <link rel="canonical" href="{html.escape(url, quote=True)}" />\n'
        + seo.google_head_tags(url, indexable=indexable)
        + seo.social_tags(title, desc, url, image)
        + date_meta
        + seo.breadcrumb_jsonld(crumbs)
        + extra_jsonld(rel, title, desc, url, image, text, by_href)
    )
    text = CANON_RE.sub("", text)
    text = OG_RE.sub("", text)
    text = JSONLD_RE.sub("", text)
    text = ROBOTS_META_RE.sub("", text)
    text = ICON_RE.sub("", text)
    text = THEME_RE.sub("", text)
    text = ADSENSE_RE.sub("", text)
    text = ADSENSE_META_RE.sub("", text)
    text = re.sub(r'(<link rel="stylesheet"[^>]*>)(?=<)', r"\1\n", text)
    if TITLE_RE.search(text):
        text = TITLE_RE.sub(f"<title>{html.escape(title)}</title>", text, count=1)
    else:
        text = text.replace("</head>", f"  <title>{html.escape(title)}</title>\n</head>", 1)
    if DESC_RE.search(text):
        text = DESC_RE.sub(f'<meta name="description" content="{html.escape(desc)}"', text, count=1)
    else:
        text = text.replace("</title>", f'</title>\n  <meta name="description" content="{html.escape(desc)}" />', 1)
    if "</head>" in text:
        text = text.replace("</head>", extras + "</head>", 1)
    elif "</title>" in text:
        text = text.replace("</title>", "</title>\n" + extras.rstrip("\n"), 1)
    return text


def patch_nav_footer(text: str) -> str:
    text = text.replace('href="/#decklists"', 'href="/#recent"')
    text = text.replace('href="#decklists"', 'href="/#recent"')
    text = re.sub(
        r'<a href="/#recent"(?: aria-current="page")?>Decklists</a>',
        '<a href="/#recent">Recent lists</a>',
        text,
    )
    nav = text.split("<nav", 1)[-1].split("</nav>", 1)[0] if "<nav" in text else ""
    if 'href="/guides/"' not in nav:
        text = text.replace(
            '        <a href="/format.html">Format</a>\n        <a href="/shop/">Shop</a>',
            '        <a href="/format.html">Format</a>\n        <a href="/guides/">Guides</a>\n        <a href="/shop/">Shop</a>',
        )
        text = text.replace(
            '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="/shop/">Shop</a>',
            '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="/guides/">Guides</a>\n        <a href="/shop/">Shop</a>',
        )
        text = text.replace(
            '        <a href="/format.html">Format</a>\n        <a href="/shop/" aria-current="page">Shop</a>',
            '        <a href="/format.html">Format</a>\n        <a href="/guides/">Guides</a>\n        <a href="/shop/" aria-current="page">Shop</a>',
        )
    nav = text.split("<nav", 1)[-1].split("</nav>", 1)[0] if "<nav" in text else ""
    if "onepiece-cardgame.com/events" not in nav:
        text = text.replace(
            '        <a href="/format.html">Format</a>\n        <a href="/guides/">Guides</a>',
            '        <a href="/format.html">Format</a>\n        <a href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">Events</a>\n        <a href="/guides/">Guides</a>',
        )
        text = text.replace(
            '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="/guides/">Guides</a>',
            '        <a href="/format.html" aria-current="page">Format</a>\n        <a href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">Events</a>\n        <a href="/guides/">Guides</a>',
        )
    nav = text.split("<nav", 1)[-1].split("</nav>", 1)[0] if "<nav" in text else ""
    if 'href="/search.html"' not in nav:
        text = text.replace(
            '        <a href="https://discord.gg/adZ2WUQ3D"',
            '        <a href="/search.html">Search</a>\n        <a href="https://discord.gg/adZ2WUQ3D"',
            1,
        )
    text = text.replace('<div class="logo">OP</div>', seo.BRAND_LOGO_HTML)
    if '<img class="logo"' not in text:
        text = re.sub(
            r'<div class="logo">[^<]*</div>',
            seo.BRAND_LOGO_HTML,
            text,
            count=1,
        )
    else:
        text = re.sub(r'<img class="logo"[^>]*>', seo.BRAND_LOGO_HTML, text, count=1)
    text = seo.apply_theme_chrome(text)
    text = text.replace(
        '<a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/search.html">Search</a>',
        '<a href="/search.html">Search</a> · <a href="/shop/">Shop</a>',
    )
    footer = text.split("<footer", 1)[-1] if "<footer" in text else ""
    if 'href="/search.html">Search</a>' not in footer:
        text = re.sub(
            r'(<a href="/format\.html">Format</a> · )(?!<a href="/search\.html">)',
            r'\1<a href="/search.html">Search</a> · ',
            text,
            count=1,
        )
        footer = text.split("<footer", 1)[-1] if "<footer" in text else ""
        if 'href="/search.html">Search</a>' not in footer:
            text = re.sub(
                r'(<a href="/shop/">Shop</a> · )(?!<a href="/search\.html">)(<a href="/privacy\.html">Privacy</a>)',
                r'\1<a href="/search.html">Search</a> · \2',
                text,
                count=1,
            )
        footer = text.split("<footer", 1)[-1] if "<footer" in text else ""
        if 'href="/search.html">Search</a>' not in footer and 'href="/guides/">Guides</a>' not in footer:
            text = re.sub(
                r"(<footer>\s*)",
                r"\1" + seo.FOOTER_LINKS + "\n",
                text,
                count=1,
            )
    return text


def ensure_img_alt(text: str) -> str:
    def repl(m: re.Match) -> str:
        attrs = m.group(1)
        if re.search(r"\balt\s*=", attrs, re.I):
            attrs2 = re.sub(r'\balt=""', 'alt="One Piece TCG card"', attrs)
            attrs2 = re.sub(r"\balt=''", "alt='One Piece TCG card'", attrs2)
            return f"<img{attrs2}>"
        src = re.search(r'\bsrc="([^"]+)"', attrs)
        name = Path(src.group(1)).stem.replace("-", " ") if src else "One Piece TCG"
        if "opdl-hero" in (src.group(1) if src else ""):
            name = "One Piece Decklists hero art"
        return f'<img{attrs} alt="{html.escape(name)}" />' if attrs.endswith("/") else f'<img{attrs} alt="{html.escape(name)}">'

    return IMG_RE.sub(repl, text)


def homepage_search_html() -> str:
    return """        <form class="site-search home-search" method="get" action="/search.html" role="search">
          <label class="site-search-label" for="home-q">Search OPTCG decklists</label>
          <div class="site-search-row">
            <input id="home-q" type="search" name="q" placeholder="Leader, player, or event" aria-label="Search OPTCG decklists" />
            <button type="submit">Search</button>
          </div>
        </form>
"""


def format_faq_html() -> str:
    items = []
    for q, a in seo.FORMAT_FAQ:
        items.append(
            f"""          <details>
            <summary>{html.escape(q)}</summary>
            <p>{html.escape(a)}</p>
          </details>"""
        )
    return f"""        <section class="faq" id="faq">
          <div class="section-title">
            <h3>OPTCG format FAQ</h3>
            <div class="muted">Standard rules in short answers</div>
          </div>
{chr(10).join(items)}
        </section>
"""


def patch_file(path: Path, index: dict, by_href: dict) -> tuple[bool, str]:
    rel = path.relative_to(ROOT).as_posix()
    orig = path.read_text()
    text = orig
    leader = leader_for_path(rel)

    if rel == "index.html":
        text = text.replace('alt="OPDL"', 'alt="One Piece Decklists, an OPTCG decklist site"')
        if 'href="/guides/"' not in text.split("home-leaders-intro", 1)[-1][:900]:
            text = text.replace(
                "<p>Pick a picture. Each page has lists for that leader.</p>",
                '<p>Open a hub for lists, analysis, and recent results. Character names live in the <a href="/guides/">guides</a>.</p>',
                1,
            )
        if 'class="wrap wrap-home"' not in text:
            text = text.replace('<div class="wrap">', '<div class="wrap wrap-home">', 1)
        if 'class="site-search home-search"' not in text:
            text = text.replace(
                '        </nav>\n\n        <section class="home-leaders-flow"',
                "        </nav>\n\n" + homepage_search_html() + '\n        <section class="home-leaders-flow"',
                1,
            )
        def splash_repl(m: re.Match) -> str:
            if "home-banner-" in m.group(0) or "fetchpriority=" in m.group(0):
                return m.group(0)
            return m.group(1) + ' width="1400" height="636" fetchpriority="high" decoding="async">'

        text = re.sub(r'(<img class="home-splash-bg"[^>]*?)(?:\s*/?>)', splash_repl, text, count=1)

    if rel == "format.html" and 'class="faq"' not in text:
        text = text.replace("        <!-- RELATED_LINKS -->", format_faq_html() + "        <!-- RELATED_LINKS -->", 1)

    block = ""
    if leader and rel.startswith(leader["dir"] + "/") and rel != leader["page"]:
        block = deck_related_html(rel, index)
    elif leader and rel == leader["page"]:
        block = hub_related_html(leader)
    elif rel.startswith("shop/") and rel != "shop/custom-leaders.html":
        block = shop_related_html(rel)
    elif rel.startswith("guides/characters/") and not rel.endswith("index.html"):
        slug = Path(rel).stem
        block = character_related_extra(slug)
    elif rel.startswith("guides/") and rel not in ("guides/index.html", "guides/characters/index.html"):
        slug = Path(rel).stem
        block = topic_related_extra(slug)
    elif rel == "decklists/op17.html":
        rows = [
            seo.list_row("/tier-list.html", "OP17 tier list", "Aggregated S through D with leader pictures"),
            seo.list_row("/#recent", "Recent lists", "Newest 50-card results on the homepage"),
            seo.list_row("/format.html", "Format and banlist", "Standard constructed rules"),
            seo.list_row("/guides/", "One Piece TCG guides", "Topics and character names"),
            seo.list_row("/shop/", "Shop", "Sleeves, dice, playmats, deck boxes"),
            seo.list_row("/search.html", "Search decklists", "Find a leader, player, or event"),
        ]
        block = seo.related_section("Related pages", "Around the site", rows)
    elif rel == "format.html":
        rows = [
            seo.list_row("/decklists/op17.html", "All leader pages", "Constructed OPTCG hubs"),
            seo.list_row("/guides/constructed.html", "Constructed guide", "What 50-card OPTCG means"),
            seo.list_row("/guides/", "More guides", "Topics and character pages"),
            seo.list_row("/search.html", "Search decklists", "Leader, player, or event"),
        ]
        block = seo.related_section("Related pages", "Lists and guides", rows)

    if block:
        text = insert_related(text, block)

    text = patch_nav_footer(text)
    text = ensure_img_alt(text)
    title, desc = page_title_desc(text, rel)
    text = ensure_head(text, rel, title, desc, by_href)

    if text != orig:
        path.write_text(text)
        return True, "patched"
    return False, "ok"


def href_lookup(index: dict) -> dict:
    out = {}
    for lid, rows in index.items():
        leader = BY_ID.get(lid)
        for row in rows:
            href = row.get("href") or (f"/{leader['dir']}/{row['slug']}.html" if leader and row.get("slug") else "")
            if not href:
                continue
            rec = dict(row)
            rec["_leader"] = leader
            out[href.lstrip("/")] = rec
            out[href] = rec
    return out


def lastmod_for(rel: str, by_href: dict, newest_by_leader: dict) -> str:
    rec = by_href.get(rel) or by_href.get("/" + rel)
    if rec and rec.get("date"):
        return str(rec["date"])[:10]
    leader = leader_for_path(rel)
    if leader and rel == leader["page"] and newest_by_leader.get(leader["id"]):
        return newest_by_leader[leader["id"]]
    if rel == "index.html" and newest_by_leader:
        return max(newest_by_leader.values())
    return date.today().isoformat()


def urlset_xml(entries: list[tuple[str, str]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod in entries:
        lines.append(
            f"  <url><loc>{html.escape(loc)}</loc><lastmod>{html.escape(lastmod)}</lastmod></url>"
        )
    lines.append("</urlset>\n")
    return "\n".join(lines)


def is_core(rel: str) -> bool:
    if rel in CORE_RELS:
        return True
    if rel.startswith("guides/") or rel.startswith("shop/"):
        return True
    if rel in BY_PAGE:
        return True
    return False


def rewrite_sitemap(by_href: dict) -> None:
    newest_by_leader = {}
    for rec in by_href.values():
        lid = (rec.get("_leader") or {}).get("id")
        d = (rec.get("date") or "")[:10]
        if lid and d:
            newest_by_leader[lid] = max(d, newest_by_leader.get(lid, ""))
    core = []
    lists = []
    images: list[tuple[str, str, list[tuple[str, str]]]] = []
    today = date.today().isoformat()
    for p in sorted(public_html()):
        rel = p.relative_to(ROOT).as_posix()
        loc = seo.canonical_url(rel)
        lastmod = lastmod_for(rel, by_href, newest_by_leader)
        row = (loc, lastmod)
        if is_core(rel):
            core.append(row)
        else:
            lists.append(row)
        image = seo.og_image_for(rel, LEADERS)
        if rel == "index.html" or rel in BY_PAGE or rel.startswith("shop/"):
            title = TITLE_RE.search(p.read_text()[:1200])
            label = html.unescape(title.group(1).strip()) if title else Path(rel).stem
            extras = [(image, label)]
            if rel == "index.html":
                extras.append((seo.AVATAR, "One Piece Decklists profile picture"))
                extras.append((seo.LOGO_192, "One Piece Decklists favicon"))
            images.append((loc, lastmod, extras))

    (ROOT / "sitemap-core.xml").write_text(urlset_xml(core))
    (ROOT / "sitemap-lists.xml").write_text(urlset_xml(lists))
    img_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for loc, lastmod, extras in images:
        img_lines.append("  <url>")
        img_lines.append(f"    <loc>{html.escape(loc)}</loc>")
        img_lines.append(f"    <lastmod>{html.escape(lastmod)}</lastmod>")
        for image, label in extras:
            img_lines.append("    <image:image>")
            img_lines.append(f"      <image:loc>{html.escape(image)}</image:loc>")
            img_lines.append(f"      <image:title>{html.escape(label)}</image:title>")
            img_lines.append("    </image:image>")
        img_lines.append("  </url>")
    img_lines.append("</urlset>\n")
    (ROOT / "sitemap-images.xml").write_text("\n".join(img_lines))
    index_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>{SITE}/sitemap-core.xml</loc><lastmod>{today}</lastmod></sitemap>
  <sitemap><loc>{SITE}/sitemap-lists.xml</loc><lastmod>{today}</lastmod></sitemap>
  <sitemap><loc>{SITE}/sitemap-images.xml</loc><lastmod>{today}</lastmod></sitemap>
</sitemapindex>
"""
    (ROOT / "sitemap.xml").write_text(index_xml)
    (ROOT / "robots.txt").write_text(seo.ROBOTS_TXT)
    (ROOT / "ads.txt").write_text(seo.ADS_TXT)
    log("sitemap core", len(core), "lists", len(lists), "images", len(images))


def write_logos() -> None:
    hero_path = ROOT / "img/opdl-hero.jpg"
    needed = [
        ROOT / "img/opdl-avatar.png",
        ROOT / "img/opdl-logo-48.png",
        ROOT / "img/opdl-logo-192.png",
        ROOT / "img/opdl-logo-512.png",
        ROOT / "favicon.ico",
    ]
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        if all(p.exists() for p in needed):
            log("avatar kept, pillow missing")
            return
        raise

    hero = Image.open(hero_path).convert("RGB")
    left, right = 20, 970
    crop = hero.crop((left, 0, right, hero.size[1]))
    fill = crop.getpixel((30, 12))
    side = crop.size[0]
    square = Image.new("RGB", (side, side), fill)
    square.paste(crop, (0, (side - crop.size[1]) // 2))

    def sized(px: int) -> Image.Image:
        out = square.resize((px, px), Image.Resampling.LANCZOS)
        if px <= 192:
            out = out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=2))
        return out

    avatar = sized(512)
    avatar.save(ROOT / "img/opdl-avatar.png", optimize=True)
    avatar.save(ROOT / "img/opdl-logo-512.png", optimize=True)
    sized(192).save(ROOT / "img/opdl-logo-192.png", optimize=True)
    sized(48).save(ROOT / "img/opdl-logo-48.png", optimize=True)
    sized(48).save(ROOT / "favicon.ico", format="ICO", sizes=[(48, 48), (32, 32), (16, 16)])
    log("avatar written")


def write_discovery_files() -> None:
    (ROOT / "site.webmanifest").write_text(
        json.dumps(
            {
                "name": "One Piece Decklists",
                "short_name": "OPDL",
                "description": "OPTCG decklists for the Bandai ONE PIECE CARD GAME.",
                "start_url": "/",
                "scope": "/",
                "display": "browser",
                "background_color": "#f7f5f3",
                "theme_color": "#b71c1c",
                "icons": [
                    {"src": "/img/opdl-logo-48.png", "sizes": "48x48", "type": "image/png"},
                    {"src": "/img/opdl-logo-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "/img/opdl-avatar.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                ],
            },
            indent=2,
        )
        + "\n"
    )
    (ROOT / "ads.txt").write_text(seo.ADS_TXT)
    (ROOT / "opensearch.xml").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
  <ShortName>OPDL</ShortName>
  <LongName>One Piece Decklists</LongName>
  <Description>Search OPTCG decklists on One Piece Decklists</Description>
  <InputEncoding>UTF-8</InputEncoding>
  <Image width="48" height="48" type="image/png">{seo.LOGO_48}</Image>
  <Url type="text/html" method="get" template="{SITE}/search.html?q={{searchTerms}}"/>
</OpenSearchDescription>
"""
    )


def search_catalog(index: dict) -> tuple[list[dict], list[dict]]:
    pages = []
    for L in LEADERS:
        pages.append(
            {
                "kind": "leader",
                "title": L["name"],
                "note": f"{L['id']} constructed hub",
                "href": "/" + L["page"],
                "q": f"{L['name']} {L['id']} {L['key']} decklist optcg",
            }
        )
    pages.append({"kind": "page", "title": "OP17 tier list", "note": "Aggregated S-A-B-C-D with leader pictures", "href": "/tier-list.html", "q": "tier list meta op17 mihawk rocks sabo"})
    pages.append({"kind": "page", "title": "Format and banlist", "note": "Standard OPTCG rules", "href": "/format.html", "q": "format banlist rotation pudding"})
    pages.append({"kind": "page", "title": "All leader pages", "note": "Every constructed hub", "href": "/decklists/op17.html", "q": "leaders op17 decklists"})
    pages.append({"kind": "page", "title": "Guides", "note": "Topics and characters", "href": "/guides/", "q": "guides one piece tcg optcg"})
    pages.append({"kind": "page", "title": "Shop", "note": "Sleeves, dice, playmats, deck boxes", "href": "/shop/", "q": "shop sleeves dice playmat deck box"})
    for href, label in seo.SHOP_PAGES:
        if href == "/shop/":
            continue
        pages.append({"kind": "shop", "title": label, "note": "Amazon shop", "href": href, "q": f"{label} shop amazon optcg"})
    for topic in seopages.TOPICS:
        pages.append(
            {
                "kind": "guide",
                "title": topic["h2"],
                "note": "Topic guide",
                "href": f"/guides/{topic['slug']}.html",
                "q": f"{topic['h2']} {topic['desc']}",
            }
        )
    for name, slug, blurb, _related in seopages.CHARACTERS:
        pages.append(
            {
                "kind": "character",
                "title": name,
                "note": "Character guide",
                "href": f"/guides/characters/{slug}.html",
                "q": f"{name} {blurb}",
            }
        )
    lists = []
    seen_href = set()
    for lid, rows in index.items():
        leader = BY_ID.get(lid)
        lname = leader["name"] if leader else lid
        for row in rows:
            href = row.get("href") or (f"/{leader['dir']}/{row['slug']}.html" if leader and row.get("slug") else "")
            if not href or href in seen_href:
                continue
            seen_href.add(href)
            player = row.get("player") or "List"
            event = row.get("tournament") or ""
            date_s = row.get("date") or ""
            lists.append(
                {
                    "title": f"{player} - {lname}",
                    "note": " · ".join(x for x in (event, date_s) if x),
                    "href": href,
                    "q": f"{player} {lname} {event} {lid}",
                    "date": date_s,
                }
            )
    comm_path = ROOT / "data/community-decks.json"
    if comm_path.exists():
        community = json.loads(comm_path.read_text())
        for lid, rows in community.items():
            leader = BY_ID.get(lid)
            lname = leader["name"] if leader else lid
            for row in rows:
                href = row.get("href") or ""
                if not href or href in seen_href:
                    continue
                seen_href.add(href)
                title = row.get("title") or row.get("slug") or "List"
                note = row.get("subtitle") or ""
                date_s = row.get("date") or ""
                lists.append(
                    {
                        "title": title,
                        "note": note,
                        "href": href,
                        "q": f"{title} {lname} {note} {lid}",
                        "date": date_s,
                    }
                )
    lists.sort(key=lambda r: r.get("date") or "", reverse=True)
    return pages, lists


def write_search_page(index: dict) -> None:
    pages, lists = search_catalog(index)
    groups = [
        ("Leaders", [p for p in pages if p["kind"] == "leader"]),
        ("Pages", [p for p in pages if p["kind"] in ("page", "shop")]),
        ("Guides", [p for p in pages if p["kind"] == "guide"]),
        ("Characters", [p for p in pages if p["kind"] == "character"]),
        ("Recent lists", lists[:60]),
    ]
    sections = []
    for heading, rows in groups:
        items = []
        for row in rows:
            items.append(
                f"""            <li data-q="{html.escape(row.get('q') or row['title'], quote=True)}">
              <a class="item" href="{html.escape(row['href'], quote=True)}">
                <div>
                  <div style="font-weight:700">{html.escape(row['title'])}</div>
                  <div class="muted" style="font-size:13px">{html.escape(row.get('note') or '')}</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>"""
            )
        sections.append(
            f"""        <section class="search-group" data-search-group>
          <div class="section-title">
            <h3>{html.escape(heading)}</h3>
            <div class="muted">{len(rows)}</div>
          </div>
          <ul class="list">
{chr(10).join(items)}
          </ul>
        </section>"""
        )
    compact = [
        {"t": r["title"], "n": r.get("note") or "", "h": r["href"], "q": r["q"]}
        for r in lists
    ]
    blob = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    body = f"""        <div class="crumb"><a href="/">Home</a> / Search</div>
        <h2>Search OPTCG decklists</h2>
        <p>Find a leader, player, character, or event. Google sitelinks search and the site header both land here.</p>
        <form class="site-search" method="get" action="/search.html" role="search">
          <label class="site-search-label" for="q">Search</label>
          <div class="site-search-row">
            <input id="q" type="search" name="q" placeholder="Rocks, Mihawk, ChinoizeCup, player name" aria-label="Search OPTCG decklists" />
            <button type="submit">Search</button>
          </div>
        </form>
        <p class="muted" id="search-status" hidden></p>
        <section class="search-group" data-search-extra hidden>
          <div class="section-title">
            <h3>Matching lists</h3>
            <div class="muted" data-extra-count></div>
          </div>
          <ul class="list" data-extra-results></ul>
        </section>
{chr(10).join(sections)}
        <script type="application/json" id="search-lists">{blob}</script>
"""
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Search OPTCG decklists | One Piece Decklists</title>
  <meta name="description" content="Search One Piece TCG decklists, leaders, characters, and events on One Piece Decklists." />
{seo.THEME_BOOT_SCRIPT}  <link rel="stylesheet" href="/css/site.css?v={seo.CSS_VER}" />
{seo.ADSENSE_HEAD.rstrip()}
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
{seo.THEME_TOGGLE_HTML}{seo.primary_nav_html(current="search")}
    </header>
    <main class="single">
      <div class="card hero">
{body}
      </div>
    </main>
    <footer>
      © <span id="year"></span> One Piece Decklists - Fan site for the Bandai ONE PIECE CARD GAME (OPTCG). Not affiliated with Bandai.
{seo.FOOTER_LINKS}
    </footer>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script src="/js/site.js?v={seo.JS_VER}"></script>
</body>
</html>
"""
    (ROOT / "search.html").write_text(page)
    log("search page", len(pages), "catalog", len(lists), "lists")


def audit(paths: list[Path]) -> None:
    missing_title = missing_desc = missing_canon = missing_alt = weak_title = 0
    missing_robots = missing_icon = 0
    for p in paths:
        text = p.read_text()
        tm = TITLE_RE.search(text)
        title = tm.group(1).strip() if tm else ""
        if not title or title in ("Home", "Untitled"):
            missing_title += 1
        elif len(title) < 12:
            weak_title += 1
        if not DESC_RE.search(text):
            missing_desc += 1
        if not CANON_RE.search(text):
            missing_canon += 1
        if not ROBOTS_META_RE.search(text):
            missing_robots += 1
        if 'rel="icon"' not in text:
            missing_icon += 1
        for m in IMG_RE.finditer(text):
            attrs = m.group(1)
            if not re.search(r"\balt\s*=", attrs, re.I) or re.search(r'\balt=""', attrs):
                missing_alt += 1
                break
    log(
        "audit pages",
        len(paths),
        "no/weak title",
        missing_title,
        "short title",
        weak_title,
        "no desc",
        missing_desc,
        "no canonical",
        missing_canon,
        "no robots",
        missing_robots,
        "no icon",
        missing_icon,
        "img missing alt",
        missing_alt,
    )


def main() -> None:
    index = load_index()
    by_href = href_lookup(index)
    write_logos()
    write_discovery_files()
    write_search_page(index)
    paths = public_html()
    log("scan", len(paths), "html pages")
    audit(paths)
    changed = 0
    for p in paths:
        ok, _why = patch_file(p, index, by_href)
        if ok:
            changed += 1
    log("patched", changed)
    rewrite_sitemap(by_href)
    audit(public_html())
    log("google search seo done")


if __name__ == "__main__":
    main()
