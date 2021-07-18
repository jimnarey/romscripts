import os

root_dir = '/media/jimnarey/HDD_Data_B/Xbox/HDD - Validated/Emulators/'
max_length = 42

def get_long_files(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if len(file) > max_length:
                print(os.path.join(root, file))

get_long_files(root_dir)