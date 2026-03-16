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

- I am assigned to migrate an existing deployment from AWS to Azure.
- The existing project uses CDKTF
- I have limited Azure experience and less familiarity with Terraform.

- Limited knowledge and experience with Azure and Terraform
- For this exercise, I assume CDKTF is sunset and no longer a good strategic choice.
- I want to demonstrate that I can still deliver a successful migration using AI responsibly.

<div class="small">

Working premise: the value is not "I knew Azure already". The value is that I can reduce risk, make sound decisions, validate outcomes, and leave behind a maintainable migration path.

</div>

<!--
Key message:
- I am deliberately showing learning velocity, decision quality, and execution discipline.
-->

---

## Presentation Flow

1. Starting point: existing AWS/CDKTF solution
2. Migration drivers and decision points
3. Azure target architecture and IaC choices
4. Execution journey: blockers, fixes, and AI usage
5. Current state, hardening, and next steps

---

## Starting Point: Existing AWS Solution

- FastAPI application in Docker
- CDKTF-based AWS infrastructure
- ECS Fargate for runtime
- ALB for public ingress
- ECR for container registry
- GitHub Actions with OIDC-based deployment

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

- Azure migration was the assignment.
- CDKTF was not a durable long-term direction for this scenario.
- I needed the fastest credible path to a working Azure deployment.

### Choice made

- Use Terraform for the Azure MVP.
- Keep Pulumi as a follow-up discussion, not a second migration inside the migration.

<div class="tiny">

Reference for the exercise assumption: HashiCorp CDKTF repository status and sunset context
https://github.com/hashicorp/terraform-cdk

</div>

<!--
This is a senior trade-off slide.
- Do not overclaim "Terraform is better".
- Claim: Terraform was the lower-risk transition path for this assignment.
-->

---

## Design Choices

| Decision             | Chosen Option                      | Why                                                    |
| -------------------- | ---------------------------------- | ------------------------------------------------------ |
| Azure compute target | Azure Container Apps               | Small operational surface, public ingress, fast MVP    |
| IaC language         | Terraform                          | Direct provider support, fastest path to delivery      |
| Registry auth        | Managed Identity + AcrPull         | Avoid admin credentials and long-lived secrets         |
| Rollout model        | Two-phase bootstrap + app deploy   | Prevent first-run failures before image exists         |
| Delivery approach    | AI-assisted with manual validation | Faster discovery without giving up engineering control |

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

## Target Architecture After Migration

```text
GitHub Repository
    ↓
Manual / CI-triggered Terraform workflow
    ↓
Azure Resource Group
    ├── Azure Container Registry
    ├── Log Analytics Workspace
    ├── Container Apps Environment
    ├── User Assigned Managed Identity
    └── Azure Container App
          ├── Public HTTPS ingress
          ├── Image pull from ACR via managed identity
          ├── Health probes on /health
          └── Scale rules with cost-aware defaults
```
---

### Result

- Public Azure-hosted web app
- Private image registry with identity-based access
- IaC-controlled deployment flow

---

## Execution Journey: What Actually Happened

- I started with limited Azure knowledge.
- AI helped accelerate exploration, command generation, and Terraform scaffolding.
- I still had to debug real platform issues:
  - Missing Azure provider registrations
  - Missing image tag in ACR
  - Wrong container image architecture on Apple Silicon
- I converted those failures into a more reliable deployment model.

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

- Service comparison and option exploration
- Terraform scaffolding and iteration speed
- Troubleshooting hypotheses
- Documentation and runbook drafting

### I remained accountable for

- Architecture choices
- Risk trade-offs
- Validation through plan/apply/smoke tests
- Hardening decisions after failures

<div class="small">

My claim is not "AI solved it". My claim is that I used AI as an accelerator and still owned the engineering outcome.

</div>

---

## Current Status and Senior-Level Improvements

### Delivered

- Successful AWS to Azure MVP migration
- Working Azure Container App with public ingress
- Clean-slate reprovision validated
- Cost-aware dev defaults such as scale-to-zero

### Added hardening

- ADRs for migration and architecture decisions
- Risk register and rollback thinking
- Remote state scaffolding for team-safe execution
- GitHub Actions workflow for Terraform validate and reviewed plan output
- Production guardrails to prevent accidental bootstrap behavior

---

## What I Would Do Next in a Real Project

1. Move Terraform state to Azure Storage with locked shared access.
2. Replace manual deployment with Azure-authenticated CI/CD.
3. Add static checks such as `tflint`, `tfsec` or `checkov`, and drift detection.
4. Introduce production networking hardening, secret management, and budget alerts.
5. Revisit long-term IaC direction: stay on Terraform or move to Pulumi once the Azure baseline is stable.

<!--
This keeps the story grounded: MVP first, then platform hardening.
-->

---

## Discussion

### Questions I would welcome

- Was Terraform the right bridge technology from CDKTF?
- When is a second IaC migration justified?
- How should AI usage be governed in infrastructure work?
- What would be your production-readiness bar for this system?

## Thank you
