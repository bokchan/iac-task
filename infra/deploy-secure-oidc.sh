#!/bin/bash

# Deploy script for updated infrastructure with separate OIDC roles
# This script will deploy the new GitHub OIDC stack with granular permissions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT=${1:-dev}

echo "🔐 Deploying Enhanced GitHub OIDC Infrastructure"
echo "   Environment: $ENVIRONMENT"
echo "   Using granular IAM roles for least privilege access"
echo

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ CDK is not installed. Please install it with: npm install -g aws-cdk"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' or set environment variables"
    exit 1
fi

echo "📋 Current AWS Identity:"
aws sts get-caller-identity

echo
echo "🔨 Synthesizing CDK app with new OIDC stack..."
cdk synth -c environment=$ENVIRONMENT --all

echo
echo "📊 Stack Dependencies:"
echo "   1. VpcStack (networking infrastructure)"
echo "   2. EcrStack (container registry)"
echo "   3. GitHubOidcStack (separate IAM roles) ⭐ NEW"
echo "   4. AppStack (ECS application)"
echo

echo "🚀 Deploying infrastructure..."
cdk deploy \
    --require-approval never \
    --all \
    -c environment=$ENVIRONMENT \
    -c image_tag=latest

echo
echo "✅ Deployment completed successfully!"
echo
echo "📋 Next Steps for GitHub Actions Integration:"
echo "   1. Go to your GitHub repository settings"
echo "   2. Navigate to Secrets and Variables → Actions"
echo "   3. Update the following repository secrets:"
echo

# Get the stack outputs
echo "   🔑 Required GitHub Secrets:"
ECR_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "Andreas-$ENVIRONMENT-GitHubOidcStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubEcrRoleArn`].OutputValue' \
    --output text 2>/dev/null || echo "Not deployed yet")

DEV_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "Andreas-$ENVIRONMENT-GitHubOidcStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubDevDeployRoleArn`].OutputValue' \
    --output text 2>/dev/null || echo "Not deployed yet")

PROD_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "Andreas-$ENVIRONMENT-GitHubOidcStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubProdDeployRoleArn`].OutputValue' \
    --output text 2>/dev/null || echo "Not deployed yet")

FEATURE_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "Andreas-$ENVIRONMENT-GitHubOidcStack" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubFeatureBranchRoleArn`].OutputValue' \
    --output text 2>/dev/null || echo "Not deployed yet")

echo "      GITHUB_ECR_ROLE_ARN = $ECR_ROLE_ARN"
echo "      GITHUB_DEV_DEPLOY_ROLE_ARN = $DEV_ROLE_ARN"
echo "      GITHUB_PROD_DEPLOY_ROLE_ARN = $PROD_ROLE_ARN"
echo "      GITHUB_FEATURE_ROLE_ARN = $FEATURE_ROLE_ARN"
echo
echo "   🔒 Security Improvements Implemented:"
echo "      ✅ Separate role for ECR operations (push/pull images)"
echo "      ✅ Separate role for dev environment deployments"
echo "      ✅ Separate role for prod environment deployments"
echo "      ✅ Read-only role for feature branch validation"
echo "      ✅ Branch-specific access controls (main branch only for deployments)"
echo "      ✅ Environment-specific conditions (dev/prod environment protection)"
echo "      ✅ Workflow-specific restrictions (deploy.yml only)"
echo "      ✅ Specific CDK bootstrap role targeting (no wildcard access)"
echo
echo "   📚 Role Permissions Summary:"
echo "      ECR Role: ECR push/pull for main branch only"
echo "      Dev Deploy Role: CDK deployment for dev environment with development environment condition"
echo "      Prod Deploy Role: CDK deployment for prod environment with production environment condition"
echo "      Feature Role: Read-only access for PR validation"
echo
echo "🔗 Workflow Integration:"
echo "   The updated workflow (deploy.yml) will use these separate roles:"
echo "   • build-and-deploy job → GITHUB_ECR_ROLE_ARN"
echo "   • deploy-dev job → GITHUB_DEV_DEPLOY_ROLE_ARN"
echo "   • deploy-prod job → GITHUB_PROD_DEPLOY_ROLE_ARN"
echo
echo "🎯 Benefits of This Approach:"
echo "   • Principle of least privilege enforced"
echo "   • Reduced blast radius in case of compromise"
echo "   • Environment isolation through IAM policies"
echo "   • Branch-based access control"
echo "   • Audit trail through role session names"
