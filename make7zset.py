#!/usr/bin/env python3

import os
import re
import py7zr
import json
import shutil
from pathlib import Path
# from optparse import OptionParser
import argparse
from pprint import pprint

# from py7zr import Bad7zFile

# TO DO - change cross_ref etc to catch translations

# TO DO - prune duplicates in betas

# TO DO - progress output (it's very slow)

REGION_MATCHES = {
    'US': ['W', 'JUE', 'UE', 'JU', 'U'],
    'Europe': ['W', 'JUE', 'UE', 'JE', 'E', 'UK'],
    'Japan': ['W', 'JUE', 'JU', 'JE', 'J']
}







# class RomRootFolder:
#
#     def __init__(self, dir_path):
#         self.dir_path = dir_path
#         self.file_paths = []
#         self.valid_7z_archive_paths = []
#         self.invalid_archive_paths = []
#         self._get_file_paths()
#         self._get_archives()

    # def _get_file_paths(self):
    #     for root, dirs, files in os.walk(self.dir_path):
    #         for file in files:
    #             self.file_paths.append(os.path.join(root, file))

    # def _get_archives(self):
    #     for file_path in self.file_paths:
    #         current_file = MultiRomArchive(file_path)
    #         if current_file.populate_entries() is True:
    #             self.valid_7z_archive_paths.append(current_file)
    #         else:
    #             self.invalid_archive_paths.append(file_path)

#     def all_codes(self, code_type):
#         codes = []
#         for arch in self.valid_7z_archive_paths:
#             for code in arch.get_all_codes(code_type):
#                 if code not in codes:
#                     codes.append(code)
#         return codes
#
#     def make_selections(self, regions):
#         for archive in self.valid_7z_archive_paths:
#             archive.filter_others()
#             for region in regions:
#                 archive.filter_by_region(region)
#                 archive.prune_region_selection(region)
#             # pprint(archive.selections['Hacks'])
#             # print(len(archive.selections['Trainers']))
#             pprint(archive.selections)
#
#     def extract_matches(self, target_path):
#         for arch in self.valid_7z_archive_paths:
#             arch.extract_all(target_path)
#
#
#
#
#
# def get_dump_code_regexes(ok_dump_codes):
#     regexes = []
#     for code in ok_dump_codes:
#         # regexes.append(re.compile("^[%s][0-9]{0,2}" % code))
#         regexes.append(re.compile("^%s[0-9]{0,2}" % code))
#     return regexes
#
#
# def process(prefs):
#     root = RomRootFolder(prefs['rootDir'])
#     root.make_selections(['US', 'Europe', 'Japan'])
#     root.extract_matches(prefs['targetDir'])
#     if prefs['writeSummary'] is True:
#         pass
#     if prefs['writeFiles'] is True:
#         if not os.path.isdir(prefs['targetDir']):
#             target_path = Path(prefs['targetDir'])
#             target_path.mkdir(parents=True, exist_ok=True)
#         root.extract_matches(prefs['targetDir'])


# class ArchivedRom:
#
#     def __str__(self):
#         return self.entry_name
#
#     def __repr__(self):
#         return self.entry_name
#
#     def __init__(self, entry_name):
#         self.entry_name = entry_name
#         self.other_codes = []
#         self.dump_codes = []
#         self._populate_codes()
#
#     def _populate_codes(self):
#         self.other_codes = re.findall("\((.*?)\)", self.entry_name)
#         self.dump_codes = re.findall("\[(.*?)\]", self.entry_name)
#
#     def get_all_codes(self, code_type):
#         if code_type == 'dump':
#             return self.dump_codes
#         elif code_type == 'other':
#             return self.other_codes
#         return None


