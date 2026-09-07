#!/usr/bin/env python3
"""Add YouTube / community decklists onto existing leader pages."""

from __future__ import annotations

import html
import json
import re
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "genlists", "/workspace/scripts/generate-tournament-lists.py"
)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

ROOT = gen.ROOT
LINE_RE = re.compile(r"(?i)(\d+)\s*[x×]\s*((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})")

COMMUNITY = {
    "OP17-001": [
        {
            "slug": "yt-marineford-8k-forever",
            "player": "MarinefordTCG",
            "title": "8K Forever - MarinefordTCG",
            "subtitle": "YouTube deck profile · also on X @MarinefordTCG",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=LQdWh4mzH1o",
            "extra": "https://x.com/MarinefordTCG",
            "raw": "1xOP17-001 4xOP16-010 4xOP10-005 4xOP17-003 2xOP17-009 4xOP16-118 3xOP17-015 4xOP17-008 2xST23-001 4xOP16-004 4xOP17-007 1xOP09-118 4xOP17-005 2xOP17-018 4xOP17-019 4xOP16-021",
        },
        {
            "slug": "yt-nightingale-beefy-newgate",
            "player": "NightingaleTCG",
            "title": "Newgate is a big beefy man - Nightingale",
            "subtitle": "YouTube deck profile · also on X @BenSchumi7",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=SzOHHLZD-Vo",
            "extra": "https://x.com/BenSchumi7",
            "raw": "1xOP17-001 4xOP10-005 2xOP17-004 4xOP17-016 4xOP17-003 4xOP16-118 4xOP17-015 2xST30-008 4xOP17-008 4xOP17-013 2xST23-001 2xOP02-013 4xOP17-007 4xOP17-005 2xOP17-019 4xOP16-021",
        },
        {
            "slug": "yt-marineford-better-than-ace",
            "player": "MarinefordTCG",
            "title": "Better Than Ace? - MarinefordTCG",
            "subtitle": "YouTube deck profile · also on X @MarinefordTCG",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=ALrTnX2pAdU",
            "extra": "https://x.com/MarinefordTCG",
            "raw": "1xOP17-001 2xOP13-007 4xST30-004 4xOP10-005 4xOP17-003 2xST21-015 2xOP12-002 4xOP16-118 4xOP17-015 2xST15-005 4xST30-005 2xST23-001 3xEB04-007 4xOP17-007 1xOP09-118 4xOP17-005 4xOP16-021",
        },
    ],
    "OP17-020": [
        {
            "slug": "yt-strawhatpecan-freeze-board",
            "player": "StrawHatPecan",
            "title": "Freeze Their Board - StrawHatPecan",
            "subtitle": "YouTube deck profile · also on X @StrawHatPecan",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=GDV-9HANFyY",
            "extra": "https://x.com/StrawHatPecan",
            "raw": "1xOP17-020 4xOP17-021 4xOP17-032 2xOP17-028 4xOP17-029 4xOP17-033 4xOP17-031 2xOP17-034 4xST32-002 4xOP17-027 4xST16-004 4xOP17-022 4xOP17-038 2xOP17-036 4xOP17-037",
        },
        {
            "slug": "yt-green-shanks-first-impressions",
            "player": "YouTube",
            "title": "Green Shanks first impressions",
            "subtitle": "YouTube deck profile - Is OP17 Green Shanks overhyped?",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=NSTlSg_hR3c",
            "raw": "1xOP17-020 4xOP12-034 4xST32-001 4xST32-005 4xOP17-028 4xOP17-029 4xPRB02-006 2xOP10-030 4xOP17-031 4xST32-002 2xOP13-031 4xST32-003 4xOP17-027 2xST16-004 4xOP17-022",
        },
        {
            "slug": "yt-marineford-better-than-mihawk",
            "player": "MarinefordTCG",
            "title": "Better Than Mihawk? - MarinefordTCG",
            "subtitle": "YouTube deck profile · also on X @MarinefordTCG",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=CrLQZiTBCM4",
            "extra": "https://x.com/MarinefordTCG",
            "raw": "1xOP17-020 3xOP12-034 4xOP17-021 1xOP17-026 4xOP17-032 4xOP17-029 4xOP17-033 2xOP10-030 4xOP17-031 2xOP17-034 4xST32-002 4xOP17-027 3xST16-004 4xOP17-022 1xOP17-038 2xOP17-036 4xOP17-037",
        },
    ],
    "OP17-039": [
        {
            "slug": "yt-johnny-rocks-most-fun",
            "player": "JohnnyTCG",
            "title": "Most fun leader - JohnnyTCG",
            "subtitle": "YouTube deck list and gameplay",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=1-yzKh302CY",
            "raw": "1xOP17-039 4xOP17-050 4xOP17-045 4xOP17-054 3xOP17-041 4xOP17-042 4xOP17-046 3xOP17-043 4xOP17-049 4xOP17-040 4xOP17-048 4xOP17-118 4xOP17-055 4xOP17-056",
        },
        {
            "slug": "yt-blue-rocks-first-impressions",
            "player": "YouTube",
            "title": "Blue Rocks overhyped or legit?",
            "subtitle": "YouTube first impressions + deck profile",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=xWA7ZW3ed5E",
            "raw": "1xOP17-039 4xOP17-050 3xOP17-045 3xOP17-052 4xOP17-054 3xOP17-042 3xOP17-044 4xOP17-046 4xOP17-049 4xOP17-040 4xOP17-048 4xOP17-118 4xOP17-055 4xOP17-056 2xOP17-057",
        },
        {
            "slug": "yt-capiamo-xebec",
            "player": "CAPIAMO / BoxBreak",
            "title": "CAPIAMO Xebec testing + decklist",
            "subtitle": "YouTube Italian deck profile",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=OvIFAvP-XaM",
            "raw": "1xOP17-039 3xOP17-050 4xOP17-045 3xOP17-052 4xOP17-054 3xOP17-042 3xOP17-044 4xOP17-046 4xOP17-049 4xOP17-040 4xOP17-048 4xOP17-118 4xOP17-055 4xOP17-056 2xOP17-057",
        },
        {
            "slug": "web-cardkaizoku-xebec-guide",
            "player": "CardKaizoku",
            "title": "CardKaizoku Rocks guide list",
            "subtitle": "YouTube guide + CardKaizoku deck builder · 8 hours ago",
            "kind": "web",
            "source_url": "https://www.youtube.com/watch?v=E-iESLJ8N_4",
            "extra": "https://deckbuilder.cardkaizoku.com/",
            "raw": "1xOP17-039 4xOP17-040 2xOP17-041 4xOP17-042 2xOP17-044 4xOP17-045 4xOP17-046 4xOP17-048 4xOP17-049 4xOP17-050 2xOP17-052 4xOP17-054 4xOP17-055 4xOP17-056 4xOP17-118",
        },
        {
            "slug": "web-cardkaizoku-rocks-testing",
            "player": "CardKaizoku",
            "title": "CardKaizoku Rocks testing list",
            "subtitle": "YouTube testing + CardKaizoku deck builder",
            "kind": "web",
            "source_url": "https://www.youtube.com/watch?v=7aCHDV0zuoI",
            "extra": "https://deckbuilder.cardkaizoku.com/",
            "raw": "1xOP17-039 4xOP17-040 4xOP17-042 2xOP17-044 4xOP17-045 4xOP17-046 4xOP17-048 4xOP17-049 4xOP17-050 4xOP17-052 4xOP17-054 4xOP17-055 4xOP17-056 4xOP17-118",
        },
    ],
    "OP17-058": [
        {
            "slug": "yt-johnny-kaido-hard-to-beat",
            "player": "JohnnyTCG",
            "title": "Kaido is hard to beat - JohnnyTCG",
            "subtitle": "YouTube deck list and gameplay",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=KViquBQIsx0",
            "raw": "1xOP17-058 4xEB04-032 2xOP08-074 4xOP17-073 4xOP17-074 2xEB01-061 4xOP06-076 4xEB04-031 2xEB04-030 3xOP17-065 3xOP17-062 2xOP17-063 3xST34-004 4xOP15-078 4xOP07-077 3xOP07-076 2xOP08-077",
        },
        {
            "slug": "yt-purple-kaido-first-impressions",
            "player": "YouTube",
            "title": "They were wrong about Purple Kaido",
            "subtitle": "YouTube first impressions + deck profile",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=xC0KQ-smZZA",
            "raw": "1xOP17-058 4xEB04-032 2xOP08-074 4xOP17-073 4xOP17-074 4xEB04-031 4xOP17-061 4xOP17-065 4xOP17-062 2xOP17-063 4xST34-004 2xOP13-076 4xOP15-078 4xOP07-077 4xOP07-076",
        },
        {
            "slug": "yt-new-best-purple-kaido",
            "player": "YouTube",
            "title": "The new best purple deck - Kaido",
            "subtitle": "YouTube OP17 Kaido deck breakdown",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=suASpq6xDS8",
            "raw": "1xOP17-058 4xEB04-032 3xOP17-072 4xOP17-075 4xOP17-073 4xOP17-074 4xEB04-031 2xOP17-060 3xOP17-061 3xOP17-065 4xOP17-062 3xOP17-063 2xST34-004 4xOP15-078 4xOP07-077 2xOP07-076",
        },
        {
            "slug": "yt-marineford-king-of-beasts",
            "player": "MarinefordTCG",
            "title": "Don't sleep on the King of the Beasts - MarinefordTCG",
            "subtitle": "YouTube deck profile · also on X @MarinefordTCG",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=kKBHITaidrY",
            "extra": "https://x.com/MarinefordTCG",
            "raw": "1xOP17-058 4xEB04-032 2xOP17-072 4xOP17-075 4xOP17-073 4xOP17-074 4xEB04-031 2xOP17-061 2xOP17-065 4xOP17-062 3xOP17-063 3xST34-004 2xOP13-076 4xOP15-078 4xOP07-077 2xOP17-077 2xOP07-076",
        },
    ],
    "OP17-079": [
        {
            "slug": "yt-black-elbaf-luffy-profile",
            "player": "YouTube",
            "title": "Black Elbaf Luffy deck profile",
            "subtitle": "YouTube profile and commentary - 10 hours ago",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=_YAadqK5OaA",
            "raw": "1xOP17-079 4xOP05-081 4xOP17-080 4xOP17-081 4xOP17-082 4xOP17-083 3xOP17-087 3xOP17-090 4xOP17-095 4xEB01-048 2xOP17-089 3xOP15-088 4xOP17-119 3xOP17-093 2xOP17-098 2xST14-017",
        },
        {
            "slug": "yt-strawhatpecan-infinite-blockers",
            "player": "StrawHatPecan",
            "title": "Luffy has infinite blockers - StrawHatPecan",
            "subtitle": "YouTube deck profile · also on X @StrawHatPecan",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=4MyNT1IM0DE",
            "extra": "https://x.com/StrawHatPecan",
            "raw": "1xOP17-079 2xOP17-084 2xOP17-086 4xOP17-094 4xOP17-080 4xOP17-081 4xOP17-082 3xOP17-083 2xOP17-087 2xOP17-091 2xOP17-095 4xOP17-089 3xOP17-085 3xOP17-092 4xOP17-119 4xOP17-093 1xOP17-097 2xOP17-098",
        },
        {
            "slug": "yt-blaise-luffy-strong-already",
            "player": "BlaisePlaysTCG",
            "title": "OP17 Luffy is strong already - BlaisePlaysTCG",
            "subtitle": "YouTube decklist + gameplay",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=yF5NQsfwZWY",
            "raw": "1xOP17-079 4xOP05-081 4xOP17-080 4xOP17-081 4xOP17-083 4xOP17-087 4xOP17-090 4xOP17-091 4xOP17-089 4xOP17-119 3xOP17-093 3xOP15-096 4xOP07-096 4xST14-017",
        },
    ],
    "OP17-099": [
        {
            "slug": "yt-strawhatpecan-yellow-slop",
            "player": "StrawHatPecan",
            "title": "Most slop yellow deck - StrawHatPecan",
            "subtitle": "YouTube Linlin deck profile · also on X @StrawHatPecan",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=8tM5AofdVQ4",
            "extra": "https://x.com/StrawHatPecan",
            "raw": "1xOP17-099 4xOP17-113 4xOP17-104 4xOP17-107 3xOP17-108 4xOP17-109 4xOP17-102 4xOP17-106 4xOP17-103 4xOP17-114 4xOP17-100 4xOP17-110 4xOP17-112 2xOP17-115 1xOP17-116",
        },
        {
            "slug": "yt-linlin-big-problem",
            "player": "YouTube",
            "title": "Linlin is a big problem",
            "subtitle": "YouTube deck breakdown and gameplay",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=L7f95snVnB4",
            "raw": "1xOP17-099 3xEB01-056 4xOP17-113 2xOP11-106 2xOP17-104 3xOP17-107 3xOP17-108 4xOP17-109 4xOP17-102 4xOP17-106 4xOP17-103 4xOP17-114 3xOP17-110 4xOP17-112 3xOP17-115 3xOP17-117",
        },
    ],
    "OP11-040": [
        {
            "slug": "yt-youtube-up-luffy-rlffbode4qs",
            "player": "NightingaleTCG",
            "title": "OP17 UP Luffy gets TWO new 9 costs - Nightingale",
            "subtitle": "YouTube deck profile · also on X @BenSchumi7",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=rlffBOdE4qs",
            "extra": "https://x.com/BenSchumi7",
            "raw": "1xOP11-040 4xOP13-043 3xOP16-056 3xOP17-046 4xOP11-054 4xOP06-119 4xOP05-067 4xOP17-074 4xST18-001 4xEB01-061 4xP-107 2xOP17-064 2xOP17-065 4xOP09-078 4xOP11-080",
        },
        {
            "slug": "yt-artress-up-luffy-m5jw91p5be",
            "player": "ArtressTCG",
            "title": "Mr.3 Brings Back UP Luffy - Artress",
            "subtitle": "YouTube + EgmanEvents deck builder",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=-M5JW91P5BE",
            "extra": "https://deckbuilder.egmanevents.com/?deck=OP11-040:1,OP15-047:1,OP06-119:4,P-107:4,OP07-051:4,OP07-064:2,ST18-001:4,OP11-054:4,P-053:2,EB03-034:2,OP16-056:4,OP09-078:4,OP11-080:4,OP14-077:2,OP08-076:4,OP06-058:1,EB01-061:4&type=optcg",
            "raw": "1xOP11-040 1xOP15-047 4xOP06-119 4xP-107 4xOP07-051 2xOP07-064 4xST18-001 4xOP11-054 2xP-053 2xEB03-034 4xOP16-056 4xOP09-078 4xOP11-080 2xOP14-077 4xOP08-076 1xOP06-058 4xEB01-061",
        },
    ],
    "OP13-001": [
        {
            "slug": "yt-johnny-rg-luffy-meta-again",
            "player": "JohnnyTCG",
            "title": "Did RG Luffy just become meta again? - JohnnyTCG",
            "subtitle": "YouTube deck list and gameplay",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=XieqBf_xpns",
            "raw": "1xOP13-001 4xOP01-016 4xST21-003 3xEB04-007 3xST31-004 4xOP15-035 2xOP13-037 4xOP14-022 3xOP14-031 4xOP13-027 4xOP13-118 2xOP15-032 3xOP13-040 4xOP05-038 2xOP08-036 4xST31-005",
        },
        {
            "slug": "web-egman-artress-rg-luffy",
            "player": "ArtressTCG",
            "title": "They made RG Luffy even harder to beat - Artress",
            "subtitle": "YouTube + EgmanEvents deck builder · also on X @michaelartress",
            "kind": "web",
            "source_url": "https://www.youtube.com/watch?v=MhjCjFwn7SI",
            "extra": "https://deckbuilder.egmanevents.com/?deck=OP13-001:1,OP01-016:4,ST21-003:2,EB04-007:4,ST31-004:3,EB02-017:4,OP15-035:4,OP13-037:3,OP14-022:4,OP14-031:4,OP13-027:4,OP13-118:2,OP15-032:1,OP05-038:3,OP08-036:4,ST31-005:4&type=optcg",
            "raw": "1xOP13-001 4xOP01-016 2xST21-003 4xEB04-007 3xST31-004 4xEB02-017 4xOP15-035 3xOP13-037 4xOP14-022 4xOP14-031 4xOP13-027 2xOP13-118 1xOP15-032 3xOP05-038 4xOP08-036 4xST31-005",
        },
    ],
    "OP14-020": [
        {
            "slug": "web-egman-artress-mihawk",
            "player": "ArtressTCG",
            "title": "Green Mihawk won the starter deck lottery - Artress",
            "subtitle": "YouTube + EgmanEvents deck builder · also on X @michaelartress",
            "kind": "web",
            "source_url": "https://www.youtube.com/watch?v=xyTp2cBJpMM",
            "extra": "https://deckbuilder.egmanevents.com/?deck=OP14-020:1,OP12-034:4,OP15-035:4,ST32-001:4,ST32-005:4,EB04-018:2,OP10-030:2,OP14-033:4,ST32-002:4,OP13-031:2,ST32-003:4,ST16-004:2,ST24-004:4,OP01-055:3,OP06-038:1,OP12-037:2,OP13-040:3,OP14-039:1&type=optcg",
            "raw": "1xOP14-020 4xOP12-034 4xOP15-035 4xST32-001 4xST32-005 2xEB04-018 2xOP10-030 4xOP14-033 4xST32-002 2xOP13-031 4xST32-003 2xST16-004 4xST24-004 3xOP01-055 1xOP06-038 2xOP12-037 3xOP13-040 1xOP14-039",
        },
    ],
    "OP11-041": [
        {
            "slug": "yt-nami-op15-eb04-profile",
            "player": "YouTube",
            "title": "Nami deck profile - OP15/EB04",
            "subtitle": "YouTube standard-format Nami list",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=wvbMkjghVtU",
            "raw": "1xOP11-041 4xP-096 2xOP15-047 1xPRB02-008 3xOP13-042 4xOP14-102 2xOP06-106 4xOP11-106 3xOP06-104 3xOP14-110 3xOP14-111 1xOP15-113 4xEB03-053 4xEB04-058 4xEB03-055 4xOP14-104 4xEB03-060",
        },
        {
            "slug": "yt-ultimate-uy-nami-guide",
            "player": "YouTube",
            "title": "Ultimate Blue/Yellow Nami guide",
            "subtitle": "YouTube OP15 Nami guide list",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=WnXYFHwz08E",
            "raw": "1xOP11-041 4xP-096 1xOP15-047 3xOP13-042 4xOP14-102 3xOP11-106 4xOP06-104 3xOP12-112 4xOP14-110 4xOP14-111 4xEB03-053 4xEB04-058 4xEB03-055 4xOP14-104 4xEB03-060",
        },
        {
            "slug": "yt-kebbieg-op16-nami-gameplay",
            "player": "KebbieG",
            "title": "Nami OP16 gameplay - KebbieG",
            "subtitle": "YouTube OP16 Nami list",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=fZAOabjuE64",
            "raw": "1xOP11-041 4xP-096 1xPRB02-008 3xOP13-042 4xOP14-102 4xOP11-106 2xOP06-104 2xOP12-112 4xOP14-110 4xOP14-111 1xOP15-113 4xEB03-053 4xEB04-058 2xOP14-108 4xEB03-055 4xOP14-104 2xOP16-119 1xOP06-058",
        },
    ],
    "OP16-001": [
        {
            "slug": "web-mabi-op16-ace-infinite-counters",
            "player": "Mabi",
            "title": "Infinite Counters - Mabi",
            "subtitle": "Public MabTCG OP16 red Ace list",
            "kind": "web",
            "source_url": "https://mabitcg.com/one-piece-tcg-portgas-d-ace-op16-infinite-counters-op16-mabi/",
            "raw": "1xOP16-001 4xOP16-002 4xOP13-016 4xOP16-015 4xOP16-017 4xOP16-118 4xOP16-014 4xOP16-011 4xOP16-004 2xOP08-118 4xOP16-005 4xOP16-003 1xOP09-118 3xOP16-020 4xOP16-021",
        },
    ],
    "OP13-079": [
        {
            "slug": "web-mabi-imu-five-elders",
            "player": "Mabi",
            "title": "The Five Elders - Mabi",
            "subtitle": "Public MabTCG black Imu list",
            "kind": "web",
            "source_url": "https://mabitcg.com/one-piece-tcg-imu-op13-the-five-elders-op13-mabi/",
            "raw": "1xOP13-079 4xOP13-086 4xOP13-087 4xOP13-092 4xOP13-083 4xOP13-089 4xOP13-080 4xOP13-091 4xPRB02-014 4xOP13-084 4xOP13-082 4xOP13-096 2xOP13-097 3xOP13-098 1xOP13-099",
        },
    ],
    "OP13-002": [
        {
            "slug": "yt-tcg353-op13-ace-vs-enel",
            "player": "TCG353",
            "title": "OP15 Ace vs Enel - TCG353",
            "subtitle": "YouTube red/blue OP13 Ace tournament list",
            "kind": "youtube",
            "source_url": "https://www.youtube.com/watch?v=hbYhFPZRY5E",
            "raw": "1xOP13-002 4xOP13-016 4xST23-001 4xEB04-007 2xOP09-118 4xOP13-043 4xST22-002 2xOP08-040 1xOP10-045 4xPRB02-008 4xOP13-054 2xST22-010 1xOP07-051 3xOP08-047 4xOP13-042 3xEB04-008 4xST22-015",
        },
    ],
    "OP08-058": [
        {
            "slug": "reddit-pudding-wjyx7brkbb",
            "player": "r/OnePieceTCG",
            "title": "Purple/Yellow Pudding - r/OnePieceTCG",
            "subtitle": "Community screenshot from r/OnePieceTCG · 2026-08-24",
            "kind": "web",
            "source_url": "https://www.reddit.com/r/OnePieceTCG/s/wjyx7BRKbb",
            "raw": "1xOP08-058 4xOP11-070 4xST34-003 4xOP08-062 4xOP05-073 1xOP08-064 4xOP08-063 3xPRB02-010 4xOP11-067 4xOP03-112 4xOP17-109 4xOP17-103 4xOP17-114 2xOP03-113 4xOP03-114",
        },
    ],
}


