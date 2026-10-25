#!/usr/bin/env python3
"""Write every hosted card that has no TCGplayer product id or catalog name.

Prints a short summary and a GitHub warning annotation. Exits 0 so a known
historical gap does not hide a scrape failure, and the annotation keeps the
gap on the workflow summary.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "scripts"))
import tcgplayer_links  # noqa: E402

LINE_RE = re.compile(
    r'<span class="qty">(\d+)x</span>\s*'
    r'<span class="card-title">(.*?)</span>\s*'
    r'<span class="muted card-id">([^<]+)</span>',
    re.S,
)
TAG_RE = re.compile(r"<[^>]+>")
OUT = ROOT / "data" / "tcgplayer-unmatched.json"


def cause(cid: str) -> str:
    prefix = cid.split("-", 1)[0]
    if cid.startswith("P-") or prefix == "PR":
        return "promo"
    if prefix.startswith("ST"):
        return "starter"
    if prefix.startswith(("OP", "EB", "PRB")):
        return "booster"
    return "other"


def main() -> None:
    ids = tcgplayer_links.load_ids()
    names = tcgplayer_links.load_catalog_names()
    cards: dict[str, dict] = {}
    for path in (ROOT / "decklists").rglob("*.html"):
        if len(path.relative_to(ROOT).parts) != 3:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Moved" in text[:300] and "http-equiv" in text[:800]:
            continue
        for qty, title, cid in LINE_RE.findall(text):
            cid = cid.strip().upper()
            if not cid:
                continue
            slot = cards.setdefault(
                cid,
                {
                    "id": cid,
                    "name": TAG_RE.sub("", title).strip(),
                    "pages": 0,
                    "qty_sample": int(qty),
                },
            )
            slot["pages"] += 1
    rows = []
    for cid, slot in cards.items():
        reasons = []
        if cid not in ids:
            reasons.append("no_product_id")
        if cid not in names:
            reasons.append("no_catalog_name")
        if not reasons:
            continue
        slot["reasons"] = reasons
        slot["cause"] = cause(cid)
        slot["set_code"] = tcgplayer_links.tcg_set_code(cid)
        rows.append(slot)
    rows.sort(key=lambda row: (row["cause"], row["id"]))
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if "no_product_id" in row["reasons"]:
            grouped[row["cause"]].append(row["id"])
    summary = {
        "hosted_card_ids": len(cards),
        "missing_product_id": sum(len(v) for v in grouped.values()),
        "missing_catalog_name": sum("no_catalog_name" in row["reasons"] for row in rows),
        "by_cause": {key: ids_ for key, ids_ in grouped.items()},
    }
    payload = {"summary": {k: v for k, v in summary.items() if k != "by_cause"}, "groups": summary["by_cause"], "cards": rows}
    # summary.by_cause is the id lists; also store counts
    payload["summary"]["by_cause"] = {key: len(value) for key, value in grouped.items()}
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    missing = payload["summary"]["missing_product_id"]
    print(
        f"hosted_ids={payload['summary']['hosted_card_ids']} "
        f"missing_product_id={missing} "
        f"missing_catalog_name={payload['summary']['missing_catalog_name']} "
        f"by_cause={payload['summary']['by_cause']}"
    )
    if missing:
        print(
            f"::warning::{missing} hosted card ids have no TCGplayer product id. "
            f"See data/tcgplayer-unmatched.json."
        )


if __name__ == "__main__":
    main()
