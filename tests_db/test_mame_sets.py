import os
import unittest
import json
import logging
import glob

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from arcade_db.shared import db, indexing

logging.basicConfig(level=logging.INFO)

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(SCRIPT_PATH, "fixtures")
DB_PATH = os.path.join(SCRIPT_PATH, "..", "arcade-out", "arcade.db")


class TestDb(unittest.TestCase):
    def setUp(self):
        engine = create_engine(f"sqlite:///{DB_PATH}")  # noqa: E231
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.fixtures = {}
        json_files = glob.glob(os.path.join(FIXTURES_PATH, "*.json"))

        for json_file_path in json_files:
            fixture_name = os.path.basename(json_file_path).replace(".json", "")
            logging.info(f"Loading fixture: {fixture_name}")
            with open(json_file_path, "r") as json_file:
                zip_specs = json.load(json_file)
            for key in zip_specs:
                zip_specs[key] = [
                    {"name": spec["name"], "size": spec["size"], "crc": format(spec["crc"], "08x")}
                    for spec in zip_specs[key]
                ]
            self.fixtures[fixture_name] = zip_specs

    def test_game_matching_all_fixtures(self):
        """Test that games from all fixtures can be found in the database."""
        for fixture_name, zip_specs in self.fixtures.items():
            with self.subTest(fixture=fixture_name):
                logging.info(f"Testing fixture: {fixture_name}")
                not_found = []
                for name, file_specs in zip_specs.items():
                    with self.subTest(fixture=fixture_name, game=name):
                        # logging.debug(f"Testing {name} from {fixture_name}")
                        signature = indexing.get_roms_signature(file_specs)
                        index_hash = indexing.get_game_index_hash(name.split(".")[0], signature)
                        results = self.session.query(db.Game).filter(db.Game.hash == index_hash)
                        if len(results.all()) != 1:
                            not_found.append(name)
                if not_found:
                    self.fail(
                        f"The following games from {fixture_name} were not found in the database: {not_found}"  # noqa: E713
                    )  # noqa: E713
                logging.info(f"Successfully tested {len(zip_specs)} zips from {fixture_name}")

    def tearDown(self):
        self.session.rollback()
