#!/usr/bin/env python3
"""Build crawlable OPTCG topic and character pages plus a sitemap.

These pages are not in the primary nav. They exist so search engines can
find One Piece TCG / OPTCG / Bandai terms and character names, then route
people to real decklists. They are normal public HTML, not cloaked or hidden.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"

LEADERS = [
    ("Edward Newgate", "/decklists/op17/edward-newgate.html", "OP17 Red Whitebeard"),
    ("Shanks", "/decklists/op17/shanks.html", "OP17 Green Red-Haired"),
    ("Rocks D. Xebec", "/decklists/op17/rocks-d-xebec.html", "OP17 Blue Rocks Pirates"),
    ("Kaido", "/decklists/op17/kaido.html", "OP17 Purple Animal Kingdom"),
    ("Monkey D. Luffy", "/decklists/op17/monkey-d-luffy.html", "OP17 Black Straw Hat / Elbaph"),
    ("Charlotte Linlin", "/decklists/op17/charlotte-linlin.html", "OP17 Yellow Big Mom"),
    ("RG Luffy", "/decklists/rg-luffy.html", "Red/Green Monkey D. Luffy"),
    ("Nami", "/decklists/nami.html", "Blue/Yellow Nami"),
    ("Mihawk", "/decklists/mihawk.html", "Green Dracule Mihawk"),
    ("Portgas D. Ace", "/decklists/portgas-d-ace.html", "OP16 Red Whitebeard Pirates"),
    ("OP13 Ace", "/decklists/op13-ace.html", "OP13 Red/Blue Portgas D. Ace"),
    ("Imu", "/decklists/imu.html", "OP13 Black Mary Geoise"),
    ("Enel", "/decklists/enel.html", "OP15 Purple Sky Island"),
    ("Charlotte Katakuri", "/decklists/charlotte-katakuri.html", "OP11 Purple Big Mom Pirates"),
    ("GB Luffy", "/decklists/gb-luffy.html", "OP16 Green/Blue Impel Down Luffy"),
    ("Blackbeard", "/decklists/blackbeard.html", "OP16 Black/Yellow Marshall D. Teach"),
    ("Rosinante", "/decklists/rosinante.html", "OP12 Purple/Yellow Donquixote Rosinante"),
    ("Lucy", "/decklists/lucy.html", "OP15 Red/Blue Lucy"),
    ("Yamato", "/decklists/yamato.html", "OP16 Black Yamato"),
    ("Koby", "/decklists/koby.html", "OP11 Red/Black Koby"),
    ("Doffy", "/decklists/doffy.html", "OP14 Purple Donquixote Doflamingo"),
    ("Buggy", "/decklists/buggy.html", "OP16 Blue Buggy"),
    ("Sengoku", "/decklists/sengoku.html", "OP16 Purple Sengoku"),
    ("UP Luffy", "/decklists/up-luffy.html", "OP11 Blue/Purple Monkey D. Luffy"),
    ("Charlotte Pudding", "/decklists/charlotte-pudding.html", "OP08 Purple/Yellow Charlotte Pudding"),
    ("Sabo", "/decklists/sabo.html", "OP13 Red/Black Sabo"),
    ("Nico Robin", "/decklists/nico-robin.html", "OP09 Purple/Yellow Nico Robin"),
    ("Gecko Moria", "/decklists/gecko-moria.html", "OP14 Black/Yellow Gecko Moria"),
    ("Boa Hancock", "/decklists/boa-hancock.html", "OP14 Blue/Yellow Boa Hancock"),
    ("Koala", "/decklists/koala.html", "OP12 Black/Yellow Koala"),
    ("OP09 Shanks", "/decklists/op09-shanks.html", "OP09 Red Shanks"),
    ("OP05 Enel", "/decklists/op05-enel.html", "OP05 Yellow Enel"),
    ("ST10 Luffy", "/decklists/st10-luffy.html", "ST10 Red/Purple Monkey D. Luffy"),
    ("OP09 Luffy", "/decklists/op09-luffy.html", "OP09 Purple/Black Monkey D. Luffy"),
    ("ST13 Luffy", "/decklists/st13-luffy.html", "ST13 Black/Yellow Monkey D. Luffy"),
    ("Kuzan", "/decklists/kuzan.html", "OP12 Blue Kuzan"),
    ("Belo Betty", "/decklists/belo-betty.html", "OP05 Red/Yellow Belo Betty"),
    ("Jewelry Bonney", "/decklists/jewelry-bonney.html", "EB04 Red/Yellow Jewelry Bonney"),
    ("Eustass Kid", "/decklists/eustass-kid.html", "OP10 Yellow Eustass Kid"),
    ("Foxy", "/decklists/foxy.html", "OP07 Purple Foxy"),
    ("ST13 Sabo", "/decklists/st13-sabo.html", "ST13 Red/Yellow Sabo"),
    ("Sakazuki", "/decklists/sakazuki.html", "OP05 Blue/Black Sakazuki"),
    ("OP05 Luffy", "/decklists/op05-luffy.html", "OP05 Purple Monkey D. Luffy"),
    ("Rob Lucci", "/decklists/rob-lucci.html", "OP07 Black Rob Lucci"),
    ("Trafalgar Law", "/decklists/trafalgar-law.html", "OP10 Green/Yellow Trafalgar Law"),
    ("OP06 Yamato", "/decklists/op06-yamato.html", "OP06 Green/Yellow Yamato"),
    ("ST14 Luffy", "/decklists/st14-luffy.html", "ST14 Black Monkey D. Luffy"),
    ("EB02 Luffy", "/decklists/eb02-luffy.html", "EB02 Green/Purple Monkey D. Luffy"),
    ("Jinbe", "/decklists/jinbe.html", "OP14 Blue Jinbe"),
    ("Sanji", "/decklists/sanji.html", "OP12 Blue/Purple Sanji"),
    ("Luffy & Ace", "/decklists/luffy-ace.html", "ST30 Red/Green Luffy & Ace"),
]


def chrome(title: str, description: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}" />
  <link rel="canonical" href="{html.escape(SITE)}" />
  <link rel="stylesheet" href="/css/site.css?v=seo-links" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1074015774205047" crossorigin="anonymous"></script>
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
      <nav aria-label="Primary">
        <a href="/tier-list.html">Tier List</a>
        <a href="/#recent">Recent lists</a>
        <a href="/decklists/op17.html">Leaders</a>
        <a href="/format.html">Format</a>
        <a href="https://en.onepiece-cardgame.com/events/" target="_blank" rel="noopener">Events</a>
        <a href="/guides/">Guides</a>
        <a href="/shop/">Shop</a>
        <a href="/search.html">Search</a>
        <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">Discord</a>
      </nav>
    </header>
    <main class="single">
      <div class="card hero">
{body}
      </div>
    </main>
    <footer>
      © <span id="year"></span> One Piece Decklists - Fan site for the Bandai ONE PIECE CARD GAME (OPTCG). Not affiliated with Bandai.
      <a href="/tier-list.html">Tier List</a> · <a href="/guides/">Guides</a> · <a href="/decklists/op17.html">Leaders</a> · <a href="/format.html">Format</a> · <a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a>
    </footer>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script src="/js/site.js?v=amazon-shop"></script>
</body>
</html>
"""


def leader_list() -> str:
    rows = []
    for name, href, meta in LEADERS:
        rows.append(
            f"""            <li>
              <a class="item" href="{html.escape(href)}">
                <div>
                  <div style="font-weight:700">{html.escape(name)}</div>
                  <div class="muted" style="font-size:13px">{html.escape(meta)}</div>
                </div>
                <div class="link">Lists →</div>
              </a>
            </li>"""
        )
    return "\n".join(rows)


