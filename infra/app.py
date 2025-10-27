#!/usr/bin/env python3

import aws_cdk as cdk
from config import AWSAccountConfig
from infra.ecr_stack import EcrStack

app = cdk.App()

# Apply tags to all resources in the app for tracking and governance
cdk.Tags.of(app).add("Creator", "andreas")
cdk.Tags.of(app).add("Project", "iac-task")

aws_env = cdk.Environment(
    account=AWSAccountConfig().account_id, region=AWSAccountConfig().region
)

EcrStack(
    app,
    "AndreasEcrStack",
    env=aws_env,
    repository_name="andreas-ecr-repository",
    github_repo="repo:bokchan/iac-task:*",
)

app.synth()
