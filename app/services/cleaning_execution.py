from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_numeric_dtype,
)

from app.core.config import Settings
from app.models.schemas import DatasetProfile
from app.services.profiling import profile_dataframe


@dataclass(frozen=True)
class AppliedCleaningAction:
    category: str
    column: str | None
    title: str
    rows_affected: int
    status: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _json_safe(value: Any) -> Any:
    """
    Convert pandas and NumPy values into JSON-safe Python values.
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def _preview_rows(
    dataframe: pd.DataFrame,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Return the first rows in a JSON-safe format.
    """
    records: list[dict[str, Any]] = []

    for record in dataframe.head(limit).to_dict(
        orient="records"
    ):
        records.append(
            {
                str(key): _json_safe(value)
                for key, value in record.items()
            }
        )

    return records


def _normalize_score(
    score: float,
) -> float:
    normalized = (
        score * 100
        if score <= 1
        else score
    )

    return round(
        max(
            0.0,
            min(normalized, 100.0),
        ),
        2,
    )


def _fill_numeric_missing_values(
    dataframe: pd.DataFrame,
    column_name: str,
) -> AppliedCleaningAction:
    series = dataframe[column_name]
    missing_count = int(
        series.isna().sum()
    )

    if missing_count == 0:
        return AppliedCleaningAction(
            category="missing_values",
            column=column_name,
            title=(
                f"Fill missing values in "
                f"{column_name}"
            ),
            rows_affected=0,
            status="skipped",
            message=(
                "No missing values were found."
            ),
        )

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    median = numeric.median()

    if pd.isna(median):
        return AppliedCleaningAction(
            category="missing_values",
            column=column_name,
            title=(
                f"Fill missing values in "
                f"{column_name}"
            ),
            rows_affected=0,
            status="skipped",
            message=(
                "A numeric median could not be "
                "calculated for this column."
            ),
        )

    dataframe[column_name] = (
        numeric.fillna(median)
    )

    return AppliedCleaningAction(
        category="missing_values",
        column=column_name,
        title=(
            f"Fill missing values in "
            f"{column_name} with the median"
        ),
        rows_affected=missing_count,
        status="applied",
        message=(
            f"Filled {missing_count} missing "
            f"value"
            f"{'s' if missing_count != 1 else ''} "
            f"with median {median:g}."
        ),
    )


def _fill_text_missing_values(
    dataframe: pd.DataFrame,
    column_name: str,
) -> AppliedCleaningAction:
    series = dataframe[column_name]
    missing_count = int(
        series.isna().sum()
    )

    if missing_count == 0:
        return AppliedCleaningAction(
            category="missing_values",
            column=column_name,
            title=(
                f"Fill missing values in "
                f"{column_name}"
            ),
            rows_affected=0,
            status="skipped",
            message=(
                "No missing values were found."
            ),
        )

    mode = series.mode(
        dropna=True
    )

    if mode.empty:
        return AppliedCleaningAction(
            category="missing_values",
            column=column_name,
            title=(
                f"Fill missing values in "
                f"{column_name}"
            ),
            rows_affected=0,
            status="skipped",
            message=(
                "A mode could not be calculated "
                "for this column."
            ),
        )

    mode_value = mode.iloc[0]

    dataframe[column_name] = (
        series.fillna(mode_value)
    )

    return AppliedCleaningAction(
        category="missing_values",
        column=column_name,
        title=(
            f"Fill missing values in "
            f"{column_name} with the mode"
        ),
        rows_affected=missing_count,
        status="applied",
        message=(
            f"Filled {missing_count} missing "
            f"value"
            f"{'s' if missing_count != 1 else ''} "
            "with the most frequent value."
        ),
    )


def _apply_missing_value_cleaning(
    dataframe: pd.DataFrame,
) -> list[AppliedCleaningAction]:
    actions: list[
        AppliedCleaningAction
    ] = []

    for column_name in dataframe.columns:
        series = dataframe[column_name]

        if not series.isna().any():
            continue

        is_numeric = (
            is_numeric_dtype(series)
            and not is_bool_dtype(series)
        )

        if is_numeric:
            action = (
                _fill_numeric_missing_values(
                    dataframe=dataframe,
                    column_name=str(
                        column_name
                    ),
                )
            )
        else:
            action = (
                _fill_text_missing_values(
                    dataframe=dataframe,
                    column_name=str(
                        column_name
                    ),
                )
            )

        actions.append(action)

    return actions


def _apply_duplicate_cleaning(
    dataframe: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    AppliedCleaningAction | None,
]:
    duplicate_count = int(
        dataframe.duplicated().sum()
    )

    if duplicate_count == 0:
        return dataframe, None

    cleaned = (
        dataframe
        .drop_duplicates()
        .reset_index(drop=True)
    )

    action = AppliedCleaningAction(
        category="duplicates",
        column=None,
        title="Remove exact duplicate rows",
        rows_affected=duplicate_count,
        status="applied",
        message=(
            f"Removed {duplicate_count} exact "
            f"duplicate row"
            f"{'s' if duplicate_count != 1 else ''}."
        ),
    )

    return cleaned, action