TOPICS = [
    {
        "slug": "one-piece",
        "title": "One Piece | OPTCG decklists",
        "h2": "One Piece",
        "desc": "One Piece Card Game decklists and leader pages for the Bandai OPTCG.",
        "copy": "One Piece Decklists is a fan hub for the One Piece Card Game. Use it to open OP17 and current-format OPTCG decklists, then jump to official Bandai events when you want to play.",
    },
    {
        "slug": "one-piece-tcg",
        "title": "One Piece TCG decklists | OPTCG",
        "h2": "One Piece TCG",
        "desc": "One Piece TCG (OPTCG) decklists for OP17 leaders from the Bandai card game.",
        "copy": "The One Piece TCG, also called OPTCG or the ONE PIECE CARD GAME, is Bandai’s constructed format. This site keeps 50-card lists for the leaders people are actually registering.",
    },
    {
        "slug": "optcg",
        "title": "OPTCG decklists | One Piece Card Game",
        "h2": "OPTCG",
        "desc": "OPTCG is the One Piece Card Game from Bandai. Browse leader decklists here.",
        "copy": "OPTCG is the short name players use for the Bandai One Piece Card Game. If you searched OPTCG decklist, start with the OP17 leader pages and open any 50-card list.",
    },
    {
        "slug": "one-piece-card-game",
        "title": "ONE PIECE CARD GAME decklists | Bandai",
        "h2": "ONE PIECE CARD GAME",
        "desc": "Bandai ONE PIECE CARD GAME decklists, leaders, and tournament lists.",
        "copy": "The official English name is ONE PIECE CARD GAME. Bandai runs store play, Treasure Cups, and championships. This fan site stores decklists so you can copy a list before you go.",
    },
    {
        "slug": "bandai",
        "title": "Bandai One Piece TCG | OPTCG decklists",
        "h2": "Bandai",
        "desc": "Bandai publishes the One Piece Card Game. Find OPTCG decklists on One Piece Decklists.",
        "copy": "Bandai Namco makes the One Piece Card Game. Official kits, events, and rules live on Bandai’s site. Decklists on this page are community copies for studying lists, not official pairings.",
    },
    {
        "slug": "bandai-one-piece-card-game",
        "title": "Bandai ONE PIECE CARD GAME | OPTCG",
        "h2": "Bandai ONE PIECE CARD GAME",
        "desc": "Decklists for the Bandai ONE PIECE CARD GAME, including OP17 leaders.",
        "copy": "Search traffic often uses the full phrase Bandai ONE PIECE CARD GAME. That is the same OPTCG format these leader pages cover: Red Newgate, Green Shanks, Blue Rocks, Purple Kaido, Black Luffy, Yellow Linlin, plus RG Luffy, Nami, Mihawk, OP16 Ace, Enel, and Katakuri.",
    },
    {
        "slug": "op17",
        "title": "OP17 The World's Strongest Warriors | OPTCG",
        "h2": "OP17",
        "desc": "OP17 The World's Strongest Warriors leaders and decklists for the One Piece TCG.",
        "copy": "OP-17 The World's Strongest Warriors is the current English booster. The six OP17 leaders on this site are Edward Newgate, Shanks, Rocks D. Xebec, Kaido, Monkey D. Luffy, and Charlotte Linlin.",
    },
    {
        "slug": "optcg-decklists",
        "title": "OPTCG decklists | 50-card One Piece TCG lists",
        "h2": "OPTCG decklists",
        "desc": "50-card OPTCG decklists from Limitless events and YouTube profiles.",
        "copy": "Every list page on One Piece Decklists is a full 50-card OPTCG deck: leader, characters, events, and stages. Open a leader, then open a row for the actual list.",
    },
    {
        "slug": "one-piece-tcg-meta",
        "title": "One Piece TCG meta | OP17 OPTCG",
        "h2": "One Piece TCG meta",
        "desc": "OP17 OPTCG meta leaders with tournament and community decklists.",
        "copy": "The early OP17 meta is still moving. Rocks, Kaido, Black Luffy, Linlin, Shanks, RG Luffy, Nami, Mihawk, OP16 Ace, Enel, and Katakuri all have recent Limitless lists here. Newgate is mostly YouTube lists until more events post standings.",
    },
    {
        "slug": "op17-mihawk-matchups",
        "title": "Which decks beat OP17 Mihawk | OPTCG matchups",
        "h2": "OP17 Mihawk matchups",
        "desc": "OP17 Mihawk matchups from Limitless pairings: Robin, Ace, and Sabo beat green Dracule Mihawk. Rocks does not.",
        "copy": "Green Mihawk is the rest/control deck people call the OP17 problem. Limitless pairings in this window say Robin, Ace, and Sabo are the leaders that actually beat him; Rocks is a Mihawk-favored game.",
    },
    {
        "slug": "nico-robin-strategy",
        "title": "Nico Robin strategy | OP17 OPTCG",
        "h2": "Nico Robin strategy",
        "desc": "OP17 Nico Robin strategy: Purple/Yellow OP09-062 ramps with Triggers, then drops yellow Big Mom. Lists, curve, and the Mihawk matchup.",
        "copy": "Purple/Yellow OP09 Nico Robin is the Ohara ramp deck in OP17. Hosted lists splash yellow Big Mom; Limitless pairings say she is the volume answer to Mihawk.",
    },
    {
        "slug": "sabo-strategy",
        "title": "Sabo strategy | OP17 OPTCG",
        "h2": "Sabo strategy",
        "desc": "OP17 Sabo strategy: Red/Black OP13-004 plays Elbaph Straw Hats plus Loki. Curve, mulligan, tech, and the 52.1% Mihawk pairing.",
        "copy": "Red/Black OP13 Sabo is Elbaph midrange in OP17. Hosted lists play Saul and Loki to turn the 12-cost switch on; Limitless pairings have him slightly ahead of Mihawk.",
    },
    {
        "slug": "rocks-d-xebec-strategy",
        "title": "Rocks D. Xebec strategy | OP17 OPTCG",
        "h2": "Rocks D. Xebec strategy",
        "desc": "OP17 Rocks D. Xebec strategy: Blue OP17-039 even and odd Rocks Pirates curves, 10-cost Xebec, mulligan, tech, and the 33.6% Mihawk pairing.",
        "copy": "Blue OP17 Rocks D. Xebec is a Rocks Pirates type deck. Hosted lists curve Kyo into Newgate into Shiki, then 10-cost Xebec; Limitless pairings have Mihawk well ahead.",
    },
    {
        "slug": "portgas-d-ace-strategy",
        "title": "Portgas D. Ace strategy | OP17 OPTCG",
        "h2": "Portgas D. Ace strategy",
        "desc": "OP17 Portgas D. Ace strategy: Red OP16-001 Garp into Rush Whitebeard Pirates curve, mulligan, tech, and the 57.8% Mihawk pairing.",
        "copy": "Red OP16 Portgas D. Ace is the Rush Whitebeard leader in OP17, not red/blue OP13 Ace. Hosted lists play Garp and Moby Dick into Rush Newgate; Limitless pairings have him ahead of Mihawk.",
    },
    {
        "slug": "treasure-cup",
        "title": "Treasure Cup One Piece TCG | OPTCG lists",
        "h2": "Treasure Cup",
        "desc": "Treasure Cup is a Bandai One Piece TCG tournament series. Browse related OPTCG lists.",
        "copy": "Treasure Cup is Bandai’s year-round constructed series for the One Piece Card Game. Some lists on this site come from Limitless events in that same OPTCG constructed format.",
    },
    {
        "slug": "championship",
        "title": "One Piece TCG Championship | OPTCG",
        "h2": "Championship",
        "desc": "Bandai One Piece TCG Championship format uses constructed OPTCG decks.",
        "copy": "Championship events use the official Bandai constructed rules. The decklists here are 50-card OPTCG lists you can study before a regional, store championship, or locals.",
    },
    {
        "slug": "starter-decks",
        "title": "One Piece TCG starter decks | OPTCG ST lists",
        "h2": "Starter decks",
        "desc": "OPTCG starter-deck cards show up inside constructed 50-card lists.",
        "copy": "Bandai starter decks (ST) feed constructed OPTCG. You will see ST cards inside the 50-card lists on this site, mixed with booster cards from OP and EB sets.",
    },
    {
        "slug": "one-piece-card-game-decklist",
        "title": "One Piece Card Game decklist | OPTCG",
        "h2": "One Piece Card Game decklist",
        "desc": "Find a One Piece Card Game decklist for Bandai OPTCG leaders on this fan site.",
        "copy": "If you searched One Piece Card Game decklist, start here. Open a leader, then open a row for a full 50-card OPTCG list from Limitless events or YouTube profiles.",
    },
    {
        "slug": "optcg-deck-list",
        "title": "OPTCG deck list | Bandai One Piece TCG",
        "h2": "OPTCG deck list",
        "desc": "OPTCG deck list pages for OP17 and current-format Bandai One Piece TCG leaders.",
        "copy": "An OPTCG deck list on this site is always 50 cards plus a leader. Use the leader pages below, then copy the text list with card pictures on hover.",
    },
    {
        "slug": "one-piece-tcg-deck-list",
        "title": "One Piece TCG deck list | OPTCG",
        "h2": "One Piece TCG deck list",
        "desc": "One Piece TCG deck list hub for Bandai OPTCG constructed format.",
        "copy": "One Piece TCG deck list searches should land on real lists, not empty keyword pages. Every leader row here opens tournament or community 50-card lists.",
    },
    {
        "slug": "op-tcg",
        "title": "OP TCG | One Piece Card Game decklists",
        "h2": "OP TCG",
        "desc": "OP TCG is another name for the Bandai One Piece Card Game. Browse OPTCG lists here.",
        "copy": "Players type OP TCG, OPTCG, and One Piece TCG for the same Bandai game. This fan site keeps constructed lists for OP17 and a few current-format leaders.",
    },
    {
        "slug": "onepiece-tcg",
        "title": "Onepiece TCG | OPTCG decklists",
        "h2": "Onepiece TCG",
        "desc": "Onepiece TCG (One Piece TCG) decklists for the Bandai card game.",
        "copy": "Onepiece TCG is the same search as One Piece TCG. Bandai’s English name is ONE PIECE CARD GAME. The lists on this site are 50-card constructed OPTCG decks.",
    },
    {
        "slug": "bandai-namco",
        "title": "Bandai Namco One Piece TCG | OPTCG",
        "h2": "Bandai Namco",
        "desc": "Bandai Namco publishes the One Piece Card Game. Find OPTCG decklists here.",
        "copy": "Bandai Namco owns the ONE PIECE CARD GAME. Official products and events stay on Bandai’s site. This page only points at fan-copied OPTCG decklists.",
    },
    {
        "slug": "optcg-leaders",
        "title": "OPTCG leaders | One Piece TCG",
        "h2": "OPTCG leaders",
        "desc": "OPTCG leader pages for OP17 and current-format One Piece TCG decks.",
        "copy": "OPTCG leaders on this site: Edward Newgate, Shanks, Rocks D. Xebec, Kaido, Monkey D. Luffy, Charlotte Linlin, plus RG Luffy, Nami, Mihawk, OP16 Portgas D. Ace, OP13 Ace, Imu, Enel, and Charlotte Katakuri.",
    },
    {
        "slug": "one-piece-tcg-leaders",
        "title": "One Piece TCG leaders | OPTCG",
        "h2": "One Piece TCG leaders",
        "desc": "One Piece TCG leader list with links to 50-card OPTCG decklists.",
        "copy": "Each One Piece TCG leader has a color, life, and effect. Open a leader page for YouTube lists and Limitless tournament lists when those exist.",
    },
    {
        "slug": "constructed",
        "title": "One Piece TCG constructed | OPTCG 50-card",
        "h2": "Constructed",
        "desc": "Bandai One Piece TCG constructed format uses 50-card OPTCG decks.",
        "copy": "Constructed OPTCG is 50 cards plus a leader. Locals, Treasure Cups, and championships all use that rule. The lists here are copied in that format.",
    },
    {
        "slug": "locals",
        "title": "One Piece TCG locals | OPTCG lists",
        "h2": "Locals",
        "desc": "Store locals for the Bandai One Piece TCG use the same constructed OPTCG lists.",
        "copy": "Locals are weekly Bandai store events. Study a 50-card list here, then check the official events page for a shop near you.",
    },
    {
        "slug": "limitless",
        "title": "Limitless One Piece TCG lists | OPTCG",
        "h2": "Limitless",
        "desc": "Tournament OPTCG lists on this site are copied from Limitless Play events.",
        "copy": "Limitless Play is where many OPTCG events post standings. Tournament rows on this fan site link those 50-card lists. Card pictures still come from Limitless image hosting.",
    },
    {
        "slug": "red-optcg",
        "title": "Red One Piece TCG decks | OPTCG",
        "h2": "Red OPTCG",
        "desc": "Red One Piece TCG decks on this site start with OP17 Edward Newgate and OP16 Ace.",
        "copy": "Red OPTCG on this site is OP17 Edward Newgate / Whitebeard, OP16 Portgas D. Ace, OP13 Ace, plus red cards inside RG Luffy. Open those leader lists for 50-card decks.",
    },
    {
        "slug": "green-optcg",
        "title": "Green One Piece TCG decks | OPTCG",
        "h2": "Green OPTCG",
        "desc": "Green One Piece TCG decks: OP17 Shanks and Dracule Mihawk.",
        "copy": "Green OPTCG lists here are OP17 Shanks and green Mihawk. Both rest or control the board. Open a leader page for tournament and YouTube lists.",
    },
    {
        "slug": "blue-optcg",
        "title": "Blue One Piece TCG decks | OPTCG",
        "h2": "Blue OPTCG",
        "desc": "Blue One Piece TCG decks: OP17 Rocks D. Xebec and Nami.",
        "copy": "Blue OPTCG on this site is Rocks D. Xebec, the blue half of Nami, and red/blue OP13 Ace. Rocks is the main OP17 blue leader with recent Limitless lists.",
    },
    {
        "slug": "purple-optcg",
        "title": "Purple One Piece TCG decks | OPTCG",
        "h2": "Purple OPTCG",
        "desc": "Purple One Piece TCG decks: OP17 Kaido, Enel, and Katakuri.",
        "copy": "Purple OPTCG here is OP17 Kaido, OP15 Enel, and OP11 Charlotte Katakuri. Open those leader pages for tournament 50-card lists.",
    },
    {
        "slug": "black-optcg",
        "title": "Black One Piece TCG decks | OPTCG",
        "h2": "Black OPTCG",
        "desc": "Black One Piece TCG decks: OP17 Monkey D. Luffy and OP13 Imu.",
        "copy": "Black OPTCG on this site is OP17 Monkey D. Luffy / Elbaph and OP13 Imu / Five Elders. Open those leader pages for blockers, trash, and recent Limitless lists.",
    },
    {
        "slug": "yellow-optcg",
        "title": "Yellow One Piece TCG decks | OPTCG",
        "h2": "Yellow OPTCG",
        "desc": "Yellow One Piece TCG decks start with OP17 Charlotte Linlin.",
        "copy": "Yellow OPTCG here is OP17 Charlotte Linlin / Big Mom, plus the yellow half of Nami. Linlin has a stack of recent tournament lists.",
    },
    {
        "slug": "straw-hat-crew",
        "title": "Straw Hat Crew One Piece TCG | OPTCG",
        "h2": "Straw Hat Crew",
        "desc": "Straw Hat Crew OPTCG pages: Monkey D. Luffy, Nami, and related lists.",
        "copy": "Straw Hat Crew searches should reach Black OP17 Luffy, RG Luffy, and Nami. Those are the constructed OPTCG leaders tied to the crew on this site.",
    },
    {
        "slug": "red-hair-pirates",
        "title": "Red Hair Pirates One Piece TCG | OPTCG",
        "h2": "Red Hair Pirates",
        "desc": "Red Hair Pirates OPTCG lists live on the OP17 Shanks leader page.",
        "copy": "Red Hair Pirates / Red-Haired Pirates is the OP17 green Shanks package. Benn Beckman, Yasopp, Lucky Roux, and Rockstar searches should start on that leader page.",
    },
    {
        "slug": "whitebeard-pirates",
        "title": "Whitebeard Pirates One Piece TCG | OPTCG",
        "h2": "Whitebeard Pirates",
        "desc": "Whitebeard Pirates OPTCG lists live on OP17 Edward Newgate and OP16 Ace.",
        "copy": "Whitebeard Pirates OPTCG on this site is red OP17 Edward Newgate, red OP16 Portgas D. Ace, and red/blue OP13 Ace. Ace, Marco, Jozu, Izo, Vista, and Whitebeard searches belong there.",
    },
    {
        "slug": "rocks-pirates",
        "title": "Rocks Pirates One Piece TCG | OPTCG",
        "h2": "Rocks Pirates",
        "desc": "Rocks Pirates OPTCG lists live on the OP17 Rocks D. Xebec page.",
        "copy": "Rocks Pirates is the OP17 blue leader package. Rocks D. Xebec, Shakky, and God Valley names should open that constructed page.",
    },
    {
        "slug": "beast-pirates",
        "title": "Beast Pirates One Piece TCG | OPTCG",
        "h2": "Beast Pirates",
        "desc": "Beast Pirates / Animal Kingdom OPTCG lists live on OP17 Kaido.",
        "copy": "Beast Pirates OPTCG here is purple OP17 Kaido. King, Queen, Jack, Yamato, Ulti, and Page One searches should use that leader page.",
    },
    {
        "slug": "big-mom-pirates",
        "title": "Big Mom Pirates One Piece TCG | OPTCG",
        "h2": "Big Mom Pirates",
        "desc": "Big Mom Pirates OPTCG lists live on OP17 Charlotte Linlin and OP11 Katakuri.",
        "copy": "Big Mom Pirates OPTCG is yellow OP17 Charlotte Linlin and purple OP11 Charlotte Katakuri. Smoothie, Cracker, Perospero, and Big Mom searches belong there.",
    },
    {
        "slug": "four-emperors",
        "title": "Four Emperors One Piece TCG | OPTCG",
        "h2": "Four Emperors",
        "desc": "Four Emperors OPTCG leaders: Shanks, Kaido, Linlin, Luffy, and Whitebeard.",
        "copy": "The Four Emperors map onto several OPTCG leaders on this site: Shanks, Kaido, Charlotte Linlin, Monkey D. Luffy, and Edward Newgate.",
    },
    {
        "slug": "elbaph",
        "title": "Elbaph One Piece TCG | OPTCG",
        "h2": "Elbaph",
        "desc": "Elbaph OPTCG lists live on OP17 black Monkey D. Luffy.",
        "copy": "Elbaph / Elbaf OPTCG on this site is black OP17 Monkey D. Luffy. Loki, Harald, and giant-type cards show up in those 50-card lists.",
    },
    {
        "slug": "wano",
        "title": "Wano One Piece TCG | OPTCG",
        "h2": "Wano",
        "desc": "Wano names in the One Piece TCG often sit in Kaido, Luffy, and Newgate lists.",
        "copy": "Wano searches can start at purple Kaido, black Luffy, or red Newgate. Oden, Yamato, and the Beast Pirates are the usual OPTCG landing spots.",
    },
    {
        "slug": "marineford",
        "title": "Marineford One Piece TCG | OPTCG",
        "h2": "Marineford",
        "desc": "Marineford-era OPTCG names often land on Whitebeard and Luffy lists.",
        "copy": "Marineford searches should try Edward Newgate, OP16 Portgas D. Ace, and Monkey D. Luffy. Ace, Whitebeard, Garp, and the Admirals are linked from the character guide too.",
    },
]


