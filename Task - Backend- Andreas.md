October 24, 2025
```
Assignment | Multi-Environment Infrastructure as Code (IaC) and CI/CD Task
```
```
Your task is to design and implement a robust Infrastructure as Code (IaC) solution using AWS CDK
```
```
(Python or Typescript) or Terraform to deploy and manage a containerized web application across
```
```
two distinct environments: development (dev) and production (prod). The goal is to demonstrate
```
best practices in:
● Environment isolation
● Configuration management
● Deployment automation using GitHub Actions CI/CD
We recognize that unfamiliarity with certain technologies or techniques might significantly extend
the time required for this assignment. It is perfectly acceptable for some sections, particularly the
optional items, to remain incomplete. Should you decide to narrow the scope to manage your time
effectively, please detail the simplifying assumptions made and the challenges encountered.
Requirements
1. Containerized Application
Create a simple web app using Python Flask/FastAPI or Node.js Express. The app must expose
```
at least one HTTP GET endpoint (e.g., /health and /version). Containerize the app with
```
```
Docker. Make the container configurable via environment variables (e.g., LOG_LEVEL,
```
```
GREETING_MESSAGE).
```
2. IaC for Core AWS Infrastructure
Use AWS CDK or Terraform to provision:
● Amazon ECR: Private Docker repository.
● Amazon ECS with AWS Fargate:
○ ECS Cluster
○ Task Definitions & ECS Services
```
● Application Load Balancer (ALB): To route external traffic to your ECS service.
```
● IAM Roles and Policies: Apply least-privilege principles.
● CloudWatch Log Groups: For ECS and application logs.
3. Multi-Environment Management
IaC must support distinct dev and prod environments. Each environment must differ in:
PHASETREE | MASKINVEJ 5. - 2860 SØBORG| CVR: 42239895| WWW.PHASETREE.AI PAGE 1 of 5
● ECS CPU/memory configuration
● Desired task count
● Environment variables
Use clear mechanisms to manage config differences:
```
● CDK: context files (cdk.context.json)
```
● Terraform: workspaces or input variables
```
Resources must be named and tagged to distinguish environments (e.g.,
```
```
myapp-dev-service).
```
4. Deployment and Release Strategy
● Dev Deployment:
○ Automatically deploy the latest Docker image on code push.
● Prod Deployment:
○ Deployment must be controlled:
■ Explicit image tag parameter
■ Manual approval step
■ ECS rolling update strategy for safe rollout
5. Build and Deployment Orchestration Script(s)
Define a GitHub Actions pipeline in .github/workflows/main.yml that:
● Builds the Docker image.
```
● Pushes it to ECR (tagged with version or commit hash).
```
● Deploys to the dev automatically when changes are pushed to the dev branch.
```
● Deploys to prod only after a manual approval step (e.g., GitHub environment
```
```
protection).
```
CI/CD must:
● Use GitHub secrets for sensitive data
● Cache Docker layers where applicable
● Handle errors and provide clear logs
PHASETREE | MASKINVEJ 5. - 2860 SØBORG| CVR: 42239895| WWW.PHASETREE.AI PAGE 2 of 5
6. Configuration Management
```
Demonstrate how to pass environment-specific configuration (e.g., LOG_LEVEL=DEBUG for
```
```
dev, LOG_LEVEL=INFO for prod) into the running containers via the IaC.
```
```
Bonus (Optional)
```
Tackling any of these not required but will score you extra points:
● Blue/Green or Canary Deployments using ALB or CodeDeploy
● Secrets Management using AWS Secrets Manager or SSM
● IaC Testing: Terratest, tfsec, or cdk-nag
```
● Preview Environments for feature branches (dynamic environments)
```
Evaluation Criteria
Your submission will be evaluated based on:
● Functionality
○ All required AWS resources are created and correctly tagged.
○ App builds and deploys to both environments via IaC and GitHub Actions.
○ Config differences between environments are respected.
○ Manual promotion to prod works as specified.
● IaC Quality
```
○ Code is modular, DRY and scalable (CDK Constructs / Terraform Modules).
```
```
○ Good naming, outputs (e.g., ALB DNS) and tagging.
```
○ IAM roles are scoped with least privilege.
● DevOps Best Practices
○ Clear CI/CD pipeline with reusable workflows and secure secrets handling
○ Effective management of environments
○ Clear update and cleanup process
○ Logs and error handling in pipeline/scripts
● Code & Docs
○ Clean, readable code and comments.
PHASETREE | MASKINVEJ 5. - 2860 SØBORG| CVR: 42239895| WWW.PHASETREE.AI PAGE 3 of 5
○ Easy-to-follow README.md with:
■ Architecture explanation
■ Setup and deployment instructions
■ Cleanup steps
■ Assumptions and limitations
Credentials & Tagging
● AWS Region: eu-central-1
● Access Key: AKIASEAZYWFHSRPWLLUT
● Secret Access Key: xbdvqBsWPT6MrSbXGAobtN+rp8jIGQcOi+vdtCQH
● Log group prefix: andreas-applogs
```
● Required Tags (on all AWS resources):
```
○ Creator: andreas
○ Project: iac-task
```
NOTE: You will be assigned IAM credentials limited to resources that you create and tag correctly
```
using the tags above. You may not be able to list existing AWS resources due to security
restrictions, but you should be able to create and manage your own resources.
Submission
Create a public GitHub repository containing:
● App source code
● Dockerfile
● CDK/Terraform IaC
● GitHub Actions workflows
● Local build/deploy scripts
● README.md with:
○ Summary of architecture and choices
○ Setup instructions
○ Step-by-step for build, deploy, access, cleanup
PHASETREE | MASKINVEJ 5. - 2860 SØBORG| CVR: 42239895| WWW.PHASETREE.AI PAGE 4 of 5
○ Any assumptions or dependencies
Please submit your solution by 10:00 AM CET on Friday, October 31st.
You will be asked to prepare a presentation and present your solution in an onsite or remote
interview with the team. Feel free to reach out if you have any questions about the requirements or
need clarification on expectations.
PHASETREE | MASKINVEJ 5. - 2860 SØBORG| CVR: 42239895| WWW.PHASETREE.AI PAGE 5 of 5
