#!/usr/bin/env python3

from typing import Optional
import os
import re
import bz2
from lxml import etree as ET
import gc


PARENT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKDIR = os.path.join(PARENT_PATH, "sources", "working")

MAME_DAT_DIR = os.path.join(PARENT_PATH, "sources", "mame", "dats")

MAME_DATS = [os.path.join(MAME_DAT_DIR, file) for file in os.listdir(MAME_DAT_DIR)]

FBA_DAT_DIR = os.path.join(PARENT_PATH, "sources", "fba", "dats")

CSVS_DIR = os.path.join(PARENT_PATH, "csvs")


def extract_mame_version(filename):
    version = filename.replace("MAME ", "").replace(".xml.bz2", "")
    version = re.sub(r"\D", "", version)
    return float(version) if version else 0


def get_xml_contents(path: str) -> bytes:
    with bz2.open(path, "rb") as bzip_file:
        return bzip_file.read()


def get_dat_root(path: str) -> Optional[ET._Element]:
    print(f"Getting root from {path}")
    parser = ET.XMLParser(remove_comments=True)
    contents = get_xml_contents(path)
    root = ET.fromstring(contents, parser)
    del parser
    gc.collect()
    return root


BUILD_DATS = {
    "mame": MAME_DATS,
}

# BUILD_DATS = {
#     "mame": [dat for dat in MAME_DATS if "0.241" in dat],
# }
