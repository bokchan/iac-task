# 🎯 Interview Preparation Guide

## IaC Task Implementation - Technical Deep Dive

**Interview Date**: Monday, November 10, 2025, 13:30
**Duration**: 45 minutes (20min presentation + 25min Q&A)

---

## 📋 **Complete Technical Overview**

### **Project Summary**

- **Objective**: Multi-environment Infrastructure as Code solution with FastAPI application
- **Technology Stack**: FastAPI, Docker, AWS CDK (Python), GitHub Actions, ECS Fargate
- **Environments**: Development (auto-deploy) → Production (manual approval)
- **Key Achievement**: 100% infrastructure automated with zero-downtime deployments

### **Assignment Requirements Checklist** ✅

| **Requirement**               | **Implementation**                                      | **Status**  |
| ----------------------------- | ------------------------------------------------------- | ----------- |
| **Containerized FastAPI App** | 3 endpoints: `/`, `/health`, `/version` + env variables | ✅ Complete |
| **AWS ECR Repository**        | Environment-specific repositories with image scanning   | ✅ Complete |
| **ECS Fargate + ALB**         | Auto-scaling service with load balancer                 | ✅ Complete |
| **IAM Least Privilege**       | OIDC-based roles, environment-scoped permissions        | ✅ Complete |
| **CloudWatch Logs**           | Centralized logging with `andreas-applogs-{env}`        | ✅ Complete |
| **Multi-Environment**         | Dev (1 task, 0.5 vCPU) vs Prod (2 tasks, 1 vCPU)        | ✅ Complete |
| **Environment Variables**     | DEBUG/INFO log levels, different messages per env       | ✅ Complete |
| **Automated Dev Deploy**      | Triggers on main branch push                            | ✅ Complete |
| **Manual Prod Approval**      | GitHub environment protection + manual gates            | ✅ Complete |
| **Docker Layer Caching**      | GitHub Actions cache (50-80% faster builds)             | ✅ Complete |
| **GitHub Secrets**            | OIDC authentication, no long-lived keys                 | ✅ Complete |

**Bonus Features Implemented**:

- ✅ Comprehensive documentation and READMEs
- ✅ Reusable GitHub Actions for DRY principles
- ✅ Environment verification scripts (`check-deployment.sh`)
- ✅ Modular CDK stack architecture
- ✅ Docker multi-stage builds for security
- ✅ Trunk-based development workflow

---

## 🏗️ **Deep Technical Knowledge**

### **1. Application Architecture**

**FastAPI Application** (`webapp/main.py`):

```python
# Key technical details to know:
- 3 endpoints: GET /, /health, /version
- Environment variables: ECHO_MESSAGE, LOG_LEVEL, IMAGE_TAG
- Structured logging with configurable levels
- OpenAPI documentation auto-generated at /docs
```

**Docker Multi-Stage Build**:

- **Builder Stage**: `uv:python3.14-bookworm-slim` + build dependencies
- **Runtime Stage**: `python:3.14-slim-bookworm` + non-root user (uid 999)
- **Security**: Minimal runtime, layer caching, non-root execution
- **Performance**: UV package manager for faster dependency resolution

### **2. AWS Infrastructure (CDK Python)**

**Stack Architecture**:

1. **VpcStack**: Multi-AZ VPC with public/private subnets, NAT Gateway
2. **EcrStack**: Environment-specific repositories with vulnerability scanning
3. **GitHubOidcStack**: OIDC provider + IAM roles for keyless authentication
4. **AppStack**: ECS Fargate + ALB with health checks and auto-scaling

**Key CDK Technical Decisions**:

```python
# Configuration-driven approach (config.py):
- Environment factory pattern for dev/prod settings
- Programmatic config vs cdk.context.json
- Static type-check support configuration with dataclasses

# Security implementation:
- OIDC trust policy: repo:bokchan/iac-task:*
- Least privilege: ECR push/pull + CDK bootstrap roles only
- Environment isolation: separate resources per environment
```

**Environment Differences**:
| **Aspect** | **Development** | **Production** |
|---|---|---|
| **ECS Tasks** | 1 task, 512 CPU, 1024MB | 2 tasks, 1024 CPU, 2048MB |
| **Log Level** | DEBUG | INFO |
| **Message** | "Hello from Development!" | "Hello from Production!" |
| **ECR Policy** | DESTROY | RETAIN |
| **Deployment** | Auto on push | Manual approval |

### **3. CI/CD Pipeline (GitHub Actions)**

**Workflow Architecture**:

```yaml
# main.yml workflow:
1. QA Checks (matrix: infra, webapp) - runs ruff + pyrefly
2. Build & Push (dev ECR) - Docker with layer caching
3. Deploy Dev (auto) - CDK deployment with image tag
4. Deploy Prod (manual approval) - requires GitHub environment protection
```

**Reusable Actions** (DRY principle):

