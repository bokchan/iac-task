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
class ApplicationSettings:
    """Configuration for FastAPI application runtime settings."""

    log_level: str = "INFO"
    echo_message: str = "Hello World"

    def to_environment_dict(self) -> dict[str, str]:
        """Convert configuration to environment variable dictionary."""
        return {
            "LOG_LEVEL": self.log_level,
            "ECHO_MESSAGE": self.echo_message,
        }


@dataclass
class EcsServiceConfig:
    """Configuration for the ECS Fargate service deployment."""

    cpu: int = 512  # 0.5 vCPU
    memory_limit_mb: int = 1024  # 1 GB
    desired_count: int = 1
    container_port: int = 8000
    log_group_prefix: str = "andreas-applogs"  # CloudWatch log group prefix
    application_settings: ApplicationSettings | None = (
        None  # Will be set per environment
    )

    def __post_init__(self):
        """Set default application settings if not provided."""
        if self.application_settings is None:
            self.application_settings = ApplicationSettings()


@dataclass
class InfrastructureConfig:
    """Root configuration for all AWS infrastructure components."""

    aws_account: str
    aws_region: str
    environment: str
    project_name: str
    github_repo: str  # Format: "owner/repo"
    creator: str
    ecr: EcrConfig
    vpc: VpcConfig
    ecs_service: EcsServiceConfig

    def get_resource_name(self, name: str) -> str:
        """Generates a consistent resource name with project, environment, and resource type."""
        return f"{self.project_name.lower()}-{self.environment}-{name}"

    def get_log_group_name(self) -> str:
        """Generates the CloudWatch log group name with required prefix."""
        return f"{self.ecs_service.log_group_prefix}-{self.environment}"


def get_environment_config(environment: str) -> InfrastructureConfig:
    """
    Loads and returns a strongly-typed configuration object for the specified environment.
    """
    aws_account_id = os.getenv("AWS_ACCOUNT_ID")
    if not aws_account_id:
        raise ValueError("AWS_ACCOUNT_ID environment variable must be set.")

    project_name = "iac-task"

    # Shared configuration applicable to all environments
    infra_config = InfrastructureConfig(
        aws_account=aws_account_id,
        aws_region=os.getenv("AWS_REGION", "eu-central-1"),
        environment=environment,
        project_name=project_name,
        github_repo="bokchan/iac-task",
        creator="andreas",
        ecr=EcrConfig(
            repository_name=f"{project_name.lower()}-ecr-repository",
        ),
        vpc=VpcConfig(),
        ecs_service=EcsServiceConfig(),
    )

    # Update ECR repository name using the config method
    infra_config.ecr.repository_name = infra_config.get_resource_name("ecr-repository")

    # Environment-specific configurations using factory pattern
    if environment == "dev":
        # Development environment: more verbose logging and debugging
        infra_config.ecs_service = EcsServiceConfig(
            application_settings=ApplicationSettingsFactory.create_development_config()
        )
    elif environment == "prod":
        # Production environment: more robust settings and optimized config
        infra_config.ecs_service = EcsServiceConfig(
            desired_count=2,
            cpu=1024,  # 1 vCPU
            memory_limit_mb=2048,  # 2 GB
            application_settings=ApplicationSettingsFactory.create_production_config(),
        )
        infra_config.ecr.removal_policy = "RETAIN"
    else:
        raise ValueError(f"Invalid environment specified: {environment}")

    return infra_config


class ApplicationSettingsFactory:
    """Factory for creating environment-specific application settings."""

    @staticmethod
    def create_development_config(**overrides) -> ApplicationSettings:
        """Create development application settings with optional overrides."""
        defaults = {
            "log_level": "DEBUG",
            "echo_message": "Hello from Development!",
        }
        defaults.update(overrides)
        return ApplicationSettings(**defaults)

    @staticmethod
    def create_production_config(**overrides) -> ApplicationSettings:
        """Create production application settings with optional overrides."""
        defaults = {
            "log_level": "INFO",
            "echo_message": "Hello from Production!",
        }
        defaults.update(overrides)
        return ApplicationSettings(**defaults)