# name, slug, blurb, related leader keys (index into LEADERS)
CHARACTERS = [
    ("Monkey D. Luffy", "monkey-d-luffy", "Straw Hat captain and the most-searched OPTCG name. Black OP17 Luffy, RG Luffy, green/blue OP16 Impel Down Luffy, and blue/purple UP Luffy (OP11-040) are constructed leaders here.", [4, 6, 14, 23]),
    ("Roronoa Zoro", "roronoa-zoro", "First mate and swordsman. Zoro cards show up in Mihawk and RG Luffy OPTCG lists.", [8, 6]),
    ("Nami", "nami", "Straw Hat navigator. Nami is the blue/yellow OPTCG leader; green Shanks lists also play Nami cards.", [7, 1]),
    ("Usopp", "usopp", "Sniper of the Straw Hats. Usopp cards appear in RG Luffy and Black Luffy OPTCG decklists.", [6, 4]),
    ("Sanji", "sanji", "Cook of the Thousand Sunny. Red Sanji is a staple in Edward Newgate Whitebeard lists.", [0, 6]),
    ("Tony Tony Chopper", "tony-tony-chopper", "Doctor of the crew. Chopper cards show up in Black Elbaph Luffy OPTCG lists.", [4]),
    ("Nico Robin", "nico-robin", "Archaeologist of the Straw Hats. Robin cards appear in Black Luffy and other OPTCG midrange lists.", [4, 6]),
    ("Franky", "franky", "Shipwright. Franky is a Straw Hat name searchers type; start from the Luffy leader pages.", [4, 6]),
    ("Brook", "brook", "Soul King of the Straw Hats. Brook cards appear in some RG Luffy OPTCG lists.", [6, 4]),
    ("Jinbe", "jinbe", "Helmsman and Fish-Man. Jinbe cards show up in Black Luffy and other OPTCG lists.", [4]),
    ("Shanks", "shanks", "Red-Haired Emperor and OP17 green leader. This is one of the main OPTCG pages on the site.", [1]),
    ("Benn Beckman", "benn-beckman", "First mate of the Red Hair Pirates. Look at the OP17 Shanks OPTCG lists.", [1]),
    ("Lucky Roux", "lucky-roux", "Red Hair Pirate. Shanks OPTCG decklists are the matching constructed pages.", [1]),
    ("Yasopp", "yasopp", "Usopp’s father and Red Hair sniper. Open the Shanks leader page for OPTCG lists.", [1]),
    ("Rockstar", "rockstar", "Red Hair Pirate who shows up as a card in green Shanks OPTCG lists.", [1]),
    ("Edward Newgate", "edward-newgate", "Whitebeard, OP17 red leader. YouTube OPTCG lists live on his page while Limitless standings catch up.", [0]),
    ("Whitebeard", "whitebeard", "The same person as Edward Newgate. Search Whitebeard OPTCG and you want the red OP17 leader page.", [0]),
    ("Portgas D. Ace", "portgas-d-ace", "Fire Fist Ace. OP16 red Ace and OP13 red/blue Ace are both constructed leaders here; Ace cards also show up in Edward Newgate lists.", [9, 10, 0]),
    ("Marco", "marco", "Phoenix of the Whitebeard Pirates. Marco is a common name in red Newgate and Ace OPTCG lists.", [0, 9, 10]),
    ("Jozu", "jozu", "Diamond Jozu of Whitebeard’s crew. See the Newgate OPTCG decklists.", [0]),
    ("Izo", "izo", "Whitebeard Pirate and gunner. Izo cards appear in OP17 Newgate lists.", [0]),
    ("Thatch", "thatch", "Whitebeard Pirate. Newgate OPTCG pages are the right constructed lists.", [0]),
    ("Vista", "vista", "Flower Sword Vista. Whitebeard OPTCG lists are under Edward Newgate.", [0]),
    ("Gol D. Roger", "gol-d-roger", "Pirate King. Roger cards show up as finishers in some Newgate and Rocks OPTCG lists.", [0, 2]),
    ("Silvers Rayleigh", "silvers-rayleigh", "Dark King and Roger’s first mate. Start from Roger-adjacent OPTCG lists on Newgate and Rocks.", [0, 2]),
    ("Kouzuki Oden", "kouzuki-oden", "Samurai of Wano. Oden cards appear in red Newgate OPTCG lists.", [0]),
    ("Rocks D. Xebec", "rocks-d-xebec", "Captain of the Rocks Pirates and OP17 blue leader. One of the most-played OPTCG decks right now.", [2]),
    ("Kaido", "kaido", "King of the Beasts and OP17 purple leader. Purple Kaido has a full stack of OPTCG tournament lists.", [3]),
    ("King", "king", "All-Star of the Beasts. King cards are common in purple Kaido OPTCG lists.", [3]),
    ("Queen", "queen", "All-Star of the Beasts. Queen cards show up next to Kaido in purple OPTCG lists.", [3]),
    ("Jack", "jack", "Drought Jack of the Beasts. See purple Kaido OPTCG decklists.", [3]),
    ("Yamato", "yamato", "Oden’s name successor. Black OP16 Yamato is the constructed Wano leader; Yamato cards also appear in Kaido lists.", [18, 3]),
    ("Ulti", "ulti", "Tobi Roppo. Ulti & Page One show up in purple Kaido OPTCG lists.", [3]),
    ("Page One", "page-one", "Tobi Roppo. Paired with Ulti in some Kaido OPTCG decklists.", [3]),
    ("Charlotte Linlin", "charlotte-linlin", "Big Mom and OP17 yellow leader. Yellow Linlin OPTCG lists are on her leader page.", [5]),
    ("Big Mom", "big-mom", "The same person as Charlotte Linlin. Yellow OPTCG lists live on the Linlin page.", [5]),
    ("Charlotte Katakuri", "charlotte-katakuri", "Sweet Commander. Purple OP11 Katakuri is a constructed leader here; purple/yellow Pudding and yellow Linlin lists also play Katakuri cards.", [13, 24, 5]),
    ("Charlotte Smoothie", "charlotte-smoothie", "Sweet Commander. Open the Linlin OPTCG page for yellow lists.", [5]),
    ("Charlotte Cracker", "charlotte-cracker", "Thousand Arms Cracker. Purple/Yellow Pudding and yellow Linlin OPTCG are the matching leaders.", [24, 5]),
    ("Charlotte Perospero", "charlotte-perospero", "First son of Big Mom. See Pudding and Linlin OPTCG decklists.", [24, 5]),
    ("Dracule Mihawk", "dracule-mihawk", "World’s Strongest Swordsman and green OPTCG leader. Mihawk has tournament lists on this site.", [8]),
    ("Trafalgar Law", "trafalgar-law", "Surgeon of Death. Purple/Yellow Rosinante is the Law-partner leader; Law cards also appear in RG Luffy lists.", [16, 6, 8]),
    ("Eustass Kid", "eustass-kid", "Captain of the Kid Pirates. Kid is a common OPTCG search; start from the OP17 hub and RG Luffy.", [6, 4]),
    ("Killer", "killer", "Kid Pirates combatant. Related OPTCG lists sit with supernova packages on RG Luffy.", [6]),
    ("Jewelry Bonney", "jewelry-bonney", "Supernova captain. Bonney names often land next to other supernova OPTCG lists.", [6]),
    ("Marshall D. Teach", "marshall-d-teach", "Blackbeard. Black/Yellow OP16 Marshall D. Teach is the constructed leader on this site.", [15]),
    ("Blackbeard", "blackbeard", "Same person as Marshall D. Teach. Open the OP16 Blackbeard leader page for 50-card lists.", [15]),
    ("Buggy", "buggy", "Warlord and Emperor. Blue OP16 Buggy is the constructed Impel Down leader.", [21, 14]),
    ("Crocodile", "crocodile", "Former Warlord. No Crocodile leader page yet; the OP17 decklist hub is the start.", [2, 5]),
    ("Donquixote Doflamingo", "donquixote-doflamingo", "Heavenly Demon. Purple OP14 Doffy is the constructed leader; not blue OP01-060 Doffy.", [20, 16]),
    ("Boa Hancock", "boa-hancock", "Empress of Amazon Lily. Hancock searches can start at the OP17 hub.", [5, 4]),
    ("Gecko Moria", "gecko-moria", "Former Warlord. Use the OPTCG hub while looking for a matching leader.", [8]),
    ("Bartholomew Kuma", "bartholomew-kuma", "Tyrant and former Warlord. Start from the One Piece TCG hub on this site.", [4]),
    ("Monkey D. Garp", "monkey-d-garp", "Hero of the Marines and Luffy’s grandfather. Luffy OPTCG pages are the closest constructed lists.", [4, 6]),
    ("Monkey D. Dragon", "monkey-d-dragon", "Revolutionary Army leader. Luffy OPTCG pages are the related constructed lists.", [4]),
    ("Sabo", "sabo", "Chief of Staff of the Revolutionaries. Ace, Sabo, and Luffy cards show up in some red lists.", [0, 6]),
    ("Akainu", "akainu", "Fleet Admiral Sakazuki. Marine searches can start at the OPTCG hub.", [4]),
    ("Aokiji", "aokiji", "Kuzan. Cross-guild and marine searches still belong on this OPTCG site hub.", [2]),
    ("Kizaru", "kizaru", "Borsalino. Admiral searches should land here, then move to a leader list.", [8]),
    ("Fujitora", "fujitora", "Issho. Another admiral name that should resolve to this OPTCG hub.", [8]),
    ("Coby", "coby", "Marine prodigy. Red/Black OP11 Koby is the constructed Navy / SWORD leader.", [19]),
    ("Koby", "koby", "Same search as Coby. Red/Black OP11 Koby is the constructed Navy / SWORD leader.", [19]),
    ("Smoker", "smoker", "White Hunter of the Marines. Use the OPTCG hub.", [7]),
    ("Rob Lucci", "rob-lucci", "CP0. Lucci is a popular OPTCG name; start from the hub if you do not see a dedicated leader.", [8, 4]),
    ("Perona", "perona", "Ghost Princess. Perona cards can show up in Mihawk-adjacent OPTCG packages.", [8]),
    ("Mr 2 Bon Kurei", "mr-2-bon-kurei", "Bentham. A fun OPTCG character name that should still reach this site.", [3, 5]),
    ("Emporio Ivankov", "emporio-ivankov", "Queen of the Kamabakka Kingdom. Green/Blue OP16 Impel Down Luffy is the closest constructed leader.", [14, 4]),
    ("Uta", "uta", "New Genesis. Uta cards appear in some red Newgate OPTCG lists.", [0]),
    ("Loki", "loki", "Prince of Elbaph. Black OP17 Luffy is the Elbaph OPTCG leader on this site.", [4]),
    ("Harald", "harald", "King of Elbaph. Black Luffy OPTCG lists are the Elbaph constructed pages.", [4]),
    ("Shakuyaku", "shakuyaku", "Shakky of the Rocks era. Blue Rocks D. Xebec is the matching OP17 OPTCG leader.", [2]),
    ("Luffy", "luffy", "Same search as Monkey D. Luffy. Black OP17 Luffy, RG Luffy, GB Impel Down Luffy, and blue/purple UP Luffy are constructed leaders.", [4, 6, 14, 23]),
    ("UP Luffy", "up-luffy", "Community name for blue/purple OP11-040 Monkey D. Luffy. U is blue, P is purple. Look 5 Straw Hats once you hit 8 DON!!.", [23, 4, 6, 14]),
    ("Zoro", "zoro", "Same search as Roronoa Zoro. Mihawk and RG Luffy lists are the closest OPTCG pages.", [8, 6]),
    ("Mihawk", "mihawk", "Same search as Dracule Mihawk. Green Mihawk has tournament OPTCG lists on this site.", [8]),
    ("Newgate", "newgate", "Same person as Edward Newgate / Whitebeard. Red OP17 is the constructed page.", [0]),
    ("Xebec", "xebec", "Same search as Rocks D. Xebec. Blue OP17 is the constructed OPTCG leader.", [2]),
    ("Rocks", "rocks", "Short name for Rocks D. Xebec and the Rocks Pirates OPTCG package.", [2]),
    ("Linlin", "linlin", "Same person as Charlotte Linlin / Big Mom. Yellow OP17 is the constructed page.", [5]),
    ("Law", "law", "Same search as Trafalgar Law. Rosinante is the Law-partner leader; RG Luffy lists also play Law cards.", [16, 6]),
    ("Donquixote Rosinante", "donquixote-rosinante", "Corazon. Purple/Yellow OP12 Rosinante is the Law-partner constructed leader.", [16]),
    ("Rosinante", "rosinante", "Same search as Donquixote Rosinante / Corazon. Open the purple/yellow leader page.", [16]),
    ("Corazon", "corazon", "Codename of Donquixote Rosinante. Purple/Yellow OP12 is the constructed leader.", [16]),
    ("Kid", "kid", "Same search as Eustass Kid. Start from RG Luffy and the OP17 hub.", [6, 4]),
    ("Ace", "ace", "Same search as Portgas D. Ace. OP16 Ace is the constructed red leader; OP13 Ace is the red/blue leader.", [9, 10]),
    ("Roger", "roger", "Same search as Gol D. Roger. Roger cards show up in Newgate and Rocks OPTCG lists.", [0, 2]),
    ("Oden", "oden", "Same search as Kouzuki Oden. Red Newgate OPTCG lists are the usual home.", [0]),
    ("Katakuri", "katakuri", "Same search as Charlotte Katakuri. Purple OP11 Katakuri is the constructed leader.", [13]),
    ("Beckman", "beckman", "Same search as Benn Beckman. Open OP17 Shanks OPTCG lists.", [1]),
    ("Rayleigh", "rayleigh", "Same search as Silvers Rayleigh. Newgate and Rocks pages are the closest lists.", [0, 2]),
    ("Enel", "enel", "God of Skypeia. Purple OP15 Enel is the constructed OPTCG leader on this site.", [12]),
    ("Lucci", "lucci", "Same search as Rob Lucci. Start from the hub, Mihawk, or Black Luffy pages.", [8, 4]),
    ("Doflamingo", "doflamingo", "Same search as Donquixote Doflamingo. Open the purple OP14 Doffy leader page.", [20]),
    ("Hancock", "hancock", "Same search as Boa Hancock. Start from the OP17 hub and yellow/black lists.", [5, 4]),
    ("Teach", "teach", "Same search as Marshall D. Teach / Blackbeard. Open the OP16 Blackbeard leader page.", [15]),
    ("Garp", "garp", "Same search as Monkey D. Garp. Luffy OPTCG pages are the closest constructed lists.", [4, 6]),
    ("Dragon", "dragon", "Same search as Monkey D. Dragon. Black Luffy OPTCG is the related constructed page.", [4]),
    ("Nefertari Vivi", "nefertari-vivi", "Princess of Alabasta. Straw Hat adjacent; start from Luffy and Nami OPTCG pages.", [4, 7]),
    ("Arlong", "arlong", "Fish-Man pirate from East Blue. Nami and Luffy OPTCG pages are the closest lists.", [7, 4]),
    ("Don Krieg", "don-krieg", "East Blue pirate. Use the One Piece TCG hub, then a red or black leader list.", [0, 4]),
    ("Kuro", "kuro", "Captain Kuro of the Black Cat Pirates. Start from the OPTCG hub.", [4, 8]),
    ("Alvida", "alvida", "Iron Mace Alvida. Early One Piece name; use the OPTCG hub and Luffy pages.", [4]),
    ("Helmeppo", "helmeppo", "Marine from Shells Town. Coby and Garp searches sit next to Luffy OPTCG pages.", [4]),
    ("Tashigi", "tashigi", "Marine swordsman. Smoker and Mihawk pages are the closest OPTCG starts.", [7, 8]),
    ("Sengoku", "sengoku", "Former Fleet Admiral. Purple OP16 Sengoku is the constructed Navy leader.", [22, 19]),
    ("Sakazuki", "sakazuki", "Fleet Admiral, also searched as Akainu. Use the OPTCG hub and Luffy pages.", [4]),
    ("Kuzan", "kuzan", "Former Admiral, also searched as Aokiji. Rocks and the hub are fair starts.", [2]),
    ("Borsalino", "borsalino", "Admiral Kizaru. Use the OPTCG hub, then a leader that matches your list.", [8]),
    ("Issho", "issho", "Admiral Fujitora. Another marine name that should resolve to this OPTCG hub.", [8]),
    ("Sentomaru", "sentomaru", "Marine scientist escort. Egghead-era searches can start at the OPTCG hub.", [4, 8]),
    ("Magellan", "magellan", "Warden of Impel Down. Green/Blue OP16 Luffy is the Impel Down constructed leader.", [14, 4]),
    ("Shiryu", "shiryu", "Blackbeard Pirates swordsman. Open the OP16 Blackbeard leader page.", [15, 8]),
    ("Jesus Burgess", "jesus-burgess", "Champion of the Blackbeard Pirates. Open the OP16 Blackbeard leader page.", [15]),
    ("Van Augur", "van-augur", "Blackbeard Pirates sniper. Open the OP16 Blackbeard leader page.", [15]),
    ("Lafitte", "lafitte", "Blackbeard Pirates navigator. Open the OP16 Blackbeard leader page.", [15]),
    ("Doc Q", "doc-q", "Blackbeard Pirates doctor. Open the OP16 Blackbeard leader page.", [15]),
    ("Shirahoshi", "shirahoshi", "Princess of the Ryugu Kingdom. Jinbe and Luffy OPTCG pages are related.", [4]),
    ("Neptune", "neptune", "King of the Ryugu Kingdom. Fish-Man searches can start at Jinbe/Luffy pages.", [4]),
    ("Fisher Tiger", "fisher-tiger", "Sun Pirates founder. Jinbe-related OPTCG searches start at Black Luffy.", [4]),
    ("Koala", "koala", "Revolutionary Army. Sabo and Dragon searches sit next to Luffy OPTCG pages.", [4, 0]),
    ("Iceburg", "iceburg", "Mayor of Water 7. Franky-related searches can start at Luffy OPTCG pages.", [4]),
    ("Paulie", "paulie", "Galley-La shipwright. Water 7 names can start at the OPTCG hub.", [4]),
    ("Kalifa", "kalifa", "CP9. Lucci-adjacent searches can start at the hub or Mihawk.", [8, 4]),
    ("Kaku", "kaku", "CP9 and CP0. Lucci-adjacent OPTCG searches start at the hub.", [8, 4]),
    ("Blueno", "blueno", "CP9. Enies Lobby names can start at the OPTCG hub.", [8]),
    ("Jabra", "jabra", "CP9. Use the OPTCG hub.", [8]),
    ("Spandam", "spandam", "CP9 director. Use the OPTCG hub.", [4, 8]),
    ("Nico Olvia", "nico-olvia", "Robin’s mother. Robin and Luffy OPTCG pages are the related lists.", [4]),
    ("Jaguar D. Saul", "jaguar-d-saul", "Giant marine who saved Robin. Elbaph Luffy is the matching OP17 OPTCG leader.", [4]),
    ("Hogback", "hogback", "Thriller Bark doctor. Moria and Perona searches sit with Mihawk-adjacent lists.", [8]),
    ("Absalom", "absalom", "Thriller Bark commander. Use the OPTCG hub or Mihawk.", [8]),
    ("Ryuma", "ryuma", "Legendary samurai zombie. Zoro and Mihawk OPTCG pages are the closest lists.", [8, 6]),
    ("Caesar Clown", "caesar-clown", "Scientist of Punk Hazard. Law-related searches can start at RG Luffy.", [6]),
    ("Monet", "monet", "Snow woman of Punk Hazard. Use the OPTCG hub.", [6, 7]),
    ("Vergo", "vergo", "Corazon’s former vice admiral cover. Law searches start at the Rosinante leader page.", [16, 6]),
    ("Kinemon", "kinemon", "Kozuki retainer. Wano searches can start at Kaido or Luffy OPTCG pages.", [3, 4]),
    ("Kouzuki Momonosuke", "kouzuki-momonosuke", "Shogun of Wano. Kaido and Luffy OPTCG pages are related constructed lists.", [3, 4]),
    ("Kouzuki Hiyori", "kouzuki-hiyori", "Princess of Wano. Nami and Wano-adjacent OPTCG lists are the start.", [7, 3]),
    ("Inuarashi", "inuarashi", "Duke of the Mokomo Dukedom. Wano / Luffy OPTCG pages are related.", [4, 3]),
    ("Nekomamushi", "nekomamushi", "Ruler of the Mokomo Dukedom. Wano / Luffy OPTCG pages are related.", [4, 3]),
    ("Raizo", "raizo", "Ninja of Wano. Start from Luffy or Kaido OPTCG pages.", [4, 3]),
    ("Kikunojo", "kikunojo", "Kozuki retainer. Wano searches can start at Kaido or Luffy.", [3, 4]),
    ("Shinobu", "shinobu", "Wano kunoichi. Use the OPTCG hub and Luffy pages.", [4]),
    ("Tama", "tama", "Kibi child of Wano. Black OP16 Yamato and purple Kaido are nearby constructed pages.", [18, 3]),
    ("Who's Who", "whos-who", "Tobi Roppo. Purple Kaido OPTCG lists are the matching constructed pages.", [3]),
    ("Sasaki", "sasaki", "Tobi Roppo. Purple Kaido OPTCG lists are the matching constructed pages.", [3]),
    ("Black Maria", "black-maria", "Tobi Roppo. Purple Kaido OPTCG lists are the matching constructed pages.", [3]),
    ("Kurozumi Orochi", "kurozumi-orochi", "Shogun of Wano. Kaido OPTCG is the usual constructed start.", [3]),
    ("Denjiro", "denjiro", "Kozuki retainer. Wano searches can start at Kaido or Luffy.", [3, 4]),
    ("Kawamatsu", "kawamatsu", "Kozuki retainer. Wano searches can start at Luffy or Kaido.", [4, 3]),
    ("Ashura Doji", "ashura-doji", "Akazaya samurai. Wano searches can start at Kaido or Luffy.", [3, 4]),
    ("Hyogoro", "hyogoro", "Yakuza of Wano. Use the OPTCG hub and Luffy pages.", [4]),
    ("Pudding", "pudding", "Charlotte Pudding. Purple/Yellow OP08 Pudding is the constructed leader; yellow Linlin lists also play Pudding cards.", [24, 5]),
    ("Charlotte Pudding", "charlotte-pudding", "Big Mom’s daughter. Purple/Yellow OP08 Charlotte Pudding is the constructed leader page.", [24, 5]),
    ("Charlotte Oven", "charlotte-oven", "Big Mom Pirate. Open the Linlin OPTCG page.", [5]),
    ("Charlotte Brulee", "charlotte-brulee", "Big Mom Pirate. Open the Pudding and Linlin OPTCG pages.", [24, 5]),
    ("Streusen", "streusen", "Big Mom Pirates chef. Yellow Linlin OPTCG is the matching leader.", [5]),
    ("Prometheus", "prometheus", "Big Mom homie. Yellow Linlin OPTCG lists are the start.", [5]),
    ("Zeus", "zeus", "Big Mom / Nami thundercloud. Linlin and Nami OPTCG pages are related.", [5, 7]),
    ("Napoleon", "napoleon", "Big Mom homie. Yellow Linlin OPTCG is the matching leader.", [5]),
    ("Hera", "hera", "Big Mom homie. Yellow Linlin OPTCG is the matching leader.", [5]),
    ("Capone Bege", "capone-bege", "Fire Tank Pirates. Big Mom-adjacent searches can start at Linlin.", [5]),
    ("Cavendish", "cavendish", "Pretty Pirates captain. Supernova searches can start at RG Luffy.", [6]),
    ("Bartolomeo", "bartolomeo", "Barto Club. Straw Hat fan; start from Luffy OPTCG pages.", [4, 6]),
    ("Rebecca", "rebecca", "Dressrosa princess. Lucy and purple Doffy are the constructed pages.", [17, 20]),
    ("Kyros", "kyros", "Dressrosa gladiator. Lucy and purple Doffy are nearby constructed pages.", [17, 20]),
    ("Sugar", "sugar", "Donquixote family. Open the purple OP14 Doffy leader page.", [20]),
    ("Trebol", "trebol", "Donquixote executive. Open the purple OP14 Doffy leader page.", [20]),
    ("Diamante", "diamante", "Donquixote executive. Open the purple OP14 Doffy leader page.", [20]),
    ("Pica", "pica", "Donquixote executive. Open the purple OP14 Doffy leader page.", [20]),
    ("Senor Pink", "senor-pink", "Donquixote family. Open the purple OP14 Doffy leader page.", [20]),
    ("Baby 5", "baby-5", "Donquixote family. Open the purple OP14 Doffy leader page.", [20]),
    ("Sai", "sai", "Happo Navy. Dressrosa supernova-adjacent searches can start at RG Luffy.", [6]),
    ("Ideo", "ideo", "XXX Gym. Use the OPTCG hub or RG Luffy.", [6]),
    ("Hajrudin", "hajrudin", "Giant pirate. Elbaph Luffy is the OP17 constructed page.", [4]),
    ("Elizabello II", "elizabello-ii", "King of Prodence. Use the OPTCG hub.", [6]),
    ("Vegapunk", "vegapunk", "Scientist of Egghead. Start from the OPTCG hub and Luffy pages.", [4]),
    ("Shaka", "shaka", "Vegapunk satellite. Egghead searches can start at the hub.", [4]),
    ("Lilith", "lilith", "Vegapunk satellite. Egghead searches can start at the hub.", [4]),
    ("York", "york", "Vegapunk satellite. Egghead searches can start at the hub.", [4]),
    ("Atlas", "atlas", "Vegapunk satellite. Egghead searches can start at the hub.", [4]),
    ("Stussy", "stussy", "CP0. Lucci-adjacent searches can start at the hub.", [8, 2]),
    ("Jaygarcia Saturn", "jaygarcia-saturn", "Five Elders. Black Imu OPTCG lists are the matching constructed pages.", [11]),
    ("Marcus Mars", "marcus-mars", "Five Elders. Black Imu OPTCG lists are the matching constructed pages.", [11]),
    ("Topman Warcury", "topman-warcury", "Five Elders. Black Imu OPTCG lists are the matching constructed pages.", [11]),
    ("Ethanbaron V. Nusjuro", "ethanbaron-v-nusjuro", "Five Elders. Black Imu OPTCG lists are the matching constructed pages.", [11]),
    ("Shepherd Ju Peter", "shepherd-ju-peter", "Five Elders. Black Imu OPTCG lists are the matching constructed pages.", [11]),
    ("Imu", "imu", "Sovereign of Mary Geoise and black OP13 OPTCG leader. Five Elders lists live on the Imu page.", [11]),
    ("Figarland Garling", "figarland-garling", "Holy Knights / God Valley. Rocks and Shanks pages are related OPTCG lists.", [2, 1]),
    ("Figarland Shamrock", "figarland-shamrock", "Holy Knights. Shanks and Elbaph Luffy pages are related OPTCG lists.", [1, 4]),
    ("Gunko", "gunko", "Holy Knight. Elbaph Luffy is the matching OP17 constructed page.", [4]),
    ("Killingham", "killingham", "Holy Knight. Elbaph Luffy is the matching OP17 constructed page.", [4]),
    ("Scopper Gaban", "scopper-gaban", "Roger Pirates. Newgate, Rocks, and Elbaph Luffy are related OPTCG pages.", [0, 2, 4]),
    ("Dorry", "dorry", "Giant of Elbaph. Black OP17 Luffy is the Elbaph constructed leader.", [4]),
    ("Brogy", "brogy", "Giant of Elbaph. Black OP17 Luffy is the Elbaph constructed leader.", [4]),
    ("Colon", "colon", "Elbaph child. Black OP17 Luffy is the matching constructed page.", [4]),
    ("Ripley", "ripley", "Giant of Elbaph. Black OP17 Luffy is the matching constructed page.", [4]),
    ("Road", "road", "Giant of Elbaph. Black OP17 Luffy is the matching constructed page.", [4]),
    ("Goldberg", "goldberg", "Giant of Elbaph. Black OP17 Luffy is the matching constructed page.", [4]),
    ("Gerd", "gerd", "Giant of Elbaph. Black OP17 Luffy is the matching constructed page.", [4]),
    ("Jarul", "jarul", "Giant elder of Elbaph. Black OP17 Luffy is the matching constructed page.", [4]),
    ("Ida", "ida", "Giant of Elbaph. Black OP17 Luffy is the matching constructed page.", [4]),
    ("Gloriosa", "gloriosa", "Amazon Lily elder, Rocks era. Rocks D. Xebec is the matching OP17 leader.", [2]),
    ("Buckingham Stussy", "buckingham-stussy", "Rocks Pirates. Blue Rocks D. Xebec is the matching OP17 OPTCG leader.", [2]),
    ("Captain John", "captain-john", "Rocks Pirates. Blue Rocks D. Xebec is the matching OP17 OPTCG leader.", [2]),
    ("Wang Zhi", "wang-zhi", "Rocks Pirates. Blue Rocks D. Xebec is the matching OP17 OPTCG leader.", [2]),
    ("Ochoku", "ochoku", "Rocks Pirates. Blue Rocks D. Xebec is the matching OP17 OPTCG leader.", [2]),
    ("Red Hair", "red-hair", "Red Hair / Red-Haired Pirates OPTCG lists live on OP17 Shanks.", [1]),
    ("King of the Beasts", "king-of-the-beasts", "Kaido’s title. Purple OP17 Kaido is the constructed OPTCG page.", [3]),
    ("World's Strongest Man", "worlds-strongest-man", "Whitebeard’s title. Red OP17 Edward Newgate is the constructed page.", [0]),
    ("World's Strongest Swordsman", "worlds-strongest-swordsman", "Mihawk’s title. Green Mihawk OPTCG lists are on his leader page.", [8]),
    ("Pirate King", "pirate-king", "Gol D. Roger’s title, and Luffy’s goal. Roger and Luffy OPTCG pages are related.", [0, 4]),
    ("Fire Fist", "fire-fist", "Portgas D. Ace’s epithet. OP16 Ace and OP13 Ace are both constructed leaders; Ace cards also show up in Edward Newgate lists.", [9, 10, 0]),
    ("Surgeon of Death", "surgeon-of-death", "Trafalgar Law’s epithet. RG Luffy lists are a common home for Law cards.", [6]),
    ("Heavenly Demon", "heavenly-demon", "Doflamingo’s epithet. Open the purple OP14 Doffy leader page.", [20]),
    ("Tyrant", "tyrant", "Bartholomew Kuma’s epithet. Start from the One Piece TCG hub.", [4]),
    ("Hero of the Marines", "hero-of-the-marines", "Monkey D. Garp’s epithet. Luffy OPTCG pages are the closest lists.", [4, 6]),
    ("Dark King", "dark-king", "Silvers Rayleigh’s epithet. Newgate and Rocks pages are related OPTCG lists.", [0, 2]),
    ("All-Star King", "all-star-king", "King of the Beasts. Purple Kaido OPTCG lists are the constructed pages.", [3]),
    ("All-Star Queen", "all-star-queen", "Queen of the Beasts. Purple Kaido OPTCG lists are the constructed pages.", [3]),
    ("Drought Jack", "drought-jack", "Jack of the Beasts. Purple Kaido OPTCG lists are the constructed pages.", [3]),
    ("Sweet Commander", "sweet-commander", "Katakuri, Smoothie, and Cracker. Yellow Linlin OPTCG is the matching leader.", [5]),
    ("Red-Haired Shanks", "red-haired-shanks", "Full search for OP17 green Shanks. Open the Shanks leader page for OPTCG lists.", [1]),
    ("Blackbeard Pirates", "blackbeard-pirates", "Marshall D. Teach’s crew. Open the OP16 Blackbeard leader page for constructed lists.", [15]),
    ("Heart Pirates", "heart-pirates", "Trafalgar Law’s crew. Law cards show up in RG Luffy OPTCG lists.", [6]),
    ("Kid Pirates", "kid-pirates", "Eustass Kid’s crew. Start from RG Luffy and the OP17 hub.", [6, 4]),
    ("Sun Pirates", "sun-pirates", "Jinbe and Fisher Tiger. Black Luffy OPTCG is a related constructed page.", [4]),
    ("Revolutionary Army", "revolutionary-army", "Dragon, Sabo, Koala, Ivankov. Luffy OPTCG pages are the related lists.", [4, 0]),
    ("Marines", "marines", "Garp, Sengoku, admirals, Coby, Smoker. Start from the OPTCG hub, then a leader list.", [4, 8]),
    ("Warlords", "warlords", "Mihawk, Hancock, Doflamingo, Kuma, Moria, Crocodile, Buggy, Law, Jinbe. Open the matching leader or hub.", [8, 20, 21, 5]),
    ("Supernovas", "supernovas", "Luffy, Zoro, Law, Kid, Killer, Bonney, Bege, Urouge, Apoo, Hawkins. Start from Luffy and RG Luffy.", [4, 6]),
    ("Urouge", "urouge", "Supernova captain. Start from the OPTCG hub or RG Luffy.", [6]),
    ("Scratchmen Apoo", "scratchmen-apoo", "Supernova captain. Start from the OPTCG hub or Kaido-adjacent lists.", [3, 6]),
    ("Basil Hawkins", "basil-hawkins", "Supernova captain. Wano-era searches can start at Kaido.", [3, 6]),
    ("X Drake", "x-drake", "Supernova and marine. Wano / Kaido OPTCG pages are related.", [3, 6]),
    ("Bonney", "bonney", "Same search as Jewelry Bonney. Start from the OPTCG hub.", [6]),
    ("Carrot", "carrot", "Mink of the Mokomo Dukedom. Wano / Luffy OPTCG pages are related.", [4]),
    ("Pedro", "pedro", "Mink of Nox. Wano / Luffy OPTCG pages are related.", [4]),
    ("Wanda", "wanda", "Mink of the Mokomo Dukedom. Use the OPTCG hub and Luffy pages.", [4]),
    ("Inazuma", "inazuma", "Revolutionary. Ivankov-adjacent searches start at Luffy pages.", [4]),
    ("Hack", "hack", "Revolutionary fish-man. Use Luffy OPTCG pages.", [4]),
    ("Belo Betty", "belo-betty", "Revolutionary Army commander. Use Luffy OPTCG pages.", [4]),
    ("Karasu", "karasu", "Revolutionary Army commander. Use Luffy OPTCG pages.", [4]),
    ("Morley", "morley", "Revolutionary Army commander. Use Luffy OPTCG pages.", [4]),
    ("Lindbergh", "lindbergh", "Revolutionary Army commander. Use Luffy OPTCG pages.", [4]),
    ("Yamato Oden", "yamato-oden", "Yamato using Oden’s name. Black OP16 Yamato is the constructed Wano leader.", [18, 3]),
    ("Onami", "onami", "Nami’s Wano alias. Nami is the constructed OPTCG leader.", [7]),
    ("O-Soba Mask", "o-soba-mask", "Sanji’s raid suit alias. Newgate and RG Luffy lists may play Sanji cards.", [0, 6]),
    ("Sogeking", "sogeking", "Usopp’s Sniper Island alias. Luffy OPTCG pages are related.", [4, 6]),
    ("Lucy", "lucy", "Luffy’s Dressrosa alias and red/blue OP15 leader. Not red/blue OP13 Ace.", [17, 10]),
    ("Straw Hat", "straw-hat", "Luffy’s epithet and crew name. Open the Luffy OPTCG leader pages.", [4, 6]),
    ("Gum-Gum", "gum-gum", "Luffy’s Devil Fruit name search. Open Monkey D. Luffy OPTCG lists.", [4, 6]),
    ("Haki", "haki", "OPTCG cards reference Haki in effects. Open any leader list to see constructed cards.", [4, 1]),
    ("DON", "don", "DON!! cards power OPTCG attacks. Every 50-card list on this site plays with DON!!.", [4, 1]),
    ("Leader card", "leader-card", "Every OPTCG deck starts with a leader. Open the leader pages below for 50-card lists.", [4, 1]),
    ("Character card", "character-card", "OPTCG Character cards make up most of a 50-card list. Open a leader page to see them.", [1, 3]),
    ("Event card", "event-card", "OPTCG Event cards sit in the 50-card list next to Characters. Open any leader page.", [1, 5]),
    ("Stage card", "stage-card", "OPTCG Stage cards are uncommon but show up in some constructed lists on this site.", [7, 2]),
]


