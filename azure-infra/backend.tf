terraform {
  # Configure remote state via -backend-config file during terraform init.
  # Example:
  # terraform init -backend-config=backend.dev.hcl
  backend "azurerm" {}
}
