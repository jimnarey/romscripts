#!/usr/bin/env python

from typing import Literal
import hashlib
from lxml import etree as ET
from sqlalchemy import event
from . import db


def get_disks_signature_from_disks(disks: list[db.Disk], hash_type: Literal["md5", "sha1"]):
    try:
        disk_signatures = [{"name": disk.name, hash_type: getattr(disk, hash_type)} for disk in disks]
        if any(not disk[hash_type] for disk in disk_signatures):
            return None
        return get_disks_signature(disk_signatures, hash_type)
    except AttributeError:
        return None


def get_disks_signature_from_elements(disks_elements: list[ET._Element], hash_type: Literal["md5", "sha1"]):
    try:
        return get_disks_signature(
            [{"name": disk.attrib["name"], hash_type: disk.attrib[hash_type]} for disk in disks_elements], hash_type
        )
    except KeyError:
        return None


def get_disks_signature(disk_specs: list[dict], hash_type: Literal["md5", "sha1"]):
    signatures = [f"{disk['name']}/{disk[hash_type]}" for disk in disk_specs]
    return ",".join(sorted(signatures))


def roms_signature_from_roms(roms: list[db.Rom]):
    return get_roms_signature([{"name": rom.name, "size": rom.size, "crc": rom.crc} for rom in roms])


def roms_signature_from_elements(roms_elements: list[ET._Element]):
    return get_roms_signature(
        [
            {"name": rom.get("name", ""), "size": int(rom.get("size", 0)), "crc": rom.get("crc", "")}
            for rom in roms_elements
        ]
    )


def get_roms_signature(rom_specs: list[dict]):
    signatures = [f"{rom['name']}/{rom['size']}/{rom['crc']}" for rom in rom_specs]
    return ",".join(sorted(signatures))


def get_data_signature_from_records(roms: list[db.Rom], disks: list[db.Disk], hash_type: Literal["md5", "sha1"]):
    rom_signatures = roms_signature_from_roms(roms)
    disk_signatures = get_disks_signature_from_disks(disks, hash_type)
    return f"{rom_signatures}+{disk_signatures}"


def get_data_signature_from_elements(
    rom_elements: list[ET._Element], disks_elements: list[ET._Element], hash_type: Literal["md5", "sha1"]
):
    rom_signatures = roms_signature_from_elements(rom_elements)
    disk_signatures = get_disks_signature_from_elements(disks_elements, hash_type)
    return f"{rom_signatures}+{disk_signatures}"


def get_game_index_from_records_by_disk_hash_type(
    game_name: str, roms: list[db.Rom], disks: list[db.Disk], hash_type: Literal["md5", "sha1"]
):
    data_signature = get_data_signature_from_records(roms, disks, hash_type)
    return hashlib.sha256(f"{game_name}{data_signature}".encode()).hexdigest()


def get_game_index_from_elements_by_disk_hash_type(
    game_name: str,
    rom_elements: list[ET._Element],
    disks_elements: list[ET._Element],
    hash_type: Literal["md5", "sha1"],
):
    data_signature = get_data_signature_from_elements(rom_elements, disks_elements, hash_type)
    return hashlib.sha256(f"{game_name}{data_signature}".encode()).hexdigest()


def disk_records_hash_type(game: db.Game) -> Literal["md5", "sha1"]:
    if any(disk.sha1 for disk in game.disks):
        return "sha1"
    return "md5"