- `setup-environment`: OIDC authentication setup
- `build-push-image`: Docker build with GitHub Actions cache
- `deploy-cdk`: CDK deployment with Python dependencies
- `run-qa`: Code quality checks (ruff, pyrefly)

**Security Features**:

- OIDC authentication (no stored AWS keys)
- Repository-scoped trust policy
- Environment-specific IAM roles
- Manual approval gates for production

### **4. Configuration Management**

**Environment-Specific Settings**:

```python
# config.py factory pattern:
def get_environment_config(environment: str) -> InfrastructureConfig:
    if environment == "dev":
        # Development settings
    elif environment == "prod":
        # Production settings with 2x resources
```

**Resource Naming Convention**:

- Format: `{project}-{environment}-{resource}`
- Example: `iac-task-dev-service`, `iac-task-prod-ecr-repository`
- Tags: Creator=andreas, Project=iac-task, Environment={env}

---

## 🎤 **20-Minute Presentation Structure**

### **Slide 1-2: Introduction & Assignment Overview** (3 min)

**Content**:

- "Today I'll present my IaC solution: a production-ready FastAPI application with automated multi-environment deployment on AWS"
- Assignment requirements overview and approach

**Key Points**:

- Chose AWS CDK (Python) for infrastructure familiarity
- GitHub Actions for CI/CD automation
- Focus on production readiness and security

### **Slide 3-4: System Architecture** (4 min)

**Visual**: Architecture diagram showing:

```
GitHub → GitHub Actions → AWS (ECR + ECS + ALB)
```

**Key Points**:

- Multi-environment isolation (dev/prod)
- OIDC-based security (no long-lived credentials)
- Containerized FastAPI with health monitoring
- Auto-scaling ECS Fargate behind ALB

### **Slide 5-6: FastAPI Application** (3 min)

**Demo**: Live demonstration

- Show running application: `http://localhost:8000`
- API endpoints: `/`, `/health`, `/version`, `/docs`
- Environment variable configuration

**Technical Highlights**:

- Multi-stage Docker build for security
- Structured logging and monitoring
- OpenAPI documentation

### **Slide 7-8: Infrastructure as Code** (4 min)

**Code Walkthrough**:

```python
# Show config.py environment factory pattern
# Show VpcStack, EcrStack, AppStack structure
# Highlight security (OIDC, least privilege)
```

**Key Points**:

- Modular CDK stack design
- Environment-specific configurations
- Type-safe configuration management

### **Slide 9-10: CI/CD Pipeline** (3 min)

**Workflow Demonstration**:

- Show GitHub Actions workflow file
- Explain QA → Build → Deploy Dev → Deploy Prod flow
- Highlight reusable actions and DRY principles

**Security Focus**:

- OIDC authentication
- Manual approval for production
- Docker layer caching optimization

### **Slide 11-12: Production Readiness** (2 min)

**Achievements**:

- ✅ Zero-downtime deployments
- ✅ Automated testing and quality checks
- ✅ Comprehensive documentation
- ✅ Security best practices
- ✅ Monitoring and logging

### **Slide 13: Questions & Discussion** (1 min)

- "I'm ready for your technical questions!"
- Prepared to discuss any architectural decisions

---

## 🎯 **Expected Q&A Topics & Answers**

### **Technical Architecture Questions**

**Q: Why did you choose CDK over Terraform?**
**A**: "I chose AWS CDK with Python for several reasons:

1. **Familiarity**: Strong Python background enabled faster development
2. **Type Safety**: CDK provides compile-time validation vs Terraform's runtime errors
3. **Integration**: Native AWS service support and automatic IAM policy generation
4. **Programmatic Config**: The `config.py` factory pattern wouldn't be as clean in HCL"

**Q: Explain your environment isolation strategy.**
**A**: "Complete environment isolation through:

1. **Separate AWS Resources**: Each environment has its own VPC, ECR, ECS cluster
2. **IAM Boundaries**: Environment-specific roles prevent cross-environment access
3. **Configuration Separation**: Factory pattern in `config.py` ensures different settings
4. **GitHub Environments**: Separate approval workflows and variable scoping"

**Q: How do you handle secrets management?**
**A**: "Multi-layered approach:

1. **No Long-lived Keys**: OIDC eliminates stored AWS credentials
2. **GitHub Secrets**: Encrypted storage for sensitive configuration
3. **Environment Variables**: Runtime configuration injection via ECS
4. **Future Enhancement**: Could integrate AWS Secrets Manager for application secrets"

### **CI/CD & DevOps Questions**

**Q: Walk me through a production deployment.**
**A**: "Production deployment process:

1. **Developer pushes to main** → triggers GitHub Actions
2. **QA checks run** → ruff linting + pyrefly analysis (parallel for infra & webapp)
3. **Image build** → Docker with layer caching, tagged with git SHA
4. **Dev deployment** → automatic with new image
5. **Production gate** → manual approval required (GitHub environment protection)
6. **Production deployment** → CDK applies infrastructure changes + new container image
7. **Verification** → `check-deployment.sh` validates all services healthy"

