# ==============================================================================
# SCRIPT POWERSHELL PARA SUBIR A AWS ECS FARGATE + ECR + LOAD BALANCER
# Proyecto: RentMetrics · Computo en la Nube (IAD-2408)
# Alumno: Luis Antonio Hinojosa Corona
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 1. Verificando sesion de AWS..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "Sesion expirada. Iniciando 'aws login'..." -ForegroundColor Yellow
    Write-Host "Por favor autoriza la sesion en la ventana del navegador que se abrira..." -ForegroundColor Yellow
    aws login
}

$APP = "rentmetrics-luis"
$REGION = "us-east-2"
$PORT = 8080
$TAG = "v1"
$ACCOUNT = (aws sts get-caller-identity --query Account --output text).Trim()
$REPO = "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$APP"
aws configure set region $REGION

Write-Host "Cuenta AWS:      $ACCOUNT" -ForegroundColor Green
Write-Host "Region:          $REGION" -ForegroundColor Green
Write-Host "Repositorio ECR: $REPO" -ForegroundColor Green

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 2. Configurando Docker para ECR (Bypass Wincred)..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$dockerAwsDir = "$env:USERPROFILE\.docker-aws"
if (!(Test-Path $dockerAwsDir)) {
    New-Item -ItemType Directory -Path $dockerAwsDir -Force | Out-Null
}
'{"auths":{}}' | Out-File -FilePath "$dockerAwsDir\config.json" -Encoding ascii
$env:DOCKER_CONFIG = $dockerAwsDir

Write-Host "Autenticando Docker con Amazon ECR..." -ForegroundColor Cyan
$pass = (aws ecr get-login-password --region $REGION).Trim()
$pass | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 3. Construyendo, taggeando y subiendo imagen a ECR..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
docker build --platform linux/amd64 -t "${APP}:${TAG}" .
docker tag "${APP}:${TAG}" "${REPO}:${TAG}"
Write-Host "Subiendo imagen a ECR: ${REPO}:${TAG} ..." -ForegroundColor Cyan
docker push "${REPO}:${TAG}"

Write-Host ""
Write-Host ">>> CAPTURA 2 LISTA: La imagen se subio exitosamente a ECR <<<" -ForegroundColor Green
aws ecr list-images --repository-name $APP --region $REGION

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 4. Actualizando servicio ECS y esperando estabilizacion..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
aws ecs update-service --cluster "$APP-cluster" --service "$APP-svc" --force-new-deployment --region $REGION | Out-Null

Write-Host "Esperando a que las 2 tareas de Fargate inicien y queden estables (2 a 4 minutos)..." -ForegroundColor Yellow
aws ecs wait services-stable --cluster "$APP-cluster" --services "$APP-svc" --region $REGION
Write-Host ">>> SERVICIO ESTABLE EN AWS ECS <<<" -ForegroundColor Green

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 5. Verificando estado de salud en el Load Balancer..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$TG_ARN = (aws elbv2 describe-target-groups --names "$APP-tg" --region $REGION --query 'TargetGroups[0].TargetGroupArn' --output text).Trim()
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $REGION --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' --output table

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 6. URL Publica de tu aplicacion..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$ALB_ARN = (aws elbv2 describe-load-balancers --names "$APP-alb" --region $REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text).Trim()
$DNS_NAME = (aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --region $REGION --query 'LoadBalancers[0].DNSName' --output text).Trim()
$URL = "http://$DNS_NAME"

Write-Host "==================================================" -ForegroundColor Green
Write-Host " APLICACION DESPLEGADA EXITOSAMENTE EN AWS" -ForegroundColor Green
Write-Host " Tu app RentMetrics esta disponible en:" -ForegroundColor Green
Write-Host " $URL" -ForegroundColor Green
Write-Host " Endpoint de salud:" -ForegroundColor Green
Write-Host " $URL/health" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
