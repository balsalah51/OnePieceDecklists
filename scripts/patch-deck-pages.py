#!/usr/bin/env python3
"""Refresh published decklist pages: SEO, one image per card, exports, TCGplayer.

Re-runnable. Skips HTML redirect stubs. Does not invent prices.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
PARTNER_NEEDLE = "partner.tcgplayer.com/c/7670706/1780961/21018"

sys.path.insert(0, str(ROOT / "scripts"))
import deck_seo  # noqa: E402
import tcgplayer_links  # noqa: E402


def load_mod(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = load_mod("genlists", "scripts/generate-tournament-lists.py")
seo = load_mod("seocommon", "scripts/seo_common.py")
fm = load_mod("formatmeta", "scripts/format_meta.py")

H2_RE = re.compile(r"<h2>(.*?)</h2>", re.S)
P_RE = re.compile(r"<h2>.*?</h2>\s*<p>(.*?)</p>", re.S)
CRUMB_RE = re.compile(r'<div class="crumb">(.*?)</div>', re.S)
LINE_RE = re.compile(
    r'<li class="text-line"[^>]*>.*?<span class="qty">(\d+)x</span>\s*'
    r'<span class="card-title">(.*?)</span>\s*'
    r'<span class="muted card-id">([^<]+)</span>',
    re.S,
)
LEADER_LINE_RE = re.compile(
    r'<div class="text-deck-leader">.*?</div>',
    re.S,
)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
PLACE_RE = re.compile(r"\b(\d+(?:st|nd|rd|th))\b", re.I)
OG_RE = re.compile(
    r"\s*<meta (?:property|name)=\"(?:og:|twitter:|article:)[^\"]+\" content=\".*?\" />",
    re.S,
)
JSONLD_RE = re.compile(r"\s*<script type=\"application/ld\+json\">.*?</script>", re.S)
POP_RE = re.compile(r'<img class="card-pop"[^>]*>')
CARD_IMG_RE = re.compile(r'(<article class="card-entry">\s*)<img([^>]*)>')
STATS_RE = re.compile(r"<!-- DECK_STATS -->.*?<!-- /DECK_STATS -->", re.S)
TITLE_BTN_RE = re.compile(r"(Copy to OP TCG SIM|Copy for sim)</button>")


def leader_names() -> dict[str, str]:
    out = {}
    for leader in gen.LEADERS:
        out[leader["key"]] = fm.public_name(leader)
    return out


def load_entries() -> dict[str, dict]:
    names = leader_names()
    by_id = {leader["id"]: leader for leader in gen.LEADERS}
    found: dict[str, dict] = {}
    for path in (ROOT / "data/tournament-decks.json", ROOT / "data/community-decks.json"):
        if not path.exists():
            continue
        raw = json.loads(path.read_text())
        for lid, rows in raw.items():
            leader = by_id.get(lid)
            key = leader["key"] if leader else ""
            label = names.get(key) or (leader["name"] if leader else "")
            for row in rows:
                href = row.get("href") or ""
                if not href:
                    continue
                item = dict(row)
                item["leader_id"] = lid
                item["leader_key"] = key
                item["leader_name"] = label
                found[href] = item
    return found


def is_stub(text: str) -> bool:
    return "Moved" in text[:400] and 'http-equiv="refresh"' in text[:800]


def parse_html_meta(text: str, key: str, names: dict[str, str]) -> dict:
    leader = names.get(key, key.replace("-", " ").title())
    crumb = CRUMB_RE.search(text)
    if crumb:
        links = re.findall(r"<a[^>]*>([^<]+)</a>", crumb.group(1))
        if len(links) >= 3:
            leader = html.unescape(links[-1].strip()) or leader
    event = ""
    placing = ""
    date = ""
    para = P_RE.search(text)
    if para:
        parts = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in para.group(1).split("·")]
        for part in parts:
            if DATE_RE.fullmatch(part):
                date = part
            elif PLACE_RE.fullmatch(part):
                placing = part
            elif re.fullmatch(r"\d+-\d+(?:-\d+)?", part):
                continue
            elif part.lower().startswith("public "):
                continue
            elif not event:
                event = part
    h2 = H2_RE.search(text)
    if h2 and not event:
        heading = html.unescape(re.sub(r"<[^>]+>", "", h2.group(1))).strip()
        if " - " in heading:
            event = heading.split(" - ", 1)[1].strip()
    return {
        "leader_name": leader,
        "tournament": event,
        "placing": placing,
        "date": date,
        "player": "",
    }


def entry_fields(entry: dict) -> tuple[str, str, str, str]:
    leader = entry.get("leader_name") or "Leader"
    event = (entry.get("tournament") or "").strip()
    if not event:
        event = (entry.get("title") or "").strip()
    placing = entry.get("placing")
    if isinstance(placing, int):
        place = gen.ordinal(placing) or ""
    else:
        place = str(placing or "")
    date = (entry.get("date") or "")[:10]
    return leader, event, place, date


def cards_from(text: str) -> list[tuple]:
    leader_block = LEADER_LINE_RE.search(text)
    leader_html = leader_block.group(0) if leader_block else ""
    cards = []
    seen = set()
    for qty, name, cid in LINE_RE.findall(text):
        cid = html.unescape(cid).strip().upper()
        if cid in seen:
            continue
        seen.add(cid)
        # The leader column is the only place this id is wrapped as the leader.
        flagged = cid in leader_html.upper() if False else (cid in html.unescape(leader_html).upper())
        cards.append((int(qty), cid, html.unescape(re.sub(r"<[^>]+>", "", name)).strip(), flagged))
    return cards


def buy_markup(cards: list[tuple]) -> str:
    if not cards:
        return ""
    dest = tcgplayer_links.mass_entry_url([(qty, cid, name) for qty, cid, name, _flag in cards])
    href = tcgplayer_links.affiliate_url(dest)
    return (
        f'<a class="buy-tcg" href="{html.escape(href, quote=True)}" '
        'target="_blank" rel="noopener nofollow sponsored">Buy list on TCGplayer</a>\n'
        '            <p class="affiliate-note">TCGplayer partner link. I earn from qualifying purchases.</p>'
    )


def fix_images(text: str) -> str:
    def pop(match: re.Match) -> str:
        tag = match.group(0)
        src = re.search(r'\ssrc="([^"]*)"', tag)
        if src and "data-src=" not in tag:
            tag = tag.replace(f' src="{src.group(1)}"', "", 1)
            tag = tag.replace("<img", f'<img data-src="{src.group(1)}"', 1)
        if "width=" not in tag:
            tag = tag.replace("<img", '<img width="220" height="308"', 1)
        return tag

    text = POP_RE.sub(pop, text)

    def card(match: re.Match) -> str:
        attrs = match.group(2)
        if "width=" not in attrs:
            attrs = ' width="300" height="419"' + attrs
        if "loading=" not in attrs:
            attrs = ' loading="lazy"' + attrs
        if "decoding=" not in attrs:
            attrs = ' decoding="async"' + attrs
        return match.group(1) + "<img" + attrs + ">"

    return CARD_IMG_RE.sub(card, text)


def fix_stats(text: str) -> str:
    match = STATS_RE.search(text)
    if not match or "deck-stats-text" in match.group(0):
        return text
    block = match.group(0)
    titles = re.findall(r'title="([^"]+)"', block)
    pills = re.findall(r'class="pill">([^<]+)', block)
    sentence = deck_seo.stats_fallback(titles, pills)
    # The bars stay aria-hidden. This sentence is the text fallback.
    block = block.replace(
        "</section>",
        f'          <p class="deck-stats-text">{html.escape(sentence)}</p>\n        </section>',
        1,
    )
    return text[: match.start()] + block + text[match.end() :]


def fix_exports(text: str, cards: list[tuple]) -> str:
    if "data-copy-plain" not in text:
        extra = (
            "</button>\n"
            '            <button type="button" class="copy-sim" data-copy-plain>Copy plain text</button>\n'
            '            <button type="button" class="copy-sim" data-copy-builder>Copy deck-builder list</button>\n'
            '            <button type="button" class="copy-sim" data-copy-link>Copy link</button>'
        )
        text, n = TITLE_BTN_RE.subn(lambda m: m.group(1) + extra, text, count=1)
        if n == 0 and 'class="text-deck"' in text:
            text = text.replace(
                "<h3>Text list</h3>",
                "<h3>Text list</h3>\n"
                '            <button type="button" class="copy-sim" data-copy-sim>Copy to OP TCG SIM</button>\n'
                '            <button type="button" class="copy-sim" data-copy-plain>Copy plain text</button>\n'
                '            <button type="button" class="copy-sim" data-copy-builder>Copy deck-builder list</button>\n'
                '            <button type="button" class="copy-sim" data-copy-link>Copy link</button>',
                1,
            )
    if 'class="buy-tcg"' not in text:
        markup = buy_markup(cards)
        if markup and 'class="text-deck"' in text:
            text = text.replace(
                '<div class="text-deck-cols">',
                markup + '\n          <div class="text-deck-cols">',
                1,
            )
    return text


def related_html(href: str, entry: dict, more: list[dict], prev_next: tuple[dict | None, dict | None]) -> str:
    leader = entry.get("leader_name") or "this leader"
    key = entry.get("leader_key") or ""
    hub = f"/decklists/{key}.html" if key else ""
    rows = []
    if hub:
        rows.append(f'<li><a href="{html.escape(hub)}">All {html.escape(leader)} decklists</a></li>')
    for other in more:
        if other.get("href") == href:
            continue
        label = other.get("player") or other.get("title") or "List"
        place = other.get("placing")
        if isinstance(place, int):
            label = f"{gen.ordinal(place) or place} {label}"
        rows.append(
            f'<li><a href="{html.escape(other["href"])}">{html.escape(str(label))}</a></li>'
        )
        if len(rows) >= 5:
            break
    more_block = ""
    if rows:
        more_block = (
            "        <!-- MORE_LISTS -->\n"
            '        <section class="more-lists">\n'
            f"          <h3>More {html.escape(leader)} lists</h3>\n"
            "          <ul>\n            " + "\n            ".join(rows) + "\n          </ul>\n"
            "        </section>\n"
            "        <!-- /MORE_LISTS -->\n"
        )
    guide = seo.LEADER_GUIDE.get(key)
    guide_href = f"/guides/{guide}-strategy.html" if guide else ""
    guide_link = ""
    if guide_href and (ROOT / guide_href.lstrip("/")).exists():
        guide_link = f' <a href="{guide_href}">{html.escape(leader)} strategy</a>.'
    matchup = (
        "        <!-- MATCHUP_NOTES -->\n"
        '        <section class="matchup-notes">\n'
        "          <h3>Matchup notes</h3>\n"
        f"          <p>Matchup notes for {html.escape(leader)} sit with the other OPTCG guides."
        f"{guide_link} "
        '<a href="/guides/matchups.html">All matchup notes</a>.</p>\n'
        "        </section>\n"
        "        <!-- /MATCHUP_NOTES -->\n"
    )
    prev, nxt = prev_next
    pager = ""
    links = []
    if prev and prev.get("href"):
        links.append(f'<a href="{html.escape(prev["href"])}">Previous in this event</a>')
    if nxt and nxt.get("href"):
        links.append(f'<a href="{html.escape(nxt["href"])}">Next in this event</a>')
    if links:
        pager = '        <nav class="event-pager" aria-label="Same event">' + " · ".join(links) + "</nav>\n"
    return pager + more_block + matchup


def upsert_social(text: str, title: str, desc: str, url: str, image: str, crumbs, author: str, date: str, about: str) -> str:
    text = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", text, count=1, flags=re.S)
    if 'name="description"' in text:
        text = re.sub(
            r'<meta name="description" content=".*?"\s*/?>',
            f'<meta name="description" content="{html.escape(desc)}" />',
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = text.replace("</title>", f"</title>\n  <meta name=\"description\" content=\"{html.escape(desc)}\" />", 1)
    text = OG_RE.sub("", text)
    text = JSONLD_RE.sub("", text)
    block = seo.social_tags(title, desc, url, image)
    if date:
        block += f'  <meta property="article:published_time" content="{html.escape(date)}" />\n'
    crumb_pairs = [(name, href or url) for name, href in crumbs]
    if crumb_pairs and crumb_pairs[-1][0] == "Decklist":
        crumb_pairs[-1] = (title[:80], url)
    block += seo.breadcrumb_jsonld(crumb_pairs)
    article = seo.article_jsonld(
        title=title, desc=desc, url=url, image=image, date=date or None, author=author or None, about=about
    )
    block += seo.jsonld_script(article)
    text = text.replace("</head>", block + "</head>", 1)
    text = text.replace('src="/js/site.js?v=', 'src="/js/site.js?v=deck-tools1" data-v="', 1)
    text = text.replace('src="/js/site.js?v=deck-tools1" data-v="', 'src="/js/site.js?v=', 1)
    text = re.sub(r'src="/js/site\.js\?v=[^"]+"', 'src="/js/site.js?v=deck-tools1"', text)
    text = re.sub(r'href="/css/site\.css\?v=[^"]+"', 'href="/css/site.css?v=home-pro25"', text)
    return text


def main() -> None:
    names = leader_names()
    entries = load_entries()
    by_leader: dict[str, list[dict]] = defaultdict(list)
    by_event: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for href, entry in entries.items():
        by_leader[entry.get("leader_key") or ""].append(entry)
        event = (entry.get("tournament") or "").strip()
        date = (entry.get("date") or "")[:10]
        if event and date:
            by_event[(event, date)].append(entry)
    for rows in by_event.values():
        rows.sort(key=lambda row: (row.get("placing") is None, row.get("placing") or 9999, row.get("player") or ""))
    more_for = {}
    for key, rows in by_leader.items():
        ranked = sorted(rows, key=lambda row: row.get("date") or "", reverse=True)
        more_for[key] = ranked[:8]

    audit = {
        "pages": 0,
        "with_partner_link": 0,
        "missing_partner": [],
        "qty_not_50": [],
        "unmatched_cards": {},
        "price": "not shown — TCGplayer price-display terms were not confirmed",
        "images": "Limitless CDN art was not copied. Terms for rehosting those files were not clear.",
    }
    names_map = tcgplayer_links.load_catalog_names()
    ids_map = tcgplayer_links.load_ids()
    changed = 0
    for path in ROOT.joinpath("decklists").rglob("*.html"):
        rel = path.relative_to(ROOT).as_posix()
        parts = Path(rel).parts
        if len(parts) != 3 or parts[0] != "decklists":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if is_stub(text):
            continue
        if 'class="text-deck"' not in text and "text-line" not in text:
            continue
        href = "/" + rel
        entry = entries.get(href) or parse_html_meta(text, parts[1], names)
        if "leader_name" not in entry or not entry.get("leader_name"):
            entry = {**parse_html_meta(text, parts[1], names), **entry}
        entry.setdefault("leader_key", parts[1])
        entry.setdefault("leader_name", names.get(parts[1], parts[1]))
        leader, event, place, date = entry_fields(entry)
        title = deck_seo.deck_title(leader, event, place, date)
        desc = deck_seo.deck_description(leader, event, place, date)
        cards = cards_from(text)
        original = text
        text = fix_images(text)
        text = fix_stats(text)
        text = fix_exports(text, cards)
        if "<!-- MORE_LISTS -->" not in text:
            event_key = ((entry.get("tournament") or "").strip(), (entry.get("date") or "")[:10])
            siblings = by_event.get(event_key, []) if event_key[0] and event_key[1] else []
            prev = nxt = None
            hrefs = [row.get("href") for row in siblings]
            if href in hrefs:
                idx = hrefs.index(href)
                prev = siblings[idx - 1] if idx > 0 else None
                nxt = siblings[idx + 1] if idx + 1 < len(siblings) else None
            block = related_html(href, entry, more_for.get(entry.get("leader_key") or "", []), (prev, nxt))
            needle = '<p class="muted" style="margin-top:22px">'
            if needle in text:
                text = text.replace(needle, block + needle, 1)
            else:
                text = text.replace("</main>", block + "</main>", 1)
        if 'class="event-pager"' not in text:
            event_key = ((entry.get("tournament") or "").strip(), (entry.get("date") or "")[:10])
            siblings = by_event.get(event_key, []) if event_key[0] and event_key[1] else []
            hrefs = [row.get("href") for row in siblings]
            if href in hrefs:
                idx = hrefs.index(href)
                prev = siblings[idx - 1] if idx > 0 else None
                nxt = siblings[idx + 1] if idx + 1 < len(siblings) else None
                links = []
                if prev and prev.get("href"):
                    links.append(f'<a href="{html.escape(prev["href"])}">Previous in this event</a>')
                if nxt and nxt.get("href"):
                    links.append(f'<a href="{html.escape(nxt["href"])}">Next in this event</a>')
                if links:
                    pager = '<nav class="event-pager" aria-label="Same event">' + " · ".join(links) + "</nav>\n"
                    text = re.sub(r"(<h2>.*?</h2>\s*<p>.*?</p>)", r"\1\n        " + pager, text, count=1, flags=re.S)
        url = SITE + href
        image = seo.og_image_for(rel, gen.LEADERS)
        crumbs = seo.parse_crumbs(text)
        author = entry.get("player") or ""
        text = upsert_social(text, title, desc, url, image, crumbs, author, date, leader)
        if text != original:
            path.write_text(text)
            changed += 1
        audit["pages"] += 1
        if PARTNER_NEEDLE in text and "massentry" in text and 'class="buy-tcg"' in text:
            audit["with_partner_link"] += 1
        else:
            if len(audit["missing_partner"]) < 40:
                audit["missing_partner"].append(href)
        main_qty = sum(qty for qty, cid, _name, flag in cards if not flag)
        if cards and main_qty != 50 and len(audit["qty_not_50"]) < 40:
            audit["qty_not_50"].append({"href": href, "main_qty": main_qty, "lines": len(cards)})
        for qty, cid, name, _flag in cards:
            reasons = []
            if cid not in names_map:
                reasons.append("no_catalog_name")
            if cid not in ids_map:
                reasons.append("no_product_id")
            if not reasons:
                continue
            slot = audit["unmatched_cards"].setdefault(cid, {"name": name, "reasons": reasons, "pages": 0})
            slot["pages"] += 1
        if audit["pages"] % 500 == 0:
            print("patched", audit["pages"], "changed", changed, flush=True)
    audit["unmatched_count"] = len(audit["unmatched_cards"])
    # Keep the report small: drop page counts into a sorted list of ids.
    unmatched = sorted(audit["unmatched_cards"].items(), key=lambda item: (-item[1]["pages"], item[0]))
    audit["unmatched_cards"] = {cid: meta for cid, meta in unmatched[:200]}
    audit["unmatched_truncated"] = max(0, len(unmatched) - 200)
    (ROOT / "data/tcgplayer-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(
        "pages",
        audit["pages"],
        "changed",
        changed,
        "partner",
        audit["with_partner_link"],
        "missing",
        len(audit["missing_partner"]),
        "qty",
        len(audit["qty_not_50"]),
        "unmatched",
        audit["unmatched_count"],
    )


if __name__ == "__main__":
    main()
