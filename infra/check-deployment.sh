#!/bin/bash

# Deployment status checker for CDK infrastructure
# Checks CloudFormation stacks, application health, ECS services, and ECR images
#
# Required AWS Permissions:
#   - cloudformation:DescribeStacks
#   - ecs:ListClusters, ecs:ListServices, ecs:DescribeServices
#   - ecr:ListImages, ecr:DescribeImages
#   - sts:GetCallerIdentity
#
# Usage: ./check-deployment.sh [dev|prod] [--profile profile-name]
# Examples:
#   ./check-deployment.sh                    # Check dev environment with default profile
#   ./check-deployment.sh prod               # Check prod environment
#   ./check-deployment.sh dev --profile work # Check dev with specific AWS profile

set -e

# Configuration
PROJECT_NAME="iac-task"
ENVIRONMENT="dev"
AWS_PROFILE=""
TIMEOUT=10  # Timeout for HTTP requests

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile) AWS_PROFILE="$2"; shift 2 ;;
        dev|prod) ENVIRONMENT="$1"; shift ;;
        --help|-h) echo "Usage: $0 [dev|prod] [--profile profile-name]"; exit 0 ;;
        *) echo "❌ Unknown argument: $1"; exit 1 ;;
    esac
done

echo "🔍 CDK Status Check: $PROJECT_NAME-$ENVIRONMENT"

# Use default profile if none specified
[ -z "$AWS_PROFILE" ] && AWS_PROFILE="default"

# Setup AWS CLI and validate access
setup_aws() {
    # Set AWS CLI arguments
    AWS_CLI_ARGS=""
    [ "$AWS_PROFILE" != "default" ] && AWS_CLI_ARGS="--profile $AWS_PROFILE"

    # Validate credentials and get basic info
    if ! caller_identity=$(aws sts get-caller-identity $AWS_CLI_ARGS --output json 2>/dev/null); then
        echo "❌ AWS credentials invalid for profile: $AWS_PROFILE"
        echo "💡 Try: aws sso login --profile $AWS_PROFILE"
        exit 1
    fi

    AWS_REGION=$(aws configure get region $AWS_CLI_ARGS 2>/dev/null || echo "eu-central-1")
    aws_account=$(echo "$caller_identity" | grep -o '"Account": *"[^"]*"' | cut -d'"' -f4)
    echo "🔐 AWS Account: $aws_account | Region: $AWS_REGION | Profile: $AWS_PROFILE"
}

setup_aws

# Check CloudFormation stacks
echo -e "\n📊 CloudFormation Stacks"
STACK_PREFIX="$PROJECT_NAME-$ENVIRONMENT"
if ! aws cloudformation describe-stacks $AWS_CLI_ARGS --region $AWS_REGION \
  --query "Stacks[?starts_with(StackName, '$STACK_PREFIX')].{StackName:StackName,Status:StackStatus}" \
  --output table --no-cli-pager 2>/dev/null; then
    echo "❌ No stacks found: $STACK_PREFIX"
    echo "💡 Deploy first: cdk deploy --all -c environment=$ENVIRONMENT"
    exit 1
fi

# Test application health
echo -e "\n🌐 Application Health Check"
if lb_dns=$(aws cloudformation describe-stacks $AWS_CLI_ARGS --region $AWS_REGION \
  --stack-name "$STACK_PREFIX-AppStack" --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text 2>/dev/null) && [[ "$lb_dns" != "None" ]]; then

    echo "🔗 URL: http://$lb_dns"
    APP_TEST_RESULT=0

    # Test key endpoints
    for endpoint in "health" "version" ""; do
        status=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "http://$lb_dns/$endpoint" 2>/dev/null || echo "000")
        if [ "$status" = "200" ]; then
            echo "✅ /$endpoint"
        else
            echo "❌ /$endpoint (HTTP $status)"
            APP_TEST_RESULT=1
        fi
    done
else
    echo "❌ Load Balancer not found - AppStack may not be deployed"
    APP_TEST_RESULT=2
fi

# Check ECS service
echo -e "\n📦 ECS Service"
if cluster_arn=$(aws ecs list-clusters $AWS_CLI_ARGS --region $AWS_REGION \
  --query "clusterArns[?contains(@, '$STACK_PREFIX')] | [0]" --output text 2>/dev/null) && [[ "$cluster_arn" != "None" ]]; then
    echo "Cluster: $(basename "$cluster_arn")"
    service_arn=$(aws ecs list-services $AWS_CLI_ARGS --region $AWS_REGION --cluster "$cluster_arn" --query "serviceArns[0]" --output text 2>/dev/null)
    [ "$service_arn" != "None" ] && aws ecs describe-services $AWS_CLI_ARGS --region $AWS_REGION --cluster "$cluster_arn" \
      --services "$service_arn" --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" \
      --output table --no-cli-pager 2>/dev/null
else
    echo "❌ No ECS cluster found: $STACK_PREFIX"
fi

# Check ECR repository
echo -e "\n🏗️ Container Images (ECR)"
ecr_repo="$PROJECT_NAME-$ENVIRONMENT-ecr-repository"
echo "📦 Repository: $ecr_repo"

if image_count=$(aws ecr list-images $AWS_CLI_ARGS --region $AWS_REGION --repository-name "$ecr_repo" \
  --query "length(imageIds)" --output text 2>/dev/null); then
    echo "📊 Images: $image_count"
    [ "$image_count" -gt 0 ] && aws ecr describe-images $AWS_CLI_ARGS --region $AWS_REGION --repository-name "$ecr_repo" \
      --query "reverse(sort_by(imageDetails, &imagePushedAt))[0:3].{Tag:imageTags[0]||'<untagged>',Pushed:imagePushedAt}" \
      --output table --no-cli-pager 2>/dev/null
else
    echo "❌ Repository not found or no access: $ecr_repo"
fi

# Final summary and exit with appropriate code
echo -e "\n📋 Summary"
if [ $APP_TEST_RESULT -eq 0 ]; then
    echo "✅ All application health checks passed"
    echo "🎉 Deployment verification complete - everything looks good!"
    exit 0
elif [ $APP_TEST_RESULT -eq 2 ]; then
    echo "⚠️  Application not accessible (AppStack may not be deployed)"
    echo "💡 Run: cdk deploy --all -c environment=$ENVIRONMENT"
    exit 2
else
    echo "❌ Some application health checks failed"
    echo "💡 Check application logs: aws logs tail andreas-applogs-$ENVIRONMENT --follow"
    exit 2
fi
