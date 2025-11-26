#!/usr/bin/env python3
from typing import Optional

from sqlalchemy.orm import Session

from .shared import db


def get_compatible_emulators(session: Session, game: db.Game):
    """Retrieve a list of emulators compatible with the given game."""
    emulators = session.query(db.Emulator).join(db.GameEmulator).filter(db.GameEmulator.game_id == game.id).all()
    return emulators


def get_compatible_games(session: Session, emulator: db.Emulator):
    """Retrieve a list of games compatible with the given emulator."""
    games = session.query(db.Game).join(db.GameEmulator).filter(db.GameEmulator.emulator_id == emulator.id).all()
    return games


def get_clones(session: Session, game: db.Game, emulator: db.Emulator):
    """Retrieve a list of clone games for the given game."""
    clones = (
        session.query(db.Game)
        .join(db.GameEmulator)
        .filter(
            db.Game.parent_id == game.id,
            db.GameEmulator.emulator_id == emulator.id,
        )
        .all()
    )
    return clones


def get_emulator_by_name(session: Session, name: str = "MAME", version: Optional[str] = None):
    version = version if version is not None else "%"
    emulator = (
        session.query(db.Emulator).filter(db.Emulator.name == name.upper(), db.Emulator.version.like(version)).first()
    )
    return emulator
