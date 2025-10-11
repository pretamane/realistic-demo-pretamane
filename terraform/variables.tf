# /terraform/variables.tf

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

variable "free_tier_mode" {
  description = "Enable Free Tier optimized configuration"
  type        = bool
  default     = false
}

variable "ses_from_email" {
  description = "SES from email address"
  type        = string
  default     = ""
}

variable "ses_to_email" {
  description = "SES to email address"
  type        = string
  default     = ""
}

variable "opensearch_master_password" {
  description = "OpenSearch master password (required, no default for security)"
  type        = string
  sensitive   = true
}