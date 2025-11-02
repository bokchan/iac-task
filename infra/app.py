#!/usr/bin/env python3

import aws_cdk as cdk
from config import get_environment_config
from stacks.app_stack import AppStack
from stacks.ecr_stack import EcrStack
from stacks.github_oidc_stack import GitHubOidcStack
from stacks.vpc_stack import VpcStack

app = cdk.App()

# Determine the environment from the CDK context
environment = app.node.try_get_context("environment")
if not environment:
    raise ValueError(
        "Environment not specified. Please use '-c environment=<dev|prod>'"
    )

config = get_environment_config(environment)

aws_env = cdk.Environment(account=config.aws_account, region=config.aws_region)

# Apply tags to all resources in the app for tracking and governance
cdk.Tags.of(app).add("Creator", config.creator)
cdk.Tags.of(app).add("Project", config.project_name)
cdk.Tags.of(app).add("Environment", environment)

# Networking Stack
vpc_stack = VpcStack(
    app,
    config.get_resource_name("VpcStack"),
    env=aws_env,
    config=config,
)

# ECR Stack - Environment-specific repositories
ecr_stack = EcrStack(
    app,
    config.get_resource_name("EcrStack"),
    env=aws_env,
    config=config,
)

# GitHub OIDC Stack for IAM roles
github_oidc_stack = GitHubOidcStack(
    app,
    config.get_resource_name("GitHubOidcStack"),
    env=aws_env,
    config=config,
    ecr_repository=ecr_stack.repository,
)

# Get image tag from context (passed from CI/CD, or with the --image_tag option)
image_tag = app.node.try_get_context("image_tag")
if not image_tag:
    # Default to 'latest' for local development
    image_tag = "latest"
    print(f"Warning: No image_tag specified, using '{image_tag}'")

# Application Stack (ECS Fargate Service)
app_stack = AppStack(
    app,
    config.get_resource_name("AppStack"),
    env=aws_env,
    config=config,
    vpc_stack=vpc_stack,
    ecr_stack=ecr_stack,
    image_tag=image_tag,
)

app.synth()
