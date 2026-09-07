#!/usr/bin/env python3
"""Build the OP17 tier list page from public sources plus this site's lists.

Does not invent tournament results. External ranks are recorded from public
pages; site ranks come from tournament-decks.json / community-decks.json.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path("/workspace")
RECENT_FROM = "2026-08-20"
CSS_VER = "tier-home"
TIER_PTS = {"S": 5.0, "A": 3.5, "B": 2.0, "C": 1.0, "D": 0.4}
COLOR_NAMES = {
    "color-red": "Red",
    "color-green": "Green",
    "color-blue": "Blue",
    "color-purple": "Purple",
    "color-black": "Black",
    "color-yellow": "Yellow",
    "color-red-green": "Red/Green",
    "color-red-blue": "Red/Blue",
    "color-green-blue": "Green/Blue",
    "color-black-yellow": "Black/Yellow",
    "color-purple-yellow": "Purple/Yellow",
    "color-red-black": "Red/Black",
    "color-blue-yellow": "Blue/Yellow",
    "color-blue-purple": "Blue/Purple",
    "color-red-purple": "Red/Purple",
    "color-purple-black": "Purple/Black",
    "color-red-yellow": "Red/Yellow",
    "color-blue-black": "Blue/Black",
    "color-green-yellow": "Green/Yellow",
    "color-green-purple": "Green/Purple",
}
SKIP_PARTS = {".git", "scripts", "node_modules", "discord-bot", "ballkeep"}
SKIP_FILES = {"shop/custom-leaders.html", "shop/buy-list.html"}
HOME_TIER_TILE = """          <a class="home-big home-big-tier" href="/tier-list.html">
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
"""

spec = importlib.util.spec_from_file_location("genlists", ROOT / "scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
sspec = importlib.util.spec_from_file_location("seocommon", ROOT / "scripts/seo_common.py")
seo = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(seo)

LEADERS = gen.LEADERS
BY_ID = {L["id"]: L for L in LEADERS}


def leader_img(lid: str) -> str:
    set_code = lid.split("-")[0]
    return f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/{set_code}/{lid}_EN.webp"


def color_name(L: dict) -> str:
    return COLOR_NAMES.get(L.get("color") or "", "")


# External public tier lists / meta reports. At least 20 sources.
# ranks: leader id -> S/A/B/C/D
SOURCES = [
    {
        "id": "opmetagame-tier",
        "name": "OP Meta Game OP-17 tier list",
        "url": "https://opmetagame.com/tier-list/",
        "when": "September 2026",
        "weight": 1.15,
        "note": "Live S/A/B/C from tournament win rate and placements.",
        "ranks": {
            "OP14-020": "S",
            "OP17-039": "S",
            "OP13-004": "S",
            "OP13-001": "S",
            "OP16-001": "A",
            "OP17-079": "A",
            "OP15-058": "A",
            "OP14-080": "A",
            "OP17-058": "B",
            "OP09-062": "B",
            "OP05-098": "B",
            "OP14-041": "C",
            "OP17-020": "C",
            "OP13-001": "S",
            "OP17-099": "C",
            "OP11-062": "C",
            "OP16-022": "C",
            "OP16-080": "C",
            "OP08-058": "C",
            "OP16-079": "C",
        },
    },
    {
        "id": "opmetagame-share",
        "name": "OP Meta Game OP-17 meta share",
        "url": "https://opmetagame.com/decks/",
        "when": "September 2026",
        "weight": 1.1,
        "note": "Top-cut share: Mihawk 26.9% S, Rocks 14.0% A, Kaido 7.5% B.",
        "ranks": {
            "OP14-020": "S",
            "OP17-039": "A",
            "OP17-058": "B",
            "OP13-004": "C",
            "OP16-001": "C",
            "OP14-041": "C",
            "OP09-062": "C",
            "OP11-062": "C",
            "OP17-099": "C",
        },
    },
    {
        "id": "new-realm",
        "name": "New Realm Games OP-17 metagame report",
        "url": "https://newrealmgames.com/blogs/news/op-17-metagame-report-best-decks",
        "when": "1 September 2026",
        "weight": 1.0,
        "note": "Written early OP-17 tier: Mihawk / Rocks / Sabo as Tier 1.",
        "ranks": {
            "OP14-020": "S",
            "OP17-039": "S",
            "OP13-004": "S",
            "OP16-001": "A",
            "OP17-079": "A",
            "OP15-058": "A",
            "OP17-058": "B",
        },
    },
    {
        "id": "opdeckguide",
        "name": "OPDeckGuide OP17 meta analysis",
        "url": "https://opdeckguide.com/meta-analysis/",
        "when": "September 2026",
        "weight": 0.95,
        "note": "Current-format pages lead with Mihawk, Sabo, and Rocks.",
        "ranks": {"OP14-020": "S", "OP13-004": "S", "OP17-039": "S", "OP13-001": "A"},
    },
    {
        "id": "eggman-power",
        "name": "Eggman Events OP17 power rankings (preview week)",
        "url": "https://www.youtube.com/watch?v=iI7d6hrhbKY",
        "when": "August 2026",
        "weight": 0.9,
        "note": "Top five: Rocks, Ace, Sabo, Linlin, Mihawk. Rocks most played and highest win rate.",
        "ranks": {
            "OP17-039": "S",
            "OP16-001": "A",
            "OP13-004": "A",
            "OP17-099": "A",
            "OP14-020": "A",
            "OP17-079": "B",
            "OP17-058": "B",
            "OP14-041": "B",
            "OP16-022": "B",
            "OP15-058": "B",
            "OP17-020": "C",
            "OP17-001": "C",
            "OP13-001": "C",
            "OP11-041": "C",
        },
    },
    {
        "id": "early-yt",
        "name": "Way too early OP17 tier list (YouTube)",
        "url": "https://www.youtube.com/watch?v=BclWG-fTyg8",
        "when": "August 2026",
        "weight": 0.45,
        "note": "Pre-release discussion. Nami as a format survivor; Linlin and Ace called out.",
        "ranks": {
            "OP11-041": "B",
            "OP17-099": "A",
            "OP16-001": "A",
            "OP14-020": "A",
            "OP14-041": "B",
            "OP16-022": "C",
        },
    },
    {
        "id": "thorn-mihawk",
        "name": "Thornberry Media OP-17 Mihawk",
        "url": "https://www.thornberrymedia.com/post/op-17-mihawk-deck-list",
        "when": "August 2026",
        "weight": 0.55,
        "note": "Calls Mihawk one of the format's biggest winners and the best green deck in testing.",
        "ranks": {"OP14-020": "S", "OP17-020": "B"},
    },
    {
        "id": "thorn-rocks",
        "name": "Thornberry Media OP-17 Rocks D. Xebec",
        "url": "https://www.thornberrymedia.com/post/op-17-rocks-d-xebec-deck-list",
        "when": "August 2026",
        "weight": 0.55,
        "note": "High-ceiling Rocks rebuild deck; weak to early aggro.",
        "ranks": {"OP17-039": "S"},
    },
    {
        "id": "thorn-luffy",
        "name": "Thornberry Media OP-17 Black Luffy",
        "url": "https://www.thornberrymedia.com/post/op-17-luffy-deck-list",
        "when": "August 2026",
        "weight": 0.5,
        "note": "Black Elbaph Luffy as a cohesive new board deck.",
        "ranks": {"OP17-079": "A"},
    },
    {
        "id": "tcg-portal",
        "name": "TCG PORTAL Japan Standard ranking",
        "url": "https://tcg-portal.jp/onepiece/meta-analysis",
        "when": "4 September 2026",
        "weight": 1.2,
        "note": "481 Japanese lists, 7 Aug to 6 Sep. Mihawk 25.4% T1; Rocks rising to 8.5% late.",
        "ranks": {
            "OP14-020": "S",
            "OP15-058": "A",
            "OP17-039": "A",
            "OP16-001": "A",
            "OP09-062": "A",
            "OP13-001": "B",
            "OP14-041": "B",
            "OP13-004": "B",
            "OP16-022": "B",
            "OP12-040": "C",
            "OP17-079": "C",
            "ST30-001": "C",
            "OP17-058": "C",
            "OP16-080": "C",
            "OP11-062": "C",
            "OP16-079": "C",
            "OP17-099": "C",
            "OP11-041": "C",
            "OP17-020": "C",
            "OP13-079": "D",
            "OP13-002": "D",
            "OP15-002": "D",
            "OP10-099": "D",
            "OP11-001": "D",
        },
    },
    {
        "id": "torecamap",
        "name": "Toreca Map environment tier table",
        "url": "https://torecamap.co.jp/column/environment-decks/",
        "when": "17 August 2026",
        "weight": 0.35,
        "note": "Late OP16 Japan snapshot before OP17 English. Mihawk / Enel / RG Luffy T1.",
        "ranks": {
            "OP14-020": "S",
            "OP15-058": "S",
            "OP13-001": "S",
            "OP16-080": "A",
            "OP11-041": "A",
            "OP11-062": "A",
            "OP12-040": "A",
        },
    },
    {
        "id": "limitless-play",
        "name": "Limitless Play decks (One Piece)",
        "url": "https://play.limitlesstcg.com/decks?game=OP",
        "when": "September 2026",
        "weight": 1.05,
        "note": "OP17 leaders on Limitless: Rocks 59.7% from 63 lists; Kaido 46.9% from 53.",
        "ranks": {
            "OP17-039": "S",
            "OP17-020": "A",
            "OP17-079": "B",
            "OP17-099": "B",
            "OP17-058": "C",
            "OP17-001": "D",
        },
    },
    {
        "id": "limitless-op",
        "name": "Limitless One Piece decks hub",
        "url": "https://onepiece.limitlesstcg.com/decks",
        "when": "2026",
        "weight": 0.3,
        "note": "Older points table still listing Nami, GB Luffy, and Enel as high share.",
        "ranks": {
            "OP11-041": "A",
            "OP16-022": "A",
            "OP15-058": "A",
            "OP12-061": "B",
            "OP16-080": "B",
            "OP14-020": "C",
            "OP16-001": "C",
        },
    },
    {
        "id": "optcg-one",
        "name": "OPTCG.one ranked-play meta",
        "url": "https://www.optcg.one/meta",
        "when": "September 2026",
        "weight": 0.85,
        "note": "Ranked win rates. Mihawk 52.9%, Sabo 52.4%, Rocks 51.6%, Luffy & Ace 55.6%.",
        "ranks": {
            "OP14-020": "S",
            "OP13-004": "S",
            "OP17-039": "S",
            "ST30-001": "S",
            "OP09-062": "S",
            "OP17-099": "A",
            "OP14-041": "A",
            "OP17-079": "A",
            "OP15-058": "A",
            "OP16-001": "A",
            "OP17-058": "A",
            "OP14-080": "A",
            "OP17-020": "B",
            "OP12-061": "B",
            "OP08-058": "B",
            "OP16-080": "B",
            "OP16-079": "B",
            "OP17-001": "B",
            "OP11-062": "B",
            "OP11-041": "C",
            "OP13-001": "C",
        },
    },
    {
        "id": "onepiece-gg",
        "name": "OnePiece.gg OP16 + ST30 tier list",
        "url": "https://onepiece.gg/one-piece-card-game-meta-tier-list-best-decks-standard-op16-st30/",
        "when": "August 2026",
        "weight": 0.3,
        "note": "Pre-OP17 English write-up. Enel / GB Luffy / Rosinante as T1 then.",
        "ranks": {
            "OP15-058": "S",
            "OP16-022": "S",
            "OP12-061": "S",
            "OP16-080": "A",
            "OP11-041": "A",
            "OP15-002": "A",
            "OP13-002": "A",
            "OP14-020": "A",
            "OP16-079": "A",
            "OP16-060": "A",
            "ST30-001": "A",
            "OP16-001": "B",
            "OP13-001": "C",
            "OP14-041": "C",
        },
    },
    {
        "id": "metafy-rocks",
        "name": "Metafy Rocks D. Xebec OP17 guide",
        "url": "https://metafy.gg/guides/view/rocks-d-xebec-op17-ultimate-guide-JF1nWCBGDgA",
        "when": "18 August 2026",
        "weight": 0.5,
        "note": "Treats Rocks as a solved OP17 deck with dedicated Mihawk, Kaido, and Black Luffy matchups.",
        "ranks": {"OP17-039": "S", "OP14-020": "S", "OP17-058": "A", "OP17-079": "A"},
    },
    {
        "id": "yuyutei-rocks",
        "name": "Yuyu-tei じょーじ Blue Rocks intro",
        "url": "https://yuyu-tei.jp/index.php/show/opc/content/27405",
        "when": "August 2026",
        "weight": 0.5,
        "note": "Japan shop list. Mentions Enel and Mihawk as the matchups Rocks techs for.",
        "ranks": {"OP17-039": "S", "OP15-058": "A", "OP14-020": "S"},
    },
    {
        "id": "mercard-rocks",
        "name": "Mercard OP Blue Rocks guide",
        "url": "https://www.mercardop.jp/article-detail/82",
        "when": "August 2026",
        "weight": 0.45,
        "note": "Full 50-card OP17 Rocks primer for the Japanese release.",
        "ranks": {"OP17-039": "S"},
    },
    {
        "id": "onepiecedb",
        "name": "OnePieceDB OP17 format page",
        "url": "https://onepiecedb.io/format/op17",
        "when": "September 2026",
        "weight": 0.2,
        "note": "OP17 format hub. Thin community sample at scrape time.",
        "ranks": {},
    },
    {
        "id": "chinoize-98",
        "name": "Limitless ChinoizeCup #98 Rocks metagame",
        "url": "https://play.limitlesstcg.com/tournament/6a7d7b64cdc0391d7fa65402/metagame/OP17-039",
        "when": "August 2026",
        "weight": 0.7,
        "note": "One large OP17 cup: Rocks 68% (83-39) with 20 pilots, including 1st and 2nd.",
        "ranks": {"OP17-039": "S", "OP13-004": "A", "OP17-058": "A", "OP14-020": "A", "OP17-079": "B"},
    },
    {
        "id": "opdl-format",
        "name": "One Piece Decklists format notes",
        "url": "https://onepiecedecklists.com/format.html",
        "when": "September 2026",
        "weight": 0.6,
        "note": "This site's written OP17 take before the dedicated tier page.",
        "ranks": {
            "OP17-039": "S",
            "OP17-058": "A",
            "OP17-079": "A",
            "OP17-099": "B",
            "OP14-020": "A",
            "OP16-001": "A",
            "OP17-020": "C",
            "OP17-001": "C",
        },
    },
    {
        "id": "opdl-meta-guide",
        "name": "One Piece Decklists meta guide",
        "url": "https://onepiecedecklists.com/guides/one-piece-tcg-meta.html",
        "when": "September 2026",
        "weight": 0.4,
        "note": "Names Rocks, Kaido, Black Luffy, Linlin, Shanks, RG Luffy, Nami, Mihawk, Ace, Enel, Katakuri.",
        "ranks": {
            "OP17-039": "A",
            "OP17-058": "A",
            "OP17-079": "A",
            "OP17-099": "B",
            "OP17-020": "B",
            "OP13-001": "B",
            "OP11-041": "B",
            "OP14-020": "A",
            "OP16-001": "A",
            "OP15-058": "B",
            "OP11-062": "C",
        },
    },
    {
        "id": "tcg-portal-extra",
        "name": "TCG PORTAL Extra format ranking",
        "url": "https://tcg-portal.jp/onepiece/meta-analysis",
        "when": "August 2026",
        "weight": 0.2,
        "note": "Extra format, not Standard. GB Luffy T1 there.",
        "ranks": {"OP16-022": "S", "OP14-020": "A", "OP13-001": "A", "OP11-040": "B"},
    },
    {
        "id": "opmetagame-op16",
        "name": "OP Meta Game OP-16 archive snapshot",
        "url": "https://opmetagame.com/tier-list/",
        "when": "August 2026",
        "weight": 0.25,
        "note": "OP-16 S was Enel and GB Luffy; Mihawk sat in B before OP17 tools.",
        "ranks": {
            "OP15-058": "S",
            "OP16-022": "S",
            "OP14-020": "B",
            "OP13-001": "B",
            "OP12-061": "B",
            "OP16-079": "C",
            "OP13-002": "C",
            "OP14-041": "C",
            "OP16-001": "C",
        },
    },
]


def site_stats() -> dict[str, dict]:
    tour = json.loads((ROOT / "data/tournament-decks.json").read_text())
    comm = json.loads((ROOT / "data/community-decks.json").read_text())
    out = {}
    for L in LEADERS:
        lid = L["id"]
        lists = tour.get(lid) or []
        recent = [x for x in lists if (x.get("date") or "") >= RECENT_FROM]
        def place(xs, n):
            return sum(1 for x in xs if isinstance(x.get("placing"), int) and x["placing"] <= n)
        def wins(xs):
            return sum(1 for x in xs if x.get("placing") == 1)
        best = None
        hrefs = []
        for x in lists:
            p = x.get("placing")
            if isinstance(p, int) and (best is None or p < best):
                best = p
            if x.get("href"):
                hrefs.append(x["href"])
        out[lid] = {
            "lists": len(lists),
            "wins": wins(lists),
            "top8": place(lists, 8),
            "top4": place(lists, 4),
            "recent_lists": len(recent),
            "recent_wins": wins(recent),
            "recent_top8": place(recent, 8),
            "community": len(comm.get(lid) or []),
            "best": best,
            "href": "/" + L["page"],
        }
    return out


def site_source(stats: dict[str, dict]) -> dict:
    ranks = {}
    for lid, s in stats.items():
        score = (
            s["recent_wins"] * 6
            + s["recent_top8"] * 1.4
            + min(s["recent_lists"], 80) * 0.09
        )
        if score >= 28:
            ranks[lid] = "S"
        elif score >= 12:
            ranks[lid] = "A"
        elif score >= 5:
            ranks[lid] = "B"
        elif score >= 1.5 or s["recent_lists"] >= 3:
            ranks[lid] = "C"
        elif s["recent_lists"] or s["recent_top8"]:
            ranks[lid] = "D"
    return {
        "id": "opdl-lists",
        "name": "One Piece Decklists tournament tables",
        "url": "https://onepiecedecklists.com/",
        "when": "through 3 September 2026",
        "weight": 1.25,
        "note": f"Recent window from {RECENT_FROM}. Wins and top eights on lists hosted here.",
        "ranks": ranks,
    }


def aggregate(stats: dict[str, dict]) -> tuple[list[dict], dict[str, dict]]:
    sources = SOURCES + [site_source(stats)]
    scores: dict[str, float] = defaultdict(float)
    hits: dict[str, int] = defaultdict(int)
    by_tier_votes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for src in sources:
        w = float(src["weight"])
        for lid, tier in (src.get("ranks") or {}).items():
            if lid not in BY_ID:
                continue
            scores[lid] += w * TIER_PTS.get(tier, 0)
            hits[lid] += 1
            by_tier_votes[lid][tier] += 1
    ranked = []
    for lid, L in BY_ID.items():
        s = stats.get(lid) or {}
        score = scores.get(lid, 0.0)
        if hits.get(lid, 0) < 2 and s.get("recent_top8", 0) == 0 and s.get("recent_lists", 0) < 4:
            continue
        if score >= 32:
            tier = "S"
        elif score >= 16:
            tier = "A"
        elif score >= 7.5:
            tier = "B"
        elif score >= 2.8:
            tier = "C"
        else:
            tier = "D"
        ranked.append(
            {
                "id": lid,
                "name": L["name"],
                "href": "/" + L["page"],
                "image": leader_img(lid),
                "color": L.get("color") or "",
                "color_label": color_name(L),
                "tier": tier,
                "score": round(score, 2),
                "sources": hits.get(lid, 0),
                "votes": dict(by_tier_votes[lid]),
                **s,
            }
        )
    ranked.sort(key=lambda r: (r["tier"], -r["score"], -r["recent_top8"], -r["recent_lists"], r["name"]))
    order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
    ranked.sort(key=lambda r: (order[r["tier"]], -r["score"], r["name"]))
    return sources, {r["id"]: r for r in ranked}


def render_board(rows: list[dict]) -> str:
    labels = {
        "S": "Format defining. Show up in top cuts every week.",
        "A": "Wins cups and converts. A step behind the default decks.",
        "B": "Real, but you have to know the room.",
        "C": "Posts lists. Not the plan unless the table is soft.",
        "D": "Rogues and leftovers still on this site.",
    }
    chunks = []
    for letter in "SABCD":
        group = [r for r in rows if r["tier"] == letter]
        if not group:
            continue
        cards = []
        for r in group:
            note = f"{r['recent_top8']} recent top 8s" if r["recent_top8"] else f"{r['recent_lists']} recent lists"
            cards.append(
                f"""            <a class="tier-leader {html.escape(r['color'])}" href="{html.escape(r['href'], quote=True)}">
              <img src="{html.escape(r['image'], quote=True)}" alt="{html.escape(r['name'])} leader card" width="86" height="120" loading="lazy" />
              <div class="name">{html.escape(r['name'])}</div>
              <div class="meta">{html.escape(note)}</div>
            </a>"""
            )
        chunks.append(
            f"""        <div class="tier-row tier-{letter.lower()}">
          <div class="tier-label" title="{html.escape(labels[letter])}">{letter}</div>
          <div class="tier-leaders">
{chr(10).join(cards)}
          </div>
        </div>"""
        )
    return "\n".join(chunks)


def render_table(rows: list[dict]) -> str:
    body = []
    for r in rows:
        body.append(
            f"""            <tr>
              <td><strong>{html.escape(r['tier'])}</strong></td>
              <td><a href="{html.escape(r['href'], quote=True)}">{html.escape(r['name'])}</a></td>
              <td>{html.escape(r['color_label'])}</td>
              <td>{r['recent_lists']}</td>
              <td>{r['recent_wins']}</td>
              <td>{r['recent_top8']}</td>
              <td>{r['lists']}</td>
              <td>{r['wins']}</td>
              <td>{r['sources']}</td>
            </tr>"""
        )
    return f"""        <div class="tier-table">
          <div class="section-title">
            <h3>This site's lists in the mix</h3>
            <div class="muted">Recent = {RECENT_FROM} onward, covering the OP17 English window</div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Tier</th><th>Leader</th><th>Color</th>
                <th>Recent lists</th><th>Recent wins</th><th>Recent top 8</th>
                <th>All lists</th><th>All wins</th><th>Sources</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(body)}
            </tbody>
          </table>
        </div>"""


def render_sources(sources: list[dict]) -> str:
    items = []
    for i, src in enumerate(sources, start=1):
        n = len(src.get("ranks") or {})
        note = src.get("note") or ""
        items.append(
            f"""            <li>
              <a href="{html.escape(src['url'], quote=True)}" target="_blank" rel="noopener">{html.escape(src['name'])}</a>
              <span class="muted"> · {html.escape(src.get('when') or '')} · {n} ranks</span>
              <div class="muted">{html.escape(note)}</div>
            </li>"""
        )
    return f"""        <section class="tier-sources" id="sources">
          <div class="section-title">
            <h3>{len(sources)} public sources</h3>
            <div class="muted">OP17 pages weighted higher than leftover OP16 tables</div>
          </div>
          <ol>
{chr(10).join(items)}
          </ol>
        </section>"""


def page_html(board: str, table: str, sources_html: str, rows: list[dict], sources: list[dict]) -> str:
    title = "OP17 One Piece TCG tier list | One Piece Decklists"
    desc = (
        "Aggregated OP17 One Piece TCG tier list with leader pictures. "
        "Built from 20+ public meta pages plus the tournament lists on this site."
    )
    url = seo.canonical_url("tier-list.html")
    s_names = [r["name"] for r in rows if r["tier"] == "S"]
    intro = (
        "Early OP17 is still Mihawk's room, with Rocks D. Xebec as the new deck people copy "
        "and Sabo converting in the West. This board averages more than twenty public tier lists "
        "and meta reports, then leans on the lists actually hosted here: recent top eights, wins, "
        "and how often a leader is posting."
    )
    if s_names:
        intro = (
            f"{', '.join(s_names[:-1]) + ' and ' + s_names[-1] if len(s_names) > 1 else s_names[0]} "
            f"sit in S. {intro}"
        )
    items = [(r["name"], r["href"]) for r in rows]
    faq = seo.faq_jsonld(
        [
            (
                "How is this One Piece TCG tier list built?",
                "It averages 20+ public OP17 tier lists, metagame reports, and tournament tables, then cross-checks recent wins and top eights on One Piece Decklists.",
            ),
            (
                "What format is the tier list?",
                "Standard constructed OP17, The World's Strongest Warriors, after the 28 August 2026 English release.",
            ),
            (
                "Why is Green Mihawk still S tier?",
                "Public meta pages still give Mihawk the largest OP17 top-cut share, and this site has more recent Mihawk lists and top eights than any other leader.",
            ),
        ]
    )
    head = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        "  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />\n"
        f"  <title>{html.escape(title)}</title>\n"
        f"  <meta name=\"description\" content=\"{html.escape(desc)}\" />\n"
        f"  <link rel=\"stylesheet\" href=\"/css/site.css?v={CSS_VER}\" />\n"
        f"  <link rel=\"canonical\" href=\"{html.escape(url, quote=True)}\" />\n"
        f"{seo.google_head_tags(url)}"
        f"{seo.social_tags(title, desc, url, seo.DEFAULT_OG)}"
        f"{seo.breadcrumb_jsonld([('Home', '/'), ('Tier List', '/tier-list.html')])}"
        f"{seo.jsonld_script(seo.collection_jsonld(title=title, desc=desc, url=url, items=items))}"
        f"{seo.jsonld_script(faq)}"
        "</head>\n"
    )
    return f"""{head}<body>
  <div class="wrap">
    <header>
      <a class="brand" href="/">
        {seo.BRAND_LOGO_HTML}
        <div>
          <h1>One Piece Decklists</h1>
          <div class="subtitle">OPTCG decklists</div>
        </div>
      </a>
{seo.primary_nav_html(current="tier")}
    </header>
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Tier List</div>
        <h2>OP17 tier list</h2>
        <p>{html.escape(intro)}</p>
        <p class="muted">Updated {date.today().isoformat()}. Leader pictures link to the 50-card lists on this site.</p>
        <div class="tier-board" aria-label="OP17 leader tier list">
{board}
        </div>
{table}
{sources_html}
        <section class="faq" id="faq">
          <div class="section-title">
            <h3>How to read it</h3>
            <div class="muted">Short answers</div>
          </div>
          <details open>
            <summary>How is this aggregated?</summary>
            <p>Each public page casts a vote (S through D). Current OP17 reports weigh more than leftover OP16 tables. This site's recent wins and top eights are a vote of their own, not a replacement for the others.</p>
          </details>
          <details>
            <summary>Where are the lists?</summary>
            <p>Tap a leader picture. Recent tables also live on <a href="/#recent">the homepage</a> and the <a href="/format.html">format</a> page.</p>
          </details>
        </section>
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


