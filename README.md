# Enterprise Cloud-Native Platform | AWS EKS

**Production-Ready Document Management & Contact Intelligence System**

A complete, enterprise-grade cloud-native platform deployed on AWS EKS, demonstrating senior-level DevOps, Cloud Architecture, and Platform Engineering expertise.

**Built to Showcase:**
- Multi-Container Kubernetes Architecture
- Advanced AWS Services Integration (15+ services)
- Production Security & Operational Excellence
- Cost-Optimized Infrastructure ($0/month on Free Tier)

## Project Structure

```
realistic-demo-pretamane/
├── scripts/           # All shell scripts
│   ├── setup-credentials.sh      # Interactive credential setup
│   ├── secure-deploy.sh          # Secure deployment script
│   ├── deploy-comprehensive.sh   # Full deployment
│   ├── cleanup-comprehensive.sh  # Cleanup script
│   ├── nuke-aws-everything.sh    # Complete AWS cleanup
│   ├── monitor-costs.sh          # Cost monitoring
│   └── ... (other scripts)
├── docs/              # All documentation
│   ├── README.md                 # Main documentation
│   ├── SECURITY_GUIDE.md         # Security best practices
│   ├── DEPLOYMENT_GUIDE.md       # Deployment instructions
│   ├── TECH_SUPPORT_TEST_SCENARIOS.md  # Test scenarios
│   └── ... (other docs)
├── k8s/               # Advanced Kubernetes manifests (PRODUCTION READY)
│   ├── deployments/              # Multi-container applications (329-line FastAPI)
│   ├── networking/               # Services & ingress (dual ingress + SSL)
│   ├── autoscaling/              # HPA configurations (multi-service scaling)
│   ├── storage/                  # EFS & storage classes (advanced mounting)
│   ├── secrets/                  # Security configurations (IRSA + secrets)
│   ├── testing/                  # Validation containers (17 comprehensive tests)
│   └── kustomization.yaml        # GitOps-ready Kustomize configuration
├── terraform/         # Infrastructure as Code
│   ├── main.tf                   # Main Terraform config
│   └── modules/                  # Terraform modules
├── docker/            # Docker configurations
│   └── api/                      # FastAPI application
└── lambda-code/       # AWS Lambda functions
```

## **Quick Start**

### **1. Enhanced Deployment (Recommended)**
```bash
# Set up credentials interactively
./scripts/setup-secure-credentials.sh

# Source environment variables
source config/environments/production.env

# Deploy with enhanced script
./scripts/deploy-enhanced.sh
```

### **2. Advanced Kubernetes Deployment**
```bash
# Deploy using Kustomize (GitOps-ready)
kubectl apply -k k8s/

# Or deploy modular components
kubectl apply -f k8s/storage/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/networking/
kubectl apply -f k8s/autoscaling/
```

### **3. Monitoring & Cleanup**
```bash
# Monitor system health
./scripts/monitoring/health-checks.sh

# Monitor costs
./scripts/monitor-costs.sh

# Clean up when done
./scripts/cleanup-comprehensive.sh
```

### **4. Emergency Cleanup**
```bash
# Nuclear option - destroys everything
./scripts/nuke-aws-everything.sh
```

## **Security First**

This project prioritizes security with:
- **No hardcoded credentials** in any files
- **Modern config management** (`config/environments/production.env`)
- **IAM Roles for Service Accounts (IRSA)**
- **Secure deployment scripts** with validation
- **Comprehensive security documentation**
- **AWS cost protection system** with auto-cleanup

**See [docs/security/SECURITY_CREDENTIALS_GUIDE.md](docs/security/SECURITY_CREDENTIALS_GUIDE.md) for detailed security practices.**
**See [docs/security/AWS_COST_PROTECTION_GUIDE.md](docs/security/AWS_COST_PROTECTION_GUIDE.md) for cost protection strategies.**

## **Documentation**

All documentation is organized in the `docs/` folder:

