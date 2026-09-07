#!/usr/bin/env python3
"""Build official TCGplayer Mass Entry names from the public catalog dump."""

from __future__ import annotations

import json
import re
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("/workspace")
OUT_JSON = ROOT / "data/tcgplayer-names.json"
OUT_JS = ROOT / "js/tcgplayer-names.js"
CATEGORY_ID = 68
UA = {"User-Agent": "OnePieceDecklists/1.0 (+https://onepiecedecklists.com)"}

VARIANT_RE = re.compile(
    r"alternate art|parallel|manga|wanted poster|pandaman|jolly roger|"
    r"reprint|\(tr\)|tournament pack|event pack|illustration box|"
    r"pre-release|participant|sealed battle|release event|"
    r"heroines battle|nami deck|\(sp\)|special art|full art|judge pack",
    re.I,
)
TRAILING_VARIANT_RE = re.compile(
    r"\s+\((?:Alternate Art|Parallel|Manga|Wanted Poster|Pandaman Art|"
    r"Special|TR|Jolly Roger Foil|Reprint|SP|Full Art)\)\s*$",
    re.I,
)

from tcgplayer_links import tcg_set_code


def http_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def fetch_products() -> list[dict]:
    groups = http_json(f"https://tcgcsv.com/tcgplayer/{CATEGORY_ID}/groups")["results"]

    def one(group: dict) -> list[dict]:
        data = http_json(f"https://tcgcsv.com/tcgplayer/{CATEGORY_ID}/{group['groupId']}/products")
        out = []
        for product in data.get("results") or []:
            ext = {row.get("name"): row.get("value") for row in (product.get("extendedData") or [])}
            out.append(
                {
                    "name": product.get("name") or "",
                    "set": group.get("abbreviation") or "",
                    "number": str(ext.get("Number") or ext.get("number") or "").strip().upper(),
                }
            )
        return out

    products: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(one, group) for group in groups]
        for fut in as_completed(futs):
            products.extend(fut.result())
    return products


def rank(product: dict, cid: str, set_code: str) -> tuple:
    name = product["name"]
    variant = 1 if VARIANT_RE.search(name) else 0
    set_match = 0 if product["set"] == set_code else 1
    promo_match = 0 if cid.startswith("P-") and product["set"] == "OP-PR" else 1
    return (variant, set_match, promo_match, len(name), name)


def pick_name(cid: str, rows: list[dict]) -> str | None:
    if not rows:
        return None
    set_code = tcg_set_code(cid)
    best = sorted(rows, key=lambda row: rank(row, cid, set_code))[0]
    return TRAILING_VARIANT_RE.sub("", best["name"]).strip() or None


def build_names(products: list[dict] | None = None) -> dict[str, str]:
    if products is None:
        products = fetch_products()
    by_number: dict[str, list[dict]] = defaultdict(list)
    for product in products:
        number = product.get("number") or ""
        if number:
            by_number[number].append(product)
    cache = json.loads((ROOT / "data/card-cache.json").read_text())
    names: dict[str, str] = {}
    for cid, meta in cache.items():
        if not isinstance(meta, dict):
            continue
        cid = str(cid).strip().upper()
        official = pick_name(cid, by_number.get(cid, []))
        if official:
            names[cid] = official
    return names


def write_names(names: dict[str, str]) -> None:
    OUT_JSON.write_text(json.dumps(names, indent=2, sort_keys=True) + "\n")
    body = json.dumps(names, indent=2, sort_keys=True)
    OUT_JS.write_text("window.OPDL_TCGPLAYER_NAMES = " + body + ";\n")


def main() -> None:
    names = build_names()
    write_names(names)
    print(f"wrote {len(names)} catalog names")


if __name__ == "__main__":
    main()
