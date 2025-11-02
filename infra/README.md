# AWS Infrastructure - CDK Configuration

AWS CDK infrastructure code for deploying the [FastAPI application](../webapp/) to AWS cloud. Provides production-ready ECS Fargate deployment with load balancer, container registry, and automated CI/CD pipeline.

> **Prerequisites**: Complete [local development setup](../README.md#getting-started) and review [application documentation](../webapp/README.md) before cloud deployment.

## 🏗️ AWS Infrastructure Components

> **System Overview**: See [project architecture diagram](../README.md#system-architecture) for complete system context.

#### 1. **Networking Stack** (`VpcStack`)

- **VPC**: Isolated network environment (`iac-task-{env}-vpc`)
- **Public Subnets**: Internet-facing resources, ALB deployment
- **Private Subnets**: ECS tasks with outbound internet via NAT Gateway
- **Availability Zones**: Multi-AZ deployment for high availability

#### 2. **Container Registry** (`EcrStack`)

- **ECR Repository**: Container image storage (`iac-task-{env}-ecr-repository`)
- **Image Scanning**: Automated security vulnerability scanning
- **Lifecycle Policy**: Automatic cleanup of old images

#### 3. **Application Stack** (`AppStack`)

- **ECS Fargate Service**: Serverless container hosting (`iac-task-{env}-service`)
- **Application Load Balancer**: Public endpoint with health checks
- **Auto Scaling**: Automatic scaling based on demand
- **CloudWatch Logs**: Centralized logging (`andreas-applogs-{env}`)

#### 4. **CI/CD & Security** (`GitHubOidcStack`)

- **OIDC Provider**: Secure, keyless authentication from GitHub Actions
- **IAM Role**: Unified permissions for ECR and deployment operations
- **Least Privilege**: Repository-scoped access with environment protection

## CI/CD Pipeline Overview

The project uses **GitHub Actions** for automated continuous integration and deployment with a secure, keyless authentication approach via OpenID Connect (OIDC).

### Pipeline Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Push   │────│   Build & Test   │────│   Deploy Multi  │
│   (main branch) │    │                  │    │   Environment   │
│                 │    │ • Build Docker   │    │                 │
│ • Code Changes  │    │ • Push to ECR    │    │ • Dev (Auto)    │
│ • Infrastructure│    │ • Generate Tag   │    │ • Prod (Manual) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Security Features

- **OIDC Authentication**: No long-lived AWS access keys stored in GitHub
- **Least Privilege IAM**: Single unified role with minimal required permissions
- **Environment Isolation**: Separate AWS resources per environment
- **Approval Gates**: Production requires manual approval
- **Audit Trail**: All deployments logged in GitHub Actions and CloudTrail

### Environment Variables and Secrets

| Type     | Name                         | Purpose                          | Scope      |
| -------- | ---------------------------- | -------------------------------- | ---------- |
| Secret   | `AWS_ACCOUNT_ID`             | AWS account identifier           | Repository |
| Secret   | `AWS_GITHUB_ACTION_ROLE_ARN` | IAM role for OIDC authentication | Repository |
| Variable | `AWS_REGION`                 | Deployment region                | Repository |
| Variable | `ECR_REPOSITORY`             | Container registry name          | Repository |

## 🚀 Setup and Deployment Instructions

### Prerequisites

- **AWS Account**: With administrative access
- **AWS CLI**: Configured with appropriate credentials
- **Node.js**: Version 18+ for AWS CDK CLI
- **Python**: Version 3.11+ for CDK development
- **Docker**: For local container testing (optional)

### Initial Setup

1. **Install AWS CDK CLI**

   ```bash
   npm install -g aws-cdk
   ```

2. **Bootstrap CDK** (one-time per account/region)

   ```bash
   cd infra
   cdk bootstrap
   ```

3. **Install Python Dependencies**

   ```bash
   pip install uv
   uv sync
   ```

4. **Configure Environment Variables**
   ```bash
   # Required environment variables
   export AWS_ACCOUNT_ID="123456789012"
   export AWS_REGION="eu-central-1"
   ```

### Deployment Process

#### 1. Deploy Infrastructure Stacks

```bash
# Deploy development environment
cdk deploy --all -c environment=dev --image_tag=<tag_of_image_in_ecr>

# Deploy production environment
cdk deploy --all -c environment=prod --image_tag=<tag_of_image_in_ecr>
```

#### 2. Using the Deploy Script (Recommended)

The `deploy.sh` script provides a convenient wrapper around CDK commands with enhanced functionality:

```bash
# Basic deployment to development
./deploy.sh dev deploy

# Deploy with specific image tag
./deploy.sh prod deploy --image_tag abc1234

# Show differences before deployment
./deploy.sh dev diff --image_tag 047f583

# Synthesize templates without deploying
./deploy.sh prod synth

# List all stacks
./deploy.sh dev list

# Destroy environment (with confirmation)
./deploy.sh dev destroy
```

**Script Features:**

- **Environment Validation**: Ensures only `dev` or `prod` environments
- **Prerequisites Check**: Validates CDK installation and AWS credentials
- **Dependency Management**: Automatically installs Python dependencies using `uv` or `pip`
- **Flexible Image Tags**: Supports custom image tags for specific deployments
- **Safety Checks**: Requires confirmation for destructive operations
- **Environment Variables**: Loads `.env` file if present for configuration

#### 3. Configure GitHub Secrets

After deployment, configure GitHub repository for automated deployments:

| Secret Name                  | Value                                                               | Description                 |
| ---------------------------- | ------------------------------------------------------------------- | --------------------------- |
| `AWS_ACCOUNT_ID`             | `123456789012`                                                      | Your AWS account ID         |
| `AWS_GITHUB_ACTION_ROLE_ARN` | `arn:aws:iam::123456789012:role/iac-task-{env}-github-actions-role` | From CloudFormation outputs |

> **Application Integration**: The CI/CD pipeline automatically builds and deploys the [FastAPI application](../webapp/README.md) from the `/webapp` directory.

#### 3. Configure GitHub Variables

| Variable Name         | Value                          | Description            |
| --------------------- | ------------------------------ | ---------------------- |
| `AWS_REGION`          | `eu-central-1`                 | Your deployment region |
| `ECR_DEV_REPOSITORY`  | `iac-task-dev-ecr-repository`  | ECR repository name    |
| `ECR_PROD_REPOSITORY` | `iac-task-prod-ecr-repository` | ECR repository name    |

#### 4. Set Up GitHub Environment Protection

1. Navigate to **Settings** → **Environments** in your GitHub repository
2. Create `development` environment
3. Create `production` environment
4. Enable **Required reviewers** for `production` deployments to require manual approval in CI/CD

### Deployment Verification

Use the script `check-deployment.sh` to verify the deployment.
The profile must be granted at least the following permissions:

  - cloudformation:DescribeStacks
  - ecs:ListClusters, ecs:ListServices, ecs:DescribeServices
  - ecr:ListImages, ecr:DescribeImages
  - sts:GetCallerIdentity

```bash
# cd into the infra directory
./check-deployment.sh dev --profile <aws_profile>
```

> **Script Details**: The deployment checker validates all infrastructure components and tests [application endpoints](../webapp/README.md#api-endpoints)

3. **Monitor Logs**

   ```bash
   # Get log group name from CloudFormation
   export LOG_GROUP=$(aws cloudformation describe-stacks \
     --stack-name iac-task-dev-AppStack \
     --query 'Stacks[0].Outputs[?OutputKey==`LogGroupName`].OutputValue' \
     --output text)

   # View application logs
   aws logs tail $LOG_GROUP --follow

   # Or use the log group name directly (if you know it)
   aws logs tail andreas-applogs-dev --follow
   ```

## 🧹 Cleanup Steps

### Complete Environment Cleanup

```bash
# Destroy all stacks (WARNING: This deletes everything)
cdk destroy --all -c environment=dev
cdk destroy --all -c environment=prod
```

### Selective Cleanup

```bash
# Destroy specific stacks (order matters due to dependencies)
cdk destroy iac-task-dev-AppStack -c environment=dev
cdk destroy iac-task-dev-EcrStack -c environment=dev
cdk destroy iac-task-dev-GitHubOidcStack -c environment=dev
cdk destroy iac-task-dev-VpcStack -c environment=dev
```

### Manual Cleanup Required

Some resources may require manual deletion:

1. **ECR Images**: Delete manually if repository removal fails

   ```bash
   # List images
   aws ecr list-images --repository-name iac-task-dev-ecr-repository

   # Delete all images
   aws ecr batch-delete-image \
     --repository-name iac-task-dev-ecr-repository \
     --image-ids imageTag=untagged
   ```

2. **CloudWatch Log Groups**: Retained in production by design
   ```bash
   # Delete log groups if needed
   aws logs delete-log-group --log-group-name andreas-applogs-prod
   ```

## ⚠️ Assumptions and Limitations

### Assumptions

- **Single Region Deployment**: Architecture assumes single AWS region
- **GitHub Repository**: CI/CD is designed specifically for GitHub Actions
- **Container Workload**: Application must be containerizable (see [webapp Docker configuration](../webapp/README.md#docker-image-details))
- **HTTP/HTTPS Traffic**: Load balancer configured for web traffic only
- **Shared ECR Repository**: Images are shared between environments (per repository naming)

### Current Limitations

#### Scale & Performance

- **ECS Service Limits**: Default configuration supports moderate traffic
- **Single Region**: No cross-region failover capability
- **Caching**: No Redis/ElastiCache integration

#### Security

- **Public Load Balancer**: ALB is internet-facing (private ALB requires VPN/bastion)
- **Container Security**: No runtime security scanning beyond ECR image scans
- **Secrets Management**: Basic environment variables (consider AWS Secrets Manager for sensitive data)

#### Operations

- **Backup Strategy**: No automated backup system for stateful components
- **Monitoring**: Basic CloudWatch integration (consider adding X-Ray, custom metrics)
- **SSL/TLS**: No automatic certificate management (add ACM integration for production domains)

#### Cost Optimization

- **NAT Gateway**: Always running (consider NAT instances for dev environments)
- **ECS Tasks**: Minimum task count may run even with no traffic
- **Load Balancer**: Always provisioned (consider using Function URLs for dev)

### Environment Differences

| Feature               | Development               | Production               |
| --------------------- | ------------------------- | ------------------------ |
| **ECS Tasks**         | 1 task, 0.5 vCPU, 1GB RAM | 2 tasks, 1 vCPU, 2GB RAM |
| **Log Retention**     | 1 month                   | 1 month (configurable)   |
| **Resource Removal**  | DESTROY on stack deletion | RETAIN ECR repository    |
| **GitHub Protection** | Direct deployment         | Manual approval required |
| **Application Logs**  | DEBUG level               | INFO level               |

For production workloads, review and adjust these configurations based on your specific requirements.
