#!/usr/bin/env python3
"""Pull the official OP18 numbered list from Limitless into data/op18-cards.json."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/workspace")
OUT = ROOT / "data/op18-cards.json"
UA = "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"
RARITY = {
    "L": "Leader",
    "C": "Common",
    "UC": "Uncommon",
    "R": "Rare",
    "SR": "Super Rare",
    "SEC": "Secret Rare",
    "SP": "Special",
    "TR": "Treasure Rare",
}
NOTES = {
    "OP18-015": "Official English name is Eyelashes. The Japanese card name is マツゲ.",
    "OP18-065": "God's Knights Super Parallel, the 4th-anniversary treatment.",
    "OP18-093": "Official text: you may have any number of this card in your deck.",
    "OP18-119": "Yoshitaka Amano drew a parallel and a foil-stamped parallel.",
}


def fetch_one(n: int) -> dict | None:
    cid = f"OP18-{n:03d}"
    url = f"https://onepiece.limitlesstcg.com/api/cards/{cid}"
    last = None
    for attempt in range(4):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            if not raw.strip().startswith(b"{"):
                last = ValueError(f"non-json {cid} {raw[:80]!r}")
                time.sleep(0.25 * (attempt + 1))
                continue
            data = json.loads(raw)
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            last = exc
            time.sleep(0.25 * (attempt + 1))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.25 * (attempt + 1))
    else:
        print("skip", cid, last)
        return None
    colors = [p.strip().title() for p in str(data.get("color") or "").split("/") if p.strip()]
    types = [p.strip() for p in str(data.get("type") or "").split("/") if p.strip()]
    counter = data.get("counter")
    effect = " ".join(p.strip() for p in (data.get("effect") or "", data.get("trigger") or "") if p and p.strip())
    kind = (data.get("category") or "character").lower()
    if kind == "leader":
        kind = "leader"
    return {
        "id": data.get("card_id") or cid,
        "name": data.get("name") or cid,
        "aliases": "",
        "kind": kind,
        "rarity": RARITY.get((data.get("rarity") or "").upper(), data.get("rarity") or ""),
        "colors": colors,
        "cost": str(data["cost"]) if data.get("cost") is not None else "",
        "power": str(data["power"]) if data.get("power") is not None else "",
        "life": str(data["life"]) if data.get("life") is not None else "",
        "counter": f"+{counter}" if counter else "",
        "attribute": (data.get("attribute") or "").title(),
        "types": types,
        "effect": effect or "No effect.",
        "note": NOTES.get(cid, ""),
        "image": True,
        "category": (data.get("category") or "Character").title(),
        "color": "/".join(colors),
        "source": f"https://onepiece.limitlesstcg.com/cards/{cid}",
    }


def main() -> None:
    cards: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(fetch_one, n): n for n in range(1, 120)}
        for fut in as_completed(futs):
            card = fut.result()
            if card:
                cards[card["id"]] = card
    ordered = [cards[cid] for cid in sorted(cards, key=lambda c: int(c.split("-")[1]))]
    OUT.write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n")
    print("op18 cards", len(ordered), "leaders", sum(1 for c in ordered if c["kind"] == "leader"))
    for card in ordered:
        if card["kind"] == "leader":
            print(" ", card["id"], card["name"], "/".join(card["colors"]))


if __name__ == "__main__":
    main()
