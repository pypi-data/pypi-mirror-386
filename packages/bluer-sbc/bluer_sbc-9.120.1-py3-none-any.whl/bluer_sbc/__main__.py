from blueness.argparse.generic import main

from bluer_sbc import NAME, VERSION, DESCRIPTION, ICON
from bluer_sbc.README.build import build
from bluer_sbc.logger import logger

main(
    ICON=ICON,
    NAME=NAME,
    DESCRIPTION=DESCRIPTION,
    VERSION=VERSION,
    main_filename=__file__,
    tasks={
        "build_README": lambda _: build(),
    },
    logger=logger,
)
