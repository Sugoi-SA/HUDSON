import pytest
from fastapi.testclient import TestClient

from app.config import API_KEY
from app.main import app

client = TestClient(app)


def test_health_does_not_require_api_key():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-API-Key": "chave-completamente-errada"},
    ],
)
def test_search_rejects_missing_or_wrong_api_key(headers):
    resp = client.get("/search", params={"q": "concreto"}, headers=headers)
    assert resp.status_code == 401


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-API-Key": "chave-completamente-errada"},
    ],
)
def test_items_rejects_missing_or_wrong_api_key(headers):
    resp = client.get("/items/qualquer-cota", headers=headers)
    assert resp.status_code == 401


def test_search_with_valid_api_key_returns_200():
    resp = client.get("/search", params={"q": "concreto"}, headers={"X-API-Key": API_KEY})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "concreto"
    assert "results" in body


def test_item_not_found_returns_404():
    resp = client.get("/items/cota-que-nao-existe-de-verdade", headers={"X-API-Key": API_KEY})
    assert resp.status_code == 404
