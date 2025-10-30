#!/bin/bash

# Deployment status checker for CDK infrastructure
# Usage: ./check-deployment.sh [environment] [--profile profile-name]

set -e

PROJECT_NAME="Andreas"
ENVIRONMENT="dev"
AWS_PROFILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile) AWS_PROFILE="$2"; shift 2 ;;
        dev|prod) ENVIRONMENT="$1"; shift ;;
        *) echo "❌ Unknown argument: $1"; exit 1 ;;
    esac
done

echo "🔍 CDK Status Check: $PROJECT_NAME-$ENVIRONMENT"

# AWS profile selection (simplified)
if [ -z "$AWS_PROFILE" ]; then
    profiles=($(grep '^\[profile ' "$HOME/.aws/config" 2>/dev/null | sed 's/\[profile \(.*\)\]/\1/' | sort))
    [ -f "$HOME/.aws/credentials" ] && grep -q '^\[default\]' "$HOME/.aws/credentials" && profiles=("default" "${profiles[@]}")

    if [ ${#profiles[@]} -eq 0 ]; then
        echo "❌ No AWS profiles found. Run: aws configure"
        exit 1
    fi

    echo "Select AWS profile:"
    select profile in "${profiles[@]}"; do
        [ -n "$profile" ] && AWS_PROFILE="$profile" && break
    done
fi

# Setup AWS CLI
AWS_CLI_ARGS=""
[ "$AWS_PROFILE" != "default" ] && AWS_CLI_ARGS="--profile $AWS_PROFILE"

# Get AWS info
CALLER_IDENTITY=$(aws sts get-caller-identity $AWS_CLI_ARGS --output json 2>/dev/null) || {
    echo "❌ AWS credentials invalid for profile: $AWS_PROFILE"
    exit 1
}

AWS_REGION=$(aws configure get region $AWS_CLI_ARGS 2>/dev/null || echo "eu-central-1")
echo "AWS: $(echo "$CALLER_IDENTITY" | grep -o '"Account": *"[^"]*"' | cut -d'"' -f4) | $AWS_REGION"

# Check stacks
echo -e "\n📊 CloudFormation Stacks"
STACK_PREFIX="$PROJECT_NAME-$ENVIRONMENT"
aws cloudformation describe-stacks $AWS_CLI_ARGS --region $AWS_REGION \
  --query "Stacks[?starts_with(StackName, '$STACK_PREFIX')].{StackName:StackName,Status:StackStatus}" \
  --output table --no-cli-pager 2>/dev/null || { echo "❌ No stacks found: $STACK_PREFIX"; exit 1; }

# Test application endpoints
echo -e "\n🌐 Application Testing"
LB_DNS=$(aws cloudformation describe-stacks $AWS_CLI_ARGS --region $AWS_REGION \
  --stack-name "$STACK_PREFIX-AppStack" \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" --output text 2>/dev/null)

if [[ -n "$LB_DNS" && "$LB_DNS" != "None" ]]; then
    echo "URL: http://$LB_DNS"
    for endpoint in "health" "version" ""; do
        url="http://$LB_DNS/${endpoint}"
        status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
        [ "$status" = "200" ] && echo "✅ /$endpoint" || echo "❌ /$endpoint ($status)"
    done
else
    echo "❌ No Load Balancer DNS found"
fi

# ECS status
echo -e "\n📦 ECS Service"
CLUSTER_ARN=$(aws ecs list-clusters $AWS_CLI_ARGS --region $AWS_REGION \
  --query "clusterArns[?contains(@, '$STACK_PREFIX')]" --output text 2>/dev/null)

if [[ -n "$CLUSTER_ARN" && "$CLUSTER_ARN" != "None" ]]; then
    echo "Cluster: $(basename "$CLUSTER_ARN")"
    aws ecs describe-services $AWS_CLI_ARGS --region $AWS_REGION --cluster "$CLUSTER_ARN" \
      --services $(aws ecs list-services $AWS_CLI_ARGS --region $AWS_REGION --cluster "$CLUSTER_ARN" --query "serviceArns[0]" --output text) \
      --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" --output table --no-cli-pager 2>/dev/null
else
    echo "❌ No ECS cluster found"
fi

# ECR images
echo -e "\n🏗️ ECR Repository"
ECR_REPO="andreas-ecr-repository"
IMAGE_COUNT=$(aws ecr list-images $AWS_CLI_ARGS --region $AWS_REGION --repository-name "$ECR_REPO" --query "length(imageIds)" --output text 2>/dev/null || echo "0")
echo "Images: $IMAGE_COUNT"

if [ "$IMAGE_COUNT" -gt 0 ]; then
    aws ecr describe-images $AWS_CLI_ARGS --region $AWS_REGION --repository-name "$ECR_REPO" \
      --query "reverse(sort_by(imageDetails, &imagePushedAt))[0:3].{Tag:imageTags[0],Pushed:to_string(imagePushedAt)}" \
      --output table --no-cli-pager 2>/dev/null || echo "No tagged images"
fi

echo -e "\n✅ Status check complete"
