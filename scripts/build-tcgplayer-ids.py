#!/usr/bin/env python3
"""Fetch Limitless TCGplayer product IDs and write js/tcgplayer-ids.js.

Does not wipe deck pages. Does not run generate-tournament-lists.main().
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/workspace")
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"
ID_RE = re.compile(r"(?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3}")


def load_cache() -> dict:
    path = ROOT / "data/card-cache.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def deck_ids() -> set[str]:
    found: set[str] = set()
    deck = ROOT / "decklists"
    if not deck.exists():
        return found
    for path in deck.rglob("*.html"):
        found.update(ID_RE.findall(path.read_text()))
    return found


def fetch_one(cid: str) -> tuple[str, int | None]:
    req = urllib.request.Request(
        f"https://onepiece.limitlesstcg.com/api/cards/{cid}",
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return cid, None
    pid = data.get("tcgplayer_id")
    try:
        return cid, int(pid) if pid else None
    except (TypeError, ValueError):
        return cid, None


def write_ids_js(ids: dict[str, int]) -> None:
    items = ",\n".join(f'  "{cid}": {pid}' for cid, pid in sorted(ids.items()))
    (ROOT / "js/tcgplayer-ids.js").write_text(
        "window.OPDL_TCGPLAYER_IDS = {\n" + items + "\n};\n"
    )
    (ROOT / "data/tcgplayer-ids.json").write_text(json.dumps(ids, indent=2, sort_keys=True) + "\n")


def main() -> None:
    cache = load_cache()
    wanted = set(cache) | deck_ids()
    ids: dict[str, int] = {}
    extra_path = ROOT / "data/tcgplayer-ids.json"
    if extra_path.exists():
        for cid, pid in json.loads(extra_path.read_text()).items():
            try:
                ids[cid] = int(pid)
            except (TypeError, ValueError):
                pass
    missing = sorted(cid for cid in wanted if cid not in ids)
    print("known", len(ids), "fetch", len(missing), "wanted", len(wanted))
    if missing:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futs = {pool.submit(fetch_one, cid): cid for cid in missing}
            for i, fut in enumerate(as_completed(futs), 1):
                cid, pid = fut.result()
                if pid:
                    ids[cid] = pid
                    meta = cache.get(cid)
                    if isinstance(meta, dict):
                        meta["tcgplayer_id"] = pid
                if i % 50 == 0 or i == len(missing):
                    print("fetched", i, "/", len(missing), "have", len(ids))
        (ROOT / "data/card-cache.json").write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")
    write_ids_js(ids)
    print("tcgplayer ids", len(ids))


if __name__ == "__main__":
    main()
