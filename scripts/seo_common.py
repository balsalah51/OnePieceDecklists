#!/usr/bin/env python3
"""Shared SEO chrome: canonical/OG tags, related-page links, nav, footer."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
DEFAULT_OG = f"{SITE}/img/opdl-hero.jpg"
AVATAR = f"{SITE}/img/opdl-avatar.png"
LOGO_SVG = f"{SITE}/img/opdl-logo.svg"
LOGO_48 = f"{SITE}/img/opdl-logo-48.png"
LOGO_192 = f"{SITE}/img/opdl-logo-192.png"
LOGO_512 = f"{SITE}/img/opdl-logo-512.png"
CSS_VER = "home-pro4"
JS_VER = "home-meta"
BRAND_LOGO_HTML = (
    '<img class="logo" src="/img/opdl-avatar.png" width="56" height="56" alt="One Piece Decklists" />'
)
THEME_BOOT_SCRIPT = (
    '  <script id="opdl-theme-boot">\n'
    "    (function(){try{var m=document.cookie.match(/(?:^|; )opdl-theme=([^;]*)/);"
    "var t=m&&decodeURIComponent(m[1]);"
    'if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);'
    "}catch(e){}})();\n"
    "  </script>\n"
)
THEME_TOGGLE_HTML = (
    '      <div class="theme-toggle" role="group" aria-label="Color theme">\n'
    '        <button type="button" class="theme-toggle-btn" data-theme-set="light" aria-pressed="true">Light</button>\n'
    '        <button type="button" class="theme-toggle-btn" data-theme-set="dark" aria-pressed="false">Dark</button>\n'
    "      </div>\n"
)

ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /shop/custom-leaders.html
Disallow: /ballkeep/
Disallow: /scripts/
Disallow: /data/
Disallow: /discord-bot/
Disallow: /.github/

User-agent: Googlebot
Allow: /
Disallow: /shop/custom-leaders.html
Disallow: /ballkeep/
Disallow: /scripts/
Disallow: /data/
Disallow: /discord-bot/
Disallow: /.github/

User-agent: Googlebot-Image
Allow: /favicon.ico
Allow: /img/
Allow: /

User-agent: Mediapartners-Google
Allow: /

Sitemap: https://onepiecedecklists.com/sitemap.xml
"""
ADSENSE_CLIENT = "ca-pub-1074015774205047"
ADSENSE_META = f'  <meta name="google-adsense-account" content="{ADSENSE_CLIENT}" />\n'
ADSENSE_SCRIPT = (
    f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" '
    'crossorigin="anonymous"></script>\n'
)
ADSENSE_HEAD = ADSENSE_META + ADSENSE_SCRIPT
ADS_TXT = "google.com, pub-1074015774205047, DIRECT, f08c47fec0942fa0\n"

