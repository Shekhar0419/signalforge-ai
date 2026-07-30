from typing import Any

import numpy as np
import pandas as pd

from app.core.config import Settings
from app.models.schemas import ColumnProfile, DatasetProfile, QualityIssue
from app.services.anomaly import iqr_outlier_mask
from app.services.scoring import calculate_reliability_score


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _numeric_statistics(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
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
    row_count = len(dataframe)
    duplicate_rows = int(dataframe.duplicated().sum())
    issues: list[QualityIssue] = []
    profiles: list[ColumnProfile] = []

    if row_count == 0:
        issues.append(
            QualityIssue(
                severity="critical",
                code="EMPTY_DATASET",
                message="The uploaded dataset does not contain any records.",
            )
        )

    for column_name in dataframe.columns:
        series = dataframe[column_name]
        missing_count = int(series.isna().sum())
        missing_ratio = missing_count / row_count if row_count else 0.0
        unique_count = int(series.nunique(dropna=True))
        unique_ratio = unique_count / row_count if row_count else 0.0
        inferred_type = str(series.dtype)

        numeric = pd.api.types.is_numeric_dtype(series)
        statistics = _numeric_statistics(series) if numeric else {}
        top_values = {
            str(key): int(value)
            for key, value in series.astype("string").value_counts(dropna=True).head(5).items()
        }

        outlier_count = 0
        outlier_ratio = 0.0
        if numeric and row_count:
            mask = iqr_outlier_mask(series)
            outlier_count = int(mask.fillna(False).sum())
            outlier_ratio = outlier_count / row_count

        profile = ColumnProfile(
            name=str(column_name),
            inferred_type=inferred_type,
            non_null_count=int(series.notna().sum()),
            missing_count=missing_count,
            missing_ratio=round(missing_ratio, 4),
            unique_count=unique_count,
            unique_ratio=round(unique_ratio, 4),
            statistics=statistics,
            top_values=top_values,
            outlier_count=outlier_count,
            outlier_ratio=round(outlier_ratio, 4),
        )
        profiles.append(profile)

        if missing_ratio >= settings.missing_warning_threshold:
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="HIGH_MISSING_RATIO",
                    column=str(column_name),
                    message=(
                        f"Column '{column_name}' has {missing_ratio:.1%} missing values."
                    ),
                )
            )

        if unique_count <= 1 and row_count:
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="CONSTANT_COLUMN",
                    column=str(column_name),
                    message=f"Column '{column_name}' has one or fewer distinct values.",
                )
            )

        if outlier_ratio >= settings.outlier_warning_threshold:
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="HIGH_OUTLIER_RATIO",
                    column=str(column_name),
                    message=(
                        f"Column '{column_name}' has {outlier_ratio:.1%} IQR outliers."
                    ),
                )
            )

    if duplicate_rows:
        issues.append(
            QualityIssue(
                severity="warning",
                code="DUPLICATE_ROWS",
                message=f"The dataset contains {duplicate_rows} duplicate rows.",
            )
        )

    score = calculate_reliability_score(row_count, duplicate_rows, profiles)

    return DatasetProfile(
        filename=filename,
        row_count=row_count,
        column_count=len(dataframe.columns),
        duplicate_rows=duplicate_rows,
        reliability_score=score,
        columns=profiles,
        issues=issues,
    )
