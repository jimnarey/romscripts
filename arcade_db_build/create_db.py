#!/usr/bin/env python

from typing import Optional
import os
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
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


game_emulator_association = Table(
    "game_emulator_association",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("emulator_id", Integer, ForeignKey("emulators.id")),
)


class Emulator(Base):
    __tablename__ = "emulators"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    version = Column(String)
    games = relationship("Game", secondary=game_emulator_association, back_populates="emulators")


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    is_bios = Column(Boolean)
    name = Column(String)
    # TODO: Add description
    year = Column(Integer)
    manufacturer = Column(String)
    emulators = relationship("Emulator", secondary=game_emulator_association, back_populates="games")
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


def create_roms(rom_elements: list[ET.Element]) -> list[Rom]:
    roms = []
    for rom_element in rom_elements:
        rom = Rom(
            name=rom_element.get("name", ""),
            size=int(rom_element.get("size", 0)),
            crc=rom_element.get("crc", ""),
            sha1=rom_element.get("sha1", ""),
        )
        roms.append(rom)
    return roms


def get_existing_game(session: Session, game: Game) -> Optional[Game]:
    try:
        existing_game = (
            session.query(Game)
            .filter(
                # TODO: just search on game name
                Game.is_bios == game.is_bios,
                Game.name == game.name,
                Game.year == game.year,
                Game.manufacturer == game.manufacturer,
            )
            .one()
        )
        # TODO: deal with multiple games with same basic attributes
        existing_game_roms = [(rom.name, rom.size, rom.crc, rom.sha1) for rom in existing_game.roms]
        game_roms = [(rom.name, rom.size, rom.crc, rom.sha1) for rom in game.roms]
        if set(existing_game_roms) == set(game_roms):
            return existing_game
    except NoResultFound:
        pass
    return None


def create_game(game_element: ET.Element) -> Optional[Game]:
    rom_elements = [element for element in game_element if element.tag == "rom"]
    if rom_elements:
        game = Game(
            is_bios=True if game_element.get("isbios", "") == "yes" else False,
            name=game_element.get("name", ""),
            year=int(game_element.get("year", 0)),
            manufacturer=game_element.get("manufacturer", ""),
        )
        game.roms = create_roms(rom_elements)
        return game
    return None


def get_mame_emulator_details(dat_file: str) -> list[str]:
    emulator = os.path.basename(dat_file)
    for substring in (".dat", ".xml", ".bz2"):
        emulator = emulator.replace(substring, "")
    return emulator.split()


def process_games(session: Session, root: ET.Element, emulator: Emulator):
    num_existing_games = 0
    num_new_games = 0
    for element in root:
        if game := create_game(element):
            if existing_game := get_existing_game(session, game):
                print(f"Game found: {game.name}")
                existing_game.emulators.append(emulator)
                num_existing_games += 1
            else:
                print(f"Adding game: {game.name}")
                game.emulators.append(emulator)
                session.add(game)
                num_new_games += 1
    return num_existing_games, num_new_games


def process_dats(session: Session, dats: list[str]):
    for dat_file in dats:
        print(f"Processing: {dat_file}")
        emulator_name, emulator_version = get_mame_emulator_details(dat_file)
        emulator = Emulator(name=emulator_name, version=emulator_version)
        source = shared.get_source_contents(dat_file)
        root = shared.get_source_root(source)
        num_existing_games, num_new_games = process_games(session, root, emulator)
        print(
            f"Emulator: {emulator_name} {emulator_version} - Existing Games: {num_existing_games}, New Games: {num_new_games}"
        )
        session.commit()


if __name__ == "__main__":
    session = get_session(DATABASE_PATH)
    process_dats(session, shared.MAME_DATS)
