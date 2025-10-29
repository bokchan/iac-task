#!/bin/bash

# Deployment status checker for CDK infrastructure
# Usage: ./check-deployment.sh [environment]
# Environment: dev (default), prod

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT=${1:-dev}
PROJECT_NAME="Andreas"

echo "🔍 CDK Deployment Status Checker"
echo "   Environment: $ENVIRONMENT"
echo "   Project: $PROJECT_NAME"

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

# Check and validate AWS environment variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "❌ AWS_ACCOUNT_ID environment variable is not set"
    echo "   Please export AWS_ACCOUNT_ID=<your-account-id>"
    exit 1
fi

if [ -z "$AWS_REGION" ]; then
    echo "❌ AWS_REGION environment variable is not set"
    echo "   Please export AWS_REGION=<your-region> (e.g., eu-central-1)"
    exit 1
fi

echo "   AWS Account: $AWS_ACCOUNT_ID"
echo "   AWS Region: $AWS_REGION"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured or invalid"
    exit 1
fi

echo -e "\n📊 CloudFormation Stacks Status"
STACK_PREFIX="$PROJECT_NAME-$ENVIRONMENT"

# Check all related stacks
echo "Checking stacks with prefix: $STACK_PREFIX"
STACKS=$(aws cloudformation describe-stacks --region $AWS_REGION --query "Stacks[?starts_with(StackName, '$STACK_PREFIX')].{StackName:StackName,Status:StackStatus,CreationTime:CreationTime}" --output table 2>/dev/null)

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
APP_OUTPUTS=$(aws cloudformation describe-stacks --region $AWS_REGION --stack-name "$APP_STACK_NAME" --query "Stacks[0].Outputs" --output table 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$APP_OUTPUTS"

    # Extract the Load Balancer DNS
    LB_DNS=$(aws cloudformation describe-stacks --region $AWS_REGION --stack-name "$APP_STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" --output text 2>/dev/null)

    if [ ! -z "$LB_DNS" ] && [ "$LB_DNS" != "None" ]; then
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

        # Test root endpoint
        echo -n "   Root endpoint... "
        ROOT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$LB_DNS/" 2>/dev/null || echo "000")
        if [ "$ROOT_STATUS" = "200" ]; then
            echo "✅ HTTP $ROOT_STATUS"
        else
            echo "❌ HTTP $ROOT_STATUS"
        fi
    else
        echo "❌ Could not find Load Balancer DNS in stack outputs"
    fi
else
    echo "❌ Could not retrieve AppStack outputs. Stack may not exist or be accessible."
fi

echo -e "\n📦 ECS Service Status"
CLUSTER_NAME="$STACK_PREFIX-Cluster"

# Get ECS cluster ARN
CLUSTER_ARN=$(aws ecs list-clusters --region $AWS_REGION --query "clusterArns[?contains(@, '$CLUSTER_NAME')]" --output text 2>/dev/null)

if [ ! -z "$CLUSTER_ARN" ] && [ "$CLUSTER_ARN" != "None" ]; then
    echo "✅ Found ECS Cluster: $(basename $CLUSTER_ARN)"

    # Get services in the cluster
    SERVICES=$(aws ecs list-services --region $AWS_REGION --cluster "$CLUSTER_ARN" --query "serviceArns" --output table 2>/dev/null)
    echo "Services in cluster:"
    echo "$SERVICES"

    # Get detailed service status
    SERVICE_ARN=$(aws ecs list-services --region $AWS_REGION --cluster "$CLUSTER_ARN" --query "serviceArns[0]" --output text 2>/dev/null)
    if [ ! -z "$SERVICE_ARN" ] && [ "$SERVICE_ARN" != "None" ]; then
        echo -e "\n📊 Service Details:"
        aws ecs describe-services --region $AWS_REGION --cluster "$CLUSTER_ARN" --services "$SERVICE_ARN" --query "services[0].{ServiceName:serviceName,Status:status,RunningCount:runningCount,DesiredCount:desiredCount,LaunchType:launchType}" --output table 2>/dev/null

        echo -e "\n🔄 Task Status:"
        TASK_ARNS=$(aws ecs list-tasks --region $AWS_REGION --cluster "$CLUSTER_ARN" --service-name "$SERVICE_ARN" --query "taskArns" --output text 2>/dev/null)
        if [ ! -z "$TASK_ARNS" ] && [ "$TASK_ARNS" != "None" ]; then
            aws ecs describe-tasks --region $AWS_REGION --cluster "$CLUSTER_ARN" --tasks $TASK_ARNS --query "tasks[*].{TaskArn:taskArn,LastStatus:lastStatus,HealthStatus:healthStatus,CreatedAt:createdAt}" --output table 2>/dev/null
        else
            echo "No running tasks found"
        fi
    else
        echo "No services found in cluster"
    fi
else
    echo "❌ ECS cluster not found: $CLUSTER_NAME"
fi

echo -e "\n🏗️ ECR Repository Status"
ECR_REPO_NAME="andreas-ecr-repository"

# Check ECR repository
echo "Checking repository: $ECR_REPO_NAME"
ECR_INFO=$(aws ecr describe-repositories --region $AWS_REGION --repository-names "$ECR_REPO_NAME" --query "repositories[0].{RepositoryName:repositoryName,ImageCount:imageCount,CreatedAt:createdAt}" --output table 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$ECR_INFO"

    # List recent images
    echo -e "\n📷 Recent Images:"
    aws ecr list-images --region $AWS_REGION --repository-name "$ECR_REPO_NAME" --max-items 10 --query "reverse(sort_by(imageIds[?imageTag!=null], &imageTag))" --output table 2>/dev/null || echo "No tagged images found"
else
    echo "❌ ECR repository not found or not accessible: $ECR_REPO_NAME"
fi

echo -e "\n✅ Status check complete!"
echo "   For deployment issues, check CloudFormation events in AWS Console"
echo "   For application logs, check ECS task logs or CloudWatch"
