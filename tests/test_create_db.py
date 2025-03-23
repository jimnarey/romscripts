import os
import unittest

# from typing import Optional

from lxml import etree as ET

# from lxml.etree import XMLParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from arcade_db import create_db
from arcade_db.shared import db


SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(SCRIPT_PATH, "fixtures", "create_db")

PARSER = ET.XMLParser(remove_comments=True)


def get_dat_root(path: str) -> ET._Element:
    with open(path, "rb") as file:
        contents = file.read()
    root = ET.fromstring(contents, PARSER)
    return root


class TestModels(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.rollback()

    def test_models_are_properly_declared(self):
        # TODO: add game:game relationships
        # Add more fields, including those derived from sub-elements
        """
        This doesn't add every field on Game. It tests the realtionships
        """
        emulator = db.Emulator(name="emu1", version="1.0")
        roms = [
            db.Rom(name="rom1", size=100, crc="crc1", sha1="sha1"),
            db.Rom(name="rom2", size=200, crc="crc2", sha1="sha2"),
        ]
        game = db.Game(isbios=False, name="game1", year="2000", manufacturer="man1", roms=roms)
        game_emulator = db.GameEmulator(game=game, emulator=emulator)
        self.session.add(game_emulator)
        self.session.commit()
        db_game = self.session.query(db.Game).filter_by(name="game1").one()
        db_emulator = self.session.query(db.Emulator).filter_by(name="emu1").one()
        self.assertEqual(db_game, game)
        self.assertEqual(db_emulator, emulator)
        self.assertEqual(db_game.game_emulators[0], game_emulator)
        self.assertEqual(db_emulator.game_emulators[0], game_emulator)
        self.assertEqual(set(rom.name for rom in db_game.roms), {"rom1", "rom2"})


class TestGetInnerElementText(unittest.TestCase):
    def test_element_with_inner_element(self):
        outer_element = ET.fromstring("<outer><inner>text</inner></outer>")
        self.assertEqual(create_db.get_inner_element_text(outer_element, "inner"), "text")

    def test_element_without_inner_element(self):
        outer_element = ET.fromstring("<outer></outer>")
        self.assertIsNone(create_db.get_inner_element_text(outer_element, "inner"))

    def test_element_with_empty_inner_element(self):
        outer_element = ET.fromstring("<outer><inner></inner></outer>")
        self.assertIsNone(create_db.get_inner_element_text(outer_element, "inner"))

    def test_element_with_multiple_inner_elements(self):
        outer_element = ET.fromstring("<outer><inner>text1</inner><inner>text2</inner></outer>")
        self.assertEqual(create_db.get_inner_element_text(outer_element, "inner"), "text1")


if __name__ == "__main__":
    unittest.main()
