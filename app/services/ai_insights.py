from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.models.schemas import DatasetProfile


class AIInsightResponse(BaseModel):
    """
    Structured insights generated from a dataset profile.
    """

    executive_summary: str

    root_causes: list[str] = Field(
        default_factory=list
    )

    business_impact: str

    priority_actions: list[str] = Field(
        default_factory=list
    )

    provider: str = "fallback"


def _failed_business_rules(
    profile: DatasetProfile,
) -> list[dict[str, Any]]:
    """
    Return only the business rules that failed.
    """
    return [
        rule
        for rule in profile.business_rules
        if not rule.get("passed", True)
    ]


def _build_executive_summary(
    profile: DatasetProfile,
) -> str:
    """
    Generate a deterministic executive summary.
    """
    failed_rules = _failed_business_rules(profile)

    parts = [
        (
            f"The dataset '{profile.filename}' contains "
            f"{profile.row_count} rows and "
            f"{profile.column_count} columns."
        ),
        (
            "Its overall reliability score is "
            f"{profile.reliability_score:.2f}%."
        ),
    ]

    if profile.duplicate_rows:
        parts.append(
            f"{profile.duplicate_rows} duplicate rows "
            "were detected."
        )

    if profile.issues:
        parts.append(
            f"{len(profile.issues)} data-quality issues "
            "were identified."
        )

    if failed_rules:
        parts.append(
            f"{len(failed_rules)} business-rule checks "
            "failed."
        )

    if profile.ml_anomalies:
        parts.append(
            f"{len(profile.ml_anomalies)} potential "
            "anomalous records were detected."
        )

    if (
        not profile.issues
        and not failed_rules
        and not profile.ml_anomalies
    ):
        parts.append(
            "No significant reliability problems were detected."
        )

    return " ".join(parts)


def _root_cause_for_rule(
    rule: dict[str, Any],
) -> str:
    """
    Generate a likely root-cause explanation for a failed rule.
    """
    column = str(
        rule.get("column", "unknown column")
    )

    rule_name = str(
        rule.get(
            "rule",
            rule.get(
                "rule_name",
                rule.get("description", ""),
            ),
        )
    ).lower()

    violations = int(
        rule.get("violations", 0)
    )

    prefix = (
        f"The '{column}' column has "
        f"{violations} rule violation"
        f"{'s' if violations != 1 else ''}."
    )

    if "email" in column.lower() or "email" in rule_name:
        return (
            f"{prefix} Malformed email values commonly result "
            "from missing input validation, manual entry errors, "
            "or inconsistent formatting across source systems."
        )

    if "age" in column.lower() or "age" in rule_name:
        return (
            f"{prefix} Invalid age values may result from "
            "incorrect source mappings, placeholder values, "
            "sign errors, or failures during data conversion."
        )

    if (
        "salary" in column.lower()
        or "salary" in rule_name
        or "amount" in column.lower()
    ):
        return (
            f"{prefix} Invalid monetary values may be caused by "
            "unit mismatches, missing validation, currency "
            "conversion problems, or incorrect source records."
        )

    if (
        "unique" in rule_name
        or column.lower().endswith("_id")
        or column.lower() == "id"
    ):
        return (
            f"{prefix} Duplicate identifiers commonly occur "
            "after repeated imports, joins, merge operations, "
            "or missing uniqueness constraints."
        )

    if "date" in column.lower() or "date" in rule_name:
        return (
            f"{prefix} Invalid dates may be caused by timezone "
            "differences, incorrect date parsing, future placeholder "
            "values, or source-system synchronization problems."
        )

    return (
        f"{prefix} This may indicate missing source validation, "
        "inconsistent transformation logic, or data-entry errors."
    )


def _build_root_causes(
    profile: DatasetProfile,
) -> list[str]:
    """
    Build root-cause explanations from profile findings.
    """
    causes: list[str] = []

    if profile.duplicate_rows:
        causes.append(
            "Duplicate rows may have been introduced by repeated "
            "imports, pipeline retries, joins, or the absence of "
            "deduplication controls."
        )

    for rule in _failed_business_rules(profile):
        causes.append(
            _root_cause_for_rule(rule)
        )

    high_missing_columns = [
        column
        for column in profile.columns
        if column.missing_ratio >= 0.20
    ]

    for column in high_missing_columns:
        causes.append(
            f"The '{column.name}' column is missing "
            f"{column.missing_ratio:.1%} of its values. "
            "This may indicate optional source fields, failed "
            "data collection, schema mismatches, or incomplete "
            "upstream records."
        )

    if profile.ml_anomalies:
        causes.append(
            "The detected anomalies may represent legitimate rare "
            "records, measurement errors, unit inconsistencies, "
            "incorrect transformations, or unexpected behavior "
            "within the source data."
        )

    if not causes:
        causes.append(
            "No clear systemic root cause was identified because "
            "the dataset passed the available quality checks."
        )

    return causes


