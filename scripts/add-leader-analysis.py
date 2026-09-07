#!/usr/bin/env python3
"""Add a community take and a consensus 50-card list to every leader hub."""

from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

import importlib.util

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

ROOT = gen.ROOT
LINE_RE = re.compile(
    r'<span class="qty">(\d+)x</span>.*?<span class="muted card-id">([^<]+)</span>',
    re.S,
)
BLOCK_RE = re.compile(
    r"        <!-- LEADER_ANALYSIS -->.*?        <!-- /CONSENSUS_LIST -->\n?",
    re.S,
)
TARGET = 50
MIN_OP17_COPIES = 8
OP17_SUBSET_MIN = 3

# Leader-hub links to handwritten strategy pages. Shown under the archetype,
# immediately above the consensus list.
STRATEGY_PAGES = {
    "OP09-062": (
        "/guides/nico-robin-strategy.html",
        "Nico Robin strategy",
        "OP17 curve, Big Mom splash, Mihawk matchup",
    ),
    "OP14-020": (
        "/guides/op17-mihawk-matchups.html",
        "Which decks beat OP17 Mihawk",
        "Limitless pairings · Robin, Ace, Sabo",
    ),
    "OP13-004": (
        "/guides/sabo-strategy.html",
        "Sabo strategy",
        "OP17 Elbaph curve, mulligan, 52.1% vs Mihawk",
    ),
    "OP17-039": (
        "/guides/rocks-d-xebec-strategy.html",
        "Rocks D. Xebec strategy",
        "Even/odd Rocks Pirates curve · 33.6% vs Mihawk",
    ),
    "OP16-001": (
        "/guides/portgas-d-ace-strategy.html",
        "Portgas D. Ace strategy",
        "Rush Whitebeard curve, mulligan, 57.8% vs Mihawk",
    ),
}

