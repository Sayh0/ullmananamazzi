"""위젯 전역 로거 설정."""
import logging
import logging.handlers
from pathlib import Path

_LOG_PATH = Path(__file__).parent / "widget.log"
_FMT = "%(asctime)s | %(levelname)-7s | %(name)-8s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup() -> None:
    root = logging.getLogger("widget")
    if root.handlers:
        return
    root.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        _LOG_PATH, maxBytes=512 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(handler)


def get(name: str) -> logging.Logger:
    return logging.getLogger(f"widget.{name}")