# Leader id -> nearby constructed pages (same color family, same set, or same character).
RELATED_LEADERS: dict[str, list[str]] = {
    "OP17-001": ["OP16-001", "OP13-002", "OP17-039"],
    "OP17-020": ["OP14-020", "OP13-001", "OP17-079"],
    "OP17-039": ["OP17-001", "OP17-058", "OP17-099"],
    "OP17-058": ["OP16-079", "OP17-039", "OP17-099"],
    "OP17-079": ["OP13-001", "OP16-022", "OP11-040"],
    "OP17-099": ["OP11-062", "OP08-058", "OP17-058"],
    "OP13-001": ["OP17-079", "OP16-022", "OP11-040"],
    "OP11-041": ["OP17-020", "OP13-001", "OP17-079"],
    "OP14-020": ["OP17-020", "OP13-001", "OP12-061"],
    "OP16-001": ["OP13-002", "OP17-001", "OP17-079"],
    "OP13-002": ["OP16-001", "OP17-001", "OP15-002"],
    "OP13-079": ["OP17-079", "OP16-080", "OP17-039"],
    "OP15-058": ["OP11-062", "OP16-060", "OP17-058"],
    "OP11-062": ["OP08-058", "OP17-099", "OP15-058"],
    "OP16-022": ["OP13-001", "OP17-079", "OP11-040"],
    "OP16-080": ["OP13-079", "OP16-041", "OP17-039"],
    "OP12-061": ["OP14-060", "OP14-020", "OP08-058"],
    "OP15-002": ["OP13-001", "OP13-002", "OP16-022"],
    "OP16-079": ["OP17-058", "OP17-079", "OP13-079"],
    "OP11-001": ["OP16-060", "OP17-001", "OP16-080"],
    "OP14-060": ["OP12-061", "OP08-058", "OP17-099"],
    "OP16-041": ["OP16-022", "OP16-080", "OP15-002"],
    "OP16-060": ["OP11-001", "OP15-058", "OP11-062"],
    "OP11-040": ["OP13-001", "OP16-022", "OP17-079"],
    "OP08-058": ["OP11-062", "OP17-099", "OP12-061"],
    "OP13-004": ["OP13-001", "OP17-079", "ST13-001"],
    "OP09-062": ["OP08-058", "OP17-099", "OP14-080"],
    "OP14-080": ["OP09-062", "OP11-041", "OP08-058"],
    "OP14-041": ["OP11-041", "OP15-002", "OP16-022"],
    "OP12-081": ["OP14-041", "OP17-079", "OP13-004"],
    "OP09-001": ["OP17-020", "OP14-020", "OP17-001"],
    "OP05-098": ["OP15-058", "OP17-099", "OP11-062"],
    "ST10-002": ["OP13-001", "OP17-079", "OP16-022"],
    "OP09-061": ["OP17-079", "OP16-022", "OP13-001"],
    "ST13-003": ["OP17-079", "OP13-001", "ST13-001"],
    "OP12-040": ["OP16-060", "OP16-080", "OP17-039"],
    "OP05-002": ["OP13-004", "OP17-079", "EB04-001"],
    "EB04-001": ["OP05-002", "OP13-004", "OP11-041"],
    "OP10-099": ["OP17-099", "OP05-098", "OP11-062"],
    "OP07-059": ["OP17-058", "OP14-060", "OP11-062"],
    "ST13-001": ["OP13-004", "OP13-002", "OP15-002"],
    "OP05-041": ["OP16-060", "OP12-040", "OP16-080"],
    "OP05-060": ["OP17-058", "OP09-061", "ST10-002"],
    "OP07-079": ["OP13-079", "OP17-079", "OP16-080"],
    "OP10-022": ["OP12-061", "OP14-020", "OP17-020"],
    "OP06-022": ["OP16-079", "OP17-058", "OP14-020"],
    "ST14-001": ["OP17-079", "OP13-001", "OP16-022"],
    "EB02-010": ["OP17-020", "OP13-001", "OP17-079"],
    "OP14-040": ["OP17-039", "OP16-041", "OP12-041"],
    "OP12-041": ["OP14-040", "OP11-040", "OP17-079"],
    "ST30-001": ["OP16-001", "OP13-002", "OP17-001"],
}

LEADER_GUIDE: dict[str, str] = {
    "edward-newgate": "edward-newgate",
    "shanks": "shanks",
    "rocks-d-xebec": "rocks-d-xebec",
    "kaido": "kaido",
    "monkey-d-luffy": "monkey-d-luffy",
    "charlotte-linlin": "charlotte-linlin",
    "rg-luffy": "monkey-d-luffy",
    "nami": "nami",
    "mihawk": "dracule-mihawk",
    "portgas-d-ace": "portgas-d-ace",
    "op13-ace": "portgas-d-ace",
    "imu": "imu",
    "enel": "enel",
    "charlotte-katakuri": "charlotte-katakuri",
    "gb-luffy": "monkey-d-luffy",
    "blackbeard": "marshall-d-teach",
    "rosinante": "rosinante",
    "lucy": "lucy",
    "yamato": "yamato",
    "koby": "koby",
    "doffy": "donquixote-doflamingo",
    "buggy": "buggy",
    "sengoku": "sengoku",
    "up-luffy": "up-luffy",
    "charlotte-pudding": "charlotte-pudding",
    "sabo": "sabo",
    "st13-sabo": "sabo",
    "nico-robin": "nico-robin",
    "gecko-moria": "gecko-moria",
    "boa-hancock": "boa-hancock",
    "koala": "koala",
    "op09-shanks": "shanks",
    "op05-enel": "enel",
    "st10-luffy": "monkey-d-luffy",
    "op09-luffy": "monkey-d-luffy",
    "st13-luffy": "monkey-d-luffy",
    "kuzan": "kuzan",
    "belo-betty": "belo-betty",
    "jewelry-bonney": "jewelry-bonney",
    "eustass-kid": "eustass-kid",
    "sakazuki": "sakazuki",
    "op05-luffy": "monkey-d-luffy",
    "rob-lucci": "rob-lucci",
    "trafalgar-law": "trafalgar-law",
    "op06-yamato": "yamato",
    "st14-luffy": "monkey-d-luffy",
    "eb02-luffy": "monkey-d-luffy",
    "jinbe": "jinbe",
    "sanji": "sanji",
}

