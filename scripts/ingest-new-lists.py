#!/usr/bin/env python3
"""Host newly published complete 50-card lists from public sources."""

from __future__ import annotations

import importlib.util

spec = importlib.util.spec_from_file_location("ingest_sep17", "/workspace/scripts/ingest-sep17-on-lists.py")
ingest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest)

ingest.SINCE = "2026-09-17"


if __name__ == "__main__":
    ingest.main()
