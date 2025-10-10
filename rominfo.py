#!/usr/bin/env python3

from pathlib import Path
from optparse import OptionParser
from zipfile import ZipFile

from sqlalchemy.orm import Query

from arcade_db.shared import db, indexing


DB_PATH = Path("./arcade.db")


def to_hex(value) -> str:
    # CRCs returned by ZipFile are integers but just in case
    if isinstance(value, int):
        return format(value, "08x")
    if isinstance(value, str):
        try:
            return format(int(value, 16), "08x")
        except ValueError:
            return format(int(value, 10), "08x")


def get_arcade_game_index(file_path: str) -> str:
    archive = ZipFile(file_path)
    file_specs = [{"name": file.filename, "size": int(file.file_size), "crc": to_hex(file.CRC)} for file in archive.infolist()]
    signature = indexing.get_roms_signature(file_specs)
    return signature


if __name__ == "__main__":
    parser = OptionParser()
    (options, args) = parser.parse_args()
    session = db.get_session(str(DB_PATH.absolute()))
    file_path = Path(args[0])
    signature = get_arcade_game_index(str(file_path))
    print(signature)
    index_hash = indexing.get_game_index_hash(file_path.stem, signature)
    print(index_hash)
    results = session.query(db.Game).filter(db.Game.hash == index_hash)
    print(len(results.all())) # Should be 1 for any valid MAME zip
