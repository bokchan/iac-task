"""
Orchestration Layer - Abstraction over Prefect/Dagster/etc.

This module demonstrates how FastAPI abstracts the underlying orchestration engine,
allowing you to swap Prefect for another system without changing the REST API.
"""

import logging
from typing import Dict, Optional
from uuid import UUID


logger = logging.getLogger(__name__)


# Configuration - could be environment variable
ORCHESTRATOR_BACKEND = "mock"  # Options: "mock", "prefect", "dagster", "airflow"


async def submit_to_orchestrator(
    job_id: UUID,
    pipeline_name: str,
    parameters: Dict,
    research_group: Optional[str] = None,
) -> str:
    """
    Submit job to the configured orchestration backend.

    This abstraction allows switching between different orchestrators
    without changing the FastAPI endpoints.

    Args:
        job_id: Job identifier
        pipeline_name: Pipeline to execute
        parameters: Pipeline parameters
        research_group: Research group identifier

    Returns:
        Orchestrator-specific run ID
    """
    if ORCHESTRATOR_BACKEND == "prefect":
        return await submit_to_prefect(
            job_id, pipeline_name, parameters, research_group
        )
    elif ORCHESTRATOR_BACKEND == "dagster":
        return await submit_to_dagster(
            job_id, pipeline_name, parameters, research_group
        )
    elif ORCHESTRATOR_BACKEND == "airflow":
        return await submit_to_airflow(
            job_id, pipeline_name, parameters, research_group
        )
    else:
        # Mock backend for demonstration
        return await submit_to_mock_orchestrator(job_id, pipeline_name, parameters)


async def submit_to_prefect(
    job_id: UUID,
    pipeline_name: str,
    parameters: Dict,
    research_group: Optional[str],
) -> str:
    """
    Submit job to Prefect via REST API.

    In production, this would:
    1. Call Prefect's /deployments/{id}/create_flow_run endpoint
    2. Map pipeline_name to Prefect deployment ID
    3. Pass job_id and parameters to the flow
    4. Return Prefect's flow_run_id
    """
    logger.info(f"[Prefect] Submitting job {job_id} for pipeline {pipeline_name}")

    # Simulated Prefect API call
    # In production:
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         f"{PREFECT_API_URL}/deployments/{deployment_id}/create_flow_run",
    #         json={
    #             "parameters": {
    #                 "job_id": str(job_id),
    #                 "pipeline_name": pipeline_name,
    #                 "parameters": parameters,
    #                 "research_group": research_group,
    #             }
    #         }
    #     )
    #     return response.json()["id"]

    prefect_run_id = f"prefect-{job_id}"
    logger.info(f"[Prefect] Created flow run: {prefect_run_id}")
    return prefect_run_id


async def submit_to_dagster(
    job_id: UUID,
    pipeline_name: str,
    parameters: Dict,
    research_group: Optional[str],
) -> str:
    """
    Submit job to Dagster via GraphQL API.

    In production, this would:
    1. Call Dagster's GraphQL endpoint
    2. Execute launchRun mutation
    3. Map pipeline_name to Dagster job
    4. Return Dagster's run_id
    """
    logger.info(f"[Dagster] Submitting job {job_id} for pipeline {pipeline_name}")

    # Simulated Dagster API call
    dagster_run_id = f"dagster-{job_id}"
    logger.info(f"[Dagster] Created run: {dagster_run_id}")
    return dagster_run_id


async def submit_to_airflow(
    job_id: UUID,
    pipeline_name: str,
    parameters: Dict,
    research_group: Optional[str],
) -> str:
    """
    Submit job to Airflow via REST API.

    In production, this would:
    1. Call Airflow's /dags/{dag_id}/dagRuns endpoint
    2. Map pipeline_name to Airflow DAG
    3. Pass configuration in conf parameter
    4. Return Airflow's dag_run_id
    """
    logger.info(f"[Airflow] Submitting job {job_id} for pipeline {pipeline_name}")

    # Simulated Airflow API call
    airflow_run_id = f"airflow-{job_id}"
    logger.info(f"[Airflow] Created DAG run: {airflow_run_id}")
    return airflow_run_id


async def submit_to_mock_orchestrator(
    job_id: UUID,
    pipeline_name: str,
    parameters: Dict,
) -> str:
    """
    Mock orchestrator for demonstration purposes.

    This is what currently runs - the mock pipeline execution.
    """
    from webapp.pipeline import execute_mock_pipeline
    import asyncio

    logger.info(f"[Mock] Submitting job {job_id} for pipeline {pipeline_name}")

    # Start mock execution in background
    asyncio.create_task(execute_mock_pipeline(job_id, pipeline_name, parameters))

    return f"mock-{job_id}"


async def cancel_job_in_orchestrator(job_id: UUID, orchestrator_run_id: str) -> bool:
    """
    Cancel a running job in the orchestrator.

    Args:
        job_id: Job identifier
        orchestrator_run_id: Orchestrator-specific run ID

    Returns:
        True if cancellation successful
    """
    if ORCHESTRATOR_BACKEND == "prefect":
        logger.info(f"[Prefect] Cancelling flow run {orchestrator_run_id}")
        # In production: call Prefect's cancel endpoint
        return True
    elif ORCHESTRATOR_BACKEND == "dagster":
        logger.info(f"[Dagster] Terminating run {orchestrator_run_id}")
        # In production: call Dagster's terminate mutation
        return True
    else:
        logger.info("[Mock] Cancellation not implemented for mock orchestrator")
        return False


def get_orchestrator_status() -> Dict:
    """
    Get status information about the orchestration backend.

    Returns:
        Status information including backend type, health, etc.
    """
    return {
        "backend": ORCHESTRATOR_BACKEND,
        "status": "healthy",
        "supported_pipelines": [
            "gatk_variant_calling",
            "rnaseq_deseq2",
            "cross_lab_etl",
            "chip_seq_macs2",
        ],
    }
