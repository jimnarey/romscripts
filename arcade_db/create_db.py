#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

# TODO: Carefully consider whether the target values for romof and cloneof are part of a game's identity (uniqueness).
# Starting point is non-merged sets. So if a game has a different romof/cloneof than a predecessor, it must have different
# roms. This is not true of split games, where a romof/cloneof target may have different roms without the the child game
# having changed. If we include split roms as additional rows, we need to take care not to effectively overwrite the
# cloneof/romof values of earlier versions of a game with those of later versions.
#
# If we treat cloneof/romof values as part of identity, add a second index to include a hash.

# TODO: Add Chip table and create records for non-rom machines (e.g. famicom)
# TODO: Investigate and implement the use of the 'merge' attribute in Rom elements. Validate parameters for merge attributes.
# TODO: Change calls to .first to .one_or_none or .one

from typing import Optional, Any, Union
import os
from pathlib import Path

# from concurrent.futures import ProcessPoolExecutor, as_completed
# import multiprocessing
import shutil
from copy import deepcopy

from lxml import etree as ET
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql.schema import Table

from .shared import sources, utils, indexing

SqlAlchemyTable = Union[Table, Any]

DatData = dict[str, dict[str, dict[str, str]]]


def create_dataframe_from_table(table: SqlAlchemyTable) -> pd.DataFrame:
    if isinstance(table, Table):
        column_names = [column.name for column in table.columns]
    else:
        column_names = [column.name for column in table.__table__.columns]
    return pd.DataFrame(columns=column_names)


def strip_keys(dict_: dict[str, Any]) -> list[str]:
    return [key for key in dict_.keys() if not key.startswith("_")]


# TODO: Test for possibility rom instance is assigned zero value
# This is needed to keep the type checker happy
def get_rom_size(rom_element: ET._Element) -> int:
    if size := rom_element.get("size"):
        return int(size)
    return 0


def get_inner_element_text(outer_element: ET._Element, inner_element_name: str) -> Optional[str]:
    inner_element = outer_element.find(inner_element_name)  # Using := confuses type checker
    if inner_element is not None:
        return inner_element.text
    return None


def add_roms(rom_elements: list[ET._Element], dat_data: DatData, game_id: str) -> None:
    for rom_element in rom_elements:
        name = rom_element.get("name", "")
        size = get_rom_size(rom_element)
        crc = rom_element.get("crc", "")
        sha1 = rom_element.get("sha1", None)
        rom_hash = indexing.get_rom_index_hash(name, size, crc)
        rom_attrs = {
            "hash": rom_hash,
            "name": name,
            "size": size,
            "crc": str(crc),
            "sha1": sha1,
        }
        dat_data["roms"][rom_hash] = rom_attrs
        composite_key = indexing.get_attributes_md5({"game_id": game_id, "rom_id": rom_hash})
        dat_data["game_rom"][composite_key] = {"game_id": game_id, "rom_id": rom_hash}


def process_game(game_element: ET._Element, dat_data: DatData) -> Optional[dict[str, str]]:
    if rom_elements := utils.get_sub_elements(game_element, "rom"):
        name = game_element.get("name", "")
        game_hash = indexing.get_game_index_from_elements(name, rom_elements)
        game_attrs = {
            "hash": game_hash,
            "name": name,
            "description": get_inner_element_text(game_element, "description"),
            "year": get_inner_element_text(game_element, "year"),
            "manufacturer": get_inner_element_text(game_element, "manufacturer"),
            "isbios": game_element.get("isbios"),
            "isdevice": game_element.get("isdevice"),
            "runnable": game_element.get("runnable"),
            "ismechanical": game_element.get("ismechanical"),
            "romof": game_element.get("romof"),
            "cloneof": game_element.get("cloneof"),
        }
        add_roms(rom_elements, dat_data, game_hash)
        return game_attrs
    return None


def get_feature_element_attributes(feature_element: ET._Element) -> dict[str, str]:
    return {
        "overall": feature_element.get("overall", ""),
        "type": feature_element.get("type", ""),
        "status": feature_element.get("status", ""),
    }


def add_features(game_emulator_attrs: dict[str, str], game_element: ET._Element, dat_data: DatData) -> None:
    for feature_element in game_element.findall("feature"):
        feature_attrs = get_feature_element_attributes(feature_element)
        feature_hash = indexing.get_attributes_md5(feature_attrs)
        feature_attrs["hash"] = feature_hash
        dat_data["features"][feature_hash] = feature_attrs
        composite_key = indexing.get_attributes_md5(
            {"game_emulator_id": game_emulator_attrs["hash"], "feature_id": feature_hash}
        )
        dat_data["game_emulator_feature"][composite_key] = {
            "game_emulator_id": game_emulator_attrs["hash"],
            "feature_id": feature_hash,
        }


