#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

# TODO: Add Chip table and create records for non-rom machines (e.g. famicom)
# TODO: Investigate and implement the use of the 'merge' attribute in Rom elements. Validate parameters for merge attributes.
# TODO: Change calls to .first to .one_or_none or .one

from typing import Optional, Type
import warnings
import os

from lxml import etree as ET
import psutil
from sqlalchemy import inspect
from sqlalchemy.orm import Session, DeclarativeBase

from .shared import db, sources, utils, indexing


def check_cpu_utilization(threshold=90):
    cpu_usages = psutil.cpu_percent(percpu=True)
    for i, cpu_usage in enumerate(cpu_usages):
        if cpu_usage > threshold:
            warnings.warn(f"CPU core {i} usage is {cpu_usage}%")


def check_memory_utilization(threshold=90):
    memory_usage = psutil.virtual_memory().percent
    if memory_usage > threshold:
        warnings.warn(f"Memory usage is {memory_usage}%")


def get_instance_attributes(instance: DeclarativeBase, model_class: Type[DeclarativeBase]) -> dict[str, str]:
    """
    Return instance attributes with the exception of the primary key and any relationships.
    """
    primary_key_column = inspect(model_class).primary_key[0].key
    instance_attrs = {c.key: getattr(instance, c.key) for c in inspect(instance).mapper.column_attrs}
    instance_attrs.pop(primary_key_column, None)
    return instance_attrs


def get_existing_game(session: Session, game_element: ET._Element) -> Optional[db.Game]:
    """
    Will call the indexing function(s) with disk hash type md5 if there are no disk elements
    This is fine for the current implementation. Remember if refactoring.
    """
    rom_elements = utils.get_sub_elements(game_element, "rom")
    index_value = indexing.get_game_index_from_elements(game_element.get("name", ""), rom_elements)
    if existing_game := session.query(db.Game).filter_by(name_roms_index=index_value).first():
        return existing_game
    return None


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


# Decide what to do when later MAME versions add attributes to an existing rom
def get_or_create_roms(session: Session, rom_elements: list[ET._Element]) -> list[db.Rom]:
    roms = []
    for rom_element in rom_elements:
        rom = (
            session.query(db.Rom)
            .filter_by(name=rom_element.get("name"), size=rom_element.get("size"), crc=rom_element.get("crc"))
            .first()
        )
        if not rom:
            rom = db.Rom(
                name=rom_element.get("name", ""),
                size=get_rom_size(rom_element),
                crc=rom_element.get("crc", ""),
                sha1=rom_element.get("sha1", None),
            )
        roms.append(rom)
    return roms


def get_existing_disk(session: Session, disk_element: ET._Element) -> Optional[db.Disk]:
    if disk_element.get("sha1"):
        if (
            disk := session.query(db.Disk)
            .filter_by(name=disk_element.get("name"), sha1=disk_element.get("sha1"))
            .first()
        ):
            return disk
    if disk_element.get("md5"):
        if disk := session.query(db.Disk).filter_by(name=disk_element.get("name"), md5=disk_element.get("md5")).first():
            return disk
    return None


def get_or_create_disks(session: Session, disk_elements: list[ET._Element]) -> list[db.Disk]:
    disks = []
    for disk_element in disk_elements:
        if not (disk := get_existing_disk(session, disk_element)):
            disk = db.Disk(
                name=disk_element.get("name", ""),
                sha1=disk_element.get("sha1", ""),
                md5=disk_element.get("md5", ""),
            )
        disks.append(disk)
    return disks


def create_game(session: Session, game_element: ET._Element) -> Optional[db.Game]:
    if rom_elements := utils.get_sub_elements(game_element, "rom"):
        game = db.Game(
            name=game_element.get("name", ""),
            description=get_inner_element_text(game_element, "description"),
            year=get_inner_element_text(game_element, "year"),
            manufacturer=get_inner_element_text(game_element, "manufacturer"),
            isbios=game_element.get("isbios"),
            isdevice=game_element.get("isdevice"),
            runnable=game_element.get("runnable"),
            ismechanical=game_element.get("ismechanical"),
        )
        game.roms = get_or_create_roms(session, rom_elements)
        return game
    return None


def get_feature_element_attributes(feature_element: ET._Element) -> dict[str, Optional[str]]:
    return {
        "overall": feature_element.get("overall", ""),
        "type": feature_element.get("type", ""),
        "status": feature_element.get("status", ""),
    }


