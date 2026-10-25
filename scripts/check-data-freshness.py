#!/usr/bin/env python3
"""Print whether the newest hosted list is older than 48 hours.

Exits 0 either way. A stale catalog is a site warning, not a crashed ingest.
GitHub shows the warning annotation on the workflow run so it is not silent.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import format_meta as fm  # noqa: E402


def main() -> None:
    rows = fm.hosted_rows()
    if not rows:
        print("NO HOSTED LISTS")
        raise SystemExit(1)
    bounds = fm.window_bounds(rows)
    print(
        f"newest={bounds.get('newest') or 'none'} "
        f"window={bounds.get('start')}..{bounds.get('end')} "
        f"stale={bounds.get('stale')}"
    )
    if bounds.get("stale"):
        newest = bounds.get("newest") or "unknown"
        print(
            f"::warning::Newest hosted list is {newest}, more than 48 hours before now in America/New_York."
        )


if __name__ == "__main__":
    main()