def get_driver_element_attributes(driver_element: ET._Element) -> dict[str, str]:
    return {
        "palettesize": driver_element.get("palettesize", ""),
        "hiscoresave": driver_element.get("hiscoresave", ""),
        "requiresartwork": driver_element.get("requiresartwork", ""),
        "unofficial": driver_element.get("unofficial", ""),
        "good": driver_element.get("good", ""),
        "status": driver_element.get("status", ""),
        "graphic": driver_element.get("graphic", ""),
        "cocktailmode": driver_element.get("cocktailmode", ""),
        "savestate": driver_element.get("savestate", ""),
        "protection": driver_element.get("protection", ""),
        "emulation": driver_element.get("emulation", ""),
        "cocktail": driver_element.get("cocktail", ""),
        "color": driver_element.get("color", ""),
        "nosoundhardware": driver_element.get("nosoundhardware", ""),
        "sound": driver_element.get("sound", ""),
        "incomplete": driver_element.get("incomplete", ""),
    }


# TODO: Check for orphaned drivers after db build.
def add_driver(game_emulator_attrs: dict[str, str], game_element: ET._Element, dat_data: DatData) -> None:
    if (driver_element := game_element.find("driver")) is not None:
        driver_attrs = get_driver_element_attributes(driver_element)
        driver_hash = indexing.get_attributes_md5(driver_attrs)
        driver_attrs["hash"] = driver_hash
        dat_data["drivers"][driver_hash] = driver_attrs
        game_emulator_attrs["driver_id"] = driver_hash


def get_disk_attributes(disk_element: ET._Element) -> dict[str, str]:
    return {
        "name": disk_element.get("name", ""),
        "sha1": disk_element.get("sha1", ""),
        "md5": disk_element.get("md5", ""),
    }


# TODO: Can probably avoid using get_sub_elements.
# TODO: Need a second index for sha1
def add_disks(game_emulator_attrs: dict[str, str], game_element: ET._Element, dat_data: DatData):
    if disk_elements := utils.get_sub_elements(game_element, "disk"):
        for disk_element in disk_elements:
            disk_attrs = get_disk_attributes(disk_element)
            disk_hash = indexing.get_attributes_md5(disk_attrs)
            disk_attrs["hash"] = disk_hash
            dat_data["disks"][disk_hash] = disk_attrs
            composite_key = indexing.get_attributes_md5(
                {"game_emulator_id": game_emulator_attrs["hash"], "disk_id": disk_hash}
            )
            dat_data["game_emulator_disk"][composite_key] = {
                "game_emulator_id": game_emulator_attrs["hash"],
                "disk_id": disk_hash,
            }


def add_game_emulator_relationship(
    game_element: ET._Element, game_attrs: dict[str, str], emulator_hash: str, dat_data: DatData
):
    game_emulator_attrs = {"game_id": game_attrs["hash"], "emulator_id": emulator_hash}
    # We don't use the driver id as part of the primary key because we only want one game_emulator record per game/emulator
    # relationship. There is a risk here of orphaning driver records, which we need to check for elsewhere.
    game_emulator_attrs["hash"] = indexing.get_attributes_md5(
        {key: game_emulator_attrs[key] for key in ("game_id", "emulator_id")}
    )
    add_features(game_emulator_attrs, game_element, dat_data)
    add_driver(game_emulator_attrs, game_element, dat_data)
    add_disks(game_emulator_attrs, game_element, dat_data)
    dat_data["game_emulator"][game_emulator_attrs["hash"]] = game_emulator_attrs


def process_games(root: ET._Element, emulator_attrs: dict[str, str]) -> DatData:
    dat_data = get_empty_dat_data()
    emulator_hash = emulator_attrs["id"]
    emulator_attrs["hash"] = emulator_hash
    dat_data["emulators"][emulator_hash] = emulator_attrs

    for game_element in root:
        rom_elements = utils.get_sub_elements(game_element, "rom")
        if rom_elements:
            game_attrs = process_game(game_element, dat_data)
            if game_attrs is not None:
                add_game_emulator_relationship(game_element, game_attrs, emulator_hash, dat_data)
                dat_data["games"][game_attrs["hash"]] = game_attrs
    return dat_data


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


# Check emulator name as expected and that version matches expected format
def get_emulator_attrs(dat_file: str) -> dict[str, str]:
    emulator_name, emulator_version = get_mame_emulator_details(dat_file)
    id = "".join([char for char in f"{emulator_name}{emulator_version}" if char.isalnum()]).lower()
    return {"id": id, "name": emulator_name, "version": str(emulator_version)}


def get_empty_dat_data() -> DatData:
    return {
        "games": {},
        "roms": {},
        "emulators": {},
        "disks": {},
        "features": {},
        "drivers": {},
        "game_emulator": {},
        "game_rom": {},
        "game_emulator_disk": {},
        "game_emulator_feature": {},
    }


