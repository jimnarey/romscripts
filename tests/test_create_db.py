import os
import unittest


from lxml import etree as ET
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from arcade_db import create_db
from arcade_db.shared import db


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


class TestGetEmulatorAttrs(unittest.TestCase):
    def test_get_mame_emulator_details_extracts_name_and_version(self):
        dat_files = [
            os.path.join(FIXTURES_PATH, "MAME 0.34b1.xml.bz2"),
            os.path.join(FIXTURES_PATH, "MAME 0.263.xml.bz2"),
            os.path.join(FIXTURES_PATH, "MAME 0.3.xml.bz2"),
        ]
        expected_results = [
            ["MAME", "0.34b1"],
            ["MAME", "0.263"],
            ["MAME", "0.3"],
        ]
        for dat_file, expected in zip(dat_files, expected_results):
            details = create_db.get_mame_emulator_details(dat_file)
            self.assertEqual(details, expected)

    def test_get_emulator_attrs_(self):
        dat_file = os.path.join(FIXTURES_PATH, "MAME 0.263.xml.bz2")
        attrs = create_db.get_emulator_attrs(dat_file)
        self.assertDictEqual({"id": "mame0_263", "name": "MAME", "version": "0.263"}, attrs)


if __name__ == "__main__":
    unittest.main()
