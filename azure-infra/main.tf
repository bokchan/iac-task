locals {
  name_prefix     = lower(replace("${var.project_name}-${var.environment}", "_", "-"))
  acr_name        = var.acr_name_override != null ? var.acr_name_override : substr(replace(lower("${var.project_name}${var.environment}${substr(md5(var.subscription_id), 0, 8)}"), "-", ""), 0, 50)
  container_image = "${azurerm_container_registry.main.login_server}/${var.container_repository}:${var.container_image_tag}"
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

resource "azurerm_resource_group" "main" {
  name     = "${local.name_prefix}-rg"
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_container_registry" "main" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = false
  tags                = local.common_tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.name_prefix}-law"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

resource "azurerm_container_app_environment" "main" {
  name                       = "${local.name_prefix}-cae"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.common_tags
}

resource "azurerm_user_assigned_identity" "webapp" {
  name                = "${local.name_prefix}-uami"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.webapp.principal_id
}

resource "azurerm_container_app" "webapp" {
  count                        = var.deploy_container_app ? 1 : 0
  name                         = "${local.name_prefix}-webapp"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.webapp.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.webapp.id
  }

  ingress {
    external_enabled           = true
    target_port                = var.container_port
    allow_insecure_connections = false
    transport                  = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "webapp"
      image  = local.container_image
      cpu    = var.container_cpu
      memory = var.container_memory

      env {
        name  = "IMAGE_TAG"
        value = var.container_image_tag
      }

      env {
        name  = "ECHO_MESSAGE"
        value = var.echo_message
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      liveness_probe {
        transport = "HTTP"
        port      = var.container_port
        path      = "/health"
      }

      readiness_probe {
        transport = "HTTP"
        port      = var.container_port
        path      = "/health"
      }

      startup_probe {
        transport = "HTTP"
        port      = var.container_port
        path      = "/health"
      }
    }
  }

  tags = local.common_tags

  depends_on = [azurerm_role_assignment.acr_pull]

  lifecycle {
    precondition {
      condition     = length(trimspace(var.container_image_tag)) > 0
      error_message = "container_image_tag must be non-empty when deploy_container_app is true."
    }
  }
}
