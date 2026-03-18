---
theme: default
paginate: true
style: |
  section {
    font-size: 28px;
  }
  h1 {
    color: #0f4c5c;
  }
  h2 {
    color: #1b4965;
  }
  .container {
    display: flex;
    gap: 1rem;
  }
  .column {
    flex: 1;
  }
  .small {
    font-size: 22px;
  }
  .tiny {
    font-size: 18px;
  }
  .mermaid {
    font-size: 20px;
  }
---

# AWS to Azure Migration

## AI-Assisted IaC Delivery

Andreas Bok Andersen
March 19, 2026

<!--
Opening:
- Frame this as a realistic migration assignment, not a toy demo.
- Goal: show how I work under uncertainty, not just the final code.
-->

---

## Context and Assumptions

- Assignment: migrate an existing AWS deployment to Azure.
- Starting point: infrastructure defined with CDKTF.
- Constraint: limited Azure and Terraform experience at project start.
- Assumption: CDKTF is sunset, so long-term direction must change.
- Objective: deliver a working migration with AI assistance and clear engineering ownership.

<div class="small">

Core value: reduce risk, make explicit trade-offs, validate outcomes, and leave a maintainable migration path.

</div>

<!--
Key message:
- I am deliberately showing learning velocity, decision quality, and execution discipline.
-->

---

## Agenda

1. Starting point: existing AWS/CDKTF solution
2. Migration drivers and decision points
3. Azure target architecture and IaC choices
4. Execution journey: blockers, fixes, and AI usage
5. Current state, hardening, and next steps

---

## Starting Point: Existing AWS Solution

- FastAPI app packaged as Docker image
- CDKTF-managed AWS infrastructure
- ECS Fargate + ALB for runtime and ingress
- ECR + GitHub Actions with OIDC authentication

<!--
Reused context from previous interview exercise.
Important: I did not start from zero. I started from an existing app and IaC baseline.
-->

---

## Existing AWS Solution

<!--
GitHub Repository
GitHub Actions CI/CD
    ├── QA Checks (ruff, pyrefly)
    ├── Docker Build + ECR Push (with caching)
    ├── Deploy Development (automatic)
    └── Deploy Production (manual approval)
    ↓
AWS Infrastructure
    ├── VPC (Multi-AZ, public/private subnets)
    ├── ECR (Environment-specific repositories)
    ├── ECS Fargate (Auto-scaling containers)
    └── ALB (Load balancer with health checks)

Key: Zero long-lived credentials, complete automation -->

![alt text](<docs/media/Application Lifecycle Architecture.png>)

---

## Why Change the IaC Approach?

### Migration driver

- Azure migration was mandated by the assignment.
- CDKTF no longer fit the long-term strategy.
- Priority was fastest credible path to a working Azure deployment.

### Choice made

- Use Terraform for the Azure MVP.
- Bicep is Azure specific. Knowledge of Terraform is more transferable across clouds and tools.
- Keep Pulumi as an explicit follow-up, not a second migration during MVP delivery.

<div class="tiny">

HashiCorp CDKTF repository status and sunset context https://github.com/hashicorp/terraform-cdk

</div>

<!--
This is a senior trade-off slide.
- Do not overclaim "Terraform is better".
- Claim: Terraform was the lower-risk transition path for this assignment.
-->

---

## Design Choices

| Decision          | Chosen Option            | Why                                   |
| ----------------- | ------------------------ | ------------------------------------- |
| Azure compute     | Container Apps           | Managed ingress, fast MVP             |
| IaC language      | Terraform                | Native Azure support, low migration risk |
| Registry auth     | Managed Identity + AcrPull | No static credentials               |
| CI/CD auth        | GitHub OIDC -> Entra SP  | Secretless, scoped Azure access       |
| Rollout model     | Bootstrap, then app deploy | Prevent first-run image failures    |
| Delivery approach | AI + manual validation   | Faster delivery with human checks     |

<!--
This slide is where I show selection criteria, not tool fandom.
-->

---

## AWS to Azure Mapping

