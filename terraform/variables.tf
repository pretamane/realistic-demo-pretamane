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