def _build_business_impact(
    profile: DatasetProfile,
) -> str:
    """
    Explain the likely business and ML impact.
    """
    failed_rule_count = len(
        _failed_business_rules(profile)
    )

    risk_signals = (
        len(profile.issues)
        + failed_rule_count
        + len(profile.ml_anomalies)
    )

    if profile.reliability_score >= 90 and risk_signals == 0:
        return (
            "The dataset currently presents a low reliability risk. "
            "It appears suitable for reporting or model development, "
            "although normal validation and monitoring should continue."
        )

    if profile.reliability_score >= 75:
        return (
            "The identified issues create a moderate risk of inaccurate "
            "reporting, unstable model features, biased predictions, "
            "or additional manual review. The highest-priority findings "
            "should be resolved before production use."
        )

    return (
        "The dataset presents a high reliability risk. Using it without "
        "remediation could lead to incorrect business decisions, model "
        "performance degradation, failed downstream pipelines, and loss "
        "of trust in analytical results."
    )


def _build_priority_actions(
    profile: DatasetProfile,
) -> list[str]:
    """
    Build a prioritized remediation plan.
    """
    actions: list[str] = []

    if profile.duplicate_rows:
        actions.append(
            "Identify the dataset's business key and remove or merge "
            "duplicate records after confirming the correct source row."
        )

    for rule in _failed_business_rules(profile):
        column = str(
            rule.get("column", "affected")
        )

        violations = int(
            rule.get("violations", 0)
        )

        actions.append(
            f"Review and correct the {violations} invalid value"
            f"{'s' if violations != 1 else ''} in the "
            f"'{column}' column."
        )

    high_missing_columns = [
        column
        for column in profile.columns
        if column.missing_ratio >= 0.20
    ]

    for column in high_missing_columns:
        actions.append(
            f"Investigate why '{column.name}' is missing "
            f"{column.missing_ratio:.1%} of its values and choose "
            "an appropriate imputation, defaulting, or exclusion policy."
        )

    if profile.ml_anomalies:
        actions.append(
            "Review the records flagged by Isolation Forest and verify "
            "whether they are valid rare cases or data-quality errors."
        )

    for recommendation in profile.recommendations:
        if recommendation not in actions:
            actions.append(recommendation)

    if not actions:
        actions.append(
            "Continue monitoring dataset quality and rerun validation "
            "whenever new data is ingested."
        )

    return actions[:5]


def generate_fallback_insights(
    profile: DatasetProfile,
) -> AIInsightResponse:
    """
    Generate structured insights without an external LLM.

    This ensures the application remains fully usable when no
    OpenAI or Ollama provider is configured.
    """
    return AIInsightResponse(
        executive_summary=_build_executive_summary(
            profile
        ),
        root_causes=_build_root_causes(
            profile
        ),
        business_impact=_build_business_impact(
            profile
        ),
        priority_actions=_build_priority_actions(
            profile
        ),
        provider="fallback",
    )


def build_insight_prompt(
    profile: DatasetProfile,
) -> str:
    """
    Construct a safe, structured prompt for an LLM provider.

    Raw dataset records are not included. Only aggregated profile
    information is sent to the model.
    """
    failed_rules = _failed_business_rules(
        profile
    )

    profile_context = {
        "filename": profile.filename,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "duplicate_rows": profile.duplicate_rows,
        "reliability_score": profile.reliability_score,
        "quality_issues": [
            {
                "severity": issue.severity,
                "code": issue.code,
                "column": issue.column,
                "message": issue.message,
            }
            for issue in profile.issues
        ],
        "failed_business_rules": failed_rules,
        "recommendations": profile.recommendations,
        "anomaly_count": len(
            profile.ml_anomalies
        ),
    }

    return (
        "You are an AI data-reliability analyst.\n\n"
        "Analyze the following aggregated dataset profile. "
        "Do not invent facts, records, statistics, or causes that "
        "are unsupported by the supplied profile.\n\n"
        "Return valid JSON with exactly these fields:\n"
        "{\n"
        '  "executive_summary": "string",\n'
        '  "root_causes": ["string"],\n'
        '  "business_impact": "string",\n'
        '  "priority_actions": ["string"]\n'
        "}\n\n"
        "Requirements:\n"
        "- Use concise, professional language.\n"
        "- Clearly separate detected facts from possible causes.\n"
        "- Prioritize actions by business and data risk.\n"
        "- Do not include markdown or text outside the JSON object.\n\n"
        "Dataset profile:\n"
        f"{json.dumps(profile_context, indent=2, default=str)}"
    )