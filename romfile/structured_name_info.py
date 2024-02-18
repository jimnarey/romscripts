import functools

from romcodes import CodeSetCollection


class StructuredRomFileName(object):
    def __init__(self, codes: list[str], codeset_collection: CodeSetCollection) -> None:
        self.codes = codes
        self.codeset_collection = codeset_collection

    @functools.cached_property
    def format(self):
        pass
