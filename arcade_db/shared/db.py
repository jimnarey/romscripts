#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import Session, DeclarativeBase, sessionmaker

# from sqlalchemy.orm import backref, relationship
# from sqlalchemy import Index
from sqlalchemy import create_engine


class Base(DeclarativeBase):
    pass


def get_session(db_path: str) -> Session:
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


game_rom_association = Table(
    "game_rom",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("rom_id", Integer, ForeignKey("roms.id")),
)

game_emulator_feature_association = Table(
    "game_emulator_feature",
    Base.metadata,
    Column("game_emulator_id", Integer, ForeignKey("game_emulator.game_id")),
    Column("feature_id", Integer, ForeignKey("features.id")),
)

game_emulator_disk_association = Table(
    "game_emulator_disk",
    Base.metadata,
    Column("game_emulator_id", Integer, ForeignKey("game_emulator.game_id")),
    Column("disk_id", Integer, ForeignKey("disks.id")),
)


class GameEmulator(Base):
    __tablename__ = "game_emulator"
    id = Column(String(32), primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    emulator_id = Column(Integer, ForeignKey("emulators.id"), primary_key=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    # game = relationship("Game", back_populates="game_emulators")
    # emulator = relationship("Emulator", back_populates="game_emulators")
    # driver = relationship("Driver", back_populates="game_emulators")
    # features = relationship("Feature", secondary=game_emulator_feature_association, back_populates="game_emulators")
    # disks = relationship("Disk", secondary=game_emulator_disk_association, back_populates="game_emulators")


class Emulator(Base):
    __tablename__ = "emulators"
    id = Column(String(32), primary_key=True)
    name = Column(String)
    version = Column(String)
    # game_emulators = relationship("GameEmulator", back_populates="emulator")


# TODO: What should happen when no games are associated with a rom?
class Game(Base):
    __tablename__ = "games"
    id = Column(String(64), primary_key=True)  # Hash of name and roms signature
    name = Column(String, nullable=False)
    description = Column(String)
    year = Column(Integer)
    manufacturer = Column(String)
    cloneof_id = Column(Integer, ForeignKey("games.id"))
    # cloneof = relationship(
    #     "Game", foreign_keys=[cloneof_id], backref=backref("clones", foreign_keys=[cloneof_id]), remote_side=[id]
    # )
    romof_id = Column(Integer, ForeignKey("games.id"))
    # romof = relationship(
    #     "Game", foreign_keys=[romof_id], backref=backref("bios_children", foreign_keys=[romof_id]), remote_side=[id]
    # )
    isbios = Column(String)
    isdevice = Column(String)
    runnable = Column(String)
    ismechanical = Column(String)
    # game_emulators = relationship("GameEmulator", back_populates="game")
    # roms = relationship("Rom", secondary=game_rom_association, back_populates="games")


class Rom(Base):
    __tablename__ = "roms"
    id = Column(String(64), primary_key=True)  # Hash of name, size, and crc
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    crc = Column(String, nullable=False)
    sha1 = Column(String)
    # games = relationship("Game", secondary=game_rom_association, back_populates="roms")
    # _table_args__ = (Index("idx_name_size_crc", "name", "size", "crc"),)


class Disk(Base):
    """
    This is missing several fields pending further research into which are emulator version
    dependent.
    """

    __tablename__ = "disks"
    id = Column(String(32), primary_key=True)
    name = Column(String, nullable=False)
    sha1 = Column(String, nullable=False)
    md5 = Column(String, nullable=False)
    # game_emulators = relationship("GameEmulator", secondary=game_emulator_disk_association, back_populates="disks")
    # _table_args__ = (Index("idx_name_sha1", "name", "sha1"), Index("idx_name_md5", "name", "md5"))


class Feature(Base):
    __tablename__ = "features"
    id = Column(String(32), primary_key=True)
    overall = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    # game_emulators = relationship("GameEmulator", secondary=game_emulator_feature_association, back_populates="features")
    # _table_args__ = (Index("idx_overall_type_status", "overall", "type", "status"),)


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(String(32), primary_key=True)
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
    # game_emulators = relationship("GameEmulator", back_populates="driver")
    # __table_args__ = (
    #     Index(
    #         "idx_all_attribs",
    #         "palettesize",
    #         "hiscoresave",
    #         "requiresartwork",
    #         "unofficial",
    #         "good",
    #         "status",
    #         "graphic",
    #         "cocktailmode",
    #         "savestate",
    #         "protection",
    #         "emulation",
    #         "cocktail",
    #         "color",
    #         "nosoundhardware",
    #         "sound",
    #         "incomplete",
    #     ),
    # )
