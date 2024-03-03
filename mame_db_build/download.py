#!/usr/bin/env python3

import os
from urllib.request import urlretrieve

import py7zr
import rarfile

BASE_URL_1 = "https://www.progettosnaps.net/download/?tipo=dat_mame&file=/dats/MAME/packs/MAME_Dats_{}.7z"
BASE_URL_2 = "https://www.progettosnaps.net/download/?tipo=dat_mame&file=/dats/MAME/MAME_Dats_{}.rar"

OTHER_URLS = [
    ("037b1", "https://www.progettosnaps.net/download/?tipo=dat_mame&file=/dats/MAME/packs/MAME_Dats_037b1.7z"),
    ("037b2", "https://www.progettosnaps.net/download/?tipo=dat_mame&file=/dats/MAME/packs/MAME_Dats_037b2.7z"),
    ("037-52", "https://www.progettosnaps.net/download/?tipo=dat_mame&file=/dats/MAME/MAME_Dats_037-52.rar"),
]

STANDARD_VERSIONED_RANGES = ((1, 31), (33, 36), (53, 262))


def is_valid_archive(path: str) -> bool:
    try:
        py7zr.SevenZipFile(path, mode="r")
        return True
    except (py7zr.Bad7zFile, FileNotFoundError):
        pass
    try:
        rarfile.RarFile(path)
        return True
    except (rarfile.BadRarFile, FileNotFoundError):
        pass
    return False


def download_dat(url, target):
    try:
        urlretrieve(url, target)
        print(url, target)
        return True
    except Exception as e:
        print("Error: ", url, e)
    return False


for range_ in STANDARD_VERSIONED_RANGES:
    for i in range(range_[0], range_[1]):
        version = str(i).zfill(3)
        urls = [BASE_URL_1.format(version), BASE_URL_2.format(version)]
        targets = [
            os.path.join(".", "dats", f"MAME-DATS-{version}.7z"),
            os.path.join(".", "dats", f"MAME-DATS-{version}.rar"),
        ]
        if not any([is_valid_archive(target) for target in targets]):
            for i in range(2):
                if download_dat(urls[i], targets[i]):
                    break

for version, url in OTHER_URLS:
    targets = [
        os.path.join(".", "dats", f"MAME-DATS-{version}.7z"),
        os.path.join(".", "dats", f"MAME-DATS-{version}.rar"),
    ]
    if not any([is_valid_archive(target) for target in targets]):
        download_dat(url, os.path.join(".", "dats", f"MAME-DATS-{version}.{url[-3:]}".replace("..", ".")))
