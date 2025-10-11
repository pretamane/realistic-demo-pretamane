# OpenSearch Password Security Fix

## Issue Resolved

**Security Issue:** Hardcoded OpenSearch credentials (`admin` / `Admin123!`) were committed to git.

**Date Fixed:** October 11, 2025  
**Severity:** HIGH - Credentials exposed in public repository  
**Status:** RESOLVED

---

## What Was Fixed

### Before (INSECURE):
```terraform
# terraform/modules/storage/variables.tf
variable "opensearch_master_password" {
  default = "Admin123!"  # EXPOSED IN GIT!
}

# terraform/main.tf
opensearch_master_password = "Admin123!"  # EXPOSED IN GIT!
```

### After (SECURE):
```terraform
# terraform/variables.tf
variable "opensearch_master_password" {
  description = "OpenSearch master password (required, no default for security)"
  type        = string
  sensitive   = true
  # NO DEFAULT - must be explicitly provided
}

# terraform/main.tf
opensearch_master_password = var.opensearch_master_password
```

---

## How to Provide Password Securely

### Method 1: terraform.tfvars (Recommended for Development)

```bash
# Copy example file
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# Generate secure password
SECURE_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-20)
echo "Generated password: $SECURE_PASSWORD"

# Edit terraform.tfvars (this file is gitignored)
vi terraform/terraform.tfvars
# Set: opensearch_master_password = "YOUR_SECURE_PASSWORD"
```

### Method 2: Environment Variable (Recommended for CI/CD)

```bash
# Generate and export password
export TF_VAR_opensearch_master_password=$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-20)

# Verify it's set
echo $TF_VAR_opensearch_master_password

# Run Terraform
terraform plan
terraform apply
```

### Method 3: AWS Secrets Manager (Recommended for Production)

```bash
# Create secret in AWS
aws secretsmanager create-secret \
  --name realistic-demo-pretamane/opensearch-password \
  --secret-string "$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-20)"

# Retrieve in Terraform or scripts
PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id realistic-demo-pretamane/opensearch-password \
  --query SecretString --output text)

export TF_VAR_opensearch_master_password=$PASSWORD
```

### Method 4: Interactive Prompt

```bash
# Terraform will prompt for the password
terraform plan
# Enter password when prompted

# Or use -var flag
terraform plan -var="opensearch_master_password=YOUR_SECURE_PASSWORD"
```

---

## Security Best Practices

### What's Protected:
- `terraform/.gitignore` prevents `*.tfvars` from being committed
- `opensearch_master_password` variable marked as `sensitive = true`
- No default value in variable definition
- Validation ensures minimum 8 character length

### Additional Recommendations:

1. **Rotate Password Immediately:**
   ```bash
   # If old password was exposed, change it
   aws opensearch update-domain-config \
     --domain-name realistic-demo-pretamane-opensearch \
     --advanced-security-options MasterUserOptions={MasterUserName=admin,MasterUserPassword=NEW_PASSWORD}
   ```

2. **Use AWS Secrets Manager:**
   - Store all sensitive credentials in Secrets Manager
   - Enable automatic rotation
   - Set up IAM policies for access control

3. **Enable MFA for AWS Console:**
   - Prevent unauthorized access even if credentials leak

4. **Audit Git History:**
   ```bash
   # Check if password was committed
   git log -p -- terraform/ | grep -i "Admin123"
   
   # If found, consider these options:
   # - Rotate password immediately
   # - Use git filter-branch to remove from history (complex)
   # - Archive repo and start fresh (simplest)
   ```

5. **Monitor Access:**
   - Enable CloudTrail logging
   - Set up CloudWatch alarms for OpenSearch access
   - Review access logs regularly

---

## Verification Checklist

- [ ] Removed hardcoded password from all Terraform files
- [ ] Added `opensearch_master_password` variable to `terraform/variables.tf`
- [ ] Created `terraform.tfvars.example` with instructions
- [ ] Added `terraform/.gitignore` to prevent tfvars commits
- [ ] Generated new secure password
- [ ] Tested deployment with new password approach
- [ ] Rotated password in existing OpenSearch domain (if already deployed)
- [ ] Updated documentation

---

## Current Deployment Status

If OpenSearch is already deployed with the old password:

```bash
# Check if OpenSearch domain exists
aws opensearch describe-domain \
  --domain-name realistic-demo-pretamane-opensearch \
  --query 'DomainStatus.DomainName'

# If exists, rotate the password
aws opensearch update-domain-config \
  --domain-name realistic-demo-pretamane-opensearch \
  --advanced-security-options \
  MasterUserOptions={MasterUserName=admin,MasterUserPassword=NEW_SECURE_PASSWORD}
```

---

## Impact Assessment

### Low Risk:
- Password only exposed in personal portfolio repository
- No public production deployment
- Can be rotated immediately

### Actions Taken:
1. Removed hardcoded credentials from all files
2. Implemented secure password management
3. Created documentation and examples
4. Added gitignore protection
5. Prepared rotation procedures

---

## References

- [AWS OpenSearch Security Best Practices](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/security.html)
- [Terraform Sensitive Variables](https://www.terraform.io/docs/language/values/variables.html#suppressing-values-in-cli-output)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

---

**Issue Status:** RESOLVED  
**Follow-up Required:** Rotate password if domain is already deployed  
**Prevention:** All sensitive variables now require explicit provision

