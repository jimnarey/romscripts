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
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import shutil

from lxml import etree as ET
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql.schema import Table

from .shared import sources, utils, indexing, db

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


def print_dat_data_stats(dat_data: DatData, label: str) -> None:
    """Print statistics to help debug size issues."""
    print(f"\n{label} Statistics:")
    total_records = 0
    for key in strip_keys(dat_data):
        count = len(dat_data[key])
        total_records += count
        print(f"  {key}: {count:,} records")
    print(f"  TOTAL: {total_records:,} records")
    
    # Check relationship ratios that might indicate problems
    if dat_data["games"] and dat_data["game_rom"]:
        ratio = len(dat_data["game_rom"]) / len(dat_data["games"])
        print(f"  ROMs per game: {ratio:.1f}")
    
    if dat_data["games"] and dat_data["game_emulator"]:
        ratio = len(dat_data["game_emulator"]) / len(dat_data["games"])
        print(f"  Emulators per game: {ratio:.1f}")
    
    # Debug features specifically
    if dat_data["features"] and dat_data["game_emulator_feature"]:
        ratio = len(dat_data["game_emulator_feature"]) / len(dat_data["features"])
        print(f"  Game-emulator-features per feature: {ratio:.1f}")
        
        # Show the actual features to see if they're generic
        print("  Features found:")
        for feature in list(dat_data["features"].values())[:10]:  # Show first 10
            print(f"    type='{feature['type']}', status='{feature['status']}', overall='{feature['overall']}'")
        if len(dat_data["features"]) > 10:
            print(f"    ... and {len(dat_data['features']) - 10} more")


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
        rom_id = indexing.get_rom_index_hash(name, size, crc)
        rom_attrs = {
            "id": rom_id,
            "name": name,
            "size": size,
            "crc": str(crc),
            "sha1": sha1,
        }
        dat_data["roms"][rom_attrs["id"]] = rom_attrs
        composite_key = indexing.get_attributes_md5({"game_id": game_id, "rom_id": rom_id})
        dat_data["game_rom"][composite_key] = {"game_id": game_id, "rom_id": rom_id}


