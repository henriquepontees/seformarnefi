"""
Testes unitários da camada de validação JWT.
Cobrem: token válido, expirado, assinatura inválida e revogado via cache.
"""
import time

import jwt
import pytest

from apps.sso.jwt_utils import verificar_token, decodificar_token


SEGREDO = "test-jwt-secret"


def _emitir(payload: dict, segredo: str = SEGREDO) -> str:
    """Helper que gera um JWT HS256 para os testes."""
    return jwt.encode(payload, segredo, algorithm="HS256")


def test_token_valido_passa():
    """JWT bem-formado e dentro da validade deve ser aceito."""
    token = _emitir({"sub": "user-1", "email": "a@b.c", "exp": time.time() + 60})
    assert verificar_token(token) is True


def test_token_expirado_falha():
    """JWT com exp no passado deve ser rejeitado."""
    token = _emitir({"sub": "user-1", "email": "a@b.c", "exp": time.time() - 60})
    assert verificar_token(token) is False


def test_assinatura_invalida_falha():
    """JWT assinado com outro segredo deve ser rejeitado."""
    token = _emitir({"sub": "user-1", "email": "a@b.c"}, segredo="segredo-errado")
    assert verificar_token(token) is False


def test_token_revogado_falha(db):
    """Token marcado no cache de revogados deve ser rejeitado mesmo se válido."""
    from django.core.cache import cache

    token = _emitir({"sub": "user-1", "email": "a@b.c", "exp": time.time() + 60})
    cache.set(f"revogado:{token}", True, timeout=60)
    try:
        assert verificar_token(token) is False
    finally:
        cache.delete(f"revogado:{token}")


def test_decodificar_retorna_claims():
    """decodificar_token deve devolver o dict de claims original."""
    payload = {"sub": "user-1", "email": "a@b.c", "name": "Henrique"}
    token = _emitir(payload)
    claims = decodificar_token(token)
    assert claims["sub"] == "user-1"
    assert claims["email"] == "a@b.c"
    assert claims["name"] == "Henrique"
