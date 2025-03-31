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
import gc

from lxml import etree as ET
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql.schema import Table

from .shared import sources, utils, indexing, db

SqlAlchemyTable = Union[Table, Any]


def create_dataframe_from_table(table: SqlAlchemyTable) -> pd.DataFrame:
    if isinstance(table, Table):
        column_names = [column.name for column in table.columns]
    else:
        column_names = [column.name for column in table.__table__.columns]
    return pd.DataFrame(columns=column_names)


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


def add_roms(rom_elements: list[ET._Element], dataframes: dict[str, Any], game_id: str) -> None:
    for rom_element in rom_elements:
        name = rom_element.get("name", "")
        size = get_rom_size(rom_element)
        crc = rom_element.get("crc", "")
        sha1 = rom_element.get("sha1", None)

        rom = {
            "id": indexing.get_rom_index_hash(name, size, crc),
            "name": name,
            "size": size,
            "crc": str(crc),
            "sha1": sha1,
        }
        dataframes["roms"].append(pd.DataFrame([rom]))
        dataframes["game_rom"].append(pd.DataFrame([{"game_id": game_id, "rom_id": rom["id"]}]))


def process_game(game_element: ET._Element, dataframes: dict[str, Any]) -> Optional[dict[str, str]]:
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
        add_roms(rom_elements, dataframes, game_id)
        return game_attrs
    return None


def get_feature_element_attributes(feature_element: ET._Element) -> dict[str, str]:
    return {
        "overall": feature_element.get("overall", ""),
        "type": feature_element.get("type", ""),
        "status": feature_element.get("status", ""),
    }


def add_features(game_emulator_attrs: dict[str, str], game_element: ET._Element, dataframes: dict[str, Any]) -> None:
    for feature_element in game_element.findall("feature"):
        feature_attributes = get_feature_element_attributes(feature_element)
        feature_attributes["id"] = indexing.get_attributes_md5(feature_attributes)
        features = pd.DataFrame([feature_attributes])
        dataframes["features"].append(features)
        dataframes["game_emulator_feature"].append(
            pd.DataFrame([{"game_emulator_id": game_emulator_attrs["id"], "feature_id": features["id"]}]).set_index(
                ["game_emulator_id", "feature_id"]
            )
        )


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
def add_driver(game_emulator_attrs: dict[str, str], game_element: ET._Element, dataframes: dict[str, Any]) -> None:
    if (driver_element := game_element.find("driver")) is not None:
        driver_attributes = get_driver_element_attributes(driver_element)
        driver_attributes["id"] = indexing.get_attributes_md5(driver_attributes)
        driver = pd.DataFrame([driver_attributes])
        dataframes["drivers"].append(driver)
        game_emulator_attrs["driver_id"] = driver_attributes["id"]


def get_disk_attributes(disk_element: ET._Element) -> dict[str, str]:
    return {
        "name": disk_element.get("name", ""),
        "sha1": disk_element.get("sha1", ""),
        "md5": disk_element.get("md5", ""),
    }


# TODO: Can probably avoid using get_sub_elements.
# TODO: Need a second index for sha1
def add_disks(game_emulator_attrs: dict[str, str], game_element: ET._Element, dataframes: dict[str, Any]):
    if disk_elements := utils.get_sub_elements(game_element, "disk"):
        for disk_element in disk_elements:
            disk_attrs = get_disk_attributes(disk_element)
            disk_attrs["id"] = indexing.get_attributes_md5(disk_attrs)
            disk = pd.DataFrame([disk_attrs])
            dataframes["disks"].append(disk)
            dataframes["game_emulator_disk"].append(
                pd.DataFrame([{"game_emulator_id": game_emulator_attrs["id"], "disk_id": disk_attrs["id"]}]).set_index(
                    ["game_emulator_id", "disk_id"]
                )
            )


