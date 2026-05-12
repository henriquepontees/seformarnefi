"""
Testes do endpoint POST /api/auth/refresh.

Cobre os caminhos seguros:
- Renovação com token válido
- Rejeição de token expirado
- Rejeição de token revogado
- Garantia de que o token antigo nao pode ser reutilizado apos renovacao
"""
import time

import jwt
import pytest
from django.test import Client

from apps.sso import jwt_utils


SEGREDO = "test-jwt-secret"


@pytest.fixture
def client():
    return Client()


def _emitir_local(payload: dict) -> str:
    """Atalho para emitir JWT com o segredo de teste."""
    return jwt.encode(payload, SEGREDO, algorithm="HS256")


def test_refresh_com_token_valido_retorna_novo_jwt(client):
    """POST /api/auth/refresh com Bearer valido emite outro JWT com mesmos claims."""
    token = jwt_utils.emitir_token({"sub": "u1", "email": "u1@x.com", "name": "U1"})
    res = client.post("/api/auth/refresh", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert res.status_code == 200
    body = res.json()
    assert "token" in body
    assert body["expires_in"] == 3600

    # Novo token e diferente do antigo e carrega os mesmos claims de identidade
    novo = body["token"]
    assert novo != token
    novos_claims = jwt_utils.decodificar_token(novo)
    assert novos_claims["sub"] == "u1"
    assert novos_claims["email"] == "u1@x.com"
    assert novos_claims["name"] == "U1"


def test_refresh_revoga_token_antigo(client):
    """Apos refresh, o token antigo nao pode mais ser usado (mitiga replay)."""
    token = jwt_utils.emitir_token({"sub": "u1", "email": "u1@x.com", "name": "U1"})
    client.post("/api/auth/refresh", HTTP_AUTHORIZATION=f"Bearer {token}")

    # Token antigo agora e tratado como invalido
    assert jwt_utils.verificar_token(token) is False
    # E uma chamada subsequente a refresh com o antigo retorna 401
    res = client.post("/api/auth/refresh", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert res.status_code == 401


def test_refresh_sem_token_retorna_401(client):
    """Sem header Authorization, refresh deve responder 401."""
    res = client.post("/api/auth/refresh")
    assert res.status_code == 401


def test_refresh_com_token_assinatura_invalida_retorna_401(client):
    """Token assinado com outro segredo deve ser rejeitado."""
    token = _emitir_local({"sub": "u", "email": "u@x.com", "exp": time.time() + 60})
    # Mas como o segredo de teste e o mesmo, vou usar um terceiro segredo
    token_invalido = jwt.encode(
        {"sub": "u", "email": "u@x.com", "exp": time.time() + 60},
        "outro-segredo-totalmente-diferente",
        algorithm="HS256",
    )
    res = client.post("/api/auth/refresh", HTTP_AUTHORIZATION=f"Bearer {token_invalido}")
    assert res.status_code == 401


def test_refresh_com_token_expirado_retorna_401(client):
    """Token com exp no passado deve ser rejeitado."""
    expirado = _emitir_local({"sub": "u", "email": "u@x.com", "exp": time.time() - 1})
    res = client.post("/api/auth/refresh", HTTP_AUTHORIZATION=f"Bearer {expirado}")
    assert res.status_code == 401


def test_refresh_extende_expiracao(client):
    """O novo token deve ter exp maior que o token original."""
    token_curto = jwt_utils.emitir_token(
        {"sub": "u1", "email": "u1@x.com", "name": "U1"},
        ttl_segundos=60,
    )
    exp_antigo = jwt_utils.decodificar_token(token_curto)["exp"]

    res = client.post("/api/auth/refresh", HTTP_AUTHORIZATION=f"Bearer {token_curto}")
    assert res.status_code == 200

    novo = res.json()["token"]
    exp_novo = jwt_utils.decodificar_token(novo)["exp"]

    # Novo exp e bem maior (deveria ser ~1h vs 60s do original)
    assert exp_novo > exp_antigo + 60