def topic_body(topic: dict) -> str:
    return f"""        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {html.escape(topic["h2"])}</div>
        <h2>{html.escape(topic["h2"])}</h2>
        <p>{html.escape(topic["copy"])}</p>
        <section style="margin-top:18px">
          <div class="section-title">
            <h3>OPTCG leader pages</h3>
            <div class="muted">One Piece TCG</div>
          </div>
          <ul class="list">
{leader_list()}
          </ul>
        </section>
        <p class="muted" style="margin-top:18px">Fan site. Not affiliated with Bandai or Shueisha. <a href="/guides/">More One Piece TCG guides</a>.</p>"""


def character_body(name: str, blurb: str, related: list[int]) -> str:
    rows = []
    for i in related:
        n, href, meta = LEADERS[i]
        rows.append(
            f"""            <li>
              <a class="item" href="{html.escape(href)}">
                <div>
                  <div style="font-weight:700">{html.escape(n)} decklists</div>
                  <div class="muted" style="font-size:13px">{html.escape(meta)} · OPTCG</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>"""
        )
    if not rows:
        rows.append(
            f"""            <li>
              <a class="item" href="/decklists/op17.html">
                <div>
                  <div style="font-weight:700">All OP17 leader pages</div>
                  <div class="muted" style="font-size:13px">One Piece TCG hub</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>"""
        )
    return f"""        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / <a href="/guides/characters/">Characters</a> / {html.escape(name)}</div>
        <h2>{html.escape(name)}</h2>
        <p>{html.escape(blurb)}</p>
        <section style="margin-top:18px">
          <div class="section-title">
            <h3>Related OPTCG decklists</h3>
            <div class="muted">One Piece Card Game</div>
          </div>
          <ul class="list">
{chr(10).join(rows)}
          </ul>
        </section>
        <p class="muted" style="margin-top:18px"><a href="/guides/characters/">All character guides</a> · <a href="/guides/">One Piece TCG guides</a></p>"""


