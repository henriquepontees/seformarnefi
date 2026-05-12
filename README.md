# TCC SSO — Pipeline CI/CD DevSecOps

Parte prática do TCC: demonstrar que um pipeline de CI/CD com etapas de segurança detecta e bloqueia vulnerabilidades em um sistema SSO antes da produção.

## Stack
Django Ninja · Vue 3 · PostgreSQL · OAuth 2.0 · Docker · GitHub Actions · Bandit · Pytest · OWASP ZAP · ArgoCD

## Como rodar localmente

Pré-requisitos: Docker e Docker Compose.

```bash
# 1. Criar o .env a partir do exemplo
cp .env.example .env       # Linux/Mac
copy .env.example .env     # Windows (cmd)

# 2. Editar .env com valores reais

# 3. Subir tudo
docker compose up --build
```

- Backend: http://localhost:18000/api/health
- Frontend: http://localhost:5173

## Variáveis de ambiente

Todas as variáveis ficam no arquivo `.env` (não versionado). Veja [.env.example](.env.example) para o template.

| Nome | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | Chave do Django |
| `DJANGO_DEBUG` | `true` em dev, `false` em produção |
| `JWT_SECRET` | Segredo HMAC para assinar/validar JWT |
| `POSTGRES_DB` | Nome do banco |
| `POSTGRES_USER` | Usuário do banco |
| `POSTGRES_PASSWORD` | Senha do banco |

### No GitHub Actions
As mesmas variáveis devem existir em **Settings → Secrets and variables → Actions** com os mesmos nomes. O workflow gera um `.env` no runner a partir desses secrets antes de subir os containers.

Nenhum arquivo `.env` deve ser comitado.

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
├── .env.example                # Template das variáveis
└── docker-compose.yml
```
