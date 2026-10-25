
import json

from clickpilot import config


def test_load_config_returns_defaults_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")

    result = config.load_config()

    assert result == config.DEFAULT_CONFIG
    assert result is not config.DEFAULT_CONFIG


def test_load_config_merges_saved_values(tmp_path, monkeypatch):
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
    assert result["hotkey"] == config.DEFAULT_CONFIG["hotkey"]


def test_load_config_handles_invalid_json(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text("{invalid json", encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    assert config.load_config() == config.DEFAULT_CONFIG


def test_save_config_writes_json(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    settings = {**config.DEFAULT_CONFIG, "interval": 1.5}
    config.save_config(settings)

    assert json.loads(config_file.read_text(encoding="utf-8")) == settings