def add_game_emulator_relationship(
    game_element: ET._Element, game_attrs: dict[str, str], emulator_attrs: dict[str, str], dataframes: dict[str, Any]
):
    game_emulator_attrs = {"game_id": game_attrs["id"], "emulator_id": emulator_attrs["id"]}
    # We don't use the driver id as part of the primary key because we only want one game_emulator record per game/emulator
    # relationship. There is a risk here of orphaning driver records, which we need to check for elsewhere.
    game_emulator_attrs["id"] = indexing.get_attributes_md5(
        {key: game_emulator_attrs[key] for key in ("game_id", "emulator_id")}
    )
    add_features(game_emulator_attrs, game_element, dataframes)
    add_driver(game_emulator_attrs, game_element, dataframes)
    add_disks(game_emulator_attrs, game_element, dataframes)
    dataframes["game_emulator"].append(pd.DataFrame([game_emulator_attrs]))


def add_game_reference(game: dict[str, str], attribute: str, target_game_name: str, dataframes: dict[str, Any]) -> bool:
    """
    Add a reference to another game to a game object.
    field: either "cloneof" or "romof"
    """
    target_game = dataframes["games"].get(target_game_name)
    if target_game is not None:
        # Need to test that this only ever receives a one row dataframe
        game[f"{attribute}_id"] = target_game.iloc[0]["id"]
        return True
    return False


def add_game_references(
    game: dict[str, str], game_element: ET._Element, dataframes: dict[str, Any]
) -> list[dict[str, str]]:
    """
    Resolves the game > game references for a single game.
    """
    unhandled_references = []
    for attribute in ("cloneof", "romof"):
        if target_game_name := game_element.get(attribute):
            if bool(game["name"] != target_game_name):
                if add_game_reference(game, attribute, target_game_name, dataframes) is False:
                    unhandled_references.append(
                        {"game": game["name"], "attribute": attribute, "target": target_game_name}
                    )
    return unhandled_references


# @utils.time_execution("Process games")
def process_games(
    root: ET._Element, emulator_attrs: dict[str, str]
) -> tuple[dict[str, pd.DataFrame], list[dict[str, str]]]:
    dataframes: dict[str, Any] = {
        "games": {},
        "roms": [],
        "emulators": [],
        "disks": [],
        "features": [],
        "drivers": [],
        "game_emulator": [],
        "game_rom": [],
        "game_emulator_disk": [],
        "game_emulator_feature": [],
    }
    unhanded_references = []
    for game_element in root:
        rom_elements = utils.get_sub_elements(game_element, "rom")
        if rom_elements:
            game_attrs = process_game(game_element, dataframes)
            if game_attrs is not None:
                add_game_emulator_relationship(game_element, game_attrs, emulator_attrs, dataframes)
                unhanded_references.extend(add_game_references(game_attrs, game_element, dataframes))
                dataframes["games"][game_attrs["name"]] = pd.DataFrame([game_attrs])
    dataframes["emulators"].append(pd.DataFrame([emulator_attrs]))
    return dataframes, unhanded_references


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


def get_emulator_attrs(dat_file: str) -> dict[str, str]:
    emulator_name, emulator_version = get_mame_emulator_details(dat_file)
    id = "".join([char for char in f"{emulator_name}{emulator_version}" if char.isalnum()]).lower()
    return {"id": id, "name": emulator_name, "version": str(emulator_version)}


def get_master_dfs() -> dict[str, pd.DataFrame]:
    return {
        "games": create_dataframe_from_table(db.Game),
        "roms": create_dataframe_from_table(db.Rom),
        "emulators": create_dataframe_from_table(db.Emulator),
        "disks": create_dataframe_from_table(db.Disk),
        "features": create_dataframe_from_table(db.Feature),
        "drivers": create_dataframe_from_table(db.Driver),
        "game_emulator": create_dataframe_from_table(db.GameEmulator),
        "game_rom": create_dataframe_from_table(db.game_rom_association),
        "game_emulator_disk": create_dataframe_from_table(db.game_emulator_disk_association),
        "game_emulator_feature": create_dataframe_from_table(db.game_emulator_feature_association),
    }


