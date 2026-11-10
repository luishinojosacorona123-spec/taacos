terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Entregable  = "E3"
    }
  }
}

# ==============================================================================
# 1. ALMACENAMIENTO: BUCKET S3 PARA DATA LAKE (ZONAS RAW/ Y CLEAN/)
# ==============================================================================

resource "aws_s3_bucket" "datalake" {
  bucket        = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "datalake_versioning" {
  bucket = aws_s3_bucket.datalake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "datalake_crypto" {
  bucket = aws_s3_bucket.datalake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "datalake_block_public" {
  bucket = aws_s3_bucket.datalake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Prefijos obligatorios en el Data Lake
resource "aws_s3_object" "prefix_raw" {
  bucket = aws_s3_bucket.datalake.id
  key    = "raw/"
}

resource "aws_s3_object" "prefix_clean" {
  bucket = aws_s3_bucket.datalake.id
  key    = "clean/"
}


# ==============================================================================
# 2. MIDDLEWARE DE MENSAJERIA: SQS + DEAD LETTER QUEUE (DLQ)
# ==============================================================================

# Dead Letter Queue para aislamiento de mensajes corruptos o reintentos agotados
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-ingesta-dlq"
  message_retention_seconds = 1209600 # 14 dias
}

# Cola principal con politica de redrive hacia la DLQ (maximo 3 reintentos)
resource "aws_sqs_queue" "ingesta_queue" {
  name                       = "${var.project_name}-ingesta-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600 # 4 dias

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}


# ==============================================================================
# 3. IDENTIDAD Y ACCESO (IAM): PRINCIPIO DE MENOR PRIVILEGIO
# ==============================================================================

# Rol para el Microservicio de Ingesta (API)
resource "aws_iam_role" "api_role" {
  name = "${var.project_name}-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["ecs-tasks.amazonaws.com", "apprunner.amazonaws.com"]
        }
      }
    ]
  })
}

# Politica de Menor Privilegio para la API: Solo escribir en raw/ y enviar a SQS
resource "aws_iam_policy" "api_policy" {
  name        = "${var.project_name}-api-policy"
  description = "Permisos minimos para la API de Ingesta"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3RawWriteOnly"
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.datalake.arn}/raw/*"
      },
      {
        Sid    = "AllowSQSSendOnly"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.ingesta_queue.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_attach" {
  role       = aws_iam_role.api_role.name
  policy_arn = aws_iam_policy.api_policy.arn
}

# Rol para el Worker Asincrono / Serverless Lambda
resource "aws_iam_role" "worker_role" {
  name = "${var.project_name}-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
        }
      }
    ]
  })
}

# Politica de Menor Privilegio para el Worker: Leer raw/, escribir clean/, consumir cola y enviar a DLQ
resource "aws_iam_policy" "worker_policy" {
  name        = "${var.project_name}-worker-policy"
  description = "Permisos minimos para el Worker de Limpieza y Persistencia"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3ReadRawWriteClean"
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.datalake.arn}/raw/*"
      },
      {
        Sid    = "AllowS3WriteClean"
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.datalake.arn}/clean/*"
      },
      {
        Sid    = "AllowSQSConsume"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = aws_sqs_queue.ingesta_queue.arn
      },
      {
        Sid    = "AllowSendToDLQ"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.dlq.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_attach" {
  role       = aws_iam_role.worker_role.name
  policy_arn = aws_iam_policy.worker_policy.arn
}
