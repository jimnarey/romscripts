import json
# import re
# import os
from optparse import OptionParser
from romrename.rename_root import RenameRoot


def get_rename_prefs(json_path):
    with open(json_path, 'r') as json_file:
        return json.load(json_file)


def write_summary(summary_file_path, summary_lines):
    with open(summary_file_path, 'w') as summary_file:
        summary_file.writelines(summary_lines)


def process(rename_prefs):
    root = RenameRoot(rename_prefs['rootDir'], rename_prefs['maxFileNameLength'])
    root.process_actions(rename_prefs)
    if rename_prefs['writeSummary']:
        write_summary(rename_prefs['summaryFilePath'], root.get_changes(
        ) + ['\n\n\n\n'] + root.get_truncated_files() + ['\n\n\n\n'] + root.get_long_files())


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option('-j', '--json', dest='json_rename_prefs',
                      help='Specify input json file')
    (options, args) = parser.parse_args()
    if options.json_rename_prefs is None:
        print(parser.usage)
        exit(0)

    rename_prefs = get_rename_prefs(options.json_rename_prefs)

    process(rename_prefs)
