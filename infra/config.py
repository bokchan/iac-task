import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# --- Centralized Configuration ---


@dataclass
class Config:
    aws_region: str
    aws_account: str
    github_repo: str
    repository_name: str
    environment: str


def get_environment_config(environment: str) -> Config:
    """
    Returns a configuration dictionary for the specified environment.
    """
    # Common configuration for all environments
    shared_config = {
        "aws_region": os.getenv("AWS_REGION", "eu-central-1"),
        "aws_account": os.getenv("AWS_ACCOUNT_ID"),
        "github_repo": "bokchan/iac-task",  # Your GitHub repo: user/repo
        "repository_name": "andreas-ecr-repository",
    }

    if not shared_config["aws_account"]:
        raise ValueError("AWS_ACCOUNT_ID environment variable is not set.")

    # Environment-specific overrides
    if environment == "dev":
        env_config = {}  # No overrides for dev yet
    elif environment == "prod":
        env_config = {}  # No overrides for prod yet
    else:
        raise ValueError(f"Invalid environment specified: {environment}")

    # Merge shared and environment-specific configs
    config = {**shared_config, **env_config}
    config["environment"] = environment

    return Config(**config)