def patch_nav(text: str, *, current: bool = False) -> str:
    m = re.search(r'(<nav aria-label="Primary">)(.*?)(</nav>)', text, re.S)
    if not m:
        return text
    inner = m.group(2)
    link = '        <a href="/tier-list.html"'
    if current:
        link += ' aria-current="page"'
    else:
        # drop leftover aria-current if this is not the tier page
        pass
    link += ">Tier List</a>\n"
    inner = re.sub(r"[ \t]*<a href=\"/tier-list.html\"[^>]*>Tier List</a>\s*", "", inner)
    rest = inner.lstrip("\n")
    if rest and not rest.startswith("        "):
        rest = "        " + rest.lstrip()
    new_inner = "\n" + link + rest
    if not rest.endswith("\n") and "\n" in rest:
        new_inner = "\n" + link + rest
    return text[: m.start(2)] + new_inner + text[m.end(2) :]


def patch_footer(text: str) -> str:
    foot = re.search(r"<footer>(.*?)</footer>", text, re.S)
    if not foot:
        return text
    inner = foot.group(1)
    copy = re.search(r"©[^\n]+", inner)
    copy_line = copy.group(0).strip() if copy else (
        "© <span id=\"year\"></span> One Piece Decklists - Built with community in mind."
    )
    # Keep extra disclosure lines (Amazon) that are not the link row.
    extras = []
    for line in inner.splitlines():
        s = line.strip()
        if not s or s.startswith("©") or s.startswith("<a ") or s.startswith("·"):
            continue
        if "id=\"year\"" in s:
            continue
        extras.append(s)
    hrefs = re.findall(r"<a href=\"([^\"]+)\"([^>]*)>([^<]+)</a>", inner)
    links = []
    seen = set()
    ordered = [("/tier-list.html", "Tier List", "")]
    for href, extra, label in hrefs:
        if href == "/tier-list.html":
            continue
        ordered.append((href, label, extra))
    for href, label, extra in ordered:
        key = (href, label)
        if key in seen:
            continue
        seen.add(key)
        links.append(f"<a href=\"{href}\"{extra}>{label}</a>")
    link_row = " · ".join(links)
    parts = ["    <footer>"]
    if copy_line:
        parts.append("      " + copy_line)
    for extra in extras:
        parts.append("      " + extra)
    if link_row:
        parts.append("      " + link_row)
    parts.append("    </footer>")
    rebuilt = "\n".join(parts)
    return text[: foot.start()] + rebuilt + text[foot.end() :]


