import json

import responses as responses_mock

from meta_cli.cli import app

BASE = "https://graph.facebook.com/v20.0"


@responses_mock.activate
def test_apps_list(runner, seeded_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me/apps",
        json={"data": [
            {"id": "111", "name": "my-app", "category": "OTHER"},
            {"id": "222", "name": "chatbot", "category": "BUSINESS"},
        ]},
    )
    result = runner.invoke(app, ["apps", "list"])
    assert result.exit_code == 0
    assert "my-app" in result.output
    assert "chatbot" in result.output


@responses_mock.activate
def test_apps_list_json(runner, seeded_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me/apps",
        json={"data": [{"id": "111", "name": "my-app"}]},
    )
    result = runner.invoke(app, ["--json", "apps", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["data"][0]["id"] == "111"


@responses_mock.activate
def test_apps_use(runner, seeded_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/123",
        json={"id": "123", "name": "new-app"},
    )
    result = runner.invoke(app, ["apps", "use", "123"])
    assert result.exit_code == 0
    assert "new-app" in result.output


@responses_mock.activate
def test_apps_use_not_found(runner, seeded_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/999",
        json={"error": {"message": "No node", "type": "GraphMethodException", "code": 100}},
        status=404,
    )
    result = runner.invoke(app, ["apps", "use", "999"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_apps_list_no_token(runner, tmp_config):
    result = runner.invoke(app, ["apps", "list"])
    assert result.exit_code == 1
    assert "meta login" in result.output


@responses_mock.activate
def test_apps_list_missing_permission(runner, seeded_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me/apps",
        json={"error": {"message": "(#100) Tried accessing nonexisting field (apps)", "type": "OAuthException", "code": 100}},
        status=400,
    )
    result = runner.invoke(app, ["apps", "list"])
    assert result.exit_code == 1
    assert "developers.facebook.com/apps" in result.output
    assert "meta apps use" in result.output
