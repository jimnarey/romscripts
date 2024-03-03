import unittest
import os

import romfile.romcodes as romcodes
from .fixtures import region_codes

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(SCRIPT_PATH, "fixtures")

GOODTOOLS_DUMP_CODES_PATH = os.path.join(FIXTURES_PATH, "goodtools_dump.json")
GOODTOOLS_REGION_CODES_JSON_PATH = os.path.join(FIXTURES_PATH, "goodtools_region.json")
NOINTRO_REGION_LANGUAGE_CODES_JSON_PATH = os.path.join(FIXTURES_PATH, "nointro_region_language.json")
TOSEC_REGION_LANGUAGE_CODES_JSON_PATH = os.path.join(FIXTURES_PATH, "tosec_region_language.json")


goodtools_dump_code_set = romcodes.CodeSet("goodtools", GOODTOOLS_DUMP_CODES_PATH)
goodtools_region_code_set = romcodes.CodeSet("goodtools", GOODTOOLS_REGION_CODES_JSON_PATH)
tosec_region_language_code_set = romcodes.CodeSet("tosec", TOSEC_REGION_LANGUAGE_CODES_JSON_PATH)
nointro_region_language_code_set = romcodes.CodeSet("nointro", NOINTRO_REGION_LANGUAGE_CODES_JSON_PATH)

region_code_set_manager = romcodes.CodeSetManager(
    [goodtools_region_code_set, tosec_region_language_code_set, nointro_region_language_code_set]
)


class TestCodeSet(unittest.TestCase):
    def test_flat_codes_by_type(self):
        code_specs = []
        for code_spec in goodtools_dump_code_set.flat_codes_by_type("dump"):
            code_specs.append(code_spec)
        self.assertEqual(len(code_specs), 9)
        self.assertEqual(
            code_specs[0],
            {
                "code_type": "dump",
                "code": "[a#]",
                "value": "Alternative",
                "regex": "\\[a[0-9]?\\]",
                "description": "The ROM is a copy of an alternative release of the game. Many games have been re-released to fix bugs or to eliminate Game Genie codes.",
            },
        )

    def test_split_code_tosec(self):
        code = "(EU-US)"
        delimiter = "-"
        parts = romcodes.CodeSet.split_code(code, delimiter)
        self.assertEqual(parts, ["EU", "US"])

    def test_split_code_nointro(self):
        code = "(USA, Europe)"
        delimiter = ","
        parts = romcodes.CodeSet.split_code(code, delimiter)
        self.assertEqual(parts, ["USA", "Europe"])

    def test_try_as_multi_code_tosec(self):
        code = "(EU-US)"
        multi_code = romcodes.CodeSet.try_as_multi_code(code)
        self.assertEqual(multi_code, {"(EU-US)": ["EU", "US"]})

    def test_try_as_multi_code_nointro(self):
        code = "(USA, Europe)"
        multi_code = romcodes.CodeSet.try_as_multi_code(code)
        self.assertEqual(multi_code, {"(USA, Europe)": ["USA", "Europe"]})

    def test_try_as_multi_code_no_multi_code(self):
        code = "(USA)"
        multi_code = romcodes.CodeSet.try_as_multi_code(code)
        self.assertEqual(multi_code, None)

    def test_match_split_codes_with_unbracketed_code(self):
        split_codes = [{"(US-EU)": ["US", "EU"]}, {"(En, Fr)": ["En", "Fr"]}]
        ub_code = "EU"
        index, code = romcodes.CodeSet.match_split_codes_with_unbracketed_code(split_codes, ub_code)
        self.assertEqual(index, 0)
        self.assertEqual(code, "(US-EU)")
        ub_code = "En"
        index, code = romcodes.CodeSet.match_split_codes_with_unbracketed_code(split_codes, ub_code)
        self.assertEqual(index, 1)
        self.assertEqual(code, "(En, Fr)")

    # TODO: match_bracketed/match_unbracketed - test multiple codes return one value

    def test_match_bracketed_literal(self):
        code = "[!]"
        code_spec = {"code": "[!]", "value": "verified"}
        match = goodtools_dump_code_set.match_bracketed([code], code_spec)
        self.assertEqual(match, {"[!]": {"code": "[!]", "value": "verified"}})

    def test_match_bracketed_regex(self):
        code = "[f4]"
        code_spec = {"code": "[f#]", "regex": "\\[f[0-9]?\\]", "value": "fixed"}
        match = goodtools_dump_code_set.match_bracketed([code], code_spec)
        self.assertEqual(match, {"[f4]": {"code": "[f#]", "regex": "\\[f[0-9]?\\]", "value": "fixed"}})


