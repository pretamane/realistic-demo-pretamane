# /terraform/modules/database/outputs.tf

output "contact_submissions_table_name" {
  value = aws_dynamodb_table.contact_submissions.name
}

output "contact_submissions_table_arn" {
  value = aws_dynamodb_table.contact_submissions.arn
}

output "website_visitors_table_name" {
  value = aws_dynamodb_table.website_visitors.name
}

output "website_visitors_table_arn" {
  value = aws_dynamodb_table.website_visitors.arn
}

output "app_role_arn" {
  value = aws_iam_role.app_role.arn
}

output "ses_from_email" {
  value = var.ses_from_email
}

output "ses_to_email" {
  value = var.ses_to_email
}
