variable "subscription_id" {
  description = "Azure subscription ID used for deployment."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", trimspace(var.subscription_id)))
    error_message = "subscription_id must be a non-empty UUID in Azure subscription format. Provide it via TF_VAR_subscription_id or a secure var source."
  }
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "westeurope"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be one of: dev, prod."
  }
}

variable "project_name" {
  description = "Project name used in resource naming."
  type        = string
  default     = "iac-task"
}

variable "acr_name_override" {
  description = "Optional explicit ACR name. If null, Terraform derives a deterministic name from project, environment, and subscription."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.acr_name_override == null || can(regex("^[a-z0-9]{5,50}$", var.acr_name_override))
    error_message = "acr_name_override must match Azure ACR naming constraints: lowercase alphanumeric, 5-50 chars."
  }
}

variable "acr_sku" {
  description = "Container Registry SKU."
  type        = string
  default     = "Standard"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "acr_sku must be one of: Basic, Standard, Premium."
  }
}

variable "container_repository" {
  description = "Repository name inside ACR."
  type        = string
  default     = "webapp"
}

variable "container_image_tag" {
  description = "Docker image tag to deploy."
  type        = string
  default     = "latest"
}

variable "deploy_container_app" {
  description = "Whether to deploy the Azure Container App. Use false for initial clean-slate bootstrap before pushing image to ACR."
  type        = bool
  default     = false
}

variable "enable_destroy_protection" {
  description = "Enable production guardrail checks that block destructive bootstrap patterns by default."
  type        = bool
  default     = true
}

variable "allow_prod_bootstrap" {
  description = "Allow deploy_container_app=false when environment=prod. Keep false unless explicitly running a controlled bootstrap."
  type        = bool
  default     = false
}

variable "container_port" {
  description = "Container port exposed by the webapp."
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "CPU cores allocated to the container."
  type        = number
  default     = 0.5
}

variable "container_memory" {
  description = "Memory allocated to the container."
  type        = string
  default     = "1Gi"
}

variable "min_replicas" {
  description = "Minimum number of running container replicas."
  type        = number
  default     = 1

  validation {
    condition     = var.min_replicas >= 0
    error_message = "min_replicas must be greater than or equal to 0."
  }
}

variable "max_replicas" {
  description = "Maximum number of container replicas."
  type        = number
  default     = 2

  validation {
    condition     = var.max_replicas >= 1
    error_message = "max_replicas must be greater than or equal to 1."
  }
}

variable "echo_message" {
  description = "Value for ECHO_MESSAGE environment variable."
  type        = string
  default     = "Hello from Azure MVP"
}

variable "log_level" {
  description = "Value for LOG_LEVEL environment variable."
  type        = string
  default     = "INFO"
}

variable "create_github_oidc_identity" {
  description = "Create Entra App Registration and Service Principal for GitHub OIDC. Set false to reuse an existing identity."
  type        = bool
  default     = true
}

variable "existing_github_oidc_client_id" {
  description = "Existing Entra application client_id to reuse when create_github_oidc_identity is false."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = var.existing_github_oidc_client_id == null || can(regex(
      "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
      trimspace(var.existing_github_oidc_client_id)
    ))
    error_message = "existing_github_oidc_client_id must be null or a valid UUID."
  }

  validation {
    condition     = var.create_github_oidc_identity || var.existing_github_oidc_client_id != null
    error_message = "existing_github_oidc_client_id is required when create_github_oidc_identity is false."
  }
}

variable "existing_github_oidc_application_object_id" {
  description = "Existing Entra application object_id (required if reusing identity and creating federated credential)."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = var.existing_github_oidc_application_object_id == null || can(regex(
      "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
      trimspace(var.existing_github_oidc_application_object_id)
    ))
    error_message = "existing_github_oidc_application_object_id must be null or a valid UUID."
  }

  validation {
    condition     = !(var.create_github_federated_credential && !var.create_github_oidc_identity && var.existing_github_oidc_application_object_id == null)
    error_message = "existing_github_oidc_application_object_id is required when create_github_federated_credential is true and create_github_oidc_identity is false."
  }
}

variable "github_oidc_application_name" {
  description = "Display name for the GitHub OIDC Entra application."
  type        = string
  default     = null
  nullable    = true
}

variable "create_github_federated_credential" {
  description = "Create a federated credential on the Entra application for GitHub OIDC."
  type        = bool
  default     = true
}

variable "github_repository_owner" {
  description = "GitHub repository owner for OIDC subject matching."
  type        = string
  default     = "bokchan"
}

variable "github_repository_name" {
  description = "GitHub repository name for OIDC subject matching."
  type        = string
  default     = "iac-task"
}

variable "github_oidc_subject" {
  description = "Optional explicit GitHub OIDC subject claim. If null, Terraform derives one from branch or environment inputs."
  type        = string
  default     = null
  nullable    = true
}

variable "github_oidc_branch" {
  description = "Git branch used to derive OIDC subject when github_oidc_environment_name is null."
  type        = string
  default     = "main"
}

variable "github_oidc_environment_name" {
  description = "Optional GitHub Actions environment name used in OIDC subject derivation."
  type        = string
  default     = null
  nullable    = true
}

variable "github_oidc_audiences" {
  description = "Audiences accepted by the federated credential."
  type        = list(string)
  default     = ["api://AzureADTokenExchange"]
}

variable "github_oidc_federated_credential_name" {
  description = "Name of the Entra federated credential object."
  type        = string
  default     = "github-oidc"
}

variable "assign_github_oidc_rg_contributor" {
  description = "Assign Contributor role at Resource Group scope to the GitHub OIDC service principal."
  type        = bool
  default     = true
}

variable "assign_github_oidc_acr_push" {
  description = "Assign AcrPush role on ACR to the GitHub OIDC service principal."
  type        = bool
  default     = true
}

variable "assign_github_oidc_subscription_contributor" {
  description = "Assign Contributor role at subscription scope to the GitHub OIDC service principal. Keep false unless required."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional Azure tags."
  type        = map(string)
  default     = {}
}
