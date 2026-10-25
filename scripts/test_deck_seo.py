#!/usr/bin/env python3
"""Decklist titles name the leader, event, place, and date."""

from __future__ import annotations

import unittest

import deck_seo


class DeckSeoTests(unittest.TestCase):
    def test_title_shape(self) -> None:
        title = deck_seo.deck_title("Mihawk", "Regional", "1st", "2026-10-08")
        self.assertEqual(title, "Mihawk Decklist - Regional 1st (2026-10-08)")
        self.assertIn("Decklist", title)

    def test_description_terms(self) -> None:
        desc = deck_seo.deck_description("OP05 Enel", "Store Championship", "3rd", "2026-09-02")
        self.assertIn("OPTCG", desc)
        self.assertIn("decklist", desc)
        self.assertIn("OP05 Enel", desc)

    def test_stats_fallback_skips_empty_costs(self) -> None:
        text = deck_seo.stats_fallback(
            ["1 DON!! · 0", "2 DON!! · 8", "10+ DON!! · 2"],
            ["4× 2k", "6× 1k"],
        )
        self.assertIn("8 at 2 DON!!", text)
        self.assertIn("2 at 10+ DON!!", text)
        self.assertNotIn(" at 0+", text)
        self.assertIn("4× 2k", text)


if __name__ == "__main__":
    unittest.main()
