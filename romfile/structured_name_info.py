import functools

import romcodes


class StructutedRomFileNameInfo(object):
    def __init__(self, codes: list[str]) -> None:
        self.codes = codes

    @functools.cached_property
    def format(self):
        return romcodes.manager.check_format(self.codes)
