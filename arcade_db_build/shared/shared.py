#!/usr/bin/env python3

from typing import Optional
import os
import re
import bz2
import xml.etree.ElementTree as ET

PARENT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAME_SOURCES = os.path.join(PARENT_PATH, "mame_db_source", "dats")
FBA_SOURCES = os.path.join(PARENT_PATH, "fba_db_source", "dats")
MAME_DATS = [os.path.join(MAME_SOURCES, file) for file in os.listdir(MAME_SOURCES)]


def extract_mame_version(filename):
    version = filename.replace("MAME ", "").replace(".xml.bz2", "")
    version = re.sub(r"\D", "", version)
    return float(version) if version else 0


def get_xml_contents(path: str) -> str:
    with bz2.open(path, "r") as bzip_file:
        return bzip_file.read().decode("utf-8")


def get_dat_root(path: str) -> Optional[ET.Element]:
    try:
        contents = get_xml_contents(path)
        root = ET.fromstring(contents)
    except Exception as e:
        print("Error: ", type(e), path)
        return None
    return root


SORTED_DATS = {
    "mame": sorted(MAME_DATS, key=extract_mame_version),
}
