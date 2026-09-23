#!/usr/bin/env python3
"""Add a self-canonical to every public HTML page that is missing one.

Google Search Console flagged "Duplicate without user-selected canonical".
Recent ingest pages were written without a <link rel="canonical">, so Google
could not tell which URL to index. This writes an absolute https canonical
to https://onepiecedecklists.com/{path} and an index,follow robots tag when
the page is not already noindex. Does not change existing canonicals.
"""

from __future__ import annotations

import html
import importlib.util
import re
from pathlib import Path

ROOT = Path("/workspace")
SKIP = {".git", "scripts", "node_modules", "discord-bot", "ballkeep"}
CANON_RE = re.compile(r'<link\s+rel=["\']canonical["\']', re.I)
DESC_RE = re.compile(r'(<meta\s+name=["\']description["\'][^>]*>)', re.I)
TITLE_RE = re.compile(r"(</title>)", re.I)
ROBOTS_RE = re.compile(r'<meta\s+name=["\']robots["\']', re.I)
NOINDEX_RE = re.compile(r"noindex", re.I)


def load_seo():
    spec = importlib.util.spec_from_file_location("seo_common", "/workspace/scripts/seo_common.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def public_html() -> list[Path]:
    out = []
    for path in ROOT.rglob("*.html"):
        if any(part in path.parts for part in SKIP):
            continue
        out.append(path)
    return out


def inject(path: Path, seo) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(ROOT).as_posix()
    url = seo.canonical_url(rel)
    tag = f'  <link rel="canonical" href="{html.escape(url, quote=True)}" />\n'
    changed = False
    if not CANON_RE.search(text):
        if DESC_RE.search(text):
            text = DESC_RE.sub(r"\1\n" + tag.rstrip("\n"), text, count=1)
        elif TITLE_RE.search(text):
            text = TITLE_RE.sub(r"\1\n" + tag.rstrip("\n"), text, count=1)
        else:
            text = text.replace("<head>", "<head>\n" + tag.rstrip("\n"), 1)
        changed = True
    if not ROBOTS_RE.search(text) and not NOINDEX_RE.search(text[:2500]):
        robots = (
            '  <meta name="robots" content="index, follow, max-image-preview:large, '
            'max-snippet:-1, max-video-preview:-1" />\n'
        )
        if CANON_RE.search(text):
            text = CANON_RE.sub(lambda m: m.group(0), text, count=1)
            text = re.sub(
                r'(<link\s+rel=["\']canonical["\'][^>]*>)',
                r"\1\n" + robots.rstrip("\n"),
                text,
                count=1,
                flags=re.I,
            )
        else:
            text = text.replace("</title>", "</title>\n" + robots.rstrip("\n"), 1)
        changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main() -> None:
    seo = load_seo()
    paths = public_html()
    n = 0
    for path in paths:
        if inject(path, seo):
            n += 1
    print("canonicals added", n, "of", len(paths), flush=True)


if __name__ == "__main__":
    main()
