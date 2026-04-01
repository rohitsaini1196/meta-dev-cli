import json

import responses as responses_mock

from meta_cli.cli import app

BASE = "https://graph.facebook.com/v20.0"


@responses_mock.activate
def test_phone_numbers(runner, seeded_config):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/987654321/phone_numbers",
        json={"data": [
            {"id": "111222333", "display_phone_number": "+14155552671",
             "verified_name": "Test Business", "status": "CONNECTED"},
        ]},
    )
    result = runner.invoke(app, ["wa", "phone-numbers"])
    assert result.exit_code == 0
    assert "+14155552671" in result.output


@responses_mock.activate
def test_send_message(runner, seeded_config):
    responses_mock.add(
        responses_mock.POST,
        f"{BASE}/111222333/messages",
        json={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "14155552671", "wa_id": "14155552671"}],
            "messages": [{"id": "wamid.ABC123"}],
        },
    )
    result = runner.invoke(app, ["wa", "send", "+14155552671", "Hello world"])
    assert result.exit_code == 0
    assert "wamid.ABC123" in result.output


@responses_mock.activate
def test_send_message_json(runner, seeded_config):
    responses_mock.add(
        responses_mock.POST,
        f"{BASE}/111222333/messages",
        json={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "14155552671", "wa_id": "14155552671"}],
            "messages": [{"id": "wamid.XYZ"}],
        },
    )
    result = runner.invoke(app, ["--json", "wa", "send", "+14155552671", "Hi"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["message_id"] == "wamid.XYZ"
    assert data["status"] == "sent"


def test_send_invalid_phone(runner, seeded_config):
    result = runner.invoke(app, ["wa", "send", "not-a-phone", "Hello"])
    assert result.exit_code != 0


@responses_mock.activate
def test_send_test(runner, seeded_config):
    responses_mock.add(
        responses_mock.POST,
        f"{BASE}/111222333/messages",
        json={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "14155552671", "wa_id": "14155552671"}],
            "messages": [{"id": "wamid.TEST"}],
        },
    )
    result = runner.invoke(app, ["wa", "send-test", "+14155552671"])
    assert result.exit_code == 0
    assert "hello_world" in result.output.lower() or "wamid.TEST" in result.output


def test_send_no_waba_config(runner, tmp_config):
    import json as j
    (tmp_config / "config.json").write_text(j.dumps({"access_token": "tok"}))
    result = runner.invoke(app, ["wa", "phone-numbers"])
    assert result.exit_code == 1
    assert "meta wa setup" in result.output
