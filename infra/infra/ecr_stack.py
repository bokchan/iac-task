from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from constructs import Construct


class EcrStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repository = ecr.Repository(
            self,
            "AndreasEcrRepository",
            repository_name="andreas-ecr-repository",
            image_tag_mutability=ecr.TagMutability.MUTABLE,
            removal_policy=RemovalPolicy.RETAIN,
            image_scan_on_push=True,
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
                    "token.actions.githubusercontent.com:sub": "repo:bokchan/iac-task:*"
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
        repository.grant_pull_push(github_role)
