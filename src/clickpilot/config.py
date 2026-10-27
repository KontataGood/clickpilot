
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / "AppData" / "Local" / "ClickPilot"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_PROFILE_NAME = "По умолчанию"

DEFAULT_CONFIG: dict[str, Any] = {
    "x": None,
    "y": None,
    "interval": 5.0,
    "click_type": "left",
    "hotkey": "F6",
    "interval_unit": "s",
    "point_hotkey": "F5",
    "toggle_hotkey": "F6",
}


DEFAULT_PROFILES: dict[str, dict[str, Any]] = {
    DEFAULT_PROFILE_NAME: deepcopy(DEFAULT_CONFIG),
}


def load_config() -> dict[str, Any]:
    """Загружает настройки приложения."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        return {
            **deepcopy(DEFAULT_CONFIG),
            "profiles": deepcopy(DEFAULT_PROFILES),
            "autostart": False,
            "active_profile": DEFAULT_PROFILE_NAME,
        }

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            saved = json.load(file)

        if not isinstance(saved, dict):
            raise ValueError("Неверный формат настроек")

        # Поддерживаем старый формат config.json.
        config = deepcopy(DEFAULT_CONFIG)
        config.update({
            key: value
            for key, value in saved.items()
            if key in DEFAULT_CONFIG
        })

        profiles = saved.get("profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}

        valid_profiles: dict[str, dict[str, Any]] = {}

        for name, profile in profiles.items():
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(profile, dict):
                continue

            valid_profile = deepcopy(DEFAULT_CONFIG)
            valid_profile.update({
                key: value
                for key, value in profile.items()
                if key in DEFAULT_CONFIG
            })
            valid_profiles[name] = valid_profile

        if not valid_profiles:
            valid_profiles = deepcopy(DEFAULT_PROFILES)

        active_profile = saved.get("active_profile", DEFAULT_PROFILE_NAME)
        if active_profile not in valid_profiles:
            active_profile = next(iter(valid_profiles))

        # При миграции старого файла переносим настройки в профиль.
        if "profiles" not in saved:
            valid_profiles[DEFAULT_PROFILE_NAME] = deepcopy(config)
            active_profile = DEFAULT_PROFILE_NAME

        active_settings = valid_profiles[active_profile]
        config.update(active_settings)
        config["autostart"] = bool(saved.get("autostart", False))
        config["profiles"] = valid_profiles
        config["active_profile"] = active_profile

        return config

    except (OSError, json.JSONDecodeError, ValueError):
        return {
            **deepcopy(DEFAULT_CONFIG),
            "profiles": deepcopy(DEFAULT_PROFILES),
            "active_profile": DEFAULT_PROFILE_NAME,
            "autostart": False,
        }


def save_config(config: dict[str, Any]) -> None:
    """Сохраняет настройки приложения."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)


def save_profile(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """Сохраняет текущие параметры в выбранный профиль."""
    name = profile_name.strip()
    if not name:
        raise ValueError("Название профиля не может быть пустым")

    updated = deepcopy(config)
    profiles = updated.setdefault("profiles", {})
    profiles[name] = {
        key: updated.get(key, deepcopy(value))
        for key, value in DEFAULT_CONFIG.items()
    }
    updated["active_profile"] = name
    return updated


def activate_profile(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """Переключает конфигурацию на существующий профиль."""
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"Профиль «{profile_name}» не найден")

    updated = deepcopy(config)
    updated.update(deepcopy(profiles[profile_name]))
    updated["active_profile"] = profile_name
    return updated


def delete_profile(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """Удаляет профиль, сохраняя хотя бы один профиль."""
    profiles = deepcopy(config.get("profiles", {}))

    if profile_name not in profiles:
        raise ValueError(f"Профиль «{profile_name}» не найден")

    if len(profiles) <= 1:
        raise ValueError("Нельзя удалить последний профиль")

    del profiles[profile_name]

    updated = deepcopy(config)
    updated["profiles"] = profiles

    if updated.get("active_profile") == profile_name:
        new_active = next(iter(profiles))
        updated.update(deepcopy(profiles[new_active]))
        updated["active_profile"] = new_active

    return updated
