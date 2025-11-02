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
# Usage: ./check-deployment.sh [environment] [--profile profile-name]
# Examples:
#   ./check-deployment.sh                    # Check dev environment, prompt for AWS profile
#   ./check-deployment.sh prod               # Check prod environment
#   ./check-deployment.sh dev --profile work # Check dev with specific AWS profile
#
# Exit codes:
#   0 - All checks passed
#   1 - Configuration error or critical failure
#   2 - Application health check failed (non-critical)

set -e

# Configuration
PROJECT_NAME="iac-task"
ENVIRONMENT="dev"
AWS_PROFILE=""
TIMEOUT=10  # Timeout for HTTP requests

# Parse command line arguments
parse_arguments() {
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
            --help|-h)
                echo "Usage: $0 [environment] [--profile profile-name]"
                echo "  environment: dev (default) or prod"
                echo "  --profile: AWS profile name (will prompt if not provided)"
                exit 0
                ;;
            *)
                echo "❌ Unknown argument: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

parse_arguments "$@"

echo "🔍 CDK Status Check: $PROJECT_NAME-$ENVIRONMENT"

# AWS profile selection - prompt user if not specified
select_aws_profile() {
    if [ -n "$AWS_PROFILE" ]; then
        return 0  # Profile already specified via command line
    fi

    # Get available profiles from AWS config
    local profiles=()

    # Add default profile if it exists in credentials
    if [ -f "$HOME/.aws/credentials" ] && grep -q '^\[default\]' "$HOME/.aws/credentials" 2>/dev/null; then
        profiles+=("default")
    fi

    # Add named profiles from config
    if [ -f "$HOME/.aws/config" ]; then
        while IFS= read -r profile; do
            profiles+=("$profile")
        done < <(grep '^\[profile ' "$HOME/.aws/config" 2>/dev/null | sed 's/\[profile \(.*\)\]/\1/' | sort)
    fi

    if [ ${#profiles[@]} -eq 0 ]; then
        echo "❌ No AWS profiles found. Run: aws configure"
        exit 1
    fi

    echo "Available AWS profiles:"
    select profile in "${profiles[@]}"; do
        if [ -n "$profile" ]; then
            AWS_PROFILE="$profile"
            break
        fi
        echo "Invalid selection. Please try again."
    done
}

select_aws_profile

# Check AWS permissions for required services
check_aws_permissions() {
    echo "🔐 Checking AWS permissions..."
    local permission_errors=()

    # Test CloudFormation permissions
    if ! aws cloudformation list-stacks $AWS_CLI_ARGS --region $AWS_REGION --max-items 1 >/dev/null 2>&1; then
        permission_errors+=("CloudFormation: list-stacks, describe-stacks")
    fi

    # Test ECS permissions
    if ! aws ecs list-clusters $AWS_CLI_ARGS --region $AWS_REGION --max-items 1 >/dev/null 2>&1; then
        permission_errors+=("ECS: list-clusters, list-services, describe-services")
    fi

    # Test ECR permissions
    if ! aws ecr describe-repositories $AWS_CLI_ARGS --region $AWS_REGION --max-items 1 >/dev/null 2>&1; then
        permission_errors+=("ECR: describe-repositories, list-images, describe-images")
    fi

    # Report permission issues
    if [ ${#permission_errors[@]} -gt 0 ]; then
        echo "❌ Missing required AWS permissions:"
        for error in "${permission_errors[@]}"; do
            echo "   • $error"
        done
        echo ""
        echo "💡 Required IAM permissions:"
        echo "   • cloudformation:DescribeStacks, cloudformation:ListStacks"
        echo "   • ecs:ListClusters, ecs:ListServices, ecs:DescribeServices"
        echo "   • ecr:DescribeRepositories, ecr:ListImages, ecr:DescribeImages"
        echo "   • sts:GetCallerIdentity"
        echo ""
        echo "💡 Contact your AWS administrator to grant these permissions"
        exit 1
    fi

    echo "✅ All required AWS permissions verified"
}

# Setup AWS CLI with profile and validate credentials
setup_aws_cli() {
    # Set AWS CLI arguments based on profile
    AWS_CLI_ARGS=""
    if [ "$AWS_PROFILE" != "default" ]; then
        AWS_CLI_ARGS="--profile $AWS_PROFILE"
    fi

    # Validate AWS credentials
    echo "🔐 Validating AWS credentials for profile: $AWS_PROFILE"
    local caller_identity
    if ! caller_identity=$(aws sts get-caller-identity $AWS_CLI_ARGS --output json 2>/dev/null); then
        echo "❌ AWS credentials invalid for profile: $AWS_PROFILE"
        echo "💡 Try: aws sso login --profile $AWS_PROFILE (if using SSO)"
        echo "💡 Or: aws configure --profile $AWS_PROFILE"
        exit 1
    fi

    # Get AWS region (fallback to eu-central-1)
    AWS_REGION=$(aws configure get region $AWS_CLI_ARGS 2>/dev/null || echo "eu-central-1")

    # Extract and display AWS account info
    local aws_account
    aws_account=$(echo "$caller_identity" | grep -o '"Account": *"[^"]*"' | cut -d'"' -f4)
    echo "✅ AWS Account: $aws_account | Region: $AWS_REGION"

    # Check required permissions
    check_aws_permissions
}

setup_aws_cli

# Check stacks
echo -e "\n📊 CloudFormation Stacks"
STACK_PREFIX="$PROJECT_NAME-$ENVIRONMENT"
if ! aws cloudformation describe-stacks $AWS_CLI_ARGS --region $AWS_REGION \
  --query "Stacks[?starts_with(StackName, '$STACK_PREFIX')].{StackName:StackName,Status:StackStatus}" \
  --output table --no-cli-pager 2>/dev/null; then

    # Check if it's a permission error vs no stacks found
    local error_output
    error_output=$(aws cloudformation describe-stacks $AWS_CLI_ARGS --region $AWS_REGION 2>&1 || true)

    if echo "$error_output" | grep -q "AccessDenied\|UnauthorizedOperation\|Forbidden"; then
        echo "❌ Permission denied accessing CloudFormation"
        echo "💡 Required permissions: cloudformation:DescribeStacks, cloudformation:ListStacks"
        exit 1
    else
        echo "❌ No stacks found with prefix: $STACK_PREFIX"
        echo "💡 Deploy infrastructure first: cdk deploy --all -c environment=$ENVIRONMENT"
        exit 1
    fi
fi

# Test application endpoints via load balancer
test_application() {
    echo -e "\n🌐 Application Health Check"

    # Get load balancer DNS from CloudFormation outputs
    local lb_dns
    lb_dns=$(aws cloudformation describe-stacks $AWS_CLI_ARGS --region $AWS_REGION \
        --stack-name "$STACK_PREFIX-AppStack" \
        --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
        --output text 2>/dev/null)

    if [[ -z "$lb_dns" || "$lb_dns" == "None" ]]; then
        echo "❌ Load Balancer DNS not found - AppStack may not be deployed"
        return 2
    fi

    echo "🔗 URL: http://$lb_dns"

    # Test critical application endpoints
    local endpoints=("health:Health Check" "version:Version Info" ":Root Endpoint")
    local failed=0

    for endpoint_info in "${endpoints[@]}"; do
        IFS=':' read -r endpoint description <<< "$endpoint_info"
        local url="http://$lb_dns/${endpoint}"

        # Perform HTTP request with timeout
        local status
        status=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "000")

        if [ "$status" = "200" ]; then
            echo "✅ /$endpoint - $description"
        else
            echo "❌ /$endpoint - $description (HTTP $status)"
            failed=$((failed + 1))
        fi
    done

    # Return non-zero if any endpoint failed (but don't exit script)
    return $failed
}

test_application
APP_TEST_RESULT=$?

# ECS status
echo -e "\n📦 ECS Service"
cluster_result=$(aws ecs list-clusters $AWS_CLI_ARGS --region $AWS_REGION \
  --query "clusterArns[?contains(@, '$STACK_PREFIX')]" --output text 2>&1)

# Check for permission errors
if echo "$cluster_result" | grep -q "AccessDenied\|UnauthorizedOperation\|Forbidden"; then
    echo "❌ Permission denied accessing ECS"
    echo "💡 Required permissions: ecs:ListClusters, ecs:ListServices, ecs:DescribeServices"
else
    CLUSTER_ARN="$cluster_result"
    if [[ -n "$CLUSTER_ARN" && "$CLUSTER_ARN" != "None" ]]; then
        echo "Cluster: $(basename "$CLUSTER_ARN")"
        aws ecs describe-services $AWS_CLI_ARGS --region $AWS_REGION --cluster "$CLUSTER_ARN" \
          --services $(aws ecs list-services $AWS_CLI_ARGS --region $AWS_REGION --cluster "$CLUSTER_ARN" --query "serviceArns[0]" --output text) \
          --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" --output table --no-cli-pager 2>/dev/null
    else
        echo "❌ No ECS cluster found with prefix: $STACK_PREFIX"
    fi
fi

# Check ECR repository and recent images
check_ecr_repository() {
    echo -e "\n🏗️ Container Images (ECR)"

    # ECR repository name should match the environment-specific naming
    local ecr_repo="$PROJECT_NAME-$ENVIRONMENT-ecr-repository"
    echo "📦 Repository: $ecr_repo"

    # Get image count with permission error handling
    local image_result
    image_result=$(aws ecr list-images $AWS_CLI_ARGS --region $AWS_REGION \
        --repository-name "$ecr_repo" \
        --query "length(imageIds)" --output text 2>&1)

    # Check for permission errors
    if echo "$image_result" | grep -q "AccessDenied\|UnauthorizedOperation\|Forbidden"; then
        echo "❌ Permission denied accessing ECR"
        echo "💡 Required permissions: ecr:ListImages, ecr:DescribeImages"
        return 1
    elif echo "$image_result" | grep -q "RepositoryNotFoundException"; then
        echo "❌ ECR repository not found: $ecr_repo"
        echo "💡 Deploy ECR stack first: cdk deploy $PROJECT_NAME-$ENVIRONMENT-EcrStack"
        return 1
    fi

    local image_count="$image_result"
    echo "📊 Total Images: $image_count"

    if [ "$image_count" -gt 0 ]; then
        echo "🕒 Recent Images (last 3):"
        # Show recent images with better formatting
        aws ecr describe-images $AWS_CLI_ARGS --region $AWS_REGION \
            --repository-name "$ecr_repo" \
            --query "reverse(sort_by(imageDetails, &imagePushedAt))[0:3].{Tag:imageTags[0]||'<untagged>',Pushed:imagePushedAt,Size:to_string(imageSizeInBytes)}" \
            --output table --no-cli-pager 2>/dev/null || echo "   ⚠️  Could not retrieve image details"
    else
        echo "⚠️  No images found - may need to run CI/CD pipeline"
    fi
}

check_ecr_repository

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
