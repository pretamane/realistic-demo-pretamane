#!/bin/bash
# scripts/lib/prerequisites.sh
# Extracted from: ansible/playbooks/01-terraform-orchestration.yml (lines 24-50)
# Enhanced prerequisites checking with better error handling

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]  $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]   $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]  $1${NC}"
}

# Check AWS CLI installation and version
check_aws_cli() {
    log_info "Checking AWS CLI installation..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        log_info "Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        return 1
    fi
    
    local aws_version=$(aws --version 2>&1 | cut -d/ -f2 | cut -d' ' -f1)
    log_success "AWS CLI installed: version $aws_version"
    
    # Check for minimum version (2.0.0+)
    local major_version=$(echo $aws_version | cut -d. -f1)
    if [ "$major_version" -lt 2 ]; then
        log_warning "AWS CLI version $aws_version detected. Version 2.0+ recommended for better EKS support"
    fi
    
    return 0
}

# Check Terraform installation and version
check_terraform() {
    log_info "Checking Terraform installation..."
    
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed"
        log_info "Install Terraform: https://developer.hashicorp.com/terraform/downloads"
        return 1
    fi
    
    local terraform_version=$(terraform --version | head -n1 | cut -d' ' -f2 | sed 's/v//')
    log_success "Terraform installed: version $terraform_version"
    
    # Check for minimum version (1.0.0+)
    local major_version=$(echo $terraform_version | cut -d. -f1)
    if [ "$major_version" -lt 1 ]; then
        log_warning "Terraform version $terraform_version detected. Version 1.0+ recommended"
    fi
    
    return 0
}

# Check kubectl installation and version
check_kubectl() {
    log_info "Checking kubectl installation..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        log_info "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
        return 1
    fi
    
    local kubectl_version=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 | sed 's/v//')
    if [ -z "$kubectl_version" ]; then
        # Fallback for newer kubectl versions
        kubectl_version=$(kubectl version --client -o json 2>/dev/null | grep -o '"gitVersion":"v[^"]*' | cut -d'"' -f4 | sed 's/v//')
    fi
    
    log_success "kubectl installed: version $kubectl_version"
    return 0
}

# Check Helm installation and version
check_helm() {
    log_info "Checking Helm installation..."
    
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed"
        log_info "Install Helm: https://helm.sh/docs/intro/install/"
        return 1
    fi
    
    local helm_version=$(helm version --short 2>/dev/null | cut -d' ' -f1 | sed 's/v//')
    if [ -z "$helm_version" ]; then
        # Fallback for different helm version output formats
        helm_version=$(helm version 2>/dev/null | grep -o 'Version:"v[^"]*' | cut -d'"' -f2 | sed 's/v//')
    fi
    
    log_success "Helm installed: version $helm_version"
    
    # Check for minimum version (3.0.0+)
    local major_version=$(echo $helm_version | cut -d. -f1)
    if [ "$major_version" -lt 3 ]; then
        log_warning "Helm version $helm_version detected. Version 3.0+ recommended"
    fi
    
    return 0
}

# Verify AWS credentials and permissions
verify_aws_credentials() {
    log_info "Verifying AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        log_info "Configure AWS credentials:"
        log_info "  aws configure"
        log_info "  OR set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
        return 1
    fi
    
    local aws_identity=$(aws sts get-caller-identity 2>/dev/null)
    local account_id=$(echo "$aws_identity" | grep -o '"Account": "[^"]*' | cut -d'"' -f4)
    local user_arn=$(echo "$aws_identity" | grep -o '"Arn": "[^"]*' | cut -d'"' -f4)
    
    log_success "AWS credentials verified"
    log_info "Account ID: $account_id"
    log_info "User/Role: $user_arn"
    
    return 0
}

# Check Docker installation (optional but recommended)
check_docker() {
    log_info "Checking Docker installation (optional)..."
    
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed (optional for local development)"
        log_info "Install Docker: https://docs.docker.com/get-docker/"
        return 0
    fi
    
    if ! docker info &> /dev/null; then
        log_warning "Docker is installed but not running"
        log_info "Start Docker service"
        return 0
    fi
    
    local docker_version=$(docker --version | cut -d' ' -f3 | sed 's/,//')
    log_success "Docker installed and running: version $docker_version"
    
    return 0
}

# Check Git installation
check_git() {
    log_info "Checking Git installation..."
    
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed"
        log_info "Install Git: https://git-scm.com/downloads"
        return 1
    fi
    
    local git_version=$(git --version | cut -d' ' -f3)
    log_success "Git installed: version $git_version"
    
    return 0
}

# Check jq installation (for JSON processing)
check_jq() {
    log_info "Checking jq installation..."
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed (recommended for JSON processing)"
        log_info "Install jq: https://stedolan.github.io/jq/download/"
        return 0
    fi
    
    local jq_version=$(jq --version | sed 's/jq-//')
    log_success "jq installed: version $jq_version"
    
    return 0
}

# Check specific AWS CLI plugins/extensions
check_aws_extensions() {
    log_info "Checking AWS CLI extensions..."
    
    # Check if AWS CLI can access EKS
    if aws eks help &> /dev/null; then
        log_success "AWS EKS CLI support available"
    else
        log_warning "AWS EKS CLI support not available"
    fi
    
    # Check if AWS CLI can access ECR
    if aws ecr help &> /dev/null; then
        log_success "AWS ECR CLI support available"
    else
        log_warning "AWS ECR CLI support not available"
    fi
    
    return 0
}

# Main prerequisites check function
check_all_prerequisites() {
    log_info " Checking all prerequisites..."
    echo ""
    
    local failed_checks=0
    
    # Required tools
    check_aws_cli || ((failed_checks++))
    check_terraform || ((failed_checks++))
    check_kubectl || ((failed_checks++))
    check_helm || ((failed_checks++))
    verify_aws_credentials || ((failed_checks++))
    check_git || ((failed_checks++))
    
    echo ""
    
    # Optional tools
    check_docker
    check_jq
    check_aws_extensions
    
    echo ""
    
    if [ $failed_checks -eq 0 ]; then
        log_success "All required prerequisites met!"
        return 0
    else
        log_error " $failed_checks prerequisite check(s) failed"
        log_info "Please install missing tools and try again"
        return 1
    fi
}

# Enhanced prerequisites check with system info
check_prerequisites_detailed() {
    log_info " Running detailed prerequisites check..."
    echo ""
    
    # System information
    log_info "System Information:"
    log_info "  OS: $(uname -s)"
    log_info "  Architecture: $(uname -m)"
    log_info "  Kernel: $(uname -r)"
    echo ""
    
    # Check all prerequisites
    check_all_prerequisites
    local result=$?
    
    echo ""
    log_info "Prerequisites check completed"
    
    return $result
}

# Quick prerequisites check (essential tools only)
check_prerequisites_quick() {
    local failed_checks=0
    
    command -v aws &> /dev/null || ((failed_checks++))
    command -v terraform &> /dev/null || ((failed_checks++))
    command -v kubectl &> /dev/null || ((failed_checks++))
    command -v helm &> /dev/null || ((failed_checks++))
    aws sts get-caller-identity &> /dev/null || ((failed_checks++))
    
    return $failed_checks
}

# Export functions for use in other scripts
export -f check_aws_cli
export -f check_terraform
export -f check_kubectl
export -f check_helm
export -f verify_aws_credentials
export -f check_docker
export -f check_git
export -f check_jq
export -f check_all_prerequisites
export -f check_prerequisites_detailed
export -f check_prerequisites_quick
