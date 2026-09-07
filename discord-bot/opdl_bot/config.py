"""Server layout, leaders, and copy for the OPDL Discord bot."""

from __future__ import annotations

from pathlib import Path

SITE_URL = "https://onepiecedecklists.com"
INVITE_URL = "https://discord.gg/adZ2WUQ3D"
REPO_ROOT = Path(__file__).resolve().parents[2]
BOT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = BOT_ROOT / "assets" / "emojis"
STATE_PATH = BOT_ROOT / "state.json"

# Discord channel names: lowercase, digits, hyphen.
# Discord emoji names: 2-32 chars, alphanumeric + underscore.

COLOR_HEX = {
    "color-red": 0xC62828,
    "color-green": 0x2E7D32,
    "color-blue": 0x1565C0,
    "color-purple": 0x6A1B9A,
    "color-black": 0x212121,
    "color-yellow": 0xF9A825,
    "color-red-green": 0x558B2F,
    "color-blue-yellow": 0x0288D1,
    "color-red-blue": 0xC2185B,
}

COLOR_UNICODE = {
    "color-red": "🔴",
    "color-green": "🟢",
    "color-blue": "🔵",
    "color-purple": "🟣",
    "color-black": "⚫",
    "color-yellow": "🟡",
    "color-red-green": "🟢",
    "color-blue-yellow": "🔵",
    "color-red-blue": "🔴",
}

