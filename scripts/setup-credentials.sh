#!/bin/bash

# Setup Credentials Script for AWS EKS Portfolio Demo
# This script helps users set up their credentials securely

set -e

echo " AWS EKS Portfolio Demo - Credential Setup"
echo "==========================================="
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "  Warning: .env file already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

echo " Please provide your AWS credentials:"
echo ""

# Get AWS Access Key ID
read -p "AWS Access Key ID: " AWS_ACCESS_KEY_ID
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo " Error: AWS Access Key ID is required"
    exit 1
fi

# Get AWS Secret Access Key
read -s -p "AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo
if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo " Error: AWS Secret Access Key is required"
    exit 1
fi

# Get AWS Region
read -p "AWS Region (default: ap-southeast-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-ap-southeast-1}

echo ""
echo " Optional: OpenSearch credentials (press Enter to skip):"
read -p "OpenSearch Username (default: admin): " OPENSEARCH_USERNAME
OPENSEARCH_USERNAME=${OPENSEARCH_USERNAME:-admin}

read -s -p "OpenSearch Password (default: Admin123!): " OPENSEARCH_PASSWORD
echo
OPENSEARCH_PASSWORD=${OPENSEARCH_PASSWORD:-Admin123!}

read -p "OpenSearch Endpoint: " OPENSEARCH_ENDPOINT

# Create .env file
echo " Creating .env file..."
cat > .env << EOF
# AWS Credentials
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=$AWS_REGION

# OpenSearch Credentials
OPENSEARCH_USERNAME=$OPENSEARCH_USERNAME
OPENSEARCH_PASSWORD=$OPENSEARCH_PASSWORD
OPENSEARCH_ENDPOINT=$OPENSEARCH_ENDPOINT
EOF

# Set file permissions
chmod 600 .env

echo " .env file created successfully"
echo ""

# Create .env.example file
echo " Creating .env.example file..."
cat > .env.example << EOF
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=ap-southeast-1

# OpenSearch Credentials
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=Admin123!
OPENSEARCH_ENDPOINT=https://search-your-domain.us-east-1.es.amazonaws.com
EOF

echo " .env.example file created successfully"
echo ""

# Update .gitignore to include .env
if ! grep -q "\.env" .gitignore; then
    echo " Updating .gitignore to exclude .env file..."
    echo "" >> .gitignore
    echo "# Environment variables" >> .gitignore
    echo ".env" >> .gitignore
    echo " .gitignore updated"
fi

echo ""
echo " Credential setup completed!"
echo ""
echo " Next steps:"
echo "1. Source the environment variables:"
echo "   source .env"
echo ""
echo "2. Deploy the application:"
echo "   ./scripts/secure-deploy.sh"
echo ""
echo "  SECURITY REMINDERS:"
echo "  - Never commit the .env file to version control"
echo "  - The .env file has been added to .gitignore"
echo "  - Use IAM roles with minimal permissions for production"
echo "  - Rotate credentials regularly"
echo ""
echo " For more security information, see: SECURITY_GUIDE.md"
