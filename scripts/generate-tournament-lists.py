#!/usr/bin/env python3
"""Build per-leader tournament decklist pages from Limitless Play standings."""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/workspace")
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"
MAX_LISTS = 8
MIN_CARDS = 45
TOURNAMENT_LIMIT = 80
# Official constructed ban (Blue Charlotte Pudding, including parallels).
# Other Pudding prints stay legal: OP17-109, ST20-004, EB03-035, OP12-071,
# OP08-067, OP11-070, PRB02-010.
BANNED_CARDS = {"OP06-047"}

LEADERS = [
    {
        "id": "OP17-001",
        "key": "edward-newgate",
        "page": "decklists/op17/edward-newgate.html",
        "dir": "decklists/op17/edward-newgate",
        "name": "Edward Newgate",
        "color": "color-red",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": True,
        "pool_heading": "OP17 card pool",
        "pool_note": "All cards of this leader's color from the set",
    },
    {
        "id": "OP17-020",
        "key": "shanks",
        "page": "decklists/op17/shanks.html",
        "dir": "decklists/op17/shanks",
        "name": "Shanks",
        "color": "color-green",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": True,
        "pool_heading": "OP17 card pool",
        "pool_note": "All cards of this leader's color from the set",
    },
    {
        "id": "OP17-039",
        "key": "rocks-d-xebec",
        "page": "decklists/op17/rocks-d-xebec.html",
        "dir": "decklists/op17/rocks-d-xebec",
        "name": "Rocks D. Xebec",
        "color": "color-blue",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": True,
        "pool_heading": "OP17 card pool",
        "pool_note": "All cards of this leader's color from the set",
    },
    {
        "id": "OP17-058",
        "key": "kaido",
        "page": "decklists/op17/kaido.html",
        "dir": "decklists/op17/kaido",
        "name": "Kaido",
        "color": "color-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": True,
        "pool_heading": "OP17 card pool",
        "pool_note": "All cards of this leader's color from the set",
    },
    {
        "id": "OP17-079",
        "key": "monkey-d-luffy",
        "page": "decklists/op17/monkey-d-luffy.html",
        "dir": "decklists/op17/monkey-d-luffy",
        "name": "Monkey D. Luffy",
        "color": "color-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": True,
        "pool_heading": "OP17 card pool",
        "pool_note": "All cards of this leader's color from the set",
    },
    {
        "id": "OP17-099",
        "key": "charlotte-linlin",
        "page": "decklists/op17/charlotte-linlin.html",
        "dir": "decklists/op17/charlotte-linlin",
        "name": "Charlotte Linlin",
        "color": "color-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": True,
        "pool_heading": "OP17 card pool",
        "pool_note": "All cards of this leader's color from the set",
    },
    {
        "id": "OP13-001",
        "key": "rg-luffy",
        "page": "decklists/rg-luffy.html",
        "dir": "decklists/rg-luffy",
        "name": "RG Luffy",
        "color": "color-red-green",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP11-041",
        "key": "nami",
        "page": "decklists/nami.html",
        "dir": "decklists/nami",
        "name": "Nami",
        "color": "color-blue-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP14-020",
        "key": "mihawk",
        "page": "decklists/mihawk.html",
        "dir": "decklists/mihawk",
        "name": "Mihawk",
        "color": "color-green",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP16-001",
        "key": "portgas-d-ace",
        "page": "decklists/portgas-d-ace.html",
        "dir": "decklists/portgas-d-ace",
        "name": "Portgas D. Ace",
        "color": "color-red",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP15-058",
        "key": "enel",
        "page": "decklists/enel.html",
        "dir": "decklists/enel",
        "name": "Enel",
        "color": "color-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP11-062",
        "key": "charlotte-katakuri",
        "page": "decklists/charlotte-katakuri.html",
        "dir": "decklists/charlotte-katakuri",
        "name": "Charlotte Katakuri",
        "color": "color-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP13-079",
        "key": "imu",
        "page": "decklists/imu.html",
        "dir": "decklists/imu",
        "name": "Imu",
        "color": "color-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP13-002",
        "key": "op13-ace",
        "page": "decklists/op13-ace.html",
        "dir": "decklists/op13-ace",
        "name": "OP13 Ace",
        "color": "color-red-blue",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP16-022",
        "key": "gb-luffy",
        "page": "decklists/gb-luffy.html",
        "dir": "decklists/gb-luffy",
        "name": "GB Luffy",
        "color": "color-green-blue",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP16-080",
        "key": "blackbeard",
        "page": "decklists/blackbeard.html",
        "dir": "decklists/blackbeard",
        "name": "Blackbeard",
        "color": "color-black-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP12-061",
        "key": "rosinante",
        "page": "decklists/rosinante.html",
        "dir": "decklists/rosinante",
        "name": "Rosinante",
        "color": "color-purple-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP15-002",
        "key": "lucy",
        "page": "decklists/lucy.html",
        "dir": "decklists/lucy",
        "name": "Lucy",
        "color": "color-red-blue",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP16-079",
        "key": "yamato",
        "page": "decklists/yamato.html",
        "dir": "decklists/yamato",
        "name": "Yamato",
        "color": "color-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP11-001",
        "key": "koby",
        "page": "decklists/koby.html",
        "dir": "decklists/koby",
        "name": "Koby",
        "color": "color-red-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP14-060",
        "key": "doffy",
        "page": "decklists/doffy.html",
        "dir": "decklists/doffy",
        "name": "Doffy",
        "color": "color-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP16-041",
        "key": "buggy",
        "page": "decklists/buggy.html",
        "dir": "decklists/buggy",
        "name": "Buggy",
        "color": "color-blue",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP16-060",
        "key": "sengoku",
        "page": "decklists/sengoku.html",
        "dir": "decklists/sengoku",
        "name": "Sengoku",
        "color": "color-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP11-040",
        "key": "up-luffy",
        "page": "decklists/up-luffy.html",
        "dir": "decklists/up-luffy",
        "name": "UP Luffy",
        "color": "color-blue-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP08-058",
        "key": "charlotte-pudding",
        "page": "decklists/charlotte-pudding.html",
        "dir": "decklists/charlotte-pudding",
        "name": "Charlotte Pudding",
        "color": "color-purple-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP13-004",
        "key": "sabo",
        "page": "decklists/sabo.html",
        "dir": "decklists/sabo",
        "name": "Sabo",
        "color": "color-red-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP09-062",
        "key": "nico-robin",
        "page": "decklists/nico-robin.html",
        "dir": "decklists/nico-robin",
        "name": "Nico Robin",
        "color": "color-purple-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP14-080",
        "key": "gecko-moria",
        "page": "decklists/gecko-moria.html",
        "dir": "decklists/gecko-moria",
        "name": "Gecko Moria",
        "color": "color-black-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP14-041",
        "key": "boa-hancock",
        "page": "decklists/boa-hancock.html",
        "dir": "decklists/boa-hancock",
        "name": "Boa Hancock",
        "color": "color-blue-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP12-081",
        "key": "koala",
        "page": "decklists/koala.html",
        "dir": "decklists/koala",
        "name": "Koala",
        "color": "color-black-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP09-001",
        "key": "op09-shanks",
        "page": "decklists/op09-shanks.html",
        "dir": "decklists/op09-shanks",
        "name": "OP09 Shanks",
        "color": "color-red",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP05-098",
        "key": "op05-enel",
        "page": "decklists/op05-enel.html",
        "dir": "decklists/op05-enel",
        "name": "OP05 Enel",
        "color": "color-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "ST10-002",
        "key": "st10-luffy",
        "page": "decklists/st10-luffy.html",
        "dir": "decklists/st10-luffy",
        "name": "ST10 Luffy",
        "color": "color-red-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP09-061",
        "key": "op09-luffy",
        "page": "decklists/op09-luffy.html",
        "dir": "decklists/op09-luffy",
        "name": "OP09 Luffy",
        "color": "color-purple-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "ST13-003",
        "key": "st13-luffy",
        "page": "decklists/st13-luffy.html",
        "dir": "decklists/st13-luffy",
        "name": "ST13 Luffy",
        "color": "color-black-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP12-040",
        "key": "kuzan",
        "page": "decklists/kuzan.html",
        "dir": "decklists/kuzan",
        "name": "Kuzan",
        "color": "color-blue",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP05-002",
        "key": "belo-betty",
        "page": "decklists/belo-betty.html",
        "dir": "decklists/belo-betty",
        "name": "Belo Betty",
        "color": "color-red-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "EB04-001",
        "key": "jewelry-bonney",
        "page": "decklists/jewelry-bonney.html",
        "dir": "decklists/jewelry-bonney",
        "name": "Jewelry Bonney",
        "color": "color-red-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP10-099",
        "key": "eustass-kid",
        "page": "decklists/eustass-kid.html",
        "dir": "decklists/eustass-kid",
        "name": "Eustass Kid",
        "color": "color-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP07-059",
        "key": "foxy",
        "page": "decklists/foxy.html",
        "dir": "decklists/foxy",
        "name": "Foxy",
        "color": "color-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "ST13-001",
        "key": "st13-sabo",
        "page": "decklists/st13-sabo.html",
        "dir": "decklists/st13-sabo",
        "name": "ST13 Sabo",
        "color": "color-red-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP05-041",
        "key": "sakazuki",
        "page": "decklists/sakazuki.html",
        "dir": "decklists/sakazuki",
        "name": "Sakazuki",
        "color": "color-blue-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP05-060",
        "key": "op05-luffy",
        "page": "decklists/op05-luffy.html",
        "dir": "decklists/op05-luffy",
        "name": "OP05 Luffy",
        "color": "color-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP07-079",
        "key": "rob-lucci",
        "page": "decklists/rob-lucci.html",
        "dir": "decklists/rob-lucci",
        "name": "Rob Lucci",
        "color": "color-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP10-022",
        "key": "trafalgar-law",
        "page": "decklists/trafalgar-law.html",
        "dir": "decklists/trafalgar-law",
        "name": "Trafalgar Law",
        "color": "color-green-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP06-022",
        "key": "op06-yamato",
        "page": "decklists/op06-yamato.html",
        "dir": "decklists/op06-yamato",
        "name": "OP06 Yamato",
        "color": "color-green-yellow",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "ST14-001",
        "key": "st14-luffy",
        "page": "decklists/st14-luffy.html",
        "dir": "decklists/st14-luffy",
        "name": "ST14 Luffy",
        "color": "color-black",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "EB02-010",
        "key": "eb02-luffy",
        "page": "decklists/eb02-luffy.html",
        "dir": "decklists/eb02-luffy",
        "name": "EB02 Luffy",
        "color": "color-green-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP14-040",
        "key": "jinbe",
        "page": "decklists/jinbe.html",
        "dir": "decklists/jinbe",
        "name": "Jinbe",
        "color": "color-blue",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "OP12-041",
        "key": "sanji",
        "page": "decklists/sanji.html",
        "dir": "decklists/sanji",
        "name": "Sanji",
        "color": "color-blue-purple",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
    {
        "id": "ST30-001",
        "key": "luffy-ace",
        "page": "decklists/luffy-ace.html",
        "dir": "decklists/luffy-ace",
        "name": "Luffy & Ace",
        "color": "color-red-green",
        "crumb": ("/decklists/op17.html", "OP17 decklists"),
        "nav_op17": False,
        "pool_heading": "Card pictures",
        "pool_note": "English names and art from Limitless",
    },
]


def http_json(url: str, retries: int = 6):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read())
        except Exception as exc:  # noqa: BLE001
            last = exc
            wait = 0.5 * (attempt + 1)
            if "429" in str(exc):
                wait = 8 * (attempt + 1)
            time.sleep(wait)
    raise last


