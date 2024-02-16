import os
import re
import functools


class StructuredRomFileName(object):

    info_pattern = r"([(\[])([^)]+?)([)\]])"
    title_pattern = r'(\([^]]*\))*(\[[^]]*\])*([\w\+\~\@\!\#\$\%\^\&\*\;\,\'\""\?\-\.\-\s]+)'
    article_suffixes = (
        ", The",
        ", A",
        ", Die",
        ", De",
        ", La",
        ", Le",
        ", Les",
    )

    @staticmethod
    def get_base_name(name):
        return os.path.split(name)[-1]

    @staticmethod
    def restore_article(name):
        sub_strings = name.split(",")
        end_article = sub_strings.pop().strip()
        no_article = ",".join(reversed(sub_strings))
        return end_article + " " + no_article

    def __init__(self, name):
        self.original_name = self.get_base_name(name)
        self._codes_split = [
            match
            for match in re.findall(
                StructuredRomFileName.info_pattern, self.original_name
            )
        ]
        self.title = self.get_title()
        self.year = self.get_year()

    # Fallback in case title regex match fails
    def remove_codes_from_filename(self):
        name_no_codes = self.original_name
        for code in self._codes_split:
            name_no_codes = name_no_codes.replace(code, "").strip()
        return name_no_codes

    def get_title(self):
        m = re.match(StructuredRomFileName.title_pattern, self.original_name)
        if m:
            match = m.group(0).strip()
            if not match.endswith(StructuredRomFileName.article_suffixes):
                return match
            match = self.restore_article(match)
            return match
        return self.remove_codes_from_filename()

    @functools.cached_property
    def inner_codes(self):
        return [code[1] for code in self._codes_split]

    @functools.cached_property
    def codes(self):
        return ["".join(code) for code in self._codes_split]

    def get_year(self):
        for match in self.inner_codes:
            if match[:2] in ("19", "20"):
                return match[:4]
        return None
