#!/bin/bash

# Comprehensive deployment script for different environments
# Usage: ./deploy.sh [environment] [action] [--image_tag <tag>] [additional-args]
# Actions: synth, deploy, destroy, diff
# Examples:
#   ./deploy.sh dev deploy
#   ./deploy.sh prod synth --image_tag abc1234
#   ./deploy.sh dev diff --image_tag 047f583

set -e

IMAGE_TAG=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments for --image_tag
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --image_tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Reset positional parameters
set -- "${ARGS[@]}"

# Now get environment and action from remaining arguments
ENVIRONMENT=${1:-dev}
ACTION=${2:-deploy}

echo "🚀 CDK Infrastructure Management"
echo "   Environment: $ENVIRONMENT"
echo "   Action: $ACTION"
echo "   Image Tag: ${IMAGE_TAG:-'not specified (will use default)'}"
echo "   Directory: $SCRIPT_DIR"

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

# Load environment variables if .env file exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "📋 Loading environment variables from .env"
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Set the environment for the deployment
export ENVIRONMENT=$ENVIRONMENT

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ CDK is not installed. Please install it with: npm install -g aws-cdk"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please configure your AWS credentials."
    exit 1
fi

if command -v uv &> /dev/null; then
    echo "📦 Installing Python dependencies with uv..."
    if [ ! -f ./.venv/bin/activate ]; then
        echo "❌ Virtual environment not found. Please create it with: python3 -m venv .venv"
        exit 1
    fi

    source ./.venv/bin/activate
    uv sync --frozen --active || uv pip install -r requirements.txt
elif command -v pip &> /dev/null; then
    echo "📦 Installing Python dependencies with pip (uv not found)..."
    pip install -r requirements.txt
else
    echo "❌ Neither 'uv' nor 'pip' is installed. Please install one of them to proceed."
    exit 1

# Build CDK context arguments
CDK_CONTEXT="-c environment=$ENVIRONMENT"
if [[ -n "$IMAGE_TAG" ]]; then
    CDK_CONTEXT="$CDK_CONTEXT -c image_tag=$IMAGE_TAG"
    echo "📦 Using image tag: $IMAGE_TAG"
fi

# Perform the requested action
case $ACTION in
    synth)
        echo "🔨 Synthesizing CDK app..."
        cdk synth $CDK_CONTEXT "${@:3}"
        ;;
    deploy)
        echo "🔨 Synthesizing CDK app..."
        cdk synth $CDK_CONTEXT

        echo "🚀 Deploying stacks..."
        cdk deploy $CDK_CONTEXT --require-approval never "${@:3}"

        echo "✅ Deployment complete!"
        echo "📋 Retrieving stack outputs..."
        cdk list $CDK_CONTEXT
        ;;
    destroy)
        echo "💥 Destroying stacks..."
        echo "⚠️  This will delete all resources in environment: $ENVIRONMENT"
        if [ ! -z "$IMAGE_TAG" ]; then
            echo "   Image tag: $IMAGE_TAG"
        fi
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cdk destroy $CDK_CONTEXT --force "${@:3}"
            echo "✅ Destruction complete!"
        else
            echo "❌ Destruction cancelled"
        fi
        ;;
    diff)
        echo "📊 Showing differences..."
        cdk diff $CDK_CONTEXT "${@:3}"
        ;;
    list)
        echo "📋 Listing stacks..."
        cdk list $CDK_CONTEXT "${@:3}"
        ;;
    *)
        echo "❌ Invalid action: $ACTION"
        echo "   Valid actions: synth, deploy, destroy, diff, list"
        exit 1
        ;;
esac
