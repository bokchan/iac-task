# ADR 0002: Azure Target Architecture and Phased Rollout

## Status

Accepted

## Context

The migration should deliver a publicly reachable app quickly with low operational overhead. Initial failures during first-time apply showed that app deployment can fail when image availability and infrastructure provisioning are not sequenced.

## Decision

Use Azure Container Apps with a phased rollout:

1. Bootstrap phase: deploy core infrastructure only.
2. Push application image to ACR.
3. App phase: deploy the Container App with ingress and probes.

## Rationale

- Reduces first-run failure modes caused by missing images.
- Keeps architecture simple for MVP while retaining identity-based registry access.
- Supports iterative hardening without reworking the deployment model.

## Consequences

- Requires explicit runbook and clear variable toggles.
- Improves repeatability for clean-slate deployments.
- Provides a clear control point for production safeguards.
