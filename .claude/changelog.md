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
