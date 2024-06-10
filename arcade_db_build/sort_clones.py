#!/usr/bin/env python3

import os
import multiprocessing
import bz2

import lxml.etree as ET

from arcade_db_build.shared import sources


WRITE_PATH = os.path.join(sources.PARENT_PATH, "mame_db_source", "clones_sorted_dats")


def get_parent_elements(
    basename: str, element: ET._Element, elements_dict: dict[str, ET._Element]
) -> tuple[set[ET._Element], list[dict]]:
    parent_element_names = {element.get(attr) for attr in ["romof", "cloneof"] if element.get(attr) is not None}
    parent_elements = set()
    not_found = []
    for parent_element_name in parent_element_names:
        if parent_element_name != element.get("name"):
            parent_element = elements_dict.get(parent_element_name)  # type: ignore
            if parent_element is None:
                not_found.append({"dat": basename, "element": element.get("name"), "parent": parent_element_name})
            else:
                parent_elements.add(parent_element)
    return parent_elements, not_found


def sort_groups(groups: dict[str, set], game_elements: set) -> dict[str, set]:
    sorted_groups = {
        "parents_only": groups["parents"] - groups["children"],
        "children_and_parents": groups["parents"] & groups["children"],
        "children_only": groups["children"] - groups["parents"],
        "no_relationships": game_elements - groups["parents"] - groups["children"],
    }
    return sorted_groups


def group_romsets(basename: str, game_elements: set) -> tuple[dict[str, set], list[dict]]:
    all_not_found = []
    groups: dict[str, set] = {"parents": set(), "children": set()}
    elements_dict = {element.get("name"): element for element in game_elements}
    for element in game_elements:
        parent_elements, not_found = get_parent_elements(basename, element, elements_dict)
        all_not_found.extend(not_found)
        if parent_elements:
            groups["parents"].update(parent_elements)
            groups["children"].add(element)
    return groups, all_not_found


def validate_new_root_romsets(basename: str, game_elements: set, new_root: ET._Element):
    output_game_elements = set(new_root.findall("game") + new_root.findall("machine"))
    if not output_game_elements == game_elements:
        print(f"{basename}: input and output game/machine elements do not match")
        raise


def validate_sort_order(basename: str, root: ET._Element) -> list[dict]:
    results = []
    game_elements = list(root)
    elements_dict = {
        element.get("name"): {"element": element, "index": index} for index, element in enumerate(game_elements)
    }
    for element_index, element in enumerate(game_elements):
        parent_element_names = {element.get(attr) for attr in ["romof", "cloneof"] if element.get(attr) is not None}
        for parent_element_name in parent_element_names:
            parent_element = elements_dict.get(parent_element_name)  # type: ignore
            if parent_element is not None:
                if (parent_index := parent_element["index"]) > element_index:
                    results.append(
                        {
                            "dat": basename,
                            "parent": parent_element_name,
                            "parent_index": parent_index,
                            "element": element.get("name"),
                            "index": element_index,
                        }
                    )
    return results


def process_dat(path: str) -> tuple[list[dict], list]:
    validation_results = []
    basename = os.path.basename(path)
    print(basename)
    if (root := sources.get_dat_root(path, concurrent=False)) is not None:
        header = root.find("header")
        game_elements = set(root.findall("game") + root.findall("machine"))
        groups, not_found = group_romsets(basename, game_elements)
        sorted_groups = sort_groups(groups, game_elements)
        root.clear()
        if header is not None:
            root.append(header)
        for group in [
            sorted_groups[name]
            for name in (
                "parents_only",
                "children_and_parents",
                "children_only",
                "no_relationships",
            )
        ]:
            for element in group:
                root.append(element)
        validate_new_root_romsets(basename, game_elements, root)
        validation_results.extend(validate_sort_order(basename, root))
        with bz2.open(os.path.join(WRITE_PATH, basename), "wb") as f:
            f.write(ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8"))
    return validation_results, not_found


def process_files() -> None:
    with multiprocessing.Pool(8) as pool:
        results = pool.map(process_dat, sources.MAME_DATS)

    validation_errors = []
    not_found = []
    for result in results:
        validation_errors.extend(result[0])
        not_found.extend(result[1])

    print("Validation errors: parent romsets found after children")
    print(f"{'Dat':<10}\t{'Parent':<10}\t{'Index':<10}\t{'Child':<10}\t{'Index':<10}")
    for error in validation_errors:
        print(
            f"{error['dat']:<10}\t{error['parent']:<10}\t{error['parent_index']:<10}\t{error['element']:<10}\t{error['index']:<10}"
        )
    print("Parent romsets not found")
    print(f"{'Dat':<10}\t{'Element':<10}\t{'Parent':<10}")
    for error in not_found:
        print(f"{error['dat']:<10}\t{error['element']:<10}\t{error['parent']:<10}")


if __name__ == "__main__":
    process_files()
