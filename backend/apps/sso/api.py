"""
Endpoints de autenticação e exemplo de rota protegida via SSO.
A NinjaAPI é montada em /api/ pelo config/urls.py.
"""
from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer

from .jwt_utils import verificar_token, decodificar_token

api = NinjaAPI(title="SSO API", version="1.0.0")


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
        return decodificar_token(token)


class UsuarioOut(Schema):
    """Resposta padrão com dados do usuário autenticado via SSO."""
    sub: str
    email: str
    nome: str | None = None


# GET /api/health — health check público (sem autenticação).
# Usado pelo pipeline para saber quando o backend está pronto.
@api.get("/health", auth=None)
def health(request):
    """Retorna status simples para liveness probe e CI."""
    return {"status": "ok"}


# GET /api/me — exemplo de rota protegida por SSO.
# Requer um JWT válido emitido pelo provedor OAuth 2.0 / OIDC.
@api.get("/me", auth=JWTAuth(), response=UsuarioOut)
def me(request):
    """
    Retorna os dados do usuário autenticado, extraídos dos claims do JWT.

    Returns:
        UsuarioOut com sub, email e nome (quando presente nos claims).
    """
    claims = request.auth
    return UsuarioOut(
        sub=claims["sub"],
        email=claims["email"],
        nome=claims.get("name"),
    )