def card_id(set_code: str, number) -> str:
    num = str(number).strip()
    if num.isdigit():
        num = num.zfill(3)
    return f"{set_code}-{num}"


def display_name(name: str) -> str:
    if not name:
        return ""
    s = re.sub(r"\.D\.", " D. ", name)
    s = re.sub(r"(?<!D)\.", " ", s)
    return " ".join(s.split())


def ordinal(n) -> str | None:
    if n is None:
        return None
    try:
        n = int(n)
    except (TypeError, ValueError):
        return None
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def slugify(text: str) -> str:
    s = display_name(text).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:70] or "list"


def record_text(record) -> str:
    if not isinstance(record, dict):
        return ""
    w = record.get("wins") or 0
    l = record.get("losses") or 0
    t = record.get("ties") or 0
    if not w and not l and not t:
        return ""
    if t:
        return f"{w}-{l}-{t}"
    return f"{w}-{l}"


def deck_signature(dl: dict) -> str:
    parts = []
    for key in ("character", "event", "stage"):
        for card in dl.get(key) or []:
            parts.append(f"{card.get('count')}x{card.get('set')}-{card.get('number')}")
    return "|".join(sorted(parts))


def count_cards(dl: dict) -> int:
    total = 0
    for key in ("character", "event", "stage"):
        for card in dl.get(key) or []:
            try:
                total += int(card.get("count") or 0)
            except (TypeError, ValueError):
                pass
    return total


def deck_has_banned(dl: dict) -> bool:
    return any(item["id"] in BANNED_CARDS for item in flatten_cards(dl))


