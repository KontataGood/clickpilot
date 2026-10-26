import json

from clickpilot.config import load_config, save_config

from copy import deepcopy

from clickpilot.config import (
    DEFAULT_CONFIG,
    DEFAULT_PROFILE_NAME,
    activate_profile,
    save_profile,
)


def test_default_hotkeys_exist():
    assert DEFAULT_CONFIG["point_hotkey"] == "F5"
    assert DEFAULT_CONFIG["toggle_hotkey"] == "F6"


def test_hotkeys_are_saved_in_profile():
    config = deepcopy(DEFAULT_CONFIG)
    config["point_hotkey"] = "F8"
    config["toggle_hotkey"] = "F9"

    result = save_profile(config, DEFAULT_PROFILE_NAME)

    profile = result["profiles"][DEFAULT_PROFILE_NAME]
    assert profile["point_hotkey"] == "F8"
    assert profile["toggle_hotkey"] == "F9"


def test_hotkeys_are_restored_when_profile_is_activated():
    config = deepcopy(DEFAULT_CONFIG)
    config["profiles"] = {
        "По умолчанию": {
            **deepcopy(DEFAULT_CONFIG),
            "point_hotkey": "F5",
            "toggle_hotkey": "F6",
        },
        "Игры": {
            **deepcopy(DEFAULT_CONFIG),
            "point_hotkey": "F8",
            "toggle_hotkey": "F9",
        },
    }
    config["active_profile"] = "По умолчанию"

    result = activate_profile(config, "Игры")

    assert result["point_hotkey"] == "F8"
    assert result["toggle_hotkey"] == "F9"
    assert result["active_profile"] == "Игры"


def test_hotkeys_survive_config_reload(tmp_path, monkeypatch):
    import clickpilot.config as config_module

    config_file = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
    monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path)

    config = deepcopy(DEFAULT_CONFIG)
    config["point_hotkey"] = "F8"
    config["toggle_hotkey"] = "F9"

    save_config(config)
    loaded = load_config()

    assert loaded["point_hotkey"] == "F8"
    assert loaded["toggle_hotkey"] == "F9"


def test_saved_hotkeys_are_present_in_json(tmp_path, monkeypatch):
    import clickpilot.config as config_module

    config_file = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
    monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path)

    config = deepcopy(DEFAULT_CONFIG)
    config["point_hotkey"] = "F10"
    config["toggle_hotkey"] = "F11"

    save_config(config)

    saved_data = json.loads(config_file.read_text(encoding="utf-8"))
    assert saved_data["point_hotkey"] == "F10"
    assert saved_data["toggle_hotkey"] == "F11"

from clickpilot.hotkeys import hotkeys_conflict


def test_different_hotkeys_do_not_conflict():
    assert hotkeys_conflict("F5", "F6") is False


def test_same_hotkeys_conflict():
    assert hotkeys_conflict("F5", "F5") is True


def test_custom_hotkeys_do_not_conflict():
    assert hotkeys_conflict("F8", "F11") is False
