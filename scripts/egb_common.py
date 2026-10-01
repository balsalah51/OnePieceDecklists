#!/usr/bin/env python3
"""Identify Extra Grand Battle lists already hosted on the site.

Limitless marks Extra cups as format EXTRA (ChinoizeCup Wednesdays, [EGB] names).
Does not treat a local event named "EGB 1° Edição" as Extra Grand Battle.
"""

from __future__ import annotations

import re

EGB_RE = re.compile(
    r"\[EGB\]|extra grand battle|egb-chinoizecup|egb chinoize|chinoizecup[^\n]{0,40}egb",
    re.I,
)


def is_egb(row: dict | None = None, *, name: str = "", slug: str = "", href: str = "", fmt: str = "") -> bool:
    if row:
        name = name or str(row.get("tournament_name") or row.get("tournament") or row.get("subtitle") or "")
        slug = slug or str(row.get("slug") or "")
        href = href or str(row.get("href") or "")
        fmt = fmt or str(row.get("format") or "")
    if str(fmt).upper() == "EXTRA":
        return True
    blob = " ".join(part for part in (name, slug, href) if part)
    return bool(EGB_RE.search(blob))
