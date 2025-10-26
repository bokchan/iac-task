#!/usr/bin/env python3

import aws_cdk as cdk
from config import AWSAccountConfig
from infra.ecr_stack import EcrStack

app = cdk.App()

aws_env = cdk.Environment(
    account=AWSAccountConfig.account_id, region=AWSAccountConfig.region
)

EcrStack(
    app,
    "CiCdStack",
    env=aws_env,
)

app.synth()
