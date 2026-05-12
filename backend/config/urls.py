"""
Roteamento principal: monta a NinjaAPI sob /api/.
"""
from django.urls import path

from apps.sso.api import api

urlpatterns = [
    path("api/", api.urls),
]
