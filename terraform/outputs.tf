# /terraform/outputs.tf

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "eks_node_security_group_id" {
  value = module.vpc.eks_node_security_group_id
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  value = module.eks.cluster_certificate_authority_data
}

# Database outputs
output "contact_submissions_table_name" {
  value = module.database.contact_submissions_table_name
}

output "website_visitors_table_name" {
  value = module.database.website_visitors_table_name
}

output "app_role_arn" {
  value = module.database.app_role_arn
}

# EFS outputs
output "efs_csi_driver_role_arn" {
  value = module.efs.efs_csi_driver_role_arn
}

# API Gateway outputs
output "api_gateway_url" {
  value = module.api_gateway.api_gateway_url
  description = "External API Gateway URL for public access"
}