class TestCodeSetIntegration(unittest.TestCase):
    maxDiff = None

    # TODO: find_matching_full_code/test_matching_multi_code - test when multiple codes are passed in
    # TODO: add tests to confirm codes are de-populated as matches are found

    def test_find_matching_full_code(self):
        code = "[!]"
        matches = goodtools_dump_code_set.find_matching_full_codes([code], ["dump"])
        self.assertDictEqual(
            matches,
            {
                "[!]": {
                    "code": "[!]",
                    "code_type": "dump",
                    "description": "Verified - Good Dump. The ROM is an exact copy of the original game; it has not had any hacks or modifications.",
                    "regex": "",
                    "value": "verified",
                }
            },
        )

    def test_find_matching_full_code_by_type(self):
        code = "[!]"
        matches = goodtools_dump_code_set.find_matching_full_codes_by_type([code], "dump")
        self.assertDictEqual(
            matches,
            {
                "[!]": {
                    "code": "[!]",
                    "code_type": "dump",
                    "description": "Verified - Good Dump. The ROM is an exact copy of the original game; it has not had any hacks or modifications.",
                    "regex": "",
                    "value": "verified",
                }
            },
        )

    def test_find_matching_full_code_by_type_with_non_existent_type(self):
        code = "[!]"
        matches = goodtools_dump_code_set.find_matching_full_codes_by_type([code], "nonsense")
        self.assertDictEqual(matches, {})

    # TODO: add tests to confirm split_codes is de-populated as matches are found
    def test_find_matching_split_codes_by_type_tosec(self):
        split_codes = [{"(US-EU)": ["US", "EU"]}]
        matches = tosec_region_language_code_set.find_matching_split_codes_by_type(split_codes, "region")
        self.assertDictEqual(
            matches,
            {
                "(US-EU)": [
                    {"code_type": "region", "code": "(EU)", "value": "Europe", "regex": "", "description": ""},
                    {"code_type": "region", "code": "(US)", "value": "United States", "regex": "", "description": ""},
                ]
            },
        )
        split_codes = [{"(en, fr)": ["en", "fr"]}]
        matches = tosec_region_language_code_set.find_matching_split_codes_by_type(split_codes, "language")
        self.assertDictEqual(
            matches,
            {
                "(en, fr)": [
                    {"code_type": "language", "code": "(en)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(fr)", "value": "French", "regex": "", "description": ""},
                ]
            },
        )

    def test_find_matching_split_codes_by_type_nointro(self):
        split_codes = [{"(USA, Europe)": ["USA", "Europe"]}]
        matches = nointro_region_language_code_set.find_matching_split_codes_by_type(split_codes, "region")
        self.assertDictEqual(
            matches,
            {
                "(USA, Europe)": [
                    {
                        "code_type": "region",
                        "code": "(USA)",
                        "value": "United States, Canada",
                        "regex": "",
                        "description": "",
                    },
                    {
                        "code_type": "region",
                        "code": "(Europe)",
                        "value": "Europe",
                        "regex": "",
                        "description": "Can include Australia",
                    },
                ]
            },
        )
        split_codes = [{"(En,Fr)": ["En", "Fr"]}]
        matches = nointro_region_language_code_set.find_matching_split_codes_by_type(split_codes, "language")
        self.assertDictEqual(
            matches,
            {
                "(En,Fr)": [
                    {"code_type": "language", "code": "(En)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(Fr)", "value": "French", "regex": "", "description": ""},
                ]
            },
        )

    def test_find_matching_split_codes_by_type_with_non_existent_type(self):
        split_codes = [{"(USA, Europe)": ["USA", "Europe"]}]
        matches = nointro_region_language_code_set.find_matching_split_codes_by_type(split_codes, "nonsense")
        self.assertDictEqual(matches, {})

    def test_find_matching_split_codes_tosec(self):
        split_codes = [{"(US-EU)": ["US", "EU"]}, {"(en, fr)": ["en", "fr"]}]
        matches = tosec_region_language_code_set.find_matching_split_codes(split_codes)
        self.assertDictEqual(
            matches,
            {
                "(US-EU)": [
                    {"code_type": "region", "code": "(EU)", "value": "Europe", "regex": "", "description": ""},
                    {"code_type": "region", "code": "(US)", "value": "United States", "regex": "", "description": ""},
                ],
                "(en, fr)": [
                    {"code_type": "language", "code": "(en)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(fr)", "value": "French", "regex": "", "description": ""},
                ],
            },
        )

    def test_find_matching_split_codes_nointro(self):
        split_codes = [{"(USA, Europe)": ["USA", "Europe"]}, {"(En,Fr)": ["En", "Fr"]}]
        matches = nointro_region_language_code_set.find_matching_split_codes(split_codes)
        self.assertDictEqual(
            matches,
            {
                "(USA, Europe)": [
                    {
                        "code_type": "region",
                        "code": "(USA)",
                        "value": "United States, Canada",
                        "regex": "",
                        "description": "",
                    },
                    {
                        "code_type": "region",
                        "code": "(Europe)",
                        "value": "Europe",
                        "regex": "",
                        "description": "Can include Australia",
                    },
                ],
                "(En,Fr)": [
                    {"code_type": "language", "code": "(En)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(Fr)", "value": "French", "regex": "", "description": ""},
                ],
            },
        )

    def test_find_matching_multi_codes_tosec(self):
        codes = ["(US-EU)", "(en, fr)"]
        matches = tosec_region_language_code_set.find_matching_multi_codes(codes)
        self.assertDictEqual(
            matches,
            {
                "(US-EU)": [
                    {"code_type": "region", "code": "(EU)", "value": "Europe", "regex": "", "description": ""},
                    {"code_type": "region", "code": "(US)", "value": "United States", "regex": "", "description": ""},
                ],
                "(en, fr)": [
                    {"code_type": "language", "code": "(en)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(fr)", "value": "French", "regex": "", "description": ""},
                ],
            },
        )

    def test_find_matching_multi_codes_nointro(self):
        codes = ["(USA, Europe)", "(En,Fr)"]
        matches = nointro_region_language_code_set.find_matching_multi_codes(codes)
        self.assertDictEqual(
            matches,
            {
                "(USA, Europe)": [
                    {
                        "code_type": "region",
                        "code": "(USA)",
                        "value": "United States, Canada",
                        "regex": "",
                        "description": "",
                    },
                    {
                        "code_type": "region",
                        "code": "(Europe)",
                        "value": "Europe",
                        "regex": "",
                        "description": "Can include Australia",
                    },
                ],
                "(En,Fr)": [
                    {"code_type": "language", "code": "(En)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(Fr)", "value": "French", "regex": "", "description": ""},
                ],
            },
        )

    def test_match_codes_tosec(self):
        codes = ["(EU)", "(en, fr)"]
        matches = tosec_region_language_code_set.match_codes(codes)
        self.assertDictEqual(
            matches,
            {
                "(EU)": {"code_type": "region", "code": "(EU)", "value": "Europe", "regex": "", "description": ""},
                "(en, fr)": [
                    {"code_type": "language", "code": "(en)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(fr)", "value": "French", "regex": "", "description": ""},
                ],
            },
        )

    def test_match_codes_nointro(self):
        codes = ["(USA)", "(En,Fr)"]
        matches = nointro_region_language_code_set.match_codes(codes)
        self.assertDictEqual(
            matches,
            {
                "(USA)": {
                    "code_type": "region",
                    "code": "(USA)",
                    "value": "United States, Canada",
                    "regex": "",
                    "description": "",
                },
                "(En,Fr)": [
                    {"code_type": "language", "code": "(En)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(Fr)", "value": "French", "regex": "", "description": ""},
                ],
            },
        )

    def test_match_codes_by_type_tosec(self):
        codes = ["(EU)", "(en, fr)"]
        matches = tosec_region_language_code_set.match_codes(codes, ["region"])
        self.assertDictEqual(
            matches,
            {
                "(EU)": {"code_type": "region", "code": "(EU)", "value": "Europe", "regex": "", "description": ""},
            },
        )
        matches = tosec_region_language_code_set.match_codes(codes, ["language"])
        self.assertDictEqual(
            matches,
            {
                "(en, fr)": [
                    {"code_type": "language", "code": "(en)", "value": "English", "regex": "", "description": ""},
                    {"code_type": "language", "code": "(fr)", "value": "French", "regex": "", "description": ""},
                ],
            },
        )


class TestCodeSetManager(unittest.TestCase):
    def test_match_format_by_region_no_intro(self):
        codes = region_codes.NOINTRO_REGION_CODES
        for code in codes:
            matches = region_code_set_manager.match_format_by_region([code])
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].format, "nointro")

    def test_match_format_by_region_tosec(self):
        codes = region_codes.TOSEC_REGION_CODES
        codes.remove("(HK)")
        for code in codes:
            matches = region_code_set_manager.match_format_by_region([code])
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].format, "tosec")

    def test_match_format_by_region_goodtools(self):
        codes = region_codes.GOODTOOLS_REGION_CODES
        codes.remove("(HK)")
        for code in codes:
            matches = region_code_set_manager.match_format_by_region([code])
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].format, "goodtools")

    def test_match_format_by_region_no_match(self):
        codes = ["(HK)"]
        matches = region_code_set_manager.match_format_by_region(codes)
        self.assertEqual(len(matches), 2)
