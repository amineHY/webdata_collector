import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    return logger


logger = setup_logging()
