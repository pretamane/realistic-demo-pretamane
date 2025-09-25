# /terraform/modules/efs/main.tf
# EFS File System Module

# ---------------------------
# EFS File System
# ---------------------------

resource "aws_efs_file_system" "main" {
  creation_token = "${var.project_name}-efs-${random_id.efs_token.hex}"
  
  performance_mode = var.performance_mode
  throughput_mode  = var.throughput_mode
  
  # Enable encryption at rest
  encrypted = true
  kms_key_id = var.kms_key_id
  
  # Enable lifecycle management
  lifecycle_policy {
    transition_to_ia = "AFTER_7_DAYS"
  }
  
  tags = {
    Name        = "${var.project_name}-efs"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Shared storage for Kubernetes pods"
  }
}

# Random ID for EFS creation token
resource "random_id" "efs_token" {
  byte_length = 4
}

# ---------------------------
# EFS Mount Targets
# ---------------------------

resource "aws_efs_mount_target" "main" {
  count           = length(var.subnet_ids)
  file_system_id  = aws_efs_file_system.main.id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = [aws_security_group.efs.id]
}

# ---------------------------
# EFS Security Group
# ---------------------------

resource "aws_security_group" "efs" {
  name_prefix = "${var.project_name}-efs-"
  vpc_id      = var.vpc_id
  description = "Security group for EFS file system"

  ingress {
    description = "NFS from EKS nodes"
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    security_groups = [var.eks_node_security_group_id]
  }

  ingress {
    description = "NFS from EKS cluster"
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    security_groups = [var.eks_cluster_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-efs-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ---------------------------
# EFS Access Point
# ---------------------------

resource "aws_efs_access_point" "main" {
  file_system_id = aws_efs_file_system.main.id
  
  posix_user {
    gid = 1000
    uid = 1000
  }
  
  root_directory {
    path = "/data"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }
  
  tags = {
    Name        = "${var.project_name}-efs-access-point"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ---------------------------
# EFS Backup Vault (Optional)
# ---------------------------

resource "aws_backup_vault" "efs" {
  count       = var.enable_backup ? 1 : 0
  name        = "${var.project_name}-efs-backup-vault"
  kms_key_arn = var.kms_key_id
  
  tags = {
    Name        = "${var.project_name}-efs-backup-vault"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_backup_plan" "efs" {
  count = var.enable_backup ? 1 : 0
  name  = "${var.project_name}-efs-backup-plan"

  rule {
    rule_name         = "daily_backup"
    target_vault_name = aws_backup_vault.efs[0].name
    schedule          = "cron(0 2 * * ? *)"  # Daily at 2 AM

    lifecycle {
      cold_storage_after = 30
      delete_after       = 120
    }

    recovery_point_tags = {
      Name        = "${var.project_name}-efs-backup"
      Environment = var.environment
      Project     = var.project_name
    }
  }

  tags = {
    Name        = "${var.project_name}-efs-backup-plan"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_backup_selection" "efs" {
  count        = var.enable_backup ? 1 : 0
  iam_role_arn = aws_iam_role.backup[0].arn
  name         = "${var.project_name}-efs-backup-selection"
  plan_id      = aws_backup_plan.efs[0].id

  resources = [aws_efs_file_system.main.arn]
}

resource "aws_iam_role" "backup" {
  count = var.enable_backup ? 1 : 0
  name  = "${var.project_name}-efs-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  count      = var.enable_backup ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
  role       = aws_iam_role.backup[0].name
}

# ---------------------------
# EFS CSI Driver IAM Role
# ---------------------------

resource "aws_iam_role" "efs_csi_driver" {
  name = "${var.project_name}-efs-csi-driver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${replace(var.oidc_provider_url, "https://", "")}:sub" = "system:serviceaccount:kube-system:efs-csi-controller-sa"
            "${replace(var.oidc_provider_url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "efs_csi_driver" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy"
  role       = aws_iam_role.efs_csi_driver.name
}
