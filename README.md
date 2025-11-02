# IaC Task - FastAPI Cloud Infrastructure

A production-ready FastAPI application deployed on AWS using Infrastructure as Code (CDK) with automated CI/CD pipeline via GitHub Actions.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │────│  GitHub Actions  │────│   AWS Account   │
│                 │    │                  │    │                 │
│ • FastAPI Code  │    │ • Build & Test   │    │ • ECS Fargate   │
│ • Dockerfile    │    │ • Push to ECR    │    │ • Load Balancer │
│ • CDK Infra     │    │ • Deploy Stacks  │    │ • CloudWatch    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

This project demonstrates a complete cloud-native application lifecycle:

| Component                               | Purpose          | Technology Stack          |
| --------------------------------------- | ---------------- | ------------------------- |
| **[Web Application](webapp/README.md)** | REST API service | FastAPI, Python, Docker   |
| **[Infrastructure](infra/READ)**        | Cloud resources  | AWS CDK, ECS Fargate, ALB |
| **CI/CD Pipeline**                      | Automation       | GitHub Actions, OIDC      |

> **Quick Navigation**: Start with [local development](#🚀-getting-started) or jump to [AWS deployment](infra/README.md#setup-and-deployment-instructions)

## 📁 Project Structure

```
iac-task/
├── docker-compose.yml          # Local development setup
├── .github/workflows/          # CI/CD automation
├── webapp/                     # 🌐 FastAPI Application
│   ├── README.md               # → API docs, local dev, testing
│   ├── main.py                 # Application code
│   └── tests/                  # Test suite
└── infra/                      # ☁️ AWS Infrastructure
    ├── README.md               # → Deployment, architecture, CI/CD
    ├── deploy.sh               # Deployment scripts
    └── stacks/                 # CDK infrastructure code
```

> **Detailed structure**: See component-specific documentation in [webapp/](webapp/README.md) and [infra/](infra/README.md) directories

## 🚀 Getting Started

### Prerequisites
- **Docker** (recommended) or **>=Python 3.14**
- **AWS Account** (for cloud deployment)

### 1. Run Locally
```bash
git clone <repository-url>
cd iac-task

# Option A: Docker Compose (recommended)
docker compose up --build
# → Access at http://localhost:8000

# Option B: Direct Python (see webapp/README.md for details)
cd webapp && pip install uv && uv sync && uv run uvicorn main:app --reload
```

### 2. Deploy to AWS from host
```bash
cd infra
# Full deployment instructions in infra/README.md
./deploy.sh dev deploy --image_tag <existing_image_tag>
```

### 3. Explore the Application
- **API Endpoints**: See [webapp documentation](webapp/README.md#api-endpoints)
- **Infrastructure**: See [infra documentation](infra/README.md#architecture-overview)
- **API Docs**: http://localhost:8000/docs (when running locally)

## Component Documentation

### 🌐 [Web Application](webapp/README.md)
- **Purpose**: FastAPI REST service with monitoring endpoints
- **Quick Start**: Local development, testing, Docker deployment
- **Key Features**: Health checks, version tracking, configurable responses

### ☁️ [Infrastructure](infra/README.md)
- **Purpose**: AWS cloud resources and deployment automation
- **Quick Start**: CDK setup, AWS deployment, CI/CD configuration
- **Key Features**: ECS Fargate, Load Balancer, Multi-environment support

### CI/CD Pipeline
- **Implementation**: GitHub Actions with OIDC authentication
- **Environments**: Development (auto) → Production (manual approval)
- **Details**: See [Infrastructure Documentation](infra/README.md#ci-cd-pipeline-overview)

## 🔍 Quick Reference

| Task | Command | Documentation |
|------|---------|---------------|
| **Local Development** | `docker compose up --build` | [webapp/README.md](webapp/README.md#running-the-application) |
| **Run Tests** | `cd webapp && uv run pytest` | [webapp/README.md](webapp/README.md#testing) |
| **Deploy to AWS** | `cd infra && ./deploy.sh dev deploy` | [infra/README.md](infra/README.md#deployment-process) |
| **Verify Deployment** | `cd infra && ./check-deployment.sh dev` | [infra/README.md](infra/README.md#deployment-verification) |
| **View API Docs** | http://localhost:8000/docs | [webapp/README.md](webapp/README.md#api-documentation) |

## 🛡️ Security & Monitoring Overview

- **Security**: OIDC authentication, environment isolation, container hardening
- **Monitoring**: Health endpoints, CloudWatch logs, deployment verification
- **Details**: See [Infrastructure Security](infra/README.md#security-features) and [Application Monitoring](webapp/README.md#monitoring-and-observability)

---

**🚀 Next Steps:**
- **New to the project?** Start with [local development](#getting-started)
- **Ready for AWS?** Follow the [infrastructure guide](infra/README.md#setup-and-deployment-instructions)
- **API development?** Check the [webapp documentation](webapp/README.md)
- **Need help?** Review [component documentation](#-component-documentation)