**Q: How do you ensure zero-downtime deployments?**
**A**: "ECS rolling deployments:

1. **ALB Health Checks**: Only routes to healthy containers
2. **Gradual Replacement**: New tasks start before old tasks terminate
3. **Health Check Grace Period**: Allows containers to fully initialize
4. **Circuit Breaker**: ECS stops deployment if health checks fail"

**Q: Explain your Docker optimization strategy.**
**A**: "Multi-stage approach:

1. **Builder Stage**: Heavy dependencies (build-essential, UV cache)
2. **Runtime Stage**: Minimal python:slim-bookworm
3. **Layer Caching**: GitHub Actions cache reduces build time by 50-80%
4. **Security**: Non-root user (uid 999), minimal attack surface"

### **Security Questions**

**Q: How do you implement least privilege?**
**A**: "Granular IAM approach:

1. **OIDC Trust Policy**: Limited to specific GitHub repository
2. **ECR Permissions**: Only push/pull to environment-specific repositories
3. **CDK Bootstrap**: Uses existing CDK deployment roles, no additional privileges
4. **Environment Scoping**: Roles can't access other environments' resources"

**Q: What about container security?**
**A**: "Defense in depth:

1. **Base Images**: Official python:slim images with security updates
2. **Non-root Execution**: Custom user with uid 999
3. **Minimal Runtime**: Multi-stage build removes build dependencies
4. **Vulnerability Scanning**: ECR scans images on push
5. **Network Isolation**: Private subnets with NAT Gateway egress"

### **Scalability & Performance Questions**

**Q: How would you scale this solution?**
**A**: "Multiple scaling dimensions:

1. **Horizontal**: ECS auto-scaling based on CPU/memory metrics
2. **Infrastructure**: ALB can handle multiple AZ distribution
3. **Multi-region**: CDK stacks can deploy to multiple regions
4. **Microservices**: Current structure supports multiple services
5. **Caching**: Could add ElastiCache for application-level caching"

**Q: What monitoring would you add?**
**A**: "Comprehensive observability:

1. **Application**: Custom CloudWatch metrics via FastAPI middleware
2. **Infrastructure**: ECS service metrics, ALB request metrics
3. **Alerting**: CloudWatch alarms for service health, error rates
4. **Distributed Tracing**: OpenTelemetry for request correlation
5. **Dashboards**: CloudWatch or Grafana for operational visibility"

### **Code Quality & Testing Questions**

**Q: How do you ensure code quality?**
**A**: "Automated quality gates:

1. **Static Analysis**: Ruff for linting, pyrefly for code analysis
2. **Unit Testing**: pytest for application logic (webapp/tests/)
3. **Integration Testing**: Could add CDK unit tests for infrastructure
4. **Pipeline Gates**: QA checks must pass before any deployment
5. **Documentation**: Comprehensive READMEs and inline documentation"

**Q: What would you add for better testing?**
**A**: "Enhanced testing strategy:

1. **Infrastructure Tests**: CDK unit tests with aws-cdk-lib/assertions
2. **Integration Tests**: End-to-end API testing post-deployment
3. **Load Testing**: Performance validation before production
4. **Security Testing**: Container vulnerability scanning, SAST/DAST
5. **Chaos Engineering**: Resilience testing with deliberate failures"
6. **CI/CD for release tags**: Support deployment of versioning
7. **Pydantic models for configuration**: Type-safety

---

## 🚀 **Key Strengths to Highlight**

1. **Production Readiness**: Security, monitoring, documentation
2. **Automation**: Complete CI/CD with quality gates
3. **Maintainability**: Modular design, reusable components
4. **Scalability**: Auto-scaling, multi-environment ready
5. **Security**: OIDC, least privilege, container hardening
6. **Developer Experience**: Clear documentation, easy local development

---

## 📚 **Quick Reference - Key Numbers**

- **Build Time Improvement**: 50-80% faster with Docker layer caching
- **Infrastructure Stacks**: 4 modular CDK stacks
- **Environments**: 2 (dev auto, prod manual)
- **Security**: 0 long-lived AWS credentials stored
- **Documentation**: 3 comprehensive READMEs + inline docs
- **Container Security**: Non-root user (uid 999)
- **Multi-AZ**: 2 availability zones for high availability
- **Resource Scaling**: Dev (0.5 vCPU) → Prod (1 vCPU), 2x memory

---

## 🎤 **Final Presentation Tips**

1. **Start Strong**: "I built a production-ready, secure, automated infrastructure solution"
2. **Show, Don't Just Tell**: Live demo of application and deployment verification
3. **Technical Depth**: Be ready to go deeper on any component
4. **Business Value**: Emphasize zero-downtime, security, cost optimization
5. **Continuous Learning**: Mention areas for future improvement
6. **Confidence**: You've built something impressive - own it!

**Good luck with your interview!** 🚀
