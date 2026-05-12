# 🎓 Guia de Apresentação — TCC

> **Tema:** Modelos Preventivos de Quality Assurance para Mitigação de Vulnerabilidades em Sistemas Web com Single Sign-On
>
> **Argumento central:** um pipeline de CI/CD com etapas de segurança detecta e bloqueia vulnerabilidades antes que cheguem à produção.

---

## 🧭 Roteiro sugerido (15-20 min)

1. **Contexto e problema** (2 min) — por que QA preventiva em SSO
2. **Stack escolhida** (2 min) — Django Ninja + Vue + Keycloak + Docker
3. **Fluxo SSO funcionando** (3 min) — demo ao vivo do login OAuth
4. **Pipeline DevSecOps** (3 min) — 3 estágios: SAST → testes → DAST
5. **Demo "Sem QA vs Com QA"** (5 min) — este é o coração da apresentação
6. **Resultados e conclusões** (2-3 min)

---

## 🎬 Demo ao vivo — duas branches, dois cenários

O repositório tem duas branches preparadas para a apresentação:

| Branch | Cenário | O que esperar |
|---|---|---|
| `main` | **Com QA aplicada** | Bandit: 0 issues · Pytest: 14/14 · ZAP: clean |
| `demo/vulneravel` | **Sem QA aplicada** | Bandit: 2 issues · Pytest: 17/17 (3 provando exploit) · ZAP: vazamento de dados |

Comando para alternar:
```bash
git checkout main             # versão segura
git checkout demo/vulneravel  # versão com falhas intencionais
```

---

## 📋 Pré-demo — checklist

```bash
# 1. Estar na pasta do projeto
cd C:\Users\henri\Projetos\tcc-sso

# 2. Containers no ar
docker compose up -d
docker compose ps

# 3. Smoke test rápido
curl http://localhost:18000/api/health   # {"status": "ok"}

# 4. Vue acessível
# abrir http://localhost:5173 no navegador
```

Se algum container estiver parado: `docker compose up -d` resolve.

---

## 1️⃣ Demo do fluxo SSO (com QA — branch `main`)

```bash
git checkout main
```

**No navegador:**

1. Abrir http://localhost:5173
2. Clicar em **Entrar com SSO**
3. Logar no Keycloak: `henrique` / `tcc123`
4. Voltar ao Vue mostrando `sub`, `email`, `nome`
5. Clicar **Sair** — token revogado, sessão encerrada

**Pontos a destacar:**
- O backend nunca expôs as credenciais ao cliente — só recebeu um *authorization code*
- O cliente vê apenas um JWT emitido pelo backend (HS256), nunca os tokens RS256 do Keycloak
- O `state` aleatório protege contra CSRF no callback
- O token vai no fragment (`#token=`), não em query string — não aparece em logs

---

## 2️⃣ Demo "Com QA" — pipeline na branch `main`

### Estágio 1 — Bandit (SAST)
```bash
docker compose exec backend bandit -r apps/ -ll -ii
```
**Saída esperada:**
```
Test results:
  No issues identified.
```

### Estágio 2 — Pytest
```bash
docker compose exec backend pytest -v
```
**Saída esperada:** `14 passed`

### Estágio 3 — ZAP (resumo)
No CI o `zaproxy/action-baseline` faz varredura passiva. Localmente daria pra simular com:
```bash
docker run --rm --network tcc-sso_default \
  zaproxy/zap-stable zap-baseline.py -t http://backend:8000
```

**Conclusão:** main passaria nos 3 estágios → deploy autorizado.

---

## 3️⃣ Demo "Sem QA" — pipeline na branch `demo/vulneravel`

```bash
git checkout demo/vulneravel
docker compose restart backend   # backend recarrega com o novo código
```

A branch adiciona um módulo `apps/sso/legado.py` com **vulnerabilidades intencionais**:

| Vulnerabilidade | Tipo | Quem detecta |
|---|---|---|
| Senha de banco hardcoded (`admin123`) | Credencial em código | Bandit B105 / Pytest |
| API key hardcoded (`sk_live_*`) | Credencial em código | Bandit / Pytest |
| `hashlib.md5()` para senha | Crypto quebrado | **Bandit B324 (HIGH)** |
| `f"SELECT ... WHERE name = '{nome}'"` | SQL Injection | **Bandit B608 (MEDIUM)** |
| `/api/legado/admin/dump` sem autenticação | Auth bypass | Pytest / DAST |