def deck_has_op17(dl: dict) -> bool:
    return any((item.get("id") or "").startswith("OP17-") for item in flatten_cards(dl))


def page_has_banned(text: str) -> bool:
    return any(cid in text for cid in BANNED_CARDS)


def flatten_cards(dl: dict) -> list[dict]:
    out = []
    leader = dl.get("leader") or {}
    if leader.get("set"):
        out.append(
            {
                "count": 1,
                "id": card_id(leader["set"], leader.get("number")),
                "name": leader.get("name") or "",
                "group": "Leader",
            }
        )
    groups = (("character", "Characters"), ("event", "Events"), ("stage", "Stages"))
    for key, group in groups:
        for card in dl.get(key) or []:
            out.append(
                {
                    "count": int(card.get("count") or 0),
                    "id": card_id(card.get("set"), card.get("number")),
                    "name": card.get("name") or "",
                    "group": group,
                }
            )
    return out


def date_sort_key(entry: dict) -> tuple:
    """Newest Limitless event date first; better placing breaks a same-day tie."""
    date = entry.get("date") or "0000-00-00"
    placing = entry.get("placing")
    placing_n = int(placing) if placing is not None else 10_000
    return (date, -placing_n)


def quality_key(entry: dict) -> tuple:
    placing = entry.get("placing")
    placing_n = int(placing) if placing is not None else 10_000
    rec = entry.get("record") or {}
    wins = rec.get("wins") or 0
    players = entry.get("players") or 0
    date = entry.get("date") or ""
    cards = count_cards(entry.get("decklist") or {})
    return (placing_n, -wins, -players, -cards, date)


def select_lists(entries: list[dict], limit: int = MAX_LISTS) -> list[dict]:
    unique = []
    seen = set()
    for entry in sorted(entries, key=quality_key):
        dl = entry.get("decklist") or {}
        if count_cards(dl) < MIN_CARDS:
            continue
        if deck_has_banned(dl):
            continue
        sig = deck_signature(dl)
        if sig in seen:
            continue
        seen.add(sig)
        unique.append(entry)
    picked = []
    per_event = defaultdict(int)
    for entry in unique:
        tid = entry.get("tournament_id") or ""
        if per_event[tid] >= 2:
            continue
        picked.append(entry)
        per_event[tid] += 1
        if len(picked) >= limit:
            return picked
    for entry in unique:
        if entry in picked:
            continue
        picked.append(entry)
        if len(picked) >= limit:
            break
    return picked


def fetch_standings(tournaments: list[dict], target_ids: set[str]) -> dict[str, list]:
    by_leader = defaultdict(list)
    skip_re = re.compile(r"\b(draft|sealed)\b", re.I)
    eligible = [t for t in tournaments if t.get("id") and not skip_re.search(t.get("name") or "")]
    lock = defaultdict(list)

    def one(tourney: dict) -> list[tuple[str, dict]]:
        tid = tourney["id"]
        time.sleep(0.03)
        try:
            standings = http_json(f"https://play.limitlesstcg.com/api/tournaments/{tid}/standings")
        except Exception as exc:  # noqa: BLE001
            print("standings fail", tid, exc)
            return []
        found = []
        for row in standings:
            dl = row.get("decklist") or {}
            leader = dl.get("leader") or {}
            if not leader.get("set"):
                continue
            lid = card_id(leader["set"], leader.get("number"))
            if lid not in target_ids:
                continue
            found.append(
                (
                    lid,
                    {
                        "tournament_id": tid,
                        "tournament_name": tourney.get("name") or "Limitless event",
                        "date": (tourney.get("date") or "")[:10],
                        "players": tourney.get("players") or 0,
                        "player": row.get("name") or "Unknown",
                        "placing": row.get("placing"),
                        "record": row.get("record") or {},
                        "decklist": dl,
                        "source_url": f"https://play.limitlesstcg.com/tournament/{tid}/standings",
                        "kind": "tournament",
                    },
                )
            )
        return found

    done = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(one, t) for t in eligible]
        for fut in as_completed(futures):
            for lid, entry in fut.result():
                lock[lid].append(entry)
            done += 1
            if done % 40 == 0:
                print(f"  processed {done}/{len(eligible)} events")
    for lid, rows in lock.items():
        by_leader[lid].extend(rows)
    return by_leader


def featured_from_other_leaders() -> dict[str, dict]:
    path = ROOT / "data/other-leaders.json"
    data = json.loads(path.read_text())
    mapping = {
        "rg-luffy": "OP13-001",
        "uy-nami": "OP11-041",
        "mihawk": "OP14-020",
    }
    extra = {}
    for key, lid in mapping.items():
        lst = data["lists"][key]
        grouped = {"leader": None, "character": [], "event": [], "stage": []}
        for card in lst["cards"]:
            cid = card["id"]
            set_code, number = cid.split("-", 1)
            item = {"count": card["count"], "name": card["name"].split(" (")[0], "set": set_code, "number": number}
            group = (card.get("group") or "").lower()
            if group.startswith("leader"):
                grouped["leader"] = {"name": item["name"], "set": set_code, "number": number}
            elif group.startswith("event"):
                grouped["event"].append(item)
            elif group.startswith("stage"):
                grouped["stage"].append(item)
            else:
                grouped["character"].append(item)
        desc = lst.get("description") or lst.get("title") or ""
        player = ""
        m = re.search(r"by ([^–-]+) -", desc)
        if m:
            player = m.group(1).strip()
        placing = None
        m = re.search(r"(\d+)(?:st|nd|rd|th) Place", desc, re.I)
        if m:
            placing = int(m.group(1))
        event = desc
        m = re.search(r"Place (.+?) - \d", desc)
        if m:
            event = m.group(1).strip()
        extra[lid] = {
            "tournament_id": f"limitless-{lst.get('list_id')}",
            "tournament_name": event,
            "date": "",
            "players": 0,
            "player": player,
            "placing": placing,
            "record": {},
            "decklist": grouped,
            "source_url": lst.get("list_url"),
            "kind": "featured",
            "title_override": None,
            "subtitle": desc,
            "forced_slug": f"featured-{slugify(player or 'list')}",
        }
    return extra