SHOP_PAGES = [
    ("/shop/", "Shop home"),
    ("/shop/sleeves.html", "Sleeves"),
    ("/shop/dice.html", "Dice"),
    ("/shop/playmats.html", "Playmats"),
    ("/shop/deck-boxes.html", "Deck boxes"),
    ("/shop/extras.html", "Table extras"),
]


def canonical_url(rel: str) -> str:
    rel = rel.lstrip("/")
    if rel in ("index.html", ""):
        return f"{SITE}/"
    if rel.endswith("/index.html"):
        return f"{SITE}/{rel[: -len('index.html')]}"
    return f"{SITE}/{rel}"


def leader_by_id(leaders: list[dict], lid: str) -> dict | None:
    return next((L for L in leaders if L["id"] == lid), None)


def leader_by_key(leaders: list[dict], key: str) -> dict | None:
    return next((L for L in leaders if L["key"] == key), None)


def og_image_for(rel: str, leaders: list[dict]) -> str:
    rel = rel.lstrip("/")
    for L in leaders:
        if rel == L["page"] or rel.startswith(L["dir"] + "/"):
            cid = L["id"]
            set_code = cid.split("-")[0]
            return f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/{set_code}/{cid}_EN.webp"
    if rel.startswith("shop/"):
        return f"{SITE}/img/shop/sleeve-jet.jpg"
    return DEFAULT_OG


def social_tags(title: str, desc: str, url: str, image: str) -> str:
    t = html.escape(title)
    d = html.escape(desc[:300])
    u = html.escape(url, quote=True)
    img = html.escape(image, quote=True)
    alt = html.escape(title[:120])
    return (
        f'  <meta property="og:site_name" content="One Piece Decklists" />\n'
        f'  <meta property="og:locale" content="en_US" />\n'
        f'  <meta property="og:type" content="website" />\n'
        f'  <meta property="og:title" content="{t}" />\n'
        f'  <meta property="og:description" content="{d}" />\n'
        f'  <meta property="og:url" content="{u}" />\n'
        f'  <meta property="og:image" content="{img}" />\n'
        f'  <meta property="og:image:alt" content="{alt}" />\n'
        f'  <meta name="twitter:card" content="summary_large_image" />\n'
        f'  <meta name="twitter:title" content="{t}" />\n'
        f'  <meta name="twitter:description" content="{d}" />\n'
        f'  <meta name="twitter:image" content="{img}" />\n'
        f'  <meta name="twitter:image:alt" content="{alt}" />\n'
    )


def jsonld_script(payload: dict) -> str:
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f'  <script type="application/ld+json">{blob}</script>\n'


def google_head_tags(url: str, *, indexable: bool = True) -> str:
    robots = (
        "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
        if indexable
        else "noindex, nofollow"
    )
    u = html.escape(url, quote=True)
    return (
        f'  <meta name="robots" content="{robots}" />\n'
        f'  <meta name="googlebot" content="{robots}" />\n'
        f'  <meta name="theme-color" content="#b71c1c" />\n'
        f'  <link rel="icon" href="{html.escape(LOGO_192, quote=True)}" type="image/png" sizes="192x192" />\n'
        f'  <link rel="apple-touch-icon" href="{html.escape(LOGO_192, quote=True)}" sizes="192x192" />\n'
        f'  <link rel="manifest" href="/site.webmanifest" />\n'
        f'  <link rel="search" type="application/opensearchdescription+xml" title="One Piece Decklists" href="/opensearch.xml" />\n'
        f'  <link rel="alternate" hreflang="en" href="{u}" />\n'
        f'  <link rel="alternate" hreflang="x-default" href="{u}" />\n'
        f"{ADSENSE_HEAD}"
    )


