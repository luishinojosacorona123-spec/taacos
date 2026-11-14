#!/usr/bin/env bash
# ==============================================================================
# DESPLIEGUE OFICIAL: RENTMETRICS STREAMLIT EN AWS ECS FARGATE + ALB
# Proyecto: RentMetrics · Gestion Inteligente de Arrendamientos
# Alumno: Luis Antonio Hinojosa Corona
# ==============================================================================

set -e

export MSYS_NO_PATHCONV=1
export AWS_CLI_FILE_ENCODING=UTF-8

# Determinar directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=================================================="
echo " 1. Verificando sesion de AWS..."
echo "=================================================="
if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "La sesion de AWS ha expirado. Iniciando 'aws login'..."
  echo "Por favor autoriza la sesion en la ventana del navegador que se abrira..."
  aws login
fi

export APP=rentmetrics-luis
export REGION=us-east-2
export PORT=8080
export TAG=v1
export ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export REPO=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$APP
aws configure set region $REGION

echo "Cuenta AWS:      $ACCOUNT"
echo "Region:          $REGION"
echo "Repositorio ECR: $REPO"

echo ""
echo "=================================================="
echo " 2. Configurando Docker para ECR (Bypass Wincred)..."
echo "=================================================="
mkdir -p ~/.docker-aws
echo '{"auths":{}}' > ~/.docker-aws/config.json
export DOCKER_CONFIG="$HOME/.docker-aws"

echo "Autenticando Docker con Amazon ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

echo ""
echo "=================================================="
echo " 3. Construyendo imagen de RentMetrics Streamlit..."
echo "=================================================="
cd "$REPO_ROOT"
echo "Directorio de construccion: $(pwd)"
docker build --platform linux/amd64 -f deploy/aws-ecs/Dockerfile -t $APP:$TAG .
docker tag $APP:$TAG $REPO:$TAG

echo "Subiendo imagen a ECR: $REPO:$TAG ..."
docker push $REPO:$TAG

echo ">>> Imagen de RentMetrics subida exitosamente a Amazon ECR <<<"
aws ecr list-images --repository-name $APP --region $REGION

echo ""
echo "=================================================="
echo " 4. Configurando Health Check de Streamlit en ALB..."
echo "=================================================="
TG_ARN=$(aws elbv2 describe-target-groups --names $APP-tg --region $REGION --query 'TargetGroups[0].TargetGroupArn' --output text)
aws elbv2 modify-target-group --target-group-arn $TG_ARN \
  --health-check-path /_stcore/health \
  --matcher HttpCode=200 \
  --region $REGION >/dev/null
echo "Health Check actualizado a /_stcore/health (Matcher: 200)"

echo ""
echo "=================================================="
echo " 5. Actualizando Task Definition en ECS (1GB RAM)..."
echo "=================================================="
EXEC_ROLE=$(aws iam list-roles --query "Roles[?RoleName=='$APP-exec-role' || RoleName=='ecsTaskExecutionRole' || RoleName=='LabRole'].Arn | [0]" --output text)

cat > "$SCRIPT_DIR/taskdef_streamlit.json" <<FIN
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
    "image": "$REPO:$TAG",
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
FIN

aws ecs register-task-definition --cli-input-json "file://$SCRIPT_DIR/taskdef_streamlit.json" --region $REGION >/dev/null

echo "Actualizando servicio en el cluster $APP-cluster..."
aws ecs update-service --cluster $APP-cluster --service $APP-svc \
  --task-definition $APP --force-new-deployment --region $REGION >/dev/null

echo "Esperando a que las tareas de Fargate arranquen RentMetrics (2 a 4 minutos)..."
aws ecs wait services-stable --cluster $APP-cluster --services $APP-svc --region $REGION
echo ">>> SERVICIO ESTABLE: RENTMETRICS EN EJECUCION <<<"

echo ""
echo "=================================================="
echo " 6. Verificando estado de salud en el Load Balancer..."
echo "=================================================="
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $REGION \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
  --output table

echo ""
echo "=================================================="
echo " 7. URL Publica de tu aplicacion en Amazon Web Services..."
echo "=================================================="
ALB_ARN=$(aws elbv2 describe-load-balancers --names $APP-alb --region $REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text)
URL=http://$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --region $REGION --query 'LoadBalancers[0].DNSName' --output text)

echo "=================================================="
echo " RENTMETRICS DESPLEGADO EXITOSAMENTE EN AWS"
echo " Tu aplicacion esta disponible en:"
echo " $URL"
echo " Endpoint de salud:"
echo " $URL/_stcore/health"
echo "=================================================="
