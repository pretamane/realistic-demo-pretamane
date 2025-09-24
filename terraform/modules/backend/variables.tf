# /terraform/modules/backend/variables.tf

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
