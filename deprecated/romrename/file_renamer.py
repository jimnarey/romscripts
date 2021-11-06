import os
import re

# TO DO - rationalise compress_subtitle
# TO DO - allow separate target dir

class FileRenamer:

    def __init__(self, file_path, max_length):
        self.full_path = file_path
        self.max_length = max_length
        self.dir_path, self.base_name = os.path.split(file_path)
        self.new_base_name = self.base_name
        self.truncated = False


    # TO DO - split into literal and regex private methods
    def replace_sub_string(self, sub_string, replacement, case_sensitive=True):
        if case_sensitive:
            self.new_base_name = self.new_base_name.replace(
                sub_string, replacement)  # No if check for substring
        else:
            redata = re.compile(re.escape(sub_string), re.IGNORECASE)
            self.new_base_name = redata.sub(replacement, self.new_base_name)
        self.cut_whitespace()

    def replace_many(self, sub_strings, replacement, case_sensitive):
        for sub_string in sub_strings:
            self.replace_sub_string(
                sub_string, replacement, case_sensitive=case_sensitive)

    def remove_bracketed(self):
        self.new_base_name = re.sub('[\(\[].*?[\)\]]', '', self.new_base_name)
        self.cut_whitespace()

    # Consider splitting, though safe this way
    def cut_whitespace(self):
        self.new_base_name = ' '.join(self.new_base_name.split())
        name_stem, name_ext = os.path.splitext(self.new_base_name)
        self.new_base_name = '{0}{1}'.format(name_stem.rstrip(), name_ext)

    def apply_shorten_replacements(self, replace_specs):
        for replace_spec in replace_specs:
            if self.current_length() > self.max_length:
                self.replace_sub_string(
                    replace_spec['pattern'],
                    replace_spec['replacement'],
                    replace_spec['caseSensitive'])
            else:
                break

    def compress_subtitle(self, compress_spec):
        if compress_spec['subtitleMark'] in self.new_base_name:
            name_stem, name_ext = os.path.splitext(self.new_base_name)
            # Find the last occurance of text meeting the specified regex (e.g. '_Dxx')
            # TO DO - allow multiple suffix types (regexes)
            preserve_text = ''
            if compress_spec['preserveSuffix']:
                preserve_text_occurances = re.findall(
                    compress_spec['preserveSuffix'], name_stem)
                if preserve_text_occurances:
                    preserve_text = preserve_text_occurances[-1]
                    # Remove last occurance of found substring from name stem
                    name_stem = ''.join(name_stem.rsplit(preserve_text, 1))
            subtitle = name_stem.split(compress_spec['subtitleMark'])[-1]
            name_stem = ''.join(name_stem.rsplit(subtitle, 1))
            # Replace full subtitle with abbreviation
            subtitle = ''.join(char[0] for char in subtitle.split())
            self.new_base_name = '{0}{1}{2}{3}'.format(
                name_stem, subtitle, preserve_text, name_ext)

    def ordered_shorten(self, replace_specs, compress_spec):
        self.apply_shorten_replacements(replace_specs)
        if self.current_length() > self.max_length:
            self.compress_subtitle(compress_spec)
        if self.current_length() > self.max_length:
            self.truncate()

    def truncate(self):
        name_stem, name_ext = os.path.splitext(self.new_base_name)
        if len(name_stem) > self.max_length - len(name_ext):
            self.new_base_name = '{0}{1}'.format(
                self.new_base_name[:self.max_length - len(name_ext)], name_ext)
            self.cut_whitespace()
            self.truncated = True

    def orig_length(self):
        return len(self.base_name)

    def current_length(self):
        return len(self.new_base_name)

    def new_file_path(self):
        return os.path.join(self.dir_path, self.new_base_name)

    def rename(self):
        os.rename(os.path.join(self.dir_path, self.base_name),
                  os.path.join(self.dir_path, self.new_base_name))
