import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()


@dataclass
class EcrConfig:
    """Configuration for the ECR stack."""

    repository_name: str


@dataclass
class AppConfig:
    """Root configuration class for the application."""

    aws_account: str
    aws_region: str
    environment: str
    project_name: str
    github_repo: str  # Format: "owner/repo"
    ecr: EcrConfig

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
    }

    # You can introduce environment-specific overrides here if needed
    if environment == "dev":
        pass  # No overrides for dev yet
    elif environment == "prod":
        # Example of an override for prod
        # base_config["ecr"].repository_name = "andreas-prod-repository"
        pass
    else:
        raise ValueError(f"Invalid environment specified: {environment}")

    return AppConfig(**base_config)