def parse_raw(raw: str) -> dict[str, int]:
    counts = {}
    for n, cid in LINE_RE.findall(raw):
        cid = cid.upper().replace("PRB", "PRB")
        counts[cid] = counts.get(cid, 0) + int(n)
    return counts


def counts_to_decklist(counts: dict[str, int], cache: dict, leader_id: str) -> dict:
    grouped = {"leader": None, "character": [], "event": [], "stage": []}
    for cid, n in counts.items():
        set_code, number = cid.split("-", 1)
        meta = cache.get(cid) or {}
        name = meta.get("name") or cid
        cat = (meta.get("category") or "").lower()
        if cid == leader_id or cat == "leader":
            grouped["leader"] = {"name": name, "set": set_code, "number": number}
            continue
        item = {"count": n, "name": name, "set": set_code, "number": number}
        if cat == "event":
            grouped["event"].append(item)
        elif cat == "stage":
            grouped["stage"].append(item)
        else:
            grouped["character"].append(item)
    if grouped["leader"] is None:
        set_code, number = leader_id.split("-", 1)
        grouped["leader"] = {"name": cache.get(leader_id, {}).get("name", leader_id), "set": set_code, "number": number}
    return grouped


def community_section(leader: dict, lists: list[dict], tournament_html: str) -> str:
    rows = []
    for entry in lists:
        href = entry["href"]
        title = entry.get("title_override") or entry.get("title")
        subtitle = entry.get("subtitle") or ""
        badge = {"youtube": "YouTube", "x": "X"}.get(entry.get("kind"), "Web")
        copy_btn = gen.copy_sim_button(gen.sim_text_for_entry(leader, entry))
        rows.append(
            f"""            <li class="list-row">
              <a class="item" href="{html.escape(href)}">
                <div>
                  <div style="font-weight:700">{html.escape(title)}</div>
                  <div class="muted" style="font-size:13px">{html.escape(subtitle)}</div>
                </div>
                <div class="link">{html.escape(badge)} →</div>
              </a>
              {copy_btn}
            </li>"""
        )
    comm = f"""        <!-- COMMUNITY_DECKLISTS -->
        <section class="deck-index" style="margin-top:22px">
          <div class="section-title">
            <h3>YouTube and community decklists</h3>
            <div class="muted">{len(lists)} lists</div>
          </div>
          <p class="muted">Public YouTube and web lists with a full 50-card ID list. Tournament tables below are from Limitless.</p>
          <ul class="list" aria-label="YouTube and community decklists">
{chr(10).join(rows)}
          </ul>
        </section>
        <!-- /COMMUNITY_DECKLISTS -->"""
    return comm + "\n" + tournament_html


