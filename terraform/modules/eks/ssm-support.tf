# SSM Session Manager Support for EKS Nodes
# Enables secure, audit-logged access to EKS nodes without bastion hosts

# Attach SSM policy to node IAM role (already done manually, this makes it permanent)
resource "aws_iam_role_policy_attachment" "eks_node_ssm" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.eks_node.name
}

# Optional: SSM Session Manager preferences
resource "aws_ssm_document" "session_manager_prefs" {
  name            = "${var.project_name}-session-manager-preferences"
  document_type   = "Session"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "1.0"
    description   = "Session Manager preferences for EKS node access"
    sessionType   = "Standard_Stream"
    inputs = {
      s3BucketName                = ""
      s3KeyPrefix                 = ""
      s3EncryptionEnabled         = true
      cloudWatchLogGroupName      = "/aws/ssm/${var.project_name}"
      cloudWatchEncryptionEnabled = true
      cloudWatchStreamingEnabled  = true
      kmsKeyId                    = ""
      runAsEnabled                = false
      runAsDefaultUser            = ""
      idleSessionTimeout          = "20"
      maxSessionDuration          = ""
      shellProfile = {
        linux = "cd /home/ssm-user\nPS1='[\\u@\\h \\W]\\$ '\nexport PATH=$PATH:/usr/local/bin"
      }
    }
  })

  tags = {
    Name        = "${var.project_name}-session-manager-prefs"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

# CloudWatch Log Group for session logging
resource "aws_cloudwatch_log_group" "ssm_sessions" {
  name              = "/aws/ssm/${var.project_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-ssm-sessions"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

# Output for documentation
output "ssm_session_manager_enabled" {
  value       = true
  description = "SSM Session Manager is enabled for EKS nodes"
}

output "ssm_session_commands" {
  value = <<-EOT
    SSM Session Manager Commands:
    
    # List available instances
    aws ssm describe-instance-information --query 'InstanceInformationList[*].{ID:InstanceId,Name:ComputerName,Status:PingStatus}' --output table
    
    # Start interactive session
    aws ssm start-session --target <instance-id>
    
    # Port forward to private service (e.g., kubectl proxy)
    aws ssm start-session --target <instance-id> --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'
    
    # Run one-off command
    aws ssm send-command --instance-ids <instance-id> --document-name "AWS-RunShellScript" --parameters 'commands=["kubectl get pods"]'
    
    # View session logs
    aws logs tail /aws/ssm/${var.project_name} --follow
  EOT
  description = "Useful SSM Session Manager commands"
}

