import os
import unittest

# from typing import Optional

from lxml import etree as ET

# from lxml.etree import XMLParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from arcade_db import create_db
from arcade_db.shared import db

from arcade_db.shared import sources



SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(SCRIPT_PATH, "fixtures", "create_db")
MAME_DATS_PATH = os.path.join(SCRIPT_PATH, "..", "arcade_db", "sources", "mame", "dats")

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


class TestAddGameReference(unittest.TestCase):

    def test_references_is_added_to_game_attrs(self):
        name_index_mapping = {"mslug": "abcdef0123456789", "neogeo": "1234567890abcdef"}
        game_attrs = {"name": "mslug2"}
        create_db.add_game_reference(game_attrs, "romof", "neogeo", name_index_mapping)
        self.assertEqual(game_attrs["romof_id"], "1234567890abcdef")
        create_db.add_game_reference(game_attrs, "cloneof", "mslug", name_index_mapping)
        self.assertEqual(game_attrs["cloneof_id"], "abcdef0123456789")

    def test_reference_is_not_added_if_target_does_not_exist(self):
        name_index_mapping = {"mslug": "abcdef0123456789", "neogeo": "1234567890abcdef"}
        game_attrs = {"name": "mslug2"}
        create_db.add_game_reference(game_attrs, "romof", "non_existent", name_index_mapping)
        self.assertNotIn("romof_id", game_attrs)
        create_db.add_game_reference(game_attrs, "cloneof", "non_existent", name_index_mapping)
        self.assertNotIn("cloneof_id", game_attrs)

    def test_add_reference_returns_true_if_target_found(self):
        name_index_mapping = {"mslug": "abcdef0123456789", "neogeo": "1234567890abcdef"}
        game_attrs = {"name": "mslug2"}
        result = create_db.add_game_reference(game_attrs, "romof", "neogeo", name_index_mapping)
        self.assertTrue(result)
        result = create_db.add_game_reference(game_attrs, "cloneof", "mslug", name_index_mapping)
        self.assertTrue(result)

    def test_add_reference_returns_false_if_target_not_found(self):
        name_index_mapping = {"mslug": "abcdef0123456789", "neogeo": "1234567890abcdef"}
        game_attrs = {"name": "mslug2"}
        result = create_db.add_game_reference(game_attrs, "romof", "non_existent", name_index_mapping)
        self.assertFalse(result)
        result = create_db.add_game_reference(game_attrs, "cloneof", "non_existent", name_index_mapping)
        self.assertFalse(result)


class TestAddGameReferences(unittest.TestCase):

    def test_all_references_are_added(self):
        name_index_mapping = {"mslug": "abcdef0123456789", "neogeo": "1234567890abcdef"}
        game_attrs = {"name": "mslug2"}
        references = {"romof": "neogeo", "cloneof": "mslug"}
        unhandled_references = create_db.add_game_references(game_attrs, references, name_index_mapping)
        self.assertEqual(unhandled_references, [])
        self.assertEqual(game_attrs["romof_id"], "1234567890abcdef")
        self.assertEqual(game_attrs["cloneof_id"], "abcdef0123456789")
        for attr in ["_romof", "_cloneof"]:
            self.assertNotIn(attr, game_attrs)

    def test_unhandled_references_are_returned(self):
        name_index_mapping = {"mslug": "abcdef0123456789", "neogeo": "1234567890abcdef"}
        game_attrs = {"name": "mslug2"}
        references = {"romof": "non_existent", "cloneof": "mslug"}
        unhandled_references = create_db.add_game_references(game_attrs, references, name_index_mapping)
        # self.assertEqual(unhandled_references, [game_attrs])
        self.assertEqual(game_attrs["_romof"], "non_existent")
        self.assertNotIn("romof_id", game_attrs)
        self.assertEqual(game_attrs["cloneof_id"], "abcdef0123456789")
        self.assertNotIn("_cloneof", game_attrs)
        
    def test_multiple_unhandled_references_added_only_once(self):
        name_index_mapping = {"existing_game": "abcdef0123456789"}
        game_attrs = {"name": "mslug", "hash": "0123456789abcdef"}
        references = {"romof": "non_existent1", "cloneof": "non_existent2"}
        unhandled_references = create_db.add_game_references(game_attrs, references, name_index_mapping)
        self.assertEqual(len(unhandled_references), 1)
        self.assertEqual(game_attrs["_romof"], "non_existent1")
        self.assertEqual(game_attrs["_cloneof"], "non_existent2")


class TestGetEmulatorAttrs(unittest.TestCase):

    def test_get_mame_emulator_details_extracts_name_and_version(self):
        dat_files = [
            os.path.join(FIXTURES_PATH, "MAME 0.34b1.xml.bz2"),
            os.path.join(FIXTURES_PATH, "MAME 0.263.xml.bz2"),
            os.path.join(FIXTURES_PATH, "MAME 0.3.xml.bz2"),
        ]
        expected_results = [
            ['MAME', '0.34b1'],
            ['MAME', '0.263'],
            ['MAME', '0.3'],
        ]
        for dat_file, expected in zip(dat_files, expected_results):
            details = create_db.get_mame_emulator_details(dat_file)
            self.assertEqual(details, expected)

    def test_get_emulator_attrs_(self):
        dat_file = os.path.join(FIXTURES_PATH, "MAME 0.263.xml.bz2")
        attrs = create_db.get_emulator_attrs(dat_file)
        self.assertDictEqual({'id': 'mame0263', 'name': 'MAME', 'version': '0.263'}, attrs)

class TestProcessGames(unittest.TestCase):

    def test_references_are_properly_added(self):
        dat_path = os.path.join(FIXTURES_PATH, "games_with_cloneof_romof_unordered.xml")
        root = get_dat_root(dat_path)
        emulator_attrs = {'id': 'mame0263', 'name': 'MAME', 'version': '0.263'}
        data, unresolvable_references = create_db.process_games(root, emulator_attrs)
        self.assertEqual(len(unresolvable_references), 0)


    def test_unresolvable_references_are_returned(self):
        dat_path = os.path.join(FIXTURES_PATH, "games_with_cloneof_romof_broken_rel.xml")
        root = get_dat_root(dat_path)
        emulator_attrs = {'id': 'mame0263', 'name': 'MAME', 'version': '0.263'}
        data, unresolvable_references = create_db.process_games(root, emulator_attrs)
        self.assertEqual(len(unresolvable_references), 1)

    def test_resolvable_references_are_added_to_game_attrs(self):
        dat_path = os.path.join(FIXTURES_PATH, "games_with_cloneof_romof_broken_rel.xml")
        root = get_dat_root(dat_path)
        emulator_attrs = {'id': 'mame0263', 'name': 'MAME', 'version': '0.263'}
        data, unresolvable_references = create_db.process_games(root, emulator_attrs)
        columnsj_hash = data["name_index_mapping"]["columnsj"]
        columnsj = data["games"][columnsj_hash]
        self.assertEqual(columnsj["_romof"], "columns")
        self.assertEqual(columnsj["_cloneof"], "columns")

class TestReferences(unittest.TestCase):
    
    def test_references(self):
        dat_path = os.path.join(MAME_DATS_PATH, "MAME 0.37b7.dat.bz2")
        create_db.process_dats_consecutively([dat_path])


if __name__ == "__main__":
    unittest.main()
