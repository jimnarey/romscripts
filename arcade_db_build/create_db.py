#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

from typing import Optional, Type

import warnings
import os
import functools
from lxml import etree as ET
import psutil

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.exc import NoResultFound

from .shared import shared, db


def check_cpu_utilization(threshold=90):
    cpu_usages = psutil.cpu_percent(percpu=True)
    for i, cpu_usage in enumerate(cpu_usages):
        if cpu_usage > threshold:
            warnings.warn(f"CPU core {i} usage is {cpu_usage}%")


def check_memory_utilization(threshold=90):
    memory_usage = psutil.virtual_memory().percent
    if memory_usage > threshold:
        warnings.warn(f"Memory usage is {memory_usage}%")


def create_features(game_element: ET._Element) -> list[db.Feature]:
    features = []
    feature_elements = [element for element in game_element if element.tag == "feature"]
    for feature_element in feature_elements:
        feature = db.Feature(
            overall=feature_element.get("overall", None),
            type=feature_element.get("type", None),
            status=feature_element.get("status", None),
        )
        features.append(feature)
    return features


def create_driver(game_element: ET._Element) -> Optional[db.Driver]:
    driver_element = game_element.find("driver")
    # instances of ET.Element are falsey
    if driver_element is not None:
        driver = db.Driver(
            palettesize=driver_element.get("palettesize", None),
            hiscoresave=driver_element.get("hiscoresave", None),
            requiresartwork=driver_element.get("requiresartwork", None),
            unofficial=driver_element.get("unofficial", None),
            good=driver_element.get("good", None),
            status=driver_element.get("status", None),
            graphic=driver_element.get("graphic", None),
            cocktailmode=driver_element.get("cocktailmode", None),
            savestate=driver_element.get("savestate", None),
            protection=driver_element.get("protection", None),
            emulation=driver_element.get("emulation", None),
            cocktail=driver_element.get("cocktail", None),
            color=driver_element.get("color", None),
            nosoundhardware=driver_element.get("nosoundhardware", None),
            sound=driver_element.get("sound", None),
            incomplete=driver_element.get("incomplete", None),
        )
        return driver
    return None


def get_session(db_path: str) -> Session:
    engine = create_engine(f"sqlite:///{db_path}")
    db.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def get_instance_attributes(instance: DeclarativeBase, model_class: Type[DeclarativeBase]) -> dict[str, str]:
    """
    Return instance attributes with the exception of the primary key and any relationships.
    """
    primary_key_column = inspect(model_class).primary_key[0].key
    instance_attrs = {c.key: getattr(instance, c.key) for c in inspect(instance).mapper.column_attrs}
    instance_attrs.pop(primary_key_column, None)
    return instance_attrs


def get_existing_records(
    session: Session, model_class: Type[DeclarativeBase], instance_attrs: dict[str, str]
) -> list[DeclarativeBase]:
    # Warning in MAME 0.85
    existing_records = session.query(model_class).filter_by(**instance_attrs).all()
    return existing_records


# Merge these two functions
@functools.cache
def get_rom_elements(game_element: ET._Element) -> list[ET._Element]:
    return [element for element in game_element if element.tag == "rom"]


@functools.cache
def get_disk_elements(game_element: ET._Element) -> list[ET._Element]:
    return [element for element in game_element if element.tag == "disk"]


def match_rom_with_rom_element(rom: db.Rom, rom_element: ET._Element) -> bool:
    if bool(rom.name == rom_element.get("name")):
        if bool(rom.size) and bool(rom_element.get("size")) and bool(rom.size == int(rom_element.get("size"))):  # type: ignore
            if bool(rom.crc == rom_element.get("crc")):
                return True
        if not any((bool(rom.crc), bool(rom_element.get("crc")))):
            return True
    return False


def match_rom_in_rom_elements(rom: db.Rom, rom_elements: list[ET._Element]) -> bool:
    for rom_element in rom_elements:
        if match_rom_with_rom_element(rom, rom_element):
            return True
    return False


def match_game_roms(existing_game: db.Game, rom_elements: list[ET._Element]) -> bool:
    if len(existing_game.roms) != len(rom_elements):
        return False
    for rom in existing_game.roms:
        if not match_rom_in_rom_elements(rom, rom_elements):
            return False
    return True


def match_disk_with_disk_element(disk: db.Disk, disk_element: ET._Element) -> bool:
    """
    Checks a provided disk object against a disk elements. An element is
    considered a match if the disk name matches the element name and either the md5
    or sha1 matches.

    A disk is also a match against an element if both have the same name and neither
    have an md5 or sha1 value. This is to handle games where a disk is defined but
    recorded as not yet dumped.
    """
    if bool(disk.name == disk_element.get("name")):
        if bool(disk.md5) and bool(disk.md5 == disk_element.get("md5")):
            return True
        if bool(disk.sha1) and bool(disk.sha1 == disk_element.get("sha1")):
            return True
        if not any((bool(disk.md5), bool(disk.sha1), disk_element.get("md5"), disk_element.get("sha1"))):
            return True
    return False


def match_disk_in_disk_elements(disk: db.Disk, disk_elements: list[ET._Element]) -> bool:
    for disk_element in disk_elements:
        if match_disk_with_disk_element(disk, disk_element):
            return True
    return False