def organization_node() -> dict:
    return {
        "@type": "Organization",
        "@id": SITE + "/#organization",
        "name": "One Piece Decklists",
        "alternateName": ["OPDL", "One Piece TCG Decklists"],
        "url": SITE + "/",
        "logo": {
            "@type": "ImageObject",
            "url": AVATAR,
            "width": 512,
            "height": 512,
        },
        "image": AVATAR,
        "sameAs": ["https://discord.gg/adZ2WUQ3D"],
    }


def website_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            {
                "@type": "WebSite",
                "@id": SITE + "/#website",
                "name": "One Piece Decklists",
                "alternateName": ["OPDL", "One Piece TCG Decklists"],
                "url": SITE + "/",
                "description": "OPTCG decklists for the Bandai ONE PIECE CARD GAME.",
                "inLanguage": "en",
                "publisher": {"@id": SITE + "/#organization"},
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": SITE + "/search.html?q={search_term_string}",
                    },
                    "query-input": "required name=search_term_string",
                },
            },
        ],
    }


def article_jsonld(
    *,
    title: str,
    desc: str,
    url: str,
    image: str,
    date: str | None,
    author: str | None,
    about: str | None,
) -> dict:
    payload = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "description": desc[:300],
        "mainEntityOfPage": url,
        "image": image,
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "publisher": {
            "@type": "Organization",
            "name": "One Piece Decklists",
            "logo": {"@type": "ImageObject", "url": AVATAR},
        },
    }
    if date:
        payload["datePublished"] = date
        payload["dateModified"] = date
    if author:
        payload["author"] = {"@type": "Person", "name": author}
    else:
        payload["author"] = {"@type": "Organization", "name": "One Piece Decklists"}
    if about:
        payload["about"] = {"@type": "Thing", "name": about}
    return payload


def collection_jsonld(*, title: str, desc: str, url: str, items: list[tuple[str, str]]) -> dict:
    elements = []
    for i, (name, href) in enumerate(items[:20], start=1):
        item_url = href if href.startswith("http") else SITE + (href if href.startswith("/") else "/" + href)
        elements.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "url": item_url,
            }
        )
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc[:300],
        "url": url,
        "inLanguage": "en",
        "isPartOf": {"@id": SITE + "/#website"},
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": elements,
            "numberOfItems": len(elements),
        },
    }


def faq_jsonld(pairs: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in pairs
        ],
    }


def breadcrumb_jsonld(crumbs: list[tuple[str, str]]) -> str:
    items = []
    for i, (name, href) in enumerate(crumbs, start=1):
        url = href if href.startswith("http") else SITE + (href if href.startswith("/") else "/" + href)
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": url,
            }
        )
    payload = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f'  <script type="application/ld+json">{blob}</script>\n'


def list_row(href: str, title: str, note: str) -> str:
    return f"""            <li>
              <a class="item" href="{html.escape(href, quote=True)}">
                <div>
                  <div style="font-weight:700">{html.escape(title)}</div>
                  <div class="muted" style="font-size:13px">{html.escape(note)}</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>"""


def crew_siblings(slug: str, characters: list, limit: int = 8) -> list[tuple[str, str]]:
    """Return (name, slug) for other character pages that share a constructed leader."""
    groups: dict[int, list[tuple[str, str]]] = {}
    slug_leaders: dict[str, list[int]] = {}
    for name, cslug, _blurb, related in characters:
        slug_leaders[cslug] = related
        if related:
            groups.setdefault(related[0], []).append((name, cslug))
    mine = slug_leaders.get(slug) or []
    seen = {slug}
    out: list[tuple[str, str]] = []
    for idx in mine:
        for name, cslug in groups.get(idx, []):
            if cslug in seen:
                continue
            seen.add(cslug)
            out.append((name, cslug))
            if len(out) >= limit:
                return out
    return out


def related_section(heading: str, note: str, rows: list[str]) -> str:
    if not rows:
        return ""
    return f"""        <!-- RELATED_LINKS -->
        <section class="related-links" style="margin-top:22px">
          <div class="section-title">
            <h3>{html.escape(heading)}</h3>
            <div class="muted">{html.escape(note)}</div>
          </div>
          <ul class="list">
{chr(10).join(rows)}
          </ul>
        </section>
        <!-- /RELATED_LINKS -->
"""


RELATED_BLOCK_RE = re.compile(
    r"\s*<!-- RELATED_LINKS -->.*?<!-- /RELATED_LINKS -->\n?",
    re.S,
)


