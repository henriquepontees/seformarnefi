# 📝 Changelog — Alterações por Sessão

Registro de todas as mudanças feitas pela LLM ao longo do projeto.
Atualizar ao fim de cada sessão.

---

## Formato de entrada

```
## Sessão N — DD/MM/AAAA
### Arquivos criados
### Arquivos editados
### Arquivos deletados
### Decisões tomadas
### Observações
```

---

## Sessão 1 — 11/05/2025

### Arquivos criados
| Arquivo | Caminho | Descrição |
|---|---|---|
| `prompt_projeto_sso_v2.md` | `.claude/` | Prompt inicial do projeto com persona, stack, entregas e regras |
| `rules.md` | `.claude/` | Regras de operação da LLM para economizar tokens |
| `registro_sessao_tcc.md` | `.claude/` | Resumo geral de tudo que foi decidido nesta sessão |
| `changelog.md` | `.claude/` | Este arquivo |

### Arquivos editados
| Arquivo | Caminho | O que mudou |
|---|---|---|
| `rules.md` | `.claude/` | Adicionada seção de comentários obrigatórios no código (docstrings, classes, endpoints) |

### Arquivos deletados
— nenhum —

### Decisões tomadas
- Parte prática do TCC será um pipeline CI/CD DevSecOps aplicado a um sistema SSO
- Stack definida: Django Ninja, Vue.js 3, PostgreSQL, OAuth 2.0, GitHub Actions, OWASP ZAP, Bandit, Pytest, ArgoCD, Doppler
- Doppler escolhido como gerenciador de segredos gratuito
- ArgoCD incluído para GitOps (CD)
- Código deve ter comentários completos em funções, classes e endpoints

### Observações
Sessão de planejamento. Nenhum código do projeto foi escrito ainda.

---

## Sessão 2 — 11/05/2026

### Arquivos criados
| Arquivo | Caminho | Descrição |
|---|---|---|
| `docker-compose.yml` | `/` | Orquestra backend, frontend, db (Postgres) e zap (OWASP ZAP daemon) |
| `.gitignore` | `/` | Ignora artefatos de Python, Node, Doppler, editores e SO |
| `README.md` | `/` | Visão geral, instruções Doppler e plano ArgoCD |
| `security-pipeline.yml` | `.github/workflows/` | Pipeline CI com 3 estágios: Bandit → Pytest → OWASP ZAP |
| `Dockerfile` | `backend/` | Imagem Python 3.12-slim com libpq5 |
| `requirements.txt` | `backend/` | Django 5.1, Django Ninja, PyJWT, psycopg, dj-database-url, pytest, bandit |
| `manage.py` | `backend/` | CLI do Django |
| `pytest.ini` | `backend/` | Config do pytest-django |
| `settings.py` | `backend/config/` | Settings mínimo, lê segredos do ambiente, banco via DATABASE_URL |
| `urls.py` | `backend/config/` | Monta a NinjaAPI sob `/api/` |
| `__init__.py` | `backend/config/`, `backend/apps/`, `backend/apps/sso/`, `backend/tests/` | Marcadores de pacote |
| `api.py` | `backend/apps/sso/` | Endpoints `/api/health` (público) e `/api/me` (protegido por JWT) |
| `jwt_utils.py` | `backend/apps/sso/` | `verificar_token` e `decodificar_token` com cache de revogação |
| `test_smoke.py` | `backend/tests/` | Smoke test mínimo do pytest |
| `Dockerfile` | `frontend/` | Imagem Node 20-alpine com `npm install` |
| `package.json` | `frontend/` | Vue 3 + Vite |
| `vite.config.js` | `frontend/` | Vite escutando em 0.0.0.0:5173 |
| `index.html` | `frontend/` | Entry HTML do Vite |
| `main.js` | `frontend/src/` | Bootstrap do Vue |
| `App.vue` | `frontend/src/` | Componente raiz que consulta `/api/health` |

### Arquivos editados
| Arquivo | Caminho | O que mudou |
|---|---|---|
| `changelog.md` | `.claude/` | Adicionada entrada da Sessão 2 |

