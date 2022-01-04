import logging
import logging.config
from pathlib import Path

from config import settings


def _get_logger(name: str) -> logging.Logger:
    Path(settings.logging.handlers.file.filename).parent.mkdir(exist_ok=True)
    logging.config.dictConfig(settings.logging.to_dict())
    logger = logging.getLogger(name)
    return logger


LOGGER = _get_logger("utils")


def _get_output_path(fname: str) -> Path:
    output_dir = Path.cwd() / settings.output_directory
    output_dir.mkdir(exist_ok=True)

    path = output_dir / fname
    LOGGER.info(f"Output path: {path}")
    return path


if __name__ == "__main__":
    LOGGER.info("Hello INFO")
    LOGGER.warning("Hello WARNING")
    LOGGER.error("Hello ERROR")

    LOGGER.info(settings.to_dict())
