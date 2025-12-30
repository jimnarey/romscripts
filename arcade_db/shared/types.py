# from typing import NamedTuple, Optional, get_type_hints
from typing import NamedTuple, Optional
from sqlalchemy import inspect

# from sqlalchemy.types import Integer, String, Boolean

from . import db


# If SQLAlchemy types have a common base class, we can check for that and then
# just use a mapping of the class name to the Python type, saving going through
# the loop. Maybe the type checker is enough
def _sqlalchemy_to_python_type(column_type):
    """Map SQLAlchemy column types to Python types."""
    from sqlalchemy import Integer, String, Boolean, Float, DateTime, Date, Time, Text

    type_map = {
        Integer: int,
        String: str,
        Boolean: bool,
        Float: float,
        Text: str,
        DateTime: str,
        Date: str,
        Time: str,
    }
    for sqlalchemy_type, python_type in type_map.items():
        if isinstance(column_type, sqlalchemy_type):
            return python_type
    return str


def get_typed_tuple_from_model(model_class: type[db.Base], tuple_name: str, fields: list[str] | None = None):
    mapper = inspect(model_class)
    field_definitions = []
    for column in mapper.columns:
        if fields is None or column.name in fields:
            python_type = _sqlalchemy_to_python_type(column.type)
            if column.nullable and column.name != "id":
                python_type = Optional[python_type]
            field_definitions.append((column.name, python_type))
    return NamedTuple(tuple_name, field_definitions)


Game = get_typed_tuple_from_model(db.Game, "Game")
Rom = get_typed_tuple_from_model(db.Rom, "Rom")
Emulator = get_typed_tuple_from_model(db.Emulator, "Emulator")
Feature = get_typed_tuple_from_model(db.Feature, "Feature")
Disk = get_typed_tuple_from_model(db.Disk, "Disk")
Driver = get_typed_tuple_from_model(db.Driver, "Driver")
GameEmulator = get_typed_tuple_from_model(db.GameEmulator, "GameEmulator")
GameRom = get_typed_tuple_from_model(db.GameRom, "GameRom")
GameEmulatorFeature = get_typed_tuple_from_model(db.GameEmulatorFeature, "GameEmulatorFeature")
GameEmulatorDisk = get_typed_tuple_from_model(db.GameEmulatorDisk, "GameEmulatorDisk")

# RomSpecTuple = get_typed_tuple_from_model(db.Rom, 'RomSpecTuple', fields=['name', 'size', 'crc'])
# GameSpecTuple = get_typed_tuple_from_model(db.Game, 'GameSpecTuple', fields=['name', 'hash', 'description'])
