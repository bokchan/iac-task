from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from config import InfrastructureConfig
from constructs import Construct


class GitHubOidcStack(Stack):
    """
    A CloudFormation stack that creates OIDC provider and a unified role for GitHub Actions operations.
    Uses single role with comprehensive permissions, relying on GitHub environment approval for production security.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: InfrastructureConfig,
        ecr_repository: ecr.Repository,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create or reference the OIDC provider for GitHub Actions
        # Note: Only create if this is the first environment (dev), otherwise reference existing
        # Requires that the dev environment is deployed first
        if config.environment == "dev":
            self.github_provider = iam.OpenIdConnectProvider(
                self,
                "GitHubOidcProvider",
                url="https://token.actions.githubusercontent.com",
                client_ids=["sts.amazonaws.com"],
            )
        else:
            # Reference existing OIDC provider from dev environment
            self.github_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(  # type: ignore[bad-argument-type]
                self,
                "GitHubOidcProvider",
                open_id_connect_provider_arn=f"arn:aws:iam::{self.account}:oidc-provider/token.actions.githubusercontent.com",
            )

        # 2. Create unified role for all GitHub Actions operations
        self.github_role = self._create_github_role(config, ecr_repository)

        # 3. Output role ARN
        self._create_outputs()

    def _create_github_role(
        self, config: InfrastructureConfig, ecr_repository: ecr.Repository
    ) -> iam.Role:
        """Create unified role for all GitHub Actions operations (ECR + deployment)."""
        # OIDC conditions - restrict to specific repository
        principal = iam.FederatedPrincipal(
            federated=self.github_provider.open_id_connect_provider_arn,
            conditions={
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": f"repo:{config.github_repo}:*",
                },
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                },
            },
            assume_role_action="sts:AssumeRoleWithWebIdentity",
        )

        role = iam.Role(
            self,
            "GitHubRole",
            assumed_by=principal,  # pyrefly: ignore[bad-argument-type]
            description="Unified role for GitHub Actions - ECR operations and deployments to all environments",
            max_session_duration=None,
        )

        # ECR permissions - scoped to specific repository
        ecr_repository.grant_pull_push(role)

        # ECR authorization token - required for ECR login
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
            )
        )

        # CDK bootstrap roles for deployment - retrieved dynamically
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                resources=[
                    self.format_arn(
                        service="iam",
                        resource="role",
                        resource_name=f"cdk-{self.synthesizer.bootstrap_qualifier}-deploy-role-{self.account}-{self.region}",
                        region="",
                    ),
                    self.format_arn(
                        service="iam",
                        resource="role",
                        resource_name=f"cdk-{self.synthesizer.bootstrap_qualifier}-file-publishing-role-{self.account}-{self.region}",
                        region="",
                    ),
                ],
                conditions={"StringEquals": {"aws:RequestedRegion": config.aws_region}},
            )
        )

        return role

    def _create_outputs(self):
        """Create CloudFormation outputs for the role ARN."""
        CfnOutput(
            self,
            "GitHubRoleArn",
            value=self.github_role.role_arn,
            description="ARN of the unified GitHub Actions role for ECR and deployments",
        )

        CfnOutput(
            self,
            "GitHubOidcProviderArn",
            value=self.github_provider.open_id_connect_provider_arn,
            description="ARN of the GitHub OIDC Provider",
        )
