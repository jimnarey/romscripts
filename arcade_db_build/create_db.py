#!/usr/bin/env python
from typing import Optional, Type
import re
import os
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


game_emulator_feature = Table(
    "game_emulator_feature",
    Base.metadata,
    Column("game_emulator_id", Integer, ForeignKey("game_emulator.game_id")),
    Column("feature_id", Integer, ForeignKey("features.id")),
)


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


class GameEmulator(Base):
    __tablename__ = "game_emulator"
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    emulator_id = Column(Integer, ForeignKey("emulators.id"), primary_key=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    game = relationship("Game", back_populates="game_emulators")
    emulator = relationship("Emulator", back_populates="game_emulators")
    driver = relationship("Driver", back_populates="game_emulators")
    features = relationship("Feature", secondary=game_emulator_feature, back_populates="game_emulators")


class Emulator(Base):
    __tablename__ = "emulators"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    version = Column(String)
    game_emulators = relationship("GameEmulator", back_populates="emulator")


class Game(Base):
    """
    This can be improved by adding a model for yes/no choices and
    using references for clone_of and rom_of which are assigned on
    a second pass through the data (just in case any XML declares
    a clone before a parent)
    """

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
    is_bios = Column(String)
    is_device = Column(String)
    runnable = Column(String)
    ismechanical = Column(String)
    game_emulators = relationship("GameEmulator", back_populates="game")
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


def get_session(db_path: str) -> Session:
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def get_instance_attributes(instance: DeclarativeBase, model_class: Type[DeclarativeBase]) -> dict[str, str]:
    """
    Return instance attributes with the exception of the primary key and
    any relationships.
    """
    primary_key_column = inspect(model_class).primary_key[0].key
    instance_attrs = {c.key: getattr(instance, c.key) for c in inspect(instance).mapper.column_attrs}
    instance_attrs.pop(primary_key_column, None)
    return instance_attrs


def get_existing_records(
    session: Session, model_class: Type[DeclarativeBase], instance_attrs: dict[str, str]
) -> list[DeclarativeBase]:
    existing_records = session.query(model_class).filter_by(**instance_attrs).all()
    # breakpoint()
    return existing_records


def get_existing_game(session: Session, game: Game) -> Optional[Game]:
    try:
        existing_games: list[Game] = get_existing_records(session, Game, {"name": str(game.name)})  # type: ignore
        for existing_game in existing_games:
            existing_game_roms = [(rom.name, rom.size, rom.crc, rom.sha1) for rom in existing_game.roms]
            game_roms = [(rom.name, rom.size, rom.crc, rom.sha1) for rom in game.roms]
            if set(existing_game_roms) == set(game_roms):
                return existing_game
    except NoResultFound:
        pass
    return None


def create_features(game_element: ET.Element) -> list[Feature]:
    features = []
    feature_elements = [element for element in game_element if element.tag == "feature"]
    for feature_element in feature_elements:
        feature = Feature(
            overall=feature_element.get("overall", ""),
            type=feature_element.get("type", ""),
            status=feature_element.get("status", ""),
        )
        features.append(feature)
    return features


def create_driver(game_element: ET.Element) -> Optional[Driver]:
    driver_element = game_element.find("driver")
    # driver_element is falsey!
    if driver_element is not None:
        driver = Driver(
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
        return driver
    return None


# def create_roms(rom_elements: list[ET.Element]) -> list[Rom]:
#     roms = []
#     for rom_element in rom_elements:
#         rom = Rom(
#             name=rom_element.get("name", ""),
#             size=int(rom_element.get("size", 0)),
#             crc=rom_element.get("crc", ""),
#             sha1=rom_element.get("sha1", ""),
#         )
#         roms.append(rom)
#     return roms


def get_or_create_roms(session: Session, rom_elements: list[ET.Element]) -> list[Rom]:
    """
    Need to think about how to handle existing roms which have additional attributes
    in later DATs.
    """
    roms = []
    for rom_element in rom_elements:
        rom = Rom(
            name=rom_element.get("name", ""),
            size=int(rom_element.get("size", 0)),
            crc=rom_element.get("crc", ""),
            sha1=rom_element.get("sha1", ""),
        )
        if existing_roms := get_existing_records(session, Rom, get_instance_attributes(rom, Rom)):
            roms.append(existing_roms[0])  # Ugly
        else:
            roms.append(rom)
    return roms


def create_game_references(game_element: ET.Element) -> Optional[dict[str, str]]:
    references = {}
    for reference in ("cloneof", "romof"):
        if reference_target := game_element.get(reference, None):
            references[reference] = reference_target
    if references:
        return references
    return None


def create_game(session: Session, game_element: ET.Element) -> tuple[Optional[Game], Optional[dict]]:  # Tighten this
    rom_elements = [element for element in game_element if element.tag == "rom"]
    if rom_elements:
        game = Game(
            name=game_element.get("name", ""),
            description=game_element.get("description", ""),
            year=int(game_element.get("year", 0)),
            manufacturer=game_element.get("manufacturer", ""),
            is_bios=game_element.get("isbios", ""),
            is_device=game_element.get("isdevice", ""),
            runnable=game_element.get("runnable", ""),
            ismechanical=game_element.get("ismechanical", ""),
        )
        game.roms = get_or_create_roms(session, rom_elements)
        game_references = create_game_references(game_element)
        return game, game_references
    return None, None


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


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


def add_game_emulator_relationship(
    session: Session, game_element: ET.Element, game: Game, emulator: Emulator, action: str = "added"
):
    # print(f"Game {action}: {game.name}")
    game_emulator = GameEmulator(game=game, emulator=emulator)
    session.add(game_emulator)
    add_features(session, game_emulator, game_element)
    add_driver(session, game_emulator, game_element)


def process_games(session: Session, root: ET.Element, emulator: Emulator):
    all_references = []
    num_existing_games = 0
    num_new_games = 0
    for element in root:
        game, game_references = create_game(session, element)
        if game:
            if existing_game := get_existing_game(session, game):
                processing_game = existing_game
                num_existing_games += 1
            else:
                processing_game = game
                num_new_games += 1
                session.add(game)
            add_game_emulator_relationship(session, element, processing_game, emulator, action="updated")
            session.commit()
            if game_references:
                game_references["id"] = str(processing_game.id)
                all_references.append(game_references)

    return all_references, num_existing_games, num_new_games


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
    reference_count = len(all_references)
    for game_references in all_references:
        game = session.query(Game).filter(Game.id == game_references["id"]).first()
        if game:
            add_game_references(session, emulator, game_references, game)
            session.commit()
            if list(game_references.keys()) == ["id"]:
                reference_count -= 1
            # Log the unhandled references so they can be investigated
    print(f"Unhandled references: {reference_count}")


def process_dats(session: Session, dats: list[str]):
    for dat_file in dats:
        print(f"Processing: {dat_file}")
        emulator_name, emulator_version = get_mame_emulator_details(dat_file)
        emulator = Emulator(name=emulator_name, version=emulator_version)
        session.add(emulator)
        session.commit()
        source = shared.get_source_contents(dat_file)
        root = shared.get_source_root(source)
        all_references, num_existing_games, num_new_games = process_games(session, root, emulator)
        add_all_game_references(session, emulator, all_references)
        print(
            f"Emulator: {emulator_name} {emulator_version} - Existing Games: {num_existing_games}, New Games: {num_new_games}"
        )


def extract_mame_version(filename):
    version = filename.replace("MAME ", "").replace(".xml.bz2", "")
    version = re.sub(r"\D", "", version)
    return float(version) if version else 0


def create_db():
    session = get_session(DATABASE_PATH)
    sorted_dats = sorted(shared.MAME_DATS, key=extract_mame_version)
    process_dats(session, sorted_dats)
    session.close()


# if __name__ == "__main__":
#     session = get_session(DATABASE_PATH)
#     sorted_dats = sorted(shared.MAME_DATS, key=extract_mame_version)
#     process_dats(session, sorted_dats)
#     session.close()

# TODO: Fix rom cross-referencing
# Add sourcefile to game/machine
# Add disk model and read from DATs. Use validation script to get all possible attributes
# Add bios field to rom model. Work out what biosset in game elements is for
# Normalise underscoring in Game field names (is_bios etc)
# Time each DAT and get an average time per game
# Count the number of games in the validation script so we can calculate a total build time
# Log any unhandled references
# Consider logging any invalid references (circular)
# Add FBA parsing
# Add FBN DATs and parsing
# Enable updating an existing database with new DATs

# Re-order
# Get existing game based on game attributes. Don't instantiate a new game to do this
# If it exists, add the emulator (already in the session)
# If it doesn't, create a new game, add to the session and add the game_emulator/emulator
# Get any existing roms, create any new roms, add to session and to new game
# commit
