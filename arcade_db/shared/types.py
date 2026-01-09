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


def get_typed_dataclass_from_model(
    model_class: type[db.Base],
    class_name: str,
    fields_list: list[str] | None = None,
    frozen: bool = False,
    temp_fields: dict[str, tuple[type, Any]] | None = None,
):
    """
    Generate a dataclass from a SQLAlchemy model.

    Args:
        model_class: SQLAlchemy model to derive fields from
        class_name: Name for the generated dataclass
        fields_list: Optional list of field names to include (None = all fields)
        frozen: Whether to make the dataclass frozen/immutable
        temp_fields: Optional dict of temporary field definitions {name: (type, default_value)}
                    Temporary fields are prefixed with _ and not written to database
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

    # Add temporary fields if provided
    if temp_fields:
        for field_name, (field_type, default_value) in temp_fields.items():
            annotations[field_name] = field_type
            defaults[field_name] = default_value

    namespace: dict[str, Any] = {"__annotations__": annotations}

    for field_name, default_value in defaults.items():
        namespace[field_name] = default_value

    cls = type(class_name, (), namespace)
    # Apply dataclass decorator with frozen parameter
    decorator = dataclass(frozen=frozen)
    return decorator(cls)


@dataclass
class GameRelationships:
    """Relationship data extracted from processed games.

    Note: device_rom_ids contains hash strings, not numeric IDs.
    This is because relationships are built before convert_hashes_to_ids() runs.
    """

    parent_to_children: dict[str, set[str]]  # parent name -> set of child names
    child_to_parent: dict[str, str]  # child name -> parent name
    name_to_hash: dict[str, str]  # game name -> game hash
    device_rom_ids: dict[str, list[str]]  # device name -> list of ROM hashes (not numeric IDs)


@dataclass
class DeviceRef:
    """Represents a device reference extracted from XML."""

    name: str


Game = get_typed_dataclass_from_model(db.Game, "Game", temp_fields={"_device_refs": (list[DeviceRef], None)})
Rom = get_typed_dataclass_from_model(db.Rom, "Rom")
Emulator = get_typed_dataclass_from_model(db.Emulator, "Emulator")
Feature = get_typed_dataclass_from_model(db.Feature, "Feature")
Disk = get_typed_dataclass_from_model(db.Disk, "Disk")
Driver = get_typed_dataclass_from_model(db.Driver, "Driver")
GameEmulator = get_typed_dataclass_from_model(db.GameEmulator, "GameEmulator")
GameRom = get_typed_dataclass_from_model(db.GameRom, "GameRom")
GameEmulatorFeature = get_typed_dataclass_from_model(db.GameEmulatorFeature, "GameEmulatorFeature")
GameEmulatorDisk = get_typed_dataclass_from_model(db.GameEmulatorDisk, "GameEmulatorDisk")

# This is so groups of roms can be compared using set arithmetic. Some later MAME XMLs have a sha1 for
# for roms which don't have one in earlier XMLs. So this is left out for the purpose of comparison.
RomSpec = get_typed_dataclass_from_model(db.Rom, "RomSpec", fields_list=["name", "size", "crc"], frozen=True)