def convert_hashes_to_ids(dat_data: DatData) -> DatData:
    """
    Convert hash-based keys to numeric auto-increment IDs before writing to database.
    This is done at write time to minimize memory usage during processing.
    """
    print("Converting hash keys to numeric IDs...")
    hash_to_id = {}  # type: ignore
    next_id = {}

    entity_tables = ["games", "roms", "emulators", "disks", "features", "drivers"]
    for table in entity_tables:
        hash_to_id[table] = {}
        next_id[table] = 1
        for hash_key, attrs in dat_data[table].items():
            new_id = next_id[table]
            hash_to_id[table][hash_key] = new_id
            attrs["id"] = new_id  # type: ignore
            next_id[table] += 1

    hash_to_id["game_emulator"] = {}
    next_id["game_emulator"] = 1
    for hash_key, attrs in dat_data["game_emulator"].items():
        new_id = next_id["game_emulator"]
        hash_to_id["game_emulator"][hash_key] = new_id
        attrs["id"] = new_id  # type: ignore
        attrs["game_id"] = hash_to_id["games"][attrs["game_id"]]
        attrs["emulator_id"] = hash_to_id["emulators"][attrs["emulator_id"]]
        if "driver_id" in attrs:
            attrs["driver_id"] = hash_to_id["drivers"][attrs["driver_id"]]
        if "hash" in attrs:
            del attrs["hash"]
        next_id["game_emulator"] += 1

    for attrs in dat_data["game_rom"].values():
        attrs["game_id"] = hash_to_id["games"][attrs["game_id"]]
        attrs["rom_id"] = hash_to_id["roms"][attrs["rom_id"]]

    for attrs in dat_data["game_emulator_feature"].values():
        attrs["game_emulator_id"] = hash_to_id["game_emulator"][attrs["game_emulator_id"]]
        attrs["feature_id"] = hash_to_id["features"][attrs["feature_id"]]

    for attrs in dat_data["game_emulator_disk"].values():
        attrs["game_emulator_id"] = hash_to_id["game_emulator"][attrs["game_emulator_id"]]
        attrs["disk_id"] = hash_to_id["disks"][attrs["disk_id"]]

    for game_attrs in dat_data["games"].values():
        if "cloneof_id" in game_attrs and game_attrs["cloneof_id"]:
            game_attrs["cloneof_id"] = hash_to_id["games"].get(game_attrs["cloneof_id"])
        if "romof_id" in game_attrs and game_attrs["romof_id"]:
            game_attrs["romof_id"] = hash_to_id["games"].get(game_attrs["romof_id"])

    print("Conversion complete.")
    return dat_data


def write(dat_data: DatData, out_dir: str, csv: bool = False) -> None:
    dat_data = convert_hashes_to_ids(dat_data)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.mkdir(out_dir)
    engine = create_engine(f"sqlite:///{Path(out_dir, 'arcade.db')}")  # noqa: E231
    for key in strip_keys(dat_data):
        print(f"Creating {key} dataframe...")
        df = pd.DataFrame(list(dat_data[key].values()))
        if csv:
            print(f"Writing {key} dataframe to CSV...")
            df.to_csv(Path(out_dir, f"{key}.csv"), index=False)
        print(f"Writing {key} dataframe to sqlite...")
        df.to_sql(key, con=engine, if_exists="replace", index=False)


def merge_dat_data(master_dat_data: DatData, dat_data: DatData) -> None:
    for key in strip_keys(dat_data):
        master_dat_data[key].update(deepcopy(dat_data[key]))


def process_dats_consecutively(dats: list[str], out_dir: str):
    master_dat_data = get_empty_dat_data()

    for i, dat_file in enumerate(dats):
        emulator_attrs = get_emulator_attrs(dat_file)
        root = sources.get_dat_root(dat_file)
        if root is not None:
            dat_data = process_games(root, emulator_attrs)
            root.clear()
            merge_dat_data(master_dat_data, dat_data)
            for key in dat_data:
                dat_data[key].clear()
            dat_data.clear()
            dat_data = {}
        utils.log_memory(f"Processed game {dat_file} - ")
    write(master_dat_data, out_dir, csv=True)


def dat_worker(dat_file):
    emulator_attrs = get_emulator_attrs(dat_file)
    root = sources.get_dat_root(dat_file)
    if root is not None:
        utils.log_memory(f"Before process_games - {dat_file}")
        dat_data, unhandled_references = process_games(root, emulator_attrs)
        root.clear()
        return dat_data, unhandled_references
    return get_empty_dat_data(), []


# def process_dats(dats: list[str]):
#     master_dat_data = get_empty_dat_data()
#     all_unhandled_references = []

#     initial_memory = utils.log_memory("Initial memory (parallel processing):")

#     with multiprocessing.Pool() as pool:
#         results = pool.map(dat_worker, dats)

#     for i, (dat_data, unhandled_references) in enumerate(results):
#         merge_dat_data(master_dat_data, dat_data)
#         for key in dat_data:
#             dat_data[key].clear()
#         dat_data.clear()
#         all_unhandled_references.extend(unhandled_references)

#     final_memory = utils.log_memory("Final memory:")
#     print(f"Total memory growth: {final_memory - initial_memory:.2f} MB")

#     write(master_dat_data, os.getcwd(), csv=True)
#     print_unhandled_references(all_unhandled_references)