def strip_related(text: str) -> str:
    return RELATED_BLOCK_RE.sub("\n", text)


def parse_crumbs(text: str) -> list[tuple[str, str]]:
    m = re.search(r'<div class="crumb">(.*?)</div>', text, re.S)
    if not m:
        return [("Home", "/")]
    inner = m.group(1)
    crumbs: list[tuple[str, str]] = []
    for am in re.finditer(r'<a href="([^"]+)">([^<]+)</a>', inner):
        crumbs.append((html.unescape(am.group(2).strip()), am.group(1)))
    tail = re.sub(r"<a[^>]*>.*?</a>", "", inner)
    tail = re.sub(r"\s*/\s*", " ", tail)
    tail = re.sub(r"<[^>]+>", "", tail).strip(" \n/")
    if tail:
        crumbs.append((html.unescape(tail), ""))
    if not crumbs:
        crumbs = [("Home", "/")]
    return crumbs


FOOTER_LINKS = (
    '      <a href="/tier-list.html">Tier List</a> · '
    '<a href="/guides/">Guides</a> · '
    '<a href="/decklists/op17.html">Leaders</a> · '
    '<a href="/format.html">Format</a> · '
    '<a href="/search.html">Search</a> · '
    '<a href="/shop/">Shop</a> · '
    '<a href="/privacy.html">Privacy</a>'
)


def apply_theme_chrome(text: str) -> str:
    """Add the theme boot script and header toggle. Safe to re-run."""
    text = re.sub(r'href="/css/site\.css(?:\?[^"]*)?"', f'href="/css/site.css?v={CSS_VER}"', text)
    text = re.sub(r'src="/js/site\.js(?:\?[^"]*)?"', f'src="/js/site.js?v={JS_VER}"', text)
    if 'id="opdl-theme-boot"' not in text:
        text = re.sub(
            r'(<link rel="stylesheet" href="/css/site\.css[^"]*"\s*/>)',
            THEME_BOOT_SCRIPT + r"\1",
            text,
            count=1,
        )
    if "data-theme-set" not in text:
        text = re.sub(
            r'(</a>\s*\n)(\s*<nav aria-label="Primary">)',
            r"\1" + THEME_TOGGLE_HTML + r"\2",
            text,
            count=1,
        )
    return text


def primary_nav_html(*, current: str | None = None, home: bool = False) -> str:
    recent = "#recent" if home else "/recent.html"
    leaders = "#leaders" if home else "/decklists/op17.html"
    items = [
        ("/tier-list.html", "Tier List", "tier"),
        (recent, "Recent lists", "recent"),
        (leaders, "Leaders", "leaders"),
        ("/format.html", "Format", "format"),
        ("https://en.onepiece-cardgame.com/events/", "Events", "events"),
        ("/guides/", "Guides", "guides"),
        ("/shop/", "Shop", "shop"),
        ("/search.html", "Search", "search"),
        ("https://discord.gg/adZ2WUQ3D", "Discord", "discord"),
    ]
    lines = ['      <nav aria-label="Primary">']
    for href, label, key in items:
        cur = ' aria-current="page"' if key == current else ""
        extra = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        lines.append(f'        <a href="{href}"{cur}{extra}>{label}</a>')
    lines.append("      </nav>")
    return "\n".join(lines)

FORMAT_FAQ = [
    (
        "What format are One Piece Decklists lists?",
        "Lists on One Piece Decklists are 50-card Standard constructed OPTCG decks plus a leader for the Bandai ONE PIECE CARD GAME.",
    ),
    (
        "What card is banned in OPTCG constructed?",
        "Blue Charlotte Pudding OP06-047 is banned in constructed, including parallels, effective 1 April 2026. Other Pudding prints stay legal.",
    ),
    (
        "When does OP17 English release?",
        "OP17 English is dated 28 August 2026. English events before that date still use the OP16 Standard pool. OP17 lists on this site come from Japan, Germany, and online cups.",
    ),
    (
        "Did Block 1 rotate out of Standard?",
        "Yes. Standard no longer uses Block 1 (OP-01 Romance Dawn through OP-04 Kingdoms of Intrigue) as of 1 April 2026. Manga rares stay legal as Block X.",
    ),
    (
        "Where do the decklists come from?",
        "Tournament tables come from Limitless Play events. Community rows are public YouTube, web, and social lists with a full 50-card ID list.",
    ),
]
