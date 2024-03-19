#!/usr/bin/env python3

"""
For now, this only validates the MAME source files
"""

import os
import multiprocessing
import shared


def process_dat(path: str) -> None:
    print(os.path.basename(path))
    source = shared.get_source_contents(path)
    try:
        root = shared.get_source_root(source)
    except Exception as e:
        print("Error: ", type(e), path)
    if root and root.tag not in ["mame", "datafile"]:
        print("Unrecognised root tag: ", path, root)


def process_files():
    with multiprocessing.Pool(8) as pool:
        pool.map(process_dat, shared.MAME_DATS)


if __name__ == "__main__":
    process_files()
