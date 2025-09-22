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

# module "iam" {
#   source = "./modules/iam"
#   project_name        = "realistic-demo-pretamane"
#   region              = "ap-southeast-1"
#   oidc_provider_url   = module.eks.oidc_provider_url  # 👈 NOW CORRECT
#   oidc_provider_arn   = module.eks.oidc_provider_arn
# }

# /terraform/main.tf — CORRECTED

# resource "helm_release" "aws_load_balancer_controller" {
#   name       = "aws-load-balancer-controller"
#   repository = "https://aws.github.io/eks-charts"
#   chart      = "aws-load-balancer-controller"
#   namespace  = "kube-system"

#   set = [
#     {
#       name  = "clusterName"
#       value = module.eks.cluster_name
#     },
#     {
#       name  = "serviceAccount.create"
#       value = "false"
#     },
#     {
#       name  = "serviceAccount.name"
#       value = "aws-load-balancer-controller"
#     }
#   ]

#   depends_on = [module.eks]
# }