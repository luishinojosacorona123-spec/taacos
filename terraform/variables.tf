variable "aws_region" {
  description = "Region de despliegue en AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre base del proyecto"
  type        = string
  default     = "rentmetrics"
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
  default     = "production"
}

variable "bucket_name" {
  description = "Nombre unico del bucket S3 para el Data Lake"
  type        = string
  default     = "rentmetrics-datalake-prod-2026"
}
