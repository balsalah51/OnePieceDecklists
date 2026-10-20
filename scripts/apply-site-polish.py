#!/usr/bin/env python3
"""Point leader art at local files, group the nav, and hide placeholder events."""

from __future__ import annotations

import importlib.util
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
SKIP = {".git", "scripts", "node_modules", "ballkeep", "discord-bot"}
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"
CDN_RE = re.compile(
    r"https://limitlesstcg\.nyc3\.cdn\.digitaloceanspaces\.com/one-piece/"
    r"([A-Za-z0-9]+)/([A-Za-z0-9]+-\d+(?:_p\d+)?)_EN\.webp"
)
NAV_RE = re.compile(r"[ \t]*<nav aria-label=\"Primary\">.*?</nav>", re.S)
LI_RE = re.compile(r"[ \t]*<li\b[^>]*>.*?</li>\n?", re.S)
TEST_HREF_RE = re.compile(r"tournoi-test|test-tournament", re.I)
CSS_RE = re.compile(r'href="/css/site\.css(?:\?[^"]*)?"')
JS_RE = re.compile(r'src="/js/site\.js(?:\?[^"]*)?"')

spec = importlib.util.spec_from_file_location("genlists", ROOT / "scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
sspec = importlib.util.spec_from_file_location("seocommon", ROOT / "scripts/seo_common.py")
seo = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(seo)

LEADER_IDS = {leader["id"] for leader in gen.LEADERS}


def remote_url(cid: str) -> str:
    set_code = cid.split("-")[0]
    if set_code in {"EB05", "OP18"}:
        return f"https://cards.oplaytcg.com/{set_code}/en/{cid}.webp"
    return (
        "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/"
        f"{set_code}/{cid}_EN.webp"
    )


def download_one(cid: str) -> tuple[str, str]:
    set_code = cid.split("-")[0]
    dest = ROOT / "img" / "cards" / set_code / f"{cid}.webp"
    if dest.exists() and dest.stat().st_size > 800:
        return cid, "exists"
    req = urllib.request.Request(remote_url(cid), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read()
    except Exception as exc:  # noqa: BLE001 - report and keep the remote URL
        return cid, f"fail {exc}"
    if len(data) < 800 or data[:4] == b"<htm" or data[:1] == b"<":
        return cid, "not-an-image"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return cid, "ok"


def download_leaders() -> None:
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(download_one, cid) for cid in sorted(LEADER_IDS)]
        for future in as_completed(futures):
            cid, status = future.result()
            print(f"image {cid} {status}")
            if status in {"ok", "exists"}:
                ok += 1
    print(f"leader images ready {ok}/{len(LEADER_IDS)}")


def current_for(path: Path) -> tuple[str | None, bool]:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return None, True
    if rel.startswith("shop/"):
        return "shop", False
    exact = {
        "tier-list.html": "tier",
        "extra-grand-battle.html": "egb",
        "recent.html": "recent",
        "format.html": "format",
        "eb05-lists.html": "eb05-lists",
        "eb05-spoilers.html": "eb05",
        "op18-spoilers.html": "op18",
        "guides/weekly-meta.html": "weekly",
        "guides/matchups.html": "matchups",
        "guides/index.html": "guides",
        "search.html": "search",
        "decklists/op17.html": "leaders",
    }
    if rel in exact:
        return exact[rel], False
    if rel.startswith("guides/"):
        return "guides", False
    return None, False


def local_leader_url(set_code: str, cid: str, absolute: bool) -> str | None:
    base = cid.split("_")[0]
    if base not in LEADER_IDS:
        return None
    dest = ROOT / "img" / "cards" / set_code / f"{base}.webp"
    if not dest.exists():
        return None
    rel = f"/img/cards/{set_code}/{base}.webp"
    return (SITE + rel) if absolute else rel


def rewrite_images(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        window = text[max(0, match.start() - 16) : match.start()]
        absolute = not window.rstrip().endswith('src="')
        url = local_leader_url(match.group(1), match.group(2), absolute)
        return url or match.group(0)

    return CDN_RE.sub(repl, text)


def strip_test_items(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        if TEST_HREF_RE.search(match.group(0)):
            return ""
        return match.group(0)

    return LI_RE.sub(repl, text)


def noindex_if_test(path: Path, text: str) -> str:
    if not TEST_HREF_RE.search(path.as_posix()):
        return text
    if 'name="robots"' in text:
        return re.sub(
            r'<meta name="robots" content="[^"]*"\s*/>',
            '<meta name="robots" content="noindex, nofollow" />',
            text,
            count=1,
        )
    return text.replace(
        "<meta charset=\"utf-8\" />",
        "<meta charset=\"utf-8\" />\n  <meta name=\"robots\" content=\"noindex, nofollow\" />",
        1,
    )


def polish_html(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    original = text
    current, home = current_for(path)
    if NAV_RE.search(text):
        text = NAV_RE.sub(
            seo.primary_nav_html(current=current, home=home).strip("\n"),
            text,
            count=1,
        )
    text = CSS_RE.sub(f'href="/css/site.css?v={seo.CSS_VER}"', text)
    text = JS_RE.sub(f'src="/js/site.js?v={seo.JS_VER}"', text)
    text = rewrite_images(text)
    text = strip_test_items(text)
    text = noindex_if_test(path, text)
    if text != original:
        path.write_text(text)
        return True
    return False


def polish_sitemap() -> None:
    path = ROOT / "sitemap-lists.xml"
    lines = [
        line
        for line in path.read_text().splitlines(True)
        if not TEST_HREF_RE.search(line)
    ]
    path.write_text("".join(lines))
    core = ROOT / "sitemap-core.xml"
    text = core.read_text()
    for loc in (
        "https://onepiecedecklists.com/guides/weekly-meta.html",
        "https://onepiecedecklists.com/guides/matchups.html",
    ):
        if loc not in text:
            text = text.replace(
                "  <url><loc>https://onepiecedecklists.com/guides/op17-mihawk-matchups.html</loc><lastmod>2026-09-16</lastmod></url>\n",
                "  <url><loc>https://onepiecedecklists.com/guides/op17-mihawk-matchups.html</loc><lastmod>2026-09-16</lastmod></url>\n"
                f"  <url><loc>{loc}</loc><lastmod>2026-10-18</lastmod></url>\n",
            )
    core.write_text(text)


def main() -> None:
    download_leaders()
    changed = 0
    scanned = 0
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP for part in path.parts):
            continue
        scanned += 1
        if polish_html(path):
            changed += 1
    polish_sitemap()
    print(f"html scanned {scanned} changed {changed}")


if __name__ == "__main__":
    main()
