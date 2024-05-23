#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

# from typing import Optional, Type

# import warnings
# import os
# import functools
# import xml.etree.ElementTree as ET
# import psutil
# from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, inspect
from sqlalchemy import Column, Integer, String, ForeignKey, Table

# from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, backref
from sqlalchemy.orm import DeclarativeBase, backref
from sqlalchemy.orm import relationship

# from sqlalchemy.exc import NoResultFound

# from .shared import shared


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
