import os
import re
import json
from pathlib import Path
from optparse import OptionParser
from romsort.rom_root_folder import RomRootFolder


def get_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


def get_dump_code_regexes(ok_dump_codes):
    regexes = []
    for code in ok_dump_codes:
        # regexes.append(re.compile("^[%s][0-9]{0,2}" % code))
        regexes.append(re.compile("^%s[0-9]{0,2}" % code))
    return regexes


def process(prefs):
    root = RomRootFolder(prefs['rootDir'])
    ok_dump_regexes = get_dump_code_regexes(prefs['okDumpCodes'])
    root.sort(ok_dump_regexes, prefs['okRoCodes'])
    if prefs['writeSummary'] is True:
        root.write_summary(prefs['summaryFilePath'])
    if prefs['writeFiles'] is True:
        if not os.path.isdir(prefs['targetDir']):
            target_path = Path(prefs['targetDir'])
            target_path.mkdir(parents=True, exist_ok=True)
        root.extract_matches(prefs['targetDir'])

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option('-j', '--json', dest='json_prefs', help='Specify input json file')
    (options, args) = parser.parse_args()
    if options.json_prefs is None:
        print(parser.usage)
        exit(0)

    prefs = get_prefs(options.json_prefs)
    process(prefs)
