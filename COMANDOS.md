# 🛠️ Comandos Úteis

Referência rápida dos comandos do dia a dia neste projeto.
Rodar tudo na raiz `tcc-sso/`.

---

## 🐳 Docker Compose — ciclo de vida

```bash
# Sobe todos os serviços em background (db, backend, frontend, zap)
docker compose up -d

# Sobe forçando rebuild das imagens (use após mudar Dockerfile ou requirements.txt)
docker compose up --build -d

# Derruba os containers (mantém volumes — banco preservado)
docker compose down

# Derruba E apaga volumes (zera o banco)
docker compose down -v

# Status atual dos containers
docker compose ps

# Reinicia só um serviço (útil quando mexe em settings.py)
docker compose restart backend
```

## 📜 Logs

```bash
# Stream dos logs do backend (Ctrl+C para sair)
docker compose logs -f backend

# Últimas 50 linhas de qualquer serviço
docker compose logs --tail=50 frontend

# Logs de todos os serviços juntos
docker compose logs -f
```

## 🐍 Django / Backend (dentro do container)

```bash
# Abre o shell interativo do Django com acesso aos models
docker compose exec backend python manage.py shell

# Cria migrations a partir de mudanças nos models
docker compose exec backend python manage.py makemigrations

# Aplica as migrations no Postgres
docker compose exec backend python manage.py migrate

# Cria um superuser (admin do Django)
docker compose exec backend python manage.py createsuperuser

# Lista todas as rotas registradas na NinjaAPI
docker compose exec backend python manage.py show_urls

# Shell bash dentro do container do backend (debug rápido)
docker compose exec backend bash
```

## 🧪 Testes & Segurança

```bash
# Roda todos os testes do backend
docker compose exec backend pytest

# Roda testes em modo verboso (mostra cada caso)
docker compose exec backend pytest -v

# Roda só um arquivo específico
docker compose exec backend pytest tests/test_jwt_utils.py

# Roda só um teste específico
docker compose exec backend pytest tests/test_api.py::test_health_publico

# Análise estática de segurança com Bandit (mesmo do CI)
docker compose exec backend bandit -r . -ll -ii
```

## 🔐 Tokens JWT — geração manual para testar endpoints

```bash
# Gera um JWT válido de teste (substitua o JWT_SECRET pelo do .env)
docker compose exec backend python -c "
import jwt, time, os
print(jwt.encode(
    {'sub': 'henrique-1', 'email': 'henrique@tcc.com', 'name': 'Henrique', 'exp': time.time()+300},
    os.environ['JWT_SECRET'],
    algorithm='HS256'
))"

# Testar /api/me com o token gerado
curl -H "Authorization: Bearer COLE_O_TOKEN_AQUI" http://localhost:18000/api/me
```

## 🌐 Endpoints e portas

| Serviço | URL local |
|---|---|
| Backend (Django Ninja) | http://localhost:18000 |
| Health check público | http://localhost:18000/api/health |
| Rota protegida (SSO) | http://localhost:18000/api/me |
| Frontend (Vue 3) | http://localhost:5173 |
| ZAP daemon API | http://localhost:8090 |
| Postgres | localhost:5432 |

## 🔧 Frontend / Vue (dentro do container)

```bash
# Instala uma nova dependência (refletindo em package.json)
docker compose exec frontend npm install axios

# Rebuild para produção
docker compose exec frontend npm run build
```

## 📦 Git — fluxo do projeto

```bash
# Status, diff, log básicos
git status
git diff
git log --oneline -10

# Criar branch para uma nova feature/sessão
git checkout -b feature/oauth-callback

# Adicionar e commitar
git add .
git commit -m "feat: ..."

# Push da branch atual
git push origin HEAD
```

## 🌳 Branches da apresentação do TCC

| Branch | O que tem |
|---|---|
| `main` | Estado estável, pipeline verde |
| `demo/feature-segura` | PR limpo (refresh endpoint), pipeline verde, **mergeável** |
| `demo/vulneravel` | PR com 4 vulnerabilidades, pipeline vermelho, **bloqueado** |

```bash
# Alternar entre branches durante a demo
git checkout main
git checkout demo/feature-segura
git checkout demo/vulneravel

# Apos trocar, sempre reinicie o backend para carregar o novo codigo
docker compose restart backend     # se estiver no compose
kubectl rollout restart deploy/backend -n tcc-sso   # se estiver no k8s
```

## 🛡️ Pipeline CI — rodar localmente o que o GitHub Actions roda

```bash
# Stage 1: Bandit (análise estática)
docker compose exec backend bandit -r . -ll -ii

# Stage 2: Pytest
docker compose exec backend pytest

# Stage 3: ZAP Baseline (varredura dinâmica via container ZAP já no compose)
# O CI usa zaproxy/action-baseline; localmente dá pra simular com:
docker run --rm --network tcc-sso_default \
    zaproxy/zap-stable zap-baseline.py -t http://backend:8000
```

## 🔑 Keycloak

```bash
# Admin console (admin / admin)
# http://localhost:8180

# Verifica se o realm "tcc" está disponível (deve retornar JSON)
curl http://localhost:8180/realms/tcc/.well-known/openid-configuration

# Listar usuários do realm via API admin (requer pegar token admin antes)
curl -s -X POST http://localhost:8180/realms/master/protocol/openid-connect/token \
  -d "client_id=admin-cli" -d "grant_type=password" \
  -d "username=admin" -d "password=admin" | jq -r .access_token

# Re-importar o realm (apaga estado existente — útil em dev)
docker compose restart keycloak
```

Usuário de teste: **`henrique` / `tcc123`**

## 🩺 Troubleshooting rápido

```bash
# Porta já em uso? Descobrir quem ocupa (PowerShell)
Get-NetTCPConnection -LocalPort 18000 | Select OwningProcess

# Container não sobe? Ver últimos eventos
docker compose logs --tail=100 backend

# Banco corrompeu ou virou bagunça? Reset total
docker compose down -v && docker compose up -d

# Limpar imagens/volumes órfãos do Docker
docker system prune -f
```
