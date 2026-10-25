#!/usr/bin/env python3
"""Tests for event labels and placeholder-list filtering."""

from __future__ import annotations

import unittest

from event_display import display_event, event_badge, event_weight, is_test_row


class EventDisplayTests(unittest.TestCase):
    def test_hides_placeholder_events(self) -> None:
        self.assertTrue(
            is_test_row(
                {
                    "player": "Player01",
                    "tournament_name": "Tournoi Test #0",
                    "href": "/decklists/rocks-d-xebec/3rd-player01-tournoi-test-0.html",
                }
            )
        )
        self.assertTrue(
            is_test_row(
                {
                    "player": "Tenzy",
                    "tournament": "Tournoi Test #0",
                    "slug": "1st-tenzy-tournoi-test-0",
                }
            )
        )
        self.assertTrue(
            is_test_row(
                {
                    "player": "Player02",
                    "tournament_name": "1st Test Tournament",
                    "href": "/decklists/kaido/3rd-player02-1st-test-tournament.html",
                }
            )
        )
        self.assertFalse(
            is_test_row(
                {
                    "player": "Kiwitt",
                    "tournament_name": "[OP17.5] Win a box | Rumble league #13",
                    "href": "/decklists/luffy-ace/1st-kiwitt-op17-5-win-a-box-rumble-league-13.html",
                }
            )
        )

    def test_normalizes_source_titles(self) -> None:
        self.assertEqual(
            display_event("[OP17.5] Win a box | Rumble league #13"),
            "Rumble League #13 · Win a Box",
        )
        self.assertEqual(
            display_event("Liga Phoenix 2026 -  ONE PIECE - MANA 40°"),
            "Liga Phoenix 2026 · Mana 40",
        )
        self.assertEqual(
            display_event("[EGB] ChinoizeCup #123 Wednesday"),
            "Extra Grand Battle · ChinoizeCup #123 Wednesday",
        )
        self.assertEqual(display_event("Versus Cup"), "Versus Cup")
        self.assertEqual(
            display_event("[OP17] ChinoizeCup #99 Wednesday"),
            "ChinoizeCup #99 Wednesday",
        )
        self.assertEqual(
            display_event("[GER] Dressrosa Tournament-OP17"),
            "Dressrosa Tournament",
        )
        self.assertEqual(
            display_event("Public OPTCG.GG list · Organized Play Events' London Regionals"),
            "Organized Play Events' London Regional",
        )

    def test_ranks_large_events_above_online_cups(self) -> None:
        self.assertGreater(
            event_weight("NA Regional Championship"),
            event_weight("[OP17.5] Win a box | Rumble league #13"),
        )
        self.assertGreater(
            event_weight("Treasure Cup London"),
            event_weight("Versus Cup"),
        )
        self.assertEqual(event_badge("Store Championship Austin"), "Store Championship")
        self.assertEqual(event_badge("[OP17] ChinoizeCup #99 Wednesday"), "")
        self.assertEqual(event_badge("Liga Phoenix 2026 - ONE PIECE - MANA 40"), "League")


if __name__ == "__main__":
    unittest.main()
