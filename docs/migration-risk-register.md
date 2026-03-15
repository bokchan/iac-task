# Migration Risk Register

## Scope

AWS to Azure migration of containerized web app using Terraform.

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation | Trigger/Signal |
|---|---|---|---|---|
| Provider registration missing in subscription | Medium | High | Pre-register required namespaces before first apply; add preflight checks in runbook | Terraform errors with MissingSubscriptionRegistration |
| Terraform state drift after interrupted apply | Medium | High | Use remote state with locking and documented import/reconcile flow | Resource exists in Azure but not in state |
| Image not found or wrong architecture | Medium | High | Enforce push step before app deploy; build linux/amd64 image | Container App revision fails to provision |
| Accidental destructive action in production | Low | High | Block prod bootstrap by default, require explicit override, and require reviewed plan artifacts before apply | Plan shows destroy on core resources |
| Cost growth due to always-on settings | Medium | Medium | Keep dev defaults scale-to-zero and review ACR SKU by environment | Cost anomaly alerts or monthly burn rise |
| Knowledge concentration during migration | Medium | Medium | Keep ADRs, runbooks, and CI checks in repo | Team cannot reproduce deployment independently |

## Rollback Strategy

1. Keep previous AWS deployment path available until Azure smoke tests pass.
2. On failed Azure rollout, disable ingress traffic to failed revision and redeploy prior known-good image.
3. If IaC state is compromised, restore from remote backend state history and re-run plan.
