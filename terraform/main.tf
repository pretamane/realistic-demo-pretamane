# /terraform/main.tf

# ---------------------------
# Call VPC Module
# ---------------------------

module "vpc" {
  source = "./modules/vpc"
  project_name = "realistic-demo-pretamane"
  region       = "ap-southeast-1"
}

module "eks" {
  source = "./modules/eks"
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.public_subnet_ids
  eks_node_security_group_id = module.vpc.eks_node_security_group_id
  project_name               = "realistic-demo-pretamane"
  region                     = "ap-southeast-1"
}

module "iam" {
  source = "./modules/iam"
  project_name        = "realistic-demo-pretamane"
  region              = "ap-southeast-1"
}

module "database" {
  source = "./modules/database"
  project_name        = "realistic-demo-pretamane"
  region              = "ap-southeast-1"
  oidc_provider_url   = module.eks.oidc_provider_url
  oidc_provider_arn   = module.eks.oidc_provider_arn
  ses_from_email      = var.ses_from_email
  ses_to_email        = var.ses_to_email
}

# ---------------------------
# EFS File System Module
# ---------------------------

module "efs" {
  source = "./modules/efs"
  project_name                    = "realistic-demo-pretamane"
  environment                     = "production"
  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.public_subnet_ids
  eks_node_security_group_id     = module.vpc.eks_node_security_group_id
  eks_cluster_security_group_id  = module.eks.cluster_security_group_id
  oidc_provider_arn              = module.eks.oidc_provider_arn
  oidc_provider_url              = module.eks.oidc_provider_url
  performance_mode               = "generalPurpose"
  throughput_mode                = "bursting"
  enable_backup                  = true
}

# ---------------------------
# Comprehensive Storage Module
# ---------------------------

module "storage" {
  source = "./modules/storage"
  project_name                    = "realistic-demo-pretamane"
  environment                     = "production"
  region                         = "ap-southeast-1"
  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.public_subnet_ids
  eks_node_security_group_id     = module.vpc.eks_node_security_group_id
  eks_cluster_security_group_id  = module.eks.cluster_security_group_id
  oidc_provider_arn              = module.eks.oidc_provider_arn
  oidc_provider_url              = module.eks.oidc_provider_url
  allowed_cidr_blocks            = ["0.0.0.0/0"]
  opensearch_instance_type       = "t3.small.search"
  opensearch_instance_count      = 2
  opensearch_dedicated_master    = false
  opensearch_volume_size         = 20
  opensearch_master_user         = "admin"
  opensearch_master_password     = var.opensearch_master_password  # Must be provided via terraform.tfvars or TF_VAR_opensearch_master_password
  enable_s3_notifications        = true
}

# ---------------------------
# Helm Releases for Monitoring & Scaling
# ---------------------------

# Metrics Server for HPA
resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  namespace  = "kube-system"
  version    = "3.11.0"

  set = [
    {
      name  = "args[0]"
      value = "--kubelet-insecure-tls"
    },
    {
      name  = "args[1]"
      value = "--kubelet-preferred-address-types=InternalIP"
    }
  ]

  depends_on = [module.eks]
}

# Cluster Autoscaler
resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  namespace  = "kube-system"
  version    = "9.29.0"

  set = [
    {
      name  = "autoDiscovery.clusterName"
      value = module.eks.cluster_name
    },
    {
      name  = "awsRegion"
      value = "ap-southeast-1"
    },
    {
      name  = "rbac.serviceAccount.create"
      value = "false"
    },
    {
      name  = "rbac.serviceAccount.name"
      value = "cluster-autoscaler"
    },
    {
      name  = "rbac.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
      value = module.eks.cluster_autoscaler_role_arn
    }
  ]

  depends_on = [module.eks]
}

# CloudWatch Container Insights
resource "helm_release" "cloudwatch_agent" {
  name       = "aws-cloudwatch-metrics"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-cloudwatch-metrics"
  namespace  = "amazon-cloudwatch"
  version    = "0.0.7"

  set = [
    {
      name  = "clusterName"
      value = module.eks.cluster_name
    },
    {
      name  = "serviceAccount.create"
      value = "false"
    },
    {
      name  = "serviceAccount.name"
      value = "cloudwatch-agent"
    }
  ]

  depends_on = [module.eks]
}

# AWS Load Balancer Controller (uncommented and updated)
resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.6.2"

  set = [
    {
      name  = "clusterName"
      value = module.eks.cluster_name
    },
    {
      name  = "serviceAccount.create"
      value = "false"
    },
    {
      name  = "serviceAccount.name"
      value = "aws-load-balancer-controller"
    }
  ]

  depends_on = [module.eks]
}

# EFS CSI Driver
resource "helm_release" "efs_csi_driver" {
  name       = "aws-efs-csi-driver"
  repository = "https://kubernetes-sigs.github.io/aws-efs-csi-driver"
  chart      = "aws-efs-csi-driver"
  namespace  = "kube-system"
  version    = "2.4.8"

  set = [
    {
      name  = "controller.serviceAccount.create"
      value = "false"
    },
    {
      name  = "controller.serviceAccount.name"
      value = "efs-csi-controller-sa"
    },
    {
      name  = "controller.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
      value = module.efs.efs_csi_driver_role_arn
    }
  ]

  depends_on = [module.eks, module.efs]
}

# ---------------------------
# API Gateway Module for External Access
# ---------------------------

module "api_gateway" {
  source = "./modules/api-gateway"
  project_name        = "realistic-demo-pretamane"
  region              = "ap-southeast-1"
  eks_node_public_ip  = "13.215.48.255"  # EKS node public IP
  node_port           = 30080
  vpc_id              = module.vpc.vpc_id
  eks_cluster_name    = module.eks.cluster_name
  subnet_ids          = module.vpc.public_subnet_ids
}