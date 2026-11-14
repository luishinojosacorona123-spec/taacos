# ==============================================================================
# DESPLIEGUE OFICIAL POWERSHELL: RENTMETRICS STREAMLIT EN AWS ECS FARGATE + ALB
# Proyecto: RentMetrics · Gestion Inteligente de Arrendamientos
# Alumno: Luis Antonio Hinojosa Corona
# ==============================================================================

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path (Split-Path $SCRIPT_DIR -Parent) -Parent

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
Write-Host " 2. Configurando Docker y liberando espacio..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$dockerAwsDir = "$env:USERPROFILE\.docker-aws"
if (!(Test-Path $dockerAwsDir)) {
    New-Item -ItemType Directory -Path $dockerAwsDir -Force | Out-Null
}
$env:DOCKER_CONFIG = $dockerAwsDir

Write-Host "Liberando cache antigua de Docker..." -ForegroundColor Gray
try { docker builder prune -f | Out-Null } catch {}

Write-Host "Autenticando Docker con Amazon ECR (inyeccion directa de credenciales)..." -ForegroundColor Cyan
$pass = (aws ecr get-login-password --region $REGION).Trim()
$authBytes = [System.Text.Encoding]::ASCII.GetBytes("AWS:$pass")
$authB64 = [Convert]::ToBase64String($authBytes)

$dockerConfigJson = @"
{
  "auths": {
    "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com": {
      "auth": "$authB64"
    }
  }
}
"@
[System.IO.File]::WriteAllText("$dockerAwsDir\config.json", $dockerConfigJson, [System.Text.Encoding]::ASCII)
Write-Host "Credenciales ECR configuradas con exito." -ForegroundColor Green

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 3. Construyendo imagen de RentMetrics Streamlit..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Set-Location -Path $REPO_ROOT
Write-Host "Directorio de construccion: $(Get-Location)" -ForegroundColor Gray
docker build --platform linux/amd64 -f "$SCRIPT_DIR\Dockerfile" -t "${APP}:${TAG}" .
docker tag "${APP}:${TAG}" "${REPO}:${TAG}"

Write-Host "Subiendo imagen a ECR: ${REPO}:${TAG} ..." -ForegroundColor Cyan
docker push "${REPO}:${TAG}"

Write-Host ">>> Imagen de RentMetrics subida exitosamente a Amazon ECR <<<" -ForegroundColor Green
aws ecr list-images --repository-name $APP --region $REGION

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 4. Configurando Health Check de Streamlit en ALB..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$TG_ARN = (aws elbv2 describe-target-groups --names "$APP-tg" --region $REGION --query 'TargetGroups[0].TargetGroupArn' --output text).Trim()
aws elbv2 modify-target-group --target-group-arn $TG_ARN `
  --health-check-path "/_stcore/health" `
  --matcher "HttpCode=200" `
  --region $REGION | Out-Null
Write-Host "Health Check actualizado a /_stcore/health (Matcher: 200)" -ForegroundColor Green

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 5. Actualizando Task Definition en ECS (1GB RAM)..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$EXEC_ROLE = (aws iam list-roles --query "Roles[?RoleName=='$APP-exec-role' || RoleName=='ecsTaskExecutionRole' || RoleName=='LabRole'].Arn | [0]" --output text).Trim()

$taskDefContent = @"
{
  "family": "$APP",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "runtimePlatform": { "operatingSystemFamily": "LINUX", "cpuArchitecture": "X86_64" },
  "executionRoleArn": "$EXEC_ROLE",
  "containerDefinitions": [{
    "name": "$APP",
    "image": "${REPO}:${TAG}",
    "essential": true,
    "portMappings": [{ "containerPort": $PORT, "protocol": "tcp" }],
    "environment": [
      { "name": "PORT", "value": "$PORT" },
      { "name": "STREAMLIT_SERVER_PORT", "value": "$PORT" },
      { "name": "STREAMLIT_SERVER_ADDRESS", "value": "0.0.0.0" },
      { "name": "STREAMLIT_SERVER_HEADLESS", "value": "true" },
      { "name": "STREAMLIT_SERVER_ENABLE_CORS", "value": "false" },
      { "name": "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION", "value": "false" }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/$APP",
        "awslogs-region": "$REGION",
        "awslogs-stream-prefix": "app"
      }
    }
  }]
}
"@

$taskDefPath = "$SCRIPT_DIR\taskdef_streamlit.json"
[System.IO.File]::WriteAllText($taskDefPath, $taskDefContent, [System.Text.Encoding]::ASCII)
aws ecs register-task-definition --cli-input-json "file://$taskDefPath" --region $REGION | Out-Null

Write-Host "Actualizando servicio en el cluster $APP-cluster..." -ForegroundColor Cyan
aws ecs update-service --cluster "$APP-cluster" --service "$APP-svc" `
  --task-definition $APP --force-new-deployment --region $REGION | Out-Null

Write-Host "Esperando a que las tareas de Fargate arranquen RentMetrics (2 a 4 minutos)..." -ForegroundColor Yellow
aws ecs wait services-stable --cluster "$APP-cluster" --services "$APP-svc" --region $REGION
Write-Host ">>> SERVICIO ESTABLE: RENTMETRICS EN EJECUCION <<<" -ForegroundColor Green

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 6. Verificando estado de salud en el Load Balancer..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $REGION `
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' --output table

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 7. URL Publica de tu aplicacion en Amazon Web Services..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$ALB_ARN = (aws elbv2 describe-load-balancers --names "$APP-alb" --region $REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text).Trim()
$DNS_NAME = (aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --region $REGION --query 'LoadBalancers[0].DNSName' --output text).Trim()
$URL = "http://$DNS_NAME"

Write-Host "==================================================" -ForegroundColor Green
Write-Host " RENTMETRICS DESPLEGADO EXITOSAMENTE EN AWS" -ForegroundColor Green
Write-Host " Tu aplicacion esta disponible en:" -ForegroundColor Green
Write-Host " $URL" -ForegroundColor Green
Write-Host " Endpoint de salud:" -ForegroundColor Green
Write-Host " $URL/_stcore/health" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