def newgate_samples(op17: dict) -> list[dict]:
    red = [
        c
        for c in op17.values()
        if c.get("color") == "Red" and c.get("category") != "Leader"
    ]
    chars = [c for c in red if c.get("category") == "Character"]
    events = [c for c in red if c.get("category") == "Event"]
    stages = [c for c in red if c.get("category") == "Stage"]

    def pack(counts: dict[str, int]) -> dict:
        grouped = {
            "leader": {"name": "Edward.Newgate", "set": "OP17", "number": "001"},
            "character": [],
            "event": [],
            "stage": [],
        }
        for card in chars + events + stages:
            n = counts.get(card["id"], 0)
            if not n:
                continue
            set_code, number = card["id"].split("-", 1)
            bucket = {"Character": "character", "Event": "event", "Stage": "stage"}[card["category"]]
            grouped[bucket].append({"count": n, "name": card["name"], "set": set_code, "number": number})
        return grouped

    def fill(priority: list[str], event_ids: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        remaining = 50
        for cid in event_ids:
            n = min(4, remaining)
            counts[cid] = n
            remaining -= n
        for cid in priority:
            if remaining <= 0:
                break
            n = min(4, remaining)
            counts[cid] = n
            remaining -= n
        if remaining:
            for card in chars:
                if remaining <= 0:
                    break
                have = counts.get(card["id"], 0)
                if have >= 4:
                    continue
                add = min(4 - have, remaining)
                counts[card["id"]] = have + add
                remaining -= add
        return counts

    char_ids = [c["id"] for c in chars]
    event_ids = [c["id"] for c in events]
    # Aggressive: events last, finishers first
    a = fill(list(reversed(char_ids)), event_ids)
    # Search/value: events first already, then cheap characters
    b = fill(char_ids, event_ids)
    # Toolbox: 2-ofs across the pool
    c = {}
    left = 50
    for cid in event_ids + char_ids:
        n = min(2, left)
        c[cid] = n
        left -= n
    for cid in char_ids:
        if left <= 0:
            break
        have = c.get(cid, 0)
        if have >= 4:
            continue
        add = min(4 - have, left)
        c[cid] = have + add
        left -= add

    samples = [
        (
            "sample-whitebeard-finishers",
            "Sample starter - finishers",
            "50-card OP17 Red Whitebeard package. Not a tournament list - no Limitless results found for OP17-001 yet.",
            a,
        ),
        (
            "sample-whitebeard-search",
            "Sample starter - search and events",
            "50-card OP17 Red Whitebeard package with events maxed. Not a tournament list.",
            b,
        ),
        (
            "sample-whitebeard-toolbox",
            "Sample starter - toolbox",
            "50-card OP17 Red Whitebeard package with more 2-ofs. Not a tournament list.",
            c,
        ),
    ]
    out = []
    for slug, title, subtitle, counts in samples:
        dl = pack(counts)
        out.append(
            {
                "tournament_id": slug,
                "tournament_name": title,
                "date": "",
                "players": 0,
                "player": "Sample starter",
                "placing": None,
                "record": {},
                "decklist": dl,
                "source_url": "https://onepiece.limitlesstcg.com/cards/OP17-001",
                "kind": "sample",
                "title_override": title,
                "subtitle": subtitle,
                "forced_slug": slug,
            }
        )
    return out


def load_card_cache() -> dict:
    cache = {}
    op17 = json.loads((ROOT / "data/op17-cards.json").read_text())
    for cid, card in op17.items():
        cache[cid] = card
    other = json.loads((ROOT / "data/other-leaders.json").read_text())
    for cid, card in other.get("cards", {}).items():
        cache[cid] = card
    extra_path = ROOT / "data/card-cache.json"
    if extra_path.exists():
        cache.update(json.loads(extra_path.read_text()))
    return cache


def fetch_card(cid: str) -> dict | None:
    url = f"https://onepiece.limitlesstcg.com/api/cards/{cid}"
    try:
        data = http_json(url)
    except urllib.error.HTTPError:
        return None
    except Exception:  # noqa: BLE001
        return None
    set_code = data.get("set") or cid.split("-")[0]
    effect = data.get("effect") or ""
    trigger = data.get("trigger") or ""
    text = " ".join(p for p in (effect, trigger) if p)
    counter = data.get("counter")
    counter_s = f"+{counter}" if counter else None
    cat = (data.get("category") or "Character").title()
    return {
        "id": data.get("card_id") or cid,
        "name": data.get("name") or cid,
        "category": cat,
        "color": (data.get("color") or "").title(),
        "life": str(data["life"]) if data.get("life") is not None else None,
        "cost": str(data["cost"]) if data.get("cost") is not None else None,
        "power": str(data["power"]) if data.get("power") is not None else None,
        "counter": counter_s,
        "attribute": (data.get("attribute") or "").title() if data.get("attribute") else None,
        "types": data.get("type") or "",
        "effect": text,
        "image": f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/{set_code}/{cid}_EN.webp",
        "source": f"https://onepiece.limitlesstcg.com/cards/{cid}",
        "tcgplayer_id": data.get("tcgplayer_id"),
    }


def ensure_cards(ids: set[str], cache: dict) -> dict:
    missing = [cid for cid in sorted(ids) if cid not in cache]
    print(f"card cache {len(cache)} known, fetching {len(missing)}")
    if not missing:
        return cache
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(fetch_card, cid): cid for cid in missing}
        for fut in as_completed(futs):
            cid = futs[fut]
            card = fut.result()
            if card:
                cache[cid] = card
            else:
                print("  missing card", cid)
    (ROOT / "data/card-cache.json").write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")
    return cache


def stats_line(card: dict) -> str:
    cat = card.get("category") or ""
    bits = []
    if cat.lower() == "leader":
        if card.get("life"):
            bits.append(f"{card['life']} Life")
        if card.get("power"):
            bits.append(f"{card['power']} Power")
        if card.get("attribute"):
            bits.append(card["attribute"])
        if card.get("color"):
            bits.append(card["color"])
    else:
        if card.get("cost") is not None:
            bits.append(f"Cost {card['cost']}")
        if card.get("power"):
            bits.append(f"{card['power']} Power")
        if card.get("counter"):
            bits.append(f"{card['counter']} Counter")
        if card.get("attribute"):
            bits.append(card["attribute"])
        if card.get("color"):
            bits.append(card["color"])
    return " · ".join(bits)


def render_card_entry(item: dict, meta: dict) -> str:
    cid = item["id"]
    name = display_name(meta.get("name") or item.get("name") or cid)
    set_code = cid.split("-")[0]
    img = f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/{set_code}/{cid}_EN.webp"
    qty = ""
    if item["group"] != "Leader":
        qty = f'<span class="qty">{html.escape(str(item["count"]))}x</span>'
    else:
        qty = '<span class="qty">1x</span>'
    cat = meta.get("category") or item["group"].rstrip("s")
    stats = stats_line(meta)
    types = meta.get("types") or ""
    text = meta.get("effect") or ""
    return f"""        <article class="card-entry">
          <img src="{html.escape(img)}" alt="{html.escape(name)} {html.escape(cid)}" loading="lazy" />
          <div>
            <div class="id">{qty}{html.escape(cid)} · {html.escape(cat)}</div>
            <h4>{html.escape(name)}</h4>
            {f'<div class="stats">{html.escape(stats)}</div>' if stats else ''}
            {f'<div class="stats">{html.escape(types)}</div>' if types else ''}
            {f'<div class="text">{html.escape(text)}</div>' if text else ''}
          </div>
        </article>"""