def main() -> None:
    cache = gen.load_card_cache()
    needed = set()
    parsed = {}
    for lid, items in COMMUNITY.items():
        parsed[lid] = []
        for item in items:
            counts = parse_raw(item["raw"])
            total = sum(counts.values())
            banned = sorted(cid for cid in counts if cid in gen.BANNED_CARDS)
            if banned:
                print("skip banned", lid, item["slug"], banned)
                continue
            print(lid, item["slug"], "cards", total, "unique", len(counts))
            if total < 46 or total > 52:
                raise SystemExit(f"bad count {item['slug']} {total}")
            needed.update(counts)
            parsed[lid].append((item, counts))
    cache = gen.ensure_cards(needed, cache)

    index = json.loads((ROOT / "data/tournament-decks.json").read_text()) if (ROOT / "data/tournament-decks.json").exists() else {}
    community_index = {}

    for leader in gen.LEADERS:
        lid = leader["id"]
        if lid not in parsed:
            continue
        out_dir = ROOT / leader["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        # drop Newgate sample files once real lists exist
        if lid == "OP17-001":
            for sample in out_dir.glob("sample-*.html"):
                sample.unlink()
        public = []
        for item, counts in parsed[lid]:
            dl = counts_to_decklist(counts, cache, lid)
            entry = {
                "player": item["player"],
                "tournament_name": item["title"],
                "placing": None,
                "record": {},
                "date": "",
                "decklist": dl,
                "source_url": item["source_url"],
                "kind": item["kind"],
                "title_override": item["title"],
                "subtitle": item["subtitle"],
                "forced_slug": item["slug"],
            }
            if item.get("extra"):
                entry["source_url"] = item["source_url"]
                extra = item["extra"]
                # bake extra link into subtitle for the page footer via kind note by appending to source
            href = f"/{leader['dir']}/{item['slug']}.html"
            entry["slug"] = item["slug"]
            entry["href"] = href
            page = gen.render_deck_page(leader, entry, cache)
            if item.get("extra"):
                page = page.replace(
                    "</p>\n      </div>\n    </main>",
                    f' Also: <a href="{html.escape(item["extra"])}">{html.escape(item["extra"])}</a>.</p>\n      </div>\n    </main>',
                    1,
                )
            (out_dir / f"{item['slug']}.html").write_text(page)
            public.append(entry)
        community_index[lid] = [
            {"slug": e["slug"], "href": e["href"], "title": e["title_override"], "source_url": e["source_url"], "kind": e["kind"]}
            for e in public
        ]

        page_path = ROOT / leader["page"]
        page_html = page_path.read_text()
        if "<!-- COMMUNITY_DECKLISTS -->" in page_html:
            page_html = re.sub(
                r"        <!-- COMMUNITY_DECKLISTS -->.*?        <!-- /COMMUNITY_DECKLISTS -->\n?",
                "",
                page_html,
                count=1,
                flags=re.S,
            )
        # Match tournament markers only after community is stripped so indices stay valid.
        m = re.search(
            r"        <!-- TOURNAMENT_DECKLISTS -->.*?        <!-- /TOURNAMENT_DECKLISTS -->",
            page_html,
            re.S,
        )
        tournament_block = m.group(0) if m else ""
        if lid == "OP17-001":
            # replace sample-only block with a short note plus community lists
            tournament_block = """        <!-- TOURNAMENT_DECKLISTS -->
        <section class="deck-index" style="margin-top:22px">
          <div class="section-title">
            <h3>Tournament decklists</h3>
            <div class="muted">0 lists</div>
          </div>
          <p class="muted">No Limitless standings for this leader yet. Community lists are above.</p>
        </section>
        <!-- /TOURNAMENT_DECKLISTS -->"""
        combined = community_section(leader, public, tournament_block)
        if m:
            page_html = page_html[: m.start()] + combined + page_html[m.end() :]
        else:
            page_html = gen.insert_section(page_html, combined, gen.render_pool_heading(leader))
        page_path.write_text(page_html)

    (ROOT / "data/community-decks.json").write_text(json.dumps(community_index, indent=2, ensure_ascii=False) + "\n")
    print("done")


if __name__ == "__main__":
    main()
