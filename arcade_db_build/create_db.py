#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

from typing import Optional, Type
import re
import os
import functools
import xml.etree.ElementTree as ET
from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, backref
from sqlalchemy.orm import relationship
from sqlalchemy.exc import NoResultFound

from .shared import shared

DATABASE_FILENAME = "arcade.db"
DATABASE_PATH = os.path.join(shared.PARENT_PATH, DATABASE_FILENAME)


class Base(DeclarativeBase):
    pass


game_rom_association = Table(
    "game_rom_association",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("rom_id", Integer, ForeignKey("roms.id")),
)

game_disk_association = Table(
    "game_disk_association",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("disk_id", Integer, ForeignKey("disks.id")),
)

game_emulator_feature = Table(
    "game_emulator_feature",
    Base.metadata,
    Column("game_emulator_id", Integer, ForeignKey("game_emulator.game_id")),
    Column("feature_id", Integer, ForeignKey("features.id")),
)


class GameEmulator(Base):
    __tablename__ = "game_emulator"
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    emulator_id = Column(Integer, ForeignKey("emulators.id"), primary_key=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    game = relationship("Game", back_populates="game_emulators")
    emulator = relationship("Emulator", back_populates="game_emulators")
    driver = relationship("Driver", back_populates="game_emulators")
    features = relationship("Feature", secondary=game_emulator_feature, back_populates="game_emulators")


# class GameDisk(Base):
#     __tablename__ = "game_disk"
#     game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
#     disk_id = Column(Integer, ForeignKey("disks.id"), primary_key=True)
#     game = relationship("Game", back_populates="game_disks")
#     disk = relationship("Disk", back_populates="game_disks")
#     status = Column(String)


class Emulator(Base):
    __tablename__ = "emulators"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    version = Column(String)
    game_emulators = relationship("GameEmulator", back_populates="emulator")


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    year = Column(Integer)
    manufacturer = Column(String)
    cloneof_id = Column(Integer, ForeignKey("games.id"))
    cloneof = relationship(
        "Game", foreign_keys=[cloneof_id], backref=backref("clones", foreign_keys=[cloneof_id]), remote_side=[id]
    )
    romof_id = Column(Integer, ForeignKey("games.id"))
    romof = relationship(
        "Game", foreign_keys=[romof_id], backref=backref("bios_children", foreign_keys=[romof_id]), remote_side=[id]
    )
    isbios = Column(String)
    isdevice = Column(String)
    runnable = Column(String)
    ismechanical = Column(String)
    game_emulators = relationship("GameEmulator", back_populates="game")
    disks = relationship("Disk", secondary=game_disk_association, back_populates="games")
    # TODO: What should happen when no games are associated with a rom?
    roms = relationship("Rom", secondary=game_rom_association, back_populates="games")


class Rom(Base):
    __tablename__ = "roms"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    size = Column(Integer)
    crc = Column(String)
    sha1 = Column(String)
    games = relationship("Game", secondary=game_rom_association, back_populates="roms")


class Disk(Base):
    """
    This is missing several fields pending further research into which are emulator version
    dependent.
    """

    __tablename__ = "disks"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    sha1 = Column(String)
    md5 = Column(String)
    games = relationship("Game", secondary=game_disk_association, back_populates="disks")


class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True)
    overall = Column(String)
    type = Column(String)
    status = Column(String)
    game_emulators = relationship("GameEmulator", secondary=game_emulator_feature, back_populates="features")


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    palettesize = Column(String)
    hiscoresave = Column(String)
    requiresartwork = Column(String)
    unofficial = Column(String)
    good = Column(String)
    status = Column(String)
    graphic = Column(String)
    cocktailmode = Column(String)
    savestate = Column(String)
    protection = Column(String)
    emulation = Column(String)
    cocktail = Column(String)
    color = Column(String)
    nosoundhardware = Column(String)
    sound = Column(String)
    incomplete = Column(String)
    game_emulators = relationship("GameEmulator", back_populates="driver")


