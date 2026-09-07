"""Build TCGplayer search, product, and mass-entry URLs.

Buy links wrap through the Impact partner URL in data/tcgplayer.json
(and js/tcgplayer-config.js as a fallback).
"""

from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path("/workspace")
CONFIG_PATH = ROOT / "data/tcgplayer.json"
IDS_PATH = ROOT / "data/tcgplayer-ids.json"
NAMES_PATH = ROOT / "data/tcgplayer-names.json"
DEFAULT_PARTNER = "https://partner.tcgplayer.com/c/7670706/1780961/21018"
PRODUCT_LINE = "One Piece Card Game"
SEARCH_LINE = "one-piece-card-game"
SIM_CHUNK_RE = re.compile(
    r"(?i)(\d+)\s*[x×]\s*((?:OP|ST|EB|PRB)\d{2}-\d{3}|P-\d{3})"
)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"partnerLink": ""}
    return json.loads(CONFIG_PATH.read_text())


def load_ids() -> dict[str, int]:
    if not IDS_PATH.exists():
        return {}
    raw = json.loads(IDS_PATH.read_text())
    out: dict[str, int] = {}
    for cid, pid in raw.items():
        try:
            out[cid.upper()] = int(pid)
        except (TypeError, ValueError):
            continue
    return out


def affiliate_url(dest: str, partner_link: str | None = None) -> str:
    if partner_link is None:
        partner_link = str(load_config().get("partnerLink") or "")
    partner_link = (partner_link or DEFAULT_PARTNER).strip() or DEFAULT_PARTNER
    if "partner.tcgplayer.com" in dest:
        return dest
    sep = "&" if "?" in partner_link else "?"
    return partner_link + sep + "u=" + urllib.parse.quote(dest, safe="")


def card_url(cid: str, product_id: int | None = None) -> str:
    if product_id:
        return f"https://www.tcgplayer.com/product/{int(product_id)}"
    q = urllib.parse.urlencode({"q": cid, "productLineName": SEARCH_LINE})
    return f"https://www.tcgplayer.com/search/{SEARCH_LINE}/product?{q}"


TCG_SET_OVERRIDES = {
    "P": "OP-PR",
    "OP15": "OP15-EB04",
    "EB04": "OP15-EB04",
    "EB03": "EB-03-04",
}


def tcg_set_code(cid: str) -> str:
    """TCGPlayer Mass Entry set abbreviation for a Bandai card id."""
    cid = (cid or "").strip().upper()
    prefix = cid.split("-", 1)[0] if "-" in cid else cid
    if prefix in TCG_SET_OVERRIDES:
        return TCG_SET_OVERRIDES[prefix]
    if re.fullmatch(r"OP\d+", prefix):
        return prefix
    m = re.fullmatch(r"([A-Z]+)(\d+)", prefix)
    return f"{m.group(1)}-{m.group(2)}" if m else prefix


def collector_number(cid: str) -> str:
    cid = (cid or "").strip().upper()
    return cid.split("-", 1)[1] if "-" in cid else cid


_CARD_CACHE: dict | None = None
_SAME_SET_NAME_COUNTS: dict[tuple[str, str], int] | None = None
_CATALOG_NAMES: dict[str, str] | None = None


def load_catalog_names() -> dict[str, str]:
    """Official TCGplayer product names keyed by Bandai card id."""
    global _CATALOG_NAMES
    if _CATALOG_NAMES is None:
        raw = json.loads(NAMES_PATH.read_text()) if NAMES_PATH.exists() else {}
        _CATALOG_NAMES = {str(cid).upper(): str(name) for cid, name in raw.items() if name}
    return _CATALOG_NAMES


def load_card_cache() -> dict:
    global _CARD_CACHE
    if _CARD_CACHE is None:
        path = ROOT / "data/card-cache.json"
        _CARD_CACHE = json.loads(path.read_text()) if path.exists() else {}
    return _CARD_CACHE


def same_set_name_counts() -> dict[tuple[str, str], int]:
    """How many cards share the same printed name inside one Bandai set."""
    global _SAME_SET_NAME_COUNTS
    if _SAME_SET_NAME_COUNTS is None:
        counts: dict[tuple[str, str], int] = {}
        for cid, meta in load_card_cache().items():
            if not isinstance(meta, dict):
                continue
            name = str(meta.get("name") or "").strip().lower()
            if not name:
                continue
            prefix = str(cid).split("-", 1)[0].upper()
            key = (name, prefix)
            counts[key] = counts.get(key, 0) + 1
        _SAME_SET_NAME_COUNTS = counts
    return _SAME_SET_NAME_COUNTS


