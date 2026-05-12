"""
Codigo "legado" SEM QA aplicado.

Modulo didatico que concentra vulnerabilidades intencionais
para demonstrar como o pipeline DevSecOps as detecta.

NAO USAR EM PRODUCAO. Existe APENAS na branch demo/vulneravel.
"""
import hashlib

from django.db import connection
from ninja import Router

router = Router()


# ---- Vuln 1: credenciais hardcoded (Bandit B105) ---------------------------
# Usuario deixou senha do banco e API key direto no codigo "para nao esquecer".
DB_ADMIN_PASSWORD = "admin123"
API_KEY_PROD = "sk_live_prod_xyz789abc456"


def hash_senha_fraca(senha: str) -> str:
    """
    Vuln 2: uso de MD5 para hash de senha (Bandit B324).
    MD5 e considerado quebrado para qualquer uso de seguranca.
    """
    return hashlib.md5(senha.encode()).hexdigest()


# ---- Vuln 3: SQL Injection (Bandit B608) -----------------------------------
# Endpoint que monta SQL com f-string a partir de input do usuario.
# Exploravel com payload tipo: ?nome=' OR '1'='1
@router.get("/usuarios/buscar", auth=None)
def buscar_usuario(request, nome: str):
    """Busca usuarios pelo nome — vulneravel a SQL injection."""
    with connection.cursor() as c:
        # Concatenacao direta de input nao sanitizado na query
        c.execute(f"SELECT id, username FROM auth_user WHERE first_name = '{nome}'")
        rows = c.fetchall()
        return [{"id": r[0], "username": r[1]} for r in rows]


# ---- Vuln 4: endpoint admin sem autenticacao -------------------------------
# Vaza credenciais e API keys para qualquer um que descobrir a URL.
@router.get("/admin/dump", auth=None)
def admin_dump(request):
    """Endpoint 'interno' acessivel sem autenticacao — vaza segredos."""
    return {
        "db_password": DB_ADMIN_PASSWORD,
        "api_key": API_KEY_PROD,
        "hash_exemplo": hash_senha_fraca("123456"),
    }
