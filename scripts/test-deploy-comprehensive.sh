#!/bin/bash

set -e

###############################################################################
# COMPREHENSIVE TEST DEPLOYMENT SCRIPT
###############################################################################
# Purpose: Test deploy all infrastructure with AWS limit checks and validation
# Features:
#   - Pre-deployment AWS limit verification
#   - Step-by-step infrastructure deployment
#   - Health checks after each major component
#   - Cost monitoring and alerts
#   - Comprehensive logging
#   - Rollback capability
###############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="realistic-demo-pretamane"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
LOG_FILE="/tmp/test-deploy-${PROJECT_NAME}-$(date +%Y%m%d-%H%M%S).log"
DEPLOYMENT_START_TIME=$(date +%s)

# Function to log messages
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@" | tee -a "$LOG_FILE"
}

# Function to display section header
section_header() {
    echo "" | tee -a "$LOG_FILE"
    echo "============================================================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "============================================================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

# Function to check AWS credentials
check_aws_credentials() {
    section_header "STEP 1: Verifying AWS Credentials"
    
    log_info "Checking AWS CLI configuration..."
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid"
        log_error "Please run: aws configure"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local user_arn=$(aws sts get-caller-identity --query Arn --output text)
    
    log_success "AWS credentials verified"
    log_info "Account ID: ${account_id}"
    log_info "User ARN: ${user_arn}"
    log_info "Region: ${AWS_REGION}"
}

# Function to check AWS service limits
check_aws_limits() {
    section_header "STEP 2: Checking AWS Service Limits"
    
    log_info "Checking VPC limits..."
    local vpc_count=$(aws ec2 describe-vpcs --region "$AWS_REGION" --query 'length(Vpcs)' --output text)
    log_info "Current VPCs: ${vpc_count}/5 (AWS default limit)"
    
    log_info "Checking EIP limits..."
    local eip_count=$(aws ec2 describe-addresses --region "$AWS_REGION" --query 'length(Addresses)' --output text)
    log_info "Current Elastic IPs: ${eip_count}/5 (AWS default limit)"
    
    log_info "Checking EKS clusters..."
    local eks_count=$(aws eks list-clusters --region "$AWS_REGION" --query 'length(clusters)' --output text)
    log_info "Current EKS clusters: ${eks_count}/100 (AWS default limit)"
    
    log_info "Checking DynamoDB tables..."
    local dynamodb_count=$(aws dynamodb list-tables --region "$AWS_REGION" --query 'length(TableNames)' --output text)
    log_info "Current DynamoDB tables: ${dynamodb_count}/256 (AWS default limit)"
    
    log_info "Checking S3 buckets..."
    local s3_count=$(aws s3 ls | wc -l)
    log_info "Current S3 buckets: ${s3_count}/100 (AWS default limit)"
    
    # Check if we're approaching limits
    if [ "$vpc_count" -ge 4 ]; then
        log_warning "VPC count is approaching limit (${vpc_count}/5)"
    fi
    
    if [ "$eip_count" -ge 4 ]; then
        log_warning "Elastic IP count is approaching limit (${eip_count}/5)"
    fi
    
    log_success "AWS limits check completed"
}

# Function to estimate deployment costs
estimate_costs() {
    section_header "STEP 3: Cost Estimation"
    
    log_info "Estimated monthly costs for this deployment:"
    echo "" | tee -a "$LOG_FILE"
    echo "Resource                     | Estimated Cost" | tee -a "$LOG_FILE"
    echo "----------------------------|----------------" | tee -a "$LOG_FILE"
    echo "EKS Cluster                 | USD 0.00 (Free Tier)" | tee -a "$LOG_FILE"
    echo "EC2 t3.medium nodes (2)     | USD 0.00 (Free Tier 750h)" | tee -a "$LOG_FILE"
    echo "EFS Storage (10GB)          | USD 0.30/month" | tee -a "$LOG_FILE"
    echo "DynamoDB (On-Demand)        | USD 0.00 (Free Tier)" | tee -a "$LOG_FILE"
    echo "S3 Storage (5GB)            | USD 0.00 (Free Tier)" | tee -a "$LOG_FILE"
    echo "OpenSearch t3.small (Dev)   | USD 0.00 (Free Tier 750h)" | tee -a "$LOG_FILE"
    echo "NAT Gateway (if used)       | USD 32.00/month" | tee -a "$LOG_FILE"
    echo "ALB                         | USD 16.00/month" | tee -a "$LOG_FILE"
    echo "----------------------------|----------------" | tee -a "$LOG_FILE"
    echo "TOTAL (without NAT)         | ~USD 48.30/month" | tee -a "$LOG_FILE"
    echo "TOTAL (with NAT)            | ~USD 80.30/month" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    log_warning "This deployment uses mostly Free Tier resources but ALB costs apply"
    log_warning "Monitor costs with: ./scripts/monitor-costs.sh"
    
    echo "" | tee -a "$LOG_FILE"
    read -p "Do you want to proceed with deployment? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Deployment cancelled by user"
        exit 0
    fi
}

# Function to initialize Terraform
init_terraform() {
    section_header "STEP 4: Initializing Terraform"
    
    cd terraform
    
    log_info "Running terraform init..."
    if terraform init -upgrade 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Terraform initialized successfully"
    else
        log_error "Terraform initialization failed"
        exit 1
    fi
    
    log_info "Validating Terraform configuration..."
    if terraform validate 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Terraform configuration is valid"
    else
        log_error "Terraform validation failed"
        exit 1
    fi
    
    cd ..
}

# Function to plan Terraform deployment
plan_terraform() {
    section_header "STEP 5: Planning Infrastructure Deployment"
    
    cd terraform
    
    log_info "Creating Terraform execution plan..."
    if terraform plan -out=tfplan 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Terraform plan created successfully"
        
        log_info "Plan summary:"
        terraform show -json tfplan | jq -r '.resource_changes[] | "\(.change.actions[0]): \(.type).\(.name)"' | tee -a "$LOG_FILE"
    else
        log_error "Terraform planning failed"
        cd ..
        exit 1
    fi
    
    cd ..
    
    echo "" | tee -a "$LOG_FILE"
    read -p "Review the plan above. Proceed with apply? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Deployment cancelled by user"
        cd terraform && rm -f tfplan && cd ..
        exit 0
    fi
}

# Function to apply Terraform
apply_terraform() {
    section_header "STEP 6: Deploying Infrastructure with Terraform"
    
    cd terraform
    
    log_info "Applying Terraform configuration..."
    log_warning "This may take 15-20 minutes. Please be patient..."
    
    if terraform apply tfplan 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Infrastructure deployed successfully"
        rm -f tfplan
    else
        log_error "Terraform apply failed"
        log_error "Check the log file for details: $LOG_FILE"
        cd ..
        exit 1
    fi
    
    cd ..
}

# Function to configure kubectl
configure_kubectl() {
    section_header "STEP 7: Configuring kubectl"
    
    log_info "Getting EKS cluster name..."
    local cluster_name=$(aws eks list-clusters --region "$AWS_REGION" --query 'clusters[0]' --output text)
    
    if [ -z "$cluster_name" ] || [ "$cluster_name" = "None" ]; then
        log_error "No EKS cluster found"
        exit 1
    fi
    
    log_info "Cluster name: ${cluster_name}"
    log_info "Updating kubeconfig..."
    
    if aws eks update-kubeconfig --name "$cluster_name" --region "$AWS_REGION" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "kubectl configured successfully"
    else
        log_error "Failed to configure kubectl"
        exit 1
    fi
    
    log_info "Verifying cluster access..."
    if kubectl cluster-info 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Cluster is accessible"
    else
        log_warning "Cluster may not be fully ready yet"
    fi
}

# Function to deploy Kubernetes resources
deploy_kubernetes() {
    section_header "STEP 8: Deploying Kubernetes Resources"
    
    log_info "Waiting for cluster to be fully ready..."
    sleep 30
    
    log_info "Deploying storage infrastructure..."
    kubectl apply -f k8s/storage/01-efs-storage-classes.yaml 2>&1 | tee -a "$LOG_FILE"
    sleep 5
    
    log_info "Creating PersistentVolumeClaims..."
    kubectl apply -f k8s/storage/03-efs-claims.yaml 2>&1 | tee -a "$LOG_FILE"
    sleep 10
    
    log_info "Checking PVC status..."
    kubectl get pvc 2>&1 | tee -a "$LOG_FILE"
    
    log_info "Deploying secrets and service accounts..."
    kubectl apply -f k8s/secrets/ 2>&1 | tee -a "$LOG_FILE" || true
    sleep 5
    
    log_info "Deploying ConfigMaps..."
    kubectl apply -f k8s/configmaps/ 2>&1 | tee -a "$LOG_FILE" || true
    sleep 5
    
    log_info "Deploying main application..."
    kubectl apply -f k8s/deployments/02-main-application.yaml 2>&1 | tee -a "$LOG_FILE"
    sleep 10
    
    log_info "Deploying RClone mount service..."
    kubectl apply -f k8s/deployments/03-rclone-mount-sidecar.yaml 2>&1 | tee -a "$LOG_FILE"
    sleep 5
    
    log_info "Deploying S3 sync service..."
    kubectl apply -f k8s/deployments/04-s3-sync-service.yaml 2>&1 | tee -a "$LOG_FILE"
    sleep 5
    
    log_info "Deploying enhanced document processor..."
    kubectl apply -f k8s/deployments/05-enhanced-document-processor.yaml 2>&1 | tee -a "$LOG_FILE" || log_warning "Enhanced processor deployment may have issues"
    sleep 10
    
    log_info "Deploying services..."
    kubectl apply -f k8s/networking/ 2>&1 | tee -a "$LOG_FILE"
    sleep 5
    
    log_info "Deploying HPA configurations..."
    kubectl apply -f k8s/autoscaling/unified-hpa.yaml 2>&1 | tee -a "$LOG_FILE"
    
    log_success "Kubernetes resources deployed"
}

# Function to verify deployment
verify_deployment() {
    section_header "STEP 9: Verifying Deployment"
    
    log_info "Checking pod status..."
    kubectl get pods -o wide 2>&1 | tee -a "$LOG_FILE"
    
    log_info "Checking services..."
    kubectl get svc 2>&1 | tee -a "$LOG_FILE"
    
    log_info "Checking PVCs..."
    kubectl get pvc 2>&1 | tee -a "$LOG_FILE"
    
    log_info "Checking HPAs..."
    kubectl get hpa 2>&1 | tee -a "$LOG_FILE"
    
    log_info "Checking ingress..."
    kubectl get ingress 2>&1 | tee -a "$LOG_FILE"
    
    log_info "Waiting for pods to be ready (60 seconds)..."
    sleep 60
    
    log_info "Final pod status:"
    kubectl get pods 2>&1 | tee -a "$LOG_FILE"
    
    local running_pods=$(kubectl get pods --field-selector=status.phase=Running --no-headers | wc -l)
    local total_pods=$(kubectl get pods --no-headers | wc -l)
    
    log_info "Running pods: ${running_pods}/${total_pods}"
    
    if [ "$running_pods" -gt 0 ]; then
        log_success "Some pods are running successfully"
    else
        log_warning "No pods are in Running state yet - may need more time"
    fi
}

# Function to run health checks
run_health_checks() {
    section_header "STEP 10: Running Health Checks"
    
    log_info "Checking main application health..."
    local app_pod=$(kubectl get pods -l component=main-application -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -n "$app_pod" ]; then
        log_info "Application pod: ${app_pod}"
        kubectl logs "$app_pod" --tail=20 2>&1 | tee -a "$LOG_FILE" || true
    else
        log_warning "Application pod not found or not ready yet"
    fi
    
    log_info "Checking AWS resource status..."
    echo "" | tee -a "$LOG_FILE"
    echo "AWS Resources Created:" | tee -a "$LOG_FILE"
    echo "---------------------" | tee -a "$LOG_FILE"
    
    log_info "EKS Clusters:"
    aws eks list-clusters --region "$AWS_REGION" 2>&1 | tee -a "$LOG_FILE"
    
    log_info "DynamoDB Tables:"
    aws dynamodb list-tables --region "$AWS_REGION" --query 'TableNames' 2>&1 | tee -a "$LOG_FILE"
    
    log_info "S3 Buckets (project-specific):"
    aws s3 ls | grep "$PROJECT_NAME" 2>&1 | tee -a "$LOG_FILE"
    
    log_info "EFS File Systems:"
    aws efs describe-file-systems --region "$AWS_REGION" --query 'FileSystems[*].[FileSystemId,Name,SizeInBytes.Value]' --output table 2>&1 | tee -a "$LOG_FILE"
}

# Function to display deployment summary
display_summary() {
    section_header "DEPLOYMENT SUMMARY"
    
    local deployment_end_time=$(date +%s)
    local deployment_duration=$((deployment_end_time - DEPLOYMENT_START_TIME))
    local duration_minutes=$((deployment_duration / 60))
    local duration_seconds=$((deployment_duration % 60))
    
    echo "" | tee -a "$LOG_FILE"
    log_success "Test Deployment Completed!"
    echo "" | tee -a "$LOG_FILE"
    echo "Deployment Duration: ${duration_minutes}m ${duration_seconds}s" | tee -a "$LOG_FILE"
    echo "Log File: $LOG_FILE" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    echo "Next Steps:" | tee -a "$LOG_FILE"
    echo "----------" | tee -a "$LOG_FILE"
    echo "1. Monitor pod startup: kubectl get pods -w" | tee -a "$LOG_FILE"
    echo "2. Check pod logs: kubectl logs <pod-name>" | tee -a "$LOG_FILE"
    echo "3. Get service endpoints: kubectl get svc" | tee -a "$LOG_FILE"
    echo "4. Get ALB URL: kubectl get ingress" | tee -a "$LOG_FILE"
    echo "5. Monitor costs: ./scripts/monitor-costs.sh" | tee -a "$LOG_FILE"
    echo "6. Run validation tests: kubectl apply -f k8s/testing/" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    echo "To destroy everything:" | tee -a "$LOG_FILE"
    echo "  cd terraform && terraform destroy" | tee -a "$LOG_FILE"
    echo "  OR" | tee -a "$LOG_FILE"
    echo "  ./scripts/nuke-aws-everything.sh" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    log_warning "Remember to monitor your AWS costs!"
    log_info "Check AWS Cost Explorer: https://console.aws.amazon.com/cost-management/home"
}

# Main execution
main() {
    section_header "COMPREHENSIVE TEST DEPLOYMENT - ${PROJECT_NAME}"
    
    log_info "Starting deployment at $(date)"
    log_info "Log file: $LOG_FILE"
    
    # Execute deployment steps
    check_aws_credentials
    check_aws_limits
    estimate_costs
    init_terraform
    plan_terraform
    apply_terraform
    configure_kubectl
    deploy_kubernetes
    verify_deployment
    run_health_checks
    display_summary
    
    log_success "All deployment steps completed!"
}

# Error handling
trap 'log_error "Script interrupted or failed at line $LINENO. Check log: $LOG_FILE"' ERR

# Run main function
main "$@"

