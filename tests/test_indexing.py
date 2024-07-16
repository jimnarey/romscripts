import unittest
from lxml.etree import Element
from arcade_db.shared import indexing, db

# TODO: Test for cases where (some of) the XML attributes are empty.
# Test that e.g. when size is absent in an XML it produces the same hash as when it is absent in a Rom record


class TestIndexing(unittest.TestCase):
    def setUp(self):

        self.game_name = "Game"

        self.disk1 = db.Disk(
            name="disk1",
            md5="md5hash",
        )

        self.disk2 = db.Disk(
            name="disk2",
            md5="md5hash2",
        )

        self.disk3 = db.Disk(name="disk3", sha1="sha1hash")

        self.rom1 = db.Rom(name="rom1", size=100, crc="crchash")

        self.rom2 = db.Rom(name="rom2", size=200, crc="crchash2")

        self.disk_element1 = Element("disk", name="disk1", md5="md5hash")
        self.disk_element2 = Element("disk", name="disk2", md5="md5hash2")
        self.disk_element3 = Element("disk", name="disk3", sha1="sha1hash")
        self.rom_element1 = Element("rom", name="rom1", size="100", crc="crchash")
        self.rom_element2 = Element("rom", name="rom2", size="200", crc="crchash2")

    def test_roms_signature_from_one_rom(self):
        result = indexing.roms_signature_from_roms([self.rom1])
        self.assertEqual(result, "rom1/100/crchash")

    def test_roms_signature_from_two_roms(self):
        result = indexing.roms_signature_from_roms([self.rom1, self.rom2])
        self.assertEqual(result, "rom1/100/crchash,rom2/200/crchash2")

    def test_roms_signature_from_one_element(self):
        result = indexing.roms_signature_from_elements([self.rom_element1])
        self.assertEqual(result, "rom1/100/crchash")

    def test_roms_signature_from_two_elements(self):
        result = indexing.roms_signature_from_elements([self.rom_element1, self.rom_element2])
        self.assertEqual(result, "rom1/100/crchash,rom2/200/crchash2")

    def test_get_roms_signature(self):
        result = indexing.get_roms_signature(
            [{"name": "rom1", "size": 100, "crc": "crchash"}, {"name": "rom2", "size": 200, "crc": "crchash2"}]
        )
        self.assertEqual(result, "rom1/100/crchash,rom2/200/crchash2")

    def test_get_index_from_records(self):
        result = indexing.get_game_index_from_records(self.game_name, [self.rom1, self.rom2])
        self.assertEqual(result, "65ae03eb08c4fc99fede5304a8abba8df18da2acf9dc9c32379c14c43843b00a")

    def test_get_index_from_elements(self):
        result = indexing.get_game_index_from_elements(self.game_name, [self.rom_element1, self.rom_element2])
        self.assertEqual(result, "65ae03eb08c4fc99fede5304a8abba8df18da2acf9dc9c32379c14c43843b00a")


if __name__ == "__main__":
    unittest.main()
