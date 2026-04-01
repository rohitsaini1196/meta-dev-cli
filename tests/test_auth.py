import json

import responses as responses_mock

from meta_cli.cli import app

BASE = "https://graph.facebook.com/v20.0"


@responses_mock.activate
def test_login_success(runner, tmp_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me",
        json={"id": "123456", "name": "Test User"},
    )
    result = runner.invoke(app, ["login", "--token", "EAAG_TEST"])
    assert result.exit_code == 0
    assert "Test User" in result.output

    config_file = tmp_config / "config.json"
    assert config_file.exists()
    stored = json.loads(config_file.read_text())
    assert stored["access_token"] == "EAAG_TEST"


@responses_mock.activate
def test_login_invalid_token(runner, tmp_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me",
        json={"error": {"message": "Invalid OAuth token", "type": "OAuthException", "code": 190}},
        status=400,
    )
    result = runner.invoke(app, ["login", "--token", "INVALID"])
    assert result.exit_code == 1
    assert "Invalid" in result.output
