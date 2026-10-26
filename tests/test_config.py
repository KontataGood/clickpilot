
import json

from clickpilot import config


def test_load_config_returns_defaults_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")

    result = config.load_config()

    assert all(
        result[key] == value
        for key, value in config.DEFAULT_CONFIG.items()
    )
    assert result is not config.DEFAULT_CONFIG
    assert result["active_profile"] == config.DEFAULT_PROFILE_NAME
    assert result["profiles"][config.DEFAULT_PROFILE_NAME] == config.DEFAULT_CONFIG


def test_load_config_handles_invalid_json(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text("{invalid json", encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    result = config.load_config()

    assert all(
        result[key] == value
        for key, value in config.DEFAULT_CONFIG.items()
    )
    assert result["active_profile"] == config.DEFAULT_PROFILE_NAME
    assert (
        result["profiles"][config.DEFAULT_PROFILE_NAME]
        == config.DEFAULT_CONFIG
    )


def test_save_config_writes_json(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    settings = {**config.DEFAULT_CONFIG, "interval": 1.5}
    config.save_config(settings)

    assert json.loads(config_file.read_text(encoding="utf-8")) == settings


def test_load_config_migrates_legacy_settings(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"interval": 2.0, "click_type": "right"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    result = config.load_config()

    assert result["interval"] == 2.0
    assert result["click_type"] == "right"
    assert result["active_profile"] == config.DEFAULT_PROFILE_NAME
    assert result["profiles"][config.DEFAULT_PROFILE_NAME]["interval"] == 2.0


def test_save_profile_creates_profile():
    settings = {
        **config.DEFAULT_CONFIG,
        "interval": 1.5,
        "profiles": {},
        "active_profile": config.DEFAULT_PROFILE_NAME,
    }

    result = config.save_profile(settings, "Игры")

    assert result["active_profile"] == "Игры"
    assert result["profiles"]["Игры"]["interval"] == 1.5


def test_activate_profile_restores_settings():
    settings = {
        **config.DEFAULT_CONFIG,
        "interval": 1.0,
        "profiles": {
            "Работа": {**config.DEFAULT_CONFIG, "interval": 3.0},
            "Игры": {**config.DEFAULT_CONFIG, "interval": 0.5},
        },
        "active_profile": "Работа",
    }

    result = config.activate_profile(settings, "Игры")

    assert result["active_profile"] == "Игры"
    assert result["interval"] == 0.5


def test_delete_profile_preserves_another_profile():
    settings = {
        **config.DEFAULT_CONFIG,
        "profiles": {
            "Работа": {**config.DEFAULT_CONFIG, "interval": 3.0},
            "Игры": {**config.DEFAULT_CONFIG, "interval": 0.5},
        },
        "active_profile": "Игры",
    }

    result = config.delete_profile(settings, "Игры")

    assert "Игры" not in result["profiles"]
    assert result["active_profile"] == "Работа"
    assert result["interval"] == 3.0