def page_chrome(
    title: str,
    description: str,
    color: str,
    nav_op17: bool,
    body: str,
    include_tcgplayer: bool = True,
) -> str:
    op17_cur = ' aria-current="page"' if nav_op17 else ""
    tcg_scripts = ""
    if include_tcgplayer:
        tcg_scripts = (
            '  <script src="/js/tcgplayer-config.js?v=tcg-quiet"></script>\n'
            '  <script src="/js/tcgplayer-ids.js?v=tcg-quiet"></script>\n'
            '  <script src="/js/tcgplayer-names.js?v=tcg-quiet"></script>\n'
            '  <script src="/js/tcgplayer.js?v=tcg-quiet"></script>\n'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}" />
  <link rel="stylesheet" href="/css/site.css?v=utrecht-x" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1074015774205047" crossorigin="anonymous"></script>
</head>
<body class="{html.escape(color)}">
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
        <a href="/decklists/op17.html"{op17_cur}>Leaders</a>
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
      © <span id="year"></span> One Piece Decklists - Built with community in mind.
      <a href="/tier-list.html">Tier List</a> · <a href="/guides/">Guides</a> · <a href="/decklists/op17.html">Leaders</a> · <a href="/format.html">Format</a> · <a href="/search.html">Search</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a>
    </footer>
  </div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    (function(){{
      var lines = document.querySelectorAll('.text-line');
      if (!lines.length) return;
      function resetPop(pop){{
        pop.style.position = '';
        pop.style.left = '';
        pop.style.top = '';
        pop.style.right = '';
        pop.style.bottom = '';
        pop.classList.remove('flip-left', 'flip-down');
      }}
      function place(line){{
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
      }}
      lines.forEach(function(line){{
        line.addEventListener('mouseenter', function(){{ place(line); }});
        line.addEventListener('focus', function(){{ place(line); }});
        line.addEventListener('click', function(e){{
          if (window.matchMedia('(hover: hover)').matches) return;
          e.stopPropagation();
          lines.forEach(function(other){{ if (other !== line) other.classList.remove('is-open'); }});
          line.classList.toggle('is-open');
          place(line);
        }});
      }});
      document.addEventListener('click', function(e){{
        if (!e.target.closest('.text-line')) {{
          lines.forEach(function(line){{ line.classList.remove('is-open'); }});
        }}
      }});
    }})();
  </script>
  <script src="/js/site.js?v=utrecht-x"></script>
{tcg_scripts}</body>
</html>
"""


def plain_dash(text: str) -> str:
    return (text or "").replace("\u2014", "-").replace("&mdash;", "-")


def list_heading(entry: dict, leader_name: str) -> tuple[str, str]:
    if entry.get("title_override"):
        title = entry["title_override"]
        sub = entry.get("subtitle") or ""
        return plain_dash(title), plain_dash(sub)
    player = display_name(entry.get("player") or "Unknown")
    event = entry.get("tournament_name") or "Limitless event"
    place = ordinal(entry.get("placing"))
    rec = record_text(entry.get("record"))
    date = entry.get("date") or ""
    bits = [b for b in (place, rec, date) if b]
    title = f"{player} - {leader_name}"
    sub = event
    if bits:
        sub = f"{event} · {' · '.join(bits)}"
    return plain_dash(title), plain_dash(sub)


def planned_slug(entry: dict) -> str:
    if entry.get("forced_slug"):
        return entry["forced_slug"]
    player = slugify(entry.get("player") or "player")
    event = slugify(entry.get("tournament_name") or "event")
    place = ordinal(entry.get("placing")) or record_text(entry.get("record")) or "list"
    return slugify(f"{place}-{player}-{event}")


def unique_slug(entry: dict, used: set[str]) -> str:
    slug = planned_slug(entry)
    base = slug
    n = 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


def card_image_url(cid: str) -> str:
    set_code = cid.split("-")[0]
    return f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/{set_code}/{cid}_EN.webp"


TEXT_QTY_RE = re.compile(
    r'<span class="qty">(\d+)x</span>.*?<span class="muted card-id">([^<]+)</span>',
    re.S,
)


def sim_text_from_cards(cards: list[dict]) -> str:
    lines = []
    for item in cards:
        try:
            n = int(item.get("count") or 0)
        except (TypeError, ValueError):
            continue
        cid = (item.get("id") or "").strip()
        if n and cid:
            lines.append(f"{n}x{cid}")
    return "\n".join(lines)


def sim_text_from_decklist(dl: dict) -> str:
    return sim_text_from_cards(flatten_cards(dl or {}))


def sim_text_from_html(page: str) -> str:
    block = page
    m = re.search(r'<section class="text-deck">.*?</section>', page, re.S)
    if m:
        block = m.group(0)
    lines = [f"{n}x{cid.strip()}" for n, cid in TEXT_QTY_RE.findall(block)]
    return "\n".join(lines)


def sim_text_for_entry(leader: dict, entry: dict) -> str:
    raw = entry.get("sim_text")
    if raw:
        return raw
    dl = entry.get("decklist")
    if dl:
        return sim_text_from_decklist(dl)
    slug = entry.get("slug")
    if slug:
        path = ROOT / leader["dir"] / f"{slug}.html"
        if path.exists():
            return sim_text_from_html(path.read_text())
    href = entry.get("href") or ""
    if href.startswith("/"):
        path = ROOT / href.lstrip("/")
        if path.exists():
            return sim_text_from_html(path.read_text())
    return ""


def sim_compact(text: str) -> str:
    return " ".join(text.split())


def copy_sim_button(sim_text: str) -> str:
    compact = sim_compact(sim_text)
    if not compact:
        return ""
    return (
        f'<button type="button" class="copy-sim" data-copy-sim data-sim="{html.escape(compact, quote=True)}">'
        "Copy to OP TCG SIM</button>"
    )


def event_bucket(name: str) -> str:
    n = (name or "").lower()
    if "treasure" in n:
        return "treasure"
    if "regional" in n:
        return "regional"
    if "championship" in n or "flagship" in n:
        return "championship"
    return "other"


def counter_value(meta: dict) -> int:
    raw = meta.get("counter")
    if raw is None:
        return 0
    m = re.search(r"(\d+)", str(raw))
    return int(m.group(1)) if m else 0


def render_deck_stats(items: list[dict], cache: dict) -> str:
    curve = {str(i): 0 for i in range(0, 10)}
    curve["10+"] = 0
    counters = {"2k": 0, "1k": 0, "0": 0}
    copies = 0
    for item in items:
        if item.get("group") == "Leader":
            continue
        n = int(item.get("count") or 0)
        copies += n
        meta = cache.get(item["id"]) or {}
        try:
            cost = int(meta.get("cost"))
        except (TypeError, ValueError):
            cost = 0
        key = "10+" if cost >= 10 else str(max(0, cost))
        curve[key] += n
        cv = counter_value(meta)
        if cv >= 2000:
            counters["2k"] += n
        elif cv >= 1000:
            counters["1k"] += n
        else:
            counters["0"] += n
    if copies <= 0:
        return ""
    max_c = max(curve.values()) or 1
    bars = []
    for key in [str(i) for i in range(1, 10)] + ["10+"]:
        h = int(round(56 * curve[key] / max_c)) if curve[key] else 2
        bars.append(
            f'<span style="height:{h}px" title="{html.escape(key)} DON!! · {curve[key]}"><em>{html.escape(key)}</em></span>'
        )
    return f"""        <!-- DECK_STATS -->
        <section class="deck-stats">
          <div class="kicker">List snapshot</div>
          <div class="stat-grid">
            <div>
              <div class="muted">DON!! curve</div>
              <div class="curve" aria-hidden="true">{"".join(bars)}</div>
            </div>
            <div>
              <div class="muted">Counters in the 50</div>
              <div class="counter-pills">
                <span class="pill">{counters["2k"]}× 2k</span>
                <span class="pill">{counters["1k"]}× 1k</span>
                <span class="pill">{counters["0"]}× no counter</span>
              </div>
            </div>
          </div>
        </section>
        <!-- /DECK_STATS -->"""


def render_text_deck(grouped: dict, cache: dict, order: list[str], totals: dict) -> str:
    total = 1 + sum(totals.values())
    cols = []
    for group in order:
        items = grouped.get(group) or []
        if not items:
            continue
        lines = []
        for item in items:
            meta = cache.get(item["id"], {})
            name = display_name(html.unescape(meta.get("name") or item.get("name") or item["id"]))
            img = card_image_url(item["id"])
            lines.append(
                f"""            <li class="text-line" tabindex="0">
              <span class="qty">{html.escape(str(item['count']))}x</span>
              <span class="card-title">{html.escape(name)}</span>
              <span class="muted card-id">{html.escape(item['id'])}</span>
              <img class="card-pop" src="{html.escape(img)}" alt="{html.escape(name)}" />
            </li>"""
            )
        cols.append(
            f"""          <div{' class="text-deck-leader"' if group == "Leader" else ""}>
            <h4>{html.escape(group)}</h4>
            <ul class="text-lines">
{chr(10).join(lines)}
            </ul>
          </div>"""
        )
    return f"""        <section class="text-deck">
          <div class="section-title">
            <h3>Text list</h3>
            <button type="button" class="copy-sim" data-copy-sim>Copy to OP TCG SIM</button>
          </div>
          <div class="text-deck-cols">
{chr(10).join(cols)}
          </div>
        </section>"""


def render_deck_page(leader: dict, entry: dict, cache: dict) -> str:
    title, subtitle = list_heading(entry, leader["name"])
    parent_href = "/" + leader["page"]
    crumb_href, crumb_label = leader["crumb"]
    cards = flatten_cards(entry["decklist"])
    grouped = defaultdict(list)
    totals = defaultdict(int)
    order = ["Leader", "Characters", "Events", "Stages"]
    for item in cards:
        grouped[item["group"]].append(item)
        if item["group"] != "Leader":
            totals[item["group"]] += item["count"]
    def cost_key(it):
        c = cache.get(it["id"], {}).get("cost")
        try:
            return int(c)
        except (TypeError, ValueError):
            return 99

    for group in grouped:
        grouped[group].sort(
            key=lambda it: (
                cost_key(it),
                display_name(cache.get(it["id"], {}).get("name") or it["name"]),
            )
        )
    leader_block = ""
    sections = []
    for group in order:
        items = grouped.get(group) or []
        if not items:
            continue
        count_label = "1 card" if group == "Leader" else f"{totals[group]} cards"
        entries = "\n".join(render_card_entry(it, cache.get(it["id"], {"name": it["name"], "category": group.rstrip("s"), "id": it["id"]})) for it in items)
        block = f"""        <section class="{'leader-block' if group == 'Leader' else 'picture-group'}" style="margin-top:22px">
          <div class="section-title">
            <h3>{html.escape(group)}</h3>
            <div class="muted">{html.escape(count_label)}</div>
          </div>
          <div class="card-grid">
{entries}
          </div>
        </section>"""
        if group == "Leader":
            leader_block = block
        else:
            sections.append(block)
    text_list = render_text_deck(grouped, cache, order, totals)
    stats = render_deck_stats(cards, cache)
    picture = f"""        <section class="picture-summary">
          <div class="section-title">
            <h3>Card pictures</h3>
            <div class="muted">Full card text</div>
          </div>
{chr(10).join(sections)}
        </section>"""
    source = entry.get("source_url") or "https://play.limitlesstcg.com/"
    kind_note = {
        "sample": "Sample 50-card list built from the OP17 Red card pool. Not taken from a tournament.",
        "featured": "Featured list and English card text from Limitless One Piece.",
        "tournament": "Tournament list from Limitless Play. English card text from Limitless One Piece.",
        "youtube": "List from a YouTube deck profile. English card text from Limitless One Piece.",
        "web": "Community list from a public deck builder. English card text from Limitless One Piece.",
        "x": "List copied from a public X/Twitter post. English card text from Limitless One Piece.",
    }.get(entry.get("kind"), "List sourced from the One Piece TCG community. Not affiliated with Bandai.")
    body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="{html.escape(crumb_href)}">{html.escape(crumb_label)}</a> / <a href="{html.escape(parent_href)}">{html.escape(leader['name'])}</a> / Decklist</div>
        <h2>{html.escape(title)}</h2>
        <p>{html.escape(subtitle)}</p>
{leader_block}
{stats}
{text_list}
{picture}
        <p class="muted" style="margin-top:22px">{html.escape(kind_note)} Source: <a href="{html.escape(source)}">{html.escape(source)}</a>. Images hosted by Limitless. Not affiliated with Bandai.</p>"""
    desc = f"{leader['name']} decklist - {subtitle}"[:160]
    return page_chrome(f"{title}", desc, leader["color"], leader["nav_op17"], body)


