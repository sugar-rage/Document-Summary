import os
from datetime import UTC, datetime, timedelta

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-test-jwt-secret-32")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("GEMINI_MODEL", "gemini-2.5-flash")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.core.config import settings

_test_private_key = ec.generate_private_key(ec.SECP256R1())
_test_public_key = _test_private_key.public_key()


class MockSigningKey:
    def __init__(self, key):
        self.key = key


class MockJWKClient:
    def __init__(self, *args, **kwargs):
        pass

    def get_signing_key_from_jwt(self, token: str):
        return MockSigningKey(_test_public_key)


def make_token(
    sub: str = "11111111-1111-1111-1111-111111111111",
    expired: bool = False,
    iss: str = "https://example.supabase.co/auth/v1",
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "role": "authenticated",
        "iss": iss,
        "iat": int(now.timestamp()),
        "exp": int((now - timedelta(hours=1) if expired else now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, _test_private_key, algorithm="ES256", headers={"kid": "test-kid"})


def api_client() -> TestClient:
    from app.main import app

    return TestClient(app)

