#!/usr/bin/env bash
# ==============================================================================
# GUIA COMPLETA DE DESPLIEGUE EN AWS ECS FARGATE + ECR + LOAD BALANCER
# Proyecto: RentMetrics · Computo en la Nube (IAD-2408) · TecNM
# Alumno: Luis Antonio Hinojosa Corona
# ==============================================================================
# NOTA IMPORTANTE: Ejecuta estos comandos en GIT BASH (no CMD ni PowerShell).
# Asegurate de tener Docker Desktop abierto y en estado "Engine running".
# ==============================================================================

# ------------------------------------------------------------------------------
# PASO 4: Iniciar sesion en AWS y tomar EVIDENCIA 1
# ------------------------------------------------------------------------------
# Comprueba tus credenciales activas:
aws sts get-caller-identity

# Si salio error "NoCredentials", ejecuta login en el navegador:
# aws login
# (Si se queda trabado en region, usa: aws configure set region us-east-1 && aws login)

# >>> TOMA CAPTURA 1 AQUI: Salida de aws sts get-caller-identity <<<


# ------------------------------------------------------------------------------
# PASO 5: Descubrir region permitida
# ------------------------------------------------------------------------------
for r in us-east-1 us-east-2 us-west-2; do
  if aws ecr describe-repositories --region $r >/dev/null 2>&1 && \
     aws ecs list-clusters --region $r >/dev/null 2>&1; then
    echo "$r -> PERMITIDA"
  else
    echo "$r -> BLOQUEADA"
  fi
done

# Anota la region que salio PERMITIDA (por defecto suele ser us-east-2 o us-east-1).


# ------------------------------------------------------------------------------
# PASO 6: Navegar a la carpeta y crear variables en vars.sh
# ------------------------------------------------------------------------------
# Entra al directorio donde estan Dockerfile y server.js:
# cd ~/Documents/miapp   # O si usas el proyecto:
cd "$(pwd)"

cat > vars.sh <<'FIN'
export MSYS_NO_PATHCONV=1
export AWS_CLI_FILE_ENCODING=UTF-8
guardar() { for v in "$@"; do echo "export $v=\"${!v}\"" >> vars.sh; done; }
FIN
source vars.sh

export APP=rentmetrics-luis
export ALUMNO="Luis Antonio Hinojosa Corona"
export REGION=us-east-2     # <-- Cambia a tu region PERMITIDA si es diferente
export PORT=8080
export TAG=v1
export AWS_DEFAULT_REGION=$REGION
export ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export REPO=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$APP
aws configure set region $REGION
guardar APP ALUMNO REGION AWS_DEFAULT_REGION PORT TAG ACCOUNT REPO
echo "Repositorio configurado: $REPO"


# ------------------------------------------------------------------------------
# PASO 7: Prueba local con Docker
# ------------------------------------------------------------------------------
docker build --platform linux/amd64 -t $APP:$TAG .
docker run -d --name prueba -p 9090:8080 -e ALUMNO="$ALUMNO" $APP:$TAG
sleep 3
curl -s http://localhost:9090/health; echo

# Abre en tu navegador: http://localhost:9090
# Limpia el contenedor de prueba:
docker rm -f prueba


# ------------------------------------------------------------------------------
# PASO 8: Crear ECR y subir imagen (con solucion 8B para Docker en Windows)
# ------------------------------------------------------------------------------
aws ecr create-repository --repository-name $APP \
  --image-scanning-configuration scanOnPush=true \
  --query 'repository.repositoryUri' --output text

# Crear atajo dk para evitar el error de credenciales de Windows:
mkdir -p ~/.docker-aws
echo '{"auths":{}}' > ~/.docker-aws/config.json
cat >> vars.sh <<'FIN'
export DOCKER_CONFIG=~/.docker-aws
DOCKER_BIN="/c/Program Files/Docker/Docker/resources/bin"
PATH_SIN_DOCKER=$(echo "$PATH" | tr ':' '\n' | grep -vi docker | paste -sd:)
dk() { PATH="$PATH_SIN_DOCKER" "$DOCKER_BIN/docker.exe" "$@"; }
FIN
source vars.sh

# Login y Push con dk:
aws ecr get-login-password --region $REGION | dk login --username AWS \
  --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

dk tag $APP:$TAG $REPO:$TAG
dk push $REPO:$TAG

# >>> TOMA CAPTURA 2 AQUI: Push terminado con v1: digest: sha256:... <<<


# ------------------------------------------------------------------------------
# PASO 9: Red y Security Groups
# ------------------------------------------------------------------------------
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
  --query 'Vpcs[0].VpcId' --output text)