| AWS                       | Azure                    | Chosen for MVP |
| ------------------------- | ------------------------ | -------------- |
| ECS Fargate               | Azure Container Apps     | Yes            |
| Application Load Balancer | Container Apps Ingress   | Yes            |
| ECR                       | Azure Container Registry | Yes            |
| CloudWatch Logs           | Log Analytics            | Yes            |
| IAM role assumptions      | Managed Identity + RBAC  | Yes            |
| VPC + subnets             | Virtual Network          | Deferred       |
| CDKTF                     | Terraform                | Yes            |

<div class="small">

Senior angle: I mapped capabilities first, then decided what to keep, replace, or defer for MVP.

</div>

---

## Azure Target Architecture

<!-- ![alt text](<docs/media/Azure Arch.png>) -->
<img src="docs/media/Azure Arch.png"  height="580">

<div class="small">

One-line story: GitHub Actions authenticates to Azure without secrets, deploys to Container Apps, and traffic plus logs flow through managed Azure services.

</div>

<!--
Use this slide when time is short.
Narrate left-to-right: auth, authorization, deploy targets, runtime traffic, observability.
-->

---

### Result

- Public Azure-hosted web app
- Identity-based private registry access
- Secretless CI/CD authentication from GitHub via OIDC federation
- Simpler operational model than original AWS baseline

---

## Execution Journey: What Actually Happened

- Learned Azure basics through Microsoft Learn and set up Terraform locally.
- Used AI for discovery, command drafting, and IaC scaffolding.
- Debugged real failures: provider registration, state drift, image tag/architecture issues.
- Converted failure patterns into a more reliable deployment workflow.

### Key correction

- Split deployment into:
  1. Infrastructure bootstrap
  2. Image build and push
  3. Container App deployment

<!--
This is one of the strongest slides.
- Shows real engineering, not generated happy-path output.
-->

---

## How I Used AI

### AI helped with

- Service comparison and option framing
- Terraform scaffolding and faster iteration
- Troubleshooting hypotheses
- Documentation and runbook drafting

### I remained accountable for

- Architecture choices
- Risk trade-offs
- Validation through plan/apply/smoke tests
- Hardening decisions after failures

<div class="small">

AI was an accelerator. Architecture decisions, risk acceptance, and validation remained my responsibility.

</div>

---

## Current Status and Senior-Level Improvements

### Delivered

- Successful AWS to Azure MVP migration
- Working Azure Container App with public ingress
- Clean-slate reprovision validated
- Cost-aware defaults such as scale-to-zero
- GitHub OIDC federation to Entra Service Principal with scoped RBAC for deployment

### Added hardening

- ADRs for migration and architecture decisions
- Risk register and rollback thinking
- Remote state scaffolding for team-safe execution
- GitHub Actions workflow for Terraform validate and plan artifact review
- Production guardrails to prevent accidental bootstrap behavior

---

## Improvement Backlog

| Area                 | Current State                                                           | Next Step                                                 |
| -------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------- |
| State management     | Local-first with remote backend scaffolding                             | Move fully to shared remote state                         |
| Deployment           | OIDC trust and RBAC are in place; apply still mostly operator-triggered | Add protected environment gates and fully automated apply |
| Security             | Managed identity and private registry pull                              | Add secret store integration and policy scanning          |
| Platform reliability | Two-phase deploy and smoke checks                                       | Add drift detection and environment promotion             |
| Cost control         | Dev scale-to-zero defaults                                              | Add budget alerts and environment-specific SKUs           |

---

## Next 90 Days (Production Path)

1. Move fully to shared remote state with access control and locking.
2. Keep OIDC auth, then enforce protected environments and approval gates for apply.
3. Add policy/security checks, drift detection, and budget alerts.

<!--
This keeps the story grounded: MVP first, then platform hardening.
-->

---

## Discussion

### Questions I would welcome

- Was Terraform the right bridge technology from CDKTF?
- At what point does a second IaC migration become justified?
- How should AI usage be governed in infrastructure work?
- What would be your production-readiness bar for this system?

## Thank you
