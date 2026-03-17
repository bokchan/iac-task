data "azurerm_client_config" "current" {}

data "azurerm_subscription" "current" {
  subscription_id = var.subscription_id
}

data "azuread_service_principal" "github_oidc_existing" {
  count     = var.create_github_oidc_identity ? 0 : 1
  client_id = var.existing_github_oidc_client_id
}

locals {
  github_oidc_app_name = var.github_oidc_application_name != null ? var.github_oidc_application_name : "${local.name_prefix}-github-oidc"
  github_oidc_subject = var.github_oidc_subject != null ? var.github_oidc_subject : (
    var.github_oidc_environment_name != null
    ? "repo:${var.github_repository_owner}/${var.github_repository_name}:environment:${var.github_oidc_environment_name}"
    : "repo:${var.github_repository_owner}/${var.github_repository_name}:ref:refs/heads/${var.github_oidc_branch}"
  )

  github_oidc_client_id                   = var.create_github_oidc_identity ? azuread_application.github_oidc[0].client_id : var.existing_github_oidc_client_id
  github_oidc_service_principal_object_id = var.create_github_oidc_identity ? azuread_service_principal.github_oidc[0].object_id : data.azuread_service_principal.github_oidc_existing[0].object_id
  github_oidc_application_object_id       = var.create_github_oidc_identity ? azuread_application.github_oidc[0].object_id : var.existing_github_oidc_application_object_id
}

resource "azuread_application" "github_oidc" {
  count        = var.create_github_oidc_identity ? 1 : 0
  display_name = local.github_oidc_app_name

  lifecycle {
    precondition {
      condition     = var.create_github_oidc_identity || var.existing_github_oidc_client_id != null
      error_message = "Set existing_github_oidc_client_id when create_github_oidc_identity is false."
    }
  }
}

resource "azuread_service_principal" "github_oidc" {
  count     = var.create_github_oidc_identity ? 1 : 0
  client_id = azuread_application.github_oidc[0].client_id
}

resource "azuread_application_federated_identity_credential" "github_oidc" {
  count = var.create_github_federated_credential ? 1 : 0

  application_id = local.github_oidc_application_object_id
  display_name   = var.github_oidc_federated_credential_name
  description    = "GitHub Actions OIDC federation"
  audiences      = var.github_oidc_audiences
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = local.github_oidc_subject

  lifecycle {
    precondition {
      condition     = local.github_oidc_application_object_id != null
      error_message = "Application object_id is required to create federated credential. Set existing_github_oidc_application_object_id when reusing an existing app."
    }
  }
}

resource "azurerm_role_assignment" "github_oidc_rg_contributor" {
  count                = var.assign_github_oidc_rg_contributor ? 1 : 0
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = local.github_oidc_service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azuread_service_principal.github_oidc]
}

resource "azurerm_role_assignment" "github_oidc_subscription_contributor" {
  count                = var.assign_github_oidc_subscription_contributor ? 1 : 0
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Contributor"
  principal_id         = local.github_oidc_service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azuread_service_principal.github_oidc]
}

resource "azurerm_role_assignment" "github_oidc_acr_push" {
  count                = var.assign_github_oidc_acr_push ? 1 : 0
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPush"
  principal_id         = local.github_oidc_service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azuread_service_principal.github_oidc]
}
