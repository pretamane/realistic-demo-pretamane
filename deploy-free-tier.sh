#!/bin/bash

# /deploy-free-tier.sh
# Free Tier Optimized Deployment Script

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
FREE_TIER_MODE=true

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

# Function to create Terraform backend
create_terraform_backend() {
    log "Creating Terraform backend infrastructure..."
    cd terraform/modules/backend
    terraform init -upgrade
    terraform apply -auto-approve -var "project_name=$PROJECT_NAME" -var "region=$REGION"
    BUCKET_NAME=$(terraform output -raw s3_bucket_id)
    DYNAMODB_TABLE=$(terraform output -raw dynamodb_table_name)
    log_success "Backend infrastructure created!"
    log "S3 Bucket: $BUCKET_NAME"
    log "DynamoDB Table: $DYNAMODB_TABLE"
    cd ../../.. # Navigate back to the root directory
}

# Function to deploy main infrastructure
deploy_infrastructure() {
    log "Deploying Free Tier optimized infrastructure..."
    cd terraform
    terraform init -upgrade
    terraform plan -var "free_tier_mode=true" -out=tfplan
    terraform apply tfplan
    log_success "Infrastructure deployed successfully!"
    cd ..
}

# Function to configure kubectl
configure_kubectl() {
    log "Configuring kubectl..."
    aws eks update-kubeconfig --region $REGION --name $PROJECT_NAME-cluster
    log_success "kubectl configured!"
}

# Function to deploy Kubernetes manifests
deploy_kubernetes() {
    log "Deploying Kubernetes manifests..."
    
    # Create namespace
    kubectl create namespace amazon-cloudwatch --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy service account
    kubectl apply -f k8s/serviceaccount.yaml
    
    # Deploy ConfigMap
    kubectl apply -f k8s/configmap.yaml
    
    # Deploy EFS storage
    kubectl apply -f k8s/efs-pv.yaml
    
    # Deploy AWS credentials secret (you need to update this with actual credentials)
    log_warning "Please update k8s/aws-credentials-secret.yaml with your AWS credentials before proceeding"
    kubectl apply -f k8s/aws-credentials-secret.yaml
    
    # Deploy Free Tier optimized deployment
    kubectl apply -f k8s/free-tier-deployment.yaml
    
    # Deploy service
    kubectl apply -f k8s/service.yaml
    
    # Deploy HPA (minimal configuration)
    kubectl apply -f k8s/hpa.yaml
    
    # Deploy ingress
    kubectl apply -f k8s/ingress.yaml
    
    log_success "Kubernetes manifests deployed!"
}

# Function to wait for deployment
wait_for_deployment() {
    log "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/contact-api-free-tier
    log_success "Deployment is ready!"
}

# Function to show deployment status
show_status() {
    log "Deployment Status:"
    echo "=================="
    
    # Show pods
    echo "📦 Pods:"
    kubectl get pods -l app=contact-api
    
    echo ""
    echo "🌐 Services:"
    kubectl get svc
    
    echo ""
    echo "📊 HPA Status:"
    kubectl get hpa
    
    echo ""
    echo "💾 Persistent Volumes:"
    kubectl get pv,pvc
    
    echo ""
    echo "🔗 Ingress:"
    kubectl get ingress
}

# Function to show cost information
show_cost_info() {
    log "Free Tier Cost Information:"
    echo "=========================="
    echo "💰 Estimated Monthly Cost: $0.00 (Free Tier)"
    echo "📊 Resources Used:"
    echo "   - EKS Cluster: Free (first 12 months)"
    echo "   - EC2 t3.micro: Free (750 hours/month)"
    echo "   - EFS: Free (5GB)"
    echo "   - DynamoDB: Free (25GB)"
    echo "   - S3: Free (5GB)"
    echo "   - CloudWatch: Free (10 metrics, 5GB logs)"
    echo ""
    echo "⚠️  Note: This deployment is optimized for AWS Free Tier"
    echo "   - Single node cluster"
    echo "   - Minimal resource requests"
    echo "   - No auto-scaling"
    echo "   - Basic monitoring only"
}

# Function to setup cleanup
setup_cleanup() {
    log "Setting up automatic cleanup after 1 hour..."
    
    # Create cleanup script
    cat > cleanup-free-tier.sh << 'EOF'
#!/bin/bash
echo "🧹 Cleaning up Free Tier deployment..."

# Delete Kubernetes resources
kubectl delete -f k8s/ingress.yaml --ignore-not-found=true
kubectl delete -f k8s/hpa.yaml --ignore-not-found=true
kubectl delete -f k8s/service.yaml --ignore-not-found=true
kubectl delete -f k8s/free-tier-deployment.yaml --ignore-not-found=true
kubectl delete -f k8s/aws-credentials-secret.yaml --ignore-not-found=true
kubectl delete -f k8s/efs-pv.yaml --ignore-not-found=true
kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
kubectl delete -f k8s/serviceaccount.yaml --ignore-not-found=true

# Delete Terraform infrastructure
cd terraform
terraform destroy -auto-approve -var "free_tier_mode=true"
cd ..

# Delete backend
cd terraform/modules/backend
terraform destroy -auto-approve -var "project_name=realistic-demo-pretamane" -var "region=ap-southeast-1"
cd ../../..

echo "✅ Free Tier cleanup completed!"
EOF

    chmod +x cleanup-free-tier.sh
    
    # Schedule cleanup
    (sleep 3600 && ./cleanup-free-tier.sh) &
    log_success "Automatic cleanup scheduled for 1 hour from now"
}

# Main deployment function
main() {
    log "🚀 Starting Free Tier Optimized Deployment"
    log "Project: $PROJECT_NAME"
    log "Region: $REGION"
    log "Free Tier Mode: $FREE_TIER_MODE"
    echo ""
    
    check_prerequisites
    create_terraform_backend
    deploy_infrastructure
    configure_kubectl
    deploy_kubernetes
    wait_for_deployment
    show_status
    show_cost_info
    setup_cleanup
    
    log_success "🎉 Free Tier deployment completed successfully!"
    log "Your application is now running on AWS Free Tier!"
    log "Access your application via the ingress URL shown above"
    log "Automatic cleanup will occur in 1 hour"
}

# Run main function
main "$@"
