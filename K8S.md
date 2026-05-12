# ☸️ Kubernetes + ArgoCD (GitOps)

Esta etapa fecha o ciclo CD do projeto: depois que o pipeline CI passa, o **ArgoCD** detecta mudanças nos manifestos do Git e sincroniza o cluster automaticamente.

---

## 🎯 O que esta sessão entrega

| Componente | Função |
|---|---|
| `k8s/` | Manifestos Kubernetes (Namespace, ConfigMap, Secret, Postgres, Keycloak, Backend, Frontend) |
| `argocd/application.yaml` | Application CR que faz ArgoCD monitorar o repo |
| `k8s/setup.ps1` | Script PowerShell que sobe cluster + ArgoCD + Application em um comando |

---

## 📦 Pré-requisitos

1. **Docker Desktop** — já instalado e rodando
2. **kubectl** — já vem com Docker Desktop (`kubectl version --client`)
3. **k3d** — instalar com **uma** das opções:

   ```powershell
   # Opção A: Chocolatey (recomendado)
   choco install k3d

   # Opção B: Scoop
   scoop install k3d

   # Opção C: download direto (veja https://k3d.io)
   ```

Conferir: `k3d version` deve responder.

---

## 🚀 Subir o ambiente em 1 comando

Na raiz do projeto:

```powershell
.\k8s\setup.ps1
```

O script:
1. Builda as imagens locais (`tcc-sso-backend`, `tcc-sso-frontend`)
2. Cria o cluster k3d `tcc-sso` com portas mapeadas
3. Importa as imagens para dentro do cluster (sem precisar de registry)
4. Instala ArgoCD no namespace `argocd`
5. Expõe ArgoCD UI em https://localhost:28443
6. Aplica o `Application` apontando para `k8s/` deste repo
7. Imprime a senha admin do ArgoCD e os endpoints da aplicação

> ⚠️ **Pare o `docker compose` antes** se ele estiver rodando — as portas conflitariam.
> ```powershell
> docker compose down
> ```

---

## 🌐 Endpoints depois que ArgoCD sincronizar

| Serviço | URL |
|---|---|
| Frontend Vue | http://localhost:25173 |
| Backend Django | http://localhost:28000/api/health |
| Keycloak | http://localhost:28180  (admin / admin) |
| ArgoCD UI | https://localhost:28443  (admin / `<senha do output do setup>`) |

Login no app via SSO: `henrique` / `tcc123` (mesmo usuário do compose).

---

## 🔍 Acompanhar a sincronização

```powershell
# Ver o estado da Application (Synced / OutOfSync / Healthy / Progressing)
kubectl get application tcc-sso -n argocd -w

# Ver pods subindo
kubectl get pods -n tcc-sso -w

# Logs do backend
kubectl logs -n tcc-sso -l app=backend -f

# Descrever a Application (mostra erros de sync)
kubectl describe application tcc-sso -n argocd
```

---

## 🔁 Fluxo GitOps na prática (demo)

```
┌──────────────────┐    git push    ┌──────────────────┐
│  Voce edita      ├───────────────▶│   GitHub repo    │
│  k8s/04-backend  │                │   (main branch)  │
└──────────────────┘                └────────┬─────────┘
                                             │
                              ArgoCD faz poll a cada 3min
                              (ou via webhook do GitHub)
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  ArgoCD detecta  │
                                    │  drift no cluster│
                                    └────────┬─────────┘
                                             │
                              syncPolicy.automated = true
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  kubectl apply   │
                                    │  (automatico)    │
                                    └──────────────────┘
```

**Para demonstrar ao vivo:**
1. Editar `k8s/04-backend.yaml` mudando `replicas: 1` → `replicas: 2`
2. `git commit` + `git push`
3. Em ~3min (ou força com **Refresh** na UI), ArgoCD sincroniza
4. `kubectl get pods -n tcc-sso` mostra 2 pods de backend

---

## 🛠️ Comandos úteis (k8s)

```powershell
# Status geral do projeto
kubectl get all -n tcc-sso

# Forcar sync imediato pela CLI do ArgoCD (se instalada)
argocd app sync tcc-sso

# Port-forward direto (sem usar NodePort)
kubectl port-forward -n tcc-sso svc/backend 28000:8000

# Reiniciar um deployment
kubectl rollout restart deployment/backend -n tcc-sso

# Deletar tudo e recomecar
kubectl delete application tcc-sso -n argocd
kubectl delete namespace tcc-sso

# Destruir o cluster inteiro
k3d cluster delete tcc-sso
```

---

## 🔐 Sobre os Secrets

O arquivo `k8s/01-config.yaml` tem um `Secret` com valores em **stringData** (texto plano). Isso é **intencional para o projeto acadêmico** — um repositório real usaria:

- **Sealed Secrets** (Bitnami) — criptografa o secret com a chave pública do cluster
- **External Secrets Operator** + Vault/AWS Secrets Manager
- **SOPS** com chaves GPG/age

Em qualquer dessas opções, o segredo encriptado fica no Git e só o cluster consegue decriptar — sem expor senhas no histórico.

Mencionar isso na apresentação reforça que a arquitetura escolhida tem caminho claro de evolução pra produção.

---

## 🆘 Troubleshooting

**Pods do backend em `CrashLoopBackOff`:**
```powershell
kubectl logs -n tcc-sso -l app=backend --previous
```
Causa comum: imagem não foi importada. Rode `k3d image import tcc-sso-backend:latest -c tcc-sso`.

**Keycloak demora pra subir:**
Normal — primeira inicialização leva ~30-60s. Acompanhe com `kubectl logs -n tcc-sso -l app=keycloak -f`.

**ArgoCD mostra "OutOfSync" mas não sincroniza:**
Force manualmente: `kubectl patch application tcc-sso -n argocd --type merge -p '{"operation":{"sync":{}}}'`.

**Cluster trava ou ficou em estado estranho:**
```powershell
k3d cluster delete tcc-sso
.\k8s\setup.ps1
```
