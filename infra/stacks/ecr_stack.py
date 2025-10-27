from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from config import AppConfig
from constructs import Construct


class EcrStack(Stack):
    """A CloudFormation stack that creates an ECR repository and configures OIDC provider and Role for
    GitHub Actions to push images to it.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: AppConfig,
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

        # 1. Look up the existing OIDC provider for GitHub Actions.
        # This is a singleton resource, so it's better to look it up than to create it.
        github_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self,
            "GitHubOidcProvider",
            # The ARN for the GitHub OIDC provider is well-known and follows this format.
            open_id_connect_provider_arn=f"arn:aws:iam::{self.account}:oidc-provider/token.actions.githubusercontent.com",
        )

        # 2. Create a role for GitHub Actions to assume
        github_principal = iam.FederatedPrincipal(
            federated=github_provider.open_id_connect_provider_arn,
            conditions={
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": f"repo:{config.github_repo}:*"
                }
            },
            assume_role_action="sts:AssumeRoleWithWebIdentity",
        )

        github_role = iam.Role(
            self,
            "GitHubActionRole",
            assumed_by=github_principal,
            description="Role for GitHub Actions to push images to ECR",
        )

        # 3. Grant the role permissions to push/pull to the ECR repository
        self.repository.grant_pull_push(github_role)

        # 4. Output the role ARN and repository name
        CfnOutput(
            self,
            "GitHubActionRoleArn",
            value=github_role.role_arn,
            description="The ARN of the role for GitHub Actions",
        )
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