def process_game(game_element: ET._Element, dat_data: DatData) -> Optional[dict[str, str]]:
    if rom_elements := utils.get_sub_elements(game_element, "rom"):
        name = game_element.get("name", "")
        game_id = indexing.get_game_index_from_elements(name, rom_elements)
        game_attrs = {
            "id": game_id,
            "name": name,
            "description": get_inner_element_text(game_element, "description"),
            "year": get_inner_element_text(game_element, "year"),
            "manufacturer": get_inner_element_text(game_element, "manufacturer"),
            "isbios": game_element.get("isbios"),
            "isdevice": game_element.get("isdevice"),
            "runnable": game_element.get("runnable"),
            "ismechanical": game_element.get("ismechanical"),
        }
        add_roms(rom_elements, dat_data, game_id)
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
        feature_attrs["id"] = indexing.get_attributes_md5(feature_attrs)
        dat_data["features"][feature_attrs["id"]] = feature_attrs
        composite_key = indexing.get_attributes_md5({
            "game_emulator_id": game_emulator_attrs["id"],
            "feature_id": feature_attrs["id"]
        })
        dat_data["game_emulator_feature"][composite_key] = {
            "game_emulator_id": game_emulator_attrs["id"],
            "feature_id": feature_attrs["id"],
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
        driver_attrs["id"] = indexing.get_attributes_md5(driver_attrs)
        dat_data["drivers"][driver_attrs["id"]] = driver_attrs
        game_emulator_attrs["driver_id"] = driver_attrs["id"]


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
            disk_attrs["id"] = indexing.get_attributes_md5(disk_attrs)
            dat_data["disks"][disk_attrs["id"]] = disk_attrs
            composite_key = indexing.get_attributes_md5({
                "game_emulator_id": game_emulator_attrs["id"],
                "disk_id": disk_attrs["id"]
            })
            dat_data["game_emulator_disk"][composite_key] = {
                "game_emulator_id": game_emulator_attrs["id"],
                "disk_id": disk_attrs["id"],
            }


def add_game_emulator_relationship(
    game_element: ET._Element, game_attrs: dict[str, str], emulator_attrs: dict[str, str], dat_data: DatData
):
    game_emulator_attrs = {"game_id": game_attrs["id"], "emulator_id": emulator_attrs["id"]}
    # We don't use the driver id as part of the primary key because we only want one game_emulator record per game/emulator
    # relationship. There is a risk here of orphaning driver records, which we need to check for elsewhere.
    game_emulator_attrs["id"] = indexing.get_attributes_md5(
        {key: game_emulator_attrs[key] for key in ("game_id", "emulator_id")}
    )
    add_features(game_emulator_attrs, game_element, dat_data)
    add_driver(game_emulator_attrs, game_element, dat_data)
    add_disks(game_emulator_attrs, game_element, dat_data)
    dat_data["game_emulator"][game_emulator_attrs["id"]] = game_emulator_attrs


def add_game_reference(game_attrs: dict[str, str], attribute: str, target_game_name: str, dat_data: DatData) -> bool:
    """
    Add a reference to another game to a game object.
    field: either "cloneof" or "romof"
    """
    target_game = dat_data["_games_name"].get(target_game_name)
    if target_game is not None:
        game_attrs[f"{attribute}_id"] = target_game["id"]
        return True
    return False


def add_game_references(game: dict[str, str], game_element: ET._Element, dat_data: DatData) -> list[dict[str, str]]:
    """
    Resolves the game > game references for a single game.
    """
    unhandled_references = []
    for attribute in ("cloneof", "romof"):
        if target_game_name := game_element.get(attribute):
            if bool(game["name"] != target_game_name):
                if add_game_reference(game, attribute, target_game_name, dat_data) is False:
                    unhandled_references.append(
                        {"game": game["name"], "attribute": attribute, "target": target_game_name}
                    )
    return unhandled_references


def process_games(root: ET._Element, emulator_attrs: dict[str, str]) -> tuple[DatData, list[dict[str, str]]]:
    dat_data = get_empty_dat_data()
    unhanded_references = []
    for game_element in root:
        rom_elements = utils.get_sub_elements(game_element, "rom")
        if rom_elements:
            game_attrs = process_game(game_element, dat_data)
            if game_attrs is not None:
                add_game_emulator_relationship(game_element, game_attrs, emulator_attrs, dat_data)
                unhanded_references.extend(add_game_references(game_attrs, game_element, dat_data))
                dat_data["_games_name"][game_attrs["name"]] = game_attrs
                dat_data["games"][game_attrs["id"]] = game_attrs
    dat_data["emulators"][emulator_attrs["id"]] = emulator_attrs
    return dat_data, unhanded_references


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


def get_emulator_attrs(dat_file: str) -> dict[str, str]:
    emulator_name, emulator_version = get_mame_emulator_details(dat_file)
    id = "".join([char for char in f"{emulator_name}{emulator_version}" if char.isalnum()]).lower()
    return {"id": id, "name": emulator_name, "version": str(emulator_version)}


def get_empty_dat_data() -> DatData:
    return {
        "_games_name": {},
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


def write(dat_data: DatData, path: str, csv: bool = False) -> None:
    target_dir = Path(path, "arcade-out")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir()
    engine = create_engine(f"sqlite:///{Path(target_dir, 'arcade.db')}")
    for key in strip_keys(dat_data):
        print(f"Creating {key} dataframe...")
        df = pd.DataFrame(list(dat_data[key].values()))
        if csv:
            print(f"Writing {key} dataframe to CSV...")
            df.to_csv(Path(target_dir, f"{key}.csv"), index=False)
        print(f"Writing {key} dataframe to sqlite...")
        df.to_sql(key, con=engine, if_exists="replace", index=False)


def print_unhandled_references(unhandled_references: list[dict[str, str]]) -> None:
    if unhandled_references:
        print(f"{'Name':<10}\t{'Attribute':<10}\t{'Target Game':<10}")
        for ref in unhandled_references:
            print(f"{ref['game']:<10}\t{ref['attribute']:<10}\t{ref['target']:<10}")


def process_dats_consecutively(dats: list[str]):
    master_dat_data = get_empty_dat_data()
    all_unhandled_references = []
    
    print_dat_data_stats(master_dat_data, "Initial")
    
    for i, dat_file in enumerate(dats):
        emulator_attrs = get_emulator_attrs(dat_file)
        root = sources.get_dat_root(dat_file)
        if root is not None:
            utils.log_memory(f"Before process_games - {dat_file}")
            dat_data, unhandled_references = process_games(root, emulator_attrs)
            all_unhandled_references.extend(unhandled_references)
            for key in strip_keys(dat_data):
                master_dat_data[key].update(dat_data[key])
            
            # Print stats every 10 DATs to see where explosion happens
            if i % 10 == 0:
                print_dat_data_stats(master_dat_data, f"After DAT {i+1}")
    
    print_dat_data_stats(master_dat_data, "Final")
    write(master_dat_data, os.getcwd(), csv=True)
    print_unhandled_references(all_unhandled_references)


def dat_worker(dat_file):
    emulator_attrs = get_emulator_attrs(dat_file)
    root = sources.get_dat_root(dat_file)
    if root is not None:
        utils.log_memory(f"Before process_games - {dat_file}")
        dat_data, unhandled_references = process_games(root, emulator_attrs)
        return dat_data, unhandled_references
    return get_empty_dat_data(), []


# Parallelized version using multiprocessing
def process_dats(dats: list[str]):
    master_dat_data = get_empty_dat_data()
    all_unhandled_references = []
    with multiprocessing.Pool() as pool:
        results = pool.map(dat_worker, dats)
    for dat_data, unhandled_references in results:
        for key in strip_keys(dat_data):
            master_dat_data[key].update(dat_data[key])
        all_unhandled_references.extend(unhandled_references)
    write(master_dat_data, os.getcwd(), csv=True)
    print_unhandled_references(all_unhandled_references)

