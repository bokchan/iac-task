# ADR 0001: IaC Language and Migration Strategy

## Status

Accepted

## Context

The assignment is to migrate an existing AWS setup to Azure. The existing implementation is in CDKTF. This exercise assumes CDKTF deprecation pressure and a need to choose a sustainable IaC direction while still delivering a working migration quickly.

## Decision

Use Terraform for the Azure migration MVP and stage potential Pulumi adoption as a follow-up decision.

## Rationale

- Terraform provides a direct path from existing IaC concepts to Azure resources.
- Team hiring signal is improved by demonstrating delivery under tool and platform uncertainty.
- The migration objective is a working production-like outcome, not a full platform rewrite.
- Pulumi remains a viable next step once cloud baseline and operating model are stable.

## Consequences

- Short-term: Fastest path to delivery and validation on Azure.
- Medium-term: Keep code structured for future refactor into modules/components.
- Risk: Potential second migration if IaC language strategy changes later.
- Mitigation: Keep resource model, naming, tags, and policy assumptions explicit and portable.
