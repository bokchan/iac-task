#!/bin/bash

# Deployment status checker for CDK infrastructure
# Usage: ./check-deployment.sh [environment] [--profile profile-name]
# Environment: dev (default), prod
# Profile: AWS CLI profile from ~/.aws/config

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="dev"
AWS_PROFILE=""
PROJECT_NAME="Andreas"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        dev|prod)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            echo "❌ Unknown argument: $1"
            echo "Usage: $0 [environment] [--profile profile-name]"
            exit 1
            ;;
    esac
done

echo "🔍 CDK Deployment Status Checker"
echo "   Environment: $ENVIRONMENT"
echo "   Project: $PROJECT_NAME"

# Function to get available AWS profiles
get_aws_profiles() {
    local profiles=()
    if [ -f "$HOME/.aws/config" ]; then
        # Extract profile names from ~/.aws/config
        profiles=($(grep '^\[profile ' "$HOME/.aws/config" | sed 's/\[profile \(.*\)\]/\1/' | sort))
        # Add default profile if it exists in credentials
        if [ -f "$HOME/.aws/credentials" ] && grep -q '^\[default\]' "$HOME/.aws/credentials"; then
            profiles=("default" "${profiles[@]}")
        fi
    fi
    echo "${profiles[@]}"
}

# Function to select AWS profile interactively
select_aws_profile() {
    local available_profiles=($(get_aws_profiles))

    if [ ${#available_profiles[@]} -eq 0 ]; then
        echo "❌ No AWS profiles found in ~/.aws/config or ~/.aws/credentials"
        echo "   Please configure AWS CLI first: aws configure"
        exit 1
    fi

    echo "📋 Available AWS profiles:"
    for i in "${!available_profiles[@]}"; do
        echo "   $((i+1)). ${available_profiles[$i]}"
    done

    while true; do
        read -p "Select AWS profile (1-${#available_profiles[@]}): " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#available_profiles[@]} ]; then
            AWS_PROFILE="${available_profiles[$((choice-1))]}"
            break
        else
            echo "❌ Invalid choice. Please select a number between 1 and ${#available_profiles[@]}"
        fi
    done
}

# Set up AWS profile
if [ -z "$AWS_PROFILE" ]; then
    select_aws_profile
fi

echo "   AWS Profile: $AWS_PROFILE"

# Set AWS CLI profile option
if [ "$AWS_PROFILE" = "default" ]; then
    AWS_CLI_PROFILE=""
else
    AWS_CLI_PROFILE="--profile $AWS_PROFILE"
fi

# Validate environment
case $ENVIRONMENT in
    dev|prod)
        echo "✅ Valid environment: $ENVIRONMENT"
        ;;
    *)
        echo "❌ Invalid environment: $ENVIRONMENT"
        echo "   Valid options: dev, prod"
        exit 1
        ;;
esac

