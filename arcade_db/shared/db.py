#!/usr/bin/env python

"""
Generate a database from a collection of arcade DAT files.

This file includes several instances of superflous casting (e.g. to bool/str) to
handle cases where the type checker was unable to properly handle SQLAlchemy
types.
"""

# from sqlalchemy import Column, Integer, String, ForeignKey, Table, Index
from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import Session, DeclarativeBase, sessionmaker

# from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


class Base(DeclarativeBase):
    pass


def get_session(db_path: str) -> Session:
    engine = create_engine(f"sqlite:///{db_path}")  # noqa: E231
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class GameRom(Base):
    __tablename__ = "game_rom"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    rom_id = Column(Integer, ForeignKey("roms.id"), nullable=False)

    __table_args__ = (Index("idx_game_rom_unique", "game_id", "rom_id", unique=True),)


class GameEmulatorFeature(Base):
    __tablename__ = "game_emulator_feature"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_emulator_id = Column(Integer, ForeignKey("game_emulator.id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False)

    __table_args__ = (Index("idx_game_emulator_feature_unique", "game_emulator_id", "feature_id", unique=True),)


class GameEmulatorDisk(Base):
    __tablename__ = "game_emulator_disk"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_emulator_id = Column(Integer, ForeignKey("game_emulator.id"), nullable=False)
    disk_id = Column(Integer, ForeignKey("disks.id"), nullable=False)

    __table_args__ = (Index("idx_game_emulator_disk_unique", "game_emulator_id", "disk_id", unique=True),)


class GameEmulator(Base):
    __tablename__ = "game_emulator"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    emulator_id = Column(Integer, ForeignKey("emulators.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    game = relationship("Game", back_populates="game_emulators")
    emulator = relationship("Emulator", back_populates="game_emulators")
    driver = relationship("Driver", back_populates="game_emulators")
    features = relationship("Feature", secondary="game_emulator_feature", back_populates="game_emulators")
    disks = relationship("Disk", secondary="game_emulator_disk", back_populates="game_emulators")

    __table_args__ = (Index("idx_game_emulator_unique", "game_id", "emulator_id", unique=True),)


class Emulator(Base):
    __tablename__ = "emulators"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String)
    version = Column(String)
    game_emulators = relationship("GameEmulator", back_populates="emulator")


# TODO: What should happen when no games are associated with a rom?
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    year = Column(Integer)
    manufacturer = Column(String)
    romof = Column(String)
    cloneof = Column(String)
    isbios = Column(String)
    isdevice = Column(String)
    # Move this to GameEmulator
    runnable = Column(String)
    ismechanical = Column(String)
    game_emulators = relationship("GameEmulator", back_populates="game")
    roms = relationship("Rom", secondary="game_rom", back_populates="games")


class Rom(Base):
    __tablename__ = "roms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    crc = Column(String, nullable=False)
    sha1 = Column(String)
    games = relationship("Game", secondary="game_rom", back_populates="roms")

    __table_args__ = (Index("idx_rom_lookup", "name", "size", "crc"),)


class Disk(Base):
    """
    This is missing several fields pending further research into which are emulator version
    dependent.
    """

    __tablename__ = "disks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    sha1 = Column(String, nullable=False)
    md5 = Column(String, nullable=False)
    game_emulators = relationship("GameEmulator", secondary="game_emulator_disk", back_populates="disks")

    __table_args__ = (
        Index("idx_disk_sha1", "name", "sha1"),
        Index("idx_disk_md5", "name", "md5"),
    )


class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    overall = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    game_emulators = relationship("GameEmulator", secondary="game_emulator_feature", back_populates="features")


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(64), unique=True, nullable=False, index=True)
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
