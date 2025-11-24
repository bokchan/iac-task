# Make a service to run pipelines

## Main components

A high level description of the architecture

## webapp:

- Rest API for submitting to submit jobs for snakemake
  - submit job
  - retrieve status for job
  - retrieve list of running jobs
- backend service to orchestrate the processing pipeline via snakemake
  - store submitted jobs in the database


Allow the pipeline to be mocked as the scope is a PoC

## infrastructure

IaC to deploy the necessary infrastructure to AWS

## Implementation Plan

### Phase 1: Foundation Setup
1. **Database Design**
   - Design schema for job submissions (id, status, created_at, updated_at, parameters)
   - Choose database (RDS PostgreSQL vs DynamoDB)
   - Add database stack to CDK infrastructure

2. **REST API Implementation**
   - Extend FastAPI application with job endpoints:
     - `POST /jobs` - Submit new pipeline job
     - `GET /jobs/{job_id}` - Get job status
     - `GET /jobs` - List all jobs (with pagination)
   - Add request/response models with Pydantic
   - Implement basic validation

3. **Mock Pipeline Service**
   - Create mock Snakemake pipeline that simulates processing
   - Configurable mock execution time (for testing)
   - Random success/failure outcomes for realistic behavior

### Phase 2: Backend Orchestration
1. **Job Queue System**
   - Implement job queue (SQS or in-memory for PoC)
   - Background worker to process jobs from queue
   - Update job status in database (pending → running → completed/failed)

2. **Pipeline Orchestration**
   - Service layer to handle Snakemake workflow execution
   - Job status tracking and updates
   - Error handling and logging
   - Integration with mock pipeline

3. **Database Integration**
   - SQLAlchemy models and database connection
   - CRUD operations for jobs
   - Database migrations setup (Alembic)

### Phase 3: Infrastructure Enhancement
1. **Database Stack (CDK)**
   - Add RDS PostgreSQL or DynamoDB to infrastructure
   - Configure security groups and access policies
   - Environment-specific database instances
   - Backup and retention policies

2. **Queue Infrastructure**
   - Add SQS queue to CDK stacks
   - Configure dead letter queue for failed jobs
   - IAM permissions for ECS tasks to access SQS

3. **Background Worker Service**
   - Separate ECS task definition for worker
   - Auto-scaling based on queue depth
   - Separate from API service for scalability

### Phase 4: Testing & Observability
1. **Testing**
   - Unit tests for API endpoints
   - Integration tests with mock database
   - End-to-end tests for job submission flow
   - Load testing for concurrent job submissions

2. **Monitoring & Logging**
   - CloudWatch metrics for job processing
   - Custom metrics: jobs submitted, processing time, success/failure rates
   - Structured logging for job lifecycle events
   - CloudWatch alarms for failures

3. **Documentation**
   - API documentation (OpenAPI/Swagger)
   - Architecture diagrams for new components
   - Deployment guide updates
   - Developer setup instructions

### Phase 5: Production Readiness
1. **Security**
   - API authentication (API keys or JWT)
   - Rate limiting for job submissions
   - Input validation and sanitization
   - Secrets management for database credentials

2. **Scalability**
   - Horizontal scaling for API and workers
   - Connection pooling for database
   - Caching strategy for job status queries
   - Pagination for job listings

3. **Operational Features**
   - Job cancellation endpoint
   - Job retry mechanism
   - Health checks including database connectivity
   - Graceful shutdown for workers

### Technical Decisions to Make
- **Database**: RDS PostgreSQL (relational, ACID) vs DynamoDB (NoSQL, serverless)
- **Queue**: SQS (managed) vs Redis (in-memory, faster) vs Celery
- **Worker Pattern**: ECS tasks vs Lambda functions vs separate container
- **Snakemake Integration**: Containerized vs local execution
- **State Management**: Database-only vs database + cache (Redis)

### Estimated Effort
- Phase 1: 2-3 days
- Phase 2: 3-4 days
- Phase 3: 2-3 days
- Phase 4: 2-3 days
- Phase 5: 2-3 days

**Total: ~2 weeks for full implementation**

### MVP Scope (1 week)
Focus on Phases 1-2 with simplified infrastructure:
- FastAPI with in-memory job storage
- Mock pipeline execution
- Basic API endpoints
- Simple background processing (threading)
- Manual deployment to existing ECS infrastructure

