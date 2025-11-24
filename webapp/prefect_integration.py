"""
Prefect Integration Example for Bioinformatics Pipeline Orchestration

This module demonstrates how to integrate the FastAPI job management service
with Prefect for production workflow orchestration in computational biology
environments.

Example Use Cases:
- GATK variant calling pipelines with quality control steps
- RNA-seq analysis workflows with DESeq2 differential expression
- Multi-sample batch processing with resource management
- Cross-lab ETL pipelines with LIMS integration

Installation:
    pip install prefect prefect-shell httpx

Usage:
    # Start Prefect server (optional, for UI)
    prefect server start

    # Run a workflow
    python -m webapp.prefect_integration
"""

import asyncio
from datetime import timedelta

import httpx
from prefect import flow, task
from prefect.tasks import task_input_hash

from .pipeline_models import PipelineName

# Configuration
API_BASE_URL = "http://localhost:8000"  # Change to your deployed URL


@task(
    retries=3,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
async def submit_pipeline_job(
    pipeline_name: str,
    parameters: dict,
    research_group: str | None = None,
) -> str:
    """
    Submit a pipeline job to the FastAPI orchestration service.

    Args:
        pipeline_name: Name of the pipeline to execute
        parameters: Pipeline-specific parameters
        research_group: Research group identifier for multi-tenant tracking

    Returns:
        Job ID for tracking
    """
    async with httpx.AsyncClient() as client:
        payload = {
            "pipeline_name": pipeline_name,
            "parameters": parameters,
        }
        if research_group:
            payload["research_group"] = research_group

        response = await client.post(
            f"{API_BASE_URL}/jobs",
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["job_id"]


@task(retries=5, retry_delay_seconds=60)
async def wait_for_job_completion(job_id: str, poll_interval: int = 30) -> dict:
    """
    Poll job status until completion or failure.

    Args:
        job_id: Job identifier to monitor
        poll_interval: Seconds between status checks

    Returns:
        Final job status dictionary
    """
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                f"{API_BASE_URL}/jobs/{job_id}",
                timeout=10.0,
            )
            response.raise_for_status()
            job_data = response.json()

            status = job_data["status"]
            if status in ["completed", "failed"]:
                return job_data

            await asyncio.sleep(poll_interval)


@task
async def validate_fastq_quality(sample_id: str, fastq_files: list[str]) -> bool:
    """
    Quality control check for FASTQ files before pipeline execution.

    Args:
        sample_id: Sample identifier
        fastq_files: list of FASTQ file paths

    Returns:
        True if quality checks pass
    """
    # Simulate quality validation logic
    # In production: run FastQC, check read counts, validate format
    print(f"✓ Validated FASTQ quality for {sample_id}: {len(fastq_files)} files")
    return True


@task
async def register_results_in_lims(
    job_id: str,
    sample_id: str,
    output_files: list[str],
    research_group: str,
) -> str:
    """
    Register pipeline results in Laboratory Information Management System.

    Args:
        job_id: Completed job identifier
        sample_id: Sample identifier
        output_files: list of output file paths
        research_group: Research group for access control

    Returns:
        LIMS record ID
    """
    # Simulate LIMS integration
    # In production: POST to Benchling, LabKey, or custom LIMS API
    lims_record_id = f"LIMS_{job_id}"
    print(f"✓ Registered {len(output_files)} files in LIMS: {lims_record_id}")
    return lims_record_id


@flow(name="GATK Variant Calling Pipeline", log_prints=True)
async def gatk_variant_calling_workflow(
    sample_id: str,
    fastq_r1: str,
    fastq_r2: str,
    reference_genome: str = "hg38",
    research_group: str = "genomics_lab",
) -> dict:
    """
    Complete GATK variant calling workflow with quality control and LIMS integration.

    Pipeline Steps:
    1. Validate FASTQ quality
    2. Submit alignment and variant calling job
    3. Wait for completion
    4. Register results in LIMS

    Args:
        sample_id: Sample identifier (e.g., "WGS_001")
        fastq_r1: Path to forward reads FASTQ
        fastq_r2: Path to reverse reads FASTQ
        reference_genome: Reference genome version
        research_group: Research group identifier

    Returns:
        Workflow result summary
    """
    print(f"🧬 Starting GATK variant calling for {sample_id}")

    # Step 1: Quality validation
    quality_ok = await validate_fastq_quality(sample_id, [fastq_r1, fastq_r2])
    if not quality_ok:
        raise ValueError(f"Quality validation failed for {sample_id}")

    # Step 2: Submit pipeline job
    job_id = await submit_pipeline_job(
        pipeline_name=PipelineName.GATK_VARIANT_CALLING,
        parameters={
            "sample_id": sample_id,
            "fastq_r1": fastq_r1,
            "fastq_r2": fastq_r2,
            "reference_genome": reference_genome,
            "caller": "HaplotypeCaller",
            "quality_threshold": 30,
            "depth_threshold": 10,
        },
        research_group=research_group,
    )
    print(f"✓ Submitted job: {job_id}")

    # Step 3: Wait for completion
    result = await wait_for_job_completion(job_id)
    print(f"✓ Job {result['status']}: {job_id}")

    if result["status"] == "failed":
        raise RuntimeError(f"Pipeline failed for {sample_id}")

    # Step 4: Register in LIMS
    output_files = [
        f"/data/{sample_id}.bam",
        f"/data/{sample_id}.vcf.gz",
        f"/data/{sample_id}.vcf.gz.tbi",
    ]
    lims_id = await register_results_in_lims(
        job_id, sample_id, output_files, research_group
    )

    return {
        "sample_id": sample_id,
        "job_id": job_id,
        "status": result["status"],
        "lims_record": lims_id,
        "output_files": output_files,
    }


@flow(name="Batch RNA-seq Analysis", log_prints=True)
async def batch_rnaseq_workflow(
    samples: list[dict[str, str]],
    reference_transcriptome: str = "gencode_v38",
    research_group: str = "transcriptomics_lab",
) -> list[dict]:
    """
    Process multiple RNA-seq samples with resource-aware scheduling.

    Args:
        samples: list of sample dictionaries with 'sample_id' and 'fastq' keys
        reference_transcriptome: Reference transcriptome version
        research_group: Research group identifier

    Returns:
        List of workflow results for each sample
    """
    print(f"🔬 Starting batch RNA-seq analysis for {len(samples)} samples")

    results = []
    for sample in samples:
        # Submit each sample as a separate job
        job_id = await submit_pipeline_job(
            pipeline_name=PipelineName.RNASEQ_DESEQ2,
            parameters={
                "sample_id": sample["sample_id"],
                "fastq_files": sample["fastq"],
                "reference": reference_transcriptome,
                "adapter_sequence": "AGATCGGAAGAGC",
                "min_quality": 20,
                "quantification_method": "salmon",
            },
            research_group=research_group,
        )
        results.append(
            {
                "sample_id": sample["sample_id"],
                "job_id": job_id,
            }
        )
        print(f"✓ Submitted {sample['sample_id']}: {job_id}")

    # Wait for all jobs to complete
    for result in results:
        job_data = await wait_for_job_completion(result["job_id"])
        result["status"] = job_data["status"]
        print(f"✓ Completed {result['sample_id']}: {result['status']}")

    return results


@flow(name="Cross-Lab ETL Pipeline", log_prints=True)
async def cross_lab_etl_workflow(
    source_research_group: str,
    target_research_group: str,
    data_types: list[str],
) -> dict:
    """
    ETL workflow for transferring and transforming data between research groups.

    Args:
        source_research_group: Source research group identifier
        target_research_group: Target research group identifier
        data_types: list of data types to transfer (e.g., ["vcf", "bam", "metadata"])

    Returns:
        ETL workflow summary
    """
    print(f"🔄 Starting ETL: {source_research_group} → {target_research_group}")

    # Submit ETL job
    job_id = await submit_pipeline_job(
        pipeline_name="cross_lab_etl",
        parameters={
            "source_group": source_research_group,
            "target_group": target_research_group,
            "data_types": data_types,
            "validation_level": "strict",
            "anonymize": True,
        },
        research_group="data_integration_team",
    )
    print(f"✓ Submitted ETL job: {job_id}")

    # Monitor completion
    result = await wait_for_job_completion(job_id, poll_interval=60)

    return {
        "job_id": job_id,
        "status": result["status"],
        "source": source_research_group,
        "target": target_research_group,
        "data_types": data_types,
    }


# Example usage
if __name__ == "__main__":
    # Example 1: Single sample variant calling
    print("=" * 60)
    print("Example 1: GATK Variant Calling")
    print("=" * 60)

    result1 = asyncio.run(
        gatk_variant_calling_workflow(
            sample_id="WGS_001",
            fastq_r1="/data/WGS_001_R1.fastq.gz",
            fastq_r2="/data/WGS_001_R2.fastq.gz",
            reference_genome="hg38",
            research_group="genomics_lab",
        )
    )
    print(f"\n✅ Result: {result1}\n")

    # Example 2: Batch RNA-seq processing
    print("=" * 60)
    print("Example 2: Batch RNA-seq Analysis")
    print("=" * 60)

    samples = [
        {"sample_id": "RNA_001", "fastq": ["/data/RNA_001.fastq.gz"]},
        {"sample_id": "RNA_002", "fastq": ["/data/RNA_002.fastq.gz"]},
        {"sample_id": "RNA_003", "fastq": ["/data/RNA_003.fastq.gz"]},
    ]

    result2 = asyncio.run(
        batch_rnaseq_workflow(  # type: ignore
            samples=samples,
            reference_transcriptome="gencode_v38",
            research_group="transcriptomics_lab",
        )
    )
    print(f"\n✅ Processed {len(result2)} samples\n")

    # Example 3: Cross-lab data integration
    print("=" * 60)
    print("Example 3: Cross-Lab ETL")
    print("=" * 60)

    result3 = asyncio.run(
        cross_lab_etl_workflow(
            source_research_group="genomics_lab",
            target_research_group="clinical_research",
            data_types=["vcf", "phenotype_data"],
        )
    )
    print(f"\n✅ Result: {result3}\n")
