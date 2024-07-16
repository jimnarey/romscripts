#!/usr/bin/env python3

from pathlib import Path
from optparse import OptionParser
from zipfile import ZipFile

from arcade_db.shared import db, indexing


DB_PATH = Path("./arcade_db/arcade-latest.db")
# breakpoint()


def get_arcade_game_index(file_path: str) -> str:
    # signatures = [f"{rom['name']}/{rom['size']}/{rom['crc']}" for rom in rom_specs]
    archive = ZipFile(file_path)
    file_specs = [{"name": file.filename, "size": file.file_size, "crc": file.CRC} for file in archive.infolist()]
    signature = indexing.get_roms_signature(file_specs)
    return signature


if __name__ == "__main__":
    parser = OptionParser()
    # parser.add_option("-f", "--file", dest="file", help="Target File", metavar="PATH")
    (options, args) = parser.parse_args()
    session = db.get_session(str(DB_PATH.absolute()))
    file_path = Path(args[0])
    signature = get_arcade_game_index(str(file_path))
    print(signature)
    index_hash = indexing.get_index_hash(file_path.stem, signature)
    print(index_hash)
    results = session.query(db.Game).filter(db.Game.name_roms_index == index_hash).all()
    breakpoint()
