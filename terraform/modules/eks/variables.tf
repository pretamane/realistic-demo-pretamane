# /terraform/modules/eks/variables.tf

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_id" {
  description = "VPC ID where EKS cluster will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for EKS cluster"
  type        = list(string)
}

variable "eks_node_security_group_id" {
  description = "Security group ID for EKS nodes"
  type        = string
}

variable "free_tier_mode" {
  description = "Enable Free Tier optimized configuration"
  type        = bool
  default     = false
}