---
theme: default
paginate: true
style: |
  .container {
    display: flex;
        gap: 1rem;
  }
  .column {
    flex: 1;
  }
---

# 📊 IaC Task Presentation

## **Monday, November 10, 2025**

```
🏗️ Multi-Environment Infrastructure as Code
FastAPI Application with Automated AWS Deployment

Andreas Bok Andersen
November 10, 2025
```

---

## **Agenda**

- Project Walkthrough
- Challenges and Approach
- Future Enhancements
- Discussion and Q&A

<!-- "Today I'll present my IaC solution: a production-ready FastAPI application with automated multi-environment deployment on AWS"
Assignment requirements overview and approach



-->

---

## **Requirements**

<div class="container">
<div class="column" style="overflow:hidden">

<!-- - Containerized Application
- IaC for Core AWS Infrastructure
- Multi-Environment Management
- CI/CD
  - Deployment and Release Strategy
  - Build and Deployment Orchestration Script(s)
- Task Configuration Management
-->

![width:600px](docs/media/task-assignment.png)

</div>

<div class="column">

![alt text](docs/media/problem-solving.png)

</div>
</div>
<!--
DELIVERED:
- FastAPI app with 3 endpoints (/health, /version, /)
- AWS CDK infrastructure (ECR, ECS Fargate, ALB, IAM, CloudWatch)
- Multi-environment (dev auto-deploy, prod manual approval)
- GitHub Actions CI/CD with OIDC authentication
- Docker layer caching and environment variables
- Documentation & verification scripts
- Reusable GitHub Actions (DRY principles)
- Security hardening (non-root containers, least privilege IAM)
- Multi-stage Docker builds for production readiness -->

---

## **Architecture Decisions**

```
🎯 Key Technical Decisions & Trade-offs

CDK (Python) vs Terraform:
✅ Choose CDK: Type safety, programmatic config, AWS integration
Trade-off: Less provider flexibility vs Terraform

Environment-Specific ECR vs Shared:
✅ Choose Environment-Specific: Clean isolation, IaC principles
Trade-off: Image promotion complexity vs cost optimization

OIDC vs Long-lived Keys:
✅ Choose OIDC: Enhanced security, no credential rotation
Trade-off: More complex setup vs Access Key based approaches
```
<!-- # Configuration-driven approach (config.py):
- Environment factory pattern for dev/prod settings
- Programmatic config vs cdk.context.json
- Static type-check support configuration with dataclasses

# Security implementation:
- OIDC trust policy: repo:bokchan/iac-task:*
- Least privilege: ECR push/pull + CDK bootstrap roles only
- Environment isolation: separate resources per environment -->

---

## **Assignment Requirements Checklist**

```
Performance:
✅ Faster image builds (Docker layer caching)
✅ Zero-downtime deployments (ECS rolling updates)
✅ Auto-scaling based on demand

Developer Experience:
✅ Complete local development setup (Docker Compose)
✅ Comprehensive documentation (3 READMEs + inline docs)
✅ Easy deployment verification (check-deployment.sh)
✅ Reusable CI/CD components (DRY principles)

Production Readiness:
✅ Security hardening (OIDC, non-root containers)
✅ Monitoring & logging integration
✅ Multi-environment isolation
✅ Infrastructure validation and testing
```

---

## **System Architecture**

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

## **Infrastructure as Code - AWS CDK**

### 4 Modular Stacks:

1. VpcStack → VPC + Multi-AZ networking
2. EcrStack → Container registry
3. GitHubOidcStack → OIDC + IAM roles
4. AppStack → ECS Fargate + ALB

 <!-- IAM: Identity and Access Management
 ALB: Application Load Balancer -->

---

## **Infrastructure as Code - Using classes**

<div class="container">
<div class="column">

```python
@dataclass
class EcsServiceConfig:
    """Configuration for the ECS Fargate service deployment."""

    cpu: int = 512  # 0.5 vCPU
    memory_limit_mb: int = 1024  # 1 GB
    desired_count: int = 1
    container_port: int = 8000
    log_group_prefix: str = "andreas-applogs"  # CloudWatch log group prefix
    application_settings: ApplicationSettings | None = (
        None  # Will be set per environment
    )
```