def render_pool_heading(leader: dict) -> str:
    return f"""        <!-- CARD_POOL_HEADING -->
        <div class="section-title" style="margin-top:28px">
          <h3>{html.escape(leader["pool_heading"])}</h3>
          <div class="muted">{html.escape(leader["pool_note"])}</div>
        </div>
        <!-- /CARD_POOL_HEADING -->"""


HUB_INTRO = {
    "OP16-022": (
        "Green/Blue OP16 Monkey D. Luffy. Impel Down / Straw Hat Crew. "
        "If your board is only Impel Down characters, set up to 2 DON!! active. "
        "Not red/green OP13 Luffy and not black OP17 Elbaph Luffy."
    ),
    "OP16-080": (
        "Black/Yellow OP16 Marshall D. Teach. Blackbeard Pirates. "
        "Your characters cost +1 on the opponent's turn; trash a Trigger to retarget an attack."
    ),
    "OP12-061": (
        "Purple/Yellow Donquixote Rosinante. Navy / Donquixote Pirates. "
        "You can pay a Life instead of letting Trafalgar Law die, then DON!! −1 to discount a 4-cost or higher Law."
    ),
    "OP15-002": (
        "Red/Blue Lucy is Dressrosa Luffy in disguise. "
        "Trash events or stages for power, then draw if you already played a 3-cost or higher event. Not red/blue OP13 Ace."
    ),
    "OP16-079": (
        "Black OP16 Yamato. Land of Wano. "
        "A Wano character played from trash gains Rush that turn. Not a Kaido character card."
    ),
    "OP11-001": (
        "Red/Black Koby. Navy / SWORD. "
        "SWORD characters can attack the turn they are played. A 7000-power-or-less Navy body can be saved from removal."
    ),
    "OP14-060": (
        "Purple OP14 Donquixote Doflamingo is the Dressrosa retarget leader - not blue OP01-060 Doffy. "
        "Once per opponent attack, DON!! −1 to send that attack at Doffy or a Donquixote Pirates character."
    ),
    "OP16-041": (
        "Blue OP16 Buggy. Impel Down / Buggy Pirates. "
        "When an Impel Down character leaves the field, DON!! ×1 lets you play a Prisoner of Impel Down from hand. Not a character in GB Luffy."
    ),
    "OP16-060": (
        "Purple OP16 Sengoku. Navy. "
        "Return 8 active DON!! to play up to 3 differently named Admirals from hand. Not Enel and not Katakuri."
    ),
    "OP11-040": (
        "Blue/Purple OP11 Monkey D. Luffy - UP Luffy in community shorthand (U = blue, P = purple). "
        "Once you have 8 DON!!, look at 5 and add a Straw Hat. "
        "Not red/green OP13 Luffy, not green/blue OP16 Impel Down Luffy, and not black OP17 Elbaph Luffy."
    ),
    "OP08-058": (
        "Purple/Yellow OP08 Charlotte Pudding is the Big Mom DON!! ramp leader - not yellow OP17 Linlin and not purple OP11 Katakuri. "
        "When attacking, turn 2 Life cards face-up to add 1 DON!! from your DON!! deck and rest it."
    ),
}


