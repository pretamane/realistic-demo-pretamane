# /terraform/modules/storage/variables.tf
# Storage Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "eks_node_security_group_id" {
  description = "Security group ID of EKS nodes"
  type        = string
}

variable "eks_cluster_security_group_id" {
  description = "Security group ID of EKS cluster"
  type        = string
}

variable "oidc_provider_arn" {
  description = "OIDC provider ARN for IRSA"
  type        = string
}

variable "oidc_provider_url" {
  description = "OIDC provider URL"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "List of allowed CIDR blocks for OpenSearch access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# OpenSearch Configuration
variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 2
}

variable "opensearch_dedicated_master" {
  description = "Enable dedicated master nodes"
  type        = bool
  default     = false
}

variable "opensearch_master_instance_type" {
  description = "OpenSearch master instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_master_instance_count" {
  description = "Number of OpenSearch master instances"
  type        = number
  default     = 3
}

variable "opensearch_volume_size" {
  description = "OpenSearch volume size in GB"
  type        = number
  default     = 20
}

variable "opensearch_master_user" {
  description = "OpenSearch master username"
  type        = string
  default     = "admin"
}

variable "opensearch_master_password" {
  description = "OpenSearch master password - MUST be provided via environment variable or terraform.tfvars"
  type        = string
  sensitive   = true
  default     = ""  # No default - must be explicitly provided
  
  validation {
    condition     = length(var.opensearch_master_password) >= 8
    error_message = "OpenSearch password must be at least 8 characters long."
  }
}

# S3 Configuration
variable "enable_s3_notifications" {
  description = "Enable S3 bucket notifications"
  type        = bool
  default     = false
}
