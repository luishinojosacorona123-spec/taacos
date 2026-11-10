output "s3_bucket_name" {
  description = "Nombre del bucket S3 creado"
  value       = aws_s3_bucket.datalake.id
}

output "s3_bucket_arn" {
  description = "ARN del bucket S3"
  value       = aws_s3_bucket.datalake.arn
}

output "sqs_queue_url" {
  description = "URL de la cola principal de ingesta"
  value       = aws_sqs_queue.ingesta_queue.id
}

output "sqs_queue_arn" {
  description = "ARN de la cola principal"
  value       = aws_sqs_queue.ingesta_queue.arn
}

output "sqs_dlq_url" {
  description = "URL de la Dead Letter Queue (DLQ)"
  value       = aws_sqs_queue.dlq.id
}

output "api_role_arn" {
  description = "ARN del Rol IAM asignado a la API de Ingesta"
  value       = aws_iam_role.api_role.arn
}

output "worker_role_arn" {
  description = "ARN del Rol IAM asignado al Worker asincrono"
  value       = aws_iam_role.worker_role.arn
}