TAKES = {
    "OP17-001": (
        "Red OP17 Edward Newgate is a Whitebeard beatstick that keeps 8000-power bodies on the board. "
        "Core lists play 4 Sanji, 4 Portgas D. Ace, 4 Izo, 4 ten-cost Edward Newgate, 4 Kouzuki Oden, plus Marco, Uta, and Moby Dick. "
        "Flex is Namule/Curiel search, Rakuyo beatdown, or an Ivankov/Zoro package."
    ),
    "OP17-020": (
        "Green OP17 Shanks rests the board and plays Red Hair Pirates. "
        "Every list locks Benn Beckman, Yasopp, and the ten-cost Shanks; most also play Limejuice, Lucky Roux, Crone Oli, and rest events. "
        "The split is staying in-theme versus splashing Perona, Smoker, and Law like Mihawk."
    ),
    "OP17-039": (
        "Blue OP17 Rocks D. Xebec is the densest Limitless pile on this site. "
        "Lists play 4 Edward Newgate, 4 Shiki, 4 Charlotte Linlin, 4 Gloriosa, 4 Miss Buckingham Stussy, 4 Rocks D. Xebec, the Rocks Pirates stage, and There's No Authority. "
        "Kaido, Streusen, Don Marlon, and Captain John are the usual ratio fights."
    ),
    "OP17-058": (
        "Purple OP17 Kaido is All-Star midrange with a tight tournament core. "
        "King, Queen, Basil Hawkins, Yamato, the on-leader Kaido, Mamaragan, and We're Going to Claim the One Piece show up in every averaged list. "
        "Flex is Black Maria, Jack, Divine Departure, or the new OP17 events."
    ),
    "OP17-079": (
        "Black OP17 Monkey D. Luffy is the Elbaph blocker deck, not Imu. "
        "Usopp, Gerd, and Loki are 4-ofs; most lists also play Jaguar D. Saul, a Luffy beater, Zoro, Nico Robin, Rodo, Sanji, and Chopper. "
        "Flex is extra giants versus events like Gum-Gum Kong Gun, Tempest Kick, or Thousand Sunny."
    ),
    "OP17-099": (
        "Yellow OP17 Charlotte Linlin is a Big Mom swarm leader. "
        "Pudding, the on-color Linlin, and Cracker are in every averaged list; Katakuri, Oven, Sweet 3 Generals, Daifuku, and Zeus are close behind. "
        "Perospero, Smoothie, Streusen, Teach, and Brulee fill the rest."
    ),
    "OP13-001": (
        "RG Luffy is a Straw Hat value pile that still posts in current format. "
        "Lists average Sanji, Usopp, Nami, EB04 Zoro, Brook, Charlestone, starter Luffy, and Thousand Sunny. "
        "Laboon, Electrical Luna, and Bonney are common; the 10-cost Luffy and extra Zoro events are the usual cuts."
    ),
    "OP11-041": (
        "Blue/Yellow Nami draws when Life cards leave, then plays a Thriller Bark yellow package. "
        "Every averaged list has Kumacy, Gecko Moria, Nico Robin, Nami, Borsalino, and Perona; Hogback, Zeus, and a Newgate splash are close to required. "
        "Mr. 3, Marco, Kikunojo, and Gravity Blade are the next tier."
    ),
    "OP14-020": (
        "Green Mihawk is a rest/control pile. "
        "Limitless lists play Perona (both printings), Law & Bepo, Kin'emon, Kouzuki Oden, the Mihawk character, and Dead Man's Game. "
        "Otama, Kikunojo, You Can Be My Samurai, Coffin Boat, and the rush event show up in most lists; Smoker, Zoro, and the ten-cost Mihawk are flex."
    ),
    "OP16-001": (
        "Red OP16 Portgas D. Ace is Whitebeard rush - not the red/blue OP13 Ace. "
        "Lists lock 4 Monkey D. Luffy, 4 Edward Newgate, 4 Vista, and Moby Dick; Garp, Little Oars Jr., Curiel, Marco, and Thatch are close to required. "
        "The 10-cost Ace is usually a 3-of; Namule, Time for the Counterattack, Uta, and Izo are flex."
    ),
    "OP15-058": (
        "Purple OP15 Enel is Sky Island ramp: a 6-card DON!! deck that floods DON!! from turn two and rests the board. "
        "Averaged lists play Ohm, Shura, Enel, El Thor, Lightning Beast Kiten, Lightning Dragon, Mamaragan, Charlotte Pudding, and Vinsmoke Reiju. "
        "Gamma Knife, Varie, Senor Pink, and Divine Departure fill the rest. This is not yellow OP05 Enel."
    ),
    "OP11-062": (
        "Purple OP11 Charlotte Katakuri is the other Big Mom leader, separate from yellow OP17 Linlin. "
        "DON!! −1 on attack or on the opponent's attack to peek their deck and gain power. "
        "Core is Katakuri and Pudding in both printings plus ST34 Big Mom: Katakuri, Brulee, Linlin, and Cracker, with We're Going to Claim the One Piece, Mamaragan, and Divine Departure."
    ),
    "OP13-079": (
        "Black OP13 Imu is Mary Geoise / Five Elders, not OP17 Elbaph Luffy. "
        "No 2-cost or higher events, and the Empty Throne stage starts in play from deck. "
        "Lists play Saturn, Warcury, Nusjuro, Mars, Ju Peter, the 10-cost Five Elders, Saint Shalria, and The Five Elders Are at Your Service. Saint Charlos, Sabo, Never Existed, and Ground Death are flex."
    ),
    "OP13-002": (
        "OP13 Ace is red/blue Portgas D. Ace - 3 life, 6000 power - not the red OP16 Ace rush deck. "
        "Trash a card to give −2000, then draw when you take damage or a 6000-power body dies. "
        "Core is Monkey D. Garp, Otama, Izo, Marco, Yamato, OP13 Edward Newgate, and I Am Whitebeard; Uta, Jozu, Atmos, and Roger finish."
    ),
    "OP16-022": (
        "Green/Blue OP16 Monkey D. Luffy is Impel Down tempo - not red/green OP13 Luffy and not black OP17 Elbaph Luffy. "
        "If the only characters on your field are Impel Down, set up to 2 DON!! active. "
        "Averaged lists lock Prisoner of Impel Down, 1-cost Luffy, Buggy, Mr. 1, Mr. 2, Mr. 3, Hancock, Ivankov, and Let's Go!! To the Navy Headquarters; Crocodile and Gravity Blade are the next cuts."
    ),
    "OP16-080": (
        "Black/Yellow OP16 Marshall D. Teach is Blackbeard, not a different Teach printing. "
        "Your characters cost +1 on the opponent's turn; trash a Trigger to retarget an attack. "
        "Averaged lists lock Shiryu, both Teach bodies, Catarina Devon, Vasco Shot, and Zehahahahaha; Borsalino, Doc Q, Fullalead, My Era Begins, Van Augur, and Burgess follow."
    ),
    "OP12-061": (
        "Purple/Yellow Donquixote Rosinante is the Law partner leader. "
        "Once per turn you can pay a Life instead of letting Law die, then DON!! −1 to discount a 4-cost or higher Law. "
        "Averaged lists lock Rosinante & Law, the promo Laws, I Love You!!, and 1-cost Rosinante; ST10 Law, 8-cost Law, Borsalino, Mamaragan, Koby, and Marineford are the next tier."
    ),
    "OP15-002": (
        "Red/Blue Lucy is Dressrosa Luffy in the colosseum disguise - not red/blue OP13 Ace. "
        "Trash events or stages for power, then draw if you already fired a 3-cost or higher event. "
        "Averaged lists lock Viola, Rebecca, Barrier-Barrier Pistol, both Fire Fist events, Just Watch Me Ace, and the Memento event; Leo, Sabo, Roger, and Cavendish finish the 50."
    ),
    "OP16-079": (
        "Black OP16 Yamato is the Wano leader, not a character in Kaido. "
        "A Land of Wano character played from trash gains Rush that turn. "
        "Averaged lists lock Nami, the Yamato bodies, both Momonosuke, Kin'emon, Shinobu, Nico Robin, and I've Come Here To Cut Those Chains; Otama and Ground Death are close."
    ),
    "OP11-001": (
        "Red/Black Koby is Navy / SWORD. "
        "SWORD characters can attack the turn they come down, and a 7000-or-less Navy body can be saved from removal. "
        "Averaged lists lock Kujyaku, Aramaki, Helmeppo, Ripper, and I'm Gonna Be a Navy Officer; Doll, both Koby bodies, Prince Grus, and Hibari are the next cuts."
    ),
    "OP14-060": (
        "Purple OP14 Donquixote Doflamingo is the Dressrosa retarget leader - not blue OP01-060 Doffy and not purple Katakuri. "
        "Once per opponent attack, DON!! −1 to send that attack at Doffy or a Donquixote Pirates body. "
        "Averaged lists lock Sugar, Dellinger, 8-cost Doffy, Monet, Vergo, Baby 5, and 10-cost Doffy; Uso-Hachi, Slow-Slow Beam Sword, Divine Departure, and Trebol finish the 50."
    ),
    "OP16-041": (
        "Blue OP16 Buggy is the Impel Down / Buggy Pirates leader - not a character in GB Luffy. "
        "When an Impel Down body leaves the field, DON!! ×1 plays a Prisoner of Impel Down from hand. "
        "Averaged lists lock Prisoner of Impel Down, Mr. 1, Mr. 2, Mr. 3, Buggy, and Crocodile; Slave Arrow and Miss Olive are the next cuts."
    ),
    "OP16-060": (
        "Purple OP16 Sengoku is the Navy Admiral drop leader - not Enel and not Katakuri. "
        "Return 8 active DON!! to play up to 3 differently named Admirals from hand. "
        "Averaged lists lock Koby, Sakazuki, Sengoku, Buddha Sengoku, Mamaragan, Borsalino, and Kuzan; Tsuru is a near 4-of."
    ),
    "OP11-040": (
        "UP Luffy is blue/purple OP11-040 - U for blue, P for purple. "
        "Ramp to 8 DON!! with Zoro-Juurou, Bon Clay, and Gear Two, then Look 5 every turn for Sanji and Straw Hats. "
        "Averaged lists lock Otama, Uso-Hachi, Zoro-Juurou, Mr. 2, Nami, Sanji, promo Roger, Gear Two, and Gum-Gum Giant. OP17 cards are the current-format flex."
    ),
    "OP08-058": (
        "Purple/Yellow OP08 Charlotte Pudding is the Big Mom DON!! ramp leader - not yellow OP17 Linlin and not purple OP11 Katakuri. "
        "When attacking, turn 2 Life face-up to rest a DON!! from the DON!! deck. "
        "The hosted list is a 50-card r/OnePieceTCG screenshot: 1-cost Pudding and Brulee, 2-cost Katakuri, Miss Doublefinger, Cracker, 6-cost and 8-cost Katakuri, 7-cost Pudding, yellow searcher Pudding, OP17 yellow Pudding, OP17 Katakuri, Sweet 3 Generals, Perospero, and 10-cost Linlin."
    ),
    "OP13-004": (
        "Red/Black OP13 Sabo is Revolutionary Army midrange, not ST13 Sabo. "
        "Current-format lists splash OP17 Elbaph Straw Hats and Loki to turn the Sabo engine on."
    ),
    "OP09-062": (
        "Purple/Yellow OP09 Nico Robin is the Ohara / archaeology leader - not a character in Nami. "
        "OP17 yellow Big Mom cards are the current splash that keeps her posting."
    ),
    "OP14-080": (
        "Black/Yellow OP14 Gecko Moria is Thriller Bark recursion, not Nami's Moria package. "
        "Hosted lists keep the Thriller Bark core and splash OP17 Pudding."
    ),
    "OP14-041": (
        "Blue/Yellow OP14 Boa Hancock is Amazon Lily control. "
        "OP17 yellow Pudding and Linlin are the current-format splash."
    ),
    "OP12-081": (
        "Black/Yellow OP12 Koala is Revolutionary Army, not Sabo's only partner. "
        "Current lists splash OP17 Elbaph search and Loki."
    ),
    "OP09-001": (
        "Red OP09 Shanks is the older Red Hair leader - not green OP17 Shanks. "
        "Hosted lists keep the Red Hair pile and splash an OP17 Newgate body."
    ),
    "OP05-098": (
        "Yellow OP05 Enel is the 4-life yellow Enel - not purple OP15 Enel. "
        "Current lists splash OP17 yellow Big Mom cards."
    ),
    "ST10-002": (
        "ST10 Luffy is red/purple 3-life Straw Hat Luffy. "
        "OP17 Kaido-package cards are the current splash."
    ),
    "OP09-061": (
        "OP09 Luffy is purple/black Film Red Luffy - not OP17 Elbaph Luffy. "
        "Current lists mix OP17 Kaido and Elbaph cards."
    ),
    "ST13-003": (
        "ST13 Luffy is black/yellow Three Brothers Luffy. "
        "Hosted lists splash OP17 Luffy as a finisher."
    ),
    "OP12-040": (
        "Blue OP12 Kuzan is the Admiral ice leader. "
        "OP17 Rocks Pirates cards are the current splash."
    ),
    "OP05-002": (
        "Red/Yellow Belo Betty is Revolutionary Army go-wide. "
        "OP17 yellow Big Mom cards show up in current-format lists."
    ),
    "EB04-001": (
        "EB04 Jewelry Bonney is red/yellow Supernova Bonney. "
        "OP17 yellow Pudding and Linlin are the current splash."
    ),
    "OP10-099": (
        "Yellow OP10 Eustass Kid is the Kid Pirates leader. "
        "Current lists splash a full OP17 yellow Big Mom package."
    ),
    "OP07-059": (
        "Purple OP07 Foxy is the Foxy Pirates stall leader. "
        "The hosted OP17-format list splashes OP17 Kaido."
    ),
    "ST13-001": (
        "ST13 Sabo is red/yellow Three Brothers Sabo - not red/black OP13 Sabo. "
        "OP17 yellow Big Mom cards are the current splash."
    ),
    "OP05-041": (
        "Blue/Black OP05 Sakazuki is the Admiral burn leader. "
        "Current lists splash OP17 Rocks and Elbaph cards."
    ),
    "OP05-060": (
        "OP05 Luffy is purple Gear 4 Luffy. "
        "OP17 Kaido-package cards are the current splash."
    ),
    "OP07-079": (
        "Black OP07 Rob Lucci is CP9 removal. "
        "Hosted lists splash OP17 Elbaph search and Loki."
    ),
    "OP10-022": (
        "Green/Yellow OP10 Trafalgar Law is the Heart Pirates leader. "
        "The hosted OP17-format list splashes OP17 Shanks."
    ),
    "OP06-022": (
        "OP06 Yamato is green/yellow Wano Yamato - not black OP16 Yamato. "
        "The hosted list splashes OP17 Shanks."
    ),
    "ST14-001": (
        "ST14 Luffy is black 3D2Y Luffy. "
        "Current lists splash a wide OP17 Elbaph Straw Hat package."
    ),
    "EB02-010": (
        "EB02 Luffy is green/purple Film Red Luffy. "
        "The hosted OP17-format list splashes OP17 Yasopp."
    ),
    "OP14-040": (
        "Blue OP14 Jinbe is the Sun Pirates leader. "
        "OP17 Rocks Pirates cards are the current splash."
    ),
    "OP12-041": (
        "Blue/Purple OP12 Sanji is the Germa / Straw Hat leader. "
        "OP17 Rocks and Elbaph cards show up in current-format lists."
    ),
    "ST30-001": (
        "ST30 Luffy & Ace is red/green Whitebeard rush. "
        "Hosted lists keep the starter Ace package and splash OP17 Shanks and Newgate cards."
    ),
}

