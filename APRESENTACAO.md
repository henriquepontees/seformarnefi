# 🎓 Guia de Apresentação — TCC

> **Tema:** Modelos Preventivos de Quality Assurance para Mitigação de Vulnerabilidades em Sistemas Web com Single Sign-On
>
> **Argumento central:** um pipeline de CI/CD com etapas de segurança detecta e bloqueia vulnerabilidades antes que cheguem à produção — e libera PRs limpos sem intervenção humana.

---

## 🧭 Roteiro sugerido (15-25 min)

1. **Contexto e problema** (2 min) — por que QA preventiva em SSO
2. **Stack escolhida** (2 min) — Django Ninja + Vue + Keycloak + Docker + k8s + ArgoCD
3. **Fluxo SSO funcionando** (3 min) — demo ao vivo do login OAuth
4. **Pipeline DevSecOps** (3 min) — 3 estágios: SAST → testes → DAST
5. **Demo do tripé — três cenários de PR** (8 min) ⭐ **coração da apresentação**
6. **GitOps com ArgoCD** (3 min) — push pra Git → cluster sincroniza sozinho
7. **Resultados e conclusões** (2-3 min)

---

## 🎬 As três branches preparadas para a apresentação

| Branch | Cenário | Bandit | Pytest | Pipeline | Mergeavel? |
|---|---|---|---|---|---|
| `main` | Estado estável atual | 0 issues | 14/14 | ✅ verde | — |
| `demo/feature-segura` | **PR limpo** — adiciona endpoint `/api/auth/refresh` com revogação | 0 issues | **20/20** (+6 novos) | ✅ verde | ✅ **sim** |
| `demo/vulneravel` | **PR ruim** — código legado com 4 vulnerabilidades | **2 issues (HIGH+MED)** | 17/17 (3 provando exploit) | ❌ vermelho | ❌ **não** |

Comando para alternar:
```bash
git checkout main
git checkout demo/feature-segura
git checkout demo/vulneravel
docker compose restart backend   # backend recarrega com o codigo da branch
```

---

## 📋 Pré-demo — checklist

```bash
cd C:\Users\henri\Projetos\tcc-sso
docker compose up -d              # ou .\k8s\setup.ps1 se for usar k8s
docker compose ps                 # confirmar 5 containers up

curl http://localhost:18000/api/health    # {"status": "ok"}
# Abrir http://localhost:5173 no navegador
```

---

## 1️⃣ Demo do fluxo SSO (branch `main`)

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

## 2️⃣ Demo do tripé — comparação de 3 PRs

A força do TCC está aqui: **mostrar que o pipeline aceita o bom e rejeita o ruim, sem revisor humano**.

### 🟢 Cenário A — PR limpo (`demo/feature-segura`)

> Um desenvolvedor implementa o endpoint `/api/auth/refresh` para renovar JWTs antes de expirarem, revogando o token antigo no mesmo passo (mitigação de replay).

```bash
git checkout demo/feature-segura
docker compose restart backend
```

**Estágio 1 — Bandit (SAST):**
```bash
docker compose exec backend bandit -r apps/ -ll -ii
```
```
Run metrics:
    Total issues (by severity):
        High: 0  |  Medium: 0  |  Low: 0
```

**Estágio 2 — Pytest:**
```bash
docker compose exec backend pytest -v
```
```
======================== 20 passed in 2.22s ========================
```
Os 6 testes novos cobrem: happy path, sem auth, assinatura inválida, expirado, revogação do antigo, extensão da expiração.

➡️ **Pipeline VERDE** → PR pode ser mergeado.

---

### 🔴 Cenário B — PR com vulnerabilidades (`demo/vulneravel`)

> Mesma situação: um desenvolvedor abre um PR. Mas dessa vez introduziu um módulo "legado" com vulnerabilidades reais.

```bash
git checkout demo/vulneravel
docker compose restart backend
```

**Vulnerabilidades injetadas:**

| Vulnerabilidade | Tipo | Detectado por |
|---|---|---|
| Senha hardcoded (`admin123`) | Credencial em código | Pytest |
| API key hardcoded (`sk_live_*`) | Credencial em código | Pytest |
| `hashlib.md5()` para senha | Crypto quebrado | **Bandit B324 HIGH** |
| SQL injection via `f"WHERE name = '{nome}'"` | SQLi | **Bandit B608 MEDIUM** |
| `/api/legado/admin/dump` sem auth | Auth bypass | Pytest / DAST |

**Estágio 1 — Bandit captura:**
```bash
docker compose exec backend bandit -r apps/ -ll -ii
```
```
>> Issue: [B324:hashlib] Use of weak MD5 hash for security.
   Severity: High   Confidence: High
   Location: apps/sso/legado.py:28:11

>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector
   Severity: Medium   Confidence: Medium
   Location: apps/sso/legado.py:39:20

Total issues (by severity):
    High: 1  |  Medium: 1  |  Low: 1
```

