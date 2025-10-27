#!/usr/bin/env python3

import aws_cdk as cdk
from config import get_environment_config
from stacks.ecr_stack import EcrStack

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

EcrStack(
    app,
    config.get_resource_name("EcrStack"),
    env=aws_env,
    config=config,
)

app.synth()
