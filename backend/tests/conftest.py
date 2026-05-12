"""
Configuração compartilhada do pytest.
Garante que os settings do Django sejam carregados com valores de teste.
"""
import os

# Valores de teste injetados ANTES do Django importar settings.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("DJANGO_DEBUG", "true")