POPUP_JS = r"""
    (function(){
      var lines = document.querySelectorAll('.text-line');
      if (!lines.length) return;
      function resetPop(pop){
        pop.style.position = '';
        pop.style.left = '';
        pop.style.top = '';
        pop.style.right = '';
        pop.style.bottom = '';
        pop.classList.remove('flip-left', 'flip-down');
      }
      function place(line){
        var pop = line.querySelector('.card-pop');
        var title = line.querySelector('.card-title');
        if (!pop || !title) return;
        resetPop(pop);
        var tr = title.getBoundingClientRect();
        var width = pop.offsetWidth || 220;
        var height = pop.offsetHeight || 308;
        var left = tr.left;
        var top = tr.top - height - 10;
        if (left + width > window.innerWidth - 12) left = window.innerWidth - width - 12;
        if (left < 12) left = 12;
        if (top < 12) top = tr.bottom + 10;
        if (top + height > window.innerHeight - 12) top = Math.max(12, window.innerHeight - height - 12);
        pop.style.position = 'fixed';
        pop.style.left = left + 'px';
        pop.style.top = top + 'px';
        pop.style.bottom = 'auto';
        pop.style.right = 'auto';
      }
      lines.forEach(function(line){
        line.addEventListener('mouseenter', function(){ place(line); });
        line.addEventListener('focus', function(){ place(line); });
        line.addEventListener('click', function(e){
          if (window.matchMedia('(hover: hover)').matches) return;
          e.stopPropagation();
          lines.forEach(function(other){ if (other !== line) other.classList.remove('is-open'); });
          line.classList.toggle('is-open');
          place(line);
        });
      });
      document.addEventListener('click', function(e){
        if (!e.target.closest('.text-line')) {
          lines.forEach(function(line){ line.classList.remove('is-open'); });
        }
      });
    })();
"""


