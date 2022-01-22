"""Common utils for all social media handlers."""
import logging
import logging.config
from pathlib import Path

from config import settings


def get_logger(name: str) -> logging.Logger:
    """Create logger."""
    Path(settings.logging.handlers.file.filename).parent.mkdir(exist_ok=True)
    logging.config.dictConfig(settings.logging.to_dict())
    logger = logging.getLogger(name)
    return logger


LOGGER = get_logger("utils")


if __name__ == "__main__":
    LOGGER.info("Hello INFO")
    LOGGER.warning("Hello WARNING")
    LOGGER.error("Hello ERROR")
