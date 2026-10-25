
import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / "AppData" / "Local" / "ClickPilot"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "x": None,
    "y": None,
    "interval": 5.0,
    "click_type": "left",
    "hotkey": "F6",
}


def load_config() -> dict[str, Any]:
    """Загружает настройки или возвращает значения по умолчанию."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            saved = json.load(file)

        if not isinstance(saved, dict):
            raise ValueError("Неверный формат настроек")

        config = DEFAULT_CONFIG.copy()
        config.update(saved)
        return config

    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Сохраняет настройки на компьютере пользователя."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
