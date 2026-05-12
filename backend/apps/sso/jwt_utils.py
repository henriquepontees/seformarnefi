"""
Utilitários de validação e decodificação de JWT.
Mantidos separados da camada de API para facilitar testes unitários.
"""
import os

import jwt
from django.core.cache import cache

# HS256: simétrico, simples para o MVP acadêmico.
# Próximo passo de produção seria migrar para RS256 + JWKS do provedor OIDC.
_ALGORITHM = "HS256"


def _segredo() -> str:
    """Lê o segredo JWT do ambiente (injetado pelo Doppler)."""
    return os.environ["JWT_SECRET"]


def verificar_token(token: str) -> bool:
    """
    Valida assinatura, expiração e revogação do JWT.

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
