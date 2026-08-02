from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QualityIssue(BaseModel):
    severity: str
    code: str
    message: str
    column: str | None = None


class ColumnProfile(BaseModel):
    name: str
    inferred_type: str
    non_null_count: int
    missing_count: int
    missing_ratio: float
    unique_count: int
    unique_ratio: float

    statistics: dict[str, Any] = Field(
        default_factory=dict,
    )

    top_values: dict[str, int] = Field(
        default_factory=dict,
    )

    outlier_count: int = 0
    outlier_ratio: float = 0.0


class DatasetProfile(BaseModel):
    filename: str
    row_count: int
    column_count: int
    duplicate_rows: int
    reliability_score: float

    columns: list[ColumnProfile]
    issues: list[QualityIssue]

    column_metadata: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    business_rules: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )

    ml_anomalies: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    preview_columns: list[str] = Field(
        default_factory=list,
    )

    preview_rows: list[dict[str, Any]] = Field(
        default_factory=list,
    )


class DatasetProfileResponse(DatasetProfile):
    dataset_id: str
    created_at: datetime

    parent_dataset_id: str | None = None
    version_number: int = 1
    version_type: str = "ORIGINAL"


class DatasetSummary(BaseModel):
    id: str
    filename: str
    row_count: int
    column_count: int
    reliability_score: float
    created_at: datetime

    parent_dataset_id: str | None = None
    version_number: int = 1
    version_type: str = "ORIGINAL"