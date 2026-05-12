"""
Testes que COMPROVAM as vulnerabilidades do modulo legado.

Em um projeto seguro, esses testes deveriam FALHAR (proteger contra a falha).
Aqui eles PASSAM — demonstrando que o sistema esta exposto.

Esse e o argumento central do TCC: testes nao escritos = vulnerabilidades nao descobertas.
"""
import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


def test_endpoint_admin_acessivel_sem_autenticacao(client):
    """
    PROVA: /api/legado/admin/dump retorna 200 sem token,
    quando deveria exigir autenticacao + role de admin.
    """
    res = client.get("/api/legado/admin/dump")
    assert res.status_code == 200
    body = res.json()
    # Confirma o vazamento — segredos chegam ao cliente
    assert "db_password" in body
    assert "api_key" in body


def test_md5_usado_para_senhas():
    """
    PROVA: a funcao de hash do modulo legado usa MD5,
    quebrado ha mais de uma decada para qualquer uso de seguranca.
    """
    from apps.sso.legado import hash_senha_fraca
    # MD5 de "123456" e sempre o mesmo — sem salt, hash precomputavel
    assert hash_senha_fraca("123456") == "e10adc3949ba59abbe56e057f20f883e"


def test_credenciais_hardcoded_no_codigo():
    """
    PROVA: existem strings de credenciais embutidas no codigo-fonte.
    Tooling de SAST (Bandit) tambem deteccta isso estaticamente.
    """
    from apps.sso import legado
    assert legado.DB_ADMIN_PASSWORD == "admin123"
    assert legado.API_KEY_PROD.startswith("sk_live_")