# @utils.time_execution("Update master dataframes")
def update_master_dfs(master_dfs: dict[str, pd.DataFrame], dataframes: dict[str, pd.DataFrame]) -> None:
    master_dfs["games"] = pd.concat([master_dfs["games"], *dataframes["games"].values()])  # type: ignore
    master_dfs["roms"] = pd.concat([master_dfs["roms"], *dataframes["roms"]])  # type: ignore
    master_dfs["emulators"] = pd.concat([master_dfs["emulators"], *dataframes["emulators"]])  # type: ignore
    master_dfs["disks"] = pd.concat([master_dfs["disks"], *dataframes["disks"]])  # type: ignore
    master_dfs["features"] = pd.concat([master_dfs["features"], *dataframes["features"]])  # type: ignore
    master_dfs["drivers"] = pd.concat([master_dfs["drivers"], *dataframes["drivers"]])  # type: ignore
    master_dfs["game_emulator"] = pd.concat([master_dfs["game_emulator"], *dataframes["game_emulator"]])  # type: ignore
    master_dfs["game_rom"] = pd.concat([master_dfs["game_rom"], *dataframes["game_rom"]])  # type: ignore
    master_dfs["game_emulator_disk"] = pd.concat([master_dfs["game_emulator_disk"], *dataframes["game_emulator_disk"]])  # type: ignore
    master_dfs["game_emulator_feature"] = pd.concat([master_dfs["game_emulator_feature"], *dataframes["game_emulator_feature"]])  # type: ignore


# @utils.time_execution("Drop duplicates")
def drop_all_duplicates(master_dfs: dict[str, pd.DataFrame]) -> None:
    for key, df in master_dfs.items():
        if "id" in df.columns:
            df.drop_duplicates(subset="id", inplace=True)
        else:
            df.drop_duplicates(inplace=True)
        df.reset_index(inplace=True, drop=True)


# @utils.time_execution("Write CSVs")
def write_csvs(master_dfs: dict[str, pd.DataFrame]) -> None:
    target_dir = Path(sources.CSVS_DIR, f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}")
    target_dir.mkdir()
    for table_name, df in master_dfs.items():
        df.to_csv(Path(target_dir, f"{table_name}.csv"), index=False)


def write_to_sqlite(master_dfs: dict[str, pd.DataFrame], db_path: str) -> None:
    os.remove(db_path) if os.path.exists(db_path) else None
    engine = create_engine(f"sqlite:///{db_path}")
    for table_name, df in master_dfs.items():
        if not df.empty:
            print(f"Writing table '{table_name}' to database...")
            df.to_sql(name=table_name, con=engine, index=False)


def clear_dataframes(dataframes: dict[str, Any]) -> None:
    dataframes["games"] = dataframes["games"].values()
    for df_set in dataframes.values():
        for df in df_set:
            df.drop(df.index, inplace=True)
            df = None
    gc.collect()


def process_dats_consecutively(dats: list[str]):
    master_dfs = get_master_dfs()
    for dat_file in dats:
        emulator_attrs = get_emulator_attrs(dat_file)
        root = sources.get_dat_root(dat_file)
        if root is not None:
            utils.log_memory(f"Before process_games - {dat_file}")
            dataframes, unhandled_references = process_games(root, emulator_attrs)
            update_master_dfs(master_dfs, dataframes)
            drop_all_duplicates(master_dfs)

    write_csvs(master_dfs)
    write_to_sqlite(master_dfs, "test.db")


def process_dat(dat_file: str) -> tuple[dict[str, pd.DataFrame], list[dict[str, str]]]:
    """
    Process a single DAT file and return the resulting dataframes and unhandled references.
    """
    emulator_attrs = get_emulator_attrs(dat_file)
    root = sources.get_dat_root(dat_file)
    if root is not None:
        return process_games(root, emulator_attrs)
    return {}, []


def process_dats(dats: list[str]):
    master_dfs = get_master_dfs()
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        future_to_dat = {executor.submit(process_dat, dat_file): dat_file for dat_file in dats}
        for future in as_completed(future_to_dat):
            dat_file = future_to_dat[future]
            try:
                dataframes, unhandled_references = future.result()
                print(f"Processed {dat_file} successfully.")
                update_master_dfs(master_dfs, dataframes)
                drop_all_duplicates(master_dfs)

                gc.collect()

            except Exception as e:
                print(f"Error processing {dat_file}: {e}")

    write_csvs(master_dfs)
    write_to_sqlite(master_dfs, "test.db")


# if unhandled_references:
#     print(f"{'Name':<10}\t{'Attribute':<10}\t{'Target Game':<10}")
#     for ref in unhandled_references:
#         print(f"{ref['game']:<10}\t{ref['attribute']:<10}\t{ref['target']:<10}")
