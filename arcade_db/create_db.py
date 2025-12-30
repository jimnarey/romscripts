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

from typing import Optional, Any, Union, TypeAlias
import os
from pathlib import Path
import multiprocessing
import shutil
from copy import deepcopy
from dataclasses import asdict

from lxml import etree as ET
import pandas as pd
from sqlalchemy import create_engine

from .shared import sources, types, utils, indexing

EntityData: TypeAlias = Union[
    types.Rom,
    types.Game,
    types.Driver,
    types.Feature,
    types.Disk,
    types.Emulator,
    types.GameEmulator,
    types.GameRom,
    types.GameEmulatorFeature,
    types.GameEmulatorDisk,
]

DatData = dict[str, dict[str, EntityData]]


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

        rom = types.Rom(
            id=0,  # Will be assigned during convert_hashes_to_ids
            hash=rom_hash,
            name=name,
            size=size,
            crc=str(crc),
            sha1=sha1,
        )
        dat_data["roms"][rom_hash] = rom

        composite_key = indexing.get_attributes_md5({"game_id": game_id, "rom_id": rom_hash})
        game_rom = types.GameRom(
            id=0,
            game_id=game_id,
            rom_id=rom_hash,
        )
        dat_data["game_rom"][composite_key] = game_rom


def process_game(game_element: ET._Element, dat_data: DatData) -> Optional[types.Game]:
    if rom_elements := utils.get_sub_elements(game_element, "rom"):
        name = game_element.get("name", "")
        game_hash = indexing.get_game_index_from_elements(name, rom_elements)
        year_text = get_inner_element_text(game_element, "year")
        year = int(year_text) if year_text and year_text.isdigit() else None
        game = types.Game(
            id=0,
            hash=game_hash,
            name=name,
            description=get_inner_element_text(game_element, "description"),
            year=year,
            manufacturer=get_inner_element_text(game_element, "manufacturer"),
            romof=game_element.get("romof"),
            cloneof=game_element.get("cloneof"),
            isbios=game_element.get("isbios"),
            isdevice=game_element.get("isdevice"),
            runnable=game_element.get("runnable"),
            ismechanical=game_element.get("ismechanical"),
        )

        add_roms(rom_elements, dat_data, game_hash)
        return game
    return None


def add_features(game_emulator_attrs: dict[str, str], game_element: ET._Element, dat_data: DatData) -> None:
    for feature_element in game_element.findall("feature"):
        # Create feature dataclass directly from XML
        feature = types.Feature(
            id=0,
            hash="",  # Will be computed and set below
            overall=feature_element.get("overall", ""),
            type=feature_element.get("type", ""),
            status=feature_element.get("status", ""),
        )

        # Compute hash from the dataclass and mutate the hash field
        feature.hash = indexing.get_entity_hash(feature)
        dat_data["features"][feature.hash] = feature

        composite_key = indexing.get_attributes_md5(
            {"game_emulator_id": game_emulator_attrs["hash"], "feature_id": feature.hash}
        )
        game_emulator_feature = types.GameEmulatorFeature(
            id=0,
            game_emulator_id=game_emulator_attrs["hash"],
            feature_id=feature.hash,
        )
        dat_data["game_emulator_feature"][composite_key] = game_emulator_feature


# TODO: Check for orphaned drivers after db build.
def add_driver(game_emulator_attrs: dict[str, str], game_element: ET._Element, dat_data: DatData) -> None:
    if (driver_element := game_element.find("driver")) is not None:
        # Create driver dataclass directly from XML
        driver = types.Driver(
            id=0,
            hash="",  # Will be computed and set below
            palettesize=driver_element.get("palettesize", ""),
            hiscoresave=driver_element.get("hiscoresave", ""),
            requiresartwork=driver_element.get("requiresartwork", ""),
            unofficial=driver_element.get("unofficial", ""),
            good=driver_element.get("good", ""),
            status=driver_element.get("status", ""),
            graphic=driver_element.get("graphic", ""),
            cocktailmode=driver_element.get("cocktailmode", ""),
            savestate=driver_element.get("savestate", ""),
            protection=driver_element.get("protection", ""),
            emulation=driver_element.get("emulation", ""),
            cocktail=driver_element.get("cocktail", ""),
            color=driver_element.get("color", ""),
            nosoundhardware=driver_element.get("nosoundhardware", ""),
            sound=driver_element.get("sound", ""),
            incomplete=driver_element.get("incomplete", ""),
        )

        # Compute hash from the dataclass and mutate the hash field
        driver.hash = indexing.get_entity_hash(driver)
        dat_data["drivers"][driver.hash] = driver
        game_emulator_attrs["driver_id"] = driver.hash


# TODO: Can probably avoid using get_sub_elements.
# TODO: Need a second index for sha1
def add_disks(game_emulator_attrs: dict[str, str], game_element: ET._Element, dat_data: DatData):
    if disk_elements := utils.get_sub_elements(game_element, "disk"):
        for disk_element in disk_elements:
            # Create disk dataclass directly from XML
            disk = types.Disk(
                id=0,
                hash="",  # Will be computed and set below
                name=disk_element.get("name", ""),
                sha1=disk_element.get("sha1", ""),
                md5=disk_element.get("md5", ""),
            )

            # Compute hash from the dataclass and mutate the hash field
            disk.hash = indexing.get_entity_hash(disk)
            dat_data["disks"][disk.hash] = disk

            composite_key = indexing.get_attributes_md5(
                {"game_emulator_id": game_emulator_attrs["hash"], "disk_id": disk.hash}
            )
            game_emulator_disk = types.GameEmulatorDisk(
                id=0,
                game_emulator_id=game_emulator_attrs["hash"],
                disk_id=disk.hash,
            )
            dat_data["game_emulator_disk"][composite_key] = game_emulator_disk


