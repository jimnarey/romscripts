#!/usr/bin/env python3

import hashlib
from dataclasses import asdict
from typing import TYPE_CHECKING
from lxml import etree as ET

if TYPE_CHECKING:
    from arcade_db.shared import types


from arcade_db.shared.types import RomSpec


def roms_signature_from_elements(roms_elements: list[ET._Element]):
    # We're using get() on the size attribute solely to deal with
    # {'name': 'snk880.11a', 'mergesize': '131072', 'crc': 'e70fd906'} in
    # /home/jimnarey/Data/Retro/MAME-DATS/MAME 0.34.xml
    # This is clearly an error. So, change all lookups to gets and come back to
    # the problem later
    return get_roms_signature(
        [
            # {"name": rom.get("name", ""), "size": int(rom.get("size", 0)), "crc": rom.get("crc", "")}
            RomSpec(
                name=rom.get("name", ""),
                size=int(rom.get("size", 0)),
                crc=rom.get("crc", ""),
            )
            for rom in roms_elements
        ]
    )


def get_roms_signature(rom_specs: list[RomSpec]):
    # This strips out any roms without a crc, so undumped roms don't change the signature
    unique_roms = list(set(rs for rs in rom_specs if rs.crc))
    sorted_rom_specs = sorted(unique_roms, key=lambda rom: rom.crc)
    signatures = [f"{rom.name}/{rom.size}/{rom.crc}" for rom in sorted_rom_specs]
    return ",".join(sorted(signatures))


def get_game_index_hash(game_name: str, roms_signature: str):
    return hashlib.sha256(f"{game_name}{roms_signature}".encode()).hexdigest()


def get_game_index_from_elements(game_name: str, rom_elements: list[ET._Element]):
    roms_signature = roms_signature_from_elements(rom_elements)
    return get_game_index_hash(game_name, roms_signature)


def get_rom_index_hash(rom_name: str, size: int, crc: str):
    return hashlib.sha256(f"{rom_name}{size}{crc}".encode()).hexdigest()


def get_attributes_md5(attributes: dict[str, str]):
    ordered_attrs = [attributes[key] for key in sorted(attributes.keys())]
    return hashlib.md5("".join(ordered_attrs).encode()).hexdigest()


def get_entity_hash(entity: "types.Driver | types.Feature | types.Disk") -> str:
    """
    Compute hash from any entity dataclass, excluding id and hash fields.

    This allows us to create dataclasses directly from XML, then compute
    and set the hash afterwards, eliminating duplicate field extraction.
    """
    entity_dict = asdict(entity)
    # Remove fields that shouldn't be part of the hash
    entity_dict.pop("id", None)
    entity_dict.pop("hash", None)
    # Convert all values to strings for consistent hashing
    string_dict = {k: str(v) if v is not None else "" for k, v in entity_dict.items()}
    return get_attributes_md5(string_dict)


# In earlier versions it was necessary to match roms/games from SQLAlchemy records.
# It's no longer necessary but might be again

# def roms_signature_from_roms(roms: list[db.Rom]):
#     return get_roms_signature([{"name": rom.name, "size": rom.size, "crc": rom.crc} for rom in roms])

# def get_game_index_from_records(game_name: str, roms: list[db.Rom]):
#     roms_signature = roms_signature_from_roms(roms)
#     # return hashlib.sha256(f"{game_name}{roms_signature}".encode()).hexdigest()
#     return get_game_index_hash(game_name, roms_signature)
