# /terraform/free-tier-main.tf
# Free Tier Optimized Main Configuration

# ---------------------------
# Call VPC Module (Free Tier)
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
  free_tier_mode             = true  # Enable Free Tier mode
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
  ses_from_email      = "thawzin252467@gmail.com"
  ses_to_email        = "thawzin252467@gmail.com"
}

# ---------------------------
# Free Tier Optimized Helm Releases
# ---------------------------

# Metrics Server (minimal configuration)
resource "helm_release" "metrics_server_free_tier" {
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
    },
    {
      name  = "resources.requests.memory"
      value = "32Mi"
    },
    {
      name  = "resources.requests.cpu"
      value = "25m"
    }
  ]

  depends_on = [module.eks]
}

# CloudWatch Agent (minimal configuration)
resource "helm_release" "cloudwatch_agent_free_tier" {
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
    },
    {
      name  = "resources.requests.memory"
      value = "64Mi"
    },
    {
      name  = "resources.requests.cpu"
      value = "50m"
    }
  ]

  depends_on = [module.eks]
}

# ---------------------------
# Free Tier Cost Monitoring
# ---------------------------

# CloudWatch Billing Alarm (Free Tier)
resource "aws_cloudwatch_metric_alarm" "free_tier_billing" {
  alarm_name          = "free-tier-billing-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "86400"  # 24 hours
  statistic           = "Maximum"
  threshold           = "5"  # Alert if charges exceed $5
  alarm_description   = "This metric monitors free tier billing"
  alarm_actions       = []

  dimensions = {
    Currency = "USD"
  }

  tags = {
    Environment = "free-tier"
    Project     = "realistic-demo-pretamane"
  }
}
