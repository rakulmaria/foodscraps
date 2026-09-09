import logging


def setup_logger():
    logging.basicConfig(
        # filename='example.log', # enables writing logs to a file
        # encoding='utf-8',       # remember encoding
        # level=logging.DEBUG,     # see everything
        level=logging.INFO,    # only high-level progress
        # level=logging.WARNING, # silent unless something goes wrong
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
