import os
import re
import py7zr
# from py7zr import Bad7zFile
from .file_entry import FileEntry

# TO DO - change cross_ref etc to catch translations

class FileSet:

    def __init__(self, file_path):
        self.file_path = file_path
        self.all_entries = []
        self.ok_dumps = []
        self.ok_ro = []
        self.matches = []
        self.best_match = None

    def name(self):
        return os.path.basename(self.file_path)

    def populate_entries(self):
        try:
            with py7zr.SevenZipFile(self.file_path, mode='r') as arch:
                self.all_entries = [FileEntry(entry)
                                    for entry in arch.getnames()]
        except (OSError, py7zr.Bad7zFile):
            print(self.file_path)
            return False
        return True

    def _get_ok_dumps(self, ok_dump_regexes):
        for entry in self.all_entries:
            for code in entry.dump_codes:
                if any(re.match(regex, code) for regex in ok_dump_regexes):
                    self.ok_dumps.append(entry)
            if not entry.dump_codes:
                self.ok_dumps.append(entry)

    def _get_ok_ro(self, ok_ro_list):
        for entry in self.all_entries:
            for code in ok_ro_list:
                if code in entry.ro_codes:
                    self.ok_ro.append(entry)

    def _cross_ref_matches(self):
        self.matches = [
            entry for entry in self.ok_ro if entry in self.ok_dumps]

    def get_matches(self, ok_dump_regexes, ok_ro_list):
        self._get_ok_dumps(ok_dump_regexes)
        self._get_ok_ro(ok_ro_list)
        self._cross_ref_matches()

    def num_matches(self):
        return len(self.matches) if self.matches else 0

    # Use set
    def all_codes(self, code_type):
        codes = []
        for entry in self.all_entries:
            for code in entry.all_codes(code_type):
                if code not in codes:
                    codes.append(code)
        return codes

    def summary(self):
        return '{archive} - DM: {num_dm} - ROM: {num_rom} - BOTH: {num_both}\n'.format(
            archive=self.name(),
            num_dm=len(self.ok_dumps),
            num_rom=len(self.ok_ro),
            num_both=self.num_matches())

    def extract_entry(self, target_path, entry_name):
        with py7zr.SevenZipFile(self.file_path, 'r') as arch:
            arch.extract(path=target_path, targets=[entry_name])

    def extract_best_match(self, target_path):
        print('Extracting: {0}'.format(self.matches[0].entry_name))
        self.extract_entry(target_path, self.matches[0].entry_name)
