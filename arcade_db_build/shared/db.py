#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

from typing import Literal
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Index
from sqlalchemy.orm import Session, DeclarativeBase, backref, relationship


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


# TODO: What should happen when no games are associated with a rom?
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
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
    roms = relationship("Rom", secondary=game_rom_association, back_populates="games")
    # md5 and sha1 refer to the hash of any disk elements. For roms we always use crc
    data_index_md5 = Column(String)
    data_index_sha1 = Column(String)

    def set_index(self, hash_type: Literal["md5", "sha1"], index: str):
        if hash_type == "sha1":
            self.data_index_sha1 = index
        else:
            self.data_index_md5 = index


def get_game_by_index(session: Session, index_value: str, index_hash_type: Literal["sha1", "md5"]):
    if index_hash_type == "sha1":
        return session.query(Game).filter(Game.data_index_sha1 == index_value).first()
    return session.query(Game).filter(Game.data_index_md5 == index_value).first()


class Rom(Base):
    __tablename__ = "roms"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    crc = Column(String, nullable=False)
    sha1 = Column(String)
    games = relationship("Game", secondary=game_rom_association, back_populates="roms")
    _table_args__ = (Index("idx_name_size_crc", "name", "size", "crc"),)


class Disk(Base):
    """
    This is missing several fields pending further research into which are emulator version
    dependent.
    """

    __tablename__ = "disks"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sha1 = Column(String, nullable=False)
    md5 = Column(String, nullable=False)
    games = relationship("Game", secondary=game_disk_association, back_populates="disks")
    _table_args__ = (Index("idx_name_sha1", "name", "sha1"), Index("idx_name_md5", "name", "md5"))


class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True)
    overall = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    game_emulators = relationship("GameEmulator", secondary=game_emulator_feature, back_populates="features")
    _table_args__ = (Index("idx_overall_type_status", "overall", "type", "status"),)


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    palettesize = Column(String, nullable=False)
    hiscoresave = Column(String, nullable=False)
    requiresartwork = Column(String, nullable=False)
    unofficial = Column(String, nullable=False)
    good = Column(String, nullable=False)
    status = Column(String, nullable=False)
    graphic = Column(String, nullable=False)
    cocktailmode = Column(String, nullable=False)
    savestate = Column(String, nullable=False)
    protection = Column(String, nullable=False)
    emulation = Column(String, nullable=False)
    cocktail = Column(String, nullable=False)
    color = Column(String, nullable=False)
    nosoundhardware = Column(String, nullable=False)
    sound = Column(String, nullable=False)
    incomplete = Column(String, nullable=False)
    game_emulators = relationship("GameEmulator", back_populates="driver")
    __table_args__ = (
        Index(
            "idx_all_attribs",
            "palettesize",
            "hiscoresave",
            "requiresartwork",
            "unofficial",
            "good",
            "status",
            "graphic",
            "cocktailmode",
            "savestate",
            "protection",
            "emulation",
            "cocktail",
            "color",
            "nosoundhardware",
            "sound",
            "incomplete",
        ),
    )
