#!/usr/bin/env python3

from pathlib import Path
from zipfile import ZipFile

import click

from arcade_db import create_db
from arcade_db.shared import db, indexing, sources


DB_PATH = Path("./arcade_db/arcade-out/arcade.db")


def to_hex(value) -> str:
    # CRCs returned by ZipFile are integers but just in case
    if isinstance(value, int):
        return format(value, "08x")
    if isinstance(value, str):
        try:
            return format(int(value, 16), "08x")
        except ValueError:
            return format(int(value, 10), "08x")
    return ""


def get_arcade_game_index(file_path: str) -> str:
    archive = ZipFile(file_path)
    file_specs = [
        {"name": file.filename, "size": int(file.file_size), "crc": to_hex(file.CRC)} for file in archive.infolist()
    ]
    signature = indexing.get_roms_signature(file_specs)
    return signature


@click.group()
def cli():
    pass


@cli.command()
@click.option("--dir", "-d", default="./arcade-out", help="Output directory")
@click.option("--type", "-t", "dat_type", default="mame", help="Dat type")
@click.option("--start", "-s", default=0, type=int, help="Start DAT index")
@click.option("--end", "-e", default=None, type=int, help="End DAT index")
def build(dir, dat_type, start, end):
    dat_paths = sources.BUILD_DATS[dat_type]
    end = end if end is not None else len(dat_paths)
    source_dats = dat_paths[start:end]
    create_db.process_dats_consecutively(source_dats, dir)


@cli.command()
@click.argument("path")
def file(path):
    session = db.get_session(str(DB_PATH.absolute()))
    signature = get_arcade_game_index(path)
    index_hash = indexing.get_game_index_hash(Path(path).stem, signature)
    results = session.query(db.Game).filter(db.Game.hash == index_hash)
    match = results.one_or_none()
    if match:
        print(match.description)


if __name__ == "__main__":
    cli()
