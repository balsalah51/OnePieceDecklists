#!/usr/bin/env python3
"""One leader URL scheme, plus accent-preserving slugs.

Canonical leader pages are /decklists/<key>.html and lists are
/decklists/<key>/<slug>.html. The six OP17 leaders move out of
/decklists/op17/<key>. Old URLs stay as HTML redirects (GitHub Pages
does not emit HTTP 301). _redirects and redirects.json list the same
pairs for a host that can send 301s.

Accented player names transliterate (José -> jose) instead of dropping
the letter (jos). Each old slug redirects to the new one.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
OP17_KEYS = (
    "edward-newgate",
    "shanks",
    "rocks-d-xebec",
    "kaido",
    "monkey-d-luffy",
    "charlotte-linlin",
)
TEXT_SUFFIXES = {".html", ".xml", ".json", ".py", ".js", ".css", ".md", ".txt"}
SKIP_DIRS = {".git", "img", "node_modules", ".venv", "__pycache__"}
H2_RE = re.compile(r"<h2>(.*?)</h2>", re.S)

spec = importlib.util.spec_from_file_location("genlists", ROOT / "scripts/generate-tournament-lists.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def old_slugify(text: str) -> str:
    s = gen.display_name(text).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:70] or "list"


def player_from(text: str) -> str:
    match = H2_RE.search(text)
    if not match:
        return ""
    h2 = html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
    if " - " not in h2:
        return ""
    return h2.split(" - ", 1)[0].strip()


def fix_stem(stem: str, page: str) -> str:
    player = player_from(page)
    if not player:
        return stem
    old = old_slugify(player)
    new = gen.slugify(player)
    if not old or old == new:
        return stem
    # Whole slug only. A substring swap turns an already-correct "mu" into "muu".
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(old)}(?![a-z0-9])")
    if not pattern.search(stem):
        return stem
    return pattern.sub(new, stem, count=1)


def destination(rel: str, page: str) -> str:
    path = Path(rel)
    parent = path.parent.as_posix()
    # Hub pages are decklists/op17/<key>.html. Path.parts keeps the suffix on the last piece.
    if parent == "decklists/op17" and path.stem in OP17_KEYS and path.suffix == ".html":
        return f"decklists/{path.stem}.html"
    if (
        len(path.parts) == 4
        and path.parts[0] == "decklists"
        and path.parts[1] == "op17"
        and path.parts[2] in OP17_KEYS
        and path.suffix == ".html"
    ):
        stem = fix_stem(path.stem, page)
        return f"decklists/{path.parts[2]}/{stem}.html"
    if parent.startswith("decklists/") and path.suffix == ".html" and len(path.parts) == 3:
        stem = fix_stem(path.stem, page)
        return f"{path.parts[0]}/{path.parts[1]}/{stem}.html"
    return rel


def stub(new_href: str) -> str:
    url = SITE + new_href
    target = json.dumps(new_href)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Moved</title>
  <link rel="canonical" href="{html.escape(url, quote=True)}" />
  <meta name="robots" content="noindex" />
  <meta http-equiv="refresh" content="0; url={html.escape(new_href, quote=True)}" />
  <script>location.replace({target});</script>
</head>
<body>
  <p>This page moved to <a href="{html.escape(new_href, quote=True)}">{html.escape(new_href)}</a>.</p>
</body>
</html>
"""


def text_files() -> list[Path]:
    out = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.name == "redirects.json":
            continue
        out.append(path)
    return out


def main() -> None:
    moves: list[tuple[str, str]] = []
    accents = 0
    for path in ROOT.joinpath("decklists").rglob("*.html"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.endswith(".html") and "Moved" in path.read_text()[:400] and 'http-equiv="refresh"' in path.read_text()[:800]:
            continue
        page = path.read_text(encoding="utf-8", errors="ignore")
        dest = destination(rel, page)
        if dest != rel:
            moves.append((rel, dest))
            if "op17/" not in rel or Path(rel).stem != Path(dest).stem:
                if Path(rel).stem != Path(dest).stem:
                    accents += 1
    # Resolve collisions.
    used: dict[str, str] = {}
    clean: list[tuple[str, str]] = []
    for old, new in moves:
        dest = new
        if dest in used and used[dest] != old:
            stem = Path(dest).stem
            n = 2
            while True:
                candidate = str(Path(dest).with_name(f"{stem}-{n}.html"))
                if candidate not in used:
                    dest = candidate
                    break
                n += 1
            print("collision", old, "->", dest)
        used[dest] = old
        clean.append((old, dest))
    moves = clean
    print("moves", len(moves), "accent renames", accents)

    repl = {}
    for old, dest in moves:
        repl["/" + old] = "/" + dest
        repl[old] = dest
    # Directory strings in generators ("dir": "decklists/shanks") are not a file move.
    for key in OP17_KEYS:
        repl.setdefault(f"/decklists/op17/{key}", f"/decklists/{key}")
        repl.setdefault(f"decklists/op17/{key}", f"decklists/{key}")
    ordered = sorted(repl, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(key) for key in ordered))
    replaced_files = 0
    for path in text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        new = pattern.sub(lambda match: repl[match.group(0)], text)
        if new != text:
            path.write_text(new)
            replaced_files += 1
    print("rewrote", replaced_files, "files")

    for old, dest in moves:
        src = ROOT / old
        target = ROOT / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            if target.exists():
                raise SystemExit(f"refusing to overwrite {target}")
            shutil.move(str(src), str(target))
        elif not target.exists():
            raise SystemExit(f"missing source and target for {old}")
        (ROOT / old).write_text(stub("/" + dest))

    existing = []
    redir_path = ROOT / "redirects.json"
    if redir_path.exists():
        existing = json.loads(redir_path.read_text())
    seen = {(row["from"], row["to"]) for row in existing}
    payload = list(existing)
    for old, dest in moves:
        pair = ("/" + old, "/" + dest)
        if pair in seen:
            continue
        seen.add(pair)
        payload.append({"from": pair[0], "to": pair[1], "status": 301})
    redir_path.write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# HTTP 301s for hosts that read _redirects (Cloudflare Pages, Netlify).",
        "# GitHub Pages ignores this file. The HTML stubs at the old paths are the fallback.",
    ]
    for row in payload:
        lines.append(f"{row['from']} {row['to']} 301")
    (ROOT / "_redirects").write_text("\n".join(lines) + "\n")
    print("wrote", len(payload), "redirects")


if __name__ == "__main__":
    main()
