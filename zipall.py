import os
from optparse import OptionParser
from zipfile import ZipFile


def get_file_paths(root_dir):
    file_paths = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def zip_file(file_path):
    stem, ext = os.path.splitext(file_path)
    with ZipFile('{0}{1}'.format(stem, '.zip'), 'w') as zip:
        zip.write(file_path)
    os.remove(file_path)
    # print(stem)
    # print(ext)


def zip_all(file_paths):
    for file_path in file_paths:
        zip_file(file_path)


parser = OptionParser()
parser.add_option('-d', '--dir', dest='root_dir', help='Specify root dir')
(options, args) = parser.parse_args()
if options.root_dir is None:
    print(parser.usage)
    exit(0)

file_paths = get_file_paths(options.root_dir)
zip_all(file_paths)