def patch_home_tile(text: str) -> str:
    if "home-big-tier" in text:
        return text
    needle = '        <nav class="home-big3" aria-label="Main sections">\n'
    if needle not in text:
        return text
    return text.replace(needle, needle + HOME_TIER_TILE, 1)


def patch_css_ver(text: str) -> str:
    return re.sub(r'href="/css/site\.css(?:\?[^"]*)?"', f'href="/css/site.css?v={CSS_VER}"', text)


def patch_all_pages() -> int:
    changed = 0
    for p in public_html():
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text()
        orig = text
        current = rel == "tier-list.html"
        text = patch_nav(text, current=current)
        text = patch_footer(text)
        if rel == "index.html":
            text = patch_home_tile(text)
            text = patch_css_ver(text)
        if rel in ("format.html", "guides/index.html", "guides/one-piece-tcg-meta.html", "search.html"):
            text = patch_css_ver(text)
        if text != orig:
            p.write_text(text)
            changed += 1
    return changed


def patch_sitemap() -> None:
    path = ROOT / "sitemap-core.xml"
    text = path.read_text()
    loc = "https://onepiecedecklists.com/tier-list.html"
    today = date.today().isoformat()
    row = f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n"
    if loc in text:
        text = re.sub(
            rf"  <url><loc>{re.escape(loc)}</loc><lastmod>[^<]*</lastmod></url>\n",
            row,
            text,
        )
    else:
        text = text.replace("</urlset>", row + "</urlset>")
    path.write_text(text)


def main() -> None:
    stats = site_stats()
    sources, by_id = aggregate(stats)
    rows = list(by_id.values())
    payload = {
        "updated": date.today().isoformat(),
        "recent_from": RECENT_FROM,
        "source_count": len(sources),
        "leaders": rows,
        "sources": [
            {
                "id": s["id"],
                "name": s["name"],
                "url": s["url"],
                "when": s.get("when"),
                "weight": s["weight"],
                "note": s.get("note"),
                "ranks": s.get("ranks") or {},
            }
            for s in sources
        ],
    }
    (ROOT / "data/tier-list.json").write_text(json.dumps(payload, indent=2) + "\n")
    board = render_board(rows)
    table = render_table(rows)
    sources_html = render_sources(sources)
    (ROOT / "tier-list.html").write_text(page_html(board, table, sources_html, rows, sources))
    changed = patch_all_pages()
    patch_sitemap()
    print("sources", len(sources))
    print("leaders on board", len(rows))
    for letter in "SABCD":
        names = [r["name"] for r in rows if r["tier"] == letter]
        print(letter, ",", ", ".join(names) if names else "(empty)")
    print("patched html", changed)


if __name__ == "__main__":
    main()
