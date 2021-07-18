import os
from .file_renamer import FileRenamer

class RenameRoot:

    def __init__(self, dir_path, file_max_length):
        self.dir_path = dir_path
        self.file_max_length = file_max_length
        self.files = []
        self.get_files(dir_path)
        self.name_length_summary = []

    def get_files(self, dir_path):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                self.files.append(FileRenamer(os.path.join(
                    root, file), self.file_max_length))

    def get_changes(self):
        changed_names = []
        for file in self.files:
            if file.base_name != file.new_base_name:
                changed_names.append('{0}: {1} chars -> {2}: {3} chars\n'.format(file.base_name,
                                                                                 file.orig_length(),
                                                                                 file.new_base_name,
                                                                                 file.current_length()))
        return changed_names

    def get_long_files(self):
        long_files = []
        for file in self.files:
            if file.current_length() > file.max_length:
                long_files.append('{0}\n'.format(file.new_base_name))
        return long_files

    def get_truncated_files(self):
        truncated_files = []
        for file in self.files:
            if file.truncated:
                truncated_files.append('{0}\n'.format(file.new_base_name))
        return truncated_files

    def replace_in_file(self, file, replace_spec):
        file.replace_sub_string(
            replace_spec['pattern'],
            replace_spec['replacement'],
            replace_spec['caseSensitive'])

    def process_actions(self, rename_prefs):
        for file in self.files:
            if rename_prefs['illegalStrings']:
                file.replace_many(rename_prefs['illegalStrings'], '', True)
            if rename_prefs['replaceInAll']:
                for replace_spec in rename_prefs['replaceInAll']:
                    self.replace_in_file(file, replace_spec)
            if rename_prefs['removeBracketedText']:
                file.remove_bracketed()
            if rename_prefs['shortenNames']:
                file.ordered_shorten(rename_prefs['replaceToShorten'], rename_prefs['subtitleCompressSpec'])
            if rename_prefs['executeRenames']:
                file.rename()
