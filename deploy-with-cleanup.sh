#!/bin/bash
# deploy-with-cleanup.sh - Deploy infrastructure with automatic cleanup after 1 hour

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="realistic-demo-pretamane"
REGION="ap-southeast-1"
CLEANUP_DELAY=3600  # 1 hour in seconds
LOG_FILE="deployment-$(date +%Y%m%d-%H%M%S).log"

# Function to log with timestamp
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

# Function to create backend infrastructure first
create_backend() {
    log "Creating Terraform backend infrastructure..."
    
    cd terraform/modules/backend
    
    # Initialize and apply backend
    terraform init
    terraform plan -var="project_name=$PROJECT_NAME" -var="environment=test"
    terraform apply -var="project_name=$PROJECT_NAME" -var="environment=test" -auto-approve
    
    # Get backend outputs
    BUCKET_NAME=$(terraform output -raw terraform_state_bucket_name)
    DYNAMODB_TABLE=$(terraform output -raw terraform_locks_table_name)
    
    log_success "Backend infrastructure created!"
    log "S3 Bucket: $BUCKET_NAME"
    log "DynamoDB Table: $DYNAMODB_TABLE"
    
    cd ../../..
}

# Function to deploy main infrastructure
deploy_infrastructure() {
    log "Deploying main infrastructure..."
    
    cd terraform
    
    # Initialize with backend
    terraform init
    
    # Plan deployment
    log "Planning infrastructure deployment..."
    terraform plan -out=tfplan
    
    # Apply infrastructure
    log "Applying infrastructure..."
    terraform apply tfplan
    
    # Get outputs
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    CLUSTER_ENDPOINT=$(terraform output -raw cluster_endpoint)
    
    log_success "Infrastructure deployed successfully!"
    log "EKS Cluster: $CLUSTER_NAME"
    log "Cluster Endpoint: $CLUSTER_ENDPOINT"
    
    cd ..
}

# Function to deploy application
deploy_application() {
    log "Deploying application to EKS..."
    
    # Update kubeconfig
    aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME
    
    # Wait for cluster to be ready
    log "Waiting for cluster to be ready..."
    kubectl wait --for=condition=ready node --all --timeout=300s
    
    # Wait for metrics server
    log "Waiting for metrics server..."
    kubectl wait --for=condition=available --timeout=300s deployment/metrics-server -n kube-system || true
    
    # Wait for cluster autoscaler
    log "Waiting for cluster autoscaler..."
    kubectl wait --for=condition=available --timeout=300s deployment/cluster-autoscaler -n kube-system || true
    
    # Deploy application
    cd k8s
    ./deploy.sh
    cd ..
    
    log_success "Application deployed successfully!"
}

# Function to get application URL
get_application_url() {
    log "Getting application URL..."
    
    # Wait for ingress to be ready
    kubectl wait --for=condition=ready --timeout=300s ingress/contact-api-ingress || true
    
    # Get ALB endpoint
    ALB_ENDPOINT=$(kubectl get ingress contact-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    
    if [ "$ALB_ENDPOINT" != "pending" ] && [ -n "$ALB_ENDPOINT" ]; then
        log_success "Application is accessible at: http://$ALB_ENDPOINT"
        log "API Documentation: http://$ALB_ENDPOINT/docs"
        log "Health Check: http://$ALB_ENDPOINT/health"
    else
        log_warning "ALB endpoint not ready yet. Check with: kubectl get ingress"
    fi
}

# Function to setup cleanup
setup_cleanup() {
    log "Setting up automatic cleanup in $CLEANUP_DELAY seconds (1 hour)..."
    
    # Create cleanup script
    cat > cleanup.sh << EOF
#!/bin/bash
# Auto-generated cleanup script

set -e

echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] 🧹 Starting automatic cleanup...${NC}"

# Clean up Kubernetes resources
echo "Cleaning up Kubernetes resources..."
kubectl delete -f k8s/ --ignore-not-found=true || true

# Clean up Terraform infrastructure
echo "Cleaning up Terraform infrastructure..."
cd terraform
terraform destroy -auto-approve || true
cd ..

# Clean up backend infrastructure
echo "Cleaning up backend infrastructure..."
cd terraform/modules/backend
terraform destroy -auto-approve || true
cd ../..

echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Cleanup completed!${NC}"
EOF

    chmod +x cleanup.sh
    
    # Schedule cleanup
    (sleep $CLEANUP_DELAY && ./cleanup.sh) &
    CLEANUP_PID=$!
    
    log_success "Cleanup scheduled! PID: $CLEANUP_PID"
    log "Cleanup will run automatically in 1 hour"
    log "To cancel cleanup: kill $CLEANUP_PID"
    
    # Save cleanup PID for reference
    echo $CLEANUP_PID > cleanup.pid
}

