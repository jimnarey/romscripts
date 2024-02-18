#!/usr/bin/env python3

import os
import pathlib
import csv
import re
import argparse
from typing import Optional


SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
GAME_ID_REGEX = r"[A-Z]{4}[-_][0-9]{3}\.?[0-9]{2}"

PS2_GAME_ID_FILE = "data/PS2-GAMEID-TITLE-MASTER.csv"


def normalise_id(id: str) -> str:
    return "".join(char for char in id if char.isalnum()).upper()


def read_games_data() -> Optional[dict]:
    with open(os.path.join(SCRIPT_PATH, PS2_GAME_ID_FILE), "r") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        return {normalise_id(row["GameID"]): row for row in reader}


def find_files(path: str) -> list[str]:
    root_dir = pathlib.Path(path)
    return [item.name for item in root_dir.rglob("*") if item.is_file()]


def find_game_files(files: list[str]) -> list[str]:
    return [file for file in files if re.search(GAME_ID_REGEX, file)]


def find_unique_game_ids(files: list[str]) -> set[str]:
    game_ids = []
    for file in files:
        game_ids.extend(re.findall(GAME_ID_REGEX, file))
    return set([normalise_id(id) for id in game_ids])


def find_game_matches(game_ids: list[str], games_data: dict[str, dict[str, str]]) -> list[str]:
    matches = [games_data.get(id) for id in game_ids]
    return [match for match in matches if match]  # type: ignore


def main(path):
    games_data = read_games_data()
    files = find_files(path)
    game_files = find_game_files(files)
    unique_ids = find_unique_game_ids(game_files)
    matched_games = find_game_matches(unique_ids, games_data)

    print("{} filename matches for PS2 game IDs found".format(len(game_files)))
    print("{} unique game IDs found".format(len(unique_ids)))
    print("{} IDs matched to games list".format(len(matched_games)))
    print("")
    for name in sorted([game["Name"] for game in matched_games]):
        print(name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="PS2 Game lister",
        description="Lists all games in OPL format within a given directory",
    )
    parser.add_argument("path")
    args = vars(parser.parse_args())
    main(args["path"])
