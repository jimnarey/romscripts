#!/usr/bin/env python3

import os
import re
import py7zr  # type: ignore

# import json
# import shutil
# from pathlib import Path

# from optparse import OptionParser
import argparse

# from pprint import pprint


REGION_MATCHES = {
    "US": ["W", "JUE", "UE", "JU", "U"],
    "Europe": ["W", "JUE", "UE", "JE", "E", "UK"],
    "Japan": ["W", "JUE", "JU", "JE", "J"],
}

type_regexes = {
    "hack": re.compile("^%s[0-9]{0,2}" % "h"),
    "trainer": re.compile("^%s[0-9]{0,2}" % "t"),
    "translation": re.compile("^T ?[+-]{1}.*"),
}

alt_dump_regexes = (
    re.compile("^%s[0-9]{0,2}" % code) for code in ["a", "o", "f"]
)

non_region_paren_codes = ("SN", "NP", "GC", "MB", "PD")


def contains_digit(value):
    for char in value:
        if char.isdigit():
            return True
    return False


class Rom:
    def __init__(self, rom_name):
        self.rom_name = rom_name
        # self.parent_archive = parent_archive
        self.paren_codes = re.findall("\((.*?)\)", self.rom_name)
        self.sq_bracket_codes = re.findall("\[(.*?)\]", self.rom_name)
        self.region = "Unk"
        self.is_beta = False
        self.is_unlicensed = False
        self.is_translation = False
        self.is_hack_game = False
        self.is_hacked_dump = False
        self.is_trainer = False
        self.is_pd = False
        self._set_region()
        self._set_types()

    def _set_region(self):
        poss_matches = [
            code
            for code in self.paren_codes
            if len(code) < 4
            and not contains_digit(code)
            and code.isupper()
            and code not in non_region_paren_codes
        ]
        if len(poss_matches) == 1:
            self.region = poss_matches[0]
        elif "1" in self.paren_codes:
            self.region = "JK"
        elif "4" in self.paren_codes:
            self.region = "UB"

    def _set_types(self):
        for code in self.paren_codes:
            if "hack" in code.lower():
                self.is_hack_game = True
            if "beta" in code.lower():
                self.is_beta = True
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
            self.is_beta,
            self.is_unlicensed,
            self.is_pd,
        ):
            return False
        return True


class MultiRomArchive:
    def __init__(self, file_path):
        self.file_path = file_path
        self.valid = False
        self.roms = []
        self.get_roms()
        self.regions = {rom.region for rom in self.roms}

    def get_roms(self):
        try:
            with py7zr.SevenZipFile(self.file_path, mode="r") as _7z_archive:
                self.roms = [
                    Rom(rom_name) for rom_name in _7z_archive.getnames()
                ]
                self.valid = True
        except (OSError, py7zr.Bad7zFile) as e:
            print("Error opening archive {0}: {1}".format(self.file_path, e))

    def get_best_from_region(self, region):
        region_matches = [
            rom
            for rom in self.roms
            if rom.region == region and rom.is_commercial()
        ]
        for rom in region_matches:
            if "!" in rom.sq_bracket_codes:
                return rom
            if not rom.sq_bracket_codes:
                return rom
            for alt_dump_regex in alt_dump_regexes:
                for code in rom.sq_bracket_codes:
                    if re.match(alt_dump_regex, code):
                        return rom
        return None

    def get_hacks(self):
        return [rom for rom in self.roms if rom.is_hack_game is True]

    def get_translations(self):
        return [rom for rom in self.roms if rom.is_translation is True]

    def get_trainers(self):
        return [rom for rom in self.roms if rom.is_trainer is True]

    def extract_entry(self, target_path, entry_name):
        with py7zr.SevenZipFile(self.file_path, "r") as arch:
            arch.extract(path=target_path, targets=[entry_name])


class SevenZArchiveDir:
    def __init__(self, path):
        self.path = path
        self.archives = []
        self.regions = set()
        self.get_archives()
        self.get_regions()

    def get_archives(self):
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if py7zr.is_7zfile(os.path.join(root, file)):
                    self.archives.append(
                        MultiRomArchive(os.path.join(root, file))
                    )

    def get_regions(self):
        for archive in self.archives:
            if archive.valid is True:
                for region in archive.regions:
                    self.regions.add(region)


# TODO - add option to (not) include translations, hacks etc
# TODO - add option to merge multi-region games
# TODO - consider not sorting into dirs to deal with multi-region games


def main(input_dir, output_dir):
    archive_dir = SevenZArchiveDir(input_dir)
    romset = {"trainers": [], "translations": [], "hacks": []}
    for region in archive_dir.regions:
        romset[region] = []

    for archive in archive_dir.archives:
        for rom in archive.get_trainers():
            archive.extract_entry(
                os.path.join(output_dir, "Trainers"), rom.rom_name
            )
        for rom in archive.get_hacks():
            archive.extract_entry(
                os.path.join(output_dir, "Hacks"), rom.rom_name
            )
        for rom in archive.get_translations():
            archive.extract_entry(
                os.path.join(output_dir, "Translations"), rom.rom_name
            )
        for region in archive_dir.regions:
            best_region_match = archive.get_best_from_region(region)
            if best_region_match:
                archive.extract_entry(
                    os.path.join(output_dir, region),
                    best_region_match.rom_name,
                )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="")
    parser.add_argument(
        "-i", "--input_dir", dest="input_dir", help="Input directory"
    )
    parser.add_argument(
        "-o", "--output_dir", dest="output_dir", help="Output directory"
    )
    args = vars(parser.parse_args())
    main(input_dir=args["input_dir"], output_dir=args["output_dir"])