SUBNETS_SP=$(aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=$VPC_ID Name=default-for-az,Values=true \
  --query 'Subnets[*].SubnetId' --output text)
SUBNETS_CSV=$(echo $SUBNETS_SP | tr ' ' ',')
guardar VPC_ID SUBNETS_SP SUBNETS_CSV
echo "VPC: $VPC_ID"
echo "Subredes: $SUBNETS_CSV"

ALB_SG=$(aws ec2 create-security-group --group-name $APP-alb-sg \
  --description "ALB $APP" --vpc-id $VPC_ID --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $ALB_SG \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null

APP_SG=$(aws ec2 create-security-group --group-name $APP-app-sg \
  --description "App $APP" --vpc-id $VPC_ID --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $APP_SG \
  --protocol tcp --port $PORT --source-group $ALB_SG >/dev/null

guardar ALB_SG APP_SG
echo "SG del ALB: $ALB_SG"
echo "SG de la app: $APP_SG"


# ------------------------------------------------------------------------------
# PASO 10: Crear Application Load Balancer
# ------------------------------------------------------------------------------
ALB_ARN=$(aws elbv2 create-load-balancer --name $APP-alb \
  --subnets $SUBNETS_SP --security-groups $ALB_SG \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

TG_ARN=$(aws elbv2 create-target-group --name $APP-tg \
  --protocol HTTP --port $PORT --vpc-id $VPC_ID --target-type ip \
  --health-check-path /health --health-check-interval-seconds 15 \
  --healthy-threshold-count 2 \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

L80_ARN=$(aws elbv2 create-listener --load-balancer-arn $ALB_ARN \
  --protocol HTTP --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --query 'Listeners[0].ListenerArn' --output text)

guardar ALB_ARN TG_ARN L80_ARN
echo "ALB: $ALB_ARN"
echo "Target group: $TG_ARN"
echo "Listener: $L80_ARN"


# ------------------------------------------------------------------------------
# PASO 11: Rol de ejecucion IAM y Cluster ECS
# ------------------------------------------------------------------------------
cat > trust.json <<'FIN'
{ "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow",
  "Principal": { "Service": "ecs-tasks.amazonaws.com" },
  "Action": "sts:AssumeRole" }] }
FIN

if aws iam create-role --role-name $APP-exec-role \
  --assume-role-policy-document file://trust.json >/dev/null 2>&1; then
  aws iam attach-role-policy --role-name $APP-exec-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
  EXEC_ROLE=$(aws iam get-role --role-name $APP-exec-role \
    --query Role.Arn --output text)
  ROL_CREADO=si
  echo "Rol creado. Esperando 15 s a que AWS lo active..."; sleep 15
else
  echo "No se pudo crear el rol. Buscando uno existente..."
  FILTRO="Roles[?RoleName=='ecsTaskExecutionRole' || RoleName=='LabRole'].Arn | [0]"
  EXEC_ROLE=$(aws iam list-roles --query "$FILTRO" --output text)
  ROL_CREADO=no
fi
guardar EXEC_ROLE ROL_CREADO
echo "Rol de ejecucion: $EXEC_ROLE"

aws logs create-log-group --log-group-name /ecs/$APP
aws ecs create-cluster --cluster-name $APP-cluster \
  --query 'cluster.status' --output text


# ------------------------------------------------------------------------------
# PASO 12: Registrar Task Definition (la receta)
# ------------------------------------------------------------------------------
cat > taskdef.json <<FIN
{
  "family": "$APP",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "runtimePlatform": { "operatingSystemFamily": "LINUX", "cpuArchitecture": "X86_64" },
  "executionRoleArn": "$EXEC_ROLE",
  "containerDefinitions": [{
    "name": "$APP",
    "image": "$REPO:$TAG",
    "essential": true,
    "portMappings": [{ "containerPort": $PORT, "protocol": "tcp" }],
    "environment": [
      { "name": "ALUMNO", "value": "$ALUMNO" },
      { "name": "VERSION", "value": "$TAG" }
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

aws ecs register-task-definition --cli-input-json file://taskdef.json \
  --query 'taskDefinition.taskDefinitionArn' --output text


# ------------------------------------------------------------------------------
# PASO 13: Crear el Servicio ECS (¡Tu app en internet!)
# ------------------------------------------------------------------------------
NETCFG="awsvpcConfiguration={subnets=[$SUBNETS_CSV],"
NETCFG+="securityGroups=[$APP_SG],assignPublicIp=ENABLED}"

aws ecs create-service --cluster $APP-cluster --service-name $APP-svc \
  --task-definition $APP --desired-count 2 --launch-type FARGATE \
  --network-configuration "$NETCFG" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=$APP,containerPort=$PORT" \
  --health-check-grace-period-seconds 60 \
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true}" \
  --query 'service.status' --output text

echo "Esperando a que el servicio quede estable (2 a 5 minutos)..."
aws ecs wait services-stable --cluster $APP-cluster --services $APP-svc \
  && echo "SERVICIO ESTABLE"

aws elbv2 describe-target-health --target-group-arn $TG_ARN \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
  --output table

# >>> TOMA CAPTURA 3 AQUI: Tabla de describe-target-health con dos 'healthy' <<<

URL=http://$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' --output text)
guardar URL
echo "Tu app esta en: $URL"

# Abre la URL en el navegador.
# >>> TOMA CAPTURA 4 AQUI: Navegador con tu URL mostrando tu nombre y 2 recargas con diferente contenedor <<<


# ------------------------------------------------------------------------------
# PASO 14: Publicar Version 2 (Rolling Update)
# ------------------------------------------------------------------------------
# Modifica server.js para cambiar el texto a: "¡Ya voy en la versión 2!"
sed -i 's/¡Mi app corre en AWS!/¡Ya voy en la versión 2!/g' server.js

export TAG=v2
guardar TAG
docker build --platform linux/amd64 -t $APP:$TAG .
dk tag $APP:$TAG $REPO:$TAG
dk push $REPO:$TAG

# Registrar taskdef revision 2:
cat > taskdef.json <<FIN
{
  "family": "$APP",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "runtimePlatform": { "operatingSystemFamily": "LINUX", "cpuArchitecture": "X86_64" },
  "executionRoleArn": "$EXEC_ROLE",
  "containerDefinitions": [{
    "name": "$APP",
    "image": "$REPO:$TAG",
    "essential": true,
    "portMappings": [{ "containerPort": $PORT, "protocol": "tcp" }],
    "environment": [
      { "name": "ALUMNO", "value": "$ALUMNO" },
      { "name": "VERSION", "value": "$TAG" }
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
aws ecs register-task-definition --cli-input-json file://taskdef.json \
  --query 'taskDefinition.taskDefinitionArn' --output text

aws ecs update-service --cluster $APP-cluster --service $APP-svc \
  --task-definition $APP --query 'service.taskDefinition' --output text
aws ecs wait services-stable --cluster $APP-cluster --services $APP-svc \
  && echo "VERSION $TAG EN LINEA"

# Recarga la URL en el navegador.
# >>> TOMA CAPTURA 5 AQUI: Navegador mostrando "Versión: v2" <<<


# ------------------------------------------------------------------------------
# PASO 15: Borrar todo (OBLIGATORIO para no generar costos)
# ------------------------------------------------------------------------------
echo "Iniciando limpieza total de recursos AWS..."

echo "1/6 Servicio y cluster"
aws ecs update-service --cluster $APP-cluster --service $APP-svc --desired-count 0 >/dev/null
aws ecs delete-service --cluster $APP-cluster --service $APP-svc --force >/dev/null
aws ecs wait services-inactive --cluster $APP-cluster --services $APP-svc
aws ecs delete-cluster --cluster $APP-cluster >/dev/null

TDS=$(aws ecs list-task-definitions --family-prefix $APP --query 'taskDefinitionArns[]' --output text)
for td in $TDS; do
  aws ecs deregister-task-definition --task-definition $td >/dev/null
done

echo "2/6 Load Balancer"
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
aws elbv2 wait load-balancers-deleted --load-balancer-arns $ALB_ARN
aws elbv2 delete-target-group --target-group-arn $TG_ARN

echo "3/6 Security groups"
for sg in $APP_SG $ALB_SG; do
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if aws ec2 delete-security-group --group-id $sg 2>/dev/null; then
      echo " $sg borrado"; break
    fi
    echo " $sg aun en uso, reintento en 20 s..."; sleep 20
  done
done

echo "4/6 Repositorio de imagenes"
aws ecr delete-repository --repository-name $APP --force >/dev/null

echo "5/6 Logs"
aws logs delete-log-group --log-group-name /ecs/$APP

echo "6/6 Rol"
if [ "$ROL_CREADO" = "si" ]; then
  aws iam detach-role-policy --role-name $APP-exec-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
  aws iam delete-role --role-name $APP-exec-role
fi

echo "LISTO: todo borrado."
# >>> TOMA CAPTURA 6 AQUI: Terminal con LISTO: todo borrado. <<<
