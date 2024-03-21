import os
import unittest
from xml.etree import ElementTree as ET
from sqlalchemy import create_engine
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
        emulator = create_db.Emulator(name="emu1", version="1.0")
        roms = [
            create_db.Rom(name="rom1", size=100, crc="crc1", sha1="sha1"),
            create_db.Rom(name="rom2", size=200, crc="crc2", sha1="sha2"),
        ]
        game = create_db.Game(
            is_bios=False, name="game1", year="2000", manufacturer="man1", emulators=[emulator], roms=roms
        )
        self.session.add(game)
        self.session.commit()
        db_game = self.session.query(create_db.Game).filter_by(name="game1").one()
        self.assertEqual(db_game, game)
        self.assertEqual(db_game.emulators[0], emulator)
        self.assertEqual(set(rom.name for rom in db_game.roms), {"rom1", "rom2"})


def create_game_fixture(emulator_name: str = "emu1", rom_crcs: list[str] = ["crc1", "crc2"]):
    roms = [
        create_db.Rom(name="rom1", size=100, crc=rom_crcs[0], sha1="sha1"),
        create_db.Rom(name="rom2", size=200, crc=rom_crcs[1], sha1="sha2"),
    ]
    emulator = create_db.Emulator(name=emulator_name, version="1.0")
    game = create_db.Game(is_bios=False, name="game", year="2000", manufacturer="man1", emulators=[emulator], roms=roms)
    return game


class TestGameExists(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        create_db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.rollback()

    def test_returns_none_when_no_game_exists(self):
        game = create_game_fixture()
        self.assertIsNone(create_db.get_existing_game(self.session, game))

    def test_returns_existing_game_with_same_attributes(self):
        game_1 = create_game_fixture()
        game_2 = create_game_fixture()
        # Confirm we're not dealing with the same instance
        self.assertNotEqual(game_1, game_2)
        self.session.add(game_1)
        self.session.commit()
        self.assertEqual(create_db.get_existing_game(self.session, game_2), game_1)

    def test_returns_existing_game_with_same_attributes_except_emulator(self):
        game_1 = create_game_fixture()
        self.session.add(game_1)
        self.session.commit()
        game_2 = create_game_fixture(emulator_name="emu2")
        self.assertEqual(create_db.get_existing_game(self.session, game_2), game_1)

    def test_returns_none_when_game_rom_has_different_crc(self):
        game_1 = create_game_fixture()
        self.session.add(game_1)
        self.session.commit()
        game_2 = create_game_fixture(rom_crcs=["crc1", "crc3"])
        self.assertIsNone(create_db.get_existing_game(self.session, game_2))


class TestCreateGame(unittest.TestCase):
    def test_create_game(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        game = create_db.create_game(root[0])
        self.assertIsNotNone(game)
        self.assertEqual(game.name, "005")
        self.assertEqual(len(game.roms), 22)


class TestGetEmulatorDetails(unittest.TestCase):
    def test_get_emulator_name_xml(self):
        dat_file = "romscripts/arcade_db_build/mame_db_source/dats/MAME 0.158.xml.bz2"
        self.assertEqual(create_db.get_mame_emulator_details(dat_file), ["MAME", "0.158"])

    def test_get_emulator_name_dat(self):
        dat_file = "romscripts/arcade_db_build/mame_db_source/dats/MAME 0.37b2.dat.bz2"
        self.assertEqual(create_db.get_mame_emulator_details(dat_file), ["MAME", "0.37b2"])


class TestProcessGames(unittest.TestCase):
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

    def test_adds_emulator_to_existing_game_with_same_attributes(self):
        tree = ET.parse(os.path.join(FIXTURES_PATH, "one_game.xml"))
        root = tree.getroot()
        emulator_1 = create_db.Emulator(name="MAME", version="1")
        create_db.process_games(self.session, root, emulator_1)
        emulator_2 = create_db.Emulator(name="MAME", version="2")
        create_db.process_games(self.session, root, emulator_2)
        games = self.session.query(create_db.Game).filter_by(name="005").all()
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0].emulators, [emulator_1, emulator_2])

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
        self.assertEqual(len(games), 2)
        self.assertEqual(games[0].emulators, [emulator_1])
        self.assertEqual(games[1].emulators, [emulator_2])


if __name__ == "__main__":
    unittest.main()
