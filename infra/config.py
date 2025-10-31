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
class AppEnvironmentConfig:
    """Configuration for FastAPI application environment variables."""

    log_level: str = "INFO"
    echo_message: str = "Hello World"

    def to_environment_dict(self) -> dict[str, str]:
        """Convert configuration to environment variable dictionary."""
        return {
            "LOG_LEVEL": self.log_level,
            "ECHO_MESSAGE": self.echo_message,
        }


@dataclass
class AppServiceConfig:
    """Configuration for the App stack (ECS service)."""

    cpu: int = 256  # 0.25 vCPU
    memory_limit_mb: int = 512  # 0.5 GB
    desired_count: int = 1
    container_port: int = 8000
    app_environment: AppEnvironmentConfig | None = None  # Will be set per environment

    def __post_init__(self):
        """Set default app environment if not provided."""
        if self.app_environment is None:
            self.app_environment = AppEnvironmentConfig()


@dataclass
class AppConfig:
    """Root configuration class for the application."""

    aws_account: str
    aws_region: str
    environment: str
    project_name: str
    github_repo: str  # Format: "owner/repo"
    cdk_bootstrap_qualifier: str  # CDK bootstrap qualifier (e.g., 'hnb659fds')
    ecr: EcrConfig
    vpc: VpcConfig
    app_service: AppServiceConfig

    def get_resource_name(self, name: str) -> str:
        """Generates a consistent resource name with a prefix."""
        return f"{self.project_name}-{self.environment}-{name}"

    def get_cdk_bootstrap_role_arn(self, role_type: str) -> str:
        """Generate CDK bootstrap role ARN dynamically.

        Args:
            role_type: Either 'deploy-role' or 'file-publishing-role'

        Returns:
            Full ARN for the CDK bootstrap role
        """
        return f"arn:aws:iam::{self.aws_account}:role/cdk-{self.cdk_bootstrap_qualifier}-{role_type}-{self.aws_account}-{self.aws_region}"


def get_environment_config(environment: str) -> AppConfig:
    """
    Loads and returns a strongly-typed configuration object for the specified environment.
    """
    aws_account_id = os.getenv("AWS_ACCOUNT_ID")
    if not aws_account_id:
        raise ValueError("AWS_ACCOUNT_ID environment variable must be set.")

    # CDK_BOOTSTRAP_QUALIFIER is required for CDK deployments.
    # Ensure this environment variable is set in your environment or .env file.
    # If using deployment scripts (e.g., deploy-secure-oidc.sh), update them to export this variable.
    cdk_bootstrap_qualifier = os.getenv("CDK_BOOTSTRAP_QUALIFIER")
    if not cdk_bootstrap_qualifier:
        raise ValueError("CDK_BOOTSTRAP_QUALIFIER environment variable must be set.")

    project_name = "Andreas"

    # Shared configuration applicable to all environments
    base_config = {
        "aws_account": aws_account_id,
        "aws_region": os.getenv("AWS_REGION", "eu-central-1"),
        "environment": environment,
        "project_name": project_name,
        "github_repo": "bokchan/iac-task",
        "cdk_bootstrap_qualifier": cdk_bootstrap_qualifier,
        "ecr": EcrConfig(
            repository_name=f"{project_name.lower()}-ecr-repository",
        ),
        "vpc": VpcConfig(),
        "app_service": AppServiceConfig(),
    }

    # Environment-specific configurations using factory pattern
    if environment == "dev":
        # Development environment: more verbose logging and debugging
        base_config["app_service"] = AppServiceConfig(
            app_environment=AppEnvironmentFactory.create_development_config()
        )
    elif environment == "prod":
        # Production environment: more robust settings and optimized config
        base_config["app_service"] = AppServiceConfig(
            desired_count=2,
            cpu=1024,  # 1 vCPU
            memory_limit_mb=2048,  # 2 GB
            app_environment=AppEnvironmentFactory.create_production_config(),
        )
        base_config["ecr"].removal_policy = "RETAIN"
    else:
        raise ValueError(f"Invalid environment specified: {environment}")

    return AppConfig(**base_config)


class AppEnvironmentFactory:
    """Factory for creating environment-specific app configurations."""

    @staticmethod
    def create_development_config(**overrides) -> AppEnvironmentConfig:
        """Create development environment configuration with optional overrides."""
        defaults = {
            "log_level": "DEBUG",
            "echo_message": "Hello from Development!",
        }
        defaults.update(overrides)
        return AppEnvironmentConfig(**defaults)

    @staticmethod
    def create_production_config(**overrides) -> AppEnvironmentConfig:
        """Create production environment configuration with optional overrides."""
        defaults = {
            "log_level": "INFO",
            "echo_message": "Hello from Production!",
        }
        defaults.update(overrides)
        return AppEnvironmentConfig(**defaults)
