# GitHub OIDC Security Implementation

This document outlines the implementation of granular GitHub Actions OIDC permissions following the principle of least privilege.

## Security Issues Addressed

### 1. **Overly Broad CDK Access** ❌ → ✅
**Before:**
```python
resources=[f"arn:aws:iam::{config.aws_account}:role/cdk-*"]
```
- Wildcard access to ALL CDK bootstrap roles
- No restriction on operations

**After:**
```python
resources=[
    f"arn:aws:iam::{config.aws_account}:role/cdk-hnb659fds-deploy-role-{config.aws_account}-{config.aws_region}",
    f"arn:aws:iam::{config.aws_account}:role/cdk-hnb659fds-file-publishing-role-{config.aws_account}-{config.aws_region}",
]
```
- Specific CDK role targeting only
- Limited to deployment and file publishing roles

### 2. **Insufficient Branch Restrictions** ❌ → ✅
**Before:**
```python
"token.actions.githubusercontent.com:sub": f"repo:{config.github_repo}:*"
```
- Any branch, PR, or workflow could assume roles

**After:**
```python
"token.actions.githubusercontent.com:sub": f"repo:{config.github_repo}:ref:refs/heads/main"
```
- Only main branch can assume deployment roles
- Feature branches get read-only access

### 3. **Single Role for Multiple Operations** ❌ → ✅
**Before:**
- One role for ECR push, dev deploy, and prod deploy

**After:**
- **ECR Role**: Only ECR push/pull operations
- **Dev Deploy Role**: Only dev environment deployment
- **Prod Deploy Role**: Only prod environment deployment
- **Feature Branch Role**: Read-only validation access

## Role Architecture

### ECR Role (`GitHubEcrRole`)
```yaml
Purpose: Container image operations only
Branch Access: main branch only
Workflow Restriction: *deploy*.yml files only
Permissions:
  - ecr:BatchCheckLayerAvailability
  - ecr:BatchGetImage
  - ecr:CompleteLayerUpload
  - ecr:GetDownloadUrlForLayer
  - ecr:InitiateLayerUpload
  - ecr:PutImage
  - ecr:UploadLayerPart
  - ecr:GetAuthorizationToken (global)
```

### Dev Deploy Role (`GitHubDevDeployRole`)
```yaml
Purpose: Development environment deployment
Branch Access: main branch only
Environment Condition: development environment required
Workflow Restriction: *deploy*.yml files only
Permissions:
  - sts:AssumeRole on specific CDK deploy roles
  - Regional restriction to configured AWS region
```

### Prod Deploy Role (`GitHubProdDeployRole`)
```yaml
Purpose: Production environment deployment
Branch Access: main branch only
Environment Condition: production environment required
Workflow Restriction: deploy.yml@refs/heads/main only (stricter)
Permissions:
  - sts:AssumeRole on specific CDK deploy roles
  - Regional restriction to configured AWS region
```

### Feature Branch Role (`GitHubFeatureBranchRole`)
```yaml
Purpose: PR validation and testing
Branch Access: feature/* branches and pull requests
Workflow Restriction: Any workflow
Permissions: Read-only
  - sts:GetCallerIdentity
  - cloudformation:Describe*, List*, Get*
  - ecr:Describe*, List*
```

## Enhanced Security Conditions

### Environment-Based Access Control
```python
conditions={
    "StringEquals": {
        "token.actions.githubusercontent.com:environment": "production"
    }
}
```
Ensures roles can only be used from their intended GitHub environment.

### Workflow-Specific Restrictions
```python
"StringLike": {
    "token.actions.githubusercontent.com:job_workflow_ref": f"{config.github_repo}/.github/workflows/*deploy*.yml@*"
}
```
Restricts role usage to specific workflow files.

### Session Naming for Audit Trail
```yaml
role-session-name: GitHubActions-ECR-${{ github.run_id }}
```
Provides clear audit trail for role assumptions.

## Implementation Steps

### 1. Deploy Updated Infrastructure
```bash
cd infra
./deploy-secure-oidc.sh dev
```

### 2. Update GitHub Secrets
After deployment, add these secrets to your GitHub repository:

```
GITHUB_ECR_ROLE_ARN = arn:aws:iam::ACCOUNT:role/Andreas-dev-GitHubOidcStack-GitHubEcrRole...
GITHUB_DEV_DEPLOY_ROLE_ARN = arn:aws:iam::ACCOUNT:role/Andreas-dev-GitHubOidcStack-GitHubDevDeployRole...
GITHUB_PROD_DEPLOY_ROLE_ARN = arn:aws:iam::ACCOUNT:role/Andreas-dev-GitHubOidcStack-GitHubProdDeployRole...
GITHUB_FEATURE_ROLE_ARN = arn:aws:iam::ACCOUNT:role/Andreas-dev-GitHubOidcStack-GitHubFeatureBranchRole...
```

### 3. Verify Workflow Integration
The updated `deploy.yml` workflow uses these roles:
- `build-and-deploy` job → `GITHUB_ECR_ROLE_ARN`
- `deploy-dev` job → `GITHUB_DEV_DEPLOY_ROLE_ARN`
- `deploy-prod` job → `GITHUB_PROD_DEPLOY_ROLE_ARN`

## Security Benefits

### ✅ Principle of Least Privilege
Each role has only the minimum permissions needed for its specific function.

### ✅ Reduced Blast Radius
Compromise of one role doesn't grant access to other operations or environments.

### ✅ Environment Isolation
Dev and prod environments are isolated through IAM policy conditions.

### ✅ Branch-Based Access Control
Only authorized branches can perform deployments.

### ✅ Audit Trail
Clear role session names provide audit trail for all operations.

### ✅ Workflow Restrictions
Roles can only be assumed from specific workflow files.

## Comparison: Before vs After

| Aspect | Before (Single Role) | After (Separate Roles) |
|--------|---------------------|------------------------|
| ECR Access | ✅ Push/Pull | ✅ Push/Pull (ECR Role only) |
| Dev Deploy | ✅ Full CDK access | ✅ Limited CDK access (Dev Role only) |
| Prod Deploy | ✅ Full CDK access | ✅ Limited CDK access (Prod Role only) |
| Branch Restrictions | ❌ Any branch | ✅ Main branch only for deployments |
| Environment Conditions | ❌ None | ✅ Environment-specific access |
| Workflow Restrictions | ❌ Any workflow | ✅ Deploy workflows only |
| CDK Role Access | ❌ Wildcard (`cdk-*`) | ✅ Specific roles only |
| Feature Branch Access | ❌ Full permissions | ✅ Read-only validation |
| Audit Trail | ❌ Generic session names | ✅ Specific session names |

## Testing the Implementation

### 1. Test ECR Access
```bash
# Should work from main branch deploy workflow
docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```

### 2. Test Environment Isolation
```bash
# Dev role should only work with development environment
# Prod role should only work with production environment
```

### 3. Test Feature Branch Restrictions
```bash
# Feature branches should only have read-only access
cdk synth --all  # Should work
cdk deploy       # Should fail
```

This implementation significantly improves security by following AWS IAM best practices and implementing defense-in-depth through multiple layers of access control.