def is_leader_card(cid: str, flagged: bool = False) -> bool:
    if flagged:
        return True
    meta = load_card_cache().get((cid or "").strip().upper()) or {}
    return str(meta.get("category") or "").lower() == "leader"


def catalog_name(name: str, cid: str, is_leader: bool = False) -> str:
    """TCGPlayer Mass Entry product name.

    Prefer the official catalog name. TCGPlayer suffixes many unique-in-set
    cards (`Sanji (065)`, `Jewelry Bonney (026)`) and uses other shapes
    (`Boa Hancock - OP14-041`) that same-set collision counting misses.
    """
    del is_leader
    cid = (cid or "").strip().upper()
    official = load_catalog_names().get(cid)
    if official:
        return official
    name = (name or "").strip()
    if not name:
        meta = load_card_cache().get(cid) or {}
        name = str(meta.get("name") or "").strip()
    if not name:
        return ""
    if "(" in name:
        return name
    prefix = cid.split("-", 1)[0] if "-" in cid else cid
    if same_set_name_counts().get((name.lower(), prefix), 0) > 1:
        return f"{name} ({collector_number(cid)})"
    return name


def mass_entry_line(
    qty: int,
    cid: str,
    name: str = "",
    product_id: int | None = None,
    is_leader: bool = False,
) -> str:
    """One Mass Entry line in TCGPlayer's documented format.

    Quantity → Card Name → [Set Code] → Card Number
    Number is TCGPlayer's catalog number (OP17-112), not just 112.
    Same-set name collisions get a collector suffix.
    https://help.tcgplayer.com/hc/en-us/articles/360055768913
    """
    cid = (cid or "").strip().upper()
    name = catalog_name(name, cid, is_leader)
    set_code = tcg_set_code(cid)
    if name and set_code:
        return f"{int(qty)} {name} [{set_code}] {cid}"
    if name:
        return f"{int(qty)} {name}"
    if product_id:
        return f"{int(qty)}-{int(product_id)}"
    return f"{int(qty)} {cid}"


def mass_entry_text(cards: list[tuple]) -> str:
    """Newline Mass Entry list for the paste box."""
    parts = []
    seen: set[str] = set()
    for row in cards:
        qty = int(row[0])
        cid = str(row[1] or "").strip().upper()
        name = str(row[2]).strip() if len(row) > 2 and row[2] else ""
        flagged = bool(row[3]) if len(row) > 3 else False
        if qty <= 0 or not cid or cid in seen:
            continue
        seen.add(cid)
        parts.append(mass_entry_line(qty, cid, name, is_leader=flagged))
    return "\n".join(parts)


def mass_entry_url(cards: list[tuple], product_ids: dict[str, int] | None = None) -> str:
    """Build a TCGplayer Mass Entry URL.

    Each card is (qty, card_id) or (qty, card_id, name).
    product_ids defaults to data/tcgplayer-ids.json. Pass {} to force text lines.
    """
    if product_ids is None:
        product_ids = load_ids()
    cache = load_card_cache()
    parts = []
    for row in cards:
        qty = int(row[0])
        cid = str(row[1] or "").strip().upper()
        name = str(row[2]).strip() if len(row) > 2 and row[2] else ""
        if qty <= 0 or not cid:
            continue
        if not name:
            meta = cache.get(cid) or {}
            name = str(meta.get("name") or "").strip()
        pid = product_ids.get(cid)
        if not pid:
            meta = cache.get(cid) or {}
            try:
                pid = int(meta.get("tcgplayer_id") or 0) or None
            except (TypeError, ValueError):
                pid = None
        parts.append(mass_entry_line(qty, cid, name, pid))
    c = "||".join(parts)
    q = urllib.parse.urlencode({"productline": PRODUCT_LINE, "c": c})
    return f"https://www.tcgplayer.com/massentry?{q}"


def parse_sim_text(text: str) -> list[tuple[int, str]]:
    cards: list[tuple[int, str]] = []
    seen: set[str] = set()
    for qty, cid in SIM_CHUNK_RE.findall(text or ""):
        cid = cid.upper()
        if cid in seen:
            continue
        seen.add(cid)
        cards.append((int(qty), cid))
    return cards
