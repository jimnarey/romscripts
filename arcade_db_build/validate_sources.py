#!/usr/bin/env python3

"""
For now, this only validates the MAME source files
"""
from typing import Optional
import os
import multiprocessing
import xml.etree.ElementTree as ET
from shared import shared


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


def validate_tag_attributes(path: str, elements: list[ET.Element]) -> tuple[set, set, set, set]:
    game_attributes: set[str] = set()
    driver_attributes: set[str] = set()
    feature_attributes: set[str] = set()
    disk_attributes: set[str] = set()
    for element in elements:
        game_attributes.update(element.attrib.keys())
        driver_elements = [subelement for subelement in element if subelement.tag == "driver"]
        if len(driver_elements) > 1:
            print("Multiple driver elements: ", path)
        for driver_element in driver_elements:
            driver_attributes.update(driver_element.attrib.keys())
        feature_elements = [subelement for subelement in element if subelement.tag == "feature"]
        for feature_element in feature_elements:
            feature_attributes.update(feature_element.attrib.keys())
        disk_elements = [subelement for subelement in element if subelement.tag == "disk"]
        for disk_element in disk_elements:
            disk_attributes.update(disk_element.attrib.keys())
    return game_attributes, driver_attributes, feature_attributes, disk_attributes


def process_dat(path: str) -> Optional[tuple[set, set, set, set]]:
    print(os.path.basename(path))
    source = shared.get_source_contents(path)
    try:
        root = shared.get_source_root(source)
    except Exception as e:
        print("Error: ", type(e), path)
    if root:
        elements = [element for element in root]
        element_tags = [element.tag for element in root]
        validate_root_tag(root)
        validate_num_headers(path, element_tags)
        validate_tag_names(path, element_tags)
        return validate_tag_attributes(path, elements)
    return None


def process_files():
    with multiprocessing.Pool(8) as pool:
        results = pool.map(process_dat, shared.MAME_DATS)

    game_attributes = set()
    driver_attributes = set()
    feature_attributes = set()
    disk_attributes = set()

    for result in results:
        if result:
            game_attributes.update(result[0])
            driver_attributes.update(result[1])
            feature_attributes.update(result[2])
            disk_attributes.update(result[3])

    known_game_attributes = set(
        ["rom", "isdevice", "name", "cloneof", "runnable", "isbios", "sourcefile", "ismechanical", "romof", "sampleof"]
    )
    known_driver_attributes = set(
        [
            "palettesize",
            "hiscoresave",
            "requiresartwork",
            "unofficial",
            "good",
            "status",
            "graphic",
            "cocktailmode",
            "savestate",
            "protection",
            "emulation",
            "cocktail",
            "color",
            "nosoundhardware",
            "sound",
            "incomplete",
        ]
    )

    known_feature_attributes = set(["overall", "type", "status"])

    known_disk_attributes = set(
        ["sha1", "optional", "index", "writable", "region", "md5", "name", "status", "writeable", "merge"]
    )

    if not game_attributes == known_game_attributes:
        print("Unrecognised game attributes: ", game_attributes - known_game_attributes)
    if not driver_attributes == known_driver_attributes:
        print("Unrecognised driver attributes: ", driver_attributes - known_driver_attributes)
    if not feature_attributes == known_feature_attributes:
        print("Unrecognised feature attributes: ", feature_attributes - known_feature_attributes)
    if not disk_attributes == known_disk_attributes:
        print("Unrecognised disk attributes: ", disk_attributes - known_disk_attributes)


if __name__ == "__main__":
    process_files()
