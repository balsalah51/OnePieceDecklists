#!/usr/bin/env python3
"""Mark navigation and commerce links so they do not open AdSense vignettes.

Google's supported opt-out is data-google-vignette="false" on the anchor.
https://support.google.com/adsense/answer/17016693
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTR = ' data-google-vignette="false"'
SKIP_DIRS = {".git", "ballkeep", "node_modules"}
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "source", "track", "wbr",
}
ANCHOR_CLASSES = {
    "events-banner",
    "home-big",
    "home-splash-card",
    "shop-buy",
    "shop-photo-link",
    "recent-all-link",
    "buy-tcg",
    "buy-tcg-inline",
    "brand",
    "discord",
}
REGION_CLASSES = {"crumb", "related-links", "section-title", "home-big3"}
REGION_TAGS = {"nav", "footer", "header"}
TOKEN = re.compile(r"<(/?)([a-zA-Z][\w:-]*)([^>]*)>", re.S)
CLASS_RE = re.compile(r"""class\s*=\s*["']([^"']*)["']""", re.I)


def class_list(attrs: str) -> set[str]:
    match = CLASS_RE.search(attrs)
    if not match:
        return set()
    return set(match.group(1).split())


def stamp_html(html: str) -> str:
    out: list[str] = []
    pos = 0
    region_depth = 0
    stack: list[bool] = []
    for match in TOKEN.finditer(html):
        out.append(html[pos:match.start()])
        slash, name, attrs = match.group(1), match.group(2).lower(), match.group(3)
        raw = match.group(0)
        self_closing = attrs.rstrip().endswith("/") or name in VOID
        if slash:
            if stack:
                if stack.pop():
                    region_depth -= 1
            out.append(raw)
        else:
            is_region = name in REGION_TAGS or bool(class_list(attrs) & REGION_CLASSES)
            if (
                name == "a"
                and "data-google-vignette" not in raw
                and (region_depth > 0 or bool(class_list(attrs) & ANCHOR_CLASSES))
            ):
                if raw.endswith("/>"):
                    raw = raw[:-2] + ATTR + " />"
                else:
                    raw = raw[:-1] + ATTR + ">"
            if not self_closing:
                stack.append(is_region)
                if is_region:
                    region_depth += 1
            out.append(raw)
        pos = match.end()
    out.append(html[pos:])
    return "".join(out)


def fix_alias_redirect(html: str) -> str:
    html = re.sub(r'\s*<meta name="google-adsense-account"[^>]*>\s*', "\n", html)
    html = re.sub(
        r'\s*<script async src="https://pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js[^"]*" crossorigin="anonymous"></script>\s*',
        "\n",
        html,
    )
    html = html.replace(
        'href="https://onepiecedecklists.com/decklists/uy-nami.html"',
        'href="https://onepiecedecklists.com/decklists/nami.html"',
    )
    html = html.replace(
        'content="https://onepiecedecklists.com/decklists/uy-nami.html"',
        'content="https://onepiecedecklists.com/decklists/nami.html"',
    )
    html = re.sub(
        r'<meta name="robots" content="[^"]*"\s*/?>',
        '<meta name="robots" content="noindex, follow" />',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta name="googlebot" content="[^"]*"\s*/?>',
        '<meta name="googlebot" content="noindex, follow" />',
        html,
        count=1,
    )
    html = html.replace(
        'src="/js/site.js?v=home-smooth"',
        'src="/js/site.js?v=nav-groups2"',
    )
    return html


def bump_site_js(html: str) -> str:
    return re.sub(
        r'src="/js/site\.js(?:\?[^"]*)?"',
        'src="/js/site.js?v=nav-groups2"',
        html,
    )


def main() -> None:
    """Add the vignette opt-out only. Do not rewrite the site.js cache key."""
    changed = 0
    files = 0
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files += 1
        original = path.read_text(encoding="utf-8")
        updated = stamp_html(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"stamped {changed} of {files} html files")


if __name__ == "__main__":
    main()
