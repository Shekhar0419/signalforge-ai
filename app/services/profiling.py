from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from app.core.config import Settings
from app.models.schemas import (
    ColumnProfile,
    DatasetProfile,
    QualityIssue,
)
from app.services.anomaly import iqr_outlier_mask
from app.services.business_rules import evaluate_business_rules
from app.services.column_metadata import build_column_metadata
from app.services.ml_anomaly import detect_ml_anomalies
from app.services.recommendations import generate_recommendations
from app.services.scoring import calculate_reliability_score


def _json_safe(value: Any) -> Any:
    """
    Convert NumPy and pandas scalar values into JSON-safe Python values.
    """
    if pd.isna(value):
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def _numeric_statistics(
    series: pd.Series,
) -> dict[str, Any]:
    """
    Calculate descriptive statistics for a numeric, non-boolean Series.
    """
    if is_bool_dtype(series):
        return {}

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric.empty:
        return {}

    return {
        "mean": _json_safe(numeric.mean()),
        "median": _json_safe(numeric.median()),
        "std": _json_safe(numeric.std()),
        "min": _json_safe(numeric.min()),
        "max": _json_safe(numeric.max()),
        "q25": _json_safe(numeric.quantile(0.25)),
        "q75": _json_safe(numeric.quantile(0.75)),
    }


def profile_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
    settings: Settings,
) -> DatasetProfile:
    """
    Build a complete quality and anomaly profile for an uploaded dataframe.
    """
    row_count = len(dataframe)
    duplicate_rows = int(dataframe.duplicated().sum())

    issues: list[QualityIssue] = []
    profiles: list[ColumnProfile] = []

    if row_count == 0:
        issues.append(
            QualityIssue(
                severity="critical",
                code="EMPTY_DATASET",
                message=(
                    "The uploaded dataset does not contain any records."
                ),
            )
        )

    for column_name in dataframe.columns:
        series = dataframe[column_name]

        missing_count = int(series.isna().sum())
        missing_ratio = (
            missing_count / row_count
            if row_count
            else 0.0
        )

        unique_count = int(
            series.nunique(dropna=True)
        )
        unique_ratio = (
            unique_count / row_count
            if row_count
            else 0.0
        )

        inferred_type = str(series.dtype)

        is_numeric = (
            is_numeric_dtype(series)
            and not is_bool_dtype(series)
        )

        statistics = (
            _numeric_statistics(series)
            if is_numeric
            else {}
        )

        top_values = {
            str(key): int(value)
            for key, value in (
                series.astype("string")
                .value_counts(dropna=True)
                .head(5)
                .items()
            )
        }

        outlier_count = 0
        outlier_ratio = 0.0

        if is_numeric and row_count:
            outlier_mask = iqr_outlier_mask(series)

            outlier_count = int(
                outlier_mask.fillna(False).sum()
            )

            outlier_ratio = (
                outlier_count / row_count
            )

        profile = ColumnProfile(
            name=str(column_name),
            inferred_type=inferred_type,
            non_null_count=int(
                series.notna().sum()
            ),
            missing_count=missing_count,
            missing_ratio=round(
                missing_ratio,
                4,
            ),
            unique_count=unique_count,
            unique_ratio=round(
                unique_ratio,
                4,
            ),
            statistics=statistics,
            top_values=top_values,
            outlier_count=outlier_count,
            outlier_ratio=round(
                outlier_ratio,
                4,
            ),
        )

        profiles.append(profile)

        if (
            missing_ratio
            >= settings.missing_warning_threshold
        ):
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="HIGH_MISSING_RATIO",
                    column=str(column_name),
                    message=(
                        f"Column '{column_name}' has "
                        f"{missing_ratio:.1%} missing values."
                    ),
                )
            )

        if unique_count <= 1 and row_count:
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="CONSTANT_COLUMN",
                    column=str(column_name),
                    message=(
                        f"Column '{column_name}' has one "
                        "or fewer distinct values."
                    ),
                )
            )

        if (
            outlier_ratio
            >= settings.outlier_warning_threshold
        ):
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="HIGH_OUTLIER_RATIO",
                    column=str(column_name),
                    message=(
                        f"Column '{column_name}' has "
                        f"{outlier_ratio:.1%} IQR outliers."
                    ),
                )
            )

    if duplicate_rows:
        issues.append(
            QualityIssue(
                severity="warning",
                code="DUPLICATE_ROWS",
                message=(
                    "The dataset contains "
                    f"{duplicate_rows} duplicate rows."
                ),
            )
        )

    reliability_score = calculate_reliability_score(
        row_count,
        duplicate_rows,
        profiles,
    )

    column_metadata = build_column_metadata(
        dataframe
    )

    business_rules = evaluate_business_rules(
        dataframe
    )

    recommendations = generate_recommendations(
        column_metadata=column_metadata,
        business_rules=business_rules,
    )

    ml_anomalies = detect_ml_anomalies(
        dataframe
    )

    return DatasetProfile(
        filename=filename,
        row_count=row_count,
        column_count=len(dataframe.columns),
        duplicate_rows=duplicate_rows,
        reliability_score=reliability_score,
        columns=profiles,
        issues=issues,
        column_metadata=column_metadata,
        business_rules=business_rules,
        recommendations=recommendations,
        ml_anomalies=ml_anomalies,
    )