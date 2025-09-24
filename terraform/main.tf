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
  oidc_provider_url   = module.eks.oidc_provider_url  # 👈 NOW CORRECT
  oidc_provider_arn   = module.eks.oidc_provider_arn
}

module "database" {
  source = "./modules/database"
  project_name        = "realistic-demo-pretamane"
  region              = "ap-southeast-1"
  oidc_provider_url   = module.eks.oidc_provider_url
  oidc_provider_arn   = module.eks.oidc_provider_arn
  ses_from_email      = "thawzin252467@gmail.com"
  ses_to_email        = "thawzin252467@gmail.com"
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