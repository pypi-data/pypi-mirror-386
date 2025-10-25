import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_sbc import NAME
from bluer_sbc.parts.db import db_of_parts
from bluer_sbc.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="adjust",
)
parser.add_argument(
    "--dryrun",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--generate_grid",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--verbose",
    type=int,
    default=0,
    help="0 | 1",
)
args = parser.parse_args()

success = False
if args.task == "adjust":
    success = db_of_parts.adjust(
        generate_grid=args.generate_grid == 1,
        dryrun=args.dryrun == 1,
        verbose=args.verbose == 1,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
