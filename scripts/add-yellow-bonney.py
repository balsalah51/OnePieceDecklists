#!/usr/bin/env python3
"""Add yellow OP13 Bonney and host 5 complete lists that splash OP17.

Does not run generate-tournament-lists.main().
Does not wipe existing leader lists.
Does not invent cards from screenshots.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request

YELLOW = "OP13-100"
TARGET = 5
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com; public OPTCG list scrape)"
MAIN_RE = re.compile(r"mainDeck:\s*(\[[^\]]+\])")
CARD_RE = re.compile(r"^((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})$")
SIM_RE = re.compile(r'data-sim-deck="([^"]+)"')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
META_RE = re.compile(
    r'<span class="meta-label"[^>]*>(.*?)</span>\s*<[^>]+>(.*?)</',
    re.S,
)
BY_RE = re.compile(r"\bby\s+([^<-]+?)(?:\s*-\s*OnePieceDB)?\s*$", re.I)
DATE_RE = re.compile(r"(2026-\d{2}-\d{2})")
TAG_RE = re.compile(r"<[^>]+>")
DECK_HREF_RE = re.compile(r'href="(https://onepiecedb\.io/deck/[^"]+)"')
OPDECK_HREF_RE = re.compile(r'href="(/tournaments-decklists/op17-(?:east|west)/[^"#?]*bonney[^"#?]*)"', re.I)


def load(name: str, path: str):
    spec = __import__("importlib.util").util.spec_from_file_location(name, path)
    mod = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch(url: str, timeout: int = 22, accept: str = "text/html") -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def clean(text: str) -> str:
    return " ".join(TAG_RE.sub("", text or "").replace("&amp;", "&").split())


def has_op17(counts: dict[str, int]) -> bool:
    return any(cid.startswith("OP17-") for cid in counts)


def write_hub(gen) -> None:
    cache = gen.ensure_cards({YELLOW}, gen.load_card_cache())
    leader = next(L for L in gen.LEADERS if L["id"] == YELLOW)
    path = gen.ROOT / leader["page"]
    (gen.ROOT / leader["dir"]).mkdir(parents=True, exist_ok=True)
    if path.exists():
        print("hub exists", path)
        return
    path.write_text(gen.render_hub_page(leader, cache))
    print("wrote hub", path)


def opdeck_items(gen, comm) -> list[dict]:
    found: list[dict] = []
    try:
        hub = fetch("https://opdeckguide.com/tournaments-decklists/")
    except Exception as exc:  # noqa: BLE001
        print("opdeck hub fail", exc, flush=True)
        return found
    paths = []
    for href in OPDECK_HREF_RE.findall(hub):
        if href not in paths:
            paths.append(href)
    print("opdeck bonney paths", paths, flush=True)
    for path in paths:
        url = "https://opdeckguide.com" + path
        try:
            body = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print("opdeck fail", path, exc, flush=True)
            continue
        sim = SIM_RE.search(body)
        if not sim:
            print("opdeck no sim", path, flush=True)
            continue
        raw = " ".join(sim.group(1).split())
        counts = comm.parse_raw(raw)
        if counts.get(YELLOW) != 1:
            print("opdeck skip leader", path, "counts", counts.get(YELLOW), flush=True)
            continue
        main_n = sum(n for cid, n in counts.items() if cid != YELLOW)
        if main_n != 50 or not has_op17(counts) or any(cid in gen.BANNED_CARDS for cid in counts):
            print("opdeck skip", path, "cards", main_n, "op17", has_op17(counts), flush=True)
            continue
        title_html = TITLE_RE.search(body)
        h1 = H1_RE.search(body)
        title = clean(h1.group(1) if h1 else (title_html.group(1) if title_html else path))
        meta = {clean(a): clean(b) for a, b in META_RE.findall(body)}
        player = meta.get("Author") or path.rstrip("/").split("-")[-1]
        host = meta.get("Host") or meta.get("Location") or "OPDeckGuide"
        slug_tail = path.rstrip("/").split("/")[-1]
        day = ""
        m = re.search(
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*-?(\d{1,2})",
            slug_tail,
            re.I,
        )
        months = {
            "jan": "01",
            "feb": "02",
            "mar": "03",
            "apr": "04",
            "may": "05",
            "jun": "06",
            "jul": "07",
            "aug": "08",
            "sep": "09",
            "oct": "10",
            "nov": "11",
            "dec": "12",
        }
        if m:
            day = f"2026-{months[m.group(1)[:3].lower()]}-{int(m.group(2)):02d}"
        found.append(
            {
                "leader": YELLOW,
                "kind": "web",
                "player": player,
                "title": title or slug_tail,
                "subtitle": f"{host} · public list from OPDeckGuide",
                "source_url": url,
                "slug": f"opdeck-{slug_tail}"[:70],
                "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                "cards": main_n,
                "date": day or "2026-09-01",
            }
        )
        print("opdeck keep", player, day, "op17", True, flush=True)
        time.sleep(0.12)
    return found


def opdb_items(gen, comm) -> list[dict]:
    found: list[dict] = []
    page = "https://onepiecedb.io/category/leader/jewelry-bonney-op13-100"
    try:
        body = fetch(page)
    except Exception as exc:  # noqa: BLE001
        print("opdb category fail", exc, flush=True)
        return found
    urls = []
    for href in DECK_HREF_RE.findall(body):
        if href not in urls:
            urls.append(href)
    print("opdb urls", urls, flush=True)
    for url in urls:
        try:
            page_body = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print("opdb fail", url, exc, flush=True)
            continue
        m = MAIN_RE.search(page_body)
        if not m:
            print("opdb no main", url, flush=True)
            continue
        try:
            arr = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        counts: dict[str, int] = {}
        for raw in arr:
            cid = str(raw).upper().split("_")[0]
            if CARD_RE.match(cid):
                counts[cid] = counts.get(cid, 0) + 1
        # OnePieceDB sometimes stores the 50-card main separately from the
        # leader. The category page and og:image still name OP13-100.
        if counts.get(YELLOW) != 1 and "OP13-100" in page_body:
            main_only = sum(counts.values())
            if main_only == 50:
                counts[YELLOW] = 1
                print("opdb added leader from page", url.rsplit("/", 1)[-1], flush=True)
            else:
                print("opdb skip no leader", url.rsplit("/", 1)[-1], "cards", main_only, flush=True)
                continue
        main_n = sum(n for cid, n in counts.items() if cid != YELLOW)
        if counts.get(YELLOW) != 1 or main_n != 50:
            print("opdb skip size", url.rsplit("/", 1)[-1], "leader", counts.get(YELLOW), "cards", main_n, flush=True)
            continue
        if not has_op17(counts) or any(cid in gen.BANNED_CARDS for cid in counts):
            print("opdb skip op17/ban", url.rsplit("/", 1)[-1], "op17", has_op17(counts), flush=True)
            continue
        title_html = TITLE_RE.search(page_body)
        title = clean(title_html.group(1) if title_html else url.rsplit("/", 1)[-1])
        title = title.replace(" - OnePieceDB", "").strip()
        player = "OnePieceDB"
        by = BY_RE.search(title)
        if by:
            player = by.group(1).strip() or player
        days = DATE_RE.findall(page_body)
        day = days[-1] if days else ""
        slug_tail = url.rstrip("/").rsplit("/", 1)[-1]
        found.append(
            {
                "leader": YELLOW,
                "kind": "web",
                "player": player,
                "title": title or slug_tail,
                "subtitle": "Public OnePieceDB list" + (f" · {day}" if day else ""),
                "source_url": url,
                "slug": gen.slugify(f"opdb-{slug_tail}")[:70],
                "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                "cards": main_n,
                "date": day or "",
            }
        )
        print("opdb keep", player, day, flush=True)
        time.sleep(0.12)
    return found


def youtube_items(gen, comm, commsrc) -> list[dict]:
    queries = [
        "OP13-100 Jewelry Bonney decklist OP17",
        "Yellow Bonney OP13-100 decklist 4x OP17",
        "site:youtube.com OP13-100 Bonney decklist",
    ]
    found: list[dict] = []
    seen: set[str] = set()
    for q in queries:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
        try:
            body = fetch(url, timeout=14)
        except Exception as exc:  # noqa: BLE001
            print("ddg fail", q, exc, flush=True)
            continue
        print("ddg", q, "chars", len(body), flush=True)
        hrefs = re.findall(r'uddg=([^&"]+)', body)
        hrefs = [urllib.parse.unquote(h) for h in hrefs]
        for href in hrefs[:8]:
            if "youtube.com" not in href and "youtu.be" not in href:
                continue
            vid = ""
            m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{8,})", href)
            if m:
                vid = m.group(1)
            watch = f"https://www.youtube.com/watch?v={vid}" if vid else href
            try:
                desc = fetch(f"https://r.jina.ai/{watch}", timeout=18)
            except Exception as exc:  # noqa: BLE001
                print("yt fail", watch, exc, flush=True)
                continue
            counts = comm.parse_raw(desc)
            if counts.get(YELLOW) != 1:
                continue
            main_n = sum(n for cid, n in counts.items() if cid != YELLOW)
            if main_n != 50 or not has_op17(counts) or any(cid in gen.BANNED_CARDS for cid in counts):
                continue
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            item = {
                "leader": YELLOW,
                "kind": "youtube",
                "player": "YouTube",
                "title": f"Yellow Bonney - YouTube {vid or 'list'}",
                "subtitle": "YouTube description list",
                "source_url": watch,
                "slug": gen.slugify(f"yt-yellow-bonney-{vid or watch}")[:70],
                "raw": raw,
                "cards": main_n,
            }
            commsrc.record(found, item, seen)
            time.sleep(0.12)
        time.sleep(0.15)
    return found


def rebuild_analysis(gen, ana) -> None:
    cache = gen.load_card_cache()
    leader = next(L for L in gen.LEADERS if L["id"] == YELLOW)
    decks = []
    for path in sorted((gen.ROOT / leader["dir"]).glob("*.html")):
        parsed = ana.parse_deck(path, YELLOW)
        if parsed and not any(cid in gen.BANNED_CARDS for cid in parsed):
            decks.append(parsed)
    if not decks:
        print(YELLOW, "no decks for consensus")
        return
    picks = ana.consensus_list(decks)
    print(YELLOW, "consensus from", len(decks), "lists")
    grouped, totals = ana.grouped_from_picks(leader, picks, cache)
    text_deck = gen.render_text_deck(grouped, cache, ["Leader", "Characters", "Events", "Stages"], totals)
    op17_n = sum(1 for d in decks if ana._has_op17(d))
    block = ana.analysis_block(leader, len(decks), ana.TAKES[YELLOW], text_deck, op17_n)
    page_path = gen.ROOT / leader["page"]
    page = ana.inject(page_path.read_text(), block)
    page = ana.ensure_popup_js(page)
    if "/js/site.js" not in page:
        page = page.replace("</body>", '  <script src="/js/site.js?v=sim-copy"></script>\n</body>')
    page_path.write_text(page)
    cons_path = gen.ROOT / "data/consensus-decks.json"
    cons = json.loads(cons_path.read_text()) if cons_path.exists() else {}
    cons[YELLOW] = {
        "lists": len(decks),
        "cards": [{"id": cid, "count": count, "rate": round(rate, 3)} for cid, count, rate in picks],
    }
    cons_path.write_text(json.dumps(cons, indent=2) + "\n")


def list_count() -> int:
    from pathlib import Path

    d = Path("/workspace/decklists/yellow-bonney")
    if not d.exists():
        return 0
    return len(list(d.glob("*.html")))


def main() -> None:
    gen = load("genlists", "/workspace/scripts/generate-tournament-lists.py")
    comm = load("commlists", "/workspace/scripts/add-community-lists.py")
    commsrc = load("commsrc", "/workspace/scripts/scrape-community-sources.py")
    more = load("morelists", "/workspace/scripts/add-more-tournament-lists.py")
    ana = load("analysis", "/workspace/scripts/add-leader-analysis.py")
    up = load("upgrade", "/workspace/scripts/upgrade-public-pages.py")
    seo = load("seo", "/workspace/scripts/generate-seo-pages.py")

    print("=== Yellow Bonney hub ===", flush=True)
    write_hub(gen)

    found: list[dict] = []
    seen: set[str] = set()
    print("=== OPDeckGuide ===", flush=True)
    for item in opdeck_items(gen, comm):
        commsrc.record(found, item, seen)
    print("=== OnePieceDB ===", flush=True)
    for item in opdb_items(gen, comm):
        commsrc.record(found, item, seen)

    print("=== write community lists ===", flush=True)
    commsrc.write_lists(found)
    print("community hosted", list_count(), flush=True)

    if list_count() < TARGET:
        print("=== YouTube / public pages ===", flush=True)
        extra = youtube_items(gen, comm, commsrc)
        commsrc.write_lists(extra)

    if list_count() < TARGET:
        need = TARGET - list_count()
        print("=== Limitless OP17-splash lists need", need, "===" , flush=True)
        index = more.load_index()
        index = more.fetch_more(
            index,
            pages=30,
            only_ids={YELLOW},
            extra_limit=need,
            per_event=3,
            since="2026-08-01",
            require_op17=True,
        )
        more.save_index(index)
        more.rebuild_hubs(index, only_ids={YELLOW})

    hosted = list_count()
    print("hosted yellow bonney lists", hosted, flush=True)
    if hosted < TARGET:
        raise SystemExit(f"wanted {TARGET} yellow Bonney OP17 lists, hosted {hosted}")

    print("=== consensus ===", flush=True)
    rebuild_analysis(gen, ana)

    print("=== homepage / leaders / sitemap / guides ===", flush=True)
    more.rewrite_sitemap()
    up.patch_home()
    up.patch_op17()
    seo.main()
    seofix = load("seofix", "/workspace/scripts/enhance-seo.py")
    seofix.main()
    buy = load("tcgbuy", "/workspace/scripts/add-tcgplayer-buy.py")
    buy.main()
    print("yellow bonney ingest done", flush=True)


if __name__ == "__main__":
    main()