def add_game_emulator_relationship(game_element: ET._Element, game: types.Game, emulator_hash: str, dat_data: DatData):
    game_emulator_attrs = {"game_id": game.hash, "emulator_id": emulator_hash}
    # We don't use the driver id as part of the primary key because we only want one game_emulator record per game/emulator
    # relationship. There is a risk here of orphaning driver records, which we need to check for elsewhere.
    game_emulator_attrs["hash"] = indexing.get_attributes_md5(
        {key: game_emulator_attrs[key] for key in ("game_id", "emulator_id")}
    )
    add_features(game_emulator_attrs, game_element, dat_data)
    add_driver(game_emulator_attrs, game_element, dat_data)
    add_disks(game_emulator_attrs, game_element, dat_data)
    game_emulator = types.GameEmulator(
        id=0,
        game_id=game.hash,
        emulator_id=emulator_hash,
        driver_id=game_emulator_attrs.get("driver_id"),
    )
    dat_data["game_emulator"][game_emulator_attrs["hash"]] = game_emulator


def process_games(root: ET._Element, emulator_attrs: dict[str, str]) -> DatData:
    dat_data = get_empty_dat_data()
    emulator_hash = emulator_attrs["id"]
    emulator = types.Emulator(
        id=0,
        hash=emulator_hash,
        name=emulator_attrs["name"],
        version=emulator_attrs["version"],
    )
    dat_data["emulators"][emulator_hash] = emulator

    for game_element in root:
        rom_elements = utils.get_sub_elements(game_element, "rom")
        if rom_elements:
            game = process_game(game_element, dat_data)
            if game is not None:
                add_game_emulator_relationship(game_element, game, emulator_hash, dat_data)
                dat_data["games"][game.hash] = game
    return dat_data


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


# Check emulator name as expected and that version matches expected format
def get_emulator_attrs(dat_file: str) -> dict[str, str]:
    emulator_name, emulator_version = get_mame_emulator_details(dat_file)
    id = f"{emulator_name.lower()}{emulator_version}".replace(" ", "").replace(".", "_")
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
    hash_to_id: dict[str, dict[str, int]] = {}
    next_id: dict[str, int] = {}

    # Assign numeric IDs to all entity tables
    entity_tables = ["games", "roms", "emulators", "disks", "features", "drivers"]
    for table in entity_tables:
        hash_to_id[table] = {}
        next_id[table] = 1
        for hash_key, entity in dat_data[table].items():
            new_id = next_id[table]
            hash_to_id[table][hash_key] = new_id
            entity.id = new_id  # Mutate dataclass in place
            next_id[table] += 1

    # Process game_emulator with foreign key updates
    hash_to_id["game_emulator"] = {}
    next_id["game_emulator"] = 1
    for hash_key, game_emulator in dat_data["game_emulator"].items():
        new_id = next_id["game_emulator"]
        hash_to_id["game_emulator"][hash_key] = new_id

        # Update all IDs in place
        game_emulator.id = new_id
        game_emulator.game_id = hash_to_id["games"][game_emulator.game_id]
        game_emulator.emulator_id = hash_to_id["emulators"][game_emulator.emulator_id]
        if game_emulator.driver_id:
            game_emulator.driver_id = hash_to_id["drivers"][game_emulator.driver_id]
        next_id["game_emulator"] += 1

    # Update foreign keys in join tables
    for game_rom in dat_data["game_rom"].values():
        game_rom.game_id = hash_to_id["games"][game_rom.game_id]
        game_rom.rom_id = hash_to_id["roms"][game_rom.rom_id]

    for game_emulator_feature in dat_data["game_emulator_feature"].values():
        game_emulator_feature.game_emulator_id = hash_to_id["game_emulator"][game_emulator_feature.game_emulator_id]
        game_emulator_feature.feature_id = hash_to_id["features"][game_emulator_feature.feature_id]

    for game_emulator_disk in dat_data["game_emulator_disk"].values():
        game_emulator_disk.game_emulator_id = hash_to_id["game_emulator"][game_emulator_disk.game_emulator_id]
        game_emulator_disk.disk_id = hash_to_id["disks"][game_emulator_disk.disk_id]

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

        # All values are now dataclasses, so just convert them all
        values = [asdict(item) for item in dat_data[key].values()]

        df = pd.DataFrame(values)
        if df.empty:
            print(f"  Skipping empty {key} dataframe...")
            continue

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
        dat_data = process_games(root, emulator_attrs)
        root.clear()
        return dat_data
    return get_empty_dat_data()


def process_dats_parallel(dats: list[str], out_dir: str, num_processes: int = 4):
    """Process DAT files in parallel using multiprocessing."""
    master_dat_data = get_empty_dat_data()
    print(f"Processing {len(dats)} DAT files using {num_processes} processes...")
    initial_memory = utils.log_memory("Initial memory (parallel processing):")

    with multiprocessing.Pool(processes=num_processes) as pool:
        # Use imap_unordered to consume results as they complete
        for i, dat_data in enumerate(pool.imap_unordered(dat_worker, dats)):
            if dat_data:
                print(f"Merging result {i+1}/{len(dats)}...")
                merge_dat_data(master_dat_data, dat_data)
                for key in dat_data:
                    dat_data[key].clear()
                dat_data.clear()
                del dat_data
                if (i + 1) % 10 == 0:
                    utils.log_memory(f"Processed {i+1}/{len(dats)} files - ")

    final_memory = utils.log_memory("Final memory:")
    print(f"Total memory growth: {final_memory - initial_memory:.2f} MB")  # noqa: E231

    write(master_dat_data, out_dir, csv=True)
