from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.db.models import Dataset
from app.models.schemas import DatasetProfile


class VersionComparisonError(RuntimeError):
    """Raised when two dataset versions cannot be compared."""


@dataclass(frozen=True)
class MetricComparison:
    before: int | float
    after: int | float
    difference: int | float
    percent_change: float | None
    improved: bool | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "before": self.before,
            "after": self.after,
            "difference": self.difference,
            "percent_change": self.percent_change,
            "improved": self.improved,
        }


def _load_profile(
    dataset: Dataset,
) -> DatasetProfile:
    if dataset.analysis is None:
        raise VersionComparisonError(
            "The selected dataset does not have an analysis."
        )

    try:
        return DatasetProfile.model_validate(
            dataset.analysis.profile_json,
        )
    except Exception as exc:
        raise VersionComparisonError(
            "The stored dataset profile could not be loaded."
        ) from exc


def _get_root_dataset_id(
    dataset: Dataset,
) -> str:
    return (
        dataset.parent_dataset_id
        or dataset.id
    )


def _validate_same_lineage(
    first_dataset: Dataset,
    second_dataset: Dataset,
) -> None:
    first_root_id = _get_root_dataset_id(
        first_dataset,
    )

    second_root_id = _get_root_dataset_id(
        second_dataset,
    )

    if first_root_id != second_root_id:
        raise VersionComparisonError(
            "Only versions from the same dataset lineage can be compared."
        )


def _calculate_percent_change(
    before: int | float,
    after: int | float,
) -> float | None:
    if before == 0:
        if after == 0:
            return 0.0

        return None

    return round(
        ((after - before) / abs(before)) * 100,
        2,
    )


def _build_metric_comparison(
    before: int | float,
    after: int | float,
    *,
    higher_is_better: bool | None,
) -> MetricComparison:
    difference = after - before

    improved: bool | None

    if higher_is_better is None:
        improved = None
    elif difference == 0:
        improved = None
    elif higher_is_better:
        improved = difference > 0
    else:
        improved = difference < 0

    return MetricComparison(
        before=before,
        after=after,
        difference=difference,
        percent_change=_calculate_percent_change(
            before=before,
            after=after,
        ),
        improved=improved,
    )


def _count_missing_values(
    profile: DatasetProfile,
) -> int:
    return sum(
        column.missing_count
        for column in profile.columns
    )


def _count_outliers(
    profile: DatasetProfile,
) -> int:
    return sum(
        column.outlier_count
        for column in profile.columns
    )


def _count_rule_violations(
    profile: DatasetProfile,
) -> int:
    total = 0

    for rule in profile.business_rules:
        violation_count = rule.get(
            "violation_count",
            rule.get(
                "violations",
                0,
            ),
        )

        if isinstance(
            violation_count,
            bool,
        ):
            continue

        if isinstance(
            violation_count,
            int | float,
        ):
            total += int(
                violation_count,
            )

    return total


def _count_ml_anomalies(
    profile: DatasetProfile,
) -> int:
    return len(
        profile.ml_anomalies,
    )


def _build_summary(
    comparisons: dict[str, MetricComparison],
) -> list[str]:
    summary: list[str] = []

    duplicate_difference = comparisons[
        "duplicate_rows"
    ].difference

    if duplicate_difference < 0:
        summary.append(
            f"Removed {abs(int(duplicate_difference))} duplicate row"
            f"{'' if abs(int(duplicate_difference)) == 1 else 's'}."
        )

    missing_difference = comparisons[
        "missing_values"
    ].difference

    if missing_difference < 0:
        summary.append(
            f"Resolved {abs(int(missing_difference))} missing value"
            f"{'' if abs(int(missing_difference)) == 1 else 's'}."
        )

    score_difference = comparisons[
        "reliability_score"
    ].difference

    if score_difference > 0:
        summary.append(
            "Reliability improved by "
            f"{score_difference:.2f} points."
        )
    elif score_difference < 0:
        summary.append(
            "Reliability decreased by "
            f"{abs(score_difference):.2f} points."
        )
    else:
        summary.append(
            "Reliability remained unchanged."
        )

    outlier_difference = comparisons[
        "outliers"
    ].difference

    if outlier_difference < 0:
        summary.append(
            f"Reduced statistical outliers by "
            f"{abs(int(outlier_difference))}."
        )

    rule_difference = comparisons[
        "business_rule_violations"
    ].difference

    if rule_difference < 0:
        summary.append(
            f"Reduced business-rule violations by "
            f"{abs(int(rule_difference))}."
        )

    anomaly_difference = comparisons[
        "ml_anomalies"
    ].difference

    if anomaly_difference < 0:
        summary.append(
            f"Reduced ML anomaly findings by "
            f"{abs(int(anomaly_difference))}."
        )

    if len(summary) == 1:
        summary.append(
            "No major structural changes were detected between these versions."
        )

    return summary


def compare_dataset_versions(
    first_dataset: Dataset,
    second_dataset: Dataset,
) -> dict[str, Any]:
    _validate_same_lineage(
        first_dataset=first_dataset,
        second_dataset=second_dataset,
    )

    first_profile = _load_profile(
        first_dataset,
    )

    second_profile = _load_profile(
        second_dataset,
    )

    comparisons = {
        "reliability_score": _build_metric_comparison(
            before=first_profile.reliability_score,
            after=second_profile.reliability_score,
            higher_is_better=True,
        ),
        "row_count": _build_metric_comparison(
            before=first_profile.row_count,
            after=second_profile.row_count,
            higher_is_better=None,
        ),
        "column_count": _build_metric_comparison(
            before=first_profile.column_count,
            after=second_profile.column_count,
            higher_is_better=None,
        ),
        "missing_values": _build_metric_comparison(
            before=_count_missing_values(
                first_profile,
            ),
            after=_count_missing_values(
                second_profile,
            ),
            higher_is_better=False,
        ),
        "duplicate_rows": _build_metric_comparison(
            before=first_profile.duplicate_rows,
            after=second_profile.duplicate_rows,
            higher_is_better=False,
        ),
        "outliers": _build_metric_comparison(
            before=_count_outliers(
                first_profile,
            ),
            after=_count_outliers(
                second_profile,
            ),
            higher_is_better=False,
        ),
        "business_rule_violations": _build_metric_comparison(
            before=_count_rule_violations(
                first_profile,
            ),
            after=_count_rule_violations(
                second_profile,
            ),
            higher_is_better=False,
        ),
        "ml_anomalies": _build_metric_comparison(
            before=_count_ml_anomalies(
                first_profile,
            ),
            after=_count_ml_anomalies(
                second_profile,
            ),
            higher_is_better=False,
        ),
    }

    return {
        "root_dataset_id": _get_root_dataset_id(
            first_dataset,
        ),
        "before": {
            "dataset_id": first_dataset.id,
            "filename": first_profile.filename,
            "version_number": first_dataset.version_number,
            "version_type": first_dataset.version_type,
            "created_at": first_dataset.uploaded_at,
        },
        "after": {
            "dataset_id": second_dataset.id,
            "filename": second_profile.filename,
            "version_number": second_dataset.version_number,
            "version_type": second_dataset.version_type,
            "created_at": second_dataset.uploaded_at,
        },
        "metrics": {
            key: value.to_dict()
            for key, value in comparisons.items()
        },
        "summary": _build_summary(
            comparisons,
        ),
    }