LEADERS: list[dict] = [
    {
        "id": "OP17-001",
        "key": "edward-newgate",
        "name": "Edward Newgate",
        "short": "Newgate",
        "color": "color-red",
        "meta": "op17",
        "page": "/decklists/op17/edward-newgate.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP17/OP17-001_EN.webp",
        "search": ["whitebeard", "newgate", "edwardnewgate"],
        "take": (
            "Red OP17 Edward Newgate is a Whitebeard beatstick that keeps 8000-power bodies on the board. "
            "Core lists play Sanji, Portgas D. Ace, Izo, ten-cost Edward Newgate, Kouzuki Oden, Marco, Uta, and Moby Dick."
        ),
    },
    {
        "id": "OP17-020",
        "key": "shanks",
        "name": "Shanks",
        "short": "Shanks",
        "color": "color-green",
        "meta": "op17",
        "page": "/decklists/op17/shanks.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP17/OP17-020_EN.webp",
        "search": ["shanks", "redhair"],
        "take": (
            "Green OP17 Shanks rests the board and plays Red Hair Pirates. "
            "Every list locks Benn Beckman, Yasopp, and the ten-cost Shanks."
        ),
    },
    {
        "id": "OP17-039",
        "key": "rocks-d-xebec",
        "name": "Rocks D. Xebec",
        "short": "Xebec",
        "color": "color-blue",
        "meta": "op17",
        "page": "/decklists/op17/rocks-d-xebec.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP17/OP17-039_EN.webp",
        "search": ["xebec", "rocks"],
        "take": (
            "Blue OP17 Rocks D. Xebec is a dense Rocks Pirates pile: Newgate, Shiki, Linlin, Gloriosa, "
            "Stussy, Rocks, the stage, and There's No Authority."
        ),
    },
    {
        "id": "OP17-058",
        "key": "kaido",
        "name": "Kaido",
        "short": "Kaido",
        "color": "color-purple",
        "meta": "op17",
        "page": "/decklists/op17/kaido.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP17/OP17-058_EN.webp",
        "search": ["kaido"],
        "take": (
            "Purple OP17 Kaido is All-Star midrange. King, Queen, Basil Hawkins, Yamato, "
            "on-leader Kaido, Mamaragan, and We're Going to Claim the One Piece are the core."
        ),
    },
    {
        "id": "OP17-079",
        "key": "monkey-d-luffy",
        "name": "Monkey D. Luffy",
        "short": "OP17 Luffy",
        "color": "color-black",
        "meta": "op17",
        "page": "/decklists/op17/monkey-d-luffy.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP17/OP17-079_EN.webp",
        "search": ["luffy", "strawhat", "elbaph"],
        "take": (
            "Black OP17 Monkey D. Luffy is the Elbaph blocker deck, not Imu. "
            "Usopp, Gerd, and Loki are 4-ofs; most lists also play Saul, a Luffy beater, Zoro, and Robin."
        ),
    },
    {
        "id": "OP17-099",
        "key": "charlotte-linlin",
        "name": "Charlotte Linlin",
        "short": "Linlin",
        "color": "color-yellow",
        "meta": "op17",
        "page": "/decklists/op17/charlotte-linlin.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP17/OP17-099_EN.webp",
        "search": ["linlin", "bigmom", "big-mom"],
        "take": (
            "Yellow OP17 Charlotte Linlin is a Big Mom swarm leader. "
            "Pudding, on-color Linlin, and Cracker are in every averaged list."
        ),
    },
    {
        "id": "OP13-001",
        "key": "rg-luffy",
        "name": "RG Luffy",
        "short": "RG Luffy",
        "color": "color-red-green",
        "meta": "format",
        "page": "/decklists/rg-luffy.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP13/OP13-001_EN.webp",
        "search": ["luffy"],
        "take": (
            "RG Luffy is a Straw Hat value pile still posting in current format. "
            "Lists average Sanji, Usopp, Nami, EB04 Zoro, Brook, Charlestone, starter Luffy, and Thousand Sunny."
        ),
    },
    {
        "id": "OP11-041",
        "key": "nami",
        "name": "Nami",
        "short": "Nami",
        "color": "color-blue-yellow",
        "meta": "format",
        "page": "/decklists/nami.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP11/OP11-041_EN.webp",
        "search": ["nami"],
        "take": (
            "Blue/Yellow Nami draws when Life cards leave, then plays a Thriller Bark yellow package. "
            "Kumacy, Gecko Moria, Nico Robin, Nami, Borsalino, and Perona are the average core."
        ),
    },
    {
        "id": "OP14-020",
        "key": "mihawk",
        "name": "Mihawk",
        "short": "Mihawk",
        "color": "color-green",
        "meta": "format",
        "page": "/decklists/mihawk.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP14/OP14-020_EN.webp",
        "search": ["mihawk"],
        "take": (
            "Green Mihawk is a rest/control pile. Limitless lists play Perona (both printings), "
            "Law & Bepo, Kin'emon, Kouzuki Oden, the Mihawk character, and Dead Man's Game."
        ),
    },
    {
        "id": "OP16-001",
        "key": "portgas-d-ace",
        "name": "Portgas D. Ace",
        "short": "OP16 Ace",
        "color": "color-red",
        "meta": "format",
        "page": "/decklists/portgas-d-ace.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP16/OP16-001_EN.webp",
        "search": ["ace", "portgas"],
        "take": (
            "Red OP16 Portgas D. Ace is Whitebeard rush - not the red/blue OP13 Ace. "
            "Lists lock Monkey D. Luffy, Edward Newgate, Vista, and Moby Dick."
        ),
    },
    {
        "id": "OP13-002",
        "key": "op13-ace",
        "name": "OP13 Ace",
        "short": "OP13 Ace",
        "color": "color-red-blue",
        "meta": "format",
        "page": "/decklists/op13-ace.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP13/OP13-002_EN.webp",
        "search": ["ace", "portgas"],
        "take": (
            "OP13 Ace is red/blue Portgas D. Ace - 3 life, 6000 power - not the red OP16 Ace rush deck. "
            "Trash a card to give −2000, then draw when you take damage or a 6000-power body dies."
        ),
    },
    {
        "id": "OP13-079",
        "key": "imu",
        "name": "Imu",
        "short": "Imu",
        "color": "color-black",
        "meta": "format",
        "page": "/decklists/imu.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP13/OP13-079_EN.webp",
        "search": ["imu"],
        "take": (
            "Black OP13 Imu is Mary Geoise / Five Elders, not OP17 Elbaph Luffy. "
            "No 2-cost or higher events, and the Empty Throne stage starts in play from deck."
        ),
    },
    {
        "id": "OP15-058",
        "key": "enel",
        "name": "Enel",
        "short": "Enel",
        "color": "color-purple",
        "meta": "format",
        "page": "/decklists/enel.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP15/OP15-058_EN.webp",
        "search": ["enel", "eneru"],
        "take": (
            "Purple OP15 Enel is Sky Island ramp: a 6-card DON!! deck that floods DON!! from turn two "
            "and rests the board. This is not yellow OP05 Enel."
        ),
    },
    {
        "id": "OP11-062",
        "key": "charlotte-katakuri",
        "name": "Charlotte Katakuri",
        "short": "Katakuri",
        "color": "color-purple",
        "meta": "format",
        "page": "/decklists/charlotte-katakuri.html",
        "image": "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/OP11/OP11-062_EN.webp",
        "search": ["katakuri"],
        "take": (
            "Purple OP11 Charlotte Katakuri is the other Big Mom leader, separate from yellow OP17 Linlin. "
            "DON!! −1 on attack or on the opponent's attack to peek their deck and gain power."
        ),
    },
]

METAS: list[dict] = [
    {
        "key": "op17",
        "name": "OP17",
        "category": "OP17 · World's Strongest Warriors",
        "discussion": "op17-meta",
        "topic": "Current English meta. Discuss OP17 as a format here; leader rooms are for that deck.",
    },
    {
        "key": "format",
        "name": "Format staples",
        "category": "Format staples",
        "discussion": "format-talk",
        "topic": "Site leaders still posting in OP17 that are not OP17-set leaders.",
    },
]

