# Simple CI/CD Pipeline - Mermaid Diagram

```mermaid
flowchart TD
    subgraph auto ["🔄 Automatic Pipeline: Push-to-Main → Deploy CDK to Dev"]
        direction LR
        A[📅 Push to main]
        B1[Infrastructure<br/>ruff + pyrefly]
        B2[Webapp<br/>ruff + pyrefly]
        C1[🐳 Docker Build<br/>+ Layer Cache]
        C2[📦 Push to ECR<br/>Git SHA Tag]
        C3[🚀 Deploy CDK<br/>to Dev]

        A --> B1
        A --> B2
        B1 --> C1
        B2 --> C1
        C1 --> C2
        C2 --> C3
    end

    subgraph manual ["⚠️ Manual Pipeline: Approval → Deploy CDK Same SHA Tag"]
        direction LR
        D[⚠️ Manual Approval<br/>Production Gate]
        E1[🐳 Build Prod Image]
        E2[🚀 Deploy CDK<br/>Same SHA Tag]

        D --> E1
        E1 --> E2
    end

    C3 -.-> D

    classDef qa fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef build fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef deploy fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef prod fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef approval fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    classDef subgraphStyle fill:#f9f9f9,stroke:#ddd,stroke-width:1px

    class A,B1,B2 qa
    class C1,C2,C3 build
    class D approval
    class E1,E2 prod
    class auto,manual subgraphStyle
```

## Key Pipeline Steps

1. **QA Checks** - Parallel matrix for infrastructure and webapp
2. **Build & Deploy** - Docker build with caching, push to dev ECR, deploy to development
3. **Manual Approval** - Production gate requiring human approval
4. **Deploy Prod** - Build production image, deploy with same git SHA tag

## Reusable Actions
- setup-environment
- build-push-image
- deploy-cdk
- run-qa