def render_hub_page(leader: dict, cache: dict) -> str:
    meta = cache.get(leader["id"]) or {}
    name = display_name(meta.get("name") or leader["name"])
    color = meta.get("color") or ""
    life = meta.get("life") or ""
    power = meta.get("power") or ""
    attr = meta.get("attribute") or ""
    types = meta.get("types") or ""
    effect = meta.get("effect") or ""
    intro = HUB_INTRO.get(leader["id"]) or f"{leader['name']} constructed lists from Limitless events."
    pills = []
    if color:
        pills.append(f"{color} Leader")
    pills.append(leader["id"])
    if life:
        pills.append(f"{life} Life")
    if power:
        pills.append(f"{power} Power")
    if attr:
        pills.append(attr)
    if types:
        pills.append(types)
    pill_html = "".join(f'<span class="pill">{html.escape(p)}</span>' for p in pills)
    img = card_image_url(leader["id"])
    crumb_href, crumb_label = leader["crumb"]
    body = f"""        <div class="crumb"><a href="/">Home</a> / <a href="{html.escape(crumb_href)}">{html.escape(crumb_label)}</a> / {html.escape(leader["name"])}</div>
        <div class="leader-hero">
          <img src="{html.escape(img)}" alt="{html.escape(leader["name"])} leader" />
          <div>
            <h2>{html.escape(leader["name"])}</h2>
            <p>{html.escape(intro)}</p>
            <div class="stat-row">
              {pill_html}
            </div>
            <div class="effect">{html.escape(effect)}</div>
            <p class="muted" style="margin-top:12px">{html.escape(name)} · {html.escape(leader["id"])}</p>
          </div>
        </div>
        <!-- TOURNAMENT_DECKLISTS -->
        <section class="deck-index" style="margin-top:22px">
          <div class="section-title">
            <h3>Tournament decklists</h3>
            <div class="muted">0 lists</div>
          </div>
          <p class="muted">No tournament lists found for this leader yet.</p>
        </section>
        <!-- /TOURNAMENT_DECKLISTS -->
{render_pool_heading(leader)}"""
    desc = f"{leader['name']} - {color} leader page and tournament lists."
    return page_chrome(f"{leader['name']} decklist", desc[:160], leader["color"], leader["nav_op17"], body)