GENERIC_CATEGORIES: list[dict] = [
    {
        "key": "information",
        "name": "Information",
        "channels": [
            {
                "key": "welcome",
                "name": "welcome",
                "kind": "text",
                "readonly": True,
                "topic": "Start here. What this server is and where to go next.",
            },
            {
                "key": "rules",
                "name": "rules",
                "kind": "text",
                "readonly": True,
                "topic": "How we play in this room.",
            },
            {
                "key": "announcements",
                "name": "announcements",
                "kind": "news",
                "readonly": True,
                "topic": "Site updates, meta snapshots, and shop notes.",
            },
            {
                "key": "flair",
                "name": "flair",
                "kind": "text",
                "readonly": True,
                "topic": "Pick your favorite OPTCG leader. One flair at a time.",
            },
        ],
    },
    {
        "key": "community",
        "name": "Community",
        "channels": [
            {
                "key": "general",
                "name": "general",
                "kind": "text",
                "readonly": False,
                "topic": "Anything OPTCG that does not belong in a leader room.",
            },
            {
                "key": "deck-help",
                "name": "deck-help",
                "kind": "text",
                "readonly": False,
                "topic": "Paste a 50-card list. Ask for cuts, tech, and matchup advice.",
            },
            {
                "key": "tournament-talk",
                "name": "tournament-talk",
                "kind": "text",
                "readonly": False,
                "topic": "Results, pairings, and what actually tabled.",
            },
            {
                "key": "shop-orders",
                "name": "shop-orders",
                "kind": "text",
                "readonly": False,
                "topic": "Playmats, dice, sleeves, custom leaders. Product + city + quantity.",
            },
            {
                "key": "off-topic",
                "name": "off-topic",
                "kind": "text",
                "readonly": False,
                "topic": "One Piece, other games, anything that is not a decklist.",
            },
        ],
    },
]


def emoji_name(leader: dict) -> str:
    return leader["key"].replace("-", "_")[:32]


def role_name(leader: dict) -> str:
    return f"Leader · {leader['name']}"


def channel_name(leader: dict) -> str:
    return leader["key"]


def site_url(leader: dict) -> str:
    return SITE_URL + leader["page"]


def leaders_for_meta(meta_key: str) -> list[dict]:
    return [L for L in LEADERS if L["meta"] == meta_key]


def leader_by_key(key: str) -> dict | None:
    for leader in LEADERS:
        if leader["key"] == key:
            return leader
    return None


def planned_channel_names() -> list[str]:
    names: list[str] = []
    for cat in GENERIC_CATEGORIES:
        for ch in cat["channels"]:
            names.append(ch["name"])
    for meta in METAS:
        names.append(meta["discussion"])
        for leader in leaders_for_meta(meta["key"]):
            names.append(channel_name(leader))
    return names


WELCOME_BODY = """**One Piece Decklists**

This is the Discord for [onepiecedecklists.com]({site}) - OPTCG decklists, consensus 50-card lists, and fan gear.

**Where to go**
- {rules} - how we talk in here
- {announcements} - site and meta updates
- {flair} - pick your favorite leader (one face, one role)
- Leader rooms under **OP17** and **Format staples** - each site leader has a channel with the current consensus list pinned
- {shop} - playmats, dice, sleeves, custom leaders

Not affiliated with Bandai or Shueisha. Fan site.
"""

RULES_BODY = """**Rules**

1. Be civil. Argue the list, not the person.
2. English constructed, current format, unless a channel says otherwise.
3. Paste real 50-card lists when you ask for help. Card IDs (`OP17-003`) beat nicknames.
4. Leader rooms are for that leader. Cross-meta talk goes in {meta} or {general}.
5. Spoilers for anime/manga get a spoiler tag. Card spoilers for unreleased English product get a warning in the first line.
6. No scalping spam, fake listings, or unofficial proxies passed off as English product.
7. Shop orders stay in {shop}. Include product, color, quantity, and shipping city.
8. Mods can move or delete posts that miss the room. Repeat problems lose chat.

Site: {site}
"""

ANNOUNCEMENTS_BODY = """**Welcome to the OPDL Discord**

The bot laid out this server from the site:

- Generic rooms: welcome, rules, announcements, flair, general, deck help, tournaments, shop, off-topic
- **OP17** - one channel per OP17 leader, plus an OP17 meta room
- **Format staples** - every other leader page on the site (RG Luffy, Nami, Mihawk, both Aces, Imu, Enel, Katakuri)

Each leader channel has a **pinned consensus list** averaged from the lists on that page. Use `/opdl-consensus` (admins) after the site refresh to update them.

Grab a leader flair in {flair}.
"""

FLAIR_BODY = """**Leader flair**

Pick the OPTCG leader you actually play - or the one you like looking at. One favorite at a time.

Buttons use a little One Piece face cropped from that leader's card (the same Limitless art as the site). Click again on another leader to swap. Clear flair drops the role.
"""
