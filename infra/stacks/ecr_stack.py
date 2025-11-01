from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_ecr as ecr
from config import InfrastructureConfig
from constructs import Construct


class EcrStack(Stack):
    """A CloudFormation stack that creates an ECR repository for container images."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: InfrastructureConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.repository = ecr.Repository(
            self,
            "Repository",
            repository_name=config.ecr.repository_name,
            image_tag_mutability=ecr.TagMutability.IMMUTABLE,
            removal_policy=RemovalPolicy.DESTROY,
            image_scan_on_push=True,
            empty_on_delete=True,
        )

        # Output repository information
        CfnOutput(
            self,
            "EcrRepositoryArn",
            value=self.repository.repository_arn,
            description="The ARN of the ECR repository",
        )
        CfnOutput(
            self,
            "EcrRepositoryName",
            value=self.repository.repository_name,
            description="The name of the ECR repository",
        )
        CfnOutput(
            self,
            "EcrRepositoryUri",
            value=self.repository.repository_uri,
            description="The URI of the ECR repository",
        )
