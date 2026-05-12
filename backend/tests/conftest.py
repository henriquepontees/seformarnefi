"""
Configuração compartilhada do pytest.
Força variáveis de ambiente determinísticas para os testes,
mesmo quando o container já tiver valores reais injetados via .env.
"""
import os

# Override (não setdefault) — testes precisam de segredos previsíveis
# para conseguirem assinar e validar JWTs com a mesma chave.
os.environ["DJANGO_SECRET_KEY"] = "test-secret"
os.environ["JWT_SECRET"] = "test-jwt-secret"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["DJANGO_DEBUG"] = "true"
