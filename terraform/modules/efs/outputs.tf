# /terraform/modules/efs/outputs.tf
# EFS Module Outputs

output "efs_file_system_id" {
  description = "EFS file system ID"
  value       = aws_efs_file_system.main.id
}

output "efs_file_system_arn" {
  description = "EFS file system ARN"
  value       = aws_efs_file_system.main.arn
}

output "efs_file_system_dns_name" {
  description = "EFS file system DNS name"
  value       = aws_efs_file_system.main.dns_name
}

output "efs_access_point_id" {
  description = "EFS access point ID"
  value       = aws_efs_access_point.main.id
}

output "efs_access_point_arn" {
  description = "EFS access point ARN"
  value       = aws_efs_access_point.main.arn
}

output "efs_security_group_id" {
  description = "EFS security group ID"
  value       = aws_security_group.efs.id
}

output "efs_mount_target_ids" {
  description = "EFS mount target IDs"
  value       = aws_efs_mount_target.main[*].id
}

output "efs_backup_vault_arn" {
  description = "EFS backup vault ARN"
  value       = var.enable_backup ? aws_backup_vault.efs[0].arn : null
}

output "efs_backup_plan_id" {
  description = "EFS backup plan ID"
  value       = var.enable_backup ? aws_backup_plan.efs[0].id : null
}

output "efs_csi_driver_role_arn" {
  description = "EFS CSI Driver IAM role ARN"
  value       = aws_iam_role.efs_csi_driver.arn
}
