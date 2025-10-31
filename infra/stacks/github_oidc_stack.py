from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_iam as iam
from config import AppConfig
from constructs import Construct


class GitHubOidcStack(Stack):
    """
    A CloudFormation stack that creates OIDC provider and separate roles for different GitHub Actions operations.
    Implements principle of least privilege with role separation.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: AppConfig,
        ecr_repository,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create the OIDC provider for GitHub Actions
        self.github_provider = iam.OpenIdConnectProvider(
            self,
            "GitHubOidcProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        # 2. Create separate roles for different operations
        self.ecr_role = self._create_ecr_role(config, ecr_repository)
        self.dev_deploy_role = self._create_dev_deploy_role(config, ecr_repository)
        self.prod_deploy_role = self._create_prod_deploy_role(config)
        self.feature_branch_role = self._create_feature_branch_role(config)

        # 3. Output role ARNs
        self._create_outputs()

    def _create_ecr_role(self, config: AppConfig, ecr_repository) -> iam.Role:
        """Create role specifically for ECR operations (image push/pull)."""
        # Simplified conditions - just require the correct repo and audience
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
            "GitHubEcrRole",
            assumed_by=principal,
            description="Role for GitHub Actions to push/pull ECR images - main branch only",
            max_session_duration=None,  # Default session duration depends on how the role is assumed: 1 hour for AWS Console, or as specified in AssumeRole API call (e.g., sts:AssumeRoleWithWebIdentity)
        )

        # ECR permissions - scoped to specific repository
        ecr_repository.grant_pull_push(role)

        # ECR token - minimal global permission needed
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
            )
        )

        return role

    def _create_dev_deploy_role(self, config: AppConfig, ecr_repository) -> iam.Role:
        """Create role specifically for dev environment deployment."""
        # Enhanced conditions for dev deployment
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
            "GitHubDevDeployRole",
            assumed_by=principal,
            description="Role for GitHub Actions to deploy to dev environment - main branch only",
            max_session_duration=None,
        )

        # ECR permissions for dev role (so it can handle both ECR and deployment)
        ecr_repository.grant_pull_push(role)
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
            )
        )

        # CDK bootstrap roles for deployment
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                resources=[
                    f"arn:aws:iam::{config.aws_account}:role/cdk-hnb659fds-deploy-role-{config.aws_account}-{config.aws_region}",
                    f"arn:aws:iam::{config.aws_account}:role/cdk-hnb659fds-file-publishing-role-{config.aws_account}-{config.aws_region}",
                ],
                conditions={"StringEquals": {"aws:RequestedRegion": config.aws_region}},
            )
        )

        return role

    def _create_prod_deploy_role(self, config: AppConfig) -> iam.Role:
        """Create role specifically for prod environment deployment."""
        # Enhanced conditions for prod deployment with stricter security
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
            "GitHubProdDeployRole",
            assumed_by=principal,
            description="Role for GitHub Actions to deploy to prod environment - main branch only",
            max_session_duration=None,
        )

        # Production deployment permissions - more restrictive
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                resources=[
                    f"arn:aws:iam::{config.aws_account}:role/cdk-hnb659fds-deploy-role-{config.aws_account}-{config.aws_region}",
                    f"arn:aws:iam::{config.aws_account}:role/cdk-hnb659fds-file-publishing-role-{config.aws_account}-{config.aws_region}",
                ],
                conditions={
                    "StringEquals": {
                        "aws:RequestedRegion": config.aws_region,
                    }
                },
            )
        )

        return role

    def _create_feature_branch_role(self, config: AppConfig) -> iam.Role:
        """Create role for feature branches with read-only permissions."""
        # Allow access from feature branches and pull requests
        principal = iam.FederatedPrincipal(
            federated=self.github_provider.open_id_connect_provider_arn,
            conditions={
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": [
                        f"repo:{config.github_repo}:ref:refs/heads/feature/*",
                        f"repo:{config.github_repo}:pull_request",
                    ]
                }
            },
            assume_role_action="sts:AssumeRoleWithWebIdentity",
        )

        role = iam.Role(
            self,
            "GitHubFeatureBranchRole",
            assumed_by=principal,
            description="Role for GitHub Actions feature branches - read-only validation",
            max_session_duration=None,
        )

        # Only read permissions for validation/testing
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sts:GetCallerIdentity",
                    "cloudformation:Describe*",
                    "cloudformation:List*",
                    "cloudformation:Get*",
                    "ecr:Describe*",
                    "ecr:List*",
                ],
                resources=["*"],
            )
        )

        return role

    def _create_outputs(self):
        """Create CloudFormation outputs for the role ARNs."""
        CfnOutput(
            self,
            "GitHubEcrRoleArn",
            value=self.ecr_role.role_arn,
            description="ARN of the GitHub Actions ECR role",
        )

        CfnOutput(
            self,
            "GitHubDevDeployRoleArn",
            value=self.dev_deploy_role.role_arn,
            description="ARN of the GitHub Actions dev deployment role",
        )

        CfnOutput(
            self,
            "GitHubProdDeployRoleArn",
            value=self.prod_deploy_role.role_arn,
            description="ARN of the GitHub Actions prod deployment role",
        )

        CfnOutput(
            self,
            "GitHubFeatureBranchRoleArn",
            value=self.feature_branch_role.role_arn,
            description="ARN of the GitHub Actions feature branch role",
        )

        CfnOutput(
            self,
            "GitHubOidcProviderArn",
            value=self.github_provider.open_id_connect_provider_arn,
            description="ARN of the GitHub OIDC Provider",
        )
