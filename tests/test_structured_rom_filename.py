import unittest

from romfile.structured_rom_filename import StructuredRomFileName


class TestStructuredRomFileName(unittest.TestCase):
    def test_title_extraction(self):
        filename = "Adventures of Batman and Robin, The (U) [p1][!].gen"
        rom = StructuredRomFileName(filename)
        self.assertEqual(rom.title, "The Adventures of Batman and Robin")

    def test_year_extraction(self):
        filename = "16 Tile Mahjong (1992)(City Man Technology - Gamtec)(TW)"
        rom = StructuredRomFileName(filename)
        self.assertEqual(rom.year, "1992")
        filename = "Addams Family, The (1993)(Acclaim - Flying Edge)(EU-US)(en)"
        rom = StructuredRomFileName(filename)
        self.assertEqual(rom.year, "1993")

    def test_extract_codes(self):
        filename = "Adventures of Batman and Robin, The (U) [p1][!].gen"
        rom = StructuredRomFileName(filename)
        self.assertEqual(rom.codes, ["(U)", "[p1]", "[!]"])
        filename = "Adventures of Rocky and Bullwinkle and Friends, The (1993)(Absolute Entertainment)(US)"
        rom = StructuredRomFileName(filename)
        self.assertEqual(rom.codes, ["(1993)", "(Absolute Entertainment)", "(US)"])

    def test_extract_inner_codes(self):
        filename = "Adventures of Batman and Robin, The (U) [p1][!].gen"
        rom = StructuredRomFileName(filename)
        self.assertEqual(rom.inner_codes, ["U", "p1", "!"])
        filename = "Adventures of Rocky and Bullwinkle and Friends, The (1993)(Absolute Entertainment)(US)"
        rom = StructuredRomFileName(filename)
        self.assertEqual(rom.inner_codes, ["1993", "Absolute Entertainment", "US"])
