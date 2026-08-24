from unittest.mock import patch

from tests.conftest import MockJWKClient, api_client, make_token


def test_health_public():
    client = api_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_documents_require_auth():
    client = api_client()
    response = client.get("/api/documents")
    assert response.status_code == 401


def test_invalid_token_rejected():
    client = api_client()
    response = client.get(
        "/api/documents",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


@patch("app.core.auth.get_jwks_client", return_value=MockJWKClient())
def test_expired_token_rejected(_mock_jwks):
    client = api_client()
    token = make_token(expired=True)
    response = client.get(
        "/api/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@patch("app.core.auth.get_jwks_client", return_value=MockJWKClient())
def test_invalid_issuer_rejected(_mock_jwks):
    client = api_client()
    token = make_token(iss="https://malicious.issuer.com/auth/v1")
    response = client.get(
        "/api/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_summary_requires_auth():
    client = api_client()
    response = client.post(
        "/api/documents/00000000-0000-0000-0000-000000000000/summaries",
        json={"mode": "short"},
    )
    assert response.status_code == 401


def test_document_file_requires_auth():
    client = api_client()
    response = client.get(
        "/api/documents/00000000-0000-0000-0000-000000000000/file",
    )
    assert response.status_code == 401


