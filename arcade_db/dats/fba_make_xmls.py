#!/usr/bin/env python3

import os
import subprocess

print(os.getcwd())

dirs = os.listdir(os.getcwd())
dirs.reverse()

for dir in dirs:
    with open(f"{dir}.xml", "w") as f:
        subprocess.run(["wine", os.path.join(dir, "fba.exe"), "-listinfo"], stdout=f)
