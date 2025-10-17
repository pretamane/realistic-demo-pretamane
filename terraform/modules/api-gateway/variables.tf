variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "eks_node_public_ip" {
  description = "Public IP of the EKS node"
  type        = string
}

variable "node_port" {
  description = "NodePort for the Kubernetes service"
  type        = number
  default     = 30080
}

variable "vpc_id" {
  description = "VPC ID for security groups"
  type        = string
}

variable "eks_cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for Lambda VPC configuration"
  type        = list(string)
}
