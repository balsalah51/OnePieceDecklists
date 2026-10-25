#!/usr/bin/env python3
"""Write the weekly meta note and the matchup notes from hosted data."""

from __future__ import annotations

import html
import importlib.util
import json
import re
from pathlib import Path

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def pretty_date(raw: str) -> str:
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw or "")
    if not match:
        return raw or ""
    month = MONTHS[int(match.group(2)) - 1]
    return f"{int(match.group(3))} {month} {match.group(1)}"

ROOT = Path("/workspace")
spec = importlib.util.spec_from_file_location("seocommon", ROOT / "scripts/seo_common.py")
seo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seo)


def shell(title: str, desc: str, path: str, crumb: str, body: str, current: str) -> str:
    url = seo.SITE + path
    nav = seo.primary_nav_html(current=current)
    crumbs = seo.breadcrumb_jsonld([("Home", "/"), ("Guides", "/guides/"), (crumb, path)])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}" />
  <link rel="canonical" href="{html.escape(url, quote=True)}" />
{seo.THEME_BOOT_SCRIPT}  <link rel="stylesheet" href="/css/site.css?v={seo.CSS_VER}" />
{seo.google_head_tags(url)}{seo.social_tags(title, desc, url, seo.DEFAULT_OG)}{crumbs}</head>
<body>
  <div class="wrap">
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {html.escape(crumb)}</div>
{body}
      </div>
    </main>
    <footer>
      © <span id="year"></span> One Piece Decklists - Fan site, not affiliated with Bandai.
      <a href="/tier-list.html">Tier List</a> · <a href="/guides/weekly-meta.html">Weekly meta</a> · <a href="/guides/matchups.html">Matchups</a> · <a href="/guides/">Guides</a> · <a href="/privacy.html">Privacy</a>
    </footer>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script src="/js/site.js?v={seo.JS_VER}"></script>
