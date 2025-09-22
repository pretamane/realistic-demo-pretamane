# /terraform/modules/iam/variables.tf

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

variable "oidc_provider_url" {
  description = "OIDC provider URL from EKS cluster"
  type        = string
}

variable "oidc_provider_arn" {
  description = "OIDC provider ARN from EKS cluster"
  type        = string
}