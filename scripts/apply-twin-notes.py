#!/usr/bin/env python3
"""Cross-link leaders that share a character name but are different cards."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path("/workspace")
spec = importlib.util.spec_from_file_location("formatmeta", ROOT / "scripts/format_meta.py")
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)


def main() -> None:
    changed = 0
    for leader in fm._gen.LEADERS:
        note = fm.twin_html(leader)
        if not note:
            continue
        path = ROOT / leader["page"]
        if not path.exists():
            print("missing", path)
            continue
        text = path.read_text()
        label = fm.public_name(leader)
        short = leader["name"]
        if f"<h2>{short}</h2>" in text and short != label:
            text = text.replace(f"<h2>{short}</h2>", f"<h2>{label}</h2>", 1)
        block = (
            "            <!-- TWIN_NOTE -->\n"
            f"            {note}\n"
            "            <!-- /TWIN_NOTE -->\n"
        )
        if "<!-- TWIN_NOTE -->" in text:
            text2 = re.sub(
                r"[ \t]*<!-- TWIN_NOTE -->.*?<!-- /TWIN_NOTE -->\n",
                block,
                text,
                count=1,
                flags=re.S,
            )
        else:
            needle = f"<h2>{label}</h2>"
            if needle not in text:
                print("no h2", path)
                continue
            text2 = text.replace(needle, needle + "\n" + block, 1)
        if text2 != path.read_text():
            path.write_text(text2)
            changed += 1
            print("noted", leader["id"], path)
    print("twin notes", changed)


if __name__ == "__main__":
    main()
