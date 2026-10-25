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

    def test_macron_and_acute_c(self) -> None:
        self.assertEqual(gen.slugify("Mū"), "mu")
        self.assertEqual(gen.slugify("Yū"), "yu")
        self.assertEqual(gen.slugify("Žan Marinković"), "zan-marinkovic")
        self.assertEqual(gen.slugify("Antonio Cimić"), "antonio-cimic")

    def test_fix_stem_does_not_double_a_correct_slug(self) -> None:
        import importlib.util
        from pathlib import Path

        spec = importlib.util.spec_from_file_location(
            "url_scheme", Path("/workspace/scripts/apply-url-scheme.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        page = "<h2>Mū - Event</h2>"
        self.assertEqual(
            mod.fix_stem("optcggg-8th-m-flame", page),
            "optcggg-8th-mu-flame",
        )
        self.assertEqual(mod.fix_stem("optcggg-8th-mu-flame", page), "optcggg-8th-mu-flame")
        cimic = "<h2>Antonio Cimić - Koby</h2>"
        self.assertEqual(
            mod.fix_stem("16th-antonio-cimi-tcg", cimic),
            "16th-antonio-cimic-tcg",
        )
        self.assertEqual(
            mod.fix_stem("16th-antonio-cimic-tcg", cimic),
            "16th-antonio-cimic-tcg",
        )


if __name__ == "__main__":
    unittest.main()