def add_features(session: Session, game_emulator: db.GameEmulator, game_element: ET._Element):
    for feature_element in game_element.findall("feature"):
        feature_attributes = get_feature_element_attributes(feature_element)
        if not (feature := session.query(db.Feature).filter_by(**feature_attributes).first()):
            feature = db.Feature(**feature_attributes)
        game_emulator.features.append(feature)
    session.add_all(game_emulator.features)


def get_driver_element_attributes(driver_element: ET._Element) -> dict[str, Optional[str]]:
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


def add_driver(session: Session, game_emulator: db.GameEmulator, game_element: ET._Element):
    if (driver_element := game_element.find("driver")) is not None:
        driver_attributes = get_driver_element_attributes(driver_element)
        if not (driver := session.query(db.Driver).filter_by(**driver_attributes).first()):
            driver = db.Driver(**driver_attributes)
        game_emulator.driver = driver
        session.add(driver)


# TODO: Can probably avoid using get_sub_elements.
def add_disks(session: Session, game_emulator: db.GameEmulator, game_element: ET._Element):
    if disk_elements := utils.get_sub_elements(game_element, "disk"):
        disks = get_or_create_disks(session, disk_elements)
        game_emulator.disks.extend(disks)
        session.add_all(game_emulator.features)


def add_game_emulator_relationship(session: Session, game_element: ET._Element, game: db.Game, emulator: db.Emulator):
    game_emulator = db.GameEmulator(game=game, emulator=emulator)
    session.add(game_emulator)
    add_features(session, game_emulator, game_element)
    add_driver(session, game_emulator, game_element)
    add_disks(session, game_emulator, game_element)


def add_game_reference(
    session: Session, game: db.Game, emulator: db.Emulator, attribute: str, target_game_name: str
) -> bool:
    """
    Add a reference to another game to a game object.
    field: either "cloneof" or "romof"
    """
    target_game = (
        session.query(db.Game)
        .filter(db.Game.name == target_game_name, db.Game.game_emulators.any(emulator=emulator))
        .first()
    )
    if target_game:
        setattr(game, attribute, target_game)
        return True

    return False


def add_game_references(session: Session, emulator: db.Emulator, game: db.Game, game_element: ET._Element):
    """
    Resolves the game > game references for a single game.
    """
    unhandled_references = []
    for attribute in ("cloneof", "romof"):
        if target_game_name := game_element.get(attribute):
            if bool(game.name != target_game_name):
                if not add_game_reference(session, game, emulator, attribute, target_game_name):
                    unhandled_references.append({"game": game.name, "attribute": attribute, "target": target_game_name})
    return unhandled_references


def process_games(session: Session, root: ET._Element, emulator: db.Emulator):
    unhanded_references = []
    new_games = 0
    total_games = 0
    for game_element in root:
        rom_elements = utils.get_sub_elements(game_element, "rom")
        if rom_elements:
            game = get_existing_game(session, game_element)
            if not game:
                game = create_game(session, game_element)
                session.add(game)
                new_games += 1
            if game:
                add_game_emulator_relationship(session, game_element, game, emulator)
                session.commit()  # Is this needed!?
                total_games += 1
                unhanded_references.extend(add_game_references(session, emulator, game, game_element))
        session.commit()
        check_memory_utilization()
        session.expunge_all()
    return new_games, total_games, unhanded_references


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


def create_emulator(session: Session, dat_file: str) -> db.Emulator:
    emulator_name, emulator_version = get_mame_emulator_details(dat_file)
    emulator = db.Emulator(name=emulator_name, version=emulator_version)
    session.add(emulator)
    session.commit()
    return emulator


def process_dats(session: Session, dats: list[str]):
    for dat_file in dats:
        emulator = create_emulator(session, dat_file)
        if (root := sources.get_dat_root(dat_file)) is not None:
            new_games, total_games, unhandled_references = process_games(session, root, emulator)
            check_memory_utilization()
            print(f"DAT: {os.path.basename(dat_file)} - Total: {total_games}, New: {new_games}")
            if unhandled_references:
                print(f"{'Name':<10}\t{'Attribute':<10}\t{'Target Game':<10}")
                for ref in unhandled_references:
                    print(f"{ref['game']:<10}\t{ref['attribute']:<10}\t{ref['target']:<10}")
