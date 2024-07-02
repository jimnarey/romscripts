import os
import unittest
from typing import Optional

from lxml import etree as ET
from lxml.etree import XMLParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from arcade_db_build import create_db
from arcade_db_build.shared import db


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


def create_game_fixture(game_element: ET._Element, emulator_version: str = "1", game_name: Optional[str] = None):
    rom_elements = [element for element in game_element if element.tag == "rom"]
    roms = [
        db.Rom(
            name=rom_element.get("name", ""),
            size=rom_element.get("size", 0),
            crc=rom_element.get("crc", ""),
            sha1=rom_element.get("sha1"),
        )
        for rom_element in rom_elements
    ]
    game = db.Game(name=game_name if game_name else game_element.get("name"), roms=roms)
    emulator = db.Emulator(name="MAME", version=emulator_version)
    game_emulator = db.GameEmulator(game=game, emulator=emulator)
    game.game_emulators.append(game_emulator)
    return game


class TestGetRecords(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.rollback()

    def test_get_existing_game_returns_none_when_no_game_exists(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        self.assertIsNone(create_db.get_existing_game(self.session, root[0]))

    def test_get_existing_game_returns_existing_game_with_same_attributes(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        game_1 = create_game_fixture(root[0])
        self.session.add(game_1)
        self.session.commit()
        self.assertEqual(create_db.get_existing_game(self.session, root[0]), game_1)

    def test_get_existing_game_returns_none_when_game_rom_has_different_crc(self):
        root_1 = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        game_1 = create_game_fixture(root_1[0])
        root_2 = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc.xml"))
        self.session.add(game_1)
        self.session.commit()
        self.assertIsNone(create_db.get_existing_game(self.session, root_2[0]))

    def test_get_existing_game_can_handle_multiple_existing_games_with_same_name_without_match(self):
        root_1 = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        game_1 = create_game_fixture(root_1[0])
        self.session.add(game_1)
        root_2 = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc.xml"))
        game_2 = create_game_fixture(root_2[0])
        self.session.add(game_2)
        self.session.commit()
        root_3 = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc_2.xml"))
        self.assertIsNone(create_db.get_existing_game(self.session, root_3[0]))

    def test_get_existing_game_matches_game_with_same_roms_and_disks_sha1(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "games_with_disks.xml"))
        game = create_game_fixture(root[0])
        self.session.add(game)
        self.session.commit()
        self.assertEqual(create_db.get_existing_game(self.session, root[0]), game)

    def test_get_existing_game_matches_game_with_same_roms_and_disks_md5(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "games_with_disks.xml"))
        game = create_game_fixture(root[1])
        self.session.add(game)
        self.session.commit()
        self.assertEqual(create_db.get_existing_game(self.session, root[1]), game)


class TestGetOrCreateRecords(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.parser = XMLParser(remove_comments=True)

    def test_get_or_create_roms_with_a_common_rom(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "games_with_overlapping_roms.xml"))
        rom_elements_1 = [element for element in root[0] if element.tag == "rom"]
        roms_1 = create_db.get_or_create_roms(self.session, rom_elements_1)
        self.session.add_all(roms_1)
        self.session.commit()
        rom_elements_2 = [element for element in root[1] if element.tag == "rom"]
        roms_2 = create_db.get_or_create_roms(self.session, rom_elements_2)
        self.session.add_all(roms_2)
        self.session.commit()
        all_roms = self.session.query(db.Rom).all()
        self.assertEqual(len(set(roms_1).intersection(set(roms_2))), 1)
        self.assertEqual(len(all_roms), 3)

    def test_get_or_create_disks_with_a_common_disk_sha1(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "games_with_overlapping_disks.xml"))
        disk_elements_1 = [element for element in root[0] if element.tag == "disk"]
        disks_1 = create_db.get_or_create_disks(self.session, disk_elements_1)
        self.session.add_all(disks_1)
        self.session.commit()
        disk_elements_2 = [element for element in root[1] if element.tag == "disk"]
        disks_2 = create_db.get_or_create_disks(self.session, disk_elements_2)
        self.session.add_all(disks_2)
        self.session.commit()
        all_disks = self.session.query(db.Disk).all()
        self.assertEqual(len(set(disks_1).intersection(set(disks_2))), 1)
        self.assertEqual(len(all_disks), 3)

    def test_get_or_create_disks_with_a_common_disk_md5(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "games_with_overlapping_disks.xml"))
        disk_elements_1 = [element for element in root[2] if element.tag == "disk"]
        disks_1 = create_db.get_or_create_disks(self.session, disk_elements_1)
        self.session.add_all(disks_1)
        self.session.commit()
        disk_elements_2 = [element for element in root[3] if element.tag == "disk"]
        disks_2 = create_db.get_or_create_disks(self.session, disk_elements_2)
        self.session.add_all(disks_2)
        self.session.commit()
        all_disks = self.session.query(db.Disk).all()
        self.assertEqual(len(set(disks_1).intersection(set(disks_2))), 1)
        self.assertEqual(len(all_disks), 3)

    def test_create_game_with_roms(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        game = create_db.create_game(self.session, root[0])
        self.assertEqual(game.name, "005")
        self.assertEqual(len(game.roms), 22)

    def test_add_features_no_existing_feature(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        game = create_game_fixture(root[0])
        game_emulator = game.game_emulators[0]
        create_db.add_features(self.session, game_emulator, root[0])
        self.assertEqual(len(game_emulator.features), 2)
        self.assertEqual(game_emulator.features[0].overall, "imperfect")
        self.assertEqual(game_emulator.features[0].type, "graphics")
        self.assertEqual(game_emulator.features[1].status, "imperfect")
        self.assertEqual(game_emulator.features[1].type, "sound")

    def test_add_features_with_existing_feature(self):
        root_1 = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        game_1 = create_game_fixture(root_1[0])
        game_emulator_1 = game_1.game_emulators[0]
        create_db.add_features(self.session, game_emulator_1, root_1[0])
        self.session.commit()
        game_2 = create_game_fixture(root_1[0])
        game_emulator_2 = game_2.game_emulators[0]
        create_db.add_features(self.session, game_emulator_2, root_1[0])
        self.session.commit()
        self.assertEqual(len(game_emulator_1.features), 2)
        self.assertEqual(len(game_emulator_2.features), 2)
        self.assertEqual((len(self.session.query(db.Feature).all())), 2)
        self.assertEqual(set(game_emulator_1.features), set(game_emulator_2.features))

    def test_add_driver_no_existing_driver(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        game = create_game_fixture(root[0])
        game_emulator = game.game_emulators[0]
        create_db.add_driver(self.session, game_emulator, root[0])
        self.assertEqual(game_emulator.driver.status, "imperfect")
        self.assertEqual(game_emulator.driver.emulation, "good")
        self.assertEqual(game_emulator.driver.savestate, "unsupported")

    def test_add_driver_with_existing_driver(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        game_1 = create_game_fixture(root[0])
        game_emulator_1 = game_1.game_emulators[0]
        create_db.add_driver(self.session, game_emulator_1, root[0])
        game_2 = create_game_fixture(root[0])
        game_emulator_2 = game_2.game_emulators[0]
        create_db.add_driver(self.session, game_emulator_2, root[0])
        self.session.commit()
        self.assertEqual(game_emulator_1.driver, game_emulator_2.driver)


class TestAddGameReference(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.game_1 = db.Game(name="Test Game")
        self.emulator = db.Emulator(name="Test Emulator")
        self.game_2 = db.Game(name="Target Game")
        self.game_emulator = db.GameEmulator(game=self.game_2, emulator=self.emulator)
        self.session.add_all([self.game_1, self.emulator, self.game_2, self.game_emulator])
        self.session.commit()

    def test_add_game_reference_sets_reference(self):
        result = create_db.add_game_reference(
            self.session, self.game_1, self.emulator, "cloneof", str(self.game_2.name)
        )
        self.assertEqual(self.game_1.cloneof, self.game_2)
        self.assertTrue(result)

    def test_add_game_reference_returns_false_when_no_target_game(self):
        result = create_db.add_game_reference(self.session, self.game_1, self.emulator, "cloneof", "Nonexistent Game")
        self.assertEqual(self.game_1.cloneof, None)
        self.assertFalse(result)


class TestAddGameReferences(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.game_1 = db.Game(name="Test Game")
        self.emulator = db.Emulator(name="Test Emulator")
        self.game_2 = db.Game(name="Target Game")
        self.game_emulator = db.GameEmulator(game=self.game_2, emulator=self.emulator)
        self.session.add_all([self.game_1, self.emulator, self.game_2, self.game_emulator])
        self.session.commit()

    def test_add_game_references_sets_references_when_all_valid(self):
        game_element = ET.Element("game", name="Test Game", cloneof="Target Game", romof="Target Game")
        unhandled_references = create_db.add_game_references(self.session, self.emulator, self.game_1, game_element)
        self.assertEqual(self.game_1.cloneof, self.game_2)
        self.assertEqual(self.game_1.romof, self.game_2)
        self.assertListEqual(unhandled_references, [])

    def test_add_game_references_sets_references_when_one_valid(self):
        game_element = ET.Element("game", name="Test Game", cloneof="Target Game", romof="Nonexistent Game")
        unhandled_references = create_db.add_game_references(self.session, self.emulator, self.game_1, game_element)
        self.assertEqual(self.game_1.cloneof, self.game_2)
        self.assertIsNone(self.game_1.romof)
        self.assertListEqual(
            unhandled_references, [{"game": "Test Game", "attribute": "romof", "target": "Nonexistent Game"}]
        )

    def test_add_game_references_when_none_valid(self):
        game_element = ET.Element("game", name="Test Game", cloneof="Nonexistent Game", romof="Nonexistent Game")
        unhandled_references = create_db.add_game_references(self.session, self.emulator, self.game_1, game_element)
        self.assertIsNone(self.game_1.cloneof)
        self.assertIsNone(self.game_1.romof)
        self.assertListEqual(
            unhandled_references,
            [
                {"game": "Test Game", "attribute": "cloneof", "target": "Nonexistent Game"},
                {"game": "Test Game", "attribute": "romof", "target": "Nonexistent Game"},
            ],
        )


class TestGetEmulatorDetails(unittest.TestCase):
    def test_get_emulator_name_xml(self):
        dat_file = "romscripts/arcade_db_build/mame_db_source/dats/MAME 0.158.xml.bz2"
        self.assertEqual(create_db.get_mame_emulator_details(dat_file), ["MAME", "0.158"])

    def test_get_emulator_name_dat(self):
        dat_file = "romscripts/arcade_db_build/mame_db_source/dats/MAME 0.37b2.dat.bz2"
        self.assertEqual(create_db.get_mame_emulator_details(dat_file), ["MAME", "0.37b2"])


class TestAddGameEmulatorRelationship(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_add_game_emulator_relationship_creates_relationship(self):
        game = db.Game(name="Test Game")
        emulator = db.Emulator(name="Test Emulator")
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        game_element = root[0]
        create_db.add_game_emulator_relationship(self.session, game_element, game, emulator)
        self.assertEqual(game, emulator.game_emulators[0].game)
        self.assertEqual(emulator, game.game_emulators[0].emulator)

    def test_add_game_emulator_relationship_adds_driver_and_features(self):
        game = db.Game(name="Test Game")
        emulator = db.Emulator(name="Test Emulator")
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        root = tree.getroot()
        game_element = root[0]
        create_db.add_game_emulator_relationship(self.session, game_element, game, emulator)
        self.assertEqual(game.game_emulators[0].driver.status, "imperfect")
        self.assertEqual(game.game_emulators[0].features[0].overall, "imperfect")
        self.assertEqual(game.game_emulators[0].features[1].status, "imperfect")


class TestProcessGames(unittest.TestCase):

    # TODO: Test num_added and num_updated values
    # Test all_references is properly populated
    # Test populates disks correctly

    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_creates_game(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        emulator = db.Emulator(name="MAME", version="1")
        create_db.process_games(self.session, root, emulator)
        game = self.session.query(db.Game).filter_by(name="005").one()
        self.assertEqual(game.name, "005")
        self.assertEqual(len(game.roms), 22)

    def test_process_games_adds_game_references_ids(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "games_with_cloneof_romof_rels.xml"))
        emulator = db.Emulator(name="MAME", version="1")
        _, _, unhandled_references = create_db.process_games(self.session, root, emulator)
        self.assertListEqual(unhandled_references, [])
        self.assertEqual(self.session.query(db.Game).filter_by(name="columnsj").one().cloneof_id, 1)
        self.assertEqual(self.session.query(db.Game).filter_by(name="columnsj").one().romof_id, 1)

    def test_adds_emulator_to_existing_game_with_same_attributes_and_roms(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        emulator_1 = db.Emulator(name="MAME", version="1")
        self.session.add(emulator_1)
        self.session.commit()
        emulator_1_id = emulator_1.id
        create_db.process_games(self.session, root, emulator_1)
        emulator_2 = db.Emulator(name="MAME", version="2")
        self.session.add(emulator_2)
        self.session.commit()
        emulator_2_id = emulator_2.id
        create_db.process_games(self.session, root, emulator_2)
        games = self.session.query(db.Game).filter_by(name="005").all()
        game_emulator_ids = [ge.emulator_id for ge in games[0].game_emulators]
        self.assertEqual(len(games), 1)
        self.assertEqual(len(game_emulator_ids), 2)
        self.assertIn(emulator_1_id, game_emulator_ids)
        self.assertIn(emulator_2_id, game_emulator_ids)

    def test_adds_emulator_to_existing_game_with_same_attributes_and_disks(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "games_with_disks.xml"))
        emulator_1 = db.Emulator(name="MAME", version="1")
        self.session.add(emulator_1)
        self.session.commit()
        emulator_1_id = emulator_1.id
        create_db.process_games(self.session, root, emulator_1)
        emulator_2 = db.Emulator(name="MAME", version="2")
        self.session.add(emulator_2)
        self.session.commit()
        emulator_2_id = emulator_2.id
        create_db.process_games(self.session, root, emulator_2)
        games = self.session.query(db.Game).filter_by(name="2spicy").all()
        game_emulator_ids = [ge.emulator_id for ge in games[0].game_emulators]
        self.assertEqual(len(games), 1)
        self.assertEqual(len(game_emulator_ids), 2)
        self.assertIn(emulator_1_id, game_emulator_ids)
        self.assertIn(emulator_2_id, game_emulator_ids)

    def test_creates_new_game_when_one_rom_is_different(self):
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game.xml"))
        emulator_1 = db.Emulator(name="MAME", version="1")
        self.session.add(emulator_1)
        self.session.commit()
        emulator_1_id = emulator_1.id
        create_db.process_games(self.session, root, emulator_1)
        root = get_dat_root(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc.xml"))
        emulator_2 = db.Emulator(name="MAME", version="2")
        self.session.add(emulator_2)
        self.session.commit()
        emulator_2_id = emulator_2.id
        create_db.process_games(self.session, root, emulator_2)
        games = self.session.query(db.Game).filter_by(name="005").all()
        self.assertEqual(len(games), 2)
        game_emulator_1_ids = [ge.emulator_id for ge in games[0].game_emulators]
        game_emulator_2_ids = [ge.emulator_id for ge in games[1].game_emulators]
        self.assertIn(emulator_1_id, game_emulator_1_ids)
        self.assertIn(emulator_2_id, game_emulator_2_ids)


if __name__ == "__main__":
    unittest.main()
