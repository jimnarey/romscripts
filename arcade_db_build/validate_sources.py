#!/usr/bin/env python3

"""
For now, this only validates the MAME source files
"""

import os
import multiprocessing
import xml.etree.ElementTree as ET
import shared


def validate_root_tag(root: ET.Element) -> None:
    if root.tag not in ["mame", "datafile"]:
        print("Unrecognised root tag: ", root)


def validate_num_headers(path: str, element_tags: list[str]) -> None:
    if element_tags.count("header") > 1:
        print("Multiple header elements: ", path)


def validate_tag_names(path: str, element_tags: list[str]) -> None:
    element_tags_no_header = [element_tag for element_tag in element_tags if element_tag != "header"]
    element_tags_set = set(element_tags_no_header)
    if len(element_tags_set) > 1:
        print("Multiple tag types: ", path, element_tags_set)
    if et := element_tags_set.pop() not in ("game", "machine"):
        print("Unrecognised element tag: ", path, et)


def process_dat(path: str) -> None:
    print(os.path.basename(path))
    source = shared.get_source_contents(path)
    try:
        root = shared.get_source_root(source)
    except Exception as e:
        print("Error: ", type(e), path)
    if root:
        validate_root_tag(root)
        element_tags = [element.tag for element in root]
        validate_num_headers(path, element_tags)
        validate_tag_names(path, element_tags)


def process_files():
    with multiprocessing.Pool(8) as pool:
        pool.map(process_dat, shared.MAME_DATS)


if __name__ == "__main__":
    process_files()
    # df_dat_path = "/home/jimnarey/projects/romscripts/arcade_db_build/mame_db_source/dats/MAME 0.53.dat.bz2"
    # m_dat_path = "/home/jimnarey/projects/romscripts/arcade_db_build/mame_db_source/dats/MAME 0.141.xml.bz2"
    # d = shared.get_source_root(shared.get_source_contents(df_dat_path))
    # m = shared.get_source_root(shared.get_source_contents(m_dat_path))
