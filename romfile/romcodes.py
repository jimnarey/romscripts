#!/usr/bin/python3
from typing import Optional, Union
import re
import json
import os

# import logging

MULTI_CODE_TYPES = ["region", "language"]
MULTI_CODE_DELIMITERS = "-,"

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_PATH, "data")

CodeCollection = dict[str, dict[str, dict]]
CodeSpec = dict[str, str]
CodeSpecMatches = dict[str, Union[CodeSpec, list[CodeSpec]]]
SplitCodes = list[dict[str, list[str]]]


class CodeSet(object):
    @staticmethod
    def split_code(code: str, delimiter: str) -> list[str]:
        # Multi-codes don't come in []
        code = "".join([char for char in code if char not in "() "])
        return code.split(delimiter)

    @staticmethod
    def try_as_multi_code(code: str) -> Optional[dict[str, list[str]]]:
        """
        The only multi-codes we care about are for region or language and
        we know that such codes will only have one of two delimiters, so
        it's fine to go with the first one that works.
        """
        for delimiter in MULTI_CODE_DELIMITERS:
            if len(split_code := CodeSet.split_code(code, delimiter)) > 1:
                return {code: split_code}
        return None

    @staticmethod
    def match_bracketed(codes: list[str], code_spec: CodeSpec) -> CodeSpecMatches:
        """
        codes: e.g. ["(USA)", "[!]"] or ["(U)", "[!]"]
        """
        if code_spec["code"] in codes:
            codes.remove(code_spec["code"])
            return {code_spec["code"]: code_spec}
        if code_spec["regex"]:
            for code in codes:
                if re.fullmatch(code_spec["regex"], code):
                    codes.remove(code)
                    return {code: code_spec}
        return {}

    @staticmethod
    def match_split_codes_with_unbracketed_code(
        split_codes: list[dict], ub_code: str
    ) -> tuple[Optional[int], Optional[str]]:
        """
        split_codes: e.g. [{"(US-EU)": ["US", "EU"]}, {"(En, Fr)": ["En", "Fr"]}]
        ub_code: e.g. "US"
        """
        index, code = next(
            ((i, key) for i, dict_ in enumerate(split_codes) for key, sublist in dict_.items() if ub_code in sublist),
            (None, None),
        )
        if index is not None:
            split_codes[index].get(code, []).remove(ub_code)
        return index, code

    def __init__(self, format, code_set_path: str):
        self.format = format
        with open(code_set_path, "r") as codes_file:
            self.codes: CodeCollection = json.loads(codes_file.read())
        self.code_types = list(self.codes.keys())

    def flat_codes_by_type(self, code_type: str):
        code_specs: list[CodeSpec] = []
        for code in self.codes[code_type]:
            code_specs.append(
                {
                    "code_type": code_type,
                    "code": code,
                    "value": self.codes[code_type][code].get("value", ""),
                    "regex": self.codes[code_type][code].get("regex", ""),
                    "description": self.codes[code_type][code].get("description", ""),
                }
            )
        return code_specs

    def find_matching_full_codes_by_type(self, codes: list[str], code_type: str) -> CodeSpecMatches:
        code_spec_matches = {}
        for code_spec in self.flat_codes_by_type(code_type):
            code_spec_matches.update(CodeSet.match_bracketed(codes, code_spec))
        return code_spec_matches

    def find_matching_full_codes(self, codes: list[str], code_types: list[str]) -> CodeSpecMatches:
        code_spec_matches = {}
        for code_type in code_types:
            code_spec_matches.update(self.find_matching_full_codes_by_type(codes, code_type))
        return code_spec_matches

    def find_matching_split_codes_by_type(self, split_codes: SplitCodes, code_type: str) -> CodeSpecMatches:
        code_spec_matches = {}
        for code_spec in self.flat_codes_by_type(code_type):
            ub_code = "".join([char for char in code_spec["code"] if char not in "() "])
            index, code = CodeSet.match_split_codes_with_unbracketed_code(split_codes, ub_code)
            if index is not None and code:
                if code not in code_spec_matches:
                    code_spec_matches[code] = []
                code_spec_matches[code].append(code_spec)
        return code_spec_matches

    def find_matching_split_codes(self, split_codes: SplitCodes) -> CodeSpecMatches:
        code_spec_matches = {}
        for code_type in MULTI_CODE_TYPES:
            code_spec_matches.update(self.find_matching_split_codes_by_type(split_codes, code_type))
        return code_spec_matches

    def find_matching_multi_codes(self, codes: list[str]) -> CodeSpecMatches:
        split_codes = [code for code in (CodeSet.try_as_multi_code(code) for code in codes) if code is not None]
        return self.find_matching_split_codes(split_codes)

    def match_codes(self, codes: list[str]) -> CodeSpecMatches:
        code_spec_matches = self.find_matching_full_codes(codes, self.code_types)
        code_spec_matches.update(self.find_matching_multi_codes(codes))
        return code_spec_matches

    def match_format(self, codes: list[str]) -> bool:
        """
        Uses the provided (region) code to determine whether the filename
        format matches the instance's code set convention.
        """
        for region_code in self.flat_codes_by_type("region"):
            for code in codes:
                if self.match_bracketed(code, region_code):
                    return True
        return False


class CodeSetManager(object):
    def __init__(self, codesets: list[CodeSet]):
        self.codesets = []
        for codeset in codesets:
            self.codesets.append(codeset)

    def check_format(self, codes: list[str]) -> Optional[str]:
        for codeset in self.codesets:
            if codeset.match_format(codes):
                return codeset.format
        return None

    def get_set_by_format(self, format):
        for codeset in self.codesets:
            if format == codeset.format:
                return codeset
        return None


tosec_code_set = CodeSet("tosec", os.path.join(JSON_PATH, "tosec.json"))
goodtools_code_set = CodeSet("goodtools", os.path.join(JSON_PATH, "goodtools.json"))
nointro_code_set = CodeSet("no_intro", os.path.join(JSON_PATH, "nointro.json"))

manager = CodeSetManager([tosec_code_set, goodtools_code_set, nointro_code_set])
