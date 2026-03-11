import logging


def setup_logger():
    logging.basicConfig(
        level=logging.DEBUG,     # see everything
        # level=logging.INFO,    # only high-level progress
        # level=logging.WARNING, # silent unless something goes wrong
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
