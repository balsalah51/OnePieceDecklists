#!/usr/bin/env python3
"""Window math shared by the homepage and the tier list."""

from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import format_meta as fm


def row(lid: str, day: str, placing=None, bucket="tournament"):
    return {
        "date": day,
        "placing": placing,
        "bucket": bucket,
        "leader": {"id": lid, "page": "decklists/x.html", "name": lid},
    }


class FormatMetaTests(unittest.TestCase):
    def test_window_ends_on_eastern_today_not_newest_list(self) -> None:
        rows = [row("A", "2026-08-20"), row("A", "2026-10-16"), row("B", "")]
        today = date(2026, 10, 25)
        now = datetime(2026, 10, 25, 12, 0, tzinfo=ZoneInfo("America/New_York"))
        bounds = fm.window_bounds(rows, days=45, today=today, now=now)
        self.assertEqual(bounds["end"], "2026-10-25")
        self.assertEqual(bounds["start"], "2026-09-10")
        self.assertEqual(bounds["days"], 45)
        self.assertEqual(bounds["newest"], "2026-10-16")
        self.assertTrue(bounds["stale"])
        self.assertNotEqual(bounds["end"], bounds["newest"])

    def test_stale_uses_midnight_eastern_and_48_hours(self) -> None:
        now = datetime(2026, 10, 25, 12, 0, tzinfo=ZoneInfo("America/New_York"))
        today = date(2026, 10, 25)
        fresh = fm.window_bounds([row("A", "2026-10-24")], days=45, today=today, now=now)
        self.assertFalse(fresh["stale"])
        stale = fm.window_bounds([row("A", "2026-10-23")], days=45, today=today, now=now)
        self.assertTrue(stale["stale"])
        empty = fm.window_bounds([], days=45, today=today, now=now)
        self.assertTrue(empty["stale"])
        self.assertEqual(empty["end"], "2026-10-25")

    def test_window_is_configurable(self) -> None:
        rows = [row("A", "2026-10-16")]
        bounds = fm.window_bounds(rows, days=10, today=date(2026, 10, 16))
        expect = (date(2026, 10, 16) - timedelta(days=10)).isoformat()
        self.assertEqual(bounds["start"], expect)
        self.assertEqual(bounds["end"], "2026-10-16")

    def test_share_and_recent_counts_use_the_same_rows(self) -> None:
        rows = [
            row("OP14-020", "2026-10-08", 1),
            row("OP14-020", "2026-08-20", 1),
            row("OP17-039", "2026-10-12", 2),
            row("OP05-098", "2026-09-02", 3, bucket="community"),
            row("OP17-020", "2026-07-01", 1),
        ]
        bounds = fm.window_bounds(rows, days=45, today=date(2026, 10, 16))
        window = fm.in_window(rows, bounds)
        counts = fm.count_leaders(window)
        self.assertEqual(sum(counts.values()), len(window))
        self.assertEqual(counts.get("OP14-020"), 1)
        self.assertNotIn("OP17-020", counts)
        self.assertIn("OP05-098", counts)
        stats = fm.leader_stats(rows, bounds)
        self.assertEqual(stats["OP14-020"]["recent_lists"], counts["OP14-020"])
        self.assertEqual(stats["OP17-039"]["recent_lists"], counts["OP17-039"])
        self.assertEqual(stats["OP14-020"]["lists"], 2)
        self.assertEqual(stats["OP14-020"]["recent_wins"], 1)
        self.assertEqual(stats["OP17-020"]["recent_lists"], 0)
        self.assertEqual(stats["OP17-020"]["lists"], 1)
        later = fm.window_bounds(rows, days=45, today=date(2026, 10, 25))
        later_counts = fm.count_leaders(fm.in_window(rows, later))
        self.assertNotIn("OP05-098", later_counts)
        self.assertEqual(later["start"], "2026-09-10")

    def test_public_names_keep_same_character_leaders_apart(self) -> None:
        robin = {"id": "OP09-062", "name": "Nico Robin"}
        eb = {"id": "EB05-010", "name": "Nico Robin"}
        self.assertNotEqual(fm.public_name(robin), fm.public_name(eb))
        self.assertIn("OP09", fm.public_name(robin))
        self.assertIn("EB05", fm.public_name(eb))
        note = fm.twin_html(robin)
        self.assertIn("EB05-010", note)
        self.assertIn("/decklists/eb05-nico-robin.html", note)


if __name__ == "__main__":
    unittest.main()
