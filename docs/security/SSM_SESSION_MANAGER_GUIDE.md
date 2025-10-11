# SSM Session Manager - Secure Access to EKS Nodes

## Overview

AWS Systems Manager Session Manager provides secure, auditable, and bastion-less access to EC2 instances (including EKS nodes) without the need for SSH keys, bastion hosts, or open inbound ports.

## Implementation Status

**Status:** ACTIVE AND OPERATIONAL
**Instances Registered:** 2/2 EKS nodes
**Agent Version:** 3.3.3050.0
**Implementation Date:** October 11, 2025

## Architecture

```
Traditional Approach:              Modern SSM Approach:
User → Bastion Host → EKS Node    User → AWS SSM API → EKS Node
  (SSH keys, port 22 open)         (IAM-based, no ports open)
```

### Key Components

1. **IAM Role Policy**: `AmazonSSMManagedInstanceCore` attached to EKS node role
2. **SSM Agent**: Pre-installed on Amazon Linux 2 EKS-optimized AMI
3. **CloudWatch Logs**: Session logging to `/aws/ssm/realistic-demo-pretamane`
4. **SSM Documents**: Custom session preferences for enhanced security

## Benefits Over Traditional Bastion Hosts

### Security Advantages
- **No SSH Keys**: Eliminates key management and rotation burden
- **No Open Ports**: Port 22 remains closed, reducing attack surface
- **IAM-Based Access**: Leverages AWS IAM for fine-grained access control
- **Full Auditability**: All sessions logged in CloudTrail and CloudWatch
- **Session Recording**: Optional session recording for compliance
- **Encrypted Traffic**: All traffic encrypted using AWS KMS

### Operational Advantages
- **Zero Maintenance**: No bastion host to patch, monitor, or manage
- **Cost-Effective**: FREE (included with AWS)
- **High Availability**: No single point of failure
- **Multi-Region**: Works across all AWS regions
- **Port Forwarding**: Enables secure access to private services

## Quick Start Guide

### Prerequisites
```bash
# Ensure AWS CLI is configured
aws configure list

# Install Session Manager plugin (if not already installed)
# macOS:
brew install --cask session-manager-plugin

# Linux:
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/linux_64bit/session-manager-plugin.rpm" -o "session-manager-plugin.rpm"
sudo yum install -y session-manager-plugin.rpm

# Verify installation
session-manager-plugin --version
```

### Basic Usage

#### 1. List Available Instances
```bash
aws ssm describe-instance-information \
  --query 'InstanceInformationList[*].{ID:InstanceId,Name:ComputerName,Status:PingStatus}' \
  --output table
```

**Current Instances:**
- `i-025e864b6503a0b25` - ip-10-0-0-4.ap-southeast-1.compute.internal
- `i-0b69966881621e83a` - ip-10-0-0-114.ap-southeast-1.compute.internal

#### 2. Start Interactive Session
```bash
# Connect to first node
aws ssm start-session --target i-025e864b6503a0b25

# Connect to second node
aws ssm start-session --target i-0b69966881621e83a
```

**What you can do in a session:**
```bash
# Check system info
uname -a
df -h

# View Kubernetes node status
sudo kubectl get nodes

# Check running pods
sudo crictl ps

# View system logs
sudo journalctl -u kubelet --since "1 hour ago"

# Check SSM agent status
sudo systemctl status amazon-ssm-agent
```

#### 3. Run One-Off Commands
```bash
# Run command on specific instance
aws ssm send-command \
  --instance-ids i-025e864b6503a0b25 \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["kubectl get pods -A"]' \
  --comment "Get all pods"

# Get command output
COMMAND_ID="<command-id-from-above>"
aws ssm get-command-invocation \
  --command-id $COMMAND_ID \
  --instance-id i-025e864b6503a0b25
```

#### 4. Port Forwarding
```bash
# Forward local port 8080 to remote port 8080
aws ssm start-session \
  --target i-025e864b6503a0b25 \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'

# Use case: Access kubectl proxy remotely
# On remote: kubectl proxy --port=8080
# On local: curl http://localhost:8080/api/v1/namespaces/default/pods
```

#### 5. Run Commands on Multiple Instances
```bash
# Target by tag
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:kubernetes.io/cluster/realistic-demo-pretamane-cluster,Values=owned" \
  --parameters 'commands=["uptime","free -h"]' \
  --comment "System health check"
```

## Advanced Usage

### Session Logging and Auditing

#### View Session Logs in CloudWatch
```bash
# Tail logs in real-time
aws logs tail /aws/ssm/realistic-demo-pretamane --follow

# Get recent sessions
aws logs filter-log-events \
  --log-group-name /aws/ssm/realistic-demo-pretamane \
  --start-time $(date -d '1 hour ago' +%s)000
```

