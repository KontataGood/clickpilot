
import logging
from logging.handlers import RotatingFileHandler

from .config import CONFIG_DIR


LOG_FILE = CONFIG_DIR / "activity.log"


class ActivityLogger:
    """Сохраняет историю действий ClickPilot в файл."""

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("clickpilot.activity")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            self.logger.addHandler(handler)

    def log(self, message: str) -> None:
        self.logger.info(message)

    def read_recent(self, limit: int = 100) -> list[str]:
        """Возвращает последние записи журнала."""
        if not LOG_FILE.exists():
            return []

        try:
            with LOG_FILE.open("r", encoding="utf-8") as file:
                lines = file.readlines()
            return [line.rstrip("\n") for line in lines[-limit:]]
        except OSError:
            return []
