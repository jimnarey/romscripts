#!/usr/bin/python3
from typing import Optional
import re
import json
import os
from typing import Generator

MULTI_CODE_TYPES = ["region"]
MULTI_CODE_DELIMITERS = "-,"

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_PATH, "data")

CodeCollection = dict[str, dict[str, dict]]
CodeSpec = dict[str, str]


class CodeSet(object):
    @staticmethod
    def get_code_parts(code: str, delimiter: str) -> list[str]:
        # Multi-codes don't come in []
        for char in "() ":
            code = code.replace(char, "")
        return code.split(delimiter)

    @staticmethod
    def has_multi_code_delimiter(code: str) -> bool:
        for char in MULTI_CODE_DELIMITERS:
            if char in code:
                return True
        return False

    @staticmethod
    def match_bracketed(code: str, code_spec: CodeSpec) -> Optional[CodeSpec]:
        if code == code_spec["code"]:
            return code_spec
        if code_spec["regex"]:
            if re.fullmatch(code_spec["regex"], code):
                return code_spec
        return None

    @staticmethod
    def match_unbracketed(
        code: str, code_spec: CodeSpec
    ) -> Optional[CodeSpec]:
        stripped_spec_code = code_spec["code"]
        for char in "()[]":
            stripped_spec_code = stripped_spec_code.replace(char, "")
        if code == stripped_spec_code:
            return code_spec
        return None

    def __init__(self, format, code_set_path: str):
        self.format = format
        with open(code_set_path, "r") as codes_file:
            self.codes: CodeCollection = json.loads(codes_file.read())

    def flat_all_codes(self) -> Generator[CodeSpec, None, None]:
        for code_type in self.codes.keys():
            for code_spec in self.flat_codes_by_type(code_type):
                yield code_spec

    def flat_codes_by_type(
        self, code_type: str
    ) -> Generator[CodeSpec, None, None]:
        for code in self.codes[code_type]:
            yield {
                "code_type": code_type,
                "code": code,
                "value": self.codes[code_type][code].get("value", ""),
                "regex": self.codes[code_type][code].get("regex", ""),
                "description": self.codes[code_type][code].get(
                    "description", ""
                ),
            }

    def find_matching_full_code(self, code: str) -> Optional[list[CodeSpec]]:
        """
        Searches all codes in the set for a full match with the provided code.
        """
        for code_spec in self.flat_all_codes():
            matched_code_spec = CodeSet.match_bracketed(code, code_spec)
            if matched_code_spec:
                return [matched_code_spec]
        return None

    def find_matching_multi_code_by_type(
        self, code: str, delim: str, code_type: str
    ) -> Optional[list[CodeSpec]]:
        matched_code_specs = []
        for code_spec in self.flat_codes_by_type(code_type):
            for sub_code in CodeSet.get_code_parts(code, delim):
                matched_code_spec = CodeSet.match_unbracketed(
                    sub_code, code_spec
                )
                if matched_code_spec:
                    matched_code_specs.append(matched_code_spec)
            # If len < 1 it's not a valid multi-code
            if len(matched_code_specs) > 1:
                return matched_code_specs
        return None

    def find_matching_multi_code(self, code: str) -> Optional[list[CodeSpec]]:
        """
        Only called if a full match has not been found.
        """
        if not CodeSet.has_multi_code_delimiter(code):
            return None
        for delim in MULTI_CODE_DELIMITERS:
            for code_type in MULTI_CODE_TYPES:
                matched_code_specs = self.find_matching_multi_code_by_type(
                    code, delim, code_type
                )
                if matched_code_specs:
                    return matched_code_specs
        return None

    def find_matching_code(self, code: str) -> Optional[list[CodeSpec]]:
        matched_code_spec = self.find_matching_full_code(code)
        if matched_code_spec:
            return matched_code_spec
        return None

    def match_format(self, code):
        """
        Uses the provided (region) code to determine whether the filename
        format matches the instance's code set convention.
        """
        for region_code in self.flat_codes_by_type("region"):
            if self.match_bracketed(code, region_code):
                return True
        return False


class CodeSetCollection(object):
    def __init__(self, codesets: list[CodeSet]):
        self.codesets = []
        for codeset in codesets:
            self.codesets.append(codeset)

    def check_format(self, codes):
        for code in codes:
            for codeset in self.codesets:
                if codeset.match_format(code):
                    return codeset.format
        return None

    def get_set_by_format(self, format):
        for codeset in self.codesets:
            if format == codeset.format:
                return codeset
        return None


tosec_code_set = CodeSet("tosec", os.path.join(JSON_PATH, "tosec.json"))
goodtools_code_set = CodeSet(
    "goodtools", os.path.join(JSON_PATH, "goodtools.json")
)
nointro_code_set = CodeSet("no_intro", os.path.join(JSON_PATH, "nointro.json"))

all_sets = CodeSetCollection(
    [tosec_code_set, goodtools_code_set, nointro_code_set]
)
