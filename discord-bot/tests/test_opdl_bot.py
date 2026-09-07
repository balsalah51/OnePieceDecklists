from __future__ import annotations

import io
import re
import sys
import unittest
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOT_DIR))

from opdl_bot.config import (  # noqa: E402
    LEADERS,
    METAS,
    channel_name,
    emoji_name,
    leaders_for_meta,
    planned_channel_names,
    role_name,
)
from opdl_bot.data import (  # noqa: E402
    all_planned_messages,
    format_consensus_embed,
    load_card_cache,
    load_consensus,
)
from opdl_bot.emojis import crop_face, match_catalog_emoji  # noqa: E402

CHANNEL_NAME_RE = re.compile(r"^[a-z0-9-]{1,100}$")
EMOJI_NAME_RE = re.compile(r"^[a-z0-9_]{2,32}$")


class LayoutTests(unittest.TestCase):
    def test_fourteen_site_leaders(self):
        self.assertEqual(len(LEADERS), 14)
        self.assertEqual(len({L["id"] for L in LEADERS}), 14)
        self.assertEqual(len({L["key"] for L in LEADERS}), 14)

    def test_matches_site_generator(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "genlists", BOT_DIR.parent / "scripts" / "generate-tournament-lists.py"
        )
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        self.assertEqual({L["id"] for L in LEADERS}, {L["id"] for L in gen.LEADERS})
        self.assertEqual({L["key"] for L in LEADERS}, {L["key"] for L in gen.LEADERS})

    def test_op17_meta_has_six_set_leaders(self):
        op17 = leaders_for_meta("op17")
        self.assertEqual([L["id"] for L in op17], [
            "OP17-001",
            "OP17-020",
            "OP17-039",
            "OP17-058",
            "OP17-079",
            "OP17-099",
        ])
        self.assertEqual(len(leaders_for_meta("format")), 8)

    def test_channel_names_are_discord_safe_and_unique(self):
        names = planned_channel_names()
        self.assertGreaterEqual(len(names), 20)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertRegex(name, CHANNEL_NAME_RE)

    def test_emoji_and_role_names(self):
        seen = set()
        for leader in LEADERS:
            em = emoji_name(leader)
            self.assertRegex(em, EMOJI_NAME_RE)
            self.assertNotIn(em, seen)
            seen.add(em)
            self.assertTrue(role_name(leader).startswith("Leader · "))
            self.assertEqual(channel_name(leader), leader["key"])

    def test_generic_pages_exist(self):
        names = set(planned_channel_names())
        for page in ("welcome", "rules", "announcements", "flair"):
            self.assertIn(page, names)
        self.assertEqual({m["key"] for m in METAS}, {"op17", "format"})


class ConsensusTests(unittest.TestCase):
    def test_every_leader_has_a_consensus_file(self):
        consensus = load_consensus()
        for leader in LEADERS:
            self.assertIn(leader["id"], consensus, leader["id"])
            cards = consensus[leader["id"]]["cards"]
            total = sum(int(c["count"]) for c in cards)
            self.assertGreaterEqual(total, 40, leader["id"])

    def test_embeds_fit_discord_limits(self):
        cache = load_card_cache()
        consensus = load_consensus()
        for item in all_planned_messages(cache, consensus):
            embed = item["embed"]
            self.assertLessEqual(len(embed["title"]), 256)
            self.assertLessEqual(len(embed["description"]), 4096, item["leader"]["id"])
            self.assertLessEqual(len(embed["footer"]), 2048)
            self.assertLessEqual(len(item["text_list"]), 2000, item["leader"]["id"])
            self.assertIn(item["leader"]["id"], embed["footer"])

    def test_format_includes_leader_card(self):
        cache = load_card_cache()
        consensus = load_consensus()
        embed = format_consensus_embed(LEADERS[0], cache, consensus)
        self.assertIn("Edward Newgate", embed["title"])
        self.assertIn("OP17-001", embed["description"])


class EmojiTests(unittest.TestCase):
    def test_crop_face_is_128_png(self):
        from PIL import Image

        src = Image.new("RGBA", (488, 680), (180, 30, 30, 255))
        buf = io.BytesIO()
        src.save(buf, format="PNG")
        png = crop_face(buf.getvalue(), size=128)
        out = Image.open(io.BytesIO(png))
        self.assertEqual(out.size, (128, 128))
        self.assertEqual(out.format, "PNG")

    def test_committed_faces_are_square_pngs(self):
        from PIL import Image
        from opdl_bot.config import ASSETS_DIR, emoji_name

        for leader in LEADERS:
            path = ASSETS_DIR / f"{emoji_name(leader)}.png"
            self.assertTrue(path.exists(), path)
            with Image.open(path) as img:
                self.assertEqual(img.size, (128, 128), leader["key"])

    def test_flair_view_fits_discord_grid(self):
        from opdl_bot.flair import FlairView

        view = FlairView()
        self.assertLessEqual(len(view.children), 25)
        rows: dict[int, int] = {}
        for child in view.children:
            row = 0 if child.row is None else int(child.row)
            rows[row] = rows.get(row, 0) + 1
            self.assertLessEqual(row, 4)
        for count in rows.values():
            self.assertLessEqual(count, 5)

    def test_unique_catalog_match_only(self):
        catalog = [
            {"title": "OnePiece_Shanks", "slug": "shanks", "image": "https://cdn.example/shanks.png"},
            {"title": "luffy_one", "slug": "luffy-one", "image": "https://cdn.example/l1.png"},
            {"title": "luffy_two", "slug": "luffy-two", "image": "https://cdn.example/l2.png"},
        ]
        shanks = next(L for L in LEADERS if L["key"] == "shanks")
        luffy = next(L for L in LEADERS if L["key"] == "monkey-d-luffy")
        self.assertEqual(match_catalog_emoji(shanks, catalog)["image"], "https://cdn.example/shanks.png")
        self.assertIsNone(match_catalog_emoji(luffy, catalog))


if __name__ == "__main__":
    unittest.main()
