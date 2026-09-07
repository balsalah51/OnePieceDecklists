#!/usr/bin/env python3
"""Build the BallKeep static site from scraped ranking and schedule sources."""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = "August 20, 2026"


def esc(s):
    return html.escape(str(s), quote=True)


def norm_name(name: str) -> str:
    n = name.lower()
    n = n.replace(".", " ")
    n = re.sub(r"\b(jr|sr|iii|ii|iv)\b", "", n)
    n = n.replace("'", "").replace("’", "")
    n = re.sub(r"\s+", " ", n).strip()
    aliases = {
        "patrick mahomes ii": "patrick mahomes",
        "james cook iii": "james cook",
        "kenneth walker iii": "kenneth walker",
        "luther burden iii": "luther burden",
        "brian thomas jr": "brian thomas",
        "omar cooper jr": "omar cooper",
        "marvin harrison jr": "marvin harrison",
        "michael pittman jr": "michael pittman",
        "kyle pitts sr": "kyle pitts",
        "chris godwin jr": "chris godwin",
        "travis etienne jr": "travis etienne",
        "dandre swift": "dandre swift",
        "d'andre swift": "dandre swift",
        "devon achane": "devon achane",
        "de'von achane": "devon achane",
        "amon ra st brown": "amon-ra st brown",
        "amon-ra st. brown": "amon-ra st brown",
        "ja marr chase": "jamarr chase",
        "jamarr chase": "jamarr chase",
        "nicholas singleton": "nick singleton",
        "nick singleton": "nick singleton",
        "harold fannin jr": "harold fannin",
        "deebo samuel sr": "deebo samuel",
        "aaron jones sr": "aaron jones",
    }
    return aliases.get(n, n)


TEAMS = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
}
TEAM_BY_ABBR = {v: k for k, v in TEAMS.items()}