def parse_deck(path: Path, leader_id: str) -> dict[str, int] | None:
    text = path.read_text()
    cards: dict[str, int] = {}
    for n, cid in LINE_RE.findall(text):
        cid = cid.strip()
        if cid == leader_id:
            continue
        cards[cid] = cards.get(cid, 0) + int(n)
    if sum(cards.values()) < 40:
        return None
    return cards


def _has_op17(deck: dict[str, int]) -> bool:
    return any(cid.startswith("OP17-") for cid in deck)


def _average_decks(decks: list[dict[str, int]]) -> list[tuple[str, int, float]]:
    n = len(decks)
    play: dict[str, int] = defaultdict(int)
    copy_sum: dict[str, int] = defaultdict(int)
    for deck in decks:
        for cid, count in deck.items():
            play[cid] += 1
            copy_sum[cid] += count
    ranked = sorted(play, key=lambda cid: (-play[cid] / n, -copy_sum[cid] / play[cid], cid))
    picked: list[tuple[str, int, float]] = []
    total = 0
    for cid in ranked:
        rate = play[cid] / n
        if rate < 0.25 and total >= 46:
            continue
        copies = int(round(copy_sum[cid] / play[cid]))
        copies = max(1, min(4, copies))
        if total + copies > TARGET:
            copies = TARGET - total
        if copies <= 0:
            break
        picked.append((cid, copies, rate))
        total += copies
        if total >= TARGET:
            break
    if total < TARGET:
        have = {cid for cid, _c, _r in picked}
        for cid in ranked:
            if cid in have:
                continue
            need = TARGET - total
            copies = min(need, max(1, min(4, int(round(copy_sum[cid] / play[cid])))))
            picked.append((cid, copies, play[cid] / n))
            total += copies
            if total >= TARGET:
                break
    return picked


