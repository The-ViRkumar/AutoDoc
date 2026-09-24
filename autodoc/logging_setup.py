import logging
from logging.handlers import RotatingFileHandler

from .platform_utils import log_path


def configure_logging(level=logging.INFO) -> None:
    root = logging.getLogger("autodoc")
    if root.handlers:
        return  # already configured (e.g. re-entrant import)
    root.setLevel(level)

    file_handler = RotatingFileHandler(log_path(), maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(file_handler)
