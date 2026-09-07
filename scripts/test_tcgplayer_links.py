#!/usr/bin/env python3
import sys
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tcgplayer_links import (
    affiliate_url,
    card_url,
    catalog_name,
    mass_entry_line,
    mass_entry_text,
    mass_entry_url,
    parse_sim_text,
    tcg_set_code,
)


class TcgplayerLinksTest(unittest.TestCase):
    def test_card_product_url(self):
        self.assertEqual(card_url("OP17-079", 707123), "https://www.tcgplayer.com/product/707123")

    def test_card_search_fallback(self):
        url = card_url("OP17-079")
        self.assertIn("OP17-079", url)
        self.assertIn("one-piece-card-game", url)

    def test_mass_entry_uses_official_qty_name_set_number(self):
        url = mass_entry_url(
            [
                (4, "OP17-104", "Charlotte Cracker"),
                (1, "OP09-062", "Nico Robin"),
            ],
            product_ids={},
        )
        parsed = urllib.parse.urlparse(url)
        self.assertEqual(parsed.path, "/massentry")
        q = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(q["productline"], ["One Piece Card Game"])
        self.assertEqual(
            q["c"],
            ["4 Charlotte Cracker [OP17] OP17-104||1 Nico Robin (062) [OP09] OP09-062"],
        )

    def test_mass_entry_uses_each_cards_own_name_and_number(self):
        url = mass_entry_url(
            [
                (1, "OP16-079", "Yamato"),
                (4, "OP16-091", "Nami"),
            ],
            product_ids={},
        )
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(q["c"], ["1 Yamato (079) [OP16] OP16-079||4 Nami [OP16] OP16-091"])
        self.assertNotIn("Charlotte", q["c"][0])

    def test_mass_entry_lines_match_tcgplayer_parser(self):
        import re

        official = re.compile(
            r"^(?P<quantity>\d+)(\s+(?P<productName>\S.*)|-(?P<productId>\d+))"
            r"\s+\[(?P<setCode>.+)\]\s+(?P<number>.+)$"
        )
        for line in (
            "1 Lightning Bolt [SLD] 84",
            "4 Charlotte Cracker [OP17] OP17-104",
            "1 Nico Robin (062) [OP09] OP09-062",
            "4 Streusen (113) [OP17] OP17-113",
            "4 Kin'emon [ST-32] ST32-001",
        ):
            self.assertTrue(official.match(line), line)

    def test_tcg_set_codes_match_catalog(self):
        self.assertEqual(tcg_set_code("OP17-104"), "OP17")
        self.assertEqual(tcg_set_code("ST32-001"), "ST-32")
        self.assertEqual(tcg_set_code("EB01-056"), "EB-01")
        self.assertEqual(tcg_set_code("PRB01-001"), "PRB-01")
        self.assertEqual(tcg_set_code("P-107"), "OP-PR")
        self.assertEqual(tcg_set_code("OP15-118"), "OP15-EB04")
        self.assertEqual(tcg_set_code("EB04-007"), "OP15-EB04")
        self.assertEqual(tcg_set_code("EB03-012"), "EB-03-04")

    def test_catalog_name_uses_official_tcgplayer_names(self):
        self.assertEqual(catalog_name("Charlotte Cracker", "OP17-104"), "Charlotte Cracker")
        self.assertEqual(catalog_name("Charlotte Linlin", "OP17-112"), "Charlotte Linlin (112)")
        self.assertEqual(catalog_name("Nico Robin", "OP09-062"), "Nico Robin (062)")
        self.assertEqual(catalog_name("Streusen", "OP17-113"), "Streusen (113)")
        self.assertEqual(catalog_name("Yamato", "OP17-074"), "Yamato")
        self.assertEqual(catalog_name("Charlotte Pudding", "OP17-109"), "Charlotte Pudding")
        self.assertEqual(catalog_name("Kin'emon", "ST32-001"), "Kin'emon")
        self.assertEqual(catalog_name("Sanji", "OP09-065"), "Sanji (065)")
        self.assertEqual(catalog_name("Jewelry Bonney", "OP07-026"), "Jewelry Bonney (026)")
        self.assertEqual(catalog_name("Charlotte Katakuri", "ST34-001"), "Charlotte Katakuri (ST34-001)")
        self.assertEqual(catalog_name("Boa Hancock", "OP14-041"), "Boa Hancock - OP14-041")

    def test_mass_entry_text_is_newline_official_format(self):
        text = mass_entry_text([
            (1, "OP09-062", "Nico Robin", True),
            (4, "OP17-112", "Charlotte Linlin"),
            (4, "OP17-113", "Streusen"),
            (4, "OP17-104", "Charlotte Cracker"),
        ])
        self.assertEqual(
            text,
            "1 Nico Robin (062) [OP09] OP09-062\n"
            "4 Charlotte Linlin (112) [OP17] OP17-112\n"
            "4 Streusen (113) [OP17] OP17-113\n"
            "4 Charlotte Cracker [OP17] OP17-104",
        )

    def test_mass_entry_line_official_and_id_fallback(self):
        self.assertEqual(
            mass_entry_line(4, "OP17-104", "Charlotte Cracker", product_id=708209),
            "4 Charlotte Cracker [OP17] OP17-104",
        )
        self.assertEqual(mass_entry_line(4, "OP17-104", product_id=708209), "4 Charlotte Cracker [OP17] OP17-104")
        self.assertEqual(
            mass_entry_line(4, "ST32-001", "Kin'emon"),
            "4 Kin'emon [ST-32] ST32-001",
        )
        self.assertEqual(
            mass_entry_line(1, "OP09-062", "Nico Robin", is_leader=True),
            "1 Nico Robin (062) [OP09] OP09-062",
        )

    def test_affiliate_wraps_when_partner_blank(self):
        dest = "https://www.tcgplayer.com/product/1"
        wrapped = affiliate_url(dest, "")
        self.assertTrue(wrapped.startswith("https://partner.tcgplayer.com/"))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(wrapped).query)
        self.assertEqual(q["u"], [dest])

    def test_affiliate_wraps_impact_link(self):
        dest = "https://www.tcgplayer.com/product/707123"
        wrapped = affiliate_url(dest, "https://partner.tcgplayer.com/c/1/2/3")
        self.assertTrue(wrapped.startswith("https://partner.tcgplayer.com/c/1/2/3?"))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(wrapped).query)
        self.assertEqual(q["u"], [dest])

    def test_live_partner_link_wraps_every_destination(self):
        from tcgplayer_links import load_config

        partner = load_config()["partnerLink"]
        self.assertEqual(partner, "https://partner.tcgplayer.com/c/7670706/1780961/21018")
        dest = (
            "https://www.tcgplayer.com/massentry?productline=One%20Piece%20Card%20Game"
            "&c=1%20Nico%20Robin%20%5BOP09%5D%20062"
        )
        wrapped = affiliate_url(dest)
        self.assertTrue(wrapped.startswith(partner + "?"))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(wrapped).query)
        self.assertEqual(q["u"], [dest])
        self.assertIn("partner.tcgplayer.com/c/7670706/1780961/21018", wrapped)

    def test_parse_sim_text(self):
        cards = parse_sim_text("1xOP08-058 4xOP11-070 4×ST34-003")
        self.assertEqual(cards, [(1, "OP08-058"), (4, "OP11-070"), (4, "ST34-003")])