- **[docs/README.md](docs/README.md)** - Master documentation index
- **[docs/security/SECURITY_CREDENTIALS_GUIDE.md](docs/security/SECURITY_CREDENTIALS_GUIDE.md)** - Security best practices
- **[docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[docs/TECH_SUPPORT_TEST_SCENARIOS.md](docs/TECH_SUPPORT_TEST_SCENARIOS.md)** - Test scenarios
- **[docs/PORTFOLIO_SHOWCASE_SCRIPT.md](docs/PORTFOLIO_SHOWCASE_SCRIPT.md)** - Demo script
- **[docs/analysis/](docs/analysis/)** - Project analysis and migration docs
- **[docs/guides/](docs/guides/)** - Technical guides and setup instructions

## **Key Features**

### **Advanced Kubernetes Patterns**
- **Dynamic EFS Provisioning** - Automatic access point creation with CSI driver v2.x
- **Multi-Container Applications** - Enhanced document processor with analytics & search
- **Storage Isolation** - 4 StorageClasses with automatic per-PVC isolation
- **RClone Sidecar** - Real-time S3 bucket mounting as local filesystem
- **S3 Sync Service** - Scheduled backup and synchronization
- **Init Containers** - Comprehensive data preparation and setup
- **Horizontal Pod Autoscaling** - 6 HPAs with advanced scaling policies
- **Kustomize Integration** - GitOps-ready modular deployments

### **Storage Architecture** (NEW!)
- **Dynamic Provisioning** - CSI driver auto-creates EFS access points
- **4 Storage Tiers** - Advanced (10Gi), Shared (20Gi), Secure (5Gi), Performance
- **Automatic Isolation** - Each PVC gets unique access point for security
- **Permission Control** - uid/gid 1000, configurable directory permissions
- **Auto-Cleanup** - Delete reclaim policy for automatic resource cleanup

### **AWS Integration**
- **EKS Cluster** with managed node groups and auto-scaling
- **EFS with CSI Driver** - Dynamic provisioning, automatic access points
- **DynamoDB** for contact submissions, visitor tracking, and documents
- **OpenSearch** for document indexing and full-text search
- **S3** for object storage (6 buckets with lifecycle policies)
- **SES** for email notifications
- **CloudWatch** for comprehensive monitoring and logging
- **IAM with IRSA** for secure service account access

### **Cost Optimization**
- **AWS Free Tier** optimized configuration
- **Automatic cleanup** scripts
- **Resource monitoring** and cost alerts
- **Efficient resource allocation**

## 🛠️ **Scripts Overview**

### **Setup & Deployment**
- `scripts/setup-secure-credentials.sh` - Interactive credential setup with validation
- `scripts/setup-cost-protection.sh` - One-time cost protection setup
- `scripts/deploy-enhanced.sh` - Enhanced deployment with multiple modes
- `scripts/deploy-comprehensive.sh` - Legacy comprehensive deployment
- `scripts/lib/prerequisites.sh` - Prerequisites checking library

### **Monitoring & Testing**
- `scripts/monitoring/health-checks.sh` - System health monitoring
- `scripts/monitor-costs.sh` - AWS cost monitoring and alerts
- `scripts/cost-protection-guardian.sh` - Enhanced cost protection with auto-cleanup
- `scripts/daily-cost-check.sh` - Daily cost protection reminder
- `scripts/effective-autoscaling-test.sh` - Advanced auto-scaling tests
- `scripts/quick-portfolio-demo.sh` - Quick demo script

### **Cleanup & Maintenance**
- `scripts/cleanup-comprehensive.sh` - Comprehensive cleanup
- `scripts/cleanup-now.sh` - Quick cleanup
- `scripts/nuke-aws-everything.sh` - Complete AWS resource destruction

## **Development**

### **Prerequisites**
- AWS CLI configured
- kubectl installed
- Terraform installed
- Docker installed

### **Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd realistic-demo-pretamane

# Set up credentials securely
./scripts/setup-secure-credentials.sh

# Source environment configuration
source config/environments/production.env

# Deploy with enhanced script
./scripts/deploy-enhanced.sh
```

## **Performance Metrics**

- **Startup Time**: < 2 minutes (enhanced deployment)
- **Cost**: $0/month (AWS Free Tier optimized)
- **Auto-scaling**: Multi-service HPA (1-10 pods per service)
- **Storage**: Advanced EFS + S3 integration (6 buckets)
- **Monitoring**: CloudWatch + Kubernetes metrics + health checks
- **Deployment Modes**: Full, infrastructure-only, app-only, cleanup

## **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## **License**

This project is for educational and portfolio purposes.

## **Support**

- Check [docs/TECH_SUPPORT_TEST_SCENARIOS.md](docs/TECH_SUPPORT_TEST_SCENARIOS.md) for troubleshooting
- Review [docs/security/SECURITY_CREDENTIALS_GUIDE.md](docs/security/SECURITY_CREDENTIALS_GUIDE.md) for security issues
- See [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md) for deployment help
- Browse [docs/README.md](docs/README.md) for complete documentation index
- Check [docs/analysis/](docs/analysis/) for project evolution and migration docs

---

## **Current Architecture**

### **Application Components**
```
┌─────────────────────────────────────────────────────────┐
│                  AWS EKS Cluster                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Main Application (contact-api-advanced)         │  │
│  │  - FastAPI application (8000)                     │  │
│  │  - Contact form processing                        │  │
│  │  - Document upload & management                   │  │
│  │  - EFS storage: /mnt/efs                          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Enhanced Document Processor                      │  │
│  │  ├─ FastAPI App (port 8000)                       │  │
│  │  ├─ Analytics Engine (background)                 │  │
│  │  └─ Search Index Manager (background)             │  │
│  │  - Multi-container pod architecture               │  │
│  │  - OpenSearch integration                         │  │
│  │  - Real-time document analysis                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  RClone Mount Service                             │  │
│  │  - Real-time S3 mounting (data/index/realtime)   │  │
│  │  - VFS caching for performance                    │  │
│  │  - Auto-remount on failure                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  S3 Sync Service                                  │  │
│  │  - Scheduled sync to archive/logs/backup         │  │
│  │  - Retention policy enforcement                   │  │
│  │  - Automated cleanup (30-day retention)           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### **Storage Architecture (Dynamic Provisioning)**
```
EFS File System (fs-0b3a076e9c8805489)
    │
    ├── Access Point 1 (auto-created) → advanced-efs-pvc (10Gi)
    │   └── Permissions: 0755, uid/gid: 1000
    │
    ├── Access Point 2 (auto-created) → shared-efs-pvc (20Gi)  
    │   └── Permissions: 0755, uid/gid: 1000
    │
    └── Access Point 3 (auto-created) → secure-efs-pvc (5Gi)
        └── Permissions: 0750, uid/gid: 1000 (restricted)
        
Benefits:
Automatic isolation per PVC
No manual access point creation
CSI driver handles everything
Delete reclaim policy (auto-cleanup)
```

### **Kubernetes Resources**
- **Deployments:** 4 (Main app, Enhanced processor, RClone, S3 Sync)
- **Services:** 7 (ClusterIP + LoadBalancer endpoints)
- **Ingresses:** 4 (Public + Internal, Basic + Enhanced)
- **HPAs:** 6 (Multi-service auto-scaling)
- **StorageClasses:** 4 (Dynamic provisioning enabled)
- **PVCs:** 3 (Auto-provisioned with isolated access points)
- **ConfigMaps:** 2 (App config + Enhanced config)
- **Secrets:** 3 (AWS creds, OpenSearch, SES)

### **Recent Bug Fixes & Improvements**
- Fixed PVC name mismatch (efs-pvc-advanced → advanced-efs-pvc)
- Removed conflicting StorageClass parameters
- Migrated to dynamic EFS provisioning (security improvement)
- Resolved EFS CSI driver v2.x compatibility issues
- Implemented automatic storage isolation per tier
- Backend reverted to S3 for state management
- All configurations tested and validated

---

## **Project Evolution Highlights**

This project has undergone significant evolution and optimization:

### **Recent Improvements:**
- **Ansible Migration**: Migrated from Ansible to enhanced Bash + Kustomize approach
- **Advanced Organization**: Consolidated from 54+ files to clean modular structure
- **Enhanced Deployment**: New `scripts/deploy-enhanced.sh` with multiple modes
- **⚙️ Modern Config**: Centralized configuration in `config/environments/`
- **Documentation Cleanup**: Organized 25+ docs into structured `docs/` hierarchy
- **Kustomize Integration**: GitOps-ready with `k8s/kustomization.yaml`
- **🧹 File Consolidation**: Removed redundant files, kept only production-ready components

### **Current State:**
- **Production Ready**: Advanced Kubernetes setup with industry best practices
- **Cost Optimized**: $0/month on AWS Free Tier
- **Fully Automated**: One-command deployment with comprehensive validation
- **Enterprise Grade**: Multi-container apps, IRSA, monitoring, auto-scaling
- **Portfolio Perfect**: Demonstrates advanced cloud-native development skills

---

**Ready to deploy your sophisticated cloud-native portfolio project!**