### Arquivos deletados
— nenhum —

### Decisões tomadas
- App Django renomeado de `apps.auth` para `apps.sso` para evitar colisão com `django.contrib.auth`
- Python 3.12-slim no container do backend (3.14 do host é muito novo para Django/libs)
- JWT com HS256 no MVP — migrar para RS256 + JWKS quando integrar com provedor OIDC real
- Cache em memória (`LocMemCache`) para revogação de tokens — Redis fica para produção
- ZAP roda como daemon local no compose; pipeline CI usa `zaproxy/action-baseline`

### Observações
Estrutura completa entregue. Próximo passo é validar `doppler run -- docker compose up --build`, escrever testes reais do fluxo SSO e fazer o primeiro commit/push para o repositório no GitHub.

---

## Sessão 3 — 12/05/2026

### Arquivos criados
| Arquivo | Caminho | Descrição |
|---|---|---|
| `realm.json` | `keycloak/` | Realm `tcc` pré-configurado com client `tcc-backend` e usuário `henrique` |
| `oauth.py` | `backend/apps/sso/` | Cliente OAuth/OIDC: authorize URL, troca de code, validação via JWKS |
| `test_oauth.py` | `backend/tests/` | 4 testes do fluxo OAuth com mock das chamadas ao Keycloak |
| `COMANDOS.md` | `/` | Referência de comandos do dia a dia (criado na sessão; ampliado aqui) |

### Arquivos editados
| Arquivo | Caminho | O que mudou |
|---|---|---|
| `docker-compose.yml` | `/` | Serviço `keycloak` adicionado (Keycloak 25 + import do realm) |
| `api.py` | `backend/apps/sso/` | Endpoints `/auth/login`, `/auth/callback`, `/auth/logout` |
| `jwt_utils.py` | `backend/apps/sso/` | Funções `emitir_token` e `revogar_token` |
| `settings.py` | `backend/config/` | `corsheaders` + `CORS_ALLOWED_ORIGINS` para o Vue |
| `requirements.txt` | `backend/` | + `django-cors-headers`, `requests`, `PyJWT[crypto]` |
| `App.vue` | `frontend/src/` | UI completa: login, exibição de claims, logout |
| `.env` / `.env.example` | `/` | Variáveis OAuth (issuer público + internal, client, redirect, frontend) |
| `README.md` | `/` | Documentado o fluxo SSO ponta a ponta e o admin do Keycloak |
| `COMANDOS.md` | `/` | Seção Keycloak adicionada |
| `changelog.md` | `.claude/` | Entrada da Sessão 3 |

### Arquivos deletados
— nenhum —

### Decisões tomadas
- Provedor OIDC: **Keycloak 25** no compose, com realm importado via volume na inicialização
- Backend re-emite JWT próprio (HS256) após validar o ID token (RS256) do Keycloak — cliente nunca vê tokens do provedor
- Separação `OAUTH_ISSUER` (URL pública, vai na claim `iss`) vs `OAUTH_INTERNAL` (URL na rede Docker) para resolver mismatch frontchannel/backchannel
- Token entregue ao frontend via **URL fragment** (`#token=`) — não vaza em logs/Referer
- Proteção CSRF do callback via `state` aleatório guardado no cache do Django com TTL de 5min
- Frontend sem `vue-router`: uma única `App.vue` com renderização condicional baseada em `localStorage`

### Observações
14 testes passando (4 novos do OAuth, com mock de `exchange_code` e `validar_id_token`). Fluxo end-to-end validado: `GET /api/auth/login` responde 302 para o Keycloak com state válido. Usuário de teste pré-criado: `henrique` / `tcc123`.

---

## Sessão 4 — 12/05/2026

### Arquivos criados
| Arquivo | Caminho | Descrição |
|---|---|---|
| `APRESENTACAO.md` | `/` | Guia de apresentação do TCC com roteiro, demo e outputs reais capturados |
| `legado.py` | `backend/apps/sso/` | **(branch `demo/vulneravel`)** módulo com 4 vulnerabilidades intencionais |
| `test_vulneravel.py` | `backend/tests/` | **(branch `demo/vulneravel`)** testes que provam a exploração das falhas |