#
# class OldMultiRomArchive:
#
#
#     def __init__(self, file_path):
#         self.file_path = file_path
#         self.contents = []
#         self.selections = {}
#
#     def name(self):
#         return os.path.basename(self.file_path)
#
#     def populate_entries(self):
#         try:
#             with py7zr.SevenZipFile(self.file_path, mode='r') as arch:
#                 self.contents = [ArchivedRom(entry)
#                                  for entry in arch.getnames()]
#         except (OSError, py7zr.Bad7zFile):
#             print(self.file_path)
#             return False
#         return True
#
#     def filter_by_region(self, region):
#         selection = set()
#         for match in REGION_MATCHES.get(region):
#             for rom in self.contents:
#                 if match in rom.other_codes:
#                     selection.add(rom)
#         self.selections[region] = selection
#
#     def prune_region_selection(self, region):
#         for rom in self.selections[region]:
#             if '!' in rom.dump_codes:
#                 self.selections[region] = [rom]
#                 return
#         for rom in self.selections[region]:
#             if len(rom.dump_codes) == 0:
#                 self.selections[region] = [rom]
#                 return
#         for rom in self.selections[region]:
#             for code in rom.dump_codes:
#                 if any(re.match(regex, code) for regex in MultiRomArchive.alt_dump_regexes):
#                     self.selections[region] = [rom]
#                     return
#
#     def filter_others(self):
#         self.selections['Hacks'] = set()
#         self.selections['Trainers'] = set()
#         self.selections['Translations'] = set()
#         self.selections['Betas'] = set()
#         for rom in self.contents:
#             for code in rom.other_codes:
#                 if 'hack' in code.lower():
#                     self.selections['Hacks'].add(rom)
#                 if 'beta' in code.lower():
#                     self.selections['Betas'].add(rom)
#             for code in rom.dump_codes:
#                 for cat in ['Hacks', 'Trainers', 'Translations']:
#                     if re.match(MultiRomArchive.category_regexes[cat], code):
#                         self.selections[cat].add(rom)
#
#     def get_all_codes(self, code_type):
#         codes = []
#         for entry in self.contents:
#             for code in entry.get_all_codes(code_type):
#                 if code not in codes:
#                     codes.append(code)
#         return codes
#
#     def extract_entry(self, target_path, entry_name):
#         with py7zr.SevenZipFile(self.file_path, 'r') as arch:
#             arch.extract(path=target_path, targets=[entry_name])
#
#     def extract_all(self, target_root):
#         extracted = {}
#         for key in self.selections:
#             target_path = os.path.join(target_root, key)
#             if not os.path.exists(target_path):
#                 os.makedirs(target_path)
#             for rom in self.selections[key]:
#                 if rom.entry_name in extracted:
#                     shutil.copyfile(os.path.join(extracted[rom.entry_name], rom.entry_name), os.path.join(target_path, rom.entry_name))
#                 else:
#                     self.extract_entry(target_path, rom.entry_name)
#                     extracted[rom.entry_name] = target_path


type_regexes = {
    'hack': re.compile("^%s[0-9]{0,2}" % 'h'),
    'trainer': re.compile("^%s[0-9]{0,2}" % 't'),
    'translation': re.compile("^T ?[+-]{1}.*")
}

alt_dump_regexes = [re.compile("^%s[0-9]{0,2}" % code) for code in ["a", "o", "f"]]

non_region_paren_codes = ('SN', 'NP', 'GC', 'MB', 'PD')

def contains_digit(value):
    for char in value:
        if char.isdigit():
            return True
    return False


class Rom:

    def __init__(self, rom_name):
        self.rom_name = rom_name
        self.paren_codes = re.findall("\((.*?)\)", self.rom_name)
        self.sq_bracket_codes = re.findall("\[(.*?)\]", self.rom_name)
        self._region = 'Unk'
        self.is_beta = False
        self.is_unlicensed = False
        self.is_translation = False
        self.is_hack = False
        self.is_trainer = False
        self.is_pd = False
        self._set_region()
        self._set_types()
        # if self._region == 'Unk':
        #     print(self.rom_name, self.paren_codes)

    def _set_region(self):
        poss_matches = [code for code in self.paren_codes if len(code) < 4 and not contains_digit(code) and code.isupper() and code not in non_region_paren_codes]
        if len(poss_matches) == 1:
            self._region = poss_matches[0]
        elif '1' in self.paren_codes:
            self._region = 'JK'
        elif '4' in self.paren_codes:
            self._region = 'UB'

    def _set_types(self):
        for code in self.paren_codes:
            if 'hack' in code.lower():
                self.is_hack = True
            if 'beta' in code.lower():
                self.is_beta = True
            if 'unl' in code.lower():
                self.is_unlicensed = True
            if 'pd' in code.lower():
                self.is_pd = True
        for code in self.sq_bracket_codes:
            if re.match(type_regexes['hack'], code):
                self.is_hack = True
            if re.match(type_regexes['trainer'], code):
                self.is_trainer = True
            if re.match(type_regexes['translation'], code):
                print(code)
                self.is_translation = True


class MultiRomArchive:

    def __init__(self, file_path):
        self.file_path = file_path
        self.roms = []
        self.get_roms()

    def get_roms(self):
        try:
            with py7zr.SevenZipFile(self.file_path, mode='r') as _7z_archive:
                self.roms = [Rom(rom_name) for rom_name in _7z_archive.getnames()]
        except (OSError, py7zr.Bad7zFile) as e:
            print('Error opening archive {0}: {1}'.format(self.file_path, e))


def get_7z_archives(input_dir):
    archives = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if py7zr.is_7zfile(os.path.join(root, file)):
                archives.append(MultiRomArchive(os.path.join(root, file)))
    return archives


def main(input_dir, output_dir):
    archives = get_7z_archives(input_dir)
    # print(archives)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='')
    parser.add_argument('-i', '--input_dir', dest='input_dir', help='Input directory')
    parser.add_argument('-o', '--output_dir', dest='output_dir', help='Output directory')
    args = vars(parser.parse_args())
    main(input_dir=args['input_dir'], output_dir=args['output_dir'])
