# subscription_id is intentionally not stored in version control.
# Set it in your shell before running Terraform:
# export TF_VAR_subscription_id="00000000-0000-0000-0000-000000000000"
subscription_id = "00000000-0000-0000-0000-000000000000"
location        = "westeurope"
environment     = "dev"
project_name    = "iac-task"
# Optional override if you need a specific globally unique ACR name.
acr_name_override    = "iactaskdevg18ctp"
acr_sku              = "Standard"
container_repository = "webapp"
container_image_tag  = "latest"
deploy_container_app = false
container_port       = 8000
container_cpu        = 0.5
container_memory     = "1Gi"
min_replicas         = 0
max_replicas         = 2
echo_message         = "Hello from Azure MVP"
log_level            = "INFO"

tags = {
  Owner      = "andreas"
  ManagedBy  = "terraform"
  Repository = "iac-task"
}
