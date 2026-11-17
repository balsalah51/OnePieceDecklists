#!/usr/bin/env python3
"""Write the page of hosted decks that include at least one OP18 card."""

from __future__ import annotations

import html
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "op18-lists.html"
DECKS = ROOT / "decklists"
CARD_RE = re.compile(
    r'<span class="qty">(\d+)x</span>\s*'
    r'<span class="card-title">.*?</span>\s*'
    r'<span class="muted card-id">([^<]+)</span>',
    re.S,
)
OP18_RE = re.compile(r"^OP18-\d{3}$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def load_gen():
    spec = importlib.util.spec_from_file_location(
        "genlists", ROOT / "scripts" / "generate-tournament-lists.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def collect() -> list[dict]:
    rows = []
    paths = list(DECKS.glob("*/*.html")) + list(DECKS.glob("*/*/*.html"))
    for path in sorted(paths):
        if path.name == "index.html":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        pairs = CARD_RE.findall(text)
        op18 = [(n, cid) for n, cid in pairs if OP18_RE.match(cid)]
        if not op18:
            continue
        title_m = re.search(r"<h2>(.*?)</h2>", text)
        sub_m = re.search(r"</h2>\s*<p>(.*?)</p>", text, re.S)
        title = html.unescape(re.sub(r"<[^>]+>", "", title_m.group(1))).strip() if title_m else path.stem
        subtitle = html.unescape(re.sub(r"<[^>]+>", "", sub_m.group(1))).strip() if sub_m else ""
        date_m = DATE_RE.search(subtitle) or DATE_RE.search(text)
        leader_m = re.search(r'<a href="(/decklists/[^"]+)">([^<]+)</a> / Decklist', text)
        rows.append(
            {
                "href": "/" + path.relative_to(ROOT).as_posix(),
                "title": title,
                "subtitle": subtitle,
                "date": date_m.group(0) if date_m else "",
                "leader_href": leader_m.group(1) if leader_m else "",
                "leader": html.unescape(leader_m.group(2)) if leader_m else "",
                "op18": op18,
            }
        )
    rows.sort(key=lambda row: (row["date"], row["title"]), reverse=True)
    return rows


def render(gen, rows: list[dict]) -> str:
    count = len(rows)
    items = []
    for row in rows:
        cards = ", ".join(f"{n}x {cid}" for n, cid in row["op18"][:8])
        extra = f" +{len(row['op18']) - 8} more" if len(row["op18"]) > 8 else ""
        leader = ""
        if row["leader_href"]:
            leader = f'<a href="{html.escape(row["leader_href"])}">{html.escape(row["leader"])}</a>'
        items.append(
            f"""            <li>
              <a class="item" href="{html.escape(row["href"])}">
                <div>
                  <div style="font-weight:700">{html.escape(row["title"])}</div>
                  <div class="muted" style="font-size:13px">{html.escape(row["subtitle"])}</div>
                  <div class="muted" style="font-size:13px">OP18 cards: {html.escape(cards)}{html.escape(extra)}</div>
                </div>
                <div class="link">Open →</div>
              </a>
              <p class="muted" style="margin:6px 0 0">{leader}</p>
            </li>"""
        )
    body = f"""        <div class="crumb"><a href="/">Home</a> / OP18 lists</div>
        <h2>Decks with OP18 cards</h2>
        <p>Complete public 50-card lists that include at least one OP-18 card. English OP-18 The Dominance of God releases 20 November 2026. These include simulator cups and pre-release builds with real card numbers, not invented lists.</p>
        <div class="spoiler-facts">
          <div><strong>{count}</strong><span>Hosted lists</span></div>
          <div><strong>OP18-060</strong><span><a href="/decklists/saint-gunko.html">Saint Gunko</a></span></div>
          <div><strong>20 Nov 2026</strong><span>English release</span></div>
          <div><strong><a href="/op18-spoilers.html">Spoilers</a></strong><span>Full card list</span></div>
        </div>
        <section class="related-links" style="margin-top:22px">
          <div class="section-title">
            <h3>Hosted lists</h3>
            <div class="muted">{count} complete decks</div>
          </div>
          <ul class="list">
{chr(10).join(items) if items else '            <li class="muted">No OP18 lists hosted yet.</li>'}
          </ul>
        </section>"""
    return gen.page_chrome(
        "OP18 decklists | One Piece Decklists",
        f"{count} complete public One Piece TCG decks that include OP18 The Dominance of God cards.",
        "",
        False,
        body,
        include_tcgplayer=False,
        path="op18-lists.html",
    )


def main() -> None:
    gen = load_gen()
    rows = collect()
    OUT.write_text(render(gen, rows), encoding="utf-8")
    print("op18 lists", len(rows), OUT)


if __name__ == "__main__":
    main()
