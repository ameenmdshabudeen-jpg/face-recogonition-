import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(app) -> None:
    log_file = Path(app.config["LOG_FILE"])
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    if not any(
        getattr(handler, "baseFilename", None) == str(log_file)
        for handler in app.logger.handlers
    ):
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False
