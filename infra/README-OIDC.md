# Enhanced GitHub OIDC Implementation

This project implements **Approach 1: Separate Roles per Operation** for granular GitHub Actions OIDC permissions following AWS IAM best practices.

## 🏗️ Architecture Overview

### Core Components

1. **EcrStack** - Container registry (ECR repository)
2. **GitHubOidcStack** - OIDC provider and separate IAM roles ⭐
3. **VpcStack** - Networking infrastructure
4. **AppStack** - ECS Fargate application

### IAM Role Separation

| Role | Purpose | Branch Access | Environment | Permissions |
|------|---------|---------------|-------------|-------------|
| **GitHubEcrRole** | ECR image operations | main only | any | ECR push/pull, GetAuthorizationToken |
| **GitHubDevDeployRole** | Dev deployment | main only | development | CDK deploy + file publishing roles |
| **GitHubProdDeployRole** | Prod deployment | main only | production | CDK deploy + file publishing roles |
| **GitHubFeatureBranchRole** | PR validation | feature/*, PRs | any | Read-only CloudFormation + ECR |

## 🔒 Security Features

### ✅ Branch-Based Access Control
```python
"token.actions.githubusercontent.com:sub": f"repo:{config.github_repo}:ref:refs/heads/main"
```

### ✅ Environment-Specific Conditions
```python
"token.actions.githubusercontent.com:environment": "development"  # or "production"
```

### ✅ Workflow Restrictions
```python
"token.actions.githubusercontent.com:job_workflow_ref": f"{config.github_repo}/.github/workflows/*deploy*.yml@*"
```

### ✅ Specific CDK Role Targeting
```python
# No more wildcards - specific roles only
f"arn:aws:iam::{account}:role/cdk-hnb659fds-deploy-role-{account}-{region}"
f"arn:aws:iam::{account}:role/cdk-hnb659fds-file-publishing-role-{account}-{region}"
```

## ⚙️ Configuration

The OIDC implementation is fully configurable through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `CDK_BOOTSTRAP_QUALIFIER` | CDK bootstrap qualifier for role ARNs | **Required** |
| `AWS_REGION` | Target AWS region | `eu-central-1` |

### CDK Bootstrap Qualifier

The implementation dynamically generates CDK bootstrap role ARNs using the configured qualifier:

```python
# Dynamically generated based on CDK_BOOTSTRAP_QUALIFIER
arn:aws:iam::{account}:role/cdk-{qualifier}-deploy-role-{account}-{region}
arn:aws:iam::{account}:role/cdk-{qualifier}-file-publishing-role-{account}-{region}
```

This ensures compatibility with custom CDK bootstrap configurations and fresh AWS accounts.

## 🚀 Deployment

### 1. Deploy Infrastructure
```bash
cd infra
# CDK_BOOTSTRAP_QUALIFIER is now required
CDK_BOOTSTRAP_QUALIFIER=hnb659fds ./deploy-secure-oidc.sh dev

# Or specify custom qualifier
CDK_BOOTSTRAP_QUALIFIER=myqualifier ./deploy-secure-oidc.sh dev
```

### 2. Configure GitHub Secrets
Add these secrets to your GitHub repository:

```
GITHUB_ECR_ROLE_ARN          # For ECR operations
GITHUB_DEV_DEPLOY_ROLE_ARN   # For dev deployments
GITHUB_PROD_DEPLOY_ROLE_ARN  # For prod deployments
GITHUB_FEATURE_ROLE_ARN      # For PR validation (optional)
```

### 3. Workflow Integration
The `deploy.yml` workflow automatically uses the appropriate roles:

- **build-and-deploy** job → `GITHUB_ECR_ROLE_ARN`
- **deploy-dev** job → `GITHUB_DEV_DEPLOY_ROLE_ARN`
- **deploy-prod** job → `GITHUB_PROD_DEPLOY_ROLE_ARN`

## 📊 Security Improvements

| Security Aspect | Before | After |
|-----------------|--------|-------|
| CDK Role Access | ❌ Wildcard `cdk-*` | ✅ Specific roles only |
| Branch Restrictions | ❌ Any branch | ✅ Main branch for deployments |
| Environment Isolation | ❌ None | ✅ Environment-specific conditions |
| Operation Separation | ❌ One role for all | ✅ Four specialized roles |
| Audit Trail | ❌ Generic sessions | ✅ Named sessions per operation |
| Feature Branch Access | ❌ Full permissions | ✅ Read-only validation |

## 🎯 Benefits

- **Principle of Least Privilege**: Each role has minimal required permissions
- **Reduced Blast Radius**: Compromise limited to specific operations
- **Environment Isolation**: Dev/prod separation through IAM policies
- **Audit Trail**: Clear session names for tracking (`GitHubActions-ECR-{run_id}`)
- **Defense in Depth**: Multiple layers of access control

## 🔍 Verification

Test the implementation:

```bash
# 1. Verify synthesis
cdk synth --all -c environment=dev

# 2. Check role creation
grep -E "GitHub.*Role" cdk.out/Andreas-dev-GitHubOidcStack.template.json

# 3. Deploy and test
./deploy-secure-oidc.sh dev
```

## 📚 References

- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GitHub OIDC Claims](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [CDK IAM Documentation](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam-readme.html)

This implementation provides enterprise-grade security for GitHub Actions CI/CD while maintaining operational efficiency.
