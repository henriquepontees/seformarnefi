# TCC SSO — Pipeline CI/CD DevSecOps

Parte prática do TCC: demonstrar que um pipeline de CI/CD com etapas de segurança detecta e bloqueia vulnerabilidades em um sistema SSO antes da produção.

## Stack
Django Ninja · Vue 3 · PostgreSQL · OAuth 2.0 · Docker · GitHub Actions · Bandit · Pytest · OWASP ZAP · Doppler · ArgoCD

## Como rodar localmente

Pré-requisitos: Docker, Docker Compose, Doppler CLI.

```bash
doppler login
doppler setup           # selecionar projeto e ambiente "dev"
doppler run -- docker compose up --build
```

- Backend: http://localhost:8000/api/health
- Frontend: http://localhost:5173

## Doppler — gerenciamento de segredos

Doppler substitui os arquivos `.env` injetando variáveis no ambiente em tempo de execução.

### Variáveis esperadas no projeto
| Nome | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | Chave do Django |
| `JWT_SECRET` | Segredo HMAC para assinar/validar JWT |
| `POSTGRES_DB` | Nome do banco |
| `POSTGRES_USER` | Usuário do banco |
| `POSTGRES_PASSWORD` | Senha do banco |

### Setup local
```bash
# 1. Instalar a CLI (Windows / Scoop)
scoop install doppler

# 2. Autenticar
doppler login

# 3. Vincular este diretório a um projeto/ambiente Doppler
doppler setup

# 4. Rodar qualquer comando com os segredos injetados
doppler run -- docker compose up
doppler run -- python backend/manage.py migrate
```

### Setup no GitHub Actions
1. Em Doppler: criar um **Service Token** para o ambiente `ci`.
2. Em GitHub → Settings → Secrets and variables → Actions: adicionar `DOPPLER_TOKEN_CI`.
3. O workflow já consome esse segredo no estágio ZAP via `dopplerhq/cli-action@v3`.

Nenhum arquivo `.env` deve ser comitado em hipótese alguma.

## ArgoCD — onde ele entra

ArgoCD fecha o ciclo CD aplicando GitOps:

```
Pipeline CI passa  ->  manifests Kubernetes atualizados em repo Git
                                        |
                                        v
                               ArgoCD detecta diff
                                        |
                                        v
                            Sincroniza cluster com Git
```

**Configuração planejada** (próxima sessão):
1. Criar repositório separado `tcc-sso-manifests` com os YAMLs do Kubernetes (Deployment, Service, Ingress).
2. Instalar ArgoCD em cluster local (k3d ou minikube).
3. Criar `Application` no ArgoCD apontando para o repo de manifests.
4. Adicionar ao final do workflow um job que atualiza a tag da imagem no repo de manifests — isso dispara o ArgoCD automaticamente.

A escolha por GitOps garante que o estado do cluster é sempre auditável via histórico Git e que nenhum deploy acontece fora do fluxo controlado pelo pipeline de segurança.

## Estrutura

```
tcc-sso/
├── .claude/                    # Prompt, regras e changelog do projeto
├── .github/workflows/          # Pipeline DevSecOps
├── backend/                    # Django + Django Ninja
│   ├── apps/sso/               # SSO: API, JWT, schemas
│   ├── config/                 # settings, urls
│   └── tests/
├── frontend/                   # Vue 3 + Vite
└── docker-compose.yml
```