```python
@dataclass
class InfrastructureConfig:
    """Root configuration for all
    AWS infrastructure components."""

    aws_account: str
    aws_region: str
    environment: str
    project_name: str
    github_repo: str  # Format: "owner/repo"
    creator: str
    ecr: EcrConfig
    vpc: VpcConfig
    ecs_service: EcsServiceConfig
```

</div>

<div class="column">

```python
class AppStack(Stack):
    """A CloudFormation stack that creates
    the ECS service for the application."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: InfrastructureConfig,
        vpc_stack: VpcStack,
        ecr_stack: EcrStack,
        image_tag: str,
        **kwargs,
    ) -> None:
```

</div>
</div>

---

## **Infrastructure as Code - AWS Fargate**

> Fargate is a serverless, pay-as-you-go compute engine that lets you focus on building applications without managing servers

<div class="container">

<div class="column">

25 LoC to configure Fargate Service with the `ApplicationLoadBalancedFargateService` construct:

- Links VPC
- Memory and CPU resources
- Task count
- Application Image
- Link Log-groups
- Load Balancer

</div>

<div class="column">

<!-- ```python

        # Use the high-level ApplicationLoadBalancedFargateService construct
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FargateService",
            service_name=config.get_resource_name("service"),
            vpc=vpc_stack.vpc,
            cpu=config.ecs_service.cpu,
            memory_limit_mib=config.ecs_service.memory_limit_mb,
            desired_count=config.ecs_service.desired_count,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                family=config.get_resource_name("task"),
                image=ecs.ContainerImage.from_ecr_repository(
                    ecr_stack.repository, tag=image_tag
                ),
                container_port=config.ecs_service.container_port,
                environment={
                    "IMAGE_TAG": image_tag,
                    **config.ecs_service.application_settings.to_environment_dict(),  # type: ignore[union-attr]
                },
                log_driver=ecs.LogDriver.aws_logs(
                    stream_prefix="ecs",
                    log_group=log_group,
                ),
            ),
            public_load_balancer=True,
        )
``` -->

![height:450px](docs/media/fargate-overview.png)

</div>
</div>

---

## **CI/CD Pipeline**

Reusable Actions: setup-environment, build-push-image, deploy-cdk, run-qa

![height:450px](docs/media/github-workflow-light.jpeg)

---

## **Security & Production Features**

Authentication:

- OIDC-based (no stored AWS credentials)
- Repository-scoped trust policy
- Environment-specific IAM roles

Container Security:

- Multi-stage Docker builds
- Non-root user execution
- Minimal runtime dependencies
- ECR vulnerability scanning

<!--
Container security :

- Build tools excluded: Compilers, package managers, dev dependencies stay in build stages
- Smaller final image: Only runtime essentials are included
- Fewer vulnerabilities: Less software = fewer potential security holes

- Fargate Builtin security: doesn't allow for container with elevated permissions

- Faster deployments: Smaller images transfer quicker
- Less storage: Reduced ECR costs
- Faster container startup: Less to load into memory
- Performance is improved: Leaner and faster c
-->

<!-- ---

## **Security & Production Features**

Deployment Safety:

- Rolling deployments (zero downtime)
- Health check validation
- Manual production approval gates
- Environment isolation

Monitoring:

- CloudWatch centralized logging (andreas-applogs-{env})
- ALB health checks with proper timeouts
- Deployment verification scripts -->

---

## **Challenges 😬**

```sh
Running `cdk deploy` results in an error

> current credentials could not be used to assume
'arn:aws:iam::146082935119:role/cdk-hnb659fds-deploy-role-146082935119-eu-centra
l-1', but are for the right account. Proceeding anyway.
CiCdStack: This CDK deployment requires bootstrap stack version '6', but during
the confirmation via SSM parameter /cdk-bootstrap/hnb659fds/version the
following error occurred: AccessDeniedException: User:
arn:aws:iam::146082935119:user/andreas is not authorized to perform:
ssm:GetParameter on resource:
arn:aws:ssm:eu-central-1:146082935119:parameter/cdk-bootstrap/hnb659fds/version
because no identity-based policy allows the ssm:GetParameter action
```

---

## **Development Process**

**Time spent and tools**: ~5 full days with the help of ![height:32px](docs/media/copilot.png) and ![height:32px](docs/media/google-gemini.png)

