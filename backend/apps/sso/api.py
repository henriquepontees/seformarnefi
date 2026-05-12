"""
Endpoints de autenticação e exemplo de rota protegida via SSO.
A NinjaAPI é montada em /api/ pelo config/urls.py.

Fluxo OAuth 2.0 Authorization Code:
- GET  /api/auth/login    → redireciona ao provedor (Keycloak)
- GET  /api/auth/callback → recebe code, valida, emite JWT, redireciona ao frontend
- POST /api/auth/refresh  → renova o JWT antes da expiração (revoga o antigo)
- POST /api/auth/logout   → revoga o JWT atual
- GET  /api/me            → exemplo de rota protegida (requer Bearer JWT)
"""
import os
import secrets

from django.core.cache import cache
from django.http import HttpResponseRedirect
from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer

from .jwt_utils import (
    decodificar_token,
    emitir_token,
    renovar_token,
    revogar_token,
    verificar_token,
)
from .oauth import build_authorize_url, exchange_code, validar_id_token

api = NinjaAPI(title="SSO API", version="1.0.0")

# TTL do state CSRF — janela para o usuário completar o login no provedor
_STATE_TTL = 300


class JWTAuth(HttpBearer):
    """
    Esquema de autenticação Bearer para o Django Ninja.
    Valida o JWT recebido no header Authorization a cada requisição protegida.
    """

    def authenticate(self, request, token: str):
        """
        Verifica se o token é válido e ainda não foi revogado.

        Args:
            request: requisição HTTP do Django.
            token: string do JWT recebida após "Bearer ".

        Returns:
            Dict com os claims do usuário se válido, None caso contrário
            (Ninja responde 401 automaticamente quando recebe None).
        """
        if not verificar_token(token):
            return None
        # Anexa o token bruto também, para que /auth/logout possa revogá-lo
        claims = decodificar_token(token)
        claims["_raw"] = token
        return claims


class UsuarioOut(Schema):
    """Resposta padrão com dados do usuário autenticado via SSO."""
    sub: str
    email: str
    nome: str | None = None


class LogoutOut(Schema):
    """Resposta do endpoint de logout."""
    status: str


class RefreshOut(Schema):
    """Resposta do endpoint de refresh — devolve o novo JWT."""
    token: str
    expires_in: int


# GET /api/health — health check público (sem autenticação).
# Usado pelo pipeline e pelo frontend para saber quando o backend está pronto.
@api.get("/health", auth=None)
def health(request):
    """Retorna status simples para liveness probe e CI."""
    return {"status": "ok"}


# GET /api/auth/login — inicia o fluxo Authorization Code.
# Gera state CSRF, salva no cache e redireciona ao provedor.
@api.get("/auth/login", auth=None)
def auth_login(request):
    """Redireciona o navegador ao Keycloak para autenticação."""
    state = secrets.token_urlsafe(32)
    cache.set(f"oauth_state:{state}", True, timeout=_STATE_TTL)
    return HttpResponseRedirect(build_authorize_url(state))


# GET /api/auth/callback — endpoint que o Keycloak chama após o login.
# Recebe code + state, troca o code por tokens, valida o ID token,
# emite o JWT de sessão e redireciona ao frontend com o token na fragment.
@api.get("/auth/callback", auth=None)
def auth_callback(request, code: str, state: str):
    """Recebe o callback do provedor e devolve o usuário ao frontend autenticado."""
    # CSRF: o state precisa ter sido gerado pelo nosso /auth/login
    if not cache.get(f"oauth_state:{state}"):
        return api.create_response(request, {"detail": "state invalido"}, status=400)
    cache.delete(f"oauth_state:{state}")

    tokens = exchange_code(code)
    claims = validar_id_token(tokens["id_token"])

    nosso_jwt = emitir_token({
        "sub": claims["sub"],
        "email": claims.get("email", ""),
        "name": claims.get("name") or claims.get("preferred_username", ""),
    })

    # Token vai na URL fragment (#) — não aparece em logs HTTP nem em Referer
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return HttpResponseRedirect(f"{frontend_url}/#token={nosso_jwt}")


# POST /api/auth/refresh — emite um novo JWT com TTL renovado.
# Revoga o token antigo no mesmo passo para evitar uso duplo (replay).
_REFRESH_TTL = 3600


@api.post("/auth/refresh", auth=JWTAuth(), response=RefreshOut)
def auth_refresh(request):
    """Troca o JWT atual por um novo com TTL extendido, revogando o antigo."""
    token_antigo = request.auth["_raw"]
    novo = renovar_token(token_antigo, novo_ttl_segundos=_REFRESH_TTL)
    return RefreshOut(token=novo, expires_in=_REFRESH_TTL)


# POST /api/auth/logout — revoga o JWT atual.
# O cliente também deve descartar o token localmente.
@api.post("/auth/logout", auth=JWTAuth(), response=LogoutOut)
def auth_logout(request):
    """Marca o JWT da sessão atual como revogado no cache."""
    token_bruto = request.auth["_raw"]
    revogar_token(token_bruto)
    return LogoutOut(status="logged out")


# GET /api/me — exemplo de rota protegida por SSO.
# Requer um JWT de sessão válido (emitido pelo /auth/callback).
@api.get("/me", auth=JWTAuth(), response=UsuarioOut)
def me(request):
    """Retorna os dados do usuário autenticado, extraídos dos claims do JWT."""
    claims = request.auth
    return UsuarioOut(
        sub=claims["sub"],
        email=claims["email"],
        nome=claims.get("name"),
    )
