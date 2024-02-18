import unittest

# import json
import os

# import logging

import romfile.romcodes as romcodes

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(SCRIPT_PATH, "fixtures")
GOODTOOLS_DUMP_CODES_PATH = os.path.join(FIXTURES_PATH, "goodtools_dump.json")
GOODTOOLS_REGION_CODES_PATH = os.path.join(
    FIXTURES_PATH, "goodtools_region.json"
)
NOINTRO_REGION_CODES_PATH = os.path.join(FIXTURES_PATH, "nointro_region.json")
TOSEC_REGION_CODES_PATH = os.path.join(FIXTURES_PATH, "tosec_region.json")

goodtools_dump_code_set = romcodes.CodeSet(
    "goodtools", GOODTOOLS_DUMP_CODES_PATH
)
tosec_region_code_set = romcodes.CodeSet("tosec", TOSEC_REGION_CODES_PATH)
nointro_region_code_set = romcodes.CodeSet(
    "nointro", NOINTRO_REGION_CODES_PATH
)


class TestCodeSet(unittest.TestCase):

    # Uses flat_codes_by_type
    def test_flat_codes(self):
        code_specs = []
        for code_spec in goodtools_dump_code_set.flat_all_codes():
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
        code_specs = []
        # Check against a different code set
        for code_spec in tosec_region_code_set.flat_all_codes():
            code_specs.append(code_spec)
        self.assertEqual(len(code_specs), 68)

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

    def test_get_code_parts_tosec(self):
        code = "(EU-US)"
        delimiter = "-"
        parts = romcodes.CodeSet.get_code_parts(code, delimiter)
        self.assertEqual(parts, ["EU", "US"])

    def test_code_parts_nointro(self):
        code = "(USA, Europe)"
        delimiter = ","
        parts = romcodes.CodeSet.get_code_parts(code, delimiter)
        self.assertEqual(parts, ["USA", "Europe"])

    def test_match_unbracketed(self):
        code = "!"
        code_spec = {
            "code": "[!]",
            "code_type": "dump",
            "description": "Verified - Good Dump. The ROM is an exact copy of the "
            "original game; it has not had any hacks or modifications.",
            "regex": "",
            "value": "verified",
        }
        match = goodtools_dump_code_set.match_unbracketed(code, code_spec)
        self.assertEqual(match, code_spec)

    def test_match_bracketed_literal(self):
        code = "[!]"
        code_spec = {
            "code": "[!]",
            "code_type": "dump",
            "description": "Verified - Good Dump. The ROM is an exact copy of the "
            "original game; it has not had any hacks or modifications.",
            "regex": "",
            "value": "verified",
        }
        match = goodtools_dump_code_set.match_bracketed(code, code_spec)
        self.assertEqual(match, code_spec)

    def test_match_bracketed_regex(self):
        code = "[f4]"
        code_spec = {
            "code": "[f#]",
            "code_type": "dump",
            "description": "A fixed dump is a ROM that has been altered to run better on "
            "a flashcart or an emulator.",
            "regex": "\\[f[0-9]?\\]",
            "value": "Fixed",
        }
        match = goodtools_dump_code_set.match_bracketed(code, code_spec)
        self.assertEqual(match, code_spec)

    def test_find_matching_full_code(self):
        code = "[!]"
        matches = goodtools_dump_code_set.find_matching_full_code(code)
        self.assertEqual(
            matches,
            [
                {
                    "code": "[!]",
                    "code_type": "dump",
                    "description": "Verified - Good Dump. The ROM is an exact copy of the "
                    "original game; it has not had any hacks or modifications.",
                    "regex": "",
                    "value": "verified",
                }
            ],
        )

    # Uses find_matching_multi_code_by_type
    def test_find_matching_multi_code_with_valid_tosec_region_code(self):
        code = "(EU-US)"
        matches = tosec_region_code_set.find_matching_multi_code(code)
        self.assertEqual(len(matches), 2)
        self.assertEqual(
            matches[0],
            {
                "code": "(EU)",
                "code_type": "region",
                "description": "",
                "regex": "",
                "value": "Europe",
            },
        )
        self.assertEqual(
            matches[1],
            {
                "code": "(US)",
                "code_type": "region",
                "description": "",
                "regex": "",
                "value": "United States",
            },
        )

    def test_find_matching_multi_code_with_valid_nointro_region_code(self):
        code = "(USA, Europe)"
        matches = nointro_region_code_set.find_matching_multi_code(code)
        self.assertEqual(len(matches), 2)
        self.assertEqual(
            matches[0],
            {
                "code": "(USA)",
                "code_type": "region",
                "description": "",
                "regex": "",
                "value": "United States. Includes Canada",
            },
        )
        self.assertEqual(
            matches[1],
            {
                "code": "(Europe)",
                "code_type": "region",
                "description": "",
                "regex": "",
                "value": "Two or more European countries, includes Australia",
            },
        )

    # TODO: Add some tests to ensure that arbitrary values separated by commas
    # or dashes are not matched as multi-codes

    def test_find_matching_multi_code_by_type(self):
        code = "(EU-US)"
        matches = tosec_region_code_set.find_matching_multi_code_by_type(
            code, "-", "region"
        )
        self.assertEqual(len(matches), 2)
        self.assertEqual(
            matches[0],
            {
                "code": "(EU)",
                "code_type": "region",
                "description": "",
                "regex": "",
                "value": "Europe",
            },
        )
        self.assertEqual(
            matches[1],
            {
                "code": "(US)",
                "code_type": "region",
                "description": "",
                "regex": "",
                "value": "United States",
            },
        )