def guides_index(topic_links: list[tuple[str, str]], char_links: list[tuple[str, str]]) -> str:
    topics = "\n".join(
        f'            <li><a class="item" href="{html.escape(href)}"><div style="font-weight:700">{html.escape(label)}</div><div class="link">Open →</div></a></li>'
        for label, href in topic_links
    )
    chars = "\n".join(
        f'            <li><a class="item" href="{html.escape(href)}"><div style="font-weight:700">{html.escape(label)}</div><div class="link">Open →</div></a></li>'
        for label, href in char_links
    )
    return f"""        <div class="crumb"><a href="/">Home</a> / Guides</div>
        <h2>One Piece TCG guides</h2>
        <p>Topic and character pages that link to the 50-card lists on this site.</p>
        <section style="margin-top:18px">
          <div class="section-title"><h3>Topics</h3><div class="muted">Bandai / OPTCG</div></div>
          <ul class="list">
{topics}
          </ul>
        </section>
        <section style="margin-top:18px">
          <div class="section-title"><h3>Characters</h3><div class="muted">{len(char_links)} names</div></div>
          <ul class="list">
{chars}
          </ul>
        </section>"""


def characters_index(char_links: list[tuple[str, str]]) -> str:
    chars = "\n".join(
        f'            <li><a class="item" href="{html.escape(href)}"><div style="font-weight:700">{html.escape(label)}</div><div class="link">Open →</div></a></li>'
        for label, href in char_links
    )
    return f"""        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / Characters</div>
        <h2>One Piece TCG characters</h2>
        <p>Character names from One Piece, mapped to OPTCG leader decklists on this Bandai One Piece Card Game fan site.</p>
        <ul class="list" style="margin-top:18px">
{chars}
        </ul>"""


