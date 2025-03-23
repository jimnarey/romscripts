#!/usr/bin/env python

import hashlib
from lxml import etree as ET

# from sqlalchemy import event
from . import db


def roms_signature_from_roms(roms: list[db.Rom]):
    return get_roms_signature([{"name": rom.name, "size": rom.size, "crc": rom.crc} for rom in roms])


def roms_signature_from_elements(roms_elements: list[ET._Element]):
    # We're using get() on the size attribute solely to deal with
    # {'name': 'snk880.11a', 'mergesize': '131072', 'crc': 'e70fd906'} in
    # /home/jimnarey/Data/Retro/MAME-DATS/MAME 0.34.xml
    # This is clearly an error. So, change all lookups to gets and come back to
    # the problem later
    return get_roms_signature(
        [
            {"name": rom.get("name", ""), "size": int(rom.get("size", 0)), "crc": rom.get("crc", "")}
            for rom in roms_elements
        ]
    )


def get_roms_signature(rom_specs: list[dict]):
    sorted_rom_specs = sorted(rom_specs, key=lambda rom: rom["crc"])
    signatures = [f"{rom['name']}/{rom['size']}/{rom['crc']}" for rom in sorted_rom_specs]
    return ",".join(sorted(signatures))


def get_game_index_hash(game_name: str, roms_signature: str):
    return hashlib.sha256(f"{game_name}{roms_signature}".encode()).hexdigest()


def get_game_index_from_records(game_name: str, roms: list[db.Rom]):
    roms_signature = roms_signature_from_roms(roms)
    # return hashlib.sha256(f"{game_name}{roms_signature}".encode()).hexdigest()
    return get_game_index_hash(game_name, roms_signature)


def get_game_index_from_elements(game_name: str, rom_elements: list[ET._Element]):
    roms_signature = roms_signature_from_elements(rom_elements)
    # return hashlib.sha256(f"{game_name}{roms_signature}".encode()).hexdigest()
    return get_game_index_hash(game_name, roms_signature)


def get_rom_index_hash(rom_name: str, size: int, crc: str):
    return hashlib.sha256(f"{rom_name}{size}{crc}".encode()).hexdigest()


def get_attributes_md5(attributes: dict[str, str]):
    ordered_attrs = [attributes[key] for key in sorted(attributes.keys())]
    return hashlib.md5("".join(ordered_attrs).encode()).hexdigest()


# # This wouldn't be the best event to catch if we were editing Game records because it's
# # called even if attributes unrelated to the indexing function change.
# @event.listens_for(db.Game, "before_insert")
# def update_composite_indexes(mapper, connection, target):
#     target.name_roms_index = get_game_index_from_records(target.name, target.roms)