### Arquivos editados
| Arquivo | Caminho | O que mudou |
|---|---|---|
| `urls.py` | `backend/config/` | **(branch `demo/vulneravel`)** monta `legado_router` sob `/api/legado/` |
| `changelog.md` | `.claude/` | Entrada da Sessão 4 |

### Arquivos deletados
— nenhum —

### Decisões tomadas
- Branch separada `demo/vulneravel` em vez de poluir a `main` — permite alternar com `git checkout` durante a apresentação
- 4 vulnerabilidades cobrindo o tripé SAST + testes + DAST:
  - Credenciais hardcoded (B105)
  - MD5 para hash de senha (B324, HIGH)
  - SQL injection via f-string (B608, MEDIUM)
  - Endpoint admin sem autenticação vazando segredos
- Testes que **passam** demonstrando que a exploração funciona — argumento didático: "testes não escritos = falhas não descobertas"
- Outputs reais do Bandit/Pytest/curl capturados e colados em `APRESENTACAO.md` (em vez de outputs hipotéticos)

### Observações
Pipeline comparativo pronto: `main` passa nos 3 estágios (Bandit 0 issues), `demo/vulneravel` falha com 2 issues médios/altos no Bandit + 3 testes provando exploração viva. Exploit do endpoint admin retorna `db_password` e `api_key` ao curl, demonstrando o impacto.

---

## Sessão 5 — 12/05/2026

### Arquivos criados
| Arquivo | Caminho | Descrição |
|---|---|---|
| `00-namespace.yaml` | `k8s/` | Namespace `tcc-sso` |
| `01-config.yaml` | `k8s/` | ConfigMap (vars não sensíveis) + Secret (credenciais) |
| `02-postgres.yaml` | `k8s/` | PVC + Deployment + Service do Postgres |
| `03-keycloak.yaml` | `k8s/` | ConfigMap com realm.json embedado + Deployment + Service NodePort 30180 |
| `04-backend.yaml` | `k8s/` | Deployment (imagem local) + Service NodePort 30800 |
| `05-frontend.yaml` | `k8s/` | Deployment (imagem local) + Service NodePort 30173 |
| `application.yaml` | `argocd/` | Application CR apontando para `k8s/` do repo (auto-sync + selfHeal) |
| `setup.ps1` | `k8s/` | Script PowerShell que cria cluster k3d + ArgoCD + Application em 1 comando |
| `K8S.md` | `/` | Guia completo: pré-requisitos, setup, endpoints, fluxo GitOps, troubleshooting |

### Arquivos editados
| Arquivo | Caminho | O que mudou |
|---|---|---|
| `realm.json` | `keycloak/` | redirectUris e webOrigins agora aceitam URLs do compose **e** do k8s |
| `changelog.md` | `.claude/` | Entrada da Sessão 5 |

### Arquivos deletados
— nenhum —

### Decisões tomadas
- **Single-repo GitOps**: manifestos no mesmo repo do código, não em repo separado, para simplificar
- ArgoCD `syncPolicy.automated` com `prune` + `selfHeal` — repo é fonte única de verdade
- NodePorts dedicados (30173/30800/30180/30443) mapeados via k3d para portas distintas das do compose (25173/28000/28180/28443) — permite rodar os dois ambientes sem reconfigurar
- Realm Keycloak agora declara redirect URIs dos dois ambientes em uma única `realm.json` (válida para compose e k8s)
- Secret em texto plano no Git **assumido como limitação acadêmica** — documentado em K8S.md o caminho para Sealed Secrets/Vault em produção real
- Imagens locais importadas via `k3d image import` em vez de exigir registry (Docker Hub, GHCR)

### Observações
k3d não está instalado no host. K8S.md tem instruções de instalação via Chocolatey/Scoop. O `setup.ps1` automatiza todo o resto (cluster, imagens, ArgoCD, Application) em um comando depois que o k3d estiver disponível.