- **AWS Free Tier**: Deployment to a personal AWS account
- **Planning**: Break the task assignment into issues for a [github project](https://github.com/users/bokchan/projects/2)
- **Refactoring**: E.g. github workflow from a single file to reusable actions
- **Debugging**: deployment cli scripts, CDK deployment errors

---

## **Future Enhancements**

Short-term Improvements:

- CDK unit tests for infrastructure validation\*
- Release version tagging
- End-to-end integration testing post-deployment
- CloudWatch alarms and dashboards

Medium-term Scaling:

- Cost optimization (arm64/Graviton, Fargate Spot)
- Blue/Green deployment strategy\*
- Custom CloudWatch metrics and alerting (Cloudwatch application signals)
- Container image scanning in pipeline (e.g Sonar)
- Drift detection

---

# Thanks

## **Discussion**

## **Q&A**

<!-- Topics I'm prepared to discuss:
- Architecture decisions and trade-offs
- Security implementation details
- CI/CD pipeline design choices
- Scaling and performance considerations
- Infrastructure as Code best practices
- Container orchestration strategies
- Multi-environment management
- Monitoring and observability:

Demo Available:
- Live application walkthrough
- Infrastructure deployment verification
- CI/CD pipeline in action -->

---

## Links

[Live FastAPI (dev)](http://iac-ta-farga-bmh2fqqhxdxk-533664939.eu-central-1.elb.amazonaws.com/docs)
[Localhost FastAPI](http://localhost:8000/docs)

[AWS Console -> Cloudformation](https://357864525704-w5qywbza.eu-central-1.console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks?filteringText=&filteringStatus=active&viewNested=true)

[Github project](https://github.com/users/bokchan/projects/2)

---

## **Detailed OIDC Authentication overview**

## ![height:530px](docs/media/github-oidc-overview.png)

---

## **Highlight: OIDC Based Authentication**

Policy for iac-task-prod-GitHubOidcStack-GitHubRole

```jsonc
{
    ...
            "Action": [ // Elastic Container Registry
                "ecr:BatchCheckLayerAvailability",
                "ecr:BatchGetImage",
                "ecr:CompleteLayerUpload",
                "ecr:GetDownloadUrlForLayer",
                "ecr:InitiateLayerUpload",
                "ecr:PutImage",
                "ecr:UploadLayerPart"
            ],
            "Resource": "arn:aws:ecr:eu-central-1:357864525704:repository/iac-task-prod-ecr-repository",
            ...
            "Action": "ecr:GetAuthorizationToken",
            ...
            "Action": "sts:AssumeRole", // Security Token Service
            "Resource": [
                "arn:aws:iam::357864525704:role/cdk-hnb659fds-deploy-role-357864525704-eu-central-1",
                "arn:aws:iam::357864525704:role/cdk-hnb659fds-file-publishing-role-357864525704-eu-central-1"
            ],
            ...
}
```

---

## **FastAPI Application Demo**

```
🌐 Production-Ready FastAPI Application

Live Demo:
- GET /           → {"message": "Hello World"} (configurable)
- GET /health     → "OK" (load balancer checks)
- GET /version    → {"version": "abc1234"} (deployment tracking)
- GET /docs       → Interactive OpenAPI documentation

Configuration:
- Environment Variables: ECHO_MESSAGE, LOG_LEVEL, IMAGE_TAG
- Structured logging with configurable levels
- Docker multi-stage build (security + performance)
- Non-root execution (uid 999)

```

---

## Fargate Scaling

```python
        # Configure horizontal auto-scaling
        # Task auto-scaling
        scalable_target = fargate_service.service.auto_scale_task_count(
            min_capacity=config.ecs_service.desired_count,
            max_capacity=config.ecs_service.desired_count * 2,
        )

        # Scale based on CPU and memory utilization
        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
        )
        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=70,
        )
```

---

## **AWS Cost Overview**

![height:500px](docs/media/aws-cost-overview.png)

---

## Multi-region support

- Stack-Level Region Configuration
  - Multi-Region Stack Deployment
- Cross-Region Considerations
  - ECR Image Replication
  - Global Load Balancer with Route 53
- CI/CD Pipeline Modifications
  - GitHub Actions Matrix Strategy

---
