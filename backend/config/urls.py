"""
Roteamento principal: monta a NinjaAPI sob /api/.
"""
from django.urls import path

from apps.sso.api import api
from apps.sso.legado import router as legado_router

# Branch demo/vulneravel: monta o router "legado" sob /api/legado/
# para demonstrar deteccao de vulnerabilidades pelo pipeline.
api.add_router("/legado", legado_router)

urlpatterns = [
    path("api/", api.urls),
]
