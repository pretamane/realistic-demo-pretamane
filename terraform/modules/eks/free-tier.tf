# /terraform/modules/eks/free-tier.tf
# Free Tier Optimized EKS Configuration

# EKS Cluster optimized for Free Tier
resource "aws_eks_cluster" "main_free_tier" {
  count    = var.free_tier_mode ? 1 : 0
  name     = "${var.project_name}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.eks_node_security_group_id]
    endpoint_private_access = false
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  # Minimal logging for cost savings
  enabled_cluster_log_types = ["api", "audit"]

  tags = {
    Name = "${var.project_name}-cluster"
    Environment = "free-tier"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller_policy
  ]
}

# Free Tier Node Group - Single t3.micro instance
resource "aws_eks_node_group" "main_free_tier" {
  count           = var.free_tier_mode ? 1 : 0
  cluster_name    = aws_eks_cluster.main_free_tier[0].name
  node_group_name = "${var.project_name}-node-group"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.subnet_ids

  # Free Tier optimized configuration
  capacity_type  = "ON_DEMAND"  # Use On-Demand for Free Tier eligibility
  instance_types = ["t3.micro"]  # Free Tier eligible instance
  ami_type       = "AL2_x86_64"
  disk_size      = 8  # Minimum disk size

  scaling_config {
    desired_size = 1
    max_size     = 1  # Single node for Free Tier
    min_size     = 1
  }

  update_config {
    max_unavailable_percentage = 0
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.ec2_container_registry_read_only,
  ]

  tags = {
    Name = "${var.project_name}-node-group"
    Environment = "free-tier"
  }
}

# EFS File System for Free Tier (5GB free)
resource "aws_efs_file_system" "main_free_tier" {
  count           = var.free_tier_mode ? 1 : 0
  creation_token  = "${var.project_name}-efs"
  
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"
  
  # Free Tier: 5GB of storage
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = {
    Name = "${var.project_name}-efs"
    Environment = "free-tier"
  }
}

# EFS Mount Targets
resource "aws_efs_mount_target" "main_free_tier" {
  count           = var.free_tier_mode ? length(var.subnet_ids) : 0
  file_system_id  = aws_efs_file_system.main_free_tier[0].id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = [var.eks_node_security_group_id]
}

# EFS Access Point
resource "aws_efs_access_point" "main_free_tier" {
  count          = var.free_tier_mode ? 1 : 0
  file_system_id = aws_efs_file_system.main_free_tier[0].id

  posix_user {
    gid = 1000
    uid = 1000
  }

  root_directory {
    path = "/app"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }

  tags = {
    Name = "${var.project_name}-efs-access-point"
    Environment = "free-tier"
  }
}
