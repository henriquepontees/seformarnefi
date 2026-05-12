"""
Utilitários de emissão, validação e decodificação de JWT.
Mantidos separados da camada de API para facilitar testes unitários.

Estratégia: o provedor OIDC (Keycloak) autentica o usuário e emite
um ID token RS256. O backend valida esse ID token e re-emite um JWT
próprio HS256 com escopo de sessão. O cliente só vê o JWT do backend.
"""
import os
import time

import jwt
from django.core.cache import cache

# HS256: simétrico, simples para a sessão emitida pelo próprio backend.
# O ID token vindo do Keycloak usa RS256 e é validado em oauth.py.
_ALGORITHM = "HS256"


def _segredo() -> str:
    """Lê o segredo JWT do ambiente (injetado pelo .env)."""
    return os.environ["JWT_SECRET"]


def emitir_token(claims: dict, ttl_segundos: int = 3600) -> str:
    """
    Emite um JWT de sessão assinado pelo backend.

    Args:
        claims: dict com sub, email, name (e quaisquer outros claims).
        ttl_segundos: tempo de vida do token em segundos. Padrão 1h.

    Returns:
        String do JWT pronta para enviar ao cliente.
    """
    payload = {**claims, "exp": time.time() + ttl_segundos}
    return jwt.encode(payload, _segredo(), algorithm=_ALGORITHM)


def verificar_token(token: str) -> bool:
    """
    Valida assinatura, expiração e revogação do JWT de sessão.

    Args:
        token: string do JWT recebida no header Authorization.

    Returns:
        True se o token for válido, False caso contrário.
    """
    # Tokens revogados ficam em cache para evitar lookup no banco a cada request
    if cache.get(f"revogado:{token}"):
        return False
    try:
        jwt.decode(token, _segredo(), algorithms=[_ALGORITHM])
        return True
    except jwt.PyJWTError:
        return False


def decodificar_token(token: str) -> dict:
    """
    Retorna os claims do JWT já validado.

    Args:
        token: JWT já validado por verificar_token().

    Returns:
        Dict com os claims (sub, email, exp, etc).
    """
    return jwt.decode(token, _segredo(), algorithms=[_ALGORITHM])


def revogar_token(token: str, ttl_segundos: int = 3600) -> None:
    """
    Marca um token como revogado pelo TTL configurado.
    Após o TTL, o cache expira naturalmente (e o token também).

    Args:
        token: JWT a ser revogado.
        ttl_segundos: por quanto tempo manter no cache de revogados.
    """
    cache.set(f"revogado:{token}", True, timeout=ttl_segundos)
