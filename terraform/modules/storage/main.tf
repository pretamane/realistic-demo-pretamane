# /terraform/modules/storage/main.tf
# Comprehensive Storage Module

# ---------------------------
# OpenSearch Service-Linked Role
# ---------------------------

resource "aws_iam_service_linked_role" "opensearch" {
  aws_service_name = "es.amazonaws.com"
  description      = "Service-linked role for OpenSearch Service"
}

# ---------------------------
# S3 Buckets for Data Storage
# ---------------------------

# Main data bucket
resource "aws_s3_bucket" "data_bucket" {
  bucket = "${var.project_name}-data-${random_id.bucket_suffix.hex}"
  
  tags = {
    Name        = "${var.project_name}-data-bucket"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Application data storage"
  }
}

# Indexing and search bucket
resource "aws_s3_bucket" "index_bucket" {
  bucket = "${var.project_name}-index-${random_id.bucket_suffix.hex}"
  
  tags = {
    Name        = "${var.project_name}-index-bucket"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Search index storage"
  }
}

# Backup bucket
resource "aws_s3_bucket" "backup_bucket" {
  bucket = "${var.project_name}-backup-${random_id.bucket_suffix.hex}"
  
  tags = {
    Name        = "${var.project_name}-backup-bucket"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Data backup storage"
  }
}

# Random suffix for bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# ---------------------------
# S3 Bucket Configurations
# ---------------------------

# Data bucket versioning
resource "aws_s3_bucket_versioning" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Data bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Data bucket lifecycle
resource "aws_s3_bucket_lifecycle_configuration" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    id     = "data_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Index bucket versioning
resource "aws_s3_bucket_versioning" "index_bucket" {
  bucket = aws_s3_bucket.index_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Index bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "index_bucket" {
  bucket = aws_s3_bucket.index_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Backup bucket versioning
resource "aws_s3_bucket_versioning" "backup_bucket" {
  bucket = aws_s3_bucket.backup_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Backup bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "backup_bucket" {
  bucket = aws_s3_bucket.backup_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# ---------------------------
# OpenSearch Domain for Advanced Indexing
# ---------------------------

resource "aws_opensearch_domain" "main" {
  domain_name    = "pretamane-search"
  engine_version = "OpenSearch_2.3"

  cluster_config {
    instance_type            = var.opensearch_instance_type
    instance_count           = var.opensearch_instance_count
    dedicated_master_enabled = var.opensearch_dedicated_master
    zone_awareness_enabled   = true

    zone_awareness_config {
      availability_zone_count = 2
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = var.opensearch_volume_size
  }

  vpc_options {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.opensearch.id]
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = var.opensearch_master_user
      master_user_password = var.opensearch_master_password
    }
  }

        access_policies = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Principal = {
                AWS = "*"
              }
              Action   = "es:*"
              Resource = "arn:aws:es:${var.region}:${data.aws_caller_identity.current.account_id}:domain/pretamane-search/*"
            }
          ]
        })

  tags = {
    Name        = "${var.project_name}-opensearch"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# ---------------------------
# OpenSearch Security Group
# ---------------------------

resource "aws_security_group" "opensearch" {
  name_prefix = "${var.project_name}-opensearch-"
  vpc_id      = var.vpc_id
  description = "Security group for OpenSearch domain"

  ingress {
    description = "HTTPS from EKS nodes"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    security_groups = [var.eks_node_security_group_id]
  }

  ingress {
    description = "HTTPS from EKS cluster"
    from_port   = 443
    to_port     = 443
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
    Name        = "${var.project_name}-opensearch-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ---------------------------
# IAM Policies for Storage Access
# ---------------------------

# S3 access policy
resource "aws_iam_policy" "s3_access_policy" {
  name        = "${var.project_name}-s3-access-policy"
  description = "Policy for S3 bucket access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_bucket.arn,
          "${aws_s3_bucket.data_bucket.arn}/*",
          aws_s3_bucket.index_bucket.arn,
          "${aws_s3_bucket.index_bucket.arn}/*",
          aws_s3_bucket.backup_bucket.arn,
          "${aws_s3_bucket.backup_bucket.arn}/*"
        ]
      }
    ]
  })
}

# OpenSearch access policy
resource "aws_iam_policy" "opensearch_access_policy" {
  name        = "${var.project_name}-opensearch-access-policy"
  description = "Policy for OpenSearch access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "es:ESHttpGet",
          "es:ESHttpPost",
          "es:ESHttpPut",
          "es:ESHttpDelete",
          "es:ESHttpHead"
        ]
        Resource = "${aws_opensearch_domain.main.arn}/*"
      }
    ]
  })
}

# ---------------------------
# IAM Role for Application (IRSA)
# ---------------------------

resource "aws_iam_role" "app_storage_role" {
  name = "${var.project_name}-app-storage-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(var.oidc_provider_url, "https://", "")}:sub" = "system:serviceaccount:default:contact-api"
            "${replace(var.oidc_provider_url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Attach policies to role
resource "aws_iam_role_policy_attachment" "s3_access" {
  policy_arn = aws_iam_policy.s3_access_policy.arn
  role       = aws_iam_role.app_storage_role.name
}

resource "aws_iam_role_policy_attachment" "opensearch_access" {
  policy_arn = aws_iam_policy.opensearch_access_policy.arn
  role       = aws_iam_role.app_storage_role.name
}

# ---------------------------
# S3 Bucket Notifications (Optional)
# ---------------------------

# S3 bucket notification - REMOVED
# Lambda function processing consolidated into unified FastAPI application
# Background processing now handled by FastAPI background tasks

# Lambda function for S3 processing - REMOVED
# Functionality consolidated into unified FastAPI application

# Lambda IAM role - REMOVED
# Lambda permissions - REMOVED
# All Lambda functionality now handled by unified FastAPI application
