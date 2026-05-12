"""
Testes do fluxo OAuth 2.0 / OIDC.

Mockam as chamadas HTTP ao Keycloak (`exchange_code` e `validar_id_token`)
para validar a lógica de orquestração do backend sem subir o provedor real.
"""
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import Client

from apps.sso import jwt_utils


@pytest.fixture(autouse=True)
def _oauth_env(monkeypatch):
    """Garante variáveis OAuth presentes para todos os testes deste módulo."""
    monkeypatch.setenv("OAUTH_ISSUER", "http://localhost:8180/realms/tcc")
    monkeypatch.setenv("OAUTH_INTERNAL", "http://keycloak:8080/realms/tcc")
    monkeypatch.setenv("OAUTH_CLIENT_ID", "tcc-backend")
    monkeypatch.setenv("OAUTH_CLIENT_SECRET", "tcc-backend-secret")
    monkeypatch.setenv("OAUTH_REDIRECT_URI", "http://localhost:18000/api/auth/callback")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")


@pytest.fixture
def client():
    return Client()


def test_login_redireciona_para_keycloak(client):
    """GET /api/auth/login deve responder 302 apontando para o /auth do Keycloak."""
    res = client.get("/api/auth/login")
    assert res.status_code == 302
    location = res["Location"]
    assert location.startswith("http://localhost:8180/realms/tcc/protocol/openid-connect/auth")
    assert "client_id=tcc-backend" in location
    assert "response_type=code" in location
    assert "state=" in location


def test_callback_com_state_invalido_retorna_400(client):
    """Callback sem state previamente gerado deve falhar (proteção CSRF)."""
    res = client.get("/api/auth/callback?code=fake&state=nao-existe")
    assert res.status_code == 400


def test_callback_happy_path_redireciona_com_token(client):
    """Callback válido troca code, valida ID token e redireciona ao frontend com JWT."""
    # 1. Simula que o /auth/login foi chamado e gerou um state válido
    state = "state-de-teste"
    cache.set(f"oauth_state:{state}", True, timeout=60)

    # 2. Mock dos dois pontos de I/O com o Keycloak
    fake_tokens = {"access_token": "a", "id_token": "i", "refresh_token": "r"}
    fake_claims = {
        "sub": "henrique-id",
        "email": "henrique@tcc.com",
        "name": "Henrique Pontes",
    }

    with patch("apps.sso.api.exchange_code", return_value=fake_tokens) as mock_exc, \
         patch("apps.sso.api.validar_id_token", return_value=fake_claims) as mock_val:
        res = client.get(f"/api/auth/callback?code=fake-code&state={state}")

    mock_exc.assert_called_once_with("fake-code")
    mock_val.assert_called_once_with("i")

    # 3. Resposta: redirect ao frontend com #token=...
    assert res.status_code == 302
    assert res["Location"].startswith("http://localhost:5173/#token=")

    # 4. O token emitido deve validar e conter os claims do ID token
    nosso_jwt = res["Location"].split("#token=")[1]
    assert jwt_utils.verificar_token(nosso_jwt) is True
    claims = jwt_utils.decodificar_token(nosso_jwt)
    assert claims["sub"] == "henrique-id"
    assert claims["email"] == "henrique@tcc.com"
    assert claims["name"] == "Henrique Pontes"


def test_logout_revoga_token(client):
    """POST /api/auth/logout deve revogar o JWT no cache."""
    token = jwt_utils.emitir_token({"sub": "u", "email": "u@x.com", "name": "U"})
    res = client.post("/api/auth/logout", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert res.status_code == 200
    assert res.json() == {"status": "logged out"}
    # Após logout, o token não pode mais ser usado
    assert jwt_utils.verificar_token(token) is False
