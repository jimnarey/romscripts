#!/usr/bin/env python3

import re

# from pathlib import Path


# REGION_MATCHES = {
#     'US': ['W', 'JUE', 'UE', 'JU', 'U'],
#     'Europe': ['W', 'JUE', 'UE', 'JE', 'E', 'UK'],
#     'Japan': ['W', 'JUE', 'JU', 'JE', 'J']
# }

type_regexes = {
    "hack": re.compile("^%s[0-9]{0,2}" % "h"),
    "trainer": re.compile("^%s[0-9]{0,2}" % "t"),
    "translation": re.compile("^T ?[+-]{1}.*"),
}

# alt_dump_regexes = (re.compile("^%s[0-9]{0,2}" % code) for code in ["a", "o", "f"])

non_region_paren_codes = ("SN", "NP", "GC", "MB", "PD")


def contains_digit(value):
    for char in value:
        if char.isdigit():
            return True
    return False


class StructuredRomName:
    def __init__(self, filename):
        self.filename = filename
        self.paren_codes = re.findall("\((.*?)\)", self.filename)
        self.sq_bracket_codes = re.findall("\[(.*?)\]", self.filename)
        self.region = "Unk"
        self.is_pre_release = False
        self.is_demo = False
        self.is_unlicensed = False
        self.is_translation = False
        self.is_hack_game = False
        self.is_hacked_dump = False
        self.is_trainer = False
        self.is_pd = False
        # self._set_region()
        self._set_types()

    # def _set_region(self):
    #     poss_matches = [code for code in self.paren_codes if len(code) < 4 and not contains_digit(code) and code.isupper() and code not in non_region_paren_codes]
    #     if len(poss_matches) == 1:
    #         self.region = poss_matches[0]
    #     elif '1' in self.paren_codes:
    #         self.region = 'JK'
    #     elif '4' in self.paren_codes:
    #         self.region = 'UB'

    def _set_types(self):
        for code in self.paren_codes:
            if "hack" in code.lower():
                self.is_hack_game = True
            if [
                sub
                for sub in ("beta", "alpha", "preview", "pre-release", "proto")
                if sub in code.lower()
            ]:
                self.is_pre_release = True
            if [sub for sub in ("demo", "sample") if sub in code.lower()]:
                self.is_demo = True
            if "unl" in code.lower():
                self.is_unlicensed = True
            if "pd" in code.lower():
                self.is_pd = True
        for code in self.sq_bracket_codes:
            if re.match(type_regexes["hack"], code):
                self.is_hacked_dump = True
            if re.match(type_regexes["trainer"], code):
                self.is_trainer = True
            if re.match(type_regexes["translation"], code):
                # print(code)
                self.is_translation = True

    def is_commercial(self):
        if True in (
            self.is_hacked_dump,
            self.is_hack_game,
            self.is_pre_release,
            self.is_unlicensed,
            self.is_pd,
        ):
            return False
        return True
