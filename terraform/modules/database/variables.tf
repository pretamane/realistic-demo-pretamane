# /terraform/modules/database/variables.tf

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "realistic-demo-pretamane"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "ses_from_email" {
  description = "SES from email address"
  type        = string
  default     = "thawzin252467@gmail.com"
}

variable "ses_to_email" {
  description = "SES to email address"
  type        = string
  default     = "thawzin252467@gmail.com"
}

variable "ses_domain" {
  description = "SES domain for custom domain (optional)"
  type        = string
  default     = ""
}

variable "oidc_provider_arn" {
  description = "OIDC provider ARN for IRSA"
  type        = string
}

variable "oidc_provider_url" {
  description = "OIDC provider URL for IRSA"
  type        = string
}