### Estágio 1 — Bandit captura na branch vulnerável

```bash
docker compose exec backend bandit -r apps/ -ll -ii
```

**Saída real capturada:**
```
>> Issue: [B324:hashlib] Use of weak MD5 hash for security.
   Severity: High   Confidence: High
   CWE: CWE-327
   Location: apps/sso/legado.py:28:11
27    """
28        return hashlib.md5(senha.encode()).hexdigest()

>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector
   Severity: Medium   Confidence: Medium
   CWE: CWE-89
   Location: apps/sso/legado.py:39:20
38        # Concatenacao direta de input nao sanitizado na query
39        c.execute(f"SELECT id, username FROM auth_user WHERE first_name = '{nome}'")

Run metrics:
    Total issues (by severity):
        High: 1
        Medium: 1
        Low: 1
```

➡️ **Pipeline falha aqui.** Sem QA, esse código iria pra produção.

### Estágio 2 — Pytest demonstra exploração

```bash
docker compose exec backend pytest tests/test_vulneravel.py -v
```

**Saída real capturada:**
```
tests/test_vulneravel.py::test_endpoint_admin_acessivel_sem_autenticacao PASSED
tests/test_vulneravel.py::test_md5_usado_para_senhas                    PASSED
tests/test_vulneravel.py::test_credenciais_hardcoded_no_codigo          PASSED
```

> **Importante:** esses testes PASSAM. Eles documentam que a vulnerabilidade existe e é explorável. Em um projeto sério, eles seriam o ponto de partida para corrigir a falha — depois da correção, os testes seriam reescritos para verificar que a exploração não funciona mais.

### Exploit ao vivo no navegador / curl

```bash
curl http://localhost:18000/api/legado/admin/dump
```

**Saída real capturada:**
```json
{
    "db_password": "admin123",
    "api_key": "sk_live_prod_xyz789abc456",
    "hash_exemplo": "e10adc3949ba59abbe56e057f20f883e"
}
```

➡️ Qualquer pessoa com a URL recebe credenciais e API key.

### Estágio 3 — ZAP (varredura dinâmica)

ZAP detectaria:
- Endpoint expondo dados sensíveis em `/api/legado/admin/dump`
- Falta de headers de segurança (X-Frame-Options, CSP)
- Possível disclosure via mensagens de erro detalhadas (DEBUG=true)

---

## 4️⃣ Comparação lado a lado

| Critério | Sem QA (`demo/vulneravel`) | Com QA (`main`) |
|---|---|---|
| Vulnerabilidades em produção | 4+ | 0 detectadas |
| Tempo entre commit e descoberta | meses (auditoria externa) | < 1 minuto (CI) |
| Custo de remediação | alto (incidente, multa LGPD) | baixo (PR rejeitado) |
| Confiança do time | reativa | preditiva |

---

## 5️⃣ Pontos para o examinador

**Por que cada ferramenta complementa a outra?**

- **Bandit (SAST)** lê o código sem executar — pega padrões estáticos como `f"SELECT...{var}"` ou `hashlib.md5`. É rápido e barato, mas tem falsos positivos e não enxerga lógica em tempo de execução.
- **Pytest** executa fluxos reais — pega bugs lógicos (auth bypass, permissões erradas) que SAST não consegue ver. Depende de o time escrever testes que cubram os caminhos críticos.
- **OWASP ZAP (DAST)** ataca a aplicação rodando — pega problemas de configuração (headers, redirects, CORS) e respostas inseguras que só aparecem em runtime. Complementa SAST com a visão de "como o atacante interage com a aplicação".

**Argumento defensável:** nenhuma ferramenta sozinha resolve. A combinação SAST+Testes+DAST cobre os 3 ângulos: código → comportamento → superfície exposta.

---

## 🗂️ Referências rápidas durante a apresentação

- [README.md](README.md) — visão geral
- [COMANDOS.md](COMANDOS.md) — comandos do dia a dia
- [.github/workflows/security-pipeline.yml](.github/workflows/security-pipeline.yml) — definição dos 3 estágios
- [backend/apps/sso/api.py](backend/apps/sso/api.py) — endpoints do SSO
- Branch `demo/vulneravel` — `git checkout demo/vulneravel`

---

## 🧹 Pós-demo — voltar à main

Não esquecer no final da apresentação:
```bash
git checkout main
docker compose restart backend
```
