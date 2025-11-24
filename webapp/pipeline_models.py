"""
Pydantic models for pipeline-specific parameters.

These models provide strong typing, automatic validation, and API documentation
for each bioinformatics pipeline supported by the orchestration service.
"""

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReferenceGenome(str, Enum):
    """Valid reference genome versions."""

    HG19 = "hg19"
    HG38 = "hg38"
    GRCH37 = "GRCh37"
    GRCH38 = "GRCh38"


class MouseReferenceGenome(str, Enum):
    """Valid mouse reference genome versions."""

    HG38 = "hg38"  # Also used for some human ChIP-seq
    MM10 = "mm10"
    MM39 = "mm39"


class ReferenceTranscriptome(str, Enum):
    """Valid reference transcriptome versions."""

    GENCODE_V38 = "gencode_v38"
    GENCODE_V44 = "gencode_v44"
    ENSEMBL_110 = "ensembl_110"


class VariantCaller(str, Enum):
    """GATK variant calling methods."""

    HAPLOTYPE_CALLER = "HaplotypeCaller"
    MUTECT2 = "Mutect2"
    UNIFIED_GENOTYPER = "UnifiedGenotyper"


class QuantificationMethod(str, Enum):
    """RNA-seq quantification methods."""

    SALMON = "salmon"
    KALLISTO = "kallisto"
    RSEM = "rsem"
    FEATURECOUNTS = "featureCounts"


class PeakType(str, Enum):
    """ChIP-seq peak types."""

    NARROW = "narrow"
    BROAD = "broad"
    VERY_BROAD = "very-broad"


class ValidationLevel(str, Enum):
    """ETL data validation levels."""

    STRICT = "strict"
    MODERATE = "moderate"
    PERMISSIVE = "permissive"


