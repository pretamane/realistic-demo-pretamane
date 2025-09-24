# /terraform/modules/backend/outputs.tf

output "terraform_state_bucket_name" {
  value = aws_s3_bucket.terraform_state.bucket
}

output "terraform_state_bucket_arn" {
  value = aws_s3_bucket.terraform_state.arn
}

output "terraform_locks_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}

output "terraform_locks_table_arn" {
  value = aws_dynamodb_table.terraform_locks.arn
}
