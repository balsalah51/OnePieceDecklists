#!/usr/bin/env python3
"""Host complete OP17-splash lists from the public OPDeckGuide tournament hub.

The r/OnePieceTCG "OP17 tournament decklist" post links here. Only writes a page
when the sim dump is 1 leader + 50 cards, includes an OP17 card, and has no bans.
Adds ST30 Luffy & Ace if that list splashes OP17. Does not wipe existing pages.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path("/workspace")
HUB = "https://opdeckguide.com/tournaments-decklists/"
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com; public OPTCG list scrape)"
HREF_RE = re.compile(r'href="(/tournaments-decklists/op17-(?:east|west)/[^"#?]+)"')
SIM_RE = re.compile(r'data-sim-deck="([^"]+)"')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
META_RE = re.compile(
    r'<span class="meta-label"[^>]*>(.*?)</span>\s*<[^>]+>(.*?)</',
    re.S,
)
DATE_RE = re.compile(r"(aug|sep)(\d{1,2})", re.I)
TAG_RE = re.compile(r"<[^>]+>")
NEW_IDS = {"ST30-001"}


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.read().decode("utf-8", "replace") if exc.fp else ""


def clean(text: str) -> str:
    return " ".join(TAG_RE.sub("", text).replace("&amp;", "&").split())


def collect_paths() -> list[str]:
    paths: list[str] = []
    for page in (HUB, HUB + "op17-east/", HUB + "op17-west/"):
        body = fetch(page)
        for href in HREF_RE.findall(body):
            if href not in paths and href.rstrip("/") != "/tournaments-decklists/op17-east":
                if href.rstrip("/") != "/tournaments-decklists/op17-west":
                    paths.append(href)
        time.sleep(0.12)
    return paths


def parse_page(path: str, comm, gen) -> dict | None:
    url = "https://opdeckguide.com" + path
    body = fetch(url)
    sim = SIM_RE.search(body)
    if not sim:
        print("no sim", path)
        return None
    raw = " ".join(sim.group(1).split())
    counts = comm.parse_raw(raw)
    lids = [cid for cid in counts if cid in {L["id"] for L in gen.LEADERS} or cid in NEW_IDS]
    if len(lids) != 1:
        # first 1x card is the leader
        ones = [cid for cid, n in counts.items() if n == 1]
        lid = ones[0] if ones else None
    else:
        lid = lids[0]
    if not lid:
        print("no leader", path, counts)
        return None
    main_n = sum(n for cid, n in counts.items() if cid != lid)
    banned = [cid for cid in counts if cid in gen.BANNED_CARDS]
    has_op17 = any(cid.startswith("OP17-") for cid in counts)
    print(path, "leader", lid, "cards", main_n, "op17", has_op17, "banned", banned)
    if counts.get(lid) != 1 or main_n != 50 or banned or not has_op17:
        return None
    title_html = TITLE_RE.search(body)
    h1 = H1_RE.search(body)
    title = clean(h1.group(1) if h1 else (title_html.group(1) if title_html else path))
    meta = {clean(a): clean(b) for a, b in META_RE.findall(body)}
    player = meta.get("Author") or path.rstrip("/").split("-")[-1]
    host = meta.get("Host") or meta.get("Location") or "OPDeckGuide"
    slug_tail = path.rstrip("/").split("/")[-1]
    month = DATE_RE.search(slug_tail)
    if month:
        mon = "08" if month.group(1).lower() == "aug" else "09"
        date = f"2026-{mon}-{int(month.group(2)):02d}"
    else:
        date = "2026-08-22"
    return {
        "leader": lid,
        "kind": "web",
        "player": player,
        "title": title if title else slug_tail,
        "subtitle": f"{host} · public list from OPDeckGuide",
        "source_url": url,
        "slug": f"opdeck-{slug_tail}"[:70],
        "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
        "cards": main_n,
        "date": date,
    }


def write_hubs(gen, cache: dict) -> None:
    for leader in gen.LEADERS:
        if leader["id"] not in NEW_IDS:
            continue
        path = gen.ROOT / leader["page"]
        (gen.ROOT / leader["dir"]).mkdir(parents=True, exist_ok=True)
        if path.exists():
            print("hub exists", path)
            continue
        path.write_text(gen.render_hub_page(leader, cache))
        print("wrote hub", path)


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    ana = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")

    cache = gen.ensure_cards(NEW_IDS, gen.load_card_cache())
    print("=== hubs ===")
    write_hubs(gen, cache)

    print("=== collect OPDeckGuide lists ===")
    paths = collect_paths()
    print("paths", len(paths))
    found = []
    seen: set[str] = set()
    for path in paths:
        item = parse_page(path, comm, gen)
        time.sleep(0.12)
        if not item:
            continue
        commsrc.record(found, item, seen)

    log_path = ROOT / "data/opdeckguide-log.json"
    log_path.write_text(json.dumps({"hosted": found}, indent=2, ensure_ascii=False) + "\n")
    print("ready", len(found), "log", log_path)

    print("=== write lists ===")
    touched = commsrc.write_lists(found)
    print("touched", sorted(touched))

    index = more.load_index()
    more.rebuild_hubs(index)
    more.rewrite_sitemap()
    print("=== consensus ===")
    ana.main()
    print("=== homepage / guides ===")
    up.patch_home()
    up.patch_op17()
    seo.main()
    print("=== TCGplayer ===")
    buy = load("tcgbuy", "/workspace/scripts/add-tcgplayer-buy.py")
    buy.main()
    print("=== SEO ===")
    seofix = load("seofix", "/workspace/scripts/enhance-seo.py")
    seofix.main()
    print("opdeckguide ingest done")


if __name__ == "__main__":
    main()