def parse_pfn(path: Path):
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        m = re.match(
            r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(QB|RB|WR|TE)\s*\|\s*([A-Z]{2,3})\s*\|\s*(\d+)\s*\|",
            line,
        )
        if not m:
            continue
        rows.append({
            "rank": int(m.group(1)),
            "name": m.group(2).strip(),
            "pos": m.group(3),
            "team": m.group(4).replace("GBP", "GB").replace("KCC", "KC").replace("NOS", "NO").replace("SFO", "SF").replace("LVR", "LV").replace("NEP", "NE"),
            "age": int(m.group(5)),
        })
    # keep first occurrence (best overall rank)
    seen = set()
    out = []
    for r in rows:
        k = norm_name(r["name"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def parse_nfl_schedule(path: Path):
    games = []
    week = None
    day = ""
    for line in path.read_text(errors="replace").splitlines():
        wm = re.match(r"WEEK\s+(\d+)", line.strip(), re.I)
        if wm:
            week = int(wm.group(1))
            continue
        dm = re.match(
            r"(Wednesday|Thursday|Friday|Saturday|Sunday|Monday|Date TBD),?\s*(.*)",
            line.strip(),
        )
        if dm and week:
            day = line.strip()
            continue
        gm = re.match(r"\|\s*(.+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if not gm or week is None:
            continue
        matchup = gm.group(1).strip()
        time = gm.group(2).strip()
        tv = gm.group(3).strip().rstrip("*")
        if matchup in ("Matchup", "TBD") or "---" in matchup:
            continue
        loc = ""
        mm = re.match(r"(.+?)\s+(at|vs)\s+(.+?)(?:\s+\((.+)\))?$", matchup)
        if not mm:
            continue
        left, prep, right, loc = mm.group(1).strip(), mm.group(2), mm.group(3).strip(), mm.group(4) or ""
        if left not in TEAMS or right not in TEAMS:
            continue
        away, home = (left, right) if prep == "at" else (left, right)
        games.append({
            "week": week, "day": day, "away": away, "home": home,
            "prep": prep, "time": time, "tv": tv, "note": loc,
        })
    # de-dupe (file repeats week 7)
    uniq = []
    seen = set()
    for g in games:
        key = (g["week"], g["away"], g["home"], g["time"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(g)
    return uniq


# --- additional scraped source ranks (name -> rank) ---
FANTASYPROS_SF = {
    "Drake Maye": 1, "Josh Allen": 2, "Ja'Marr Chase": 3, "Jaxon Smith-Njigba": 4,
    "Bijan Robinson": 5, "Jayden Daniels": 6, "Jahmyr Gibbs": 7, "Puka Nacua": 8,
    "Jalen Hurts": 9, "Lamar Jackson": 10, "Justin Herbert": 11, "Ashton Jeanty": 12,
}
FP_EXPERTS = {
    "Derek Brown (X)": {
        "Josh Allen": 1, "Drake Maye": 2, "Jalen Hurts": 3, "Ja'Marr Chase": 4,
        "Jaxon Smith-Njigba": 5, "Jahmyr Gibbs": 6, "Bijan Robinson": 7, "Puka Nacua": 8,
        "Ashton Jeanty": 11, "Jayden Daniels": 23, "Justin Herbert": 26, "Lamar Jackson": 27,
    },
    "Andrew Erickson (X)": {
        "Drake Maye": 1, "Jayden Daniels": 2, "Josh Allen": 3, "Lamar Jackson": 4,
        "Justin Herbert": 5, "Ja'Marr Chase": 8, "Jaxon Smith-Njigba": 9, "Bijan Robinson": 10,
        "Jalen Hurts": 14, "Jahmyr Gibbs": 16, "Puka Nacua": 18, "Ashton Jeanty": 22,
    },
    "Pat Fitzmaurice (X)": {
        "Drake Maye": 1, "Josh Allen": 2, "Jayden Daniels": 3, "Ja'Marr Chase": 5,
        "Lamar Jackson": 6, "Bijan Robinson": 7, "Jahmyr Gibbs": 8, "Puka Nacua": 9,
        "Jaxon Smith-Njigba": 10, "Justin Herbert": 12, "Ashton Jeanty": 13, "Jalen Hurts": 19,
    },
}
DYNASTY_NERDS = {
    "Josh Allen": 1, "Bijan Robinson": 2, "Drake Maye": 3, "Ja'Marr Chase": 4,
    "Jahmyr Gibbs": 5, "Jaxon Smith-Njigba": 6, "Puka Nacua": 7, "Caleb Williams": 8,
    "Jayden Daniels": 9, "Ashton Jeanty": 10, "Brock Bowers": 11, "Justin Jefferson": 12,
    "De'Von Achane": 13, "CeeDee Lamb": 14, "Amon-Ra St. Brown": 15, "Malik Nabers": 16,
    "Joe Burrow": 17, "Jeremiyah Love": 18, "Lamar Jackson": 19, "Patrick Mahomes": 20,
    "Omarion Hampton": 21, "Justin Herbert": 22, "Trey McBride": 23, "Jaxson Dart": 24,
    "Drake London": 25, "Jalen Hurts": 26, "Tetairoa McMillan": 27, "Trevor Lawrence": 28,
    "Emeka Egbuka": 29, "Jonathan Taylor": 30, "James Cook": 31, "Garrett Wilson": 32,
    "George Pickens": 33, "Brock Purdy": 34, "Bo Nix": 35, "Carnell Tate": 36,
    "Colston Loveland": 37, "Breece Hall": 38, "Ladd McConkey": 39, "Jordan Love": 40,
    "Tyler Warren": 41, "Nico Collins": 42, "Kenneth Walker": 43, "Quinshon Judkins": 44,
    "Chris Olave": 45, "TreVeyon Henderson": 46, "Fernando Mendoza": 47, "Rome Odunze": 48,
    "Marvin Harrison": 49, "Dak Prescott": 50, "Christian McCaffrey": 51, "Brian Thomas": 52,
    "Zay Flowers": 53, "Jordyn Tyson": 54, "Luther Burden": 55, "Makai Lemon": 56,
    "Baker Mayfield": 57, "Chase Brown": 58, "Saquon Barkley": 59, "A.J. Brown": 60,
    "Tee Higgins": 61, "Jared Goff": 62, "Rashee Rice": 63, "Javonte Williams": 64,
    "DeVonta Smith": 65, "Cam Skattebo": 66, "Jaylen Waddle": 67, "Kyren Williams": 68,
    "Cam Ward": 69, "Jadarian Price": 70, "Bucky Irving": 71, "KC Concepcion": 72,
    "Kyle Pitts": 73, "Tucker Kraft": 74, "Jameson Williams": 75, "Harold Fannin": 76,
    "Josh Jacobs": 77, "Travis Etienne": 78, "Sam Darnold": 79, "C.J. Stroud": 80,
    "Kyler Murray": 81, "Christian Watson": 82, "Sam LaPorta": 83, "Bhayshul Tuten": 84,
    "DJ Moore": 85, "Jordan Addison": 86, "Tyler Shough": 87, "Malik Willis": 88,
    "Daniel Jones": 89, "Alec Pierce": 90, "D'Andre Swift": 91, "Omar Cooper": 92,
    "Denzel Boston": 93, "Michael Wilson": 94, "Terry McLaurin": 95, "Ty Simpson": 96,
    "Parker Washington": 97, "Matthew Stafford": 98, "Derrick Henry": 99, "Kenyon Sadiq": 100,
}
KTC_SF = {
    "Jahmyr Gibbs": 1, "Ja'Marr Chase": 2, "Bijan Robinson": 3, "Josh Allen": 4,
    "Jaxon Smith-Njigba": 5, "Drake Maye": 6, "Puka Nacua": 7, "Brock Bowers": 8,
    "Amon-Ra St. Brown": 9, "Caleb Williams": 10, "Lamar Jackson": 11, "Ashton Jeanty": 12,
    "Jeremiyah Love": 13, "Justin Jefferson": 14, "Malik Nabers": 15, "Joe Burrow": 16,
    "Jayden Daniels": 17, "Trey McBride": 18, "CeeDee Lamb": 19, "De'Von Achane": 20,
    "Omarion Hampton": 22, "Justin Herbert": 23, "Drake London": 24, "Jonathan Taylor": 25,
    "Jalen Hurts": 26, "Tetairoa McMillan": 27, "Emeka Egbuka": 28, "Colston Loveland": 29,
    "Patrick Mahomes": 30, "Bo Nix": 31, "George Pickens": 32, "Tyler Warren": 33,
    "Jaxson Dart": 36, "Carnell Tate": 37, "Nico Collins": 38, "Chris Olave": 39,
    "Brock Purdy": 40, "Chase Brown": 41, "Kenneth Walker": 42, "Rome Odunze": 43,
    "Garrett Wilson": 44, "Luther Burden": 47, "Ladd McConkey": 48, "A.J. Brown": 49,
    "Fernando Mendoza": 50,
}
YATES_PPR = [
    ("Bijan Robinson", "RB", "ATL"), ("Jahmyr Gibbs", "RB", "DET"), ("Christian McCaffrey", "RB", "SF"),
    ("Ja'Marr Chase", "WR", "CIN"), ("Puka Nacua", "WR", "LAR"), ("Jaxon Smith-Njigba", "WR", "SEA"),
    ("Jonathan Taylor", "RB", "IND"), ("De'Von Achane", "RB", "MIA"), ("Amon-Ra St. Brown", "WR", "DET"),
    ("James Cook", "RB", "BUF"), ("Derrick Henry", "RB", "BAL"), ("Justin Jefferson", "WR", "MIN"),
    ("CeeDee Lamb", "WR", "DAL"), ("Chase Brown", "RB", "CIN"), ("Kenneth Walker", "RB", "KC"),
    ("Trey McBride", "TE", "ARI"), ("Drake London", "WR", "ATL"), ("Brock Bowers", "TE", "LV"),
    ("Rashee Rice", "WR", "KC"), ("Josh Jacobs", "RB", "GB"), ("Jeremiyah Love", "RB", "ARI"),
    ("Saquon Barkley", "RB", "PHI"), ("Ashton Jeanty", "RB", "LV"), ("Omarion Hampton", "RB", "LAC"),
    ("Malik Nabers", "WR", "NYG"), ("A.J. Brown", "WR", "NE"), ("Chris Olave", "WR", "NO"),
    ("Josh Allen", "QB", "BUF"), ("George Pickens", "WR", "DAL"), ("Javonte Williams", "RB", "DAL"),
    ("Breece Hall", "RB", "NYJ"), ("Kyren Williams", "RB", "LAR"), ("Emeka Egbuka", "WR", "TB"),
    ("Garrett Wilson", "WR", "NYJ"), ("Colston Loveland", "TE", "CHI"), ("Lamar Jackson", "QB", "BAL"),
    ("Travis Etienne", "RB", "NO"), ("Cam Skattebo", "RB", "NYG"), ("Nico Collins", "WR", "HOU"),
    ("Jayden Daniels", "QB", "WAS"), ("Zay Flowers", "WR", "BAL"), ("Tetairoa McMillan", "WR", "CAR"),
    ("DeVonta Smith", "WR", "PHI"), ("Jaylen Waddle", "WR", "DEN"), ("Quinshon Judkins", "RB", "CLE"),
    ("Tyler Warren", "TE", "IND"), ("D'Andre Swift", "RB", "CHI"), ("Drake Maye", "QB", "NE"),
    ("Bucky Irving", "RB", "TB"), ("Davante Adams", "WR", "LAR"), ("Ladd McConkey", "WR", "LAC"),
    ("Jalen Hurts", "QB", "PHI"), ("Harold Fannin", "TE", "CLE"), ("Bhayshul Tuten", "RB", "JAX"),
    ("Chuba Hubbard", "RB", "CAR"), ("Jadarian Price", "RB", "SEA"), ("Tee Higgins", "WR", "CIN"),
    ("Kyle Pitts", "TE", "ATL"), ("Justin Herbert", "QB", "LAC"), ("Terry McLaurin", "WR", "WAS"),
    ("Carnell Tate", "WR", "TEN"), ("David Montgomery", "RB", "HOU"), ("Tony Pollard", "RB", "TEN"),
    ("George Kittle", "TE", "SF"), ("Rhamondre Stevenson", "RB", "NE"), ("TreVeyon Henderson", "RB", "NE"),
    ("Rome Odunze", "WR", "CHI"), ("DK Metcalf", "WR", "PIT"), ("Kenneth Gainwell", "RB", "TB"),
    ("Jaxson Dart", "QB", "NYG"), ("Jaylen Warren", "RB", "PIT"), ("DJ Moore", "WR", "BUF"),
    ("Joe Burrow", "QB", "CIN"), ("Marvin Harrison", "WR", "ARI"), ("Trevor Lawrence", "QB", "JAX"),
    ("Christian Watson", "WR", "GB"), ("Luther Burden", "WR", "CHI"), ("Jameson Williams", "WR", "DET"),
    ("Wan'Dale Robinson", "WR", "TEN"), ("Stefon Diggs", "WR", "WAS"), ("Rachaad White", "RB", "WAS"),
    ("Sam LaPorta", "TE", "DET"), ("Aaron Jones", "RB", "MIN"), ("Michael Wilson", "WR", "ARI"),
    ("Mike Evans", "WR", "SF"), ("Courtland Sutton", "WR", "DEN"), ("Michael Pittman", "WR", "PIT"),
    ("Tucker Kraft", "TE", "GB"), ("Dak Prescott", "QB", "DAL"), ("Patrick Mahomes", "QB", "KC"),
    ("Jakobi Meyers", "WR", "JAX"), ("Jake Ferguson", "TE", "DAL"), ("Chris Godwin", "WR", "TB"),
    ("Dallas Goedert", "TE", "PHI"), ("Kyle Monangai", "RB", "CHI"), ("Brock Purdy", "QB", "SF"),
    ("Matthew Stafford", "QB", "LAR"), ("Bo Nix", "QB", "DEN"), ("Travis Kelce", "TE", "KC"),
    ("J.K. Dobbins", "RB", "DEN"),
]
FP_PPR = {"Ja'Marr Chase": 1, "Jahmyr Gibbs": 2, "Puka Nacua": 3, "Bijan Robinson": 4, "Jaxon Smith-Njigba": 5}

ROOKIES = [
    {"name": "Jeremiyah Love", "pos": "RB", "team": "ARI", "dd": 1, "fp": 1, "pff": 1, "value": "Locked 1.01 · elite RB1 capital"},
    {"name": "Fernando Mendoza", "pos": "QB", "team": "LV", "dd": 2, "fp": 2, "pff": 2, "value": "Clear 1.02 in Superflex · sit-behind-Cousins year-one risk"},
    {"name": "Carnell Tate", "pos": "WR", "team": "TEN", "dd": 3, "fp": 3, "pff": 3, "value": "Safest WR · Day-1 starter with Ward"},
    {"name": "Jordyn Tyson", "pos": "WR", "team": "NO", "dd": 4, "fp": 5, "pff": 5, "value": "Early/mid 1st · Saints volume bet"},
    {"name": "Makai Lemon", "pos": "WR", "team": "PHI", "dd": 5, "fp": 6, "pff": 6, "value": "Mid 1st · crowded Philly room, talent is real"},
    {"name": "Jadarian Price", "pos": "RB", "team": "SEA", "dd": 6, "fp": 4, "pff": 4, "value": "Riser after draft · projected Seattle volume"},
    {"name": "KC Concepcion", "pos": "WR", "team": "CLE", "dd": 7, "fp": 8, "pff": None, "value": "Mid/late 1st · Jeanty-adjacent profile in comments"},
    {"name": "Ty Simpson", "pos": "QB", "team": "LAR", "dd": 11, "fp": 7, "pff": None, "value": "SF-only first · McVay development path"},
    {"name": "Kenyon Sadiq", "pos": "TE", "team": "NYJ", "dd": 8, "fp": 9, "pff": None, "value": "Late 1st TE1 of the class"},
    {"name": "Eli Stowers", "pos": "TE", "team": "PHI", "dd": 9, "fp": 11, "pff": None, "value": "Late 1st / early 2nd TE"},
    {"name": "Omar Cooper", "pos": "WR", "team": "NYJ", "dd": 10, "fp": 10, "pff": None, "value": "Turn-of-1st WR flyer"},
    {"name": "Jonah Coleman", "pos": "RB", "team": "DEN", "dd": 14, "fp": 10, "pff": None, "value": "Early 2nd · Denver committee"},
    {"name": "Denzel Boston", "pos": "WR", "team": "CLE", "dd": 12, "fp": 12, "pff": None, "value": "Early/mid 2nd"},
    {"name": "Antonio Williams", "pos": "WR", "team": "WAS", "dd": 13, "fp": None, "pff": None, "value": "Mid 2nd"},
    {"name": "Nick Singleton", "pos": "RB", "team": "TEN", "dd": 18, "fp": None, "pff": None, "value": "Mid 2nd committee back"},
    {"name": "Germie Bernard", "pos": "WR", "team": "PIT", "dd": 15, "fp": None, "pff": None, "value": "Mid 2nd"},
    {"name": "Chris Bell", "pos": "WR", "team": "MIA", "dd": 16, "fp": None, "pff": None, "value": "Mid/late 2nd"},
    {"name": "De'Zhaun Stribling", "pos": "WR", "team": "SF", "dd": 17, "fp": None, "pff": None, "value": "Late 2nd"},
    {"name": "Carson Beck", "pos": "QB", "team": "ARI", "dd": None, "fp": 19, "pff": None, "value": "Volatile SF 2nd/3rd · high STD DEV"},
    {"name": "Kaytron Allen", "pos": "RB", "team": "WAS", "dd": None, "fp": None, "pff": None, "value": "Day 3 / 3rd-round dart"},
]

HOT = [
    {"name": "Kyler Murray", "pos": "QB", "team": "MIN", "why": "DLF (Aug 16): healthy years were locked top-10 SF QBs; currently priced like a mid-1st rookie pick.", "src": "Dynasty League Football"},
    {"name": "Christian Watson", "pos": "WR", "team": "GB", "why": "Sports Arena + Draft Sharks: WR21 in FPPG Weeks 8–18 last year on a 68% route share; Doubs/Wicks gone.", "src": "Sports Arena, Draft Sharks"},
    {"name": "A.J. Brown", "pos": "WR", "team": "NE", "why": "Sports Arena: PFM WR14 vs FantasyPros ECR WR20. Buy for Luther Burden straight up.", "src": "Sports Arena / PFM"},
    {"name": "Trevor Lawrence", "pos": "QB", "team": "JAX", "why": "FantasyPros TVC + YouTube: closed the gap on Mahomes in the QB8-9 band after a 26 FPPG second half.", "src": "FantasyPros, Fantasy Footballers"},
    {"name": "Jordan Mason", "pos": "RB", "team": "MIN", "why": "Draft Sharks: cheap potential starter in a new Minnesota scheme; buy before a spike week.", "src": "Draft Sharks"},
    {"name": "Tucker Kraft", "pos": "TE", "team": "GB", "why": "FantasyPros: positive ACL reports; 25-year-old TE who looked top-4 before the injury.", "src": "FantasyPros"},
    {"name": "Zay Flowers", "pos": "WR", "team": "BAL", "why": "FantasyPros: new contract + 1,200 yards on a historically run-heavy Ravens offense; new OC hope.", "src": "FantasyPros"},
    {"name": "Harold Fannin Jr.", "pos": "TE", "team": "CLE", "why": "FantasyPros: FBS-leading receiving TE who popped as a rookie; new HC is a TE maven.", "src": "FantasyPros"},
    {"name": "TreVeyon Henderson", "pos": "RB", "team": "NE", "why": "Sports Arena: buy for a projected late 2027 1st. Youth + Patriots backfield.", "src": "Sports Arena"},
    {"name": "Christian McCaffrey", "pos": "RB", "team": "SF", "why": "Sports Arena for contenders only: PFM RB9 vs ECR RB15. Win-now buy, not a rebuild hold.", "src": "Sports Arena"},
]
COLD = [
    {"name": "Brian Thomas Jr.", "pos": "WR", "team": "JAX", "why": "DLF + Sports Arena: Jakobi Meyers + Parker Washington crowding targets. ADP still treats him like a high WR2.", "src": "DLF, Sports Arena"},
    {"name": "Breece Hall", "pos": "RB", "team": "NYJ", "why": "Sports Arena: sell if you can still get true top-10 RB value; efficiency/target share have slipped.", "src": "Sports Arena"},
    {"name": "Makai Lemon", "pos": "WR", "team": "PHI", "why": "Sports Arena: sell the rookie premium for Christian Watson. Philly room is packed.", "src": "Sports Arena"},
    {"name": "Luther Burden III", "pos": "WR", "team": "CHI", "why": "Sports Arena: ECR has him WR19; if that's the ask, move him for A.J. Brown.", "src": "Sports Arena"},
    {"name": "Davante Adams", "pos": "WR", "team": "LAR", "why": "Fantasy Footballers (YouTube): 33-year-old coming off a 14-TD outlier. Cash to a contender.", "src": "Fantasy Footballers"},
    {"name": "DJ Moore", "pos": "WR", "team": "BUF", "why": "Fantasy Footballers: 29, new team, 60-790 line last year. Sell the name.", "src": "Fantasy Footballers"},
    {"name": "Ricky Pearsall", "pos": "WR", "team": "SF", "why": "FantasyPros live update: out until ~next September, age 27 on return. Clear sell for win-now clubs.", "src": "FantasyPros"},
    {"name": "RJ Harvey", "pos": "RB", "team": "DEN", "why": "Draft Sharks: Broncos brought J.K. Dobbins back; not a locked lead back.", "src": "Draft Sharks"},
    {"name": "Rashee Rice", "pos": "WR", "team": "KC", "why": "Draft Sharks: Chiefs look run-leaning; sell while redraft boards still pay WR10-ish.", "src": "Draft Sharks"},
    {"name": "Jonathon Brooks", "pos": "RB", "team": "CAR", "why": "FantasyPros: two ACLs in 13 months, still unproven, market near RB26.", "src": "FantasyPros"},
]


def meta_map(pfn_rows):
    m = {}
    for r in pfn_rows:
        m[norm_name(r["name"])] = r
    return m


def aggregate(pfn_rows):
    sources = {
        "PFN (Katz/Soppe)": {norm_name(r["name"]): r["rank"] for r in pfn_rows},
        "Dynasty Nerds": {norm_name(n): r for n, r in DYNASTY_NERDS.items()},
        "FantasyPros ECR": {norm_name(n): r for n, r in FANTASYPROS_SF.items()},
        "KeepTradeCut SF": {norm_name(n): r for n, r in KTC_SF.items()},
    }
    for expert, board in FP_EXPERTS.items():
        sources[expert] = {norm_name(n): r for n, r in board.items()}
    meta = meta_map(pfn_rows)
    names = set()
    for src in sources.values():
        names.update(src)
    rows = []
    for key in names:
        ranks = {s: src[key] for s, src in sources.items() if key in src}
        if not ranks:
            continue
        avg = sum(ranks.values()) / len(ranks)
        # require at least one long board
        if "PFN (Katz/Soppe)" not in ranks and "Dynasty Nerds" not in ranks:
            continue
        info = meta.get(key, {})
        display = info.get("name")
        if not display:
            for n in list(DYNASTY_NERDS) + list(KTC_SF) + list(FANTASYPROS_SF):
                if norm_name(n) == key:
                    display = n
                    break
        rows.append({
            "key": key,
            "name": display or key.title(),
            "pos": info.get("pos") or "",
            "team": info.get("team") or "",
            "age": info.get("age") or "",
            "avg": round(avg, 2),
            "n": len(ranks),
            "ranks": ranks,
        })
    rows.sort(key=lambda r: (r["avg"], -r["n"], r["name"]))
    for i, r in enumerate(rows, 1):
        r["bk"] = i
    return rows, sources


def redraft_lists():
    ppr = []
    for i, (name, pos, team) in enumerate(YATES_PPR, 1):
        fp = FP_PPR.get(name)
        avg = (i + fp) / 2 if fp else float(i)
        ppr.append({"bk": 0, "name": name, "pos": pos, "team": team, "yates": i, "fp": fp or "—", "avg": avg})
    ppr.sort(key=lambda r: r["avg"])
    for i, r in enumerate(ppr[:100], 1):
        r["bk"] = i
    # Standard: bump RB, slight WR/TE tax vs PPR
    std = []
    for r in ppr:
        adj = r["avg"]
        if r["pos"] == "RB":
            adj -= 4.5
        elif r["pos"] == "WR":
            adj += 3.0
        elif r["pos"] == "TE":
            adj += 2.0
        elif r["pos"] == "QB":
            adj += 0.5
        std.append({**r, "avg": round(adj, 2)})
    std.sort(key=lambda r: r["avg"])
    out = []
    for i, r in enumerate(std[:100], 1):
        out.append({**r, "bk": i})
    return ppr[:100], out


NAV = [
    ("index.html", "Home"),
    ("the-keep.html", "The Keep"),
    ("redraft-ppr.html", "Redraft PPR"),
    ("redraft-standard.html", "Redraft STD"),
    ("rookies-2026.html", "2026 Rookies"),
    ("hot-n-cold.html", "Hot 'n' Cold"),
    ("board.html", "The Board"),
    ("nfl-schedule.html", "NFL"),
    ("mlb-schedule.html", "MLB"),
    ("discord.html", "Discord"),
]


def page(title, path, body, extra_js=""):
    links = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == path else ""
        links.append(f'<a href="{href}"{cur}>{esc(label)}</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{esc(title)} — Ball Keep</title>
  <meta name="description" content="Ball Keep dynasty and redraft rankings, schedules, and market notes." />
  <link rel="stylesheet" href="css/site.css" />
  <link rel="icon" href="img/logo.jpg" />
</head>
<body>
  <div class="wrap">
    <header class="site">
      <a class="brand" href="index.html">
        <img src="img/logo.jpg" alt="Ball Keep circular logo" />
        <div>
          <h1>BALL KEEP</h1>
          <p>Dynasty · redraft · ball</p>
        </div>
      </a>
      <nav>{''.join(links)}</nav>
    </header>
    {body}
    <footer>© {date.today().year} Ball Keep · ballkeep.com · Rankings aggregated {UPDATED}. Sources linked on each board. Not affiliated with the NFL or MLB.</footer>
  </div>
  {extra_js}
</body>
</html>
"""


def rank_table(rows, extra_headers=None, extra_cells=None):
    extra_headers = extra_headers or []
    extra_cells = extra_cells or (lambda r: "")
    head = "".join(f"<th>{esc(h)}</th>" for h in ["BK", "Player", "Pos", "Team"] + extra_headers)
    body = []
    for r in rows:
        pos = r.get("pos") or ""
        body.append(
            "<tr>"
            f'<td class="rk">{r.get("bk","")}</td>'
            f"<td><strong>{esc(r['name'])}</strong></td>"
            f'<td><span class="pos {esc(pos)}">{esc(pos)}</span></td>'
            f"<td>{esc(r.get('team',''))}</td>"
            f"{extra_cells(r)}"
            "</tr>"
        )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def write(path, html_doc):
    (ROOT / path.lstrip("/")).write_text(html_doc)


def main():
    pfn = parse_pfn(ROOT / "data/pfn-dynasty.txt")
    nfl = parse_nfl_schedule(ROOT / "data/nfl-schedule.txt")
    board, sources = aggregate(pfn)
    keep = board[:100]
    ppr, std = redraft_lists()

    (ROOT / "data/the-keep.json").write_text(json.dumps({
        "updated": UPDATED,
        "sources": list(sources),
        "players": keep,
    }, indent=2))
    (ROOT / "data/board.json").write_text(json.dumps(board, indent=2))

    # HOME
    tiles = [
        ("the-keep.html", "The Keep", "Daily Superflex dynasty top 100. Our keystone board."),
        ("redraft-ppr.html", "Redraft PPR", "2026 startup board for full-PPR redraft."),
        ("redraft-standard.html", "Redraft Standard", "Same season, no reception point. Different order."),
        ("rookies-2026.html", "2026 Rookies", "Drafted class consensus ranks and Superflex values."),
        ("hot-n-cold.html", "BK Hot 'n' Cold", "Buys and sells scraped from dynasty desks and film shows."),
        ("board.html", "The Board", "The long proprietary aggregate — every ranked name we pulled."),
        ("nfl-schedule.html", "NFL schedules", "2026 week-by-week slate and all 32 team pages."),
        ("mlb-schedule.html", "MLB schedules", "September stretch run, filterable by club."),
        ("discord.html", "Discord", "The circular mark. Community room coming online."),
    ]
    home_body = f"""
    <section class="hero" style="background-image:url('img/hero.jpg')">
      <div class="hero-card">
        <p class="kicker" style="color:#ffd4db">Updated {UPDATED}</p>
        <h2>BALL KEEP</h2>
        <p>A powder-blue desk for dynasty and redraft. Football first. Baseball in season. One board, many experts, no fluff.</p>
      </div>
    </section>
    <section class="panel">
      <p class="kicker">What this site is</p>
      <h2>Keep the guys who still matter in 2029.</h2>
      <p class="note"><strong>Fantasy football</strong> is a one-year contest: you draft, you stream, you chase weekly points. <strong>Dynasty football</strong> is a roster you keep. Young quarterbacks, incoming rookies, and contract years all change the price. Superflex (a second QB slot) makes passers first-round assets instead of round-eight afterthoughts.</p>
      <p class="note"><strong>Fantasy baseball</strong> is the same split. Redraft/roto is this summer's counting stats. <strong>Dynasty baseball</strong> prices the next five years — peak age, service time, and whether a 22-year-old shortstop is still a shortstop in 2030. ESPN's current dynasty formula weights 2027–2030 at 80% of value.</p>
      <p class="note">Ball Keep aggregates public expert boards (FantasyPros, PFN, Dynasty Nerds, KeepTradeCut, ESPN, DLF, Draft Sharks, plus X ranks from Brown / Erickson / Fitzmaurice and YouTube trade shows) into one number. We do not pretend a podcast hot take is a 300-player sheet. Every list names the sources.</p>
    </section>
    <div class="grid-3" style="margin-top:16px">
      {''.join(f'<a class="tile" href="{h}"><h3>{esc(t)}</h3><p>{esc(p)}</p></a>' for h,t,p in tiles)}
    </div>
    """
    write("index.html", page("Home", "/", home_body))

    # THE KEEP
    def keep_extra(r):
        bits = "".join(f"<div><small>{esc(s)}</small> {v}</div>" for s, v in sorted(r["ranks"].items()))
        return f'<td>{r["avg"]}</td><td>{r["n"]}</td><td class="note">{bits}</td>'
    keep_body = f"""
    <p class="kicker">Keystone · Superflex dynasty</p>
    <h2>The Keep</h2>
    <p class="note">Top 100 for Superflex dynasty leagues, rebuilt {UPDATED}. Ball Keep rank is the average of every source that ranked the player. PFN (Katz/Soppe composite) and Dynasty Nerds are the full boards. FantasyPros ECR plus Derek Brown, Andrew Erickson, and Pat Fitzmaurice (all posted to X) cover the top. KeepTradeCut is the Superflex market tape. YouTube/podcast names are used on Hot 'n' Cold, not forced into a 1–100 they never published.</p>
    <div class="panel">{rank_table(keep, ["Avg", "Sources", "By board"], keep_extra)}</div>
    """
    write("the-keep.html", page("The Keep", "/the-keep.html", keep_body))

    # REDRAFT
    def ppr_extra(r):
        return f'<td>{r["yates"]}</td><td>{r["fp"]}</td>'
    ppr_body = f"""
    <p class="kicker">2026 redraft · PPR</p>
    <h2>Redraft PPR</h2>
    <p class="note">Full-PPR, 1QB. Primary board: Field Yates (ESPN, updated Aug 17). Overlay: FantasyPros Expert Consensus top (152 experts, Aug 20) where published. Kickers and DST from Yates are omitted so this stays a skill-player draft sheet.</p>
    <div class="panel">{rank_table(ppr, ["Yates", "FP ECR"], ppr_extra)}</div>
    """
    write("redraft-ppr.html", page("Redraft PPR", "/redraft-ppr.html", ppr_body))

    std_body = f"""
    <p class="kicker">2026 redraft · no PPR</p>
    <h2>Redraft Standard</h2>
    <p class="note">Standard (no extra point per catch) is a different sport than PPR. We start from the PPR consensus above, then apply Ball Keep positional taxes used across major STD vs PPR deltas: running backs −4.5 ranks, receivers +3, tight ends +2, quarterbacks +0.5. Result: Bijan/Gibbs/CMC/Henry/Taylor climb; Chase/Puka/JSN still go early but not as automatic 1.01s.</p>
    <div class="panel">{rank_table(std, ["Adj. score"], lambda r: f'<td>{r["avg"]}</td>')}</div>
    """
    write("redraft-standard.html", page("Redraft Standard", "/redraft-standard.html", std_body))

    # ROOKIES
    rook_rows = []
    for r in ROOKIES:
        nums = [x for x in (r["dd"], r["fp"], r["pff"]) if x]
        avg = round(sum(nums) / len(nums), 2) if nums else 99.0
        rook_rows.append({**r, "bk": 0, "avg": avg, "dd": r["dd"] or "—", "fp": r["fp"] or "—", "pff": r["pff"] or "—"})
    rook_rows.sort(key=lambda r: r["avg"])
    for i, r in enumerate(rook_rows, 1):
        r["bk"] = i
    rook_body = f"""
    <p class="kicker">2026 NFL Draft class</p>
    <h2>Notable drafted rookies</h2>
    <p class="note">Superflex rookie consensus from Dynasty Dealer (13-analyst team board, July 30), FantasyPros Superflex rookie ECR (August), and PFF's Superflex rookie column (Love / Mendoza / Tate locked 1-2-3). Values are startup/rookie-draft language, not salary-cap dollars.</p>
    <div class="panel">{rank_table(rook_rows, ["Avg", "Dealer", "FP", "PFF", "Value"], lambda r: f'<td>{r["avg"]}</td><td>{r["dd"]}</td><td>{r["fp"]}</td><td>{r["pff"]}</td><td class="note">{esc(r["value"])}</td>')}</div>
    """
    write("rookies-2026.html", page("2026 Rookies", "/rookies-2026.html", rook_body))

    # HOT COLD
    def hc_cards(items, cls):
        out = []
        for i, x in enumerate(items, 1):
            out.append(
                f'<article class="tile {cls}"><span class="badge">{i}</span> '
                f'<h3>{esc(x["name"])} <span class="pos {esc(x["pos"])}">{esc(x["pos"])}</span> {esc(x["team"])}</h3>'
                f'<p>{esc(x["why"])}</p><p class="note">Source: {esc(x["src"])}</p></article>'
            )
        return "".join(out)
    hc_body = f"""
    <p class="kicker">Market tape · {UPDATED}</p>
    <h2>BK Hot 'n' Cold</h2>
    <p class="note">Rising names to buy and aging/overpriced names to sell, pulled from DLF trending notes (Aug 16), Sports Arena trade targets (Aug 11), Draft Sharks (Aug 14), FantasyPros Trade Value Chart show (August), and the Fantasy Footballers dynasty trade episode on YouTube.</p>
    <div class="grid">
      <div>
        <h3 style="color:var(--red)">Hot — buy</h3>
        {hc_cards(HOT, "hot")}
      </div>
      <div>
        <h3 style="color:#1d4f8a">Cold — sell</h3>
        {hc_cards(COLD, "cold")}
      </div>
    </div>
    """
    write("hot-n-cold.html", page("Hot 'n' Cold", "/hot-n-cold.html", hc_body))

    # LONG BOARD
    src_names = list(sources)
    def board_extra(r):
        cells = []
        for s in src_names:
            cells.append(f"<td>{r['ranks'].get(s, '—')}</td>")
        cells.append(f"<td>{r['avg']}</td><td>{r['n']}</td>")
        return "".join(cells)
    board_body = f"""
    <p class="kicker">Proprietary aggregate</p>
    <h2>The Board</h2>
    <p class="note">Every player we could pin to at least one full Superflex dynasty board, ordered by Ball Keep average. This is the long file we will refresh with The Keep. Methodology: simple mean of published ranks; unranked sources are skipped (not treated as 999). That slightly favors household names who appear on short expert lists — which is the point of a consensus tape, not a recency-weighted model.</p>
    <div class="panel" style="overflow:auto">{rank_table(board, src_names + ["Avg", "#"], board_extra)}</div>
    """
    write("board.html", page("The Board", "/board.html", board_body))

    # NFL schedule
    weeks = sorted({g["week"] for g in nfl})
    nfl_js_games = json.dumps(nfl)
    week_btns = "".join(f'<button type="button" data-week="{w}">W{w}</button>' for w in weeks)
    team_btns = "".join(
        f'<button type="button" data-team="{esc(abbr)}">{esc(abbr)}</button>'
        for abbr in sorted(TEAM_BY_ABBR)
    )
    nfl_body = f"""
    <p class="kicker">2026 NFL regular season</p>
    <h2>NFL schedule</h2>
    <p class="note">Full slate from NFL Football Operations (released May 14). Kickoff is Wednesday, Sept. 9 in Seattle. Filter by week or club for the individual team schedule. International sites: Melbourne, Rio, London, Paris, Madrid, Munich, Mexico City.</p>
    <p class="note">Weeks</p>
    <div class="filters" id="weeks"><button type="button" class="active" data-week="all">All</button>{week_btns}</div>
    <p class="note">Teams</p>
    <div class="filters" id="teams"><button type="button" class="active" data-team="all">All clubs</button>{team_btns}</div>
    <div class="panel" id="games"></div>
    """
    nfl_js = f"""<script>
    const GAMES = {nfl_js_games};
    const ABBR = {json.dumps(TEAMS)};
    let week = 'all', team = 'all';
    function render() {{
      const rows = GAMES.filter(g => {{
        const wa = ABBR[g.away], wh = ABBR[g.home];
        const okW = week === 'all' || String(g.week) === String(week);
        const okT = team === 'all' || wa === team || wh === team;
        return okW && okT;
      }});
      const body = rows.map(g => {{
        const loc = g.note ? ` (${{g.note}})` : '';
        const line = g.prep === 'at' ? `${{g.away}} at ${{g.home}}` : `${{g.away}} vs ${{g.home}}`;
        return `<tr><td>W${{g.week}}</td><td>${{g.day}}</td><td><strong>${{line}}</strong>${{loc}}</td><td>${{g.time}} ET</td><td>${{g.tv}}</td></tr>`;
      }}).join('');
      document.getElementById('games').innerHTML = `<table><thead><tr><th>Wk</th><th>Day</th><th>Matchup</th><th>Time</th><th>TV</th></tr></thead><tbody>${{body}}</tbody></table>`;
    }}
    function bind(id, key, setter) {{
      document.getElementById(id).addEventListener('click', e => {{
        const b = e.target.closest('button'); if (!b) return;
        document.querySelectorAll('#' + id + ' button').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        setter(b.dataset[key]);
        render();
      }});
    }}
    bind('weeks', 'week', v => week = v);
    bind('teams', 'team', v => team = v);
    render();
    </script>"""
    write("nfl-schedule.html", page("NFL Schedule", "/nfl-schedule.html", nfl_body, nfl_js))

    # MLB September
    mlb_games = []
    mlb_html = ROOT / "data/mlb-september.html"
    if mlb_html.exists():
        day = ""
        blob = mlb_html.read_text(errors="replace")
        for token in re.finditer(
            r'<h4 class="amazon passion toptop">([^<]+)</h4>|<span class="right devil">([^<]+)</span>\s*<img[^>]+>\s*<span class="small">([A-Z]{2,3})</span>\s*<span[^>]*>@</span>\s*<img[^>]+>\s*<span class="small">([A-Z]{2,3})</span>',
            blob,
        ):
            if token.group(1):
                day = token.group(1).strip()
            elif day:
                mlb_games.append({
                    "day": day,
                    "time": token.group(2).strip(),
                    "away": token.group(3),
                    "home": token.group(4),
                })
    mlb_abbrs = sorted({g["away"] for g in mlb_games} | {g["home"] for g in mlb_games})
    mlb_btns = "".join(f'<button type="button" data-team="{esc(a)}">{esc(a)}</button>' for a in mlb_abbrs)
    mlb_body = f"""
    <p class="kicker">MLB · stretch run</p>
    <h2>Baseball schedules</h2>
    <p class="note">Today is Aug. 20, 2026 — the regular season wraps Sunday, Sept. 27. Below is the full September slate (Fantasy Nerds / league schedule). Filter by club for that team's remaining games. For the live daily tick, use ESPN's MLB scoreboard. Dynasty baseball prices 2027–2031 heavier than this month's box score; redraft baseball is only this month.</p>
    <div class="filters" id="mlb-teams"><button type="button" class="active" data-team="all">All clubs</button>{mlb_btns}</div>
    <div class="panel" id="mlb-games"></div>
    """
    mlb_js = f"""<script>
    const MLB = {json.dumps(mlb_games)};
    let team = 'all';
    function render() {{
      const rows = MLB.filter(g => team === 'all' || g.away === team || g.home === team)
        .map(g => `<tr><td>${{g.day}}</td><td><strong>${{g.away}} @ ${{g.home}}</strong></td><td>${{g.time}}</td></tr>`).join('');
      document.getElementById('mlb-games').innerHTML = `<table><thead><tr><th>Date</th><th>Matchup</th><th>Time</th></tr></thead><tbody>${{rows}}</tbody></table>`;
    }}
    document.getElementById('mlb-teams').addEventListener('click', e => {{
      const b = e.target.closest('button'); if (!b) return;
      document.querySelectorAll('#mlb-teams button').forEach(x => x.classList.remove('active'));
      b.classList.add('active'); team = b.dataset.team; render();
    }});
    render();
    </script>"""
    write("mlb-schedule.html", page("MLB Schedule", "/mlb-schedule.html", mlb_body, mlb_js))

    # Discord
    disc = """
    <div class="panel discord-hero">
      <img src="img/discord.jpg" alt="Ball Keep circular Discord logo" />
      <p class="kicker">Community</p>
      <h2>Ball Keep on Discord</h2>
      <p class="note">Red primary. White BK. Black ring. This is the mark for the server — ranks chat, trade block, and The Keep daily drop.</p>
      <a class="cta" href="#">Invite drops with the first Keep refresh</a>
    </div>
    """
    write("discord.html", page("Discord", "/discord.html", disc))

    print(f"Keep {len(keep)} Board {len(board)} NFL games {len(nfl)} MLB {len(mlb_games)}")


if __name__ == "__main__":
    main()
