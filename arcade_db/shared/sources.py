#!/usr/bin/env python3

from typing import Optional
import os
import re
import bz2
from lxml import etree as ET

PARENT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Use the MAME DATs sorted with parents before clones
MAME_SOURCES = os.path.join(PARENT_PATH, "mame_db_source", "clones_sorted_dats")
MAME_SOURCES_WORKING = os.path.join(PARENT_PATH, "mame_db_source_working", "dats")
FBA_SOURCES = os.path.join(PARENT_PATH, "fba_db_source", "dats")
MAME_DATS = [os.path.join(MAME_SOURCES, file) for file in os.listdir(MAME_SOURCES)]
MAME_DATS_WORKING = [
    os.path.join(MAME_SOURCES_WORKING, file) for file in os.listdir(MAME_SOURCES_WORKING) if file.endswith(".bz2")
]

PARSER = ET.XMLParser(remove_comments=True)


def extract_mame_version(filename):
    version = filename.replace("MAME ", "").replace(".xml.bz2", "")
    version = re.sub(r"\D", "", version)
    return float(version) if version else 0


def get_xml_contents(path: str) -> bytes:
    with bz2.open(path, "rb") as bzip_file:
        return bzip_file.read()


def get_dat_root(path: str, concurrent: bool = False) -> Optional[ET._Element]:
    parser = PARSER if not concurrent else ET.XMLParser(remove_comments=True)
    contents = get_xml_contents(path)
    root = ET.fromstring(contents, parser)
    return root


SORTED_DATS = {
    "mame": sorted(MAME_DATS, key=extract_mame_version),
}
