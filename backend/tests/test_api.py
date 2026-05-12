"""
Testes de integração dos endpoints da NinjaAPI.
Usam o Django test client direto contra as rotas montadas em /api/.
"""
import time

import jwt
import pytest
from django.test import Client


SEGREDO = "test-jwt-secret"


@pytest.fixture
def client():
    """Client HTTP do Django para bater nos endpoints."""
    return Client()


def _bearer(payload: dict) -> dict:
    """Monta o header Authorization Bearer com um JWT gerado on-the-fly."""
    token = jwt.encode(payload, SEGREDO, algorithm="HS256")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_health_publico(client):
    """/api/health deve responder 200 sem autenticação."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_me_sem_token_retorna_401(client):
    """/api/me sem header Authorization deve falhar com 401."""
    res = client.get("/api/me")
    assert res.status_code == 401


def test_me_com_token_invalido_retorna_401(client):
    """/api/me com JWT assinado com segredo errado deve falhar com 401."""
    token = jwt.encode({"sub": "x", "email": "a@b.c"}, "outro-segredo", algorithm="HS256")
    res = client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert res.status_code == 401


def test_me_com_token_valido_retorna_claims(client):
    """/api/me com JWT válido deve retornar sub, email e nome."""
    headers = _bearer({
        "sub": "user-42",
        "email": "henrique@example.com",
        "name": "Henrique",
        "exp": time.time() + 60,
    })
    res = client.get("/api/me", **headers)
    assert res.status_code == 200
    body = res.json()
    assert body["sub"] == "user-42"
    assert body["email"] == "henrique@example.com"
    assert body["nome"] == "Henrique"
