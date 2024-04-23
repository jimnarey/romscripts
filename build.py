#!/usr/bin/env python3

import re
from optparse import OptionParser
from arcade_db_build import create_db
from arcade_db_build.shared import shared


def extract_mame_version(filename):
    version = filename.replace("MAME ", "").replace(".xml.bz2", "")
    version = re.sub(r"\D", "", version)
    return float(version) if version else 0


SOURCE_DATS = {
    "mame": shared.MAME_DATS,
}

SORT_FUNCS = {
    "mame": extract_mame_version,
}

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="filepath", help="Target File", metavar="PATH")
    parser.add_option("-d", "--dattype", dest="dat_type", help="Dat type", metavar="DATTYPE")
    parser.add_option("-s", "--start", dest="start_index", type="int", help="Start DAT")
    parser.add_option("-e", "--end", dest="end_index", type="int", help="End DAT")

    (options, args) = parser.parse_args()
    dat_type = options.dat_type if options.dat_type else "mame"
    sorted_dats = sorted(SOURCE_DATS[dat_type], key=SORT_FUNCS[dat_type])
    filepath = options.filepath if options.filepath else "./arcade_db_build/arcade.db"
    start = options.start_index if options.start_index else 0
    end = options.end_index if options.end_index else len(sorted_dats)
    session = create_db.get_session(filepath)
    source_dats = sorted_dats[start:end]
    create_db.process_dats(session, source_dats)
    session.close()
