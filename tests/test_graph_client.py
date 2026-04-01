import pytest
import responses as responses_mock

from meta_cli.api.graph_client import (
    AuthError,
    GraphAPIError,
    GraphClient,
    NotFoundError,
    RateLimitError,
)

BASE = "https://graph.facebook.com/v20.0"
BASE_URL = BASE


@pytest.fixture
def client():
    return GraphClient(access_token="EAAG_TEST", max_retries=2)


@responses_mock.activate
def test_get_success(client):
    responses_mock.add(responses_mock.GET, f"{BASE}/me", json={"id": "123", "name": "Test"})
    result = client.get("/me")
    assert result["id"] == "123"


@responses_mock.activate
def test_auth_error_raises(client):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me",
        json={"error": {"message": "Invalid token", "type": "OAuthException", "code": 190}},
        status=400,
    )
    with pytest.raises(AuthError) as exc_info:
        client.get("/me")
    assert exc_info.value.code == 190


@responses_mock.activate
def test_not_found_raises(client):
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/99999",
        json={"error": {"message": "No node", "type": "GraphMethodException", "code": 100}},
        status=404,
    )
    with pytest.raises(NotFoundError):
        client.get("/99999")


@responses_mock.activate
def test_rate_limit_retries_and_succeeds():
    c = GraphClient(access_token="tok", max_retries=3)
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me/apps",
        json={"error": {"message": "Rate limit", "type": "OAuthException", "code": 4}},
        status=429,
        headers={"Retry-After": "0"},
    )
    responses_mock.add(
        responses_mock.GET,
        f"{BASE}/me/apps",
        json={"data": []},
    )
    result = c.get("/me/apps")
    assert result == {"data": []}
    assert len(responses_mock.calls) == 2


@responses_mock.activate
def test_rate_limit_exhausts_retries():
    c = GraphClient(access_token="tok", max_retries=2)
    for _ in range(2):
        responses_mock.add(
            responses_mock.GET,
            f"{BASE}/me",
            json={"error": {"message": "Rate limit", "type": "OAuthException", "code": 17}},
            status=429,
            headers={"Retry-After": "0"},
        )
    with pytest.raises(RateLimitError):
        c.get("/me")


@responses_mock.activate
def test_post_success(client):
    responses_mock.add(
        responses_mock.POST,
        f"{BASE}/111/messages",
        json={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "14155552671", "wa_id": "14155552671"}],
            "messages": [{"id": "wamid.XXX"}],
        },
    )
    result = client.post("/111/messages", json={"to": "14155552671"})
    assert result["messaging_product"] == "whatsapp"
