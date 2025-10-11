#!/bin/bash
# Security Cleanup Script - Remove Hardcoded Credentials
# WARNING: This script modifies files. Review before running.

set -e

echo "=========================================="
echo "SECURITY CLEANUP SCRIPT"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Remove hardcoded OpenSearch password from terraform.tfvars"
echo "2. Replace AWS credentials in documentation with placeholders"
echo "3. Remove Grafana password from Helm config"
echo "4. Update .gitignore"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Step 1: Backing up files..."
mkdir -p /tmp/security-backup
cp terraform/terraform.tfvars /tmp/security-backup/terraform.tfvars.backup
cp docs/security/PHASE_POST_AUTOSCALE_REMOVE_CREDS.md /tmp/security-backup/PHASE_POST_AUTOSCALE_REMOVE_CREDS.md.backup
cp config/helm-repositories.yaml /tmp/security-backup/helm-repositories.yaml.backup
echo "Backups created in /tmp/security-backup/"

echo ""
echo "Step 2: Removing OpenSearch password from terraform.tfvars..."
sed -i '/opensearch_master_password/d' terraform/terraform.tfvars
echo "# OpenSearch password - MUST be provided via environment variable" >> terraform/terraform.tfvars
echo "# export TF_VAR_opensearch_master_password=\$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-20)" >> terraform/terraform.tfvars
echo "Done."

echo ""
echo "Step 3: Replacing AWS credentials in documentation..."
sed -i '132s/.*/  aws-access-key-id: <BASE64_ENCODED_ACCESS_KEY_PLACEHOLDER>/' docs/security/PHASE_POST_AUTOSCALE_REMOVE_CREDS.md
sed -i '133s/.*/  aws-secret-access-key: <BASE64_ENCODED_SECRET_KEY_PLACEHOLDER>/' docs/security/PHASE_POST_AUTOSCALE_REMOVE_CREDS.md
echo "Done."

echo ""
echo "Step 4: Removing Grafana password from Helm config..."
sed -i 's/adminPassword: "admin123"/adminPassword: "CHANGE_ME_IN_PRODUCTION"/' config/helm-repositories.yaml
echo "Done."

echo ""
echo "Step 5: Updating .gitignore..."
if ! grep -q "^terraform.tfvars$" terraform/.gitignore 2>/dev/null; then
    echo "terraform.tfvars" >> terraform/.gitignore
    echo "Added terraform.tfvars to terraform/.gitignore"
fi
echo "Done."

echo ""
echo "=========================================="
echo "CLEANUP COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Generate new OpenSearch password:"
echo "   export TF_VAR_opensearch_master_password=\$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-20)"
echo ""
echo "2. If AWS credentials were real, rotate them IMMEDIATELY:"
echo "   aws iam update-access-key --access-key-id AKIAF7Z6QWJKACIQDD7N --status Inactive"
echo ""
echo "3. Review changes:"
echo "   git diff"
echo ""
echo "4. Commit changes:"
echo "   git add -A"
echo "   git commit -m 'security: Remove hardcoded credentials'"
echo ""
echo "Backups saved in: /tmp/security-backup/"
