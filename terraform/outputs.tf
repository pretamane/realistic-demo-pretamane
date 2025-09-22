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