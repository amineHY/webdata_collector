import logging


def setup_logging():
    """
    Sets up a basic logging configuration and returns a logger instance.

    The logging level is set to INFO. The format string is customized to include
    timestamp, log level, filename, function name, and the actual log message.

    :return: A logger instance for the current module.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
    )
    return logging.getLogger(__name__)


logger = setup_logging()
