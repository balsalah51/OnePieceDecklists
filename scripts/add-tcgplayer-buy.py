#!/usr/bin/env python3
"""Add TCGplayer buy scripts to deck pages.

Does not wipe list pages. Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path("/workspace")


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    up = load("upgrade", str(ROOT / "scripts/upgrade-public-pages.py"))
    changed = 0
    skipped = (".git", "scripts", "node_modules", "shop", "discord-bot", "ballkeep")
    for path in ROOT.rglob("*.html"):
        if any(part in path.parts for part in skipped):
            continue
        text = path.read_text()
        new = up.patch_nav_and_assets(text)
        if new != text:
            path.write_text(new)
            changed += 1
    print("patched html", changed)


if __name__ == "__main__":
    main()
