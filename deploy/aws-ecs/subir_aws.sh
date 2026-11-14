#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE RESOLUCIÓN Y SUBIDA A AWS ECS FARGATE + ECR + LOAD BALANCER
# Proyecto: RentMetrics · Computo en la Nube (IAD-2408)
# Alumno: Luis Antonio Hinojosa Corona
# ==============================================================================

set -e

export MSYS_NO_PATHCONV=1
export AWS_CLI_FILE_ENCODING=UTF-8

echo "=================================================="
echo " 1. Verificando sesion de AWS..."
echo "=================================================="
if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "La sesion ha expirado. Iniciando 'aws login'..."
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

echo "Cuenta AWS: $ACCOUNT"
echo "Region:     $REGION"
echo "Repositorio ECR: $REPO"

echo ""
echo "=================================================="
echo " 2. Configurando Docker para ECR (Bypasseando Wincred)..."
echo "=================================================="
mkdir -p ~/.docker-aws
echo '{"auths":{}}' > ~/.docker-aws/config.json
export DOCKER_CONFIG="$HOME/.docker-aws"

echo "Autenticando Docker con Amazon ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

echo ""
echo "=================================================="
echo " 3. Construyendo, taggeando y subiendo imagen a ECR..."
echo "=================================================="
cd "$(dirname "$0")"
docker build --platform linux/amd64 -t $APP:$TAG .
docker tag $APP:$TAG $REPO:$TAG
echo "Subiendo imagen a ECR: $REPO:$TAG ..."
docker push $REPO:$TAG

echo ""
echo ">>> CAPTURA 2 LISTA: La imagen se subio exitosamente a ECR <<<"
aws ecr list-images --repository-name $APP --region $REGION

echo ""
echo "=================================================="
echo " 4. Actualizando servicio ECS y esperando estabilizacion..."
echo "=================================================="
aws ecs update-service --cluster $APP-cluster --service $APP-svc --force-new-deployment --region $REGION >/dev/null

echo "Esperando a que las 2 tareas de Fargate inicien y queden estables (2 a 4 minutos)..."
aws ecs wait services-stable --cluster $APP-cluster --services $APP-svc --region $REGION
echo ">>> SERVICIO ESTABLE EN AWS ECS <<<"

echo ""
echo "=================================================="
echo " 5. Verificando estado de salud en el Load Balancer..."
echo "=================================================="
TG_ARN=$(aws elbv2 describe-target-groups --names $APP-tg --region $REGION --query 'TargetGroups[0].TargetGroupArn' --output text)
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $REGION \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
  --output table

echo ""
echo "=================================================="
echo " 6. URL Publica de tu aplicacion..."
echo "=================================================="
ALB_ARN=$(aws elbv2 describe-load-balancers --names $APP-alb --region $REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text)
URL=http://$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --region $REGION --query 'LoadBalancers[0].DNSName' --output text)

echo "=================================================="
echo " APLICACION DESPLEGADA EXITOSAMENTE EN AWS"
echo " Tu app RentMetrics esta disponible en:"
echo " $URL"
echo " Endpoint de salud:"
echo " $URL/health"
echo "=================================================="
