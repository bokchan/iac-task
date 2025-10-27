import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()


@dataclass
class EcrConfig:
    """Configuration for the ECR stack."""

    repository_name: str
    removal_policy: str = "DESTROY"  # Options: DESTROY, RETAIN


@dataclass
class VpcConfig:
    """Configuration for the VPC stack."""

    max_azs: int = 2


@dataclass
class AppServiceConfig:
    """Configuration for the App stack (ECS service)."""

    cpu: int = 256  # 0.25 vCPU
    memory_limit_mb: int = 512  # 0.5 GB
    desired_count: int = 1
    container_port: int = 8000


@dataclass
class AppConfig:
    """Root configuration class for the application."""

    aws_account: str
    aws_region: str
    environment: str
    project_name: str
    github_repo: str  # Format: "owner/repo"
    ecr: EcrConfig
    vpc: VpcConfig
    app_service: AppServiceConfig

    def get_resource_name(self, name: str) -> str:
        """Generates a consistent resource name with a prefix."""
        return f"{self.project_name}-{self.environment}-{name}"


def get_environment_config(environment: str) -> AppConfig:
    """
    Loads and returns a strongly-typed configuration object for the specified environment.
    """
    aws_account_id = os.getenv("AWS_ACCOUNT_ID")
    if not aws_account_id:
        raise ValueError("AWS_ACCOUNT_ID environment variable must be set.")

    project_name = "Andreas"

    # Shared configuration applicable to all environments
    base_config = {
        "aws_account": aws_account_id,
        "aws_region": os.getenv("AWS_REGION", "eu-central-1"),
        "environment": environment,
        "project_name": project_name,
        "github_repo": "bokchan/iac-task",
        "ecr": EcrConfig(
            repository_name=f"{project_name.lower()}-ecr-repository",
        ),
        "vpc": VpcConfig(),
        "app_service": AppServiceConfig(),
    }

    # You can introduce environment-specific overrides here if needed
    if environment == "dev":
        pass  # No overrides for dev yet
    elif environment == "prod":
        # Example of overrides for prod: more robust settings
        base_config["app_service"].desired_count = 2
        base_config["app_service"].cpu = 1024  # 1 vCPU
        base_config["app_service"].memory_limit_mb = 2048  # 2 GB
        base_config["ecr"].removal_policy = "RETAIN"
    else:
        raise ValueError(f"Invalid environment specified: {environment}")

    return AppConfig(**base_config)
