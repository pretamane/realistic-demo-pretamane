# /terraform/providers.tf

provider "aws" {
  region = "ap-southeast-1"
}

provider "kubernetes" {
  # Will be configured after EKS cluster is created
}

provider "helm" {
  # For ALB Ingress Controller later
}