#!/usr/bin/env python3

from optparse import OptionParser
from arcade_db import create_db
from arcade_db.shared import sources


def print_job_summary(start, end, filepath, source_dats):
    print(f"Start index: {start}")
    print(f"End index: {end}")
    print(f"Filepath: {filepath}")
    print(f"Source dats length: {len(source_dats)}")
    print(f"First DAT: {source_dats[0]}")
    print(f"Last DAT: {source_dats[-1]}")


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-p", "--path", dest="filepath", help="Target File", metavar="PATH")
    parser.add_option("-d", "--dattype", dest="dat_type", help="Dat type", metavar="DATTYPE")
    parser.add_option("-s", "--start", dest="start_index", type="int", help="Start DAT")
    parser.add_option("-e", "--end", dest="end_index", type="int", help="End DAT")

    (options, args) = parser.parse_args()
    dat_type = options.dat_type if options.dat_type else "mame"
    sorted_dats = sources.BUILD_DATS[dat_type]
    filepath = options.filepath if options.filepath else "./arcade_db_build/arcade.db"
    start = options.start_index if options.start_index else 0
    end = options.end_index if options.end_index else len(sorted_dats)
    # session = db.get_session(filepath)
    source_dats = sorted_dats[start:end]
    print_job_summary(start, end, filepath, source_dats)
    create_db.process_dats(source_dats)
    # session.close()