# Check AWS credentials and get account info
echo "🔐 Checking AWS credentials..."
CALLER_IDENTITY=$(aws sts get-caller-identity $AWS_CLI_PROFILE --output json 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ AWS credentials not configured or invalid for profile: $AWS_PROFILE"
    echo "   Please check your AWS configuration"
    exit 1
fi

# Extract account ID and region from AWS
AWS_ACCOUNT_ID=$(echo "$CALLER_IDENTITY" | grep -o '"Account": *"[^"]*"' | sed 's/"Account": *"\([^"]*\)"/\1/')
AWS_REGION=$(aws configure get region $AWS_CLI_PROFILE 2>/dev/null)

if [ -z "$AWS_REGION" ]; then
    AWS_REGION="eu-central-1"  # Default region
    echo "⚠️  No region configured for profile, using default: $AWS_REGION"
fi

echo "   AWS Account: $AWS_ACCOUNT_ID"
echo "   AWS Region: $AWS_REGION"

echo -e "\n📊 CloudFormation Stacks Status"
STACK_PREFIX="$PROJECT_NAME-$ENVIRONMENT"

# Check all related stacks
echo "Checking stacks with prefix: $STACK_PREFIX"
STACKS=$(aws cloudformation describe-stacks $AWS_CLI_PROFILE --region $AWS_REGION --query "Stacks[?starts_with(StackName, '$STACK_PREFIX')].{StackName:StackName,Status:StackStatus,CreationTime:CreationTime}" --output table 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$STACKS" ]; then
    echo "$STACKS"
else
    echo "❌ No stacks found with prefix: $STACK_PREFIX"
    echo "   Make sure you have deployed the infrastructure first"
    exit 1
fi

echo -e "\n🌐 Application URLs and Testing"
APP_STACK_NAME="$STACK_PREFIX-AppStack"

# Get application outputs
echo "Retrieving outputs from: $APP_STACK_NAME"
APP_OUTPUTS=$(aws cloudformation describe-stacks $AWS_CLI_PROFILE --region $AWS_REGION --stack-name "$APP_STACK_NAME" --query "Stacks[0].Outputs" --output table 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$APP_OUTPUTS"

    # Extract the Load Balancer DNS
    LB_DNS=$(aws cloudformation describe-stacks $AWS_CLI_PROFILE --region $AWS_REGION --stack-name "$APP_STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" --output text 2>/dev/null)

    if [[ -n "$LB_DNS" && "$LB_DNS" != "None" ]]; then
        echo -e "\n🔗 Application Endpoints:"
        echo "   Base URL: http://$LB_DNS"
        echo "   Health: http://$LB_DNS/health"
        echo "   Version: http://$LB_DNS/version"

        echo -e "\n🧪 Testing Endpoints:"

        # Test health endpoint
        echo -n "   Health endpoint... "
        HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$LB_DNS/health" 2>/dev/null || echo "000")
        if [ "$HEALTH_STATUS" = "200" ]; then
            echo "✅ HTTP $HEALTH_STATUS"
        else
            echo "❌ HTTP $HEALTH_STATUS"
        fi

        # Test version endpoint
        echo -n "   Version endpoint... "
        VERSION_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$LB_DNS/version" 2>/dev/null || echo "000")
        if [ "$VERSION_STATUS" = "200" ]; then
            echo "✅ HTTP $VERSION_STATUS"
            # Get version info
            VERSION_INFO=$(curl -s "http://$LB_DNS/version" 2>/dev/null || echo "Could not retrieve version")
            echo "   Version Info: $VERSION_INFO"
        else
            echo "❌ HTTP $VERSION_STATUS"
        fi
    else
        echo "❌ Could not find Load Balancer DNS in stack outputs"
    fi
else
    echo "❌ Could not retrieve AppStack outputs. Stack may not exist or be accessible."
fi

echo -e "\n📦 ECS Service Status"

# Get ECS cluster ARN - look for any cluster that starts with our stack prefix
# CDK creates clusters with additional suffixes, so we need a more flexible search
CLUSTER_ARN=$(aws ecs list-clusters $AWS_CLI_PROFILE --region $AWS_REGION --query "clusterArns[?contains(@, '$STACK_PREFIX')]" --output text 2>/dev/null)

if [ ! -z "$CLUSTER_ARN" ] && [ "$CLUSTER_ARN" != "None" ]; then
    echo "✅ Found ECS Cluster: $(basename $CLUSTER_ARN)"

    # Get services in the cluster
    SERVICES=$(aws ecs list-services $AWS_CLI_PROFILE --region $AWS_REGION --cluster "$CLUSTER_ARN" --query "serviceArns" --output table 2>/dev/null)
    echo "Services in cluster:"
    echo "$SERVICES"

    # Get detailed service status
    SERVICE_ARN=$(aws ecs list-services $AWS_CLI_PROFILE --region $AWS_REGION --cluster "$CLUSTER_ARN" --query "serviceArns[0]" --output text 2>/dev/null)
    if [ ! -z "$SERVICE_ARN" ] && [ "$SERVICE_ARN" != "None" ]; then
        echo -e "\n📊 Service Details:"
        aws ecs describe-services $AWS_CLI_PROFILE --region $AWS_REGION --cluster "$CLUSTER_ARN" --services "$SERVICE_ARN" --query "services[0].{ServiceName:serviceName,Status:status,RunningCount:runningCount,DesiredCount:desiredCount,LaunchType:launchType}" --output table --no-cli-pager 2>/dev/null

        echo -e "\n🔄 Task Status:"
        TASK_ARNS=$(aws ecs list-tasks $AWS_CLI_PROFILE --region $AWS_REGION --cluster "$CLUSTER_ARN" --service-name "$SERVICE_ARN" --query "taskArns" --output text 2>/dev/null)
        if [ ! -z "$TASK_ARNS" ] && [ "$TASK_ARNS" != "None" ]; then
            aws ecs describe-tasks $AWS_CLI_PROFILE --region $AWS_REGION --cluster "$CLUSTER_ARN" --tasks $TASK_ARNS --query "tasks[*].{TaskArn:taskArn,LastStatus:lastStatus,HealthStatus:healthStatus,CreatedAt:createdAt}" --output table --no-cli-pager 2>/dev/null
        else
            echo "No running tasks found"
        fi
    else
        echo "No services found in cluster"
    fi
else
    echo "❌ No ECS cluster found with prefix: $STACK_PREFIX"
    echo "   Expected cluster pattern: $STACK_PREFIX-AppStack-EcsDefaultCluster..."
fi

echo -e "\n🏗️ ECR Repository Status"
ECR_REPO_NAME="andreas-ecr-repository"

# Check ECR repository
echo "Checking repository: $ECR_REPO_NAME"
ECR_INFO=$(aws ecr describe-repositories $AWS_CLI_PROFILE --region $AWS_REGION --repository-names "$ECR_REPO_NAME" --query "repositories[0].{RepositoryName:repositoryName,CreatedAt:createdAt}" --output table 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$ECR_INFO"

    # Show image count
    IMAGE_COUNT=$(aws ecr list-images $AWS_CLI_PROFILE --region $AWS_REGION --repository-name "$ECR_REPO_NAME" --query "length(imageIds)" --output text 2>/dev/null)
    echo "Image count: $IMAGE_COUNT"
    # List recent images with details
    echo -e "\n📷 Recent Images:"
    aws ecr describe-images $AWS_CLI_PROFILE --region $AWS_REGION --repository-name "$ECR_REPO_NAME" --query "reverse(sort_by(imageDetails, &imagePushedAt))[0:5].{ImageTag:imageTags[0],PushedAt:to_string(imagePushedAt),Digest:imageDigest}" --output table --no-cli-pager 2>/dev/null || echo "No tagged images found"
else
    echo "❌ ECR repository not found or not accessible: $ECR_REPO_NAME"
fi

echo -e "\n✅ Status check complete!"
echo "   For deployment issues, check CloudFormation events in AWS Console"
echo "   For application logs, check ECS task logs or CloudWatch"
