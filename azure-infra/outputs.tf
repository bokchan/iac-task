output "resource_group_name" {
  description = "Resource Group name hosting the Azure MVP resources."
  value       = azurerm_resource_group.main.name
}

output "container_registry_login_server" {
  description = "ACR login server for docker push and image reference."
  value       = azurerm_container_registry.main.login_server
}

output "container_app_environment_name" {
  description = "Container Apps environment name."
  value       = azurerm_container_app_environment.main.name
}

output "container_app_name" {
  description = "Azure Container App name."
  value       = var.deploy_container_app ? azurerm_container_app.webapp[0].name : null
}

output "container_app_fqdn" {
  description = "Public FQDN for the deployed webapp."
  value       = var.deploy_container_app ? azurerm_container_app.webapp[0].latest_revision_fqdn : null
}

output "container_app_url" {
  description = "Public URL for the deployed webapp."
  value       = var.deploy_container_app ? "https://${azurerm_container_app.webapp[0].latest_revision_fqdn}" : null
}

output "managed_identity_principal_id" {
  description = "Principal ID for the user-assigned identity used by the webapp."
  value       = azurerm_user_assigned_identity.webapp.principal_id
}
