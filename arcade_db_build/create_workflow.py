#!/usr/bin/env python3

import os
import math
import argparse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

from shared import shared

parser = argparse.ArgumentParser()
parser.add_argument("divisor", type=int, help="Divisor")
parser.add_argument("dat_type", type=str, help="Dat Type")
args = parser.parse_args()

total_dats = len(shared.SORTED_DATS[args.dat_type])

total_jobs = math.ceil(total_dats / args.divisor)

env = Environment(loader=FileSystemLoader("workflow_templates"))
template = env.get_template("build_db_template.yml")

jobs = []
for i in range(total_jobs):
    start = i * args.divisor
    if (end := start + args.divisor) > total_dats:
        end = None
    jobs.append((start, end))

date_time = datetime.now().strftime("%Y%m%d%H%M%S")
rendered_template = template.render(total_jobs=total_jobs, jobs=jobs, dat_type=args.dat_type, date_time=date_time)

output_filename = os.path.join("..", ".github", "workflows", f"build_db_{total_jobs}_{args.dat_type}.yml")
with open(output_filename, "w") as f:
    f.write(rendered_template)