</body>
</html>
"""


def weekly_body(meta: dict, tier: dict) -> str:
    leaders = meta.get("home_leaders") or []
    pie = meta.get("pie") or []
    hole = meta.get("hole") or {}
    days = meta.get("window_days") or tier.get("recent_days") or ""
    label = meta.get("window_label") or ""
    if not label:
        label = (
            f"{pretty_date(str(tier.get('recent_from') or ''))} through "
            f"{pretty_date(str(tier.get('recent_through') or tier.get('updated') or ''))}"
        )
    top = leaders[:3]
    top_line = ", ".join(
        f"{html.escape(row['name'])} ({row['count']}"
        + (f", {html.escape(row['tier'])}" if row.get("tier") else "")
        + ")"
        for row in top
    ) or "the leaders on the homepage"
    share_bits = []
    for row in pie[:8]:
        if not row.get("name") or row["name"] == "Other":
            continue
        letter = f" {html.escape(row['tier'])}" if row.get("tier") else ""
        share_bits.append(f"{html.escape(row['name'])}{letter} {row['pct']}% ({row['count']})")
    share_line = ", ".join(share_bits)
    by_tier: dict[str, list[dict]] = {}
    for row in tier.get("leaders") or []:
        by_tier.setdefault(row.get("tier") or "?", []).append(row)
    s_rows = by_tier.get("S") or []
    s_line = ", ".join(
        f"<a href=\"{html.escape(row['href'])}\">{html.escape(row['name'])}</a> ({row['score']})"
        for row in s_rows
    )
    a_names = ", ".join(html.escape(row["name"]) for row in (by_tier.get("A") or [])[:6])
    hole_line = ""
    if hole:
        href = hole.get("href") or "/tier-list.html"
        hole_line = (
            f"<p>In the same window, <a href=\"{html.escape(href)}\">{html.escape(hole['name'])}</a> "
            f"has the best first-place rate among leaders with a full sample: {hole['wins']} firsts from "
            f"{hole['lists']} placed lists ({hole['win_pct']}%). That number is firsts divided by placed lists "
            f"on this site. It is not a game win rate.</p>"
        )
    updated = html.escape(pretty_date(str(tier.get("updated") or "")))
    sources = tier.get("source_count") or 0
    return f"""        <h2>Weekly meta</h2>
        <p>Week of {updated}. This note uses the same hosted lists and the same tier letters as the <a href="/tier-list.html">tier list</a> ({sources} published sources, rolling {html.escape(str(days))} days, {html.escape(label)}). It is not a copy of the Limitless or OPTCG.GG metagame page.</p>
        <section style="margin-top:22px">
          <div class="section-title"><h3>What the window is playing</h3><div class="muted">{html.escape(label)}</div></div>
          <p>The homepage leaders in that window are {top_line}. An older chart counted only the newest 200 lists, and a separate pie counted only lists that played an OP17 card. Mihawk lists often play no OP17 card, so that pie left him off a page that still called him S tier. Both views now count every hosted list in the rolling window.</p>
          <p>Share of the {meta.get('pie_lists') or 0} lists in the window: {share_line}.</p>
          {hole_line}
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Where that sits on the tier list</h3><div class="muted">Same letters as the board</div></div>
          <p>S tier on the {updated} list: {s_line}. A tier still includes {a_names}. The letters are the tier list's letters. The share chart does not assign a second grade.</p>
          <p>OP09 Nico Robin and EB05 Nico Robin, OP15 Enel and OP05 Enel, and OP17 Shanks and OP09 Shanks are different cards. The labels on this page use the set code so they are not the same leader.</p>
          <p>Large events are marked on the <a href="/#featured">featured results</a> and on <a href="/recent.html">recent lists</a>. A regional or championship outranks a Rumble or Chinoize cup when both are top cuts. Online cups stay in the list. They just stop looking like the headline.</p>
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>What to bring</h3><div class="muted">From the counts above</div></div>
          <ul class="guide-list">
            <li>If the room looks like this {html.escape(str(days))}-day window, pack a plan for the three names at the top before you tech for a leader who is quiet in it.</li>
            <li>If you want the season's consensus instead of this week's cups, start with the S tier and the <a href="/guides/matchups.html">matchup notes</a>.</li>
            <li>Pairing counts we have actually totaled live on the <a href="/guides/op17-mihawk-matchups.html">Mihawk matchup page</a>. This note does not invent a new win-rate table.</li>
          </ul>
        </section>
