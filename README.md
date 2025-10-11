# Cloud-Native Document Management Platform

A production-ready, enterprise-grade document processing system built on AWS EKS, demonstrating modern DevOps practices and cloud-native architecture.

## What This Project Does

This platform provides intelligent document management with contact intelligence, featuring:
- Multi-format document upload and processing (17 file types)
- Real-time search powered by OpenSearch
- Contact form with analytics and enrichment
- Automated document indexing and metadata extraction
- Scalable, fault-tolerant architecture

## Architecture Overview

**Infrastructure**: AWS EKS cluster with VPC, EFS, S3, DynamoDB, OpenSearch, Lambda, SES  
**Application**: FastAPI-based microservices with multi-container pods  
**Storage**: Dynamic EFS provisioning with S3 integration via RClone  
**Orchestration**: Kubernetes with HPA, IRSA, and automated scaling  
**IaC**: Terraform with 7 modular components managing 74+ AWS resources

## Tech Stack

```
Cloud:        AWS (15+ services)
Container:    Docker, Kubernetes 1.28+, Amazon ECR
IaC:          Terraform (modular architecture)
Application:  Python 3.11, FastAPI, Boto3
Storage:      EFS (4-tier classes), S3, DynamoDB
Search:       OpenSearch with custom indexing
Monitoring:   CloudWatch, Metrics Server
Security:     IAM IRSA, SSM Session Manager, encrypted storage
```

## Repository Structure

```
realistic-demo-pretamane/
├── terraform/           # Infrastructure as Code (7 modules)
│   ├── modules/        # VPC, EKS, EFS, Storage, Database, IAM, Backend
│   └── main.tf         # Root orchestration
├── k8s/                # Kubernetes manifests
│   ├── deployments/    # 8 deployment variants
│   ├── storage/        # Dynamic EFS provisioning
│   ├── networking/     # Services & ALB Ingress
│   └── autoscaling/    # 6 HPAs with advanced policies
├── docker/             # Container definitions
│   └── api/           # FastAPI app + Dockerfile
├── lambda-code/        # Serverless functions
├── config/             # Environment configs
└── docs/               # Comprehensive documentation
```

## Key Features

**Infrastructure**
- Multi-AZ EKS cluster with auto-scaling nodes
- 4-tier EFS storage (advanced, shared, secure, performance)
- Dynamic provisioning with automatic access point creation
- Cost-optimized with AWS Free Tier compatibility

**Application**
- RESTful API with OpenAPI documentation
- Document upload: PDF, Word, Excel, PowerPoint, images (JPG, PNG, etc.)
- Real-time search with OpenSearch integration
- Contact intelligence with analytics

**DevOps**
- Zero hardcoded credentials (all externalized)
- GitOps-ready with Kustomize
- Comprehensive health checks and monitoring
- Automated backup and archival

## Quick Start

### Prerequisites
```bash
aws-cli, kubectl 1.28+, terraform 1.5+, docker
```

### Deploy Infrastructure
```bash
# 1. Bootstrap backend
cd terraform/modules/backend && terraform init && terraform apply

# 2. Deploy main infrastructure
cd ../.. && terraform init && terraform apply

# 3. Configure kubectl
aws eks update-kubeconfig --name realistic-demo-pretamane-cluster --region ap-southeast-1

# 4. Deploy Kubernetes resources
cd k8s && kubectl apply -k .
```

### Access Application
```bash
# Get ALB URL
kubectl get ingress

# Or use port-forward for local testing
kubectl port-forward deployment/contact-api-complete 8000:8000
```

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /contact` - Submit contact form
- `POST /documents/upload` - Upload document
- `POST /documents/search` - Search documents
- `GET /analytics/insights` - System analytics
- `GET /docs` - Interactive Swagger UI

## Technical Highlights

- **1,145+ lines** of production application code
- **74+ AWS resources** managed via Terraform
- **15+ AWS services** integrated
- **6 HPAs** with sophisticated scaling policies
- **4-tier storage** with dynamic provisioning
- **Multi-container** deployments with sidecars
- **Zero hardcoded** credentials
- **Cost-optimized** for AWS Free Tier

## Project Stats

| Metric | Value |
|--------|-------|
| Terraform Modules | 7 |
| AWS Resources | 74+ |
| Kubernetes Deployments | 8 |
| HPAs | 6 |
| Storage Classes | 4 |
| Supported File Types | 17 |
| Application LoC | 1,145+ |

## Documentation

Detailed documentation available in `docs/`:
- `docs/security/` - Security guides (SSM, credentials, cost protection)
- `docs/deployment/` - Deployment procedures
- `docs/testing/` - Testing guides
- `docs/api-documentation/` - API docs & Postman collection

## Architecture Principles

- **12-Factor App** methodology
- **Infrastructure as Code** for reproducibility
- **Separation of concerns** (app, config, infrastructure)
- **Dynamic provisioning** over static configuration
- **Security by design** (IRSA, encryption, no hardcoded secrets)
- **Cost optimization** (spot instances, pay-per-request, auto-scaling)

## Monitoring & Operations

```bash
# Monitor resources
kubectl top nodes
kubectl top pods
kubectl get hpa

# Access nodes securely
aws ssm start-session --target <instance-id>

# View logs
kubectl logs -f deployment/contact-api-complete
```

## License

Portfolio demonstration project. All rights reserved.

---

**Built with**: AWS, Kubernetes, Terraform, FastAPI, Python  
**Demonstrates**: Cloud architecture, DevOps practices, Infrastructure as Code, Container orchestration