**Estágio 2 — Pytest expõe o exploit:**
```bash
docker compose exec backend pytest tests/test_vulneravel.py -v
```
```
tests/test_vulneravel.py::test_endpoint_admin_acessivel_sem_autenticacao PASSED
tests/test_vulneravel.py::test_md5_usado_para_senhas                    PASSED
tests/test_vulneravel.py::test_credenciais_hardcoded_no_codigo          PASSED
```

**Exploit ao vivo** (para impacto visual):
```bash
curl http://localhost:18000/api/legado/admin/dump
```
```json
{
    "db_password": "admin123",
    "api_key": "sk_live_prod_xyz789abc456",
    "hash_exemplo": "e10adc3949ba59abbe56e057f20f883e"
}
```

➡️ **Pipeline VERMELHO** → PR bloqueado, merge impossível.

---

### 📊 Comparação lado a lado

```
                     demo/feature-segura      demo/vulneravel
                     ────────────────────     ────────────────────
Bandit               0 issues   ✅              2 issues (1 H, 1 M)  ❌
Pytest               20/20      ✅              17/17 (3 expoem falha)
Exploit possivel?    nao        ✅              SIM — vaza segredos   ❌
Merge para main      LIBERADO   ✅              BLOQUEADO            ❌
Tempo de feedback    < 1 min                   < 1 min
```

> **A diferença não é o tamanho do PR ou o tempo do CI — é o gate automatizado.** O mesmo pipeline aprovou um, bloqueou o outro, sem revisor humano.

---

## 3️⃣ GitOps com ArgoCD (deploy automatizado)

Depois que o CI verde aprova o PR e o merge é feito em `main`, o ArgoCD detecta a mudança nos manifestos Kubernetes e sincroniza o cluster automaticamente.

```bash
# Pre-condicao: cluster k3d + ArgoCD instalados (.\k8s\setup.ps1)
kubectl get application tcc-sso -n argocd -w
# main: SYNC STATUS = Synced, HEALTH = Healthy
```

**Demonstrar a sincronização ao vivo:**
1. Editar `k8s/04-backend.yaml`: `replicas: 1` → `replicas: 2`
2. `git commit + git push origin main`
3. Em até 3min (ou forçando via UI): ArgoCD detecta `OutOfSync`
4. Auto-sync dispara → `kubectl apply` automático
5. `kubectl get pods -n tcc-sso` mostra 2 pods de backend

**Acessar a UI do ArgoCD:** https://localhost:28443 (admin / senha do setup)

> **Argumento:** o Git é a única fonte de verdade. Qualquer mudança no cluster fora do Git é desfeita automaticamente (`selfHeal: true`). Auditoria total via `git log`.

---

## 4️⃣ Pontos para o examinador

**Por que cada ferramenta complementa a outra?**

- **Bandit (SAST)** lê o código sem executar — pega padrões estáticos como `f"SELECT...{var}"` ou `hashlib.md5`. Rápido e barato, mas tem falsos positivos e não enxerga lógica em tempo de execução.
- **Pytest** executa fluxos reais — pega bugs lógicos (auth bypass, permissões erradas) que SAST não consegue ver. Depende de o time escrever testes cobrindo os caminhos críticos.
- **OWASP ZAP (DAST)** ataca a aplicação rodando — pega problemas de configuração (headers, redirects, CORS) e respostas inseguras que só aparecem em runtime. Complementa SAST com a visão de "como o atacante interage com a aplicação".

**Por que GitOps fecha o ciclo?**
- CI verde decide *se pode subir*, GitOps decide *quando subir*. Operações deixam de ser manuais.
- `selfHeal` impede que mudanças via `kubectl` direto sobrevivam — o cluster sempre obedece ao Git.

**Argumento defensável:** nenhuma ferramenta sozinha resolve. A combinação **SAST + Testes + DAST + GitOps** cobre 4 ângulos:
- *código* (estático)
- *comportamento* (testes funcionais)
- *superfície exposta* (runtime)
- *deployment* (versionado)

---

## 🗂️ Referências durante a apresentação

- [README.md](README.md) — visão geral
- [COMANDOS.md](COMANDOS.md) — comandos do dia a dia
- [K8S.md](K8S.md) — setup do cluster + ArgoCD
- [.github/workflows/security-pipeline.yml](.github/workflows/security-pipeline.yml) — pipeline CI
- [backend/apps/sso/api.py](backend/apps/sso/api.py) — endpoints SSO
- Branches: `main`, `demo/feature-segura`, `demo/vulneravel`

---

## 🧹 Pós-demo — voltar à main

```bash
git checkout main
docker compose restart backend
# se rodou k8s:
k3d cluster delete tcc-sso        # desfaz o cluster (opcional)
docker compose up -d              # volta ao ambiente dev original
```
