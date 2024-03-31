import os
import unittest
from typing import Optional
from xml.etree import ElementTree as ET
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from arcade_db_build import create_db

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_PATH = os.path.join(SCRIPT_PATH, "fixtures", "create_db")


class TestModels(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        create_db.Base.metadata.create_all(engine)
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
        emulator = create_db.Emulator(name="emu1", version="1.0")
        roms = [
            create_db.Rom(name="rom1", size=100, crc="crc1", sha1="sha1"),
            create_db.Rom(name="rom2", size=200, crc="crc2", sha1="sha2"),
        ]
        game = create_db.Game(isbios=False, name="game1", year="2000", manufacturer="man1", roms=roms)
        game_emulator = create_db.GameEmulator(game=game, emulator=emulator)
        self.session.add(game_emulator)
        self.session.commit()
        db_game = self.session.query(create_db.Game).filter_by(name="game1").one()
        db_emulator = self.session.query(create_db.Emulator).filter_by(name="emu1").one()
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


def create_game_fixture(game_element: ET.Element, emulator_version: str = "1", game_name: Optional[str] = None):
    rom_elements = [element for element in game_element if element.tag == "rom"]
    roms = [
        create_db.Rom(
            name=rom_element.get("name"),
            size=rom_element.get("size"),
            crc=rom_element.get("crc"),
            sha1=rom_element.get("sha1"),
        )
        for rom_element in rom_elements
    ]
    game = create_db.Game(name=game_name if game_name else game_element.get("name"), roms=roms)
    emulator = create_db.Emulator(name="MAME", version=emulator_version)
    game_emulator = create_db.GameEmulator(game=game, emulator=emulator)
    game.game_emulators.append(game_emulator)
    return game


class TestGetRecords(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        create_db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.rollback()

    def test_get_all_instance_attributes(self):
        driver = create_db.Driver(
            palettesize="abc",
            hiscoresave="def",
            requiresartwork="ghi",
            unofficial="jkl",
            good="mno",
            status="pqr",
            graphic="stu",
            cocktailmode="vwx",
            savestate="yz",
            protection="abc",
            emulation="def",
            cocktail="ghi",
            color="jkl",
            nosoundhardware="mno",
            sound="pqr",
            incomplete="stu",
        )
        all_attrs = create_db.get_instance_attributes(driver, create_db.Driver)
        # Confirm the driver has an id attribute which is not returned
        self.assertIsNone(driver.id)
        # Confirm the driver has a game_emulators attribute which is not returned
        self.assertEqual(driver.game_emulators, [])
        self.assertEqual(
            all_attrs,
            {
                "palettesize": "abc",
                "hiscoresave": "def",
                "requiresartwork": "ghi",
                "unofficial": "jkl",
                "good": "mno",
                "status": "pqr",
                "graphic": "stu",
                "cocktailmode": "vwx",
                "savestate": "yz",
                "protection": "abc",
                "emulation": "def",
                "cocktail": "ghi",
                "color": "jkl",
                "nosoundhardware": "mno",
                "sound": "pqr",
                "incomplete": "stu",
            },
        )

    def test_get_existing_record_returns_record_when_passed_all_attributes(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        game = create_game_fixture(root[0])
        self.session.add(game)
        self.session.commit()
        instance_attrs = {c.key: getattr(game, c.key) for c in inspect(game).mapper.column_attrs}
        instance_attrs.pop(inspect(create_db.Game).primary_key[0].key, None)
        self.assertEqual(create_db.get_existing_records(self.session, create_db.Game, instance_attrs), [game])

    def test_get_existing_record_returns_none_when_no_record_exists(self):
        self.assertEqual(create_db.get_existing_records(self.session, create_db.Game, {"name": "game"}), [])

    def test_get_existing_record_returns_record_when_passed_some_attributes(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        game = create_game_fixture(root[0])
        self.session.add(game)
        self.session.commit()
        self.assertEqual(create_db.get_existing_records(self.session, create_db.Game, {"name": "005"}), [game])

    def test_get_existing_game_returns_none_when_no_game_exists(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        self.assertIsNone(create_db.get_existing_game(self.session, root[0]))

    def test_get_existing_game_returns_existing_game_with_same_attributes(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        game_1 = create_game_fixture(root[0])
        self.session.add(game_1)
        self.session.commit()
        self.assertEqual(create_db.get_existing_game(self.session, root[0]), game_1)

    def test_get_existing_game_returns_none_when_game_rom_has_different_crc(self):
        tree_1 = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root_1 = tree_1.getroot()
        game_1 = create_game_fixture(root_1[0])
        tree_2 = ET.parse(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc.xml"))
        root_2 = tree_2.getroot()
        self.session.add(game_1)
        self.session.commit()
        self.assertIsNone(create_db.get_existing_game(self.session, root_2[0]))

    def test_get_existing_game_can_handle_multiple_existing_games_with_same_name_with_match(self):
        tree_1 = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root_1 = tree_1.getroot()
        game_1 = create_game_fixture(root_1[0])
        self.session.add(game_1)
        tree_2 = ET.parse(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc.xml"))
        root_2 = tree_2.getroot()
        game_2 = create_game_fixture(root_2[0])
        self.session.add(game_2)
        self.session.commit()
        self.assertEqual(create_db.get_existing_game(self.session, root_1[0]), game_1)

    def test_get_existing_game_can_handle_multiple_existing_games_with_same_name_without_match(self):
        tree_1 = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root_1 = tree_1.getroot()
        game_1 = create_game_fixture(root_1[0])
        self.session.add(game_1)
        tree_2 = ET.parse(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc.xml"))
        root_2 = tree_2.getroot()
        game_2 = create_game_fixture(root_2[0])
        self.session.add(game_2)
        self.session.commit()
        tree_3 = ET.parse(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc_2.xml"))
        root_3 = tree_3.getroot()
        self.assertIsNone(create_db.get_existing_game(self.session, root_3[0]))


class TestCreateRecords(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        create_db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_get_or_create_roms_with_a_common_rom(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "games_with_overlapping_roms.xml"))
        root = tree.getroot()
        rom_elements_1 = [element for element in root[0] if element.tag == "rom"]
        roms_1 = create_db.get_or_create_roms(self.session, rom_elements_1)
        self.session.add_all(roms_1)
        self.session.commit()
        rom_elements_2 = [element for element in root[1] if element.tag == "rom"]
        roms_2 = create_db.get_or_create_roms(self.session, rom_elements_2)
        self.session.add_all(roms_2)
        self.session.commit()
        all_roms = self.session.query(create_db.Rom).all()
        self.assertEqual(len(set(roms_1).intersection(set(roms_2))), 1)
        self.assertEqual(len(all_roms), 3)

    def test_create_game_with_roms(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        game = create_db.create_game(self.session, root[0])
        self.assertEqual(game.name, "005")
        self.assertEqual(len(game.roms), 22)

    def test_get_or_create_roms_adds_sha1_to_existing_rom(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_rom_twice_add_sha1.xml"))
        root = tree.getroot()
        rom_elements_1 = [root[0]]
        rom_elements_2 = [root[1]]
        roms_1 = create_db.get_or_create_roms(self.session, rom_elements_1)
        self.session.add_all(roms_1)
        self.session.commit()
        self.assertIsNone(roms_1[0].sha1)
        roms_2 = create_db.get_or_create_roms(self.session, rom_elements_2)
        self.assertEqual(roms_1[0].sha1, "123456789012345678901234567890")
        self.assertEqual(roms_1, roms_2)

    def test_create_features(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        root = tree.getroot()
        features = create_db.create_features(root[0])
        self.assertEqual(features[0].overall, "imperfect")
        self.assertEqual(features[0].type, "graphics")
        self.assertEqual(features[1].status, "imperfect")
        self.assertEqual(features[1].type, "sound")

    def test_create_driver(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        root = tree.getroot()
        driver = create_db.create_driver(root[0])
        self.assertEqual(driver.status, "imperfect")
        self.assertEqual(driver.emulation, "good")
        self.assertEqual(driver.savestate, "unsupported")

    def test_add_features_no_existing_feature(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        root = tree.getroot()
        game = create_game_fixture(root[0])
        game_emulator = game.game_emulators[0]
        create_db.add_features(self.session, game_emulator, root[0])
        self.assertEqual(len(game_emulator.features), 2)
        self.assertEqual(game_emulator.features[0].overall, "imperfect")
        self.assertEqual(game_emulator.features[0].type, "graphics")
        self.assertEqual(game_emulator.features[1].status, "imperfect")
        self.assertEqual(game_emulator.features[1].type, "sound")

    def test_add_features_with_existing_feature(self):
        tree_1 = ET.parse(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        root_1 = tree_1.getroot()
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
        self.assertEqual((len(self.session.query(create_db.Feature).all())), 2)
        self.assertEqual(set(game_emulator_1.features), set(game_emulator_2.features))

    def test_add_driver_no_existing_driver(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        root = tree.getroot()
        game = create_game_fixture(root[0])
        game_emulator = game.game_emulators[0]
        create_db.add_driver(self.session, game_emulator, root[0])
        self.assertEqual(game_emulator.driver.status, "imperfect")
        self.assertEqual(game_emulator.driver.emulation, "good")
        self.assertEqual(game_emulator.driver.savestate, "unsupported")

    def test_add_driver_with_existing_driver(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game_with_features_driver.xml"))
        root = tree.getroot()
        game_1 = create_game_fixture(root[0])
        game_emulator_1 = game_1.game_emulators[0]
        create_db.add_driver(self.session, game_emulator_1, root[0])
        game_2 = create_game_fixture(root[0])
        game_emulator_2 = game_2.game_emulators[0]
        create_db.add_driver(self.session, game_emulator_2, root[0])
        self.session.commit()
        self.assertEqual(game_emulator_1.driver, game_emulator_2.driver)


class TestCreateGameReferences(unittest.TestCase):
    def test_create_game_references_with_cloneof_and_romof(self):
        game_element = ET.Element("game", {"cloneof": "game1", "romof": "game2"})
        references = create_db.create_game_references(game_element)
        self.assertEqual(references, {"cloneof": "game1", "romof": "game2"})

    def test_create_game_references_with_only_cloneof(self):
        game_element = ET.Element("game", {"cloneof": "game1"})
        references = create_db.create_game_references(game_element)
        self.assertEqual(references, {"cloneof": "game1"})

    def test_create_game_references_with_no_references(self):
        game_element = ET.Element("game")
        references = create_db.create_game_references(game_element)
        self.assertIsNone(references)


class TestAddGameReference(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        create_db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.game_1 = create_db.Game(name="Test Game")
        self.emulator = create_db.Emulator(name="Test Emulator")
        self.game_2 = create_db.Game(name="Target Game")
        self.game_emulator = create_db.GameEmulator(game=self.game_2, emulator=self.emulator)
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
        create_db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.game_1 = create_db.Game(name="Test Game")
        self.emulator = create_db.Emulator(name="Test Emulator")
        self.game_2 = create_db.Game(name="Target Game")
        self.game_emulator = create_db.GameEmulator(game=self.game_2, emulator=self.emulator)
        self.session.add_all([self.game_1, self.emulator, self.game_2, self.game_emulator])
        self.session.commit()

    def test_add_game_references_sets_references_when_all_valid(self):
        references = {"cloneof": "Target Game", "romof": "Target Game"}
        create_db.add_game_references(self.session, self.emulator, references, self.game_1)
        self.assertEqual(self.game_1.cloneof, self.game_2)
        self.assertEqual(self.game_1.romof, self.game_2)
        self.assertDictEqual(references, {})

    def test_add_game_references_sets_references_when_one_valid(self):
        references = {"cloneof": "Target Game", "romof": "Nonexistent Game"}
        create_db.add_game_references(self.session, self.emulator, references, self.game_1)
        self.assertEqual(self.game_1.cloneof, self.game_2)
        self.assertIsNone(self.game_1.romof)
        self.assertDictEqual(references, {"romof": "Nonexistent Game"})

    def test_add_game_references_when_none_valid(self):
        references = {"cloneof": "Nonexistent Game", "romof": "Nonexistent Game"}
        create_db.add_game_references(self.session, self.emulator, references, self.game_1)
        self.assertIsNone(self.game_1.cloneof)
        self.assertIsNone(self.game_1.romof)
        self.assertDictEqual(references, {"cloneof": "Nonexistent Game", "romof": "Nonexistent Game"})


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
        create_db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_add_game_emulator_relationship_creates_relationship(self):
        game = create_db.Game(name="Test Game")
        emulator = create_db.Emulator(name="Test Emulator")
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        game_element = root[0]
        create_db.add_game_emulator_relationship(self.session, game_element, game, emulator)
        self.assertEqual(game, emulator.game_emulators[0].game)
        self.assertEqual(emulator, game.game_emulators[0].emulator)

    def test_add_game_emulator_relationship_adds_driver_and_features(self):
        game = create_db.Game(name="Test Game")
        emulator = create_db.Emulator(name="Test Emulator")
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

    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        create_db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_creates_game(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        emulator = create_db.Emulator(name="MAME", version="1")
        create_db.process_games(self.session, root, emulator)
        game = self.session.query(create_db.Game).filter_by(name="005").one()
        self.assertEqual(game.name, "005")
        self.assertEqual(len(game.roms), 22)

    def test_process_games_game_references_id(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "games_with_cloneof_romof_rels.xml"))
        root = tree.getroot()
        emulator = create_db.Emulator(name="MAME", version="1")
        all_references, _, _ = create_db.process_games(self.session, root, emulator)
        self.assertEqual(len(all_references), 1)
        game_reference = all_references[0]
        self.assertDictEqual(game_reference, {"cloneof": "columns", "romof": "columns", "id": "1"})
        game_id = game_reference["id"]
        game = self.session.query(create_db.Game).filter_by(id=game_id).one()
        self.assertIsNotNone(game)

    def test_adds_emulator_to_existing_game_with_same_attributes(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        emulator_1 = create_db.Emulator(name="MAME", version="1")
        create_db.process_games(self.session, root, emulator_1)
        emulator_2 = create_db.Emulator(name="MAME", version="2")
        create_db.process_games(self.session, root, emulator_2)
        games = self.session.query(create_db.Game).filter_by(name="005").all()
        game_emulators = games[0].game_emulators
        self.assertEqual(len(games), 1)
        self.assertEqual(len(game_emulators), 2)
        self.assertIn(emulator_1, [ge.emulator for ge in game_emulators])
        self.assertIn(emulator_2, [ge.emulator for ge in game_emulators])

    def test_creates_new_game_when_one_rom_is_different(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        emulator_1 = create_db.Emulator(name="MAME", version="1")
        create_db.process_games(self.session, root, emulator_1)
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game_diff_rom_crc.xml"))
        root = tree.getroot()
        emulator_2 = create_db.Emulator(name="MAME", version="2")
        create_db.process_games(self.session, root, emulator_2)
        games = self.session.query(create_db.Game).filter_by(name="005").all()
        game_emulators_1 = games[0].game_emulators
        game_emulators_2 = games[1].game_emulators
        self.assertEqual(len(games), 2)
        self.assertEqual([emulator_1], [ge.emulator for ge in game_emulators_1])
        self.assertEqual([emulator_2], [ge.emulator for ge in game_emulators_2])


if __name__ == "__main__":
    unittest.main()
