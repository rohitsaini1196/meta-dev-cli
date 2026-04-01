import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from meta_cli.cli import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Redirect config to a temp directory."""
    config_dir = tmp_path / ".meta-cli"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    monkeypatch.setattr("meta_cli.config.config_manager.CONFIG_DIR", config_dir)
    monkeypatch.setattr("meta_cli.config.config_manager.CONFIG_FILE", config_file)
    return config_dir


@pytest.fixture
def seeded_config(tmp_config):
    """Pre-populate config with a valid token and app_id."""
    config_file = tmp_config / "config.json"
    config_file.write_text(
        json.dumps({
            "access_token": "EAAG_TEST_TOKEN",
            "default_app_id": "123456789",
            "waba_id": "987654321",
            "phone_number_id": "111222333",
        })
    )
    return tmp_config
