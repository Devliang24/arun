from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

try:
    from rich.logging import RichHandler  # type: ignore
    _HAS_RICH = True
except Exception:  # pragma: no cover
    RichHandler = None  # type: ignore
    _HAS_RICH = False


def setup_logging(level: str = "INFO", *, log_file: Optional[str] = None) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)

    # Clear existing handlers on root
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    handlers: list[logging.Handler] = []
    console_handler: Optional[logging.Handler] = None
    if _HAS_RICH:
        console_handler = RichHandler(rich_tracebacks=True, show_path=False)
    else:
        console_handler = logging.StreamHandler()
    handlers.append(console_handler)

    if log_file:
        p = Path(log_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(p, encoding="utf-8")
        handlers.append(fh)

    # Console uses concise message-only format (RichHandler renders time/level)
    fmt_console = "%(message)s" if _HAS_RICH else "%(asctime)s | %(levelname)-8s | %(message)s"
    fmt_file = "%(asctime)s | %(levelname)-8s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(level=lvl, handlers=handlers, format=fmt_console, datefmt=datefmt)

    # Ensure file handler uses its own formatter
    for h in handlers:
        if isinstance(h, logging.FileHandler):
            h.setFormatter(logging.Formatter(fmt_file, datefmt))
        elif h is console_handler:
            h.setFormatter(logging.Formatter(fmt_console, datefmt))

    # Quiet overly verbose libraries unless in DEBUG (httpx level is set in CLI)
    if lvl > logging.DEBUG:
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "apirunner")
