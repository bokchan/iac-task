# Terraform State Strategy for Azure Migration

## Goal

Move from local Terraform state to shared remote state with locking and access controls.

## Backend Pattern

- Backend type: azurerm
- Storage location: dedicated state resource group and storage account
- Isolation model: separate state key per environment

## Setup Steps

1. Create backend infrastructure (resource group, storage account, blob container).
2. Copy [azure-infra/backend.dev.hcl.example](azure-infra/backend.dev.hcl.example) to a local non-committed backend file.
3. Run initialization with backend config.

```bash
cd azure-infra
cp backend.dev.hcl.example backend.dev.hcl
terraform init -backend-config=backend.dev.hcl -migrate-state
```

## Access Model

- Grant least-privilege access to CI identity and engineering group.
- Avoid account keys in pipelines; prefer OIDC/federated identity.

## Operational Controls

- Require plan output artifact for every change.
- Run applies only after review and approval.
- Periodically run drift detection plans.