def render_index_section(leader: dict, lists: list[dict]) -> str:
    if not lists:
        return """        <!-- TOURNAMENT_DECKLISTS -->
        <section class="deck-index" style="margin-top:22px">
          <div class="section-title">
            <h3>Decklists</h3>
            <div class="muted">0 lists</div>
          </div>
          <p class="muted">No tournament lists found for this leader yet.</p>
        </section>
        <!-- /TOURNAMENT_DECKLISTS -->"""
    sample_only = all(x.get("kind") == "sample" for x in lists)
    heading = "Sample decklists" if sample_only else "Tournament decklists"
    intro = (
        "No Limitless tournament results for this leader yet, so these are sample 50-card lists from the OP17 Red pool. Each row opens a full list."
        if sample_only
        else "Newest Limitless events first. Each row opens a separate 50-card list."
    )
    rows = []
    for entry in sorted(lists, key=date_sort_key, reverse=True):
        href = entry["href"]
        title, subtitle = list_heading(entry, leader["name"])
        right = entry.get("date") or ordinal(entry.get("placing")) or record_text(entry.get("record")) or "View"
        if entry.get("kind") == "sample":
            right = "Sample"
        elif entry.get("kind") in ("youtube", "web", "x") and not entry.get("date"):
            right = "List"
        placing = entry.get("placing")
        placing_s = "" if placing is None else str(placing)
        date_s = entry.get("date") or ""
        bucket = event_bucket(entry.get("tournament_name") or entry.get("tournament") or "")
        copy_btn = copy_sim_button(sim_text_for_entry(leader, entry))
        rows.append(
            f"""            <li class="list-row" data-date="{html.escape(date_s)}" data-placing="{html.escape(placing_s)}" data-event="{html.escape(bucket)}">
              <a class="item" href="{html.escape(href)}">
                <div>
                  <div style="font-weight:700">{html.escape(title)}</div>
                  <div class="muted" style="font-size:13px">{html.escape(subtitle)}</div>
                </div>
                <div class="link">{html.escape(str(right))} →</div>
              </a>
              {copy_btn}
            </li>"""
        )
    filters = ""
    if not sample_only and len(lists) >= 8:
        filters = """          <div class="list-filters" data-hub-filters>
            <input type="search" data-filter="q" placeholder="Filter player or event" aria-label="Filter lists" />
            <select data-filter="when" aria-label="Date">
              <option value="">Any date</option>
              <option value="jul">Since July 2026</option>
              <option value="aug">Since August 2026</option>
            </select>
            <select data-filter="place" aria-label="Placing">
              <option value="">Any placing</option>
              <option value="top8">Top 8</option>
              <option value="win">1st only</option>
            </select>
            <select data-filter="event" aria-label="Event type">
              <option value="">Any event</option>
              <option value="regional">Regional</option>
              <option value="treasure">Treasure Cup</option>
              <option value="championship">Championship / Flagship</option>
              <option value="other">Other</option>
            </select>
          </div>
"""
    return f"""        <!-- TOURNAMENT_DECKLISTS -->
        <section class="deck-index" style="margin-top:22px">
          <div class="section-title">
            <h3>{html.escape(heading)}</h3>
            <div class="muted">{len(lists)} lists</div>
          </div>
          <p class="muted">{html.escape(intro)}</p>
{filters}          <ul class="list" aria-label="{html.escape(heading)}">
{chr(10).join(rows)}
          </ul>
        </section>
        <!-- /TOURNAMENT_DECKLISTS -->"""


def insert_section(page_html: str, section: str, pool: str) -> str:
    if "<!-- TOURNAMENT_DECKLISTS -->" in page_html:
        page_html = re.sub(
            r"        <!-- TOURNAMENT_DECKLISTS -->.*?        <!-- /TOURNAMENT_DECKLISTS -->",
            section,
            page_html,
            count=1,
            flags=re.S,
        )
    else:
        start = page_html.find('<div class="leader-hero">')
        if start < 0:
            raise SystemExit("leader-hero missing")
        depth = 0
        j = start
        while j < len(page_html):
            if page_html.startswith("<div", j):
                depth += 1
                j = page_html.find(">", j) + 1
                continue
            if page_html.startswith("</div>", j):
                depth -= 1
                j += 6
                if depth == 0:
                    break
                continue
            j += 1
        page_html = page_html[:j] + "\n" + section + page_html[j:]
    if "<!-- CARD_POOL_HEADING -->" in page_html:
        page_html = re.sub(
            r"        <!-- CARD_POOL_HEADING -->.*?        <!-- /CARD_POOL_HEADING -->",
            pool,
            page_html,
            count=1,
            flags=re.S,
        )
    else:
        page_html = page_html.replace(
            "<!-- /TOURNAMENT_DECKLISTS -->",
            "<!-- /TOURNAMENT_DECKLISTS -->\n" + pool,
            1,
        )
    return page_html


def main() -> None:
    target_ids = {L["id"] for L in LEADERS}
    print("fetching tournaments")
    tournaments = http_json(f"https://play.limitlesstcg.com/api/tournaments?game=OP&limit={TOURNAMENT_LIMIT}")
    print("tournaments", len(tournaments))
    by_leader = fetch_standings(tournaments, target_ids)

    featured = featured_from_other_leaders()
    for lid, entry in featured.items():
        by_leader[lid].append(entry)

    op17 = json.loads((ROOT / "data/op17-cards.json").read_text())
    selected: dict[str, list] = {}
    for leader in LEADERS:
        lid = leader["id"]
        entries = by_leader.get(lid) or []
        featured_entries = [
            e
            for e in entries
            if e.get("kind") == "featured" and not deck_has_banned(e.get("decklist") or {})
        ]
        rest = [e for e in entries if e.get("kind") != "featured"]
        picked = select_lists(rest, limit=MAX_LISTS)
        if featured_entries:
            merged = []
            seen = set()
            for entry in featured_entries + picked:
                sig = deck_signature(entry.get("decklist") or {})
                if sig in seen:
                    continue
                seen.add(sig)
                merged.append(entry)
            picked = merged[:MAX_LISTS]
        if lid == "OP17-001" and not picked:
            picked = newgate_samples(op17)
        selected[lid] = picked
        print(lid, "raw", len(by_leader.get(lid) or []), "picked", len(picked), "kinds", [p.get("kind") for p in picked])

    needed = set()
    for lists in selected.values():
        for entry in lists:
            for item in flatten_cards(entry["decklist"]):
                needed.add(item["id"])
    cache = ensure_cards(needed, load_card_cache())

    index = {}
    for leader in LEADERS:
        out_dir = ROOT / leader["dir"]
        if out_dir.exists():
            for old in out_dir.glob("*.html"):
                old.unlink()
        out_dir.mkdir(parents=True, exist_ok=True)
        used_slugs: set[str] = set()
        lists = [
            e
            for e in selected[leader["id"]]
            if not deck_has_banned(e.get("decklist") or {})
        ]
        public = []
        for entry in lists:
            slug = unique_slug(entry, used_slugs)
            href = f"/{leader['dir']}/{slug}.html"
            entry = dict(entry)
            entry["slug"] = slug
            entry["href"] = href
            html_page = render_deck_page(leader, entry, cache)
            (out_dir / f"{slug}.html").write_text(html_page)
            public.append(entry)
        selected[leader["id"]] = public
        page_path = ROOT / leader["page"]
        page_html = page_path.read_text()
        page_path.write_text(
            insert_section(page_html, render_index_section(leader, public), render_pool_heading(leader))
        )
        index[leader["id"]] = [
            {
                "slug": e["slug"],
                "href": e["href"],
                "player": e.get("player"),
                "tournament": e.get("tournament_name"),
                "placing": e.get("placing"),
                "date": e.get("date"),
                "kind": e.get("kind"),
                "source_url": e.get("source_url"),
            }
            for e in public
        ]

    (ROOT / "data/tournament-decks.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print("done")


if __name__ == "__main__":
    main()
