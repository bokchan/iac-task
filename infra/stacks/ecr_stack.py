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

        # 1. Create the OIDC provider for GitHub Actions
        github_provider = iam.OpenIdConnectProvider(
            self,
            "GitHubOidcProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
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

        # 4. Add permissions to assume CDK bootstrap roles
        github_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                resources=[f"arn:aws:iam::{config.aws_account}:role/cdk-*"],
            )
        )

        # 5. Output the role ARN and repository name
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
            "GitHubOidcProviderArn",
            value=github_provider.open_id_connect_provider_arn,
            description="The ARN of the GitHub OIDC Provider",
        )
        CfnOutput(
            self,
            "EcrRepositoryUri",
            value=self.repository.repository_uri,
            description="The URI of the ECR repository",
        )
