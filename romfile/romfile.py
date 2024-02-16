#!/usr/bin/env python3


class RomFile:
    def __init__(self, fileobj: str, filename: str) -> None:
        self.filename = filename
        self.fileobj = fileobj
