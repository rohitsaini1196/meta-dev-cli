import json

import pytest

from meta_cli.config.config_manager import Config, ConfigError, ConfigManager


def test_load_returns_empty_config_when_file_missing(tmp_path):
    cm = ConfigManager(config_path=tmp_path / ".meta-cli" / "config.json")
    config = cm.load()
    assert config.access_token is None
    assert config.default_app_id is None


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    cm = ConfigManager(config_path=path)
    config = Config(access_token="EAAG_TEST", default_app_id="123")
    cm.save(config)
    loaded = cm.load()
    assert loaded.access_token == "EAAG_TEST"
    assert loaded.default_app_id == "123"


def test_save_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "config.json"
    cm = ConfigManager(config_path=path)
    cm.save(Config(access_token="tok"))
    assert path.exists()


def test_update_merges_fields(tmp_path):
    path = tmp_path / "config.json"
    cm = ConfigManager(config_path=path)
    cm.save(Config(access_token="OLD_TOKEN", default_app_id="111"))
    updated = cm.update(access_token="NEW_TOKEN")
    assert updated.access_token == "NEW_TOKEN"
    assert updated.default_app_id == "111"


def test_require_token_raises_when_missing(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "config.json")
    with pytest.raises(ConfigError) as exc_info:
        cm.require_token()
    assert "meta login" in exc_info.value.hint


def test_require_token_returns_token(tmp_path):
    path = tmp_path / "config.json"
    cm = ConfigManager(config_path=path)
    cm.save(Config(access_token="EAAG_123"))
    assert cm.require_token() == "EAAG_123"


def test_require_app_id_raises_when_missing(tmp_path):
    path = tmp_path / "config.json"
    cm = ConfigManager(config_path=path)
    cm.save(Config(access_token="tok"))
    with pytest.raises(ConfigError) as exc_info:
        cm.require_app_id()
    assert "meta apps use" in exc_info.value.hint


def test_require_waba_id_raises_when_missing(tmp_path):
    path = tmp_path / "config.json"
    cm = ConfigManager(config_path=path)
    cm.save(Config(access_token="tok"))
    with pytest.raises(ConfigError):
        cm.require_waba_id()


def test_config_file_permissions(tmp_path):
    import stat
    path = tmp_path / "config.json"
    cm = ConfigManager(config_path=path)
    cm.save(Config(access_token="tok"))
    mode = path.stat().st_mode
    # Only owner should have read/write (no group/other bits)
    assert not (mode & stat.S_IRGRP)
    assert not (mode & stat.S_IROTH)
