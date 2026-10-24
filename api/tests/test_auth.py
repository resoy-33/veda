"""Auth tests: password hashing, JWT, role guards (no network, no DB)."""
from __future__ import annotations

import time

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import (
    JWT_ALG,
    JWT_SECRET,
    create_access_token,
    decode_token,
    hash_password,
    require_roles,
    verify_password,
)

SEEDED_ISSUER_HASH = (
    "pbkdf2_sha256$260000$6973737565722d73616c742d32303236$"
    "16126b7cded7ba25cd6cc5dd03d6b73dca5b29c8b6b7e1ff4bfcd0e55a7de57a"
)


def _user(role: str = "admin") -> dict:
    return {
        "id": "11111111-1111-4111-8111-111111111111",
        "email": "admin@veda.tn",
        "role": role,
        "hedera_account_id": "0.0.11060814",
        "display_name": "Test User",
    }


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/admin")
    def admin(user: dict = Depends(require_roles("admin"))):
        return {"role": user["role"]}

    @app.get("/me")
    def me(user: dict = Depends(require_roles("issuer", "broker", "verifier", "admin"))):
        return user

    return TestClient(app)


def test_demo_password_matches_seeded_hash():
    assert verify_password("demo1234", SEEDED_ISSUER_HASH)


def test_hash_password_roundtrip_and_salt():
    first = hash_password("new-secret")
    second = hash_password("new-secret")
    assert first != second
    assert verify_password("new-secret", first)
    assert not verify_password("wrong", first)


def test_wrong_or_malformed_password_is_rejected():
    assert not verify_password("wrong", SEEDED_ISSUER_HASH)
    assert not verify_password("demo1234", "not-a-hash")
    assert not verify_password("demo1234", "sha256$1$aa$bb")


def test_token_roundtrip():
    payload = decode_token(create_access_token(_user("broker")))
    assert payload["sub"] == _user()["id"]
    assert payload["role"] == "broker"
    assert payload["display_name"] == "Test User"


def test_expired_token_is_rejected():
    token = jwt.encode(
        {"sub": "u", "exp": int(time.time()) - 10},
        JWT_SECRET,
        algorithm=JWT_ALG,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_missing_token_is_401():
    response = _client().get("/me")
    assert response.status_code == 401


def test_invalid_token_is_401():
    response = _client().get("/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


def test_wrong_role_is_403():
    headers = {"Authorization": f"Bearer {create_access_token(_user('broker'))}"}
    assert _client().get("/admin", headers=headers).status_code == 403


def test_allowed_role_is_200():
    headers = {"Authorization": f"Bearer {create_access_token(_user('admin'))}"}
    response = _client().get("/admin", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"role": "admin"}
