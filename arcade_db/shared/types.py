# from typing import NamedTuple, Optional, get_type_hints
from typing import Optional, Any
from dataclasses import dataclass
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


def get_typed_dataclass_from_model(model_class: type[db.Base], class_name: str, fields_list: list[str] | None = None):
    """
    Generate a dataclass from a SQLAlchemy model.

    This programmatically creates mutable dataclasses that mirror the SQLAlchemy models,
    ensuring type consistency between in-memory operations and database schema.
    """
    mapper = inspect(model_class)
    annotations: dict[str, type] = {}
    defaults: dict[str, None] = {}

    for column in mapper.columns:
        if fields_list is None or column.name in fields_list:
            python_type = _sqlalchemy_to_python_type(column.type)
            if column.nullable and column.name != "id":
                python_type = Optional[python_type]
                defaults[column.name] = None

            annotations[column.name] = python_type

    namespace: dict[str, Any] = {"__annotations__": annotations}

    for field_name, default_value in defaults.items():
        namespace[field_name] = default_value

    cls = type(class_name, (), namespace)
    return dataclass(cls)


Game = get_typed_dataclass_from_model(db.Game, "Game")
Rom = get_typed_dataclass_from_model(db.Rom, "Rom")
Emulator = get_typed_dataclass_from_model(db.Emulator, "Emulator")
Feature = get_typed_dataclass_from_model(db.Feature, "Feature")
Disk = get_typed_dataclass_from_model(db.Disk, "Disk")
Driver = get_typed_dataclass_from_model(db.Driver, "Driver")
GameEmulator = get_typed_dataclass_from_model(db.GameEmulator, "GameEmulator")
GameRom = get_typed_dataclass_from_model(db.GameRom, "GameRom")
GameEmulatorFeature = get_typed_dataclass_from_model(db.GameEmulatorFeature, "GameEmulatorFeature")
GameEmulatorDisk = get_typed_dataclass_from_model(db.GameEmulatorDisk, "GameEmulatorDisk")

# Specialized types with subset of fields
RomSpec = get_typed_dataclass_from_model(db.Rom, "RomSpec", fields_list=["name", "size", "crc"])

# RomSpecTuple = get_typed_dataclass_from_model(db.Rom, 'RomSpecTuple', fields=['name', 'size', 'crc'])
# GameSpecTuple = get_typed_dataclass_from_model(db.Game, 'GameSpecTuple', fields=['name', 'hash', 'description'])
