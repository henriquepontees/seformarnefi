"""
Configuração mínima do Django para o projeto SSO.
Segredos e DSN do banco vêm do ambiente (injetados pelo Doppler).
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = ["*"]  # Restringir em produção

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "corsheaders",
    "apps.sso",
]

MIDDLEWARE = [
    # CORS deve vir antes do CommonMiddleware para responder preflight requests
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# Frontend Vue roda em outra porta — precisa permissão de CORS para chamar a API
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

ROOT_URLCONF = "config.urls"

# Banco — espera DATABASE_URL no formato postgres://user:pass@host:port/db
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        conn_max_age=600,
    )
}

# Cache em memória — suficiente para o MVP. Trocar por Redis em produção.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

USE_TZ = True
TIME_ZONE = "America/Sao_Paulo"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
