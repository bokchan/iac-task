#!/usr/bin/env python3

import aws_cdk as cdk
from config import get_environment_config
from stacks.app_stack import AppStack
from stacks.ecr_stack import EcrStack
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
cdk.Tags.of(app).add("Creator", "andreas")
cdk.Tags.of(app).add("Project", config.project_name)
cdk.Tags.of(app).add("Environment", environment)

# Networking Stack
vpc_stack = VpcStack(
    app,
    config.get_resource_name("VpcStack"),
    env=aws_env,
    config=config,
)

# ECR Stack for container images
ecr_stack = EcrStack(
    app,
    config.get_resource_name("EcrStack"),
    env=aws_env,
    config=config,
)

# Application Stack (ECS Fargate Service)
app_stack = AppStack(
    app,
    config.get_resource_name("AppStack"),
    env=aws_env,
    config=config,
    vpc_stack=vpc_stack,
    ecr_stack=ecr_stack,
)

app.synth()
