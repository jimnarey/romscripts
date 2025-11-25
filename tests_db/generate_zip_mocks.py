#!/usr/bin/env python3

import os
import zipfile
import json


PATH = "somedir"

zips = [f for f in os.listdir(PATH) if f.endswith(".zip")]

zip_specs = {}

for zip_name in zips:
    zip_path = os.path.join(PATH, zip_name)
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        print(f"Processing {zip_name}")
        zip_specs[zip_name] = [
            {"name": file.filename, "size": file.file_size, "crc": file.CRC} for file in zip_file.infolist()
        ]

with open("mame2003p_full_non_merged_all_2021_zip_specs.json", "w") as json_file:
    json.dump(zip_specs, json_file)
