import unittest
from lxml.etree import Element
from arcade_db_build.shared import indexing, db


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

    def test_get_disks_signature_from_one_disk_md5(self):
        result = indexing.get_disks_signature_from_disks([self.disk1], "md5")
        self.assertEqual(result, "disk1/md5hash")

    def test_get_disks_signature_from_one_disk_sha1(self):
        result = indexing.get_disks_signature_from_disks([self.disk3], "sha1")
        self.assertEqual(result, "disk3/sha1hash")

    def test_get_disks_signature_from_two_disks_md5(self):
        result = indexing.get_disks_signature_from_disks([self.disk1, self.disk2], "md5")
        self.assertEqual(result, "disk1/md5hash,disk2/md5hash2")

    def test_get_disks_signature_from_one_element_md5(self):
        result = indexing.get_disks_signature_from_elements([self.disk_element1], "md5")
        self.assertEqual(result, "disk1/md5hash")

    def test_get_disks_signature_from_one_element_sha1(self):
        result = indexing.get_disks_signature_from_elements([self.disk_element3], "sha1")
        self.assertEqual(result, "disk3/sha1hash")

    def test_get_disks_signature_from_two_elements_md5(self):
        result = indexing.get_disks_signature_from_elements([self.disk_element1, self.disk_element2], "md5")
        self.assertEqual(result, "disk1/md5hash,disk2/md5hash2")

    def test_get_disks_signature_from_disks_returns_none_if_no_hash(self):
        result = indexing.get_disks_signature_from_disks([self.disk1, self.disk3], "sha1")
        self.assertIsNone(result)

    def test_get_disks_signature_from_elements_returns_none_if_no_hash(self):
        result = indexing.get_disks_signature_from_elements([self.disk_element1, self.disk_element3], "sha1")
        self.assertIsNone(result)

    def test_get_disks_signature(self):
        result = indexing.get_disks_signature(
            [{"name": "disk1", "md5": "md5hash"}, {"name": "disk2", "md5": "md5hash2"}], "md5"
        )
        self.assertEqual(result, "disk1/md5hash,disk2/md5hash2")

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

    def test_get_data_signature_from_records(self):
        result = indexing.get_data_signature_from_records([self.rom1, self.rom2], [self.disk1, self.disk2], "md5")
        self.assertEqual(result, "rom1/100/crchash,rom2/200/crchash2+disk1/md5hash,disk2/md5hash2")

    def test_get_data_signature_from_records_roms_only(self):
        result = indexing.get_data_signature_from_records([self.rom1, self.rom2], [], "md5")
        self.assertEqual(result, "rom1/100/crchash,rom2/200/crchash2+")

    def test_get_data_signature_from_elements(self):
        result = indexing.get_data_signature_from_elements(
            [self.rom_element1, self.rom_element2], [self.disk_element1, self.disk_element2], "md5"
        )
        self.assertEqual(result, "rom1/100/crchash,rom2/200/crchash2+disk1/md5hash,disk2/md5hash2")

    def test_get_data_signature_from_elements_roms_only(self):
        result = indexing.get_data_signature_from_elements([self.rom_element1, self.rom_element2], [], "md5")
        self.assertEqual(result, "rom1/100/crchash,rom2/200/crchash2+")

    def test_get_index_from_records(self):
        result = indexing.get_game_index_from_records_by_disk_hash_type(
            self.game_name, [self.rom1, self.rom2], [self.disk1, self.disk2], "md5"
        )
        self.assertEqual(result, "406c1473cd4ac6b361785b247853ff30f63211823f6c2cb78ac42e4e25b1f7b6")

    def test_get_index_from_elements(self):
        result = indexing.get_game_index_from_elements_by_disk_hash_type(
            self.game_name, [self.rom_element1, self.rom_element2], [self.disk_element1, self.disk_element2], "md5"
        )
        self.assertEqual(result, "406c1473cd4ac6b361785b247853ff30f63211823f6c2cb78ac42e4e25b1f7b6")


if __name__ == "__main__":
    unittest.main()