def create_features(game_element: ET.Element) -> list[Feature]:
    features = []
    feature_elements = [element for element in game_element if element.tag == "feature"]
    for feature_element in feature_elements:
        feature = Feature(
            overall=feature_element.get("overall", None),
            type=feature_element.get("type", None),
            status=feature_element.get("status", None),
        )
        features.append(feature)
    return features


def create_driver(game_element: ET.Element) -> Optional[Driver]:
    driver_element = game_element.find("driver")
    # instances of ET.Element are falsey
    if driver_element is not None:
        driver = Driver(
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
    Base.metadata.create_all(engine)
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
def get_rom_elements(game_element: ET.Element) -> list[ET.Element]:
    return [element for element in game_element if element.tag == "rom"]


@functools.cache
def get_disk_elements(game_element: ET.Element) -> list[ET.Element]:
    return [element for element in game_element if element.tag == "disk"]


# def match_game_roms(existing_game: Game, rom_elements: list[ET.Element]) -> bool:
#     """
#     This matches only using CRC and size. Not all roms have a sha1 value. It may be better
#     to additionally match with sha1 when both the element and the existing record have one.
#     """
#     existing_game_roms = [(rom.name, rom.size, rom.crc) for rom in existing_game.roms]
#     roms = [(rom.get("name"), int(rom.get("size")), rom.get("crc")) for rom in rom_elements]  # type: ignore
#     if set(existing_game_roms) == set(roms):
#         return True
#     return False


def match_rom_with_rom_element(rom: Rom, rom_element: ET.Element) -> bool:
    if bool(rom.name == rom_element.get("name")):
        if bool(rom.size) and bool(rom_element.get("size")) and bool(rom.size == int(rom_element.get("size"))):  # type: ignore
            if bool(rom.crc == rom_element.get("crc")):
                return True
        if not any((bool(rom.crc), bool(rom_element.get("crc")))):
            return True
    return False


def match_rom_in_rom_elements(rom: Rom, rom_elements: list[ET.Element]) -> bool:
    for rom_element in rom_elements:
        if match_rom_with_rom_element(rom, rom_element):
            return True
    return False


def match_game_roms(existing_game: Game, rom_elements: list[ET.Element]) -> bool:
    if len(existing_game.roms) != len(rom_elements):
        return False
    for rom in existing_game.roms:
        if not match_rom_in_rom_elements(rom, rom_elements):
            return False
    return True


def match_disk_with_disk_element(disk: Disk, disk_element: ET.Element) -> bool:
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


def match_disk_in_disk_elements(disk: Disk, disk_elements: list[ET.Element]) -> bool:
    for disk_element in disk_elements:
        if match_disk_with_disk_element(disk, disk_element):
            return True
    return False


def match_game_disks(existing_game: Game, game_element: ET.Element) -> bool:
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
def get_existing_game(session: Session, game_element: ET.Element) -> Optional[Game]:
    # Reduce the number of checks for rom_elements
    if rom_elements := get_rom_elements(game_element):
        try:
            existing_games: list[Game] = get_existing_records(session, Game, {"name": game_element.get("name")})  # type: ignore
            for existing_game in existing_games:
                if match_game_roms(existing_game, rom_elements) and match_game_disks(existing_game, game_element):
                    return existing_game
        except NoResultFound:
            pass
    return None


# This is needed to keep the type checker happy
def get_rom_size(rom_element: ET.Element) -> Optional[int]:
    if size := rom_element.get("size"):
        return int(size)
    return None


def get_inner_element_text(outer_element: ET.Element, inner_element_name: str) -> Optional[str]:
    inner_element = outer_element.find(inner_element_name)  # Using := confuses type checker
    if inner_element is not None:
        return inner_element.text
    return None


# # Decide what to do when later MAME versions add attributes to an existing rom
# def get_or_create_roms(session: Session, rom_elements: list[ET.Element]) -> list[Rom]:
#     """
#     Looks for roms in the database with the same name, size and crc as the each of the
#     roms in the rom_elements list. If a match is found but does not have a sha1 value,
#     and the rom element does, the sha1 is added to the rom in the database.

#     Other attributes in a rom element which are not included in a match are not added,
#     pending further work to understand how version-specific these are.
#     """
#     roms = []
#     for rom_element in rom_elements:
#         attributes = {key: value for key, value in rom_element.items() if key in ("name", "size", "crc")}
#         if existing_roms := get_existing_records(session, Rom, attributes):
#             if len(existing_roms) > 1:
#                 print("Warning: Multiple roms found with the same name, size and crc ", existing_roms[0].name)  # type: ignore
#                 breakpoint()
#             if rom_element.get("sha1") and not existing_roms[0].sha1:  # type: ignore
#                 existing_roms[0].sha1 = rom_element.get("sha1")  # type: ignore
#             roms.append(existing_roms[0])  # Ugly
#         else:
#             rom = Rom(**attributes)
#             roms.append(rom)
#     return roms


# def get_existing_disk(session: Session, disk_element: ET.Element) -> Optional[Disk]:
#     """
#     Retrieves a list of Disk records from the database which share the same name as that of
#     the provided disk element. Then check for matching md5 or sha1 in that order. MAME DATs
#     up to (very roughly) around 0.7 use md5, from there to around 0.125 use both, and after
#     that sha1 only. Add the sha1 to any md5 matches where the sha1 exists in the disk element
#     but not the database record. This will maximise the number of records with a sha1.

#     Further research is needed on which other Disk fields are emulator version dependent
#     before deciding whether to add them to existing records as with sha1.
#     """
#     try:
#         disk_name_matches: list[Disk] = get_existing_records(session, Disk, {"name": disk_element.get("name", "")})  # type: ignore
#         for match in disk_name_matches:
#             if match_disk_with_disk_element(match, disk_element):
#                 # if not bool(match.sha1) and bool(sha1 := disk_element.get("sha1", "")):
#                 #     match.sha1 = sha1  # type: ignore
#                 return match
#     except NoResultFound:
#         pass
#     return None


# Decide what to do when later MAME versions add attributes to an existing rom
def get_or_create_roms(session: Session, rom_elements: list[ET.Element]) -> list[Rom]:
    roms = []
    for rom_element in rom_elements:
        matched_rom = None
        if name_matches := get_existing_records(session, Rom, {"name": rom_element.get("name")}):  # type: ignore
            for match in name_matches:
                if match_rom_with_rom_element(match, rom_element):  # type: ignore
                    matched_rom = match
        if not matched_rom:
            matched_rom = Rom(
                name=rom_element.get("name", None),
                size=get_rom_size(rom_element),
                crc=rom_element.get("crc", None),
                sha1=rom_element.get("sha1", None),
            )
        roms.append(matched_rom)
    return roms


def get_or_create_disks(session: Session, disk_elements: list[ET.Element]) -> list[Disk]:
    disks = []
    for disk_element in disk_elements:
        matched_disk = None
        if name_matches := get_existing_records(session, Disk, {"name": disk_element.get("name")}):  # type: ignore
            for disk in name_matches:
                if match_disk_with_disk_element(disk, disk_element):  # type: ignore
                    matched_disk = disk
        if not matched_disk:
            matched_disk = Disk(
                name=disk_element.get("name", None),
                sha1=disk_element.get("sha1", None),
                md5=disk_element.get("md5", None),
            )
        disks.append(matched_disk)
    return disks


# Get description, year and manufacturer
def create_game(session: Session, game_element: ET.Element) -> Optional[Game]:  # Tighten this
    if rom_elements := get_rom_elements(game_element):  # Also checked in process_games
        game = Game(
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


def create_game_references(game_element: ET.Element) -> Optional[dict[str, str]]:
    references = {}
    for reference in ("cloneof", "romof"):
        if reference_target := game_element.get(reference, None):
            references[reference] = reference_target
    if references:
        return references
    return None


def add_features(session: Session, game_emulator: GameEmulator, game_element: ET.Element):
    added_features = []
    if found_features := create_features(game_element):
        for feature in found_features:
            if feature_query_result := get_existing_records(
                session, Feature, get_instance_attributes(feature, Feature)
            ):
                added_features.append(feature_query_result[0])
            else:
                added_features.append(feature)
        game_emulator.features.extend(added_features)
        session.add_all(added_features)


def add_driver(session: Session, game_emulator: GameEmulator, game_element: ET.Element):
    added_driver = None
    if found_driver := create_driver(game_element):
        if driver_query_result := get_existing_records(session, Driver, get_instance_attributes(found_driver, Driver)):
            added_driver = driver_query_result[0]  # This is a bit ugly
        else:
            added_driver = found_driver
        game_emulator.driver = added_driver
        session.add(added_driver)


def add_game_emulator_relationship(session: Session, game_element: ET.Element, game: Game, emulator: Emulator):
    game_emulator = GameEmulator(game=game, emulator=emulator)
    session.add(game_emulator)
    add_features(session, game_emulator, game_element)
    add_driver(session, game_emulator, game_element)


def process_games(session: Session, root: ET.Element, emulator: Emulator):
    all_references = []
    new_games = 0
    total_games = 0
    for element in root:
        rom_elements = get_rom_elements(element)
        if rom_elements:
            game = get_existing_game(session, element)
            if not game:
                # Returns None if no rom elements are found
                game = create_game(session, element)
                session.add(game)
                new_games += 1
            if game:
                add_game_emulator_relationship(session, element, game, emulator)
                session.commit()
                total_games += 1
                if game_references := create_game_references(element):
                    game_references["id"] = str(game.id)
                    all_references.append(game_references)

    return all_references, new_games, total_games


def add_game_reference(session: Session, game: Game, emulator: Emulator, field: str, target_game_name: str):
    if bool(game.name != target_game_name):
        target_game = (
            session.query(Game)
            .filter(Game.name == target_game_name, Game.game_emulators.any(emulator=emulator))
            .first()
        )
        if target_game:
            setattr(game, field, target_game)
            return True
    else:
        # Consider adding the reference as a success so it's not added to the remaining references
        # There's probably a better way to handle this
        return True
    return False


def add_game_references(session: Session, emulator: Emulator, game_references: dict[str, str], game: Game):
    for key in ["cloneof", "romof"]:
        if target_game_name := game_references.get(key):
            if add_game_reference(session, game, emulator, key, target_game_name):
                del game_references[key]


def add_all_game_references(session: Session, emulator: Emulator, all_references: list[dict[str, str]]):
    total_refs = len(all_references)
    remaining_refs = len(all_references)
    for game_references in all_references:
        game = session.query(Game).filter(Game.id == game_references["id"]).first()
        if game:
            add_game_references(session, emulator, game_references, game)
            session.commit()
            if list(game_references.keys()) == ["id"]:
                remaining_refs -= 1
            # Log the unhandled references so they can be investigated
    return total_refs, remaining_refs


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


def process_dats(session: Session, dats: list[str]):
    for dat_file in dats:
        emulator_name, emulator_version = get_mame_emulator_details(dat_file)
        emulator = Emulator(name=emulator_name, version=emulator_version)
        session.add(emulator)
        session.commit()
        source = shared.get_source_contents(dat_file)
        root = shared.get_source_root(source)
        all_references, new_games, total_games = process_games(session, root, emulator)
        (
            total_refs,
            unhandled_refs,
        ) = add_all_game_references(session, emulator, all_references)
        print(
            f"DAT: {os.path.basename(dat_file)} - Total: {total_games}, New: {new_games} - Total Refs: {total_refs}, Unhandled Refs: {unhandled_refs}"
        )


def extract_mame_version(filename):
    version = filename.replace("MAME ", "").replace(".xml.bz2", "")
    version = re.sub(r"\D", "", version)
    return float(version) if version else 0


def create_db():
    session = get_session(DATABASE_PATH)
    sorted_dats = sorted(shared.MAME_DATS, key=extract_mame_version)
    process_dats(session, sorted_dats)

    # test_dats = ["/home/jimnarey/projects/romscripts/arcade_db_build/mame_db_source/dats/MAME 0.86.xml.bz2"]
    # process_dats(session, test_dats)
    session.close()
