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

    # Maximum number of availability zones to use
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

    cpu: int = 512  # 0.5 vCPU
    memory_limit_mb: int = 1024  # 1 GB
    desired_count: int = 1
    container_port: int = 8000
    log_group_prefix: str = "andreas-applogs"  # CloudWatch log group prefix
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
    ecr: EcrConfig
    vpc: VpcConfig
    app_service: AppServiceConfig

    def get_resource_name(self, name: str) -> str:
        """Generates a consistent resource name with a prefix."""
        return f"{self.project_name}-{self.environment}-{name}"

    def get_log_group_name(self) -> str:
        """Generates the CloudWatch log group name with required prefix."""
        return f"{self.app_service.log_group_prefix}-{self.environment}"


def get_environment_config(environment: str) -> AppConfig:
    """
    Loads and returns a strongly-typed configuration object for the specified environment.
    """
    aws_account_id = os.getenv("AWS_ACCOUNT_ID")
    if not aws_account_id:
        raise ValueError("AWS_ACCOUNT_ID environment variable must be set.")

    project_name = "Andreas"

    # Shared configuration applicable to all environments
    app_config = AppConfig(
        aws_account=aws_account_id,
        aws_region=os.getenv("AWS_REGION", "eu-central-1"),
        environment=environment,
        project_name=project_name,
        github_repo="bokchan/iac-task",
        ecr=EcrConfig(
            repository_name=f"{project_name.lower()}-ecr-repository",
        ),
        vpc=VpcConfig(),
        app_service=AppServiceConfig(),
    )

    # Environment-specific configurations using factory pattern
    if environment == "dev":
        # Development environment: more verbose logging and debugging
        app_config.app_service = AppServiceConfig(
            app_environment=AppEnvironmentFactory.create_development_config()
        )
    elif environment == "prod":
        # Production environment: more robust settings and optimized config
        app_config.app_service = AppServiceConfig(
            desired_count=2,
            cpu=1024,  # 1 vCPU
            memory_limit_mb=2048,  # 2 GB
            app_environment=AppEnvironmentFactory.create_production_config(),
        )
        app_config.ecr.removal_policy = "RETAIN"
    else:
        raise ValueError(f"Invalid environment specified: {environment}")

    return app_config


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