def _ensure_op17(
    picks: list[tuple[str, int, float]],
    op17_decks: list[dict[str, int]],
) -> list[tuple[str, int, float]]:
    have_copies = sum(c for cid, c, _r in picks if cid.startswith("OP17-"))
    if have_copies >= MIN_OP17_COPIES:
        return picks
    play: dict[str, int] = defaultdict(int)
    copy_sum: dict[str, int] = defaultdict(int)
    n = len(op17_decks)
    for deck in op17_decks:
        for cid, count in deck.items():
            if not cid.startswith("OP17-"):
                continue
            play[cid] += 1
            copy_sum[cid] += count
    ranked = sorted(play, key=lambda cid: (-play[cid] / n, -copy_sum[cid] / play[cid], cid))
    picked = {cid: (cid, copies, rate) for cid, copies, rate in picks}
    need = MIN_OP17_COPIES - have_copies
    for cid in ranked:
        if need <= 0:
            break
        copies = max(1, min(4, int(round(copy_sum[cid] / play[cid]))))
        if cid in picked:
            extra = min(4 - picked[cid][1], need)
            if extra <= 0:
                continue
            _id, old, rate = picked[cid]
            picked[cid] = (_id, old + extra, rate)
            need -= extra
            continue
        take = min(copies, need)
        picked[cid] = (cid, take, play[cid] / n)
        need -= take
    out = list(picked.values())
    total = sum(c for _i, c, _r in out)
    if total <= TARGET:
        return out
    # Drop the least-played non-OP17 cards until we are back at 50.
    flex = sorted(
        [row for row in out if not row[0].startswith("OP17-")],
        key=lambda row: (row[2], row[1], row[0]),
    )
    overflow = total - TARGET
    kept = {row[0]: row for row in out}
    for cid, copies, rate in flex:
        if overflow <= 0:
            break
        cut = min(copies, overflow)
        if cut >= copies:
            kept.pop(cid, None)
        else:
            kept[cid] = (cid, copies - cut, rate)
        overflow -= cut
    return list(kept.values())


