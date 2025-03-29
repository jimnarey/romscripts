#!/usr/bin/env python3

from typing import Optional
import os
import re
import bz2
from lxml import etree as ET

from .utils import time_execution

PARENT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKDIR = os.path.join(PARENT_PATH, "sources", "working")

MAME_DAT_DIR = os.path.join(PARENT_PATH, "sources", "mame", "dats")
MAME_REORDERED_DAT_DIR = os.path.join(PARENT_PATH, "sources", "mame", "dats_reordered")

MAME_DATS = [os.path.join(MAME_DAT_DIR, file) for file in os.listdir(MAME_DAT_DIR)]
MAME_REORDERED_DATS = [os.path.join(MAME_REORDERED_DAT_DIR, file) for file in os.listdir(MAME_REORDERED_DAT_DIR)]

# MAME_DATS_WORKING = [
#     os.path.join(MAME_SOURCES_WORKING, file) for file in os.listdir(MAME_SOURCES_WORKING) if file.endswith(".bz2")
# ]

FBA_DAT_DIR = os.path.join(PARENT_PATH, "sources", "fba", "dats")

PARSER = ET.XMLParser(remove_comments=True)


def extract_mame_version(filename):
    version = filename.replace("MAME ", "").replace(".xml.bz2", "")
    version = re.sub(r"\D", "", version)
    return float(version) if version else 0


def get_xml_contents(path: str) -> bytes:
    with bz2.open(path, "rb") as bzip_file:
        return bzip_file.read()


@time_execution("Get DAT root")
def get_dat_root(path: str, concurrent: bool = False) -> Optional[ET._Element]:
    print(f"Getting root from {path}")
    parser = PARSER if not concurrent else ET.XMLParser(remove_comments=True)
    contents = get_xml_contents(path)
    root = ET.fromstring(contents, parser)
    return root


BUILD_DATS = {
    "mame": sorted(MAME_REORDERED_DATS, key=extract_mame_version),
}
