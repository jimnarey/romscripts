#!/usr/bin/env python3

"""
This is hugely inefficient. It loops through each DAT several times but this makes it easy to
drop/include particular checks.

For now, this only validates the MAME source files
"""
from typing import Optional
import os
import multiprocessing
from lxml import etree as ET
from shared import shared

KNOWN_GAME_ATTRIBUTES = set(
    ["rom", "isdevice", "name", "cloneof", "runnable", "isbios", "sourcefile", "ismechanical", "romof", "sampleof"]
)

KNOWN_DRIVER_ATTRIBUTES = set(
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

KNOWN_FEATURE_ATTRIBUTES = set(["overall", "type", "status"])

KNOWN_DISK_ATTRIBUTES = set(
    ["sha1", "optional", "index", "writable", "region", "md5", "name", "status", "writeable", "merge"]
)


def validate_root_tag(root: ET._Element) -> None:
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


def validate_cloneof_rules(path: str, root: ET._Element, elements: list[ET._Element]) -> None:
    """
    This is particularly slow. It loops through a list of parents as well as all elements. However, it's a trade-off
    between that and doing a find by name on the same element multiple times (where one element is the parent of
    many children). This seemed to be slower but wasn't properly profiled.
    """
    clone_parent_names = set()
    for element in elements:
        if (cloneof := element.get("cloneof")) is not None:
            clone_parent_names.add(cloneof)
            if element.get("romof") is None:
                print(f"{os.path.basename(path)}: cloneof without romof: {element.get('name')}, cloneof {cloneof}")
    for parent_name in clone_parent_names:
        parent_element = root.find(f"./*[@name='{parent_name}']")
        if parent_element is not None and (parent_clone_name := parent_element.get("cloneof")) is not None:
            print(f"{os.path.basename(path)}: cloneof parent has cloneof: {parent_name} -> {parent_clone_name}")


def validate_romof_parents_are_never_cloneof_children(
    path: str, root: ET._Element, elements: list[ET._Element]
) -> None:
    """
    This has the same issues as validate_clone_parents_are_never_clones

    A romof parent can be a romof child, so we don't check for that.
    """
    romof_parent_names = set()
    for element in elements:
        if (romof := element.get("romof")) is not None:
            if romof != element.get("name"):
                romof_parent_names.add(romof)
    for parent_name in romof_parent_names:
        parent_element = root.find(f"./*[@name='{parent_name}']")
        if parent_element is not None:
            if (parent_cloneof_name := parent_element.get("cloneof")) is not None:
                print(f"{os.path.basename(path)}: romof parent has cloneof: {parent_name} -> {parent_cloneof_name}")


def validate_tag_attributes(path: str, elements: list[ET._Element]) -> tuple[set, set, set, set]:
    game_attributes: set[str] = set()
    driver_attributes: set[str] = set()
    feature_attributes: set[str] = set()
    disk_attributes: set[str] = set()
    for element in elements:
        game_attributes.update(element.attrib.keys())
        driver_elements = element.findall("driver")
        if len(driver_elements) > 1:
            print("Multiple driver elements: ", path)
        for driver_element in driver_elements:
            driver_attributes.update(driver_element.attrib.keys())
        feature_elements = element.findall("feature")
        for feature_element in feature_elements:
            feature_attributes.update(feature_element.attrib.keys())
        disk_elements = element.findall("disk")
        for disk_element in disk_elements:
            disk_attributes.update(disk_element.attrib.keys())
    return game_attributes, driver_attributes, feature_attributes, disk_attributes


def find_different_romof_clone_ofs(path: str, elements: list[ET._Element]) -> list[dict[str, str]]:
    results = []
    for element in elements:
        if (romof := element.get("romof")) is not None:
            if (cloneof := element.get("cloneof")) is not None:
                if romof != cloneof and romof != element.get("name"):
                    results.append(
                        {"dat": os.path.basename(path), "name": element.get("name"), "romof": romof, "cloneof": cloneof}
                    )
    return results


def process_dat(path: str) -> Optional[tuple[set, set, set, set, list]]:
    print(os.path.basename(path))
    if (root := shared.get_dat_root(path)) is not None:
        elements = list(root)
        element_tags = [element.tag for element in elements]
        validate_root_tag(root)
        validate_num_headers(path, element_tags)
        validate_tag_names(path, element_tags)
        validate_cloneof_rules(path, root, elements)
        validate_romof_parents_are_never_cloneof_children(path, root, elements)
        diff_parent_results = find_different_romof_clone_ofs(path, elements)
        game_attributes, driver_attributes, feature_attributes, disk_attributes = validate_tag_attributes(
            path, elements
        )
    return game_attributes, driver_attributes, feature_attributes, disk_attributes, diff_parent_results


def process_files():
    with multiprocessing.Pool(8) as pool:
        results = pool.map(process_dat, shared.MAME_DATS)

    game_attributes = set()
    driver_attributes = set()
    feature_attributes = set()
    disk_attributes = set()
    diff_parent_results = []

    for result in results:
        if result:
            game_attributes.update(result[0])
            driver_attributes.update(result[1])
            feature_attributes.update(result[2])
            disk_attributes.update(result[3])
            diff_parent_results.extend(result[4])

    if not game_attributes == KNOWN_GAME_ATTRIBUTES:
        print("Unrecognised game attributes: ", game_attributes - KNOWN_GAME_ATTRIBUTES)
    if not driver_attributes == KNOWN_DRIVER_ATTRIBUTES:
        print("Unrecognised driver attributes: ", driver_attributes - KNOWN_DRIVER_ATTRIBUTES)
    if not feature_attributes == KNOWN_FEATURE_ATTRIBUTES:
        print("Unrecognised feature attributes: ", feature_attributes - KNOWN_FEATURE_ATTRIBUTES)
    if not disk_attributes == KNOWN_DISK_ATTRIBUTES:
        print("Unrecognised disk attributes: ", disk_attributes - KNOWN_DISK_ATTRIBUTES)
    # This list does not include:
    # - romset with romof but no cloneof
    # - romset where romof is self-referential
    # - romset where romof is the same as cloneof
    print(f"{len(diff_parent_results)} romsets with different cloneof and romof attributes")
    # for result in diff_parent_results:
    #     print(result)
    print(f"{'Dat':<10}\t{'Name':<10}\t{'Romof':<10}\t{'Cloneof':<10}")
    for result in diff_parent_results:
        print(f"{result['dat']:<10}\t{result['name']:<10}\t{result['romof']:<10}\t{result['cloneof']:<10}")


if __name__ == "__main__":
    process_files()
