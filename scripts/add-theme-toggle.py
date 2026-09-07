#!/usr/bin/env python3
"""Add the light/dark theme toggle and cookie boot script to public HTML.

Does not wipe list pages. Safe to re-run. Skips ballkeep and generator-only dirs.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path("/workspace")
SKIP_PARTS = {".git", "scripts", "node_modules", "discord-bot", "ballkeep"}
SKIP_FILES: set[str] = set()

spec = importlib.util.spec_from_file_location("seocommon", ROOT / "scripts/seo_common.py")
seo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seo)


def public_html() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        if any(part in p.parts for part in SKIP_PARTS):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP_FILES:
            continue
        out.append(p)
    return out


def main() -> None:
    changed = 0
    missing_toggle = 0
    missing_boot = 0
    for path in public_html():
        orig = path.read_text()
        text = seo.apply_theme_chrome(orig)
        if 'id="opdl-theme-boot"' not in text:
            missing_boot += 1
        if "data-theme-set" not in text:
            missing_toggle += 1
        if text != orig:
            path.write_text(text)
            changed += 1
    print("theme chrome patched", changed, "pages")
    print("missing boot", missing_boot, "missing toggle", missing_toggle)


if __name__ == "__main__":
    main()