"""


def matchup_body() -> str:
    return """        <h2>Matchup notes</h2>
        <p>Short notes on how the leaders people keep registering actually play into each other. Leader text is the printed effect. The only pairing table on this site with counted games is <a href="/guides/op17-mihawk-matchups.html">which decks beat Mihawk</a>. Everything else here is a play pattern, not a win rate.</p>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Mihawk into Slash</h3><div class="muted">OP14-020</div></div>
          <p>Green Mihawk is 5 life / 5000 and gains +1000 power when the opposing leader is Slash. <a href="/decklists/rocks-d-xebec.html">Rocks D. Xebec</a> is Slash, so Mihawk is a 6000 leader in that seat before any DON!!. Once per turn, with a 5-cost Character in play, he can rest one of his cards, set up to three DON!! active, and then he cannot play more Characters that turn. The plan is play the body, untap DON!!, and spend them on events and attacks.</p>
          <p>The counted games are on the Mihawk page: across that write-up he is favored into Rocks and behind into Robin, Ace, and Sabo. Decks that beat him race life or present threats his rest does not answer. Decks that lose try to win a rest war.</p>
        </section>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Rocks into the rest of the room</h3><div class="muted">OP17-039</div></div>
          <p><a href="/decklists/rocks-d-xebec.html">Rocks</a> attacks, may trash a card, and draws two if the revealed card is Rocks Pirates. The list is a type deck, so the attack is the search. Curve, keeps, and the Slash problem versus Mihawk are on the <a href="/guides/rocks-d-xebec-strategy.html">Rocks strategy page</a>.</p>
          <p>Into leaders who are not taxing his Slash attribute, the game is whether he finds the even or odd line and still has the 10-cost Xebec. Into removal that clears the 6- and 7-cost bodies, he has to attack again and hope the top deck replaces them. He does not have a built-in answer to a wide board of 12-cost blockers.</p>
        </section>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Sabo</h3><div class="muted">OP13-004</div></div>
          <p><a href="/decklists/sabo.html">Sabo</a> loses 1000 power while you have 4 or more life, and gives your leader and Characters +1000 once an 8-cost Character is in play. Early he is a 4000 leader if you are still at high life. The turn the 8-cost sticks, the whole board gets bigger. That is why the matchup is about sticking one big body, not about attacking with the leader on turn one. Curve and mulligan: <a href="/guides/sabo-strategy.html">Sabo strategy</a>.</p>
          <p>Into Mihawk he is one of the three decks the pairing page has ahead. Into a pure race he has to spend a turn on the 8-cost before the power buff exists, so a 4-life aggro leader can take the life he was trying to sit on.</p>
        </section>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Luffy &amp; Ace</h3><div class="muted">ST30-001</div></div>
          <p><a href="/decklists/luffy-ace.html">Luffy &amp; Ace</a> is 4 life / 6000. If you have a Character with 7000 or more base power, the leader loses 2000 power. On the opponent's turn, Portgas D. Ace and Monkey D. Luffy cards gain +3000 power. The deck hits hard and defends on the opponent's turn, then gets worse at blocking once the big bodies are down because the leader shrinks. Four life is the clock. It is the leader to race with, and the leader that struggles once the opponent can ignore a 4000 body and hit life twice.</p>
        </section>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Black Luffy and Kaido</h3><div class="muted">OP17-079 and OP17-058</div></div>
          <p><a href="/decklists/monkey-d-luffy.html">Black Luffy</a> gives every one of your Characters with a cost of 12 or more Blocker. One rested 12-cost can catch a single attack. The way through is removal, or a wider swing than one blocker can take. Racing the leader before the 12s land is the other plan. Leaving two 12s up and attacking one at a time is how the game stalls.</p>
          <p><a href="/decklists/kaido.html">Kaido</a> can spend one DON!! when he attacks, or when your leader or a Character attacks him, to give one of your opponent's Characters −2000 power for the turn. He answers a rested attacker and he trims a blocker on his own swing. Power reduction is the whole trick. A leader who does not need to attack with Characters, or who replaces the body he just shrunk, is the awkward seat.</p>
        </section>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Read next</h3></div>
          <ul class="guide-list">
            <li><a href="/guides/weekly-meta.html">This week's meta note</a></li>
            <li><a href="/guides/op17-mihawk-matchups.html">Counted Mihawk pairings</a></li>
            <li><a href="/guides/portgas-d-ace-strategy.html">Portgas D. Ace strategy</a></li>
            <li><a href="/guides/nico-robin-strategy.html">Nico Robin strategy</a></li>
            <li><a href="/tier-list.html">Tier list</a></li>
          </ul>
        </section>
"""


def main() -> None:
    meta = json.loads((ROOT / "data/home-meta.json").read_text())
    tier = json.loads((ROOT / "data/tier-list.json").read_text())
    weekly = shell(
        "Weekly OPTCG meta | One Piece Decklists",
        "Short weekly note on which OPTCG leaders the hosted lists are actually playing, and how that compares with the tier list.",
        "/guides/weekly-meta.html",
        "Weekly meta",
        weekly_body(meta, tier),
        "weekly",
    )
    matchups = shell(
        "OPTCG matchup notes | One Piece Decklists",
        "Matchup notes for Rocks, Mihawk, Sabo, Luffy & Ace, Black Luffy, and Kaido, from printed leader text and the Mihawk pairings counted on this site.",
        "/guides/matchups.html",
        "Matchup notes",
        matchup_body(),
        "matchups",
    )
    (ROOT / "guides/weekly-meta.html").write_text(weekly)
    (ROOT / "guides/matchups.html").write_text(matchups)
    print("wrote weekly meta and matchups")


if __name__ == "__main__":
    main()
