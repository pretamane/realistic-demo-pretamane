# /terraform/modules/eks/variables.tf

variable "vpc_id" {
  description = "VPC ID from VPC module"
  type        = string
}

variable "subnet_ids" {
  description = "Public subnet IDs from VPC module"
  type        = list(string)
}

variable "eks_node_security_group_id" {
  description = "Security group ID for EKS nodes"
  type        = string
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "realistic-demo-pretamane"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}