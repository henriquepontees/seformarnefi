# Setup completo do ambiente Kubernetes + ArgoCD para o projeto TCC.
# Pre-requisito: Docker Desktop + kubectl + k3d instalados.
#
# Uso: .\k8s\setup.ps1  (na raiz do projeto)

$ErrorActionPreference = "Stop"
$CLUSTER = "tcc-sso"

Write-Host "=== 1/7 Verificando pre-requisitos ===" -ForegroundColor Cyan
foreach ($cmd in @("docker", "kubectl", "k3d")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "$cmd nao encontrado no PATH. Veja K8S.md para instrucoes."
        exit 1
    }
}

Write-Host "=== 2/7 Build das imagens locais ===" -ForegroundColor Cyan
docker compose build backend frontend

Write-Host "=== 3/7 Criando cluster k3d ===" -ForegroundColor Cyan
$existing = k3d cluster list -o json | ConvertFrom-Json | Where-Object { $_.name -eq $CLUSTER }
if ($existing) {
    Write-Host "Cluster '$CLUSTER' ja existe, reutilizando." -ForegroundColor Yellow
} else {
    # Portas: 25173 (frontend), 28000 (backend), 28180 (keycloak), 28443 (argocd UI)
    k3d cluster create $CLUSTER `
        --port "25173:30173@loadbalancer" `
        --port "28000:30800@loadbalancer" `
        --port "28180:30180@loadbalancer" `
        --port "28443:30443@loadbalancer" `
        --agents 1
}

Write-Host "=== 4/7 Importando imagens locais para o cluster ===" -ForegroundColor Cyan
k3d image import tcc-sso-backend:latest tcc-sso-frontend:latest -c $CLUSTER

Write-Host "=== 5/7 Instalando ArgoCD ===" -ForegroundColor Cyan
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

Write-Host "Expondo ArgoCD UI via NodePort 30443..."
kubectl patch svc argocd-server -n argocd -p '{\"spec\":{\"type\":\"NodePort\",\"ports\":[{\"port\":443,\"targetPort\":8080,\"nodePort\":30443}]}}'

Write-Host "Aguardando ArgoCD subir (pode demorar ~1 min)..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

Write-Host "=== 6/7 Aplicando Application do ArgoCD ===" -ForegroundColor Cyan
kubectl apply -f argocd/application.yaml

Write-Host "=== 7/7 Pronto ===" -ForegroundColor Green
Write-Host ""
Write-Host "ArgoCD UI:  https://localhost:28443" -ForegroundColor White
Write-Host "  Usuario:  admin"
Write-Host "  Senha:    $((kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}') | ForEach-Object { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) })"
Write-Host ""
Write-Host "Aplicacao (apos ArgoCD sincronizar):" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:25173"
Write-Host "  Backend:   http://localhost:28000/api/health"
Write-Host "  Keycloak:  http://localhost:28180  (admin/admin)"
Write-Host ""
Write-Host "Acompanhar a sincronizacao:"
Write-Host "  kubectl get application tcc-sso -n argocd -w"
Write-Host "  kubectl get pods -n tcc-sso -w"
