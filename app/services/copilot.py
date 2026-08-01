from __future__ import annotations

from typing import Any

from app.models.copilot import CopilotResponse
from app.models.schemas import DatasetProfile
from app.services.copilot_context import (
    build_copilot_prompt,
)


class CopilotServiceError(RuntimeError):
    """Raised when the copilot cannot generate an answer."""


def _failed_business_rules(
    profile: DatasetProfile,
) -> list[dict[str, Any]]:
    failed_rules: list[dict[str, Any]] = []

    for rule in profile.business_rules:
        passed = rule.get("passed")
        status = str(
            rule.get("status", "")
        ).lower()

        raw_violations = rule.get(
            "violations",
            rule.get(
                "violation_count",
                rule.get("failed_count", 0),
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
            or status in {"failed", "fail"}
            or violation_count > 0
        ):
            failed_rules.append(
                {
                    **rule,
                    "normalized_violations": (
                        violation_count
                    ),
                }
            )

    return failed_rules


def _get_rule_column(
    rule: dict[str, Any],
) -> str:
    column = rule.get("column")

    if isinstance(column, str) and column.strip():
        return column.strip()

    return "affected column"


def _get_rule_name(
    rule: dict[str, Any],
) -> str:
    for key in (
        "rule",
        "rule_name",
        "description",
    ):
        value = rule.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return "validation rule"


def _column_risk_score(
    missing_ratio: float,
    outlier_ratio: float,
    failed_rule_count: int,
) -> float:
    return (
        missing_ratio * 100
        + outlier_ratio * 50
        + failed_rule_count * 25
    )


def _rank_risky_columns(
    profile: DatasetProfile,
) -> list[dict[str, Any]]:
    failed_rules = _failed_business_rules(profile)

    failed_rules_by_column: dict[str, int] = {}

    for rule in failed_rules:
        column = _get_rule_column(rule)

        failed_rules_by_column[column] = (
            failed_rules_by_column.get(column, 0)
            + 1
        )

    ranked_columns: list[dict[str, Any]] = []

    for column in profile.columns:
        failed_rule_count = (
            failed_rules_by_column.get(
                column.name,
                0,
            )
        )

        risk_score = _column_risk_score(
            missing_ratio=column.missing_ratio,
            outlier_ratio=column.outlier_ratio,
            failed_rule_count=failed_rule_count,
        )

        if (
            column.missing_count > 0
            or column.outlier_count > 0
            or failed_rule_count > 0
        ):
            ranked_columns.append(
                {
                    "name": column.name,
                    "missing_count": (
                        column.missing_count
                    ),
                    "missing_ratio": (
                        column.missing_ratio
                    ),
                    "outlier_count": (
                        column.outlier_count
                    ),
                    "outlier_ratio": (
                        column.outlier_ratio
                    ),
                    "failed_rule_count": (
                        failed_rule_count
                    ),
                    "risk_score": risk_score,
                }
            )

    return sorted(
        ranked_columns,
        key=lambda item: item["risk_score"],
        reverse=True,
    )


def _answer_cleaning_priority(
    profile: DatasetProfile,
) -> str:
    risky_columns = _rank_risky_columns(
        profile
    )

    if not risky_columns:
        return (
            "No columns currently stand out as high-priority "
            "cleaning targets based on missing values, outliers, "
            "and failed business rules. Continue validating the "
            "dataset before production use."
        )

    lines = [
        "The highest-priority columns to review are:"
    ]

    for index, column in enumerate(
        risky_columns[:5],
        start=1,
    ):
        reasons: list[str] = []

        if column["missing_count"] > 0:
            reasons.append(
                f"{column['missing_count']} missing values "
                f"({column['missing_ratio']:.1%})"
            )

        if column["outlier_count"] > 0:
            reasons.append(
                f"{column['outlier_count']} statistical "
                f"outliers ({column['outlier_ratio']:.1%})"
            )

        if column["failed_rule_count"] > 0:
            reasons.append(
                f"{column['failed_rule_count']} failed "
                "business-rule check"
                f"{'s' if column['failed_rule_count'] != 1 else ''}"
            )

        lines.append(
            f"{index}. {column['name']}: "
            + ", ".join(reasons)
            + "."
        )

    lines.append(
        "Resolve failed validation rules first, then investigate "
        "missing values and confirm whether detected outliers are "
        "legitimate rare records or data errors."
    )

    return "\n".join(lines)


def _answer_reliability(
    profile: DatasetProfile,
) -> str:
    failed_rules = _failed_business_rules(
        profile
    )

    parts = [
        (
            f"The dataset reliability score is "
            f"{profile.reliability_score:.1f}%."
        )
    ]

    if profile.duplicate_rows:
        parts.append(
            f"It contains {profile.duplicate_rows} "
            "duplicate rows."
        )

    if profile.issues:
        parts.append(
            f"The profiler identified "
            f"{len(profile.issues)} quality issue"
            f"{'s' if len(profile.issues) != 1 else ''}."
        )

    if failed_rules:
        parts.append(
            f"{len(failed_rules)} business-rule check"
            f"{'s' if len(failed_rules) != 1 else ''} failed."
        )

    if profile.ml_anomalies:
        parts.append(
            f"Isolation Forest flagged "
            f"{len(profile.ml_anomalies)} potential "
            "anomalous records."
        )

    if (
        not profile.issues
        and not failed_rules
        and not profile.ml_anomalies
        and not profile.duplicate_rows
    ):
        parts.append(
            "No major issues were detected by the current checks."
        )
    else:
        parts.append(
            "The score should be interpreted together with the "
            "individual validation findings rather than used as "
            "the only production-readiness decision."
        )

    return " ".join(parts)


def _answer_anomalies(
    profile: DatasetProfile,
) -> str:
    anomaly_count = len(
        profile.ml_anomalies
    )

    if anomaly_count == 0:
        return (
            "Isolation Forest did not flag any potential anomalous "
            "records in the current profile. This does not guarantee "
            "that every record is correct, so domain validation is "
            "still recommended."
        )

    outlier_columns = [
        column
        for column in profile.columns
        if column.outlier_count > 0
    ]

    answer = (
        f"Isolation Forest flagged {anomaly_count} potential "
        "anomalous records. An anomaly is not automatically an "
        "error; it may represent a legitimate rare event, a unit "
        "mismatch, a measurement problem, or an incorrect "
        "transformation."
    )

    if outlier_columns:
        column_details = ", ".join(
            (
                f"{column.name} "
                f"({column.outlier_count} IQR outliers)"
            )
            for column in sorted(
                outlier_columns,
                key=lambda item: item.outlier_count,
                reverse=True,
            )[:5]
        )

        answer += (
            " Columns with statistical outlier signals include "
            f"{column_details}."
        )

    answer += (
        " Review the flagged records against source systems and "
        "business expectations before removing or modifying them."
    )

    return answer


def _answer_ml_readiness(
    profile: DatasetProfile,
) -> str:
    failed_rules = _failed_business_rules(
        profile
    )

    high_missing_columns = [
        column
        for column in profile.columns
        if column.missing_ratio >= 0.20
    ]

    risk_count = (
        len(profile.issues)
        + len(failed_rules)
        + len(profile.ml_anomalies)
        + (1 if profile.duplicate_rows else 0)
    )

    if (
        profile.reliability_score >= 90
        and risk_count == 0
    ):
        return (
            "The dataset appears suitable for initial machine-learning "
            "experimentation based on the current automated checks. "
            "Before production training, still validate the target "
            "definition, leakage risk, class balance, sampling bias, "
            "time splits, and domain-specific constraints."
        )

    blockers: list[str] = []

    if profile.duplicate_rows:
        blockers.append(
            "duplicate records"
        )

    if failed_rules:
        blockers.append(
            "failed business rules"
        )

    if high_missing_columns:
        blockers.append(
            "columns with at least 20% missing values"
        )

    if profile.ml_anomalies:
        blockers.append(
            "unreviewed anomalous records"
        )

    blocker_text = (
        ", ".join(blockers)
        if blockers
        else "the detected quality issues"
    )

    return (
        "The dataset should not yet be treated as production-ready "
        f"for machine learning because of {blocker_text}. "
        "Correct or explicitly handle these findings, define an "
        "appropriate preprocessing strategy, and validate the model "
        "using leakage-safe train and test splits."
    )


def _answer_business_rules(
    profile: DatasetProfile,
) -> str:
    failed_rules = _failed_business_rules(
        profile
    )

    if not failed_rules:
        return (
            "All currently configured business-rule checks passed. "
            "This only reflects the rules implemented in SignalForge; "
            "additional domain-specific constraints may still be needed."
        )

    lines = [
        "The following business-rule checks failed:"
    ]

    for index, rule in enumerate(
        failed_rules[:10],
        start=1,
    ):
        column = _get_rule_column(rule)
        rule_name = _get_rule_name(rule)

        violation_count = int(
            rule.get(
                "normalized_violations",
                0,
            )
        )

        lines.append(
            f"{index}. {column} — {rule_name}: "
            f"{violation_count} violation"
            f"{'s' if violation_count != 1 else ''}."
        )

    lines.append(
        "Review the affected records and verify whether the "
        "validation logic matches current business requirements."
    )

    return "\n".join(lines)


def _answer_overview(
    profile: DatasetProfile,
) -> str:
    failed_rules = _failed_business_rules(
        profile
    )

    return (
        f"The dataset '{profile.filename}' contains "
        f"{profile.row_count:,} rows and "
        f"{profile.column_count} columns, with a reliability "
        f"score of {profile.reliability_score:.1f}%. "
        f"It has {profile.duplicate_rows} duplicate rows, "
        f"{len(profile.issues)} profiler issues, "
        f"{len(failed_rules)} failed business-rule checks, and "
        f"{len(profile.ml_anomalies)} potential ML anomalies. "
        "Ask which columns need cleaning, why the score is low, "
        "whether the data is ready for ML, or for an explanation "
        "of anomalies and failed rules."
    )


def generate_fallback_answer(
    profile: DatasetProfile,
    question: str,
) -> str:
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError(
            "The copilot question cannot be empty."
        )

    normalized_question = (
        cleaned_question.lower()
    )

    cleaning_terms = (
        "clean",
        "fix first",
        "priority",
        "risky column",
        "risk column",
        "attention",
        "problem column",
    )

    reliability_terms = (
        "reliability",
        "score",
        "quality score",
        "health score",
    )

    anomaly_terms = (
        "anomaly",
        "anomalies",
        "outlier",
        "unusual",
    )

    ml_terms = (
        "machine learning",
        "ml model",
        "train a model",
        "model training",
        "ready for ml",
    )

    rule_terms = (
        "business rule",
        "business rules",
        "rule failed",
        "rules failed",
        "validation rule",
    )

    if any(
        term in normalized_question
        for term in cleaning_terms
    ):
        return _answer_cleaning_priority(
            profile
        )

    if any(
        term in normalized_question
        for term in reliability_terms
    ):
        return _answer_reliability(
            profile
        )

    if any(
        term in normalized_question
        for term in anomaly_terms
    ):
        return _answer_anomalies(
            profile
        )

    if any(
        term in normalized_question
        for term in ml_terms
    ):
        return _answer_ml_readiness(
            profile
        )

    if any(
        term in normalized_question
        for term in rule_terms
    ):
        return _answer_business_rules(
            profile
        )

    return _answer_overview(
        profile
    )


def answer_copilot_question(
    dataset_id: str,
    profile: DatasetProfile,
    question: str,
) -> CopilotResponse:
    """
    Generate a privacy-safe deterministic answer.

    The prompt is built now so the same service can later call an
    OpenAI or Ollama provider without changing the API route.
    """
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError(
            "The copilot question cannot be empty."
        )

    # Validate that a provider-ready, privacy-safe prompt can be built.
    build_copilot_prompt(
        profile=profile,
        question=cleaned_question,
    )

    answer = generate_fallback_answer(
        profile=profile,
        question=cleaned_question,
    )

    return CopilotResponse(
        dataset_id=dataset_id,
        question=cleaned_question,
        answer=answer,
        provider="fallback",
        model=None,
    )