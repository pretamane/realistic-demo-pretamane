# /terraform/modules/database/main.tf

# ---------------------------
# DynamoDB Tables
# ---------------------------

# Contact Submissions Table
resource "aws_dynamodb_table" "contact_submissions" {
  name           = "${var.project_name}-contact-submissions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # Global Secondary Index for email queries
  global_secondary_index {
    name     = "email-index"
    hash_key = "email"
    projection_type = "ALL"
  }

  # Global Secondary Index for timestamp queries
  global_secondary_index {
    name     = "timestamp-index"
    hash_key = "timestamp"
    projection_type = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-contact-submissions"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Website Visitors Table
resource "aws_dynamodb_table" "website_visitors" {
  name           = "${var.project_name}-website-visitors"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-website-visitors"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Documents Table (for enhanced_app.py)
resource "aws_dynamodb_table" "documents" {
  name           = "${var.project_name}-documents"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "contact_id"
    type = "S"
  }

  attribute {
    name = "upload_timestamp"
    type = "S"
  }

  # Global Secondary Index for contact queries
  global_secondary_index {
    name            = "contact-id-index"
    hash_key        = "contact_id"
    projection_type = "ALL"
  }

  # Global Secondary Index for timestamp queries
  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "upload_timestamp"
    projection_type = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-documents"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ---------------------------
# SES Configuration
# ---------------------------

# SES Domain Identity (optional - for custom domain)
resource "aws_ses_domain_identity" "main" {
  count  = var.ses_domain != "" ? 1 : 0
  domain = var.ses_domain
}

# SES Email Identity
resource "aws_ses_email_identity" "from_email" {
  email = var.ses_from_email
}

resource "aws_ses_email_identity" "to_email" {
  email = var.ses_to_email
}

# SES Configuration Set (for tracking)
resource "aws_ses_configuration_set" "main" {
  name = "${var.project_name}-ses-config"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
}

# ---------------------------
# IAM Policy for Application
# ---------------------------

resource "aws_iam_policy" "app_database_policy" {
  name        = "${var.project_name}-app-database-policy"
  description = "Policy for application to access DynamoDB and SES"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          aws_dynamodb_table.contact_submissions.arn,
          "${aws_dynamodb_table.contact_submissions.arn}/index/*",
          aws_dynamodb_table.website_visitors.arn,
          aws_dynamodb_table.documents.arn,
          "${aws_dynamodb_table.documents.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# ---------------------------
# IAM Role for Application (IRSA)
# ---------------------------

resource "aws_iam_role" "app_role" {
  name = "${var.project_name}-app-role"

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

resource "aws_iam_role_policy_attachment" "app_database_policy" {
  policy_arn = aws_iam_policy.app_database_policy.arn
  role       = aws_iam_role.app_role.name
}
