#!/usr/bin/env python3
"""Accented names keep their letters in decklist slugs."""

from __future__ import annotations

import unittest


def _load():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "genlists_slug", Path("/workspace/scripts/generate-tournament-lists.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = _load()


class SlugifyTests(unittest.TestCase):
    def test_transliterates_accents(self) -> None:
        self.assertEqual(gen.slugify("José"), "jose")
        self.assertEqual(gen.slugify("Julián"), "julian")
        self.assertEqual(gen.slugify("José Cuevas"), "jose-cuevas")
        self.assertEqual(gen.slugify("Julián Cassano ghio"), "julian-cassano-ghio")

    def test_plain_ascii_unchanged(self) -> None:
        self.assertEqual(gen.slugify("Rocks D. Xebec"), "rocks-d-xebec")
        self.assertEqual(gen.slugify("Monkey D. Luffy"), "monkey-d-luffy")


if __name__ == "__main__":
    unittest.main()