def match_game_disks(existing_game: db.Game, game_element: ET._Element) -> bool:
    """
    Checks that the number of disks in the existing game matches the number of disk
    elements in the provided list. Then checks each disk in the existing game against
    the disk elements to check whether each has a match.

    This is more complex than matching roms. All roms, in every MAME DAT, have a CRC.
    With disks we have a mix of sha1, md5 or both.
    """
    disk_elements = get_disk_elements(game_element)
    if len(existing_game.disks) != len(disk_elements):
        return False
    for disk in existing_game.disks:
        if not match_disk_in_disk_elements(disk, disk_elements):
            return False
    return True


# What happens if None is passed as the game name to get_existing_records?
def get_existing_game(session: Session, game_element: ET._Element) -> Optional[db.Game]:
    # Reduce the number of checks for rom_elements
    if rom_elements := get_rom_elements(game_element):
        try:
            existing_games: list[db.Game] = get_existing_records(session, db.Game, {"name": game_element.get("name")})  # type: ignore
            for existing_game in existing_games:
                if match_game_roms(existing_game, rom_elements) and match_game_disks(existing_game, game_element):
                    return existing_game
        except NoResultFound:
            pass
    return None


# This is needed to keep the type checker happy
def get_rom_size(rom_element: ET._Element) -> Optional[int]:
    if size := rom_element.get("size"):
        return int(size)
    return None


def get_inner_element_text(outer_element: ET._Element, inner_element_name: str) -> Optional[str]:
    inner_element = outer_element.find(inner_element_name)  # Using := confuses type checker
    if inner_element is not None:
        return inner_element.text
    return None


# Decide what to do when later MAME versions add attributes to an existing rom
def get_or_create_roms(session: Session, rom_elements: list[ET._Element]) -> list[db.Rom]:
    roms = []
    for rom_element in rom_elements:
        matched_rom = None
        if name_matches := get_existing_records(session, db.Rom, {"name": rom_element.get("name")}):  # type: ignore
            for match in name_matches:
                if match_rom_with_rom_element(match, rom_element):  # type: ignore
                    matched_rom = match
        if not matched_rom:
            matched_rom = db.Rom(
                name=rom_element.get("name", None),
                size=get_rom_size(rom_element),
                crc=rom_element.get("crc", None),
                sha1=rom_element.get("sha1", None),
            )
        roms.append(matched_rom)
    return roms


def get_or_create_disks(session: Session, disk_elements: list[ET._Element]) -> list[db.Disk]:
    disks = []
    for disk_element in disk_elements:
        matched_disk = None
        if name_matches := get_existing_records(session, db.Disk, {"name": disk_element.get("name")}):  # type: ignore
            for disk in name_matches:
                if match_disk_with_disk_element(disk, disk_element):  # type: ignore
                    matched_disk = disk
        if not matched_disk:
            matched_disk = db.Disk(
                name=disk_element.get("name", None),
                sha1=disk_element.get("sha1", None),
                md5=disk_element.get("md5", None),
            )
        disks.append(matched_disk)
    return disks


# Get description, year and manufacturer
def create_game(session: Session, game_element: ET._Element) -> Optional[db.Game]:  # Tighten this
    if rom_elements := get_rom_elements(game_element):  # Also checked in process_games
        game = db.Game(
            name=game_element.get("name"),
            description=get_inner_element_text(game_element, "description"),
            year=get_inner_element_text(game_element, "year"),
            manufacturer=get_inner_element_text(game_element, "manufacturer"),
            isbios=game_element.get("isbios"),
            isdevice=game_element.get("isdevice"),
            runnable=game_element.get("runnable"),
            ismechanical=game_element.get("ismechanical"),
        )
        game.roms = get_or_create_roms(session, rom_elements)
        if disk_elements := get_disk_elements(game_element):
            game.disks = get_or_create_disks(session, disk_elements)
        return game
    return None


def add_features(session: Session, game_emulator: db.GameEmulator, game_element: ET._Element):
    added_features = []
    if found_features := create_features(game_element):
        for feature in found_features:
            if feature_query_result := get_existing_records(
                session, db.Feature, get_instance_attributes(feature, db.Feature)
            ):
                added_features.append(feature_query_result[0])
            else:
                added_features.append(feature)
        game_emulator.features.extend(added_features)
        session.add_all(added_features)


def add_driver(session: Session, game_emulator: db.GameEmulator, game_element: ET._Element):
    added_driver = None
    if found_driver := create_driver(game_element):
        if driver_query_result := get_existing_records(
            session, db.Driver, get_instance_attributes(found_driver, db.Driver)
        ):
            added_driver = driver_query_result[0]  # This is a bit ugly
        else:
            added_driver = found_driver
        game_emulator.driver = added_driver
        session.add(added_driver)


def add_game_emulator_relationship(session: Session, game_element: ET._Element, game: db.Game, emulator: db.Emulator):
    game_emulator = db.GameEmulator(game=game, emulator=emulator)
    session.add(game_emulator)
    add_features(session, game_emulator, game_element)
    add_driver(session, game_emulator, game_element)


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
        rom_elements = get_rom_elements(game_element)
        if rom_elements:
            game = get_existing_game(session, game_element)
            if not game:
                # Returns None if no rom elements are found
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
        if (root := shared.get_dat_root(dat_file)) is not None:
            new_games, total_games, unhandled_references = process_games(session, root, emulator)
            check_memory_utilization()
            print(f"DAT: {os.path.basename(dat_file)} - Total: {total_games}, New: {new_games}")
            if unhandled_references:
                print(f"{'Name':<10}\t{'Attribute':<10}\t{'Target Game':<10}")
                for ref in unhandled_references:
                    print(f"{ref['game']:<10}\t{ref['attribute']:<10}\t{ref['target']:<10}")
