"""
Cliente OAuth 2.0 / OpenID Connect contra o provedor Keycloak.

Encapsula os 3 passos do Authorization Code Flow:
1. Montar a URL de autorização (browser → provedor)
2. Trocar o code por tokens (backend → provedor)
3. Validar o ID token via JWKS do provedor

A separação `issuer` vs `internal` existe porque o browser acessa o
Keycloak via `localhost:8180` (porta exposta no host), mas o backend
acessa via `keycloak:8080` na rede Docker. A claim `iss` dos tokens
sempre referencia a URL pública (`issuer`).
"""
import os
from urllib.parse import urlencode

import jwt
import requests
from jwt import PyJWKClient


def _config() -> dict:
    """Lê configuração OAuth do ambiente (injetada pelo .env)."""
    issuer = os.environ["OAUTH_ISSUER"].rstrip("/")
    # OAUTH_INTERNAL é opcional; se ausente, usa o mesmo issuer (deploy single-host).
    internal = os.environ.get("OAUTH_INTERNAL", issuer).rstrip("/")
    return {
        "issuer": issuer,
        "internal": internal,
        "client_id": os.environ["OAUTH_CLIENT_ID"],
        "client_secret": os.environ["OAUTH_CLIENT_SECRET"],
        "redirect_uri": os.environ["OAUTH_REDIRECT_URI"],
        # Browser-facing (issuer público)
        "auth_url": f"{issuer}/protocol/openid-connect/auth",
        # Backend-facing (rede interna do Docker)
        "token_url": f"{internal}/protocol/openid-connect/token",
        "jwks_url": f"{internal}/protocol/openid-connect/certs",
    }


def build_authorize_url(state: str) -> str:
    """
    Monta a URL para redirecionar o usuário ao provedor de SSO.

    Args:
        state: token aleatório para prevenir CSRF; será validado no callback.

    Returns:
        URL completa do endpoint /auth do Keycloak com os query params.
    """
    cfg = _config()
    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "scope": "openid profile email",
        "state": state,
    }
    return f"{cfg['auth_url']}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    """
    Troca o authorization code pelos tokens (access + id + refresh).

    Args:
        code: authorization code recebido no callback do provedor.

    Returns:
        Dict com access_token, id_token, refresh_token, expires_in.

    Raises:
        requests.HTTPError se o provedor recusar o code.
    """
    cfg = _config()
    res = requests.post(
        cfg["token_url"],
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": cfg["redirect_uri"],
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
        },
        timeout=10,
    )
    res.raise_for_status()
    return res.json()


def validar_id_token(id_token: str) -> dict:
    """
    Valida assinatura, issuer, audience e expiração do ID token via JWKS.

    Args:
        id_token: string do ID token retornada pelo provedor.

    Returns:
        Dict com os claims do ID token (sub, email, name, etc).

    Raises:
        jwt.PyJWTError em qualquer falha de validação.
    """
    cfg = _config()
    # PyJWKClient cacheia as chaves para evitar request a cada validação
    jwks = PyJWKClient(cfg["jwks_url"])
    signing_key = jwks.get_signing_key_from_jwt(id_token)
    return jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=cfg["client_id"],
        issuer=cfg["issuer"],
    )
