#!/usr/bin/env python3

import os
import bz2
import xml.etree.ElementTree as ET

PARENT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAME_SOURCES = os.path.join(PARENT_PATH, "mame_db_source", "dats")
FBA_SOURCES = os.path.join(PARENT_PATH, "fba_db_source", "dats")
MAME_DATS = [os.path.join(MAME_SOURCES, file) for file in os.listdir(MAME_SOURCES)]


def get_source_contents(path: str) -> str:
    with bz2.open(path, "r") as bzip_file:
        return bzip_file.read().decode("utf-8")


def get_source_root(dat_contents: str) -> ET.Element:
    root = ET.fromstring(dat_contents)
    return root
