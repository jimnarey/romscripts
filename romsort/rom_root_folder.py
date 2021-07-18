
import os
from .file_set import FileSet

# TO DO - Clean up summary maker
# TO DO - zip output files

class RomRootFolder:

    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.file_paths = []
        self.valid_archives = []
        self.invalid_file_paths = []
        self._get_file_paths()
        self._get_archives()

    def _get_file_paths(self):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                self.file_paths.append(os.path.join(root, file))

    def _get_archives(self):
        for file_path in self.file_paths:
            current_file = FileSet(file_path)
            if current_file.populate_entries() is True:
                self.valid_archives.append(current_file)
            else:
                self.invalid_file_paths.append(file_path)

    def all_codes(self, code_type):
        codes = []
        for arch in self.valid_archives:
            for code in arch.all_codes(code_type):
                if code not in codes:
                    codes.append(code)
        return codes

    def sort(self, ok_dump_regexes, ok_ro_codes):
        for arch in self.valid_archives:
            arch.get_matches(ok_dump_regexes, ok_ro_codes)

    def generate_summary(self):
        has_matches = 0
        no_matches = 0
        has_matches_lines = []
        no_matches_lines = []
        for arch in self.valid_archives:
            if arch.num_matches():
                has_matches += 1
                has_matches_lines.append(arch.summary())
                has_matches_lines.append(arch.matches[0].entry_name)
                has_matches_lines.append('\n\n')
            else:
                no_matches += 1
                no_matches_lines.append(arch.summary())
                for entry in arch.all_entries:
                    no_matches_lines.append(
                        '{entry}\n'.format(entry=entry.entry_name))
                no_matches_lines.append('\n')
        headlines = [
            'Total archives: {0}\n'.format(len(self.valid_archives)),
            'With matches: {0}\n'.format(has_matches),
            'No matches: {0}\n'.format(no_matches), '\n'
            ]
        return headlines + has_matches_lines + no_matches_lines

    def write_summary(self, summary_file_path):
        with open(summary_file_path, 'w') as summary_file:
            summary_file.writelines(self.generate_summary())

    def extract_matches(self, target_path):
        for arch in self.valid_archives:
            if arch.matches:
                arch.extract_best_match(target_path)
