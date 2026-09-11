#!/usr/bin/env python3
"""Scrape public X, YouTube, Limitless, and OnePieceDB pages for 50-card lists.

Only keeps complete NxSET-NNN lists. Does not invent cards from screenshots.
Does not wipe existing tournament pages.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

spec = importlib.util.spec_from_file_location("genlists", "/workspace/scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

cspec = importlib.util.spec_from_file_location("commlists", "/workspace/scripts/add-community-lists.py")
comm = importlib.util.module_from_spec(cspec)
cspec.loader.exec_module(comm)

mspec = importlib.util.spec_from_file_location("morelists", "/workspace/scripts/add-more-tournament-lists.py")
more = importlib.util.module_from_spec(mspec)
mspec.loader.exec_module(more)

ROOT = gen.ROOT
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com; public OPTCG list scrape)"
LINE_RE = comm.LINE_RE
TARGET_IDS = {L["id"]: L["key"] for L in gen.LEADERS}
OPDL_SLUGS = {
    "OP17-001": "edward-newgate-op17-001",
    "OP17-020": "shanks-op17-020",
    "OP17-039": "rocks-d-xebec-op17-039",
    "OP17-058": "kaido-op17-058",
    "OP17-079": "monkey-d-luffy-op17-079",
    "OP17-099": "charlotte-linlin-op17-099",
    "OP13-001": "monkey-d-luffy-op13-001",
    "OP11-041": "nami-op11-041",
    "OP14-020": "dracule-mihawk-op14-020",
    "OP16-001": "portgas-d-ace-op16-001",
    "OP15-058": "enel-op15-058",
    "OP11-062": "charlotte-katakuri-op11-062",
    "OP13-079": "imu-op13-079",
    "OP13-002": "portgas-d-ace-op13-002",
    "OP16-022": "monkey-d-luffy-op16-022",
    "OP16-080": "marshall-d-teach-op16-080",
    "OP12-061": "donquixote-rosinante-op12-061",
    "OP15-002": "lucy-op15-002",
    "OP16-079": "yamato-op16-079",
    "OP11-001": "koby-op11-001",
    "OP14-060": "donquixote-doflamingo-op14-060",
    "OP16-041": "buggy-op16-041",
    "OP16-060": "sengoku-op16-060",
    "OP11-040": "monkey-d-luffy-op11-040",
    "OP08-058": "charlotte-pudding-op08-058",
}
YOUTUBE_ID_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{8,})", re.I)
DECK_HREF_RE = re.compile(r'href="(https?://onepiecedb\.io/[^"]+)"')


def log(*args) -> None:
    print(*args, flush=True)


def fetch(url: str, timeout: int = 16) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, body
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def parse_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for n, cid in LINE_RE.findall(text or ""):
        cid = cid.upper()
        counts[cid] = counts.get(cid, 0) + int(n)
    return counts


def leader_of(counts: dict[str, int]) -> str | None:
    hits = [cid for cid in counts if cid in TARGET_IDS]
    if len(hits) == 1:
        return hits[0]
    for cid in hits:
        if counts[cid] == 1:
            return cid
    return None


def complete(counts: dict[str, int], leader_id: str) -> bool:
    if leader_id not in counts:
        return False
    total = sum(n for cid, n in counts.items() if cid != leader_id)
    if any(cid in gen.BANNED_CARDS for cid in counts):
        return False
    return 46 <= total <= 52


def slug_for(kind: str, player: str, title: str) -> str:
    return gen.slugify(f"{kind}-{player}-{title}")[:70]


def record(found: list[dict], item: dict, seen: set[str]) -> None:
    key = item["raw"]
    if key in seen:
        return
    seen.add(key)
    found.append(item)
    log("found", item["leader"], item["kind"], item["slug"], "cards", item["cards"])


def ddg(query: str) -> str:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    status, body = fetch(url, timeout=12)
    log("ddg", status, query[:60])
    return body


def scrape_youtube(found: list[dict], seen: set[str]) -> None:
    queries = [
        "UP Luffy OP11-040 decklist youtube",
        "Blue Purple Luffy OP11-040 decklist youtube OP17",
        "OP11-040 Monkey D Luffy decklist youtube",
        "Charlotte Pudding OP08-058 decklist youtube",
        "Purple Yellow Pudding OP08 decklist youtube",
        "OP17 Rocks Xebec OP17-039 decklist youtube",
        "OP17 Kaido OP17-058 decklist youtube",
        "OP17 Luffy OP17-079 decklist youtube",
        "OP17 Shanks OP17-020 decklist youtube",
        "OP17 Linlin OP17-099 decklist youtube",
        "OP17 Newgate OP17-001 decklist youtube",
        "OP16 Ace OP16-001 decklist youtube August 2026",
        "OP14 Mihawk decklist youtube August 2026",
        "OP16 Buggy OP16-041 decklist youtube",
        "OP16 Sengoku OP16-060 decklist youtube",
        "OP14 Doflamingo OP14-060 decklist youtube",
        "OP15 Lucy OP15-002 decklist youtube",
        "OP16 Blackbeard OP16-080 decklist youtube",
        "OP16 Yamato OP16-079 decklist youtube",
        "OP16 GB Luffy OP16-022 decklist youtube",
        "OP17 deck profile youtube August 2026",
    ]
    video_ids: list[str] = []
    for q in queries:
        body = ddg(q)
        for vid in YOUTUBE_ID_RE.findall(body):
            if vid not in video_ids:
                video_ids.append(vid)
        time.sleep(0.2)
    log("youtube ids", len(video_ids))
    for vid in video_ids[:36]:
        url = f"https://www.youtube.com/watch?v={vid}"
        status, body = fetch(f"https://r.jina.ai/{url}", timeout=20)
        counts = parse_counts(body)
        lid = leader_of(counts)
        log("yt", status, vid, "lines", len(counts), lid or "-")
        if not lid or not complete(counts, lid):
            time.sleep(0.15)
            continue
        title = f"{TARGET_IDS[lid].replace('-', ' ').title()} YouTube list"
        m = re.search(r"(?im)^Title:\s*(.+)$", body)
        if m:
            title = m.group(1).strip()[:90]
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        record(
            found,
            {
                "leader": lid,
                "kind": "youtube",
                "player": "YouTube",
                "title": title,
                "subtitle": "YouTube deck profile from a public description",
                "source_url": url,
                "slug": slug_for("yt", "youtube", f"{TARGET_IDS[lid]}-{vid}"),
                "raw": raw,
                "cards": sum(n for cid, n in counts.items() if cid != lid),
            },
            seen,
        )
        time.sleep(0.15)


def scrape_opdl(found: list[dict], seen: set[str]) -> None:
    for lid, slug in OPDL_SLUGS.items():
        page = f"https://onepiecedb.io/category/leader/{slug}"
        status, body = fetch(f"https://r.jina.ai/{page}", timeout=20)
        log("opdl category", status, slug, "chars", len(body))
        hrefs = []
        for href in DECK_HREF_RE.findall(body):
            if "/category/" in href or "/card/" in href:
                continue
            if href not in hrefs:
                hrefs.append(href)
        # also accept relative paths rewritten by jina as markdown links
        for href in re.findall(r"https://onepiecedb\.io/[A-Za-z0-9_/?#.-]+", body):
            if any(x in href for x in ("/category/", "/card/", "/tag/")):
                continue
            if href not in hrefs:
                hrefs.append(href)
        counts = parse_counts(body)
        if complete(counts, lid):
            raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
            record(
                found,
                {
                    "leader": lid,
                    "kind": "web",
                    "player": "OnePieceDB",
                    "title": f"{TARGET_IDS[lid].replace('-', ' ').title()} - OnePieceDB",
                    "subtitle": "Public OnePieceDB leader page",
                    "source_url": page,
                    "slug": slug_for("opdl", "onepiecedb", TARGET_IDS[lid]),
                    "raw": raw,
                    "cards": sum(n for cid, n in counts.items() if cid != lid),
                },
                seen,
            )
        for href in hrefs[:8]:
            st, deck_body = fetch(f"https://r.jina.ai/{href}", timeout=18)
            deck_counts = parse_counts(deck_body)
            log("opdl deck", st, href, "lines", len(deck_counts))
            if not complete(deck_counts, lid):
                time.sleep(0.1)
                continue
            raw = " ".join(f"{n}x{cid}" for cid, n in deck_counts.items())
            record(
                found,
                {
                    "leader": lid,
                    "kind": "web",
                    "player": "OnePieceDB",
                    "title": f"{TARGET_IDS[lid].replace('-', ' ').title()} - OnePieceDB list",
                    "subtitle": "Public OnePieceDB deck page",
                    "source_url": href,
                    "slug": slug_for("opdl", "onepiecedb", href),
                    "raw": raw,
                    "cards": sum(n for cid, n in deck_counts.items() if cid != lid),
                },
                seen,
            )
            time.sleep(0.12)
        time.sleep(0.15)


def scrape_x(found: list[dict], seen: set[str]) -> None:
    xspec = importlib.util.spec_from_file_location("xlists", "/workspace/scripts/scrape-x-lists.py")
    xmod = importlib.util.module_from_spec(xspec)
    xspec.loader.exec_module(xmod)
    xmod.LEADERS = set(TARGET_IDS)
    xmod.main()
    log_path = ROOT / "data/x-search-log.json"
    if not log_path.exists():
        return
    data = json.loads(log_path.read_text())
    for item in data.get("complete_lists") or []:
        raw = item.get("raw") or ""
        counts = parse_counts(raw)
        lid = item.get("leader") or leader_of(counts)
        if lid not in TARGET_IDS or not complete(counts, lid):
            continue
        url = item.get("source") or item.get("url") or "https://x.com/"
        handle = item.get("handle") or "x"
        day = (item.get("date") or "")[:10]
        if day and day < "2026-09-04":
            log("skip old x list", handle, day)
            continue
        record(
            found,
            {
                "leader": lid,
                "kind": "x",
                "player": handle,
                "title": f"{TARGET_IDS[lid].replace('-', ' ').title()} - @{handle}",
                "subtitle": "List copied from a public X/Twitter post",
                "source_url": url if url.startswith("http") else f"https://x.com/{handle}",
                "slug": slug_for("x", handle, TARGET_IDS[lid] + raw[-12:]),
                "raw": " ".join(f"{n}x{cid}" for cid, n in counts.items()),
                "cards": sum(n for cid, n in counts.items() if cid != lid),
                "date": day,
            },
            seen,
        )


WEIRD_QUERIES = [
    "site:mabitcg.com OP17 decklist",
    "site:mabitcg.com UP Luffy OP11-040",
    "site:onepiecetopdecks.com OP17 decklist",
    "site:opmetagame.com OP11-040 decklist",
    "site:deltiasgaming.com Blue Purple Luffy decklist",
    "site:overlordtcgz1.blogspot.com OP11-040",
    "site:hikerukana.com OP11-040",
    "site:reddit.com/r/OnePieceTCG OP17 decklist 4xOP17",
    "egmanevents deckbuilder OP17 Rocks",
    "cardkaizoku OP17 Xebec decklist",
    "UP Luffy OP11-040 50 card list",
    "Blue Purple Luffy OP17 Otama decklist",
    "site:reddit.com/r/OnePieceTCG Charlotte Pudding OP08-058 decklist",
    "Charlotte Pudding OP08-058 50 card list",
]
PAGE_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:mabitcg\.com|onepiecetopdecks\.com|opmetagame\.com|"
    r"deltiasgaming\.com|overlordtcgz1\.blogspot\.com|hikerukana\.com|"
    r"reddit\.com/r/OnePieceTCG|deckbuilder\.egmanevents\.com|deckbuilder\.cardkaizoku\.com)"
    r"[^\s\"'<>]*",
    re.I,
)


def scrape_weird(found: list[dict], seen: set[str]) -> None:
    pages: list[str] = []
    for q in WEIRD_QUERIES:
        body = ddg(q)
        for href in PAGE_URL_RE.findall(body):
            href = href.rstrip(").,;]")
            if href not in pages:
                pages.append(href)
        time.sleep(0.2)
    log("weird pages", len(pages))
    for href in pages[:40]:
        status, body = fetch(f"https://r.jina.ai/{href}", timeout=20)
        counts = parse_counts(body)
        lid = leader_of(counts)
        log("weird", status, href[:80], "lines", len(counts), lid or "-")
        if not lid or not complete(counts, lid):
            time.sleep(0.12)
            continue
        raw = " ".join(f"{n}x{cid}" for cid, n in counts.items())
        host = urllib.parse.urlparse(href).netloc.replace("www.", "")
        record(
            found,
            {
                "leader": lid,
                "kind": "web",
                "player": host.split(".")[0].title(),
                "title": f"{TARGET_IDS[lid].replace('-', ' ').title()} - {host}",
                "subtitle": "Public web list from a community page",
                "source_url": href,
                "slug": slug_for("web", host, href),
                "raw": raw,
                "cards": sum(n for cid, n in counts.items() if cid != lid),
            },
            seen,
        )
        time.sleep(0.12)


UNIQUE_PAGE_HOSTS = {
    "optcg.gg",
    "www.optcg.gg",
    "tcg-portal.jp",
    "opdeckguide.com",
    "www.opdeckguide.com",
    "onepiecedb.io",
    "play.limitlesstcg.com",
    "mabitcg.com",
    "mercardop.jp",
    "cardkaizoku.com",
}


def source_host(url: str) -> str:
    if "://" not in (url or ""):
        return ""
    return (url.split("/")[2] or "").lower()


def existing_unique_urls(community: dict) -> set[str]:
    urls: set[str] = set()
    for rows in community.values():
        for row in rows or []:
            src = (row.get("source_url") or "").rstrip("/")
            if src and source_host(src) in UNIQUE_PAGE_HOSTS:
                urls.add(src)
    return urls


def write_lists(found: list[dict]) -> set[str]:
    if not found:
        return set()
    found.sort(
        key=lambda item: 0
        if any(cid.startswith("OP17-") for cid in comm.parse_raw(item["raw"]))
        else 1
    )
    needed = set()
    parsed = []
    for item in found:
        counts = comm.parse_raw(item["raw"])
        needed.update(counts)
        parsed.append((item, counts))
    cache = gen.ensure_cards(needed, gen.load_card_cache())
    index = more.load_index()
    community = {}
    comm_path = ROOT / "data/community-decks.json"
    if comm_path.exists():
        community = json.loads(comm_path.read_text())
    unique_urls = existing_unique_urls(community)
    touched = set()
    by_id = {L["id"]: L for L in gen.LEADERS}
    for item, counts in parsed:
        leader = by_id.get(item["leader"])
        if not leader:
            continue
        src = (item.get("source_url") or "").rstrip("/")
        if src and source_host(src) in UNIQUE_PAGE_HOSTS and src in unique_urls:
            log("exists url", src)
            continue
        out_dir = ROOT / leader["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{item['slug']}.html"
        if path.exists():
            log("exists", path)
            continue
        dl = comm.counts_to_decklist(counts, cache, leader["id"])
        entry = {
            "player": item["player"],
            "tournament_name": item["title"],
            "placing": None,
            "record": {},
            "date": item.get("date") or "",
            "decklist": dl,
            "source_url": item["source_url"],
            "kind": item["kind"],
            "title_override": item["title"],
            "subtitle": item["subtitle"],
            "forced_slug": item["slug"],
            "slug": item["slug"],
            "href": f"/{leader['dir']}/{item['slug']}.html",
        }
        page = gen.render_deck_page(leader, entry, cache)
        path.write_text(page)
        rows = community.setdefault(leader["id"], [])
        if not any(row.get("slug") == item["slug"] for row in rows):
            row = {
                "slug": item["slug"],
                "href": entry["href"],
                "title": item["title"],
                "subtitle": item.get("subtitle") or "",
                "source_url": item["source_url"],
                "kind": item["kind"],
            }
            if item.get("date"):
                row["date"] = item["date"]
            rows.append(row)
        if src and source_host(src) in UNIQUE_PAGE_HOSTS:
            unique_urls.add(src)
        touched.add(leader["id"])
        log("wrote", path)
    more.save_index(index)
    comm_path.write_text(json.dumps(community, indent=2, ensure_ascii=False) + "\n")
    if touched:
        more.rebuild_hubs(index, only_ids=touched)
    return touched


def main() -> None:
    found: list[dict] = []
    seen: set[str] = set()
    scrape_opdl(found, seen)
    scrape_youtube(found, seen)
    scrape_weird(found, seen)
    scrape_x(found, seen)
    (ROOT / "data/community-scrape-log.json").write_text(
        json.dumps({"found": found}, indent=2, ensure_ascii=False) + "\n"
    )
    log("complete community lists", len(found))
    write_lists(found)
    print("done")


if __name__ == "__main__":
    main()