def patch_canonical(page: str, url: str) -> str:
    return page.replace(
        f'<link rel="canonical" href="{html.escape(SITE)}" />',
        f'<link rel="canonical" href="{html.escape(url)}" />',
        1,
    )


def write_page(rel: str, title: str, desc: str, body: str) -> str:
    path = ROOT / rel.lstrip("/")
    path.parent.mkdir(parents=True, exist_ok=True)
    url = SITE + ("/" if rel == "guides/index.html" else "/" + rel)
    if rel.endswith("/index.html"):
        url = SITE + "/" + rel[: -len("index.html")]
    page = patch_canonical(chrome(title, desc, body), url)
    path.write_text(page)
    return url


def existing_html_urls() -> list[str]:
    urls = []
    for p in sorted(ROOT.rglob("*.html")):
        if any(part in p.parts for part in (".git", "scripts", "node_modules")):
            continue
        rel_check = p.relative_to(ROOT).as_posix()
        if rel_check in ("shop/custom-leaders.html",):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.endswith("index.html"):
            url = SITE + "/" if rel == "index.html" else SITE + "/" + rel[: -len("index.html")]
        else:
            url = SITE + "/" + rel
        urls.append(url)
    return urls


def main() -> None:
    slugs = [c[1] for c in CHARACTERS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate character slugs")
    topic_slugs = [t["slug"] for t in TOPICS]
    if len(topic_slugs) != len(set(topic_slugs)):
        raise SystemExit("duplicate topic slugs")
    topic_links = []
    urls = []
    handwritten = {
        "op17-mihawk-matchups",
        "nico-robin-strategy",
        "sabo-strategy",
        "rocks-d-xebec-strategy",
        "portgas-d-ace-strategy",
    }

    for topic in TOPICS:
        rel = f"guides/{topic['slug']}.html"
        if topic["slug"] in handwritten and (ROOT / rel).exists():
            topic_links.append((topic["h2"], "/" + rel))
            urls.append(SITE + "/" + rel)
            continue
        url = write_page(rel, topic["title"], topic["desc"], topic_body(topic))
        topic_links.append((topic["h2"], "/" + rel))
        urls.append(url)

    char_links = []
    for name, slug, blurb, related in CHARACTERS:
        rel = f"guides/characters/{slug}.html"
        title = f"{name} One Piece TCG | OPTCG decklists"
        desc = f"{name} in the One Piece TCG (OPTCG, Bandai ONE PIECE CARD GAME). Open related 50-card decklists."
        url = write_page(rel, title, desc, character_body(name, blurb, related))
        char_links.append((name, "/" + rel))
        urls.append(url)

    write_page(
        "guides/index.html",
        "One Piece TCG guides | OPTCG | Bandai",
        "Guides for One Piece TCG, OPTCG, Bandai, and character names, linking to real decklists.",
        guides_index(topic_links, char_links),
    )
    write_page(
        "guides/characters/index.html",
        "One Piece TCG characters | OPTCG",
        "One Piece character names mapped to OPTCG decklists on One Piece Decklists.",
        characters_index(char_links),
    )

    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nDisallow: /shop/custom-leaders.html\nDisallow: /ballkeep/\nDisallow: /scripts/\nDisallow: /data/\nDisallow: /discord-bot/\nDisallow: /.github/\n\nUser-agent: Googlebot\nAllow: /\nDisallow: /shop/custom-leaders.html\nDisallow: /ballkeep/\nDisallow: /scripts/\nDisallow: /data/\nDisallow: /discord-bot/\nDisallow: /.github/\n\nSitemap: https://onepiecedecklists.com/sitemap.xml\n"
    )

    print("topics", len(TOPICS), "characters", len(CHARACTERS), "pages", len(existing_html_urls()))


if __name__ == "__main__":
    main()