def consensus_list(decks: list[dict[str, int]]) -> list[tuple[str, int, float]]:
    op17_decks = [deck for deck in decks if _has_op17(deck)]
    source = op17_decks if len(op17_decks) >= OP17_SUBSET_MIN else decks
    picks = _average_decks(source)
    if op17_decks:
        picks = _ensure_op17(picks, op17_decks)
    return picks


def grouped_from_picks(leader: dict, picks: list[tuple[str, int, float]], cache: dict) -> tuple[dict, dict]:
    grouped = {"Leader": [], "Characters": [], "Events": [], "Stages": []}
    totals = defaultdict(int)
    lid = leader["id"]
    grouped["Leader"].append(
        {
            "count": 1,
            "id": lid,
            "name": cache.get(lid, {}).get("name") or leader["name"],
            "group": "Leader",
        }
    )
    for cid, count, _rate in picks:
        meta = cache.get(cid) or {}
        cat = (meta.get("category") or "character").lower()
        if cat == "event":
            group = "Events"
        elif cat == "stage":
            group = "Stages"
        else:
            group = "Characters"
        grouped[group].append(
            {
                "count": count,
                "id": cid,
                "name": meta.get("name") or cid,
                "group": group,
            }
        )
        totals[group] += count

    def cost_key(item: dict) -> int:
        try:
            return int((cache.get(item["id"]) or {}).get("cost"))
        except (TypeError, ValueError):
            return 99

    for group in grouped:
        grouped[group].sort(
            key=lambda it: (
                cost_key(it),
                gen.display_name((cache.get(it["id"]) or {}).get("name") or it["name"]),
            )
        )
    return grouped, totals


def strategy_block(leader: dict) -> str:
    item = STRATEGY_PAGES.get(leader["id"])
    if not item:
        return ""
    href, title, note = item
    return f"""        <!-- LEADER_STRATEGY -->
        <section class="leader-strategy" style="margin-top:22px">
          <div class="section-title">
            <h3>Strategy</h3>
            <div class="muted">How this leader plays</div>
          </div>
          <ul class="list">
            <li>
              <a class="item" href="{html.escape(href)}">
                <div>
                  <div style="font-weight:700">{html.escape(title)}</div>
                  <div class="muted" style="font-size:13px">{html.escape(note)}</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>
          </ul>
        </section>
        <!-- /LEADER_STRATEGY -->
"""


