#!/usr/bin/env python3

"""
For now, this only validates the MAME source files
"""

import os
import bz2
import multiprocessing
import xml.etree.ElementTree as ET

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
MAME_SOURCES = os.path.join(SCRIPT_PATH, "mame_db_source", "dats")
FBA_SOURCES = os.path.join(SCRIPT_PATH, "fba_db_source", "dats")
MAME_DATS = [os.path.join(MAME_SOURCES, file) for file in os.listdir(MAME_SOURCES)]


def get_source_contents(path: str) -> str:
    with bz2.open(path, "r") as bzip_file:
        return bzip_file.read().decode("utf-8")


def get_source_root(dat_contents: str):
    try:
        root = ET.fromstring(dat_contents)
        return root
    except Exception:
        print("Error")


def process_dat(path: str) -> None:
    print(os.path.basename(path))
    source = get_source_contents(path)
    root = get_source_root(source)
    if not root:
        print("Read fail, ", path)
    if root and root.tag not in ["mame", "datafile"]:
        print("Tag fail, ", path, root)


def process_files():
    with multiprocessing.Pool(8) as pool:
        pool.map(process_dat, MAME_DATS)


if __name__ == "__main__":
    process_files()
