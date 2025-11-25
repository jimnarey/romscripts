import os
import unittest
import json
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from arcade_db.shared import db, indexing

logging.basicConfig(level=logging.INFO)

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(SCRIPT_PATH, "fixtures")
DB_PATH = os.path.join(SCRIPT_PATH, "..", "arcade_db", "arcade-out", "arcade.db")


class TestDb(unittest.TestCase):
    def setUp(self):
        engine = create_engine(f"sqlite:///{DB_PATH}")  # noqa: E231
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        with open(os.path.join(FIXTURES_PATH, "mame2003p_full_non_merged_all_2021_zip_specs.json"), "r") as json_file:
            self.zip_specs = json.load(json_file)
        for key in self.zip_specs:
            self.zip_specs[key] = [
                {"name": spec["name"], "size": spec["size"], "crc": format(spec["crc"], "08x")}
                for spec in self.zip_specs[key]
            ]

    def test_mame_2003_fnm_set(self):
        not_found = []
        for name, file_specs in self.zip_specs.items():
            with self.subTest(game=name):
                logging.info(f"Testing {name}")
                signature = indexing.get_roms_signature(file_specs)
                index_hash = indexing.get_game_index_hash(name.split(".")[0], signature)
                results = self.session.query(db.Game).filter(db.Game.hash == index_hash)
                if len(results.all()) != 1:
                    not_found.append(name)
        if not_found:
            self.fail(f"The following games were not found in the database: {not_found}")  # noqa: E713
        logging.info(f"Tested {len(self.zip_specs)} zips")

    def tearDown(self):
        self.session.rollback()