def _manual_review_actions(
    profile: DatasetProfile,
) -> list[AppliedCleaningAction]:
    """
    Record findings that are intentionally not changed automatically.
    """
    actions: list[
        AppliedCleaningAction
    ] = []

    for rule in profile.business_rules:
        passed = rule.get("passed")

        status = str(
            rule.get("status", "")
        ).lower()

        raw_violations = rule.get(
            "violation_count",
            rule.get(
                "violations",
                rule.get(
                    "failed_count",
                    0,
                ),
            ),
        )

        try:
            violation_count = int(
                raw_violations or 0
            )
        except (TypeError, ValueError):
            violation_count = 0

        if (
            passed is False
            or status in {
                "failed",
                "fail",
            }
            or violation_count > 0
        ):
            rule_name = (
                rule.get("rule")
                or rule.get("rule_name")
                or rule.get("description")
                or "Business validation rule"
            )

            column = rule.get("column")

            actions.append(
                AppliedCleaningAction(
                    category="business_rules",
                    column=(
                        str(column)
                        if column is not None
                        else None
                    ),
                    title=(
                        f"Manual review required: "
                        f"{rule_name}"
                    ),
                    rows_affected=(
                        violation_count
                    ),
                    status="review_required",
                    message=(
                        "SignalForge did not modify "
                        "these records because the "
                        "correct remediation depends "
                        "on domain-specific rules."
                    ),
                )
            )

    for column in profile.columns:
        if column.outlier_count <= 0:
            continue

        actions.append(
            AppliedCleaningAction(
                category="outliers",
                column=column.name,
                title=(
                    f"Review outliers in "
                    f"{column.name}"
                ),
                rows_affected=(
                    column.outlier_count
                ),
                status="review_required",
                message=(
                    "Outliers were preserved because "
                    "rare values may be legitimate. "
                    "Review them before capping, "
                    "transforming, or removing."
                ),
            )
        )

    return actions


def preview_cleaning_execution(
    dataframe: pd.DataFrame,
    filename: str,
    settings: Settings,
    preview_limit: int = 20,
) -> dict[str, Any]:
    """
    Simulate safe cleaning operations and return before/after metrics.

    The original dataframe is never modified.
    """
    if preview_limit < 1:
        raise ValueError(
            "Preview limit must be at least 1."
        )

    original = dataframe.copy(
        deep=True
    )

    before_profile = profile_dataframe(
        dataframe=original,
        filename=filename,
        settings=settings,
    )

    cleaned = original.copy(
        deep=True
    )

    applied_actions: list[
        AppliedCleaningAction
    ] = []

    cleaned, duplicate_action = (
        _apply_duplicate_cleaning(
            cleaned
        )
    )

    if duplicate_action is not None:
        applied_actions.append(
            duplicate_action
        )

    applied_actions.extend(
        _apply_missing_value_cleaning(
            cleaned
        )
    )

    after_profile = profile_dataframe(
        dataframe=cleaned,
        filename=filename,
        settings=settings,
    )

    review_actions = (
        _manual_review_actions(
            before_profile
        )
    )

    before_score = _normalize_score(
        before_profile.reliability_score
    )

    after_score = _normalize_score(
        after_profile.reliability_score
    )

    return {
        "filename": filename,
        "before": {
            "row_count": (
                before_profile.row_count
            ),
            "column_count": (
                before_profile.column_count
            ),
            "duplicate_rows": (
                before_profile.duplicate_rows
            ),
            "missing_values": sum(
                column.missing_count
                for column in (
                    before_profile.columns
                )
            ),
            "quality_issue_count": len(
                before_profile.issues
            ),
            "reliability_score": (
                before_score
            ),
        },
        "after": {
            "row_count": (
                after_profile.row_count
            ),
            "column_count": (
                after_profile.column_count
            ),
            "duplicate_rows": (
                after_profile.duplicate_rows
            ),
            "missing_values": sum(
                column.missing_count
                for column in (
                    after_profile.columns
                )
            ),
            "quality_issue_count": len(
                after_profile.issues
            ),
            "reliability_score": (
                after_score
            ),
        },
        "estimated_score_gain": round(
            after_score - before_score,
            2,
        ),
        "applied_action_count": len(
            [
                action
                for action in applied_actions
                if action.status == "applied"
            ]
        ),
        "review_action_count": len(
            review_actions
        ),
        "applied_actions": [
            action.to_dict()
            for action in applied_actions
        ],
        "review_actions": [
            action.to_dict()
            for action in review_actions
        ],
        "preview_columns": [
            str(column)
            for column in cleaned.columns
        ],
        "preview_rows": _preview_rows(
            dataframe=cleaned,
            limit=preview_limit,
        ),
    }