def analysis_block(leader: dict, n: int, take: str, text_deck: str, op17_n: int = 0) -> str:
    text_deck = text_deck.replace("<h3>Text list</h3>", "<h3>Consensus list</h3>", 1)
    if op17_n >= OP17_SUBSET_MIN:
        extra = f", using the {op17_n} that play OP17 so the 50-card core includes the new set"
    elif op17_n:
        extra = (
            f", then folding in OP17 cards from the {op17_n} current-format "
            f"{'list' if op17_n == 1 else 'lists'}"
        )
    else:
        extra = ""
    averaged = (
        f'<p class="muted">Averaged from {n} lists on this page{extra}, then filled to 50 cards.</p>'
    )
    text_deck = text_deck.replace(
        '<p class="muted">Hover or tap a card name to see the picture. Copy pastes <code>NxSET-NNN</code> lines for OP TCG SIM import.</p>',
        averaged,
        1,
    )
    text_deck = text_deck.replace(
        '<p class="muted">Hover or tap a card name to see the picture. Copy pastes <code>NxSET-NNN</code> for OPTCGSim.</p>',
        averaged,
        1,
    )
    text_deck = text_deck.replace(
        '<p class="muted">Hover or tap a card name to see the picture.</p>',
        averaged,
        1,
    )
    if "Averaged from" not in text_deck:
        text_deck = text_deck.replace(
            '</div>\n          <div class="text-deck-cols">',
            f'</div>\n          {averaged}\n          <div class="text-deck-cols">',
            1,
        )
    return f"""        <!-- LEADER_ANALYSIS -->
        <section class="leader-analysis" style="margin-top:22px">
          <div class="section-title">
            <h3>How it plays</h3>
            <div class="muted">Staples from lists on this page</div>
          </div>
          <p class="leader-take">{html.escape(take)}</p>
        </section>
        <!-- /LEADER_ANALYSIS -->
{strategy_block(leader)}        <!-- CONSENSUS_LIST -->
{text_deck}
        <!-- /CONSENSUS_LIST -->
"""


def ensure_popup_js(page: str) -> str:
    if "querySelectorAll('.text-line')" in page:
        return page
    old = """  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
  </script>"""
    new = f"""  <script>
    document.getElementById('year').textContent = new Date().getFullYear();{POPUP_JS}
  </script>"""
    if old not in page:
        return page
    return page.replace(old, new, 1)


def inject(page: str, block: str) -> str:
    page = BLOCK_RE.sub("", page)
    marker = "        <!-- COMMUNITY_DECKLISTS -->"
    if marker not in page:
        marker = "        <!-- TOURNAMENT_DECKLISTS -->"
    if marker not in page:
        raise SystemExit("no insert marker")
    return page.replace(marker, block + "\n" + marker, 1)


def main() -> None:
    cache = gen.load_card_cache()
    index = {}
    for leader in gen.LEADERS:
        lid = leader["id"]
        decks = []
        for path in sorted((ROOT / leader["dir"]).glob("*.html")):
            parsed = parse_deck(path, lid)
            if parsed:
                decks.append({"slug": path.stem, "cards": parsed})
        raw_decks = [d["cards"] for d in decks]
        if not raw_decks:
            print(lid, "no decks")
            continue
        op17_n = sum(1 for d in raw_decks if _has_op17(d))
        picks = consensus_list(raw_decks)
        total = sum(c for _i, c, _r in picks)
        op17_c = sum(c for i, c, _r in picks if i.startswith("OP17-"))
        used = op17_n if op17_n >= OP17_SUBSET_MIN else len(raw_decks)
        print(lid, "from", used, "of", len(raw_decks), "lists", "cards", total, "op17", op17_c)
        grouped, totals = grouped_from_picks(leader, picks, cache)
        text_deck = gen.render_text_deck(grouped, cache, ["Leader", "Characters", "Events", "Stages"], totals)
        take = TAKES.get(lid) or (
            f"{leader['name']} ({lid}) lists on this site are hosted because they include OP17 cards."
        )
        block = analysis_block(leader, len(raw_decks), take, text_deck, op17_n)
        page_path = ROOT / leader["page"]
        page = inject(page_path.read_text(), block)
        page = ensure_popup_js(page)
        page_path.write_text(page)
        index[lid] = {
            "lists": len(raw_decks),
            "cards": [{"id": cid, "count": count, "rate": round(rate, 3)} for cid, count, rate in picks],
        }
    (ROOT / "data/consensus-decks.json").write_text(json.dumps(index, indent=2) + "\n")
    print("done")


if __name__ == "__main__":
    main()
