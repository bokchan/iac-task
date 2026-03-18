# Azure Migration Plan and Implementation Guide

This document captures the AWS to Azure migration plan for the current project and provides a concrete implementation path for the MVP deployment.

## Scope and Target

- Goal: Deploy the existing containerized FastAPI webapp to Azure and expose it to the internet.
- IaC: Terraform.
- Hosting: Azure Container Apps.
- CI/CD: Explicitly out of scope for this phase (follow-up).

## Current AWS Footprint

The current infrastructure is defined under [infra](infra) and uses:

- ECS Fargate + ALB for app hosting and public ingress in [infra/stacks/app_stack.py](infra/stacks/app_stack.py#L1)
- ECR for image storage in [infra/stacks/ecr_stack.py](infra/stacks/ecr_stack.py#L1)
- VPC for networking in [infra/stacks/vpc_stack.py](infra/stacks/vpc_stack.py#L1)
- IAM OIDC integration for GitHub in [infra/stacks/github_oidc_stack.py](infra/stacks/github_oidc_stack.py#L1)
- GitHub deployment workflow in [.github/workflows/main.yml](.github/workflows/main.yml#L1)

## AWS to Azure Component Mapping

| AWS | Azure Equivalent | MVP Choice | Notes |
|---|---|---|---|
| ECS Fargate Service | Azure Container Apps | Azure Container Apps | Best fit for a single containerized web service. |
| Application Load Balancer | Container Apps Ingress | Built-in external ingress | Public HTTPS endpoint without extra gateway in MVP. |
| Elastic Container Registry | Azure Container Registry | ACR Standard | Admin disabled, identity-based pull. |
| CloudWatch Logs | Log Analytics + Azure Monitor | Log Analytics | Baseline observability included in MVP. |
| IAM role assumptions | Managed Identity + RBAC | User-assigned identity | Used for secure image pull from ACR. |
| VPC + subnets | Virtual Network | Deferred | Not required for this MVP unless compliance requires it. |
| AWS CDK | Terraform | Terraform | New Azure infra is separate from AWS CDK code. |

## Azure Terraform Implementation

Azure Terraform is implemented in [azure-infra](azure-infra):

- [azure-infra/versions.tf](azure-infra/versions.tf)
- [azure-infra/providers.tf](azure-infra/providers.tf)
- [azure-infra/variables.tf](azure-infra/variables.tf)
- [azure-infra/main.tf](azure-infra/main.tf)
- [azure-infra/outputs.tf](azure-infra/outputs.tf)
- [azure-infra/dev.tfvars](azure-infra/dev.tfvars)
- [azure-infra/bootstrap.tfvars](azure-infra/bootstrap.tfvars)

### Resources Created

1. Resource Group
2. Azure Container Registry (admin disabled)
3. Log Analytics Workspace
4. Container Apps Environment
5. User-assigned Managed Identity
6. RBAC role assignment (AcrPull on ACR)
7. Public Azure Container App with:
   - HTTPS ingress (insecure disabled)
   - Port 8000 routing
   - Liveness/readiness/startup probes on `/health`
   - Env vars: `IMAGE_TAG`, `ECHO_MESSAGE`, `LOG_LEVEL`
   - Explicit CPU/memory and replica limits

Notes:

- ACR name is now deterministic by default (derived from project, environment, and subscription) so repeated clean-slate runs in the same subscription reuse the same registry name.
- Container App creation is gated by `deploy_container_app`. This prevents first-run failures when the image has not been pushed yet.

## Deployment Process

### 1. Prerequisites

- Terraform installed
- Azure CLI installed
- Docker installed
- Access to an Azure subscription

### 2. Configure Variables

Set subscription id from environment:

```bash
export TF_VAR_subscription_id="<your-subscription-id>"
```

Then update [azure-infra/dev.tfvars](azure-infra/dev.tfvars) with your real values:

- `location` (if needed)
- app settings (`echo_message`, `log_level`)

### 3. Phase 1 - Bootstrap Infrastructure

From project root:

```bash
cd azure-infra
terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars -auto-approve
```

Capture outputs:

- `container_registry_login_server`
- `container_app_environment_name`
- `resource_group_name`

At this stage, `container_app_url` is expected to be null because `deploy_container_app = false` is set by [azure-infra/dev.tfvars](azure-infra/dev.tfvars).

Important: the Container Apps environment can take 1-2 minutes to finish provisioning after this apply completes.

### 4. Build and Push Container Image

```bash
az login
az account set --subscription <your-subscription-id>

cd ..
az acr login --name <acr-name>
docker buildx build --platform linux/amd64 -f webapp/Dockerfile \
   -t <acr-login-server>/webapp:latest ./webapp --push
az acr repository show -n <acr-name> --repository webapp
```

If you are running on Apple Silicon, the `--platform linux/amd64` flag is required. Without it, Azure Container Apps can fail with errors such as `no child with platform linux/amd64`.

### 5. Phase 2 - Deploy Container App

Deploy the app after the image exists in ACR:

```bash
cd azure-infra
terraform apply -var-file=dev.tfvars -var='deploy_container_app=true' -auto-approve
```

If Terraform reports `ManagedEnvironmentNotProvisioned`, wait 60 seconds and retry. If state is out of sync after an interrupted apply, import the existing environment and re-run apply:

```bash
terraform import azurerm_container_app_environment.main \
   /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.App/managedEnvironments/<env-name>
terraform apply -var-file=dev.tfvars -var='deploy_container_app=true' -auto-approve
```

Capture outputs:

- `container_app_url`
- `container_app_fqdn`
- `container_app_name`

### 6. Update Deployed Image Tag

Set `container_image_tag` in [azure-infra/dev.tfvars](azure-infra/dev.tfvars), then re-apply:

```bash
cd azure-infra
terraform apply -var-file=dev.tfvars -var='deploy_container_app=true' -auto-approve
```

### 7. Validate MVP Deployment

Check these endpoints on `container_app_url`:

- `/`
- `/health`
- `/version`
- `/docs`
- `/redoc`

## Design Decisions for MVP Best Practices
- HTTPS-only public ingress
- Managed identity for private registry pull
- Baseline observability with Log Analytics
- Explicit probes, CPU/memory, and scaling bounds

Deferred intentionally:

- CI/CD migration from AWS workflows to Azure workflows
- Custom domain and certificate management beyond default Container Apps endpoint
- VNet/private ingress hardening
- Front Door/Application Gateway/WAF
- Multi-environment parity and production promotion flow

## Follow-Up: CI/CD Migration

Current GitHub automation covers Terraform validate on pull requests and an Azure-authenticated Terraform plan on main or manual dispatch. Full image build, push, and apply automation is still follow-up work.

Once manual Azure deployment is stable, replace AWS-specific GitHub actions in:

- [.github/actions/setup-environment/action.yml](.github/actions/setup-environment/action.yml#L1)
- [.github/workflows/main.yml](.github/workflows/main.yml#L1)

with Azure federation login, ACR push, and Terraform apply steps.

## Senior Delivery Artifacts

The migration now includes additional governance and execution controls:

- ADRs:
   - [docs/adr/0001-iac-language-and-migration-strategy.md](docs/adr/0001-iac-language-and-migration-strategy.md)
   - [docs/adr/0002-azure-target-architecture-and-phased-rollout.md](docs/adr/0002-azure-target-architecture-and-phased-rollout.md)
- Risk register:
   - [docs/migration-risk-register.md](docs/migration-risk-register.md)
- Remote state strategy:
   - [docs/terraform-state-strategy.md](docs/terraform-state-strategy.md)
- CI guardrails:
   - [.github/workflows/terraform-azure.yml](.github/workflows/terraform-azure.yml)

Terraform now includes production guardrails in [azure-infra/main.tf](azure-infra/main.tf):

## Troubleshooting

### Missing provider registration

If apply fails with `MissingSubscriptionRegistration` for `Microsoft.App`:

```bash
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az provider register --namespace Microsoft.ContainerRegistry --wait
az provider register --namespace Microsoft.ManagedIdentity --wait
az provider register --namespace Microsoft.Insights --wait
```

### Failed Container App exists outside Terraform state

If Terraform says the Container App already exists but is not in state, and it is in `Failed` provisioning state, delete it and re-apply:

```bash
az containerapp delete -g iac-task-dev-rg -n iac-task-dev-webapp --yes
terraform apply -var-file=dev.tfvars -var="deploy_container_app=true"
```

### Image not found or wrong architecture

If apply fails with `MANIFEST_UNKNOWN` or `no child with platform linux/amd64`:

1. Push `webapp:<tag>` to the output ACR login server.
2. Ensure image is built with `--platform linux/amd64`.
3. Re-run: `terraform apply -var-file=dev.tfvars -var="deploy_container_app=true"`.

### Container App Environment Not Provisioned

**Error:** `ManagedEnvironmentNotProvisioned: The environment has not been provisioned successfully.`

The Container App Environment created in Phase 1 provisions asynchronously and takes 1–2 minutes. Solutions:

1. **Wait and retry** (simple):
   ```bash
   sleep 60
   terraform apply -var-file=dev.tfvars -var='deploy_container_app=true' -auto-approve
   ```

2. **Import existing environment and retry** (if wait fails):
   ```bash
   # Get subscription and resource group from terraform output
   terraform output resource_group_name
   terraform output container_app_environment_name

   # Import the environment into state
   terraform import azurerm_container_app_environment.main \
     /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.App/managedEnvironments/<env-name>

   # Retry apply
   terraform apply -var-file=dev.tfvars -var='deploy_container_app=true' -auto-approve
   ```

3. **Verify provisioning state in Azure portal:**
   - Go to Resource Group > Container Apps environments > `<env-name>`
   - Check Provisioning State (should be "Succeeded")

### Terraform State Out of Sync

If Terraform state loses track of resources created in Azure (e.g., after interrupted apply):

```bash
# Refresh state from Azure
terraform refresh -var-file=dev.tfvars

# If specific resource is missing, import it
terraform import <resource-type>.<name> <azure-resource-id>

# Then re-plan and apply
terraform apply -var-file=dev.tfvars -var='deploy_container_app=true'
```

### Clean Slate Redeployment

To delete all Azure resources and start fresh:

```bash
# Destroy all Terraform-managed resources
cd azure-infra
terraform destroy -var-file=dev.tfvars -auto-approve

# Or delete resource group directly (faster but less controlled)
az group delete --name $(terraform output resource_group_name) --yes

# Then re-start from Phase 1
terraform apply -var-file=dev.tfvars -auto-approve
```

### Image Not Found in ACR

If apply fails because the image is not in the container registry:

```bash
# Check if image exists
az acr repository show -n <acr-name> --repository webapp

# If not, build and push (Phase 4)
cd ..
docker buildx build --platform linux/amd64 -f webapp/Dockerfile \
  -t <acr-login-server>/webapp:latest ./webapp --push

# Then retry Container App creation
cd azure-infra
terraform apply -var-file=dev.tfvars -var='deploy_container_app=true'
```