class GATKVariantCallingParams(BaseModel):
    """Parameters for GATK variant calling pipeline."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sample_id": "WGS_001",
            "reference_genome": "hg38",
            "fastq_r1": "/data/samples/WGS_001_R1.fastq.gz",
            "fastq_r2": "/data/samples/WGS_001_R2.fastq.gz",
            "variant_caller": "HaplotypeCaller",
            "quality_threshold": 30,
            "read_filters": ["MappingQualityReadFilter", "GoodCigarReadFilter"],
        }
    })

    sample_id: str = Field(..., description="Sample identifier", examples=["WGS_001"])
    reference_genome: ReferenceGenome = Field(
        ..., description="Reference genome version", examples=["hg38"]
    )
    fastq_r1: Optional[str] = Field(
        None,
        description="Path to forward reads FASTQ file",
        examples=["s3://data/WGS_001_R1.fastq.gz"],
    )
    fastq_r2: Optional[str] = Field(
        None,
        description="Path to reverse reads FASTQ file",
        examples=["s3://data/WGS_001_R2.fastq.gz"],
    )
    bam_file: Optional[str] = Field(
        None,
        description="Path to aligned BAM file (alternative to FASTQ)",
        examples=["s3://data/WGS_001.bam"],
    )
    caller: Optional[VariantCaller] = Field(
        VariantCaller.HAPLOTYPE_CALLER,
        description="Variant calling algorithm",
    )
    quality_threshold: Optional[int] = Field(
        30, ge=0, le=60, description="Minimum base quality score"
    )
    depth_threshold: Optional[int] = Field(
        10, ge=1, description="Minimum read depth for variant calling"
    )

    @field_validator("fastq_r1", "fastq_r2", "bam_file")
    @classmethod
    def validate_file_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_prefixes = ["s3://", "/data/", "/mnt/", "gs://", "https://"]
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"File path must start with one of: {', '.join(valid_prefixes)}"
            )
        return v

    @field_validator("reference_genome")
    @classmethod
    def normalize_reference(cls, v: ReferenceGenome) -> ReferenceGenome:
        """Normalize reference genome naming."""
        if v in [ReferenceGenome.GRCH38, ReferenceGenome.HG38]:
            return ReferenceGenome.HG38
        elif v in [ReferenceGenome.GRCH37, ReferenceGenome.HG19]:
            return ReferenceGenome.HG19
        return v


class RNASeqDESeq2Params(BaseModel):
    """Parameters for RNA-seq differential expression analysis."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sample_id": "RNA_001",
            "reference": "gencode_v38",
            "fastq_files": ["s3://data/RNA_001.fastq.gz"],
            "adapter_sequence": "AGATCGGAAGAGC",
            "min_quality": 20,
            "quantification_method": "salmon",
        }
    })

    sample_id: str = Field(..., description="Sample identifier", examples=["RNA_001"])
    reference: ReferenceTranscriptome = Field(
        ..., description="Reference transcriptome version", examples=["gencode_v38"]
    )
    fastq_files: Optional[List[str]] = Field(
        None,
        description="List of FASTQ file paths",
        examples=[["s3://data/RNA_001.fastq.gz"]],
    )
    adapter_sequence: Optional[str] = Field(
        None,
        description="Adapter sequence for trimming",
        examples=["AGATCGGAAGAGC"],
    )
    min_quality: Optional[int] = Field(
        20, ge=0, le=40, description="Minimum base quality score"
    )
    quantification_method: Optional[QuantificationMethod] = Field(
        QuantificationMethod.SALMON, description="Quantification tool"
    )

    @field_validator("fastq_files")
    @classmethod
    def validate_fastq_paths(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        valid_prefixes = ["s3://", "/data/", "/mnt/", "gs://", "https://"]
        for path in v:
            if not any(path.startswith(prefix) for prefix in valid_prefixes):
                raise ValueError(
                    f"File path must start with one of: {', '.join(valid_prefixes)}"
                )
        return v


class CrossLabETLParams(BaseModel):
    """Parameters for cross-laboratory data integration."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "source_group": "genomics_lab",
            "target_group": "clinical_research",
            "data_types": ["vcf", "phenotype_data"],
            "validation_level": "strict",
            "anonymize": True,
        }
    })

    source_group: str = Field(
        ..., description="Source research group", examples=["genomics_lab"]
    )
    target_group: str = Field(
        ..., description="Target research group", examples=["clinical_research"]
    )
    data_types: List[str] = Field(
        ...,
        description="Types of data to transfer",
        examples=[["vcf", "bam", "phenotype_data"]],
    )
    validation_level: Optional[ValidationLevel] = Field(
        ValidationLevel.STRICT, description="Data validation strictness"
    )
    anonymize: Optional[bool] = Field(
        False, description="Whether to anonymize patient data"
    )


class ChIPSeqMACS2Params(BaseModel):
    """Parameters for ChIP-seq peak calling with MACS2."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sample_id": "ChIP_001",
            "reference_genome": "hg38",
            "antibody": "H3K27ac",
            "input_control": "s3://data/input.bam",
            "peak_type": "narrow",
            "fdr_threshold": 0.05,
        }
    })

    sample_id: str = Field(
        ..., description="Sample identifier", examples=["ChIP_001"]
    )
    reference_genome: MouseReferenceGenome = Field(
        ..., description="Reference genome version", examples=["hg38"]
    )
    antibody: str = Field(
        ..., description="Antibody target", examples=["H3K27ac", "H3K4me3"]
    )
    input_control: Optional[str] = Field(
        None,
        description="Path to input control BAM file",
        examples=["s3://data/input_control.bam"],
    )
    peak_type: Optional[PeakType] = Field(
        PeakType.NARROW, description="Peak calling mode"
    )
    fdr_threshold: Optional[float] = Field(
        0.05, ge=0.0, le=1.0, description="False discovery rate threshold"
    )

    @field_validator("input_control")
    @classmethod
    def validate_file_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_prefixes = ["s3://", "/data/", "/mnt/", "gs://", "https://"]
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"File path must start with one of: {', '.join(valid_prefixes)}"
            )
        return v


# Pipeline registry mapping pipeline names to their parameter models
PIPELINE_MODELS = {
    "gatk_variant_calling": GATKVariantCallingParams,
    "rnaseq_deseq2": RNASeqDESeq2Params,
    "cross_lab_etl": CrossLabETLParams,
    "chip_seq_macs2": ChIPSeqMACS2Params,
}
