# /terraform/modules/storage/outputs.tf
# Storage Module Outputs

# S3 Bucket Outputs
output "data_bucket_name" {
  description = "Name of the data S3 bucket"
  value       = aws_s3_bucket.data_bucket.bucket
}

output "data_bucket_arn" {
  description = "ARN of the data S3 bucket"
  value       = aws_s3_bucket.data_bucket.arn
}

output "index_bucket_name" {
  description = "Name of the index S3 bucket"
  value       = aws_s3_bucket.index_bucket.bucket
}

output "index_bucket_arn" {
  description = "ARN of the index S3 bucket"
  value       = aws_s3_bucket.index_bucket.arn
}

output "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  value       = aws_s3_bucket.backup_bucket.bucket
}

output "backup_bucket_arn" {
  description = "ARN of the backup S3 bucket"
  value       = aws_s3_bucket.backup_bucket.arn
}

# OpenSearch Outputs
output "opensearch_domain_name" {
  description = "Name of the OpenSearch domain"
  value       = aws_opensearch_domain.main.domain_name
}

output "opensearch_domain_arn" {
  description = "ARN of the OpenSearch domain"
  value       = aws_opensearch_domain.main.arn
}

output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.main.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "OpenSearch dashboard endpoint"
  value       = aws_opensearch_domain.main.dashboard_endpoint
}

output "opensearch_security_group_id" {
  description = "Security group ID of OpenSearch"
  value       = aws_security_group.opensearch.id
}

# IAM Outputs
output "app_storage_role_arn" {
  description = "ARN of the application storage IAM role"
  value       = aws_iam_role.app_storage_role.arn
}

output "s3_access_policy_arn" {
  description = "ARN of the S3 access policy"
  value       = aws_iam_policy.s3_access_policy.arn
}

output "opensearch_access_policy_arn" {
  description = "ARN of the OpenSearch access policy"
  value       = aws_iam_policy.opensearch_access_policy.arn
}

# Lambda Outputs (if enabled)
output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = var.enable_s3_notifications ? aws_lambda_function.s3_processor[0].arn : null
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = var.enable_s3_notifications ? aws_lambda_function.s3_processor[0].function_name : null
}