# Function to show deployment status
show_status() {
    log "Deployment Status:"
    echo "=================="
    
    # Terraform status
    cd terraform
    terraform show -json | jq -r '.values.root_module.resources[] | select(.type | startswith("aws_")) | "\(.type): \(.values.tags.Name // .name)"' 2>/dev/null || echo "Terraform resources deployed"
    cd ..
    
    # Kubernetes status
    echo ""
    echo "Kubernetes Resources:"
    kubectl get pods,svc,ingress,hpa 2>/dev/null || echo "Kubernetes resources deployed"
    
    # Application status
    echo ""
    echo "Application Status:"
    ALB_ENDPOINT=$(kubectl get ingress contact-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    if [ "$ALB_ENDPOINT" != "pending" ] && [ -n "$ALB_ENDPOINT" ]; then
        echo "✅ Application URL: http://$ALB_ENDPOINT"
        echo "📚 API Docs: http://$ALB_ENDPOINT/docs"
        echo "🔍 Health: http://$ALB_ENDPOINT/health"
    else
        echo "⏳ Application URL: Pending ALB creation"
    fi
}

# Function to test application
test_application() {
    log "Testing application..."
    
    ALB_ENDPOINT=$(kubectl get ingress contact-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    
    if [ -n "$ALB_ENDPOINT" ]; then
        # Test health endpoint
        log "Testing health endpoint..."
        if curl -s "http://$ALB_ENDPOINT/health" | grep -q "healthy"; then
            log_success "Health check passed!"
        else
            log_warning "Health check failed or endpoint not ready"
        fi
        
        # Test root endpoint
        log "Testing root endpoint..."
        if curl -s "http://$ALB_ENDPOINT/" | grep -q "Contact Form API"; then
            log_success "Root endpoint working!"
        else
            log_warning "Root endpoint not responding"
        fi
    else
        log_warning "ALB endpoint not ready for testing"
    fi
}

# Main deployment function
main() {
    log "🚀 Starting deployment with automatic cleanup..."
    log "Project: $PROJECT_NAME"
    log "Region: $REGION"
    log "Cleanup in: $CLEANUP_DELAY seconds (1 hour)"
    log "Log file: $LOG_FILE"
    
    # Check prerequisites
    check_prerequisites
    
    # Create backend infrastructure
    create_backend
    
    # Deploy main infrastructure
    deploy_infrastructure
    
    # Deploy application
    deploy_application
    
    # Get application URL
    get_application_url
    
    # Setup cleanup
    setup_cleanup
    
    # Show status
    show_status
    
    # Test application
    test_application
    
    log_success "🎉 Deployment completed successfully!"
    log "📋 Next steps:"
    log "   1. Test your application at the provided URL"
    log "   2. Check API documentation at /docs"
    log "   3. Monitor with: kubectl get pods,svc,ingress"
    log "   4. Cleanup will run automatically in 1 hour"
    log "   5. To cancel cleanup: kill \$(cat cleanup.pid)"
    
    log "📊 Cost monitoring:"
    log "   - EKS cluster: ~$0.10/hour"
    log "   - EC2 instances: ~$0.02/hour (t3.small SPOT)"
    log "   - ALB: ~$0.02/hour"
    log "   - DynamoDB: Pay-per-request (minimal cost)"
    log "   - Total estimated cost: ~$0.15/hour"
}

# Trap to handle script interruption
trap 'log_error "Script interrupted. Cleanup may be needed manually."; exit 1' INT TERM

# Run main function
main "$@"