class TcgplayerPlacementTest(unittest.TestCase):
    def setUp(self):
        spec = __import__("importlib.util").util.spec_from_file_location(
            "upgrade", Path("/workspace/scripts/upgrade-public-pages.py")
        )
        self.up = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(self.up)

    def test_keeps_helper_mass_entry_page(self):
        html = '<textarea id="mass-text"></textarea></body>'
        out = self.up.ensure_tcgplayer_scripts(html)
        self.assertIn("/js/tcgplayer-names.js?v=tcg-quiet", out)
        self.assertIn("/js/tcgplayer.js?v=tcg-quiet", out)

    def test_skips_homepage_without_lists(self):
        html = '<main class="single home" role="main"><section id="recent"></section></main></body>'
        out = self.up.ensure_tcgplayer_scripts(html)
        self.assertNotIn("tcgplayer.js", out)

    def test_adds_to_leader_hub(self):
        html = '<li class="list-row"></li></body>'
        out = self.up.ensure_tcgplayer_scripts(html)
        self.assertIn("/js/tcgplayer.js?v=tcg-quiet", out)
        self.assertIn("/js/tcgplayer-names.js?v=tcg-quiet", out)

    def test_adds_to_individual_decklist(self):
        html = (
            '<section class="text-deck"></section>'
            '<section class="picture-summary"></section>'
            "</body>"
        )
        out = self.up.ensure_tcgplayer_scripts(html)
        self.assertIn("/js/tcgplayer.js?v=tcg-quiet", out)
        self.assertEqual(out.count("tcgplayer.js"), 1)

    def test_refreshes_stale_script_version(self):
        html = (
            '<li class="list-row"></li>\n'
            '  <script src="/js/tcgplayer-config.js?v=tcg-buy"></script>\n'
            '  <script src="/js/tcgplayer-ids.js?v=tcg-buy"></script>\n'
            '  <script src="/js/tcgplayer.js?v=tcg-buy"></script>\n'
            "</body>"
        )
        out = self.up.ensure_tcgplayer_scripts(html)
        self.assertIn("v=tcg-quiet", out)
        self.assertIn("/js/tcgplayer-names.js?v=tcg-quiet", out)
        self.assertNotIn("v=tcg-buy", out)

    def test_js_restores_pills_and_always_affiliates(self):
        src = Path("/workspace/js/tcgplayer.js").read_text()
        self.assertIn("addHubButtons", src)
        self.assertIn("Buy list on TCGplayer", src)
        self.assertIn("Buy on TCGplayer", src)
        self.assertIn("FALLBACK_PARTNER", src)
        self.assertIn("partner.tcgplayer.com/c/7670706/1780961/21018", src)
        self.assertIn("openMassEntry", src)
        self.assertIn("massQuery", src)
        self.assertIn("&c=", src)
        self.assertIn("[\" + setCode + \"] \" + cid", src)
        self.assertIn("OPDL_TCGPLAYER_NAMES", Path("/workspace/js/tcgplayer-names.js").read_text())
        self.assertIn("NAMES[cid]", src)
        self.assertIn("Sanji (065)", Path("/workspace/data/tcgplayer-names.json").read_text())
        self.assertIn("clipboard", src)
        self.assertIn("execCommand", src)
        self.assertIn("tcgSetCode", src)
        self.assertIn("affiliate", src)
        self.assertIn("text-deck-leader", src)
        self.assertNotIn("Buy list opens TCGplayer", src)
        self.assertNotIn("Hover or tap a card name", Path("/workspace/scripts/generate-tournament-lists.py").read_text())
        helper = Path("/workspace/shop/buy-list.html").read_text()
        self.assertIn("noindex", helper)
        self.assertIn("Lightning Bolt", helper)

    def test_hover_preview_uses_larger_fallback(self):
        chrome = Path("/workspace/scripts/generate-tournament-lists.py").read_text()
        self.assertIn("offsetWidth || 220", chrome)
        self.assertIn("offsetHeight || 308", chrome)


if __name__ == "__main__":
    unittest.main()
