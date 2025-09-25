# 🚀 Realistic Demo - Cloud-Native Portfolio Project

**Full-Stack Cloud-Native Application with Advanced Mounting Techniques**

A production-ready, cost-optimized contact form API deployed on AWS EKS with comprehensive monitoring, auto-scaling, and advanced storage mounting patterns. Perfect for portfolio demonstrations and learning modern DevOps practices.

## 📁 **Project Structure**

```
realistic-demo-pretamane/
├── 📁 scripts/           # All shell scripts
│   ├── setup-credentials.sh      # Interactive credential setup
│   ├── secure-deploy.sh          # Secure deployment script
│   ├── deploy-comprehensive.sh   # Full deployment
│   ├── cleanup-comprehensive.sh  # Cleanup script
│   ├── nuke-aws-everything.sh    # Complete AWS cleanup
│   ├── monitor-costs.sh          # Cost monitoring
│   └── ... (other scripts)
├── 📁 docs/              # All documentation
│   ├── README.md                 # Main documentation
│   ├── SECURITY_GUIDE.md         # Security best practices
│   ├── DEPLOYMENT_GUIDE.md       # Deployment instructions
│   ├── TECH_SUPPORT_TEST_SCENARIOS.md  # Test scenarios
│   └── ... (other docs)
├── 📁 k8s/               # Kubernetes manifests
│   ├── portfolio-demo.yaml       # Main application
│   ├── hpa.yaml                  # Auto-scaling config
│   └── ... (other manifests)
├── 📁 terraform/         # Infrastructure as Code
│   ├── main.tf                   # Main Terraform config
│   └── modules/                  # Terraform modules
├── 📁 docker/            # Docker configurations
│   └── api/                      # FastAPI application
└── 📁 lambda-code/       # AWS Lambda functions
```

## 🚀 **Quick Start**

### **1. Secure Setup (Recommended)**
```bash
# Set up credentials interactively
./scripts/setup-credentials.sh

# Source environment variables
source .env

# Deploy securely
./scripts/secure-deploy.sh
```

### **2. Full Deployment**
```bash
# Deploy complete infrastructure
./scripts/deploy-comprehensive.sh

# Monitor costs
./scripts/monitor-costs.sh

# Clean up when done
./scripts/cleanup-comprehensive.sh
```

### **3. Emergency Cleanup**
```bash
# Nuclear option - destroys everything
./scripts/nuke-aws-everything.sh
```

## 🔐 **Security First**

This project prioritizes security with:
- ✅ **No hardcoded credentials** in any files
- ✅ **Environment variable management**
- ✅ **Interactive credential setup**
- ✅ **Secure deployment scripts**
- ✅ **Comprehensive security documentation**

**See [docs/SECURITY_GUIDE.md](docs/SECURITY_GUIDE.md) for detailed security practices.**

## 📚 **Documentation**

All documentation is organized in the `docs/` folder:

- **[docs/README.md](docs/README.md)** - Complete project documentation
- **[docs/SECURITY_GUIDE.md](docs/SECURITY_GUIDE.md)** - Security best practices
- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[docs/TECH_SUPPORT_TEST_SCENARIOS.md](docs/TECH_SUPPORT_TEST_SCENARIOS.md)** - Test scenarios
- **[docs/PORTFOLIO_SHOWCASE_SCRIPT.md](docs/PORTFOLIO_SHOWCASE_SCRIPT.md)** - Demo script

## 🎯 **Key Features**

### **Advanced Kubernetes Patterns**
- ✅ **RClone Sidecar** - S3 bucket mounting as local filesystem
- ✅ **Init Containers** - Data preparation and configuration setup
- ✅ **EFS Persistent Volumes** - Shared file system across pods
- ✅ **Multi-container Pods** - Sidecar and init container patterns

### **AWS Integration**
- ✅ **EKS Cluster** with managed node groups
- ✅ **DynamoDB** for contact submissions and visitor tracking
- ✅ **SES** for email notifications
- ✅ **CloudWatch** for comprehensive monitoring
- ✅ **EFS** for shared storage
- ✅ **OpenSearch** for document indexing

### **Cost Optimization**
- ✅ **AWS Free Tier** optimized configuration
- ✅ **Automatic cleanup** scripts
- ✅ **Resource monitoring** and cost alerts
- ✅ **Efficient resource allocation**

## 🛠️ **Scripts Overview**

### **Setup & Deployment**
- `scripts/setup-credentials.sh` - Interactive credential setup
- `scripts/secure-deploy.sh` - Secure deployment with credential validation
- `scripts/deploy-comprehensive.sh` - Full infrastructure deployment

### **Monitoring & Testing**
- `scripts/monitor-costs.sh` - AWS cost monitoring
- `scripts/effective-autoscaling-test.sh` - Auto-scaling tests
- `scripts/quick-portfolio-demo.sh` - Quick demo script

### **Cleanup**
- `scripts/cleanup-comprehensive.sh` - Comprehensive cleanup
- `scripts/cleanup-now.sh` - Quick cleanup
- `scripts/nuke-aws-everything.sh` - Complete AWS resource destruction

## 🔧 **Development**

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

# Set up credentials
./scripts/setup-credentials.sh

# Deploy
./scripts/secure-deploy.sh
```

## 📈 **Performance Metrics**

- **Startup Time**: < 2 minutes
- **Cost**: $0/month (Free Tier)
- **Auto-scaling**: 1-10 pods based on load
- **Storage**: EFS + S3 integration
- **Monitoring**: CloudWatch + custom metrics

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is for educational and portfolio purposes.

## 🆘 **Support**

- Check [docs/TECH_SUPPORT_TEST_SCENARIOS.md](docs/TECH_SUPPORT_TEST_SCENARIOS.md) for troubleshooting
- Review [docs/SECURITY_GUIDE.md](docs/SECURITY_GUIDE.md) for security issues
- See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for deployment help

---

**🚀 Ready to deploy your cloud-native portfolio project!**