#### View Session History in CloudTrail
```bash
# Find all SSM session starts
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=StartSession \
  --max-results 50
```

### IAM Permissions

#### Minimum IAM Policy for Users
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession"
      ],
      "Resource": [
        "arn:aws:ec2:ap-southeast-1:411911107156:instance/i-025e864b6503a0b25",
        "arn:aws:ec2:ap-southeast-1:411911107156:instance/i-0b69966881621e83a"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:TerminateSession",
        "ssm:ResumeSession"
      ],
      "Resource": "arn:aws:ssm:*:*:session/${aws:username}-*"
    }
  ]
}
```

### Session Preferences

Custom session preferences are configured via Terraform in `terraform/modules/eks/ssm-support.tf`:

- **Idle Timeout**: 20 minutes
- **Session Logging**: CloudWatch Logs enabled
- **Encryption**: Enabled
- **Run As User**: ssm-user (default)

## Troubleshooting

### Instance Not Showing in SSM
```bash
# Check instance is running
aws ec2 describe-instances --instance-ids i-025e864b6503a0b25

# Check IAM role has SSM policy
aws iam list-attached-role-policies --role-name realistic-demo-pretamane-eks-node-role

# Check SSM agent status (requires existing session or SSH)
sudo systemctl status amazon-ssm-agent

# Restart SSM agent
sudo systemctl restart amazon-ssm-agent
```

### Cannot Connect to Instance
```bash
# Verify instance is registered
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=i-025e864b6503a0b25"

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names ssm:StartSession \
  --resource-arns "arn:aws:ec2:ap-southeast-1:411911107156:instance/i-025e864b6503a0b25"
```

### Session Terminates Immediately
- Check instance security group allows HTTPS (443) outbound
- Verify VPC has internet connectivity or VPC endpoints for SSM
- Ensure SSM agent is running: `sudo systemctl status amazon-ssm-agent`

## Cost Analysis

### SSM Session Manager Costs
- **Service**: FREE
- **Data Transfer**: Standard AWS data transfer rates apply
- **CloudWatch Logs**: $0.50/GB ingested + $0.03/GB stored
- **Estimated Cost**: $0-2/month for typical usage

### Cost Comparison with Bastion Host
| Item | Bastion Host | SSM Session Manager |
|------|--------------|---------------------|
| EC2 Instance (t3.micro) | $10/month | $0 |
| Elastic IP | $3.60/month | $0 |
| Maintenance Time | 2-4 hours/month | 0 |
| Security Patches | Manual | Automatic |
| **Total Monthly Cost** | **$13.60 + labor** | **~$1** |

## Interview Talking Points

When discussing this implementation in interviews:

1. **Modern Security Practices**
   - "I replaced traditional bastion hosts with AWS SSM Session Manager to implement Zero Trust principles"
   - "Eliminated SSH key management burden and reduced attack surface by keeping port 22 closed"

2. **Cost Optimization**
   - "Saved ~$14/month per environment by eliminating bastion hosts"
   - "Zero maintenance overhead compared to managing EC2 bastion instances"

3. **Auditability and Compliance**
   - "All access is logged in CloudTrail with full IAM integration"
   - "Session activity logged to CloudWatch for forensic analysis"
   - "Meets SOC 2 and PCI DSS requirements for privileged access management"

4. **Technical Implementation**
   - "Used Terraform to codify SSM configuration as infrastructure-as-code"
   - "Integrated with existing EKS IAM roles using IRSA patterns"
   - "Implemented custom session preferences for enhanced security"

5. **Operational Benefits**
   - "Zero single points of failure - no bastion host to go down"
   - "Automatic high availability across all AWS availability zones"
   - "Works seamlessly in multi-region deployments"

## References

- [AWS SSM Session Manager Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [SSM Agent on EKS](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/install-ssm-agent-on-amazon-eks-worker-nodes-by-using-kubernetes-daemonset.html)
- [IAM Policies for Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-restrict-access-examples.html)

## Next Steps

### Recommended Enhancements
1. **Enable Session Recording**: Store session recordings in S3 for compliance
2. **Add MFA Requirement**: Require MFA for production sessions
3. **Implement Session Manager Plugin**: For better local experience
4. **Create IAM Groups**: Organize user permissions by role (dev, ops, read-only)
5. **Add Automation Documents**: Create custom runbooks for common tasks

### Future Considerations
- Integrate with AWS CloudShell for browser-based access
- Set up AWS Config rules to ensure SSM compliance
- Implement session approval workflows for production access
- Add custom SSM documents for common Kubernetes operations

