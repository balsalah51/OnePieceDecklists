"""Build 128px One Piece face emojis for each site leader.

Primary source: crop the portrait from the Limitless leader card used on the site.
Optional: copy a matching custom emoji from another Discord the bot is already in,
or pull a uniquely named face from the public emoji.gg Discord catalog.
"""

from __future__ import annotations

import io
import json
import re
import urllib.request
from pathlib import Path

from .config import ASSETS_DIR, LEADERS, emoji_name

UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"
EMOJI_SIZE = 128


def http_bytes(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def crop_face(image_bytes: bytes, size: int = EMOJI_SIZE) -> bytes:
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size
    # OPTCG leader cards: skip life/power tabs in the top corners and keep the portrait.
    art_left = int(w * 0.14)
    art_right = int(w * 0.74)
    art_top = int(h * 0.11)
    art_bottom = int(h * 0.46)
    art_w = art_right - art_left
    art_h = art_bottom - art_top
    side = int(min(art_w, art_h) * 0.92)
    cx = art_left + int(art_w * 0.46)
    cy = art_top + int(art_h * 0.40)
    left = max(0, cx - side // 2)
    top = max(0, cy - side // 2)
    right = min(w, left + side)
    bottom = min(h, top + side)
    left = max(0, right - side)
    top = max(0, bottom - side)
    face = img.crop((left, top, right, bottom)).resize((size, size), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    face.save(out, format="PNG", optimize=True)
    return out.getvalue()


def asset_path(leader: dict) -> Path:
    return ASSETS_DIR / f"{emoji_name(leader)}.png"


def ensure_face_png(leader: dict, force: bool = False) -> Path:
    path = asset_path(leader)
    if path.exists() and path.stat().st_size > 0 and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = http_bytes(leader["image"])
    path.write_bytes(crop_face(raw))
    return path


def ensure_all_faces(force: bool = False) -> list[Path]:
    return [ensure_face_png(leader, force=force) for leader in LEADERS]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def match_catalog_emoji(leader: dict, catalog: list[dict]) -> dict | None:
    """Pick a catalog emoji only when the name uniquely matches this leader."""
    terms = [_norm(t) for t in leader.get("search") or [] if len(_norm(t)) >= 4]
    if not terms:
        return None
    hits = []
    for item in catalog:
        blob = _norm(f"{item.get('title') or ''} {item.get('slug') or ''}")
        if any(t in blob for t in terms):
            hits.append(item)
    # Skip ambiguous names (luffy/ace) unless the title is exact-ish.
    if len(hits) != 1:
        exact = []
        key = _norm(leader["short"])
        for item in hits:
            title = _norm(item.get("title") or "")
            if key and (title == key or title.endswith(key) or title.startswith(key)):
                exact.append(item)
        if len(exact) == 1:
            return exact[0]
        return None
    return hits[0]


def scrape_emoji_gg(limit: int | None = None) -> list[dict]:
    raw = http_bytes("https://emoji.gg/api")
    data = json.loads(raw)
    if not isinstance(data, list):
        return []
    if limit:
        return data[:limit]
    return data


def scraped_urls_for_leaders(catalog: list[dict] | None = None) -> dict[str, str]:
    catalog = catalog if catalog is not None else scrape_emoji_gg()
    found: dict[str, str] = {}
    for leader in LEADERS:
        hit = match_catalog_emoji(leader, catalog)
        if hit and hit.get("image"):
            found[leader["key"]] = hit["image"]
    return found


def main() -> None:
    paths = ensure_all_faces()
    for path in paths:
        print("wrote", path)
    try:
        catalog = scrape_emoji_gg()
        hits = scraped_urls_for_leaders(catalog)
        print("emoji.gg unique hits", len(hits), hits)
    except Exception as exc:  # noqa: BLE001
        print("emoji.gg scrape skipped:", exc)


if __name__ == "__main__":
    main()
