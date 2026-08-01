from __future__ import annotations

import json
from typing import Any

from app.models.schemas import DatasetProfile


def _failed_business_rules(
    profile: DatasetProfile,
) -> list[dict[str, Any]]:
    """
    Return only business-rule results that contain violations.
    """
    failed_rules: list[dict[str, Any]] = []

    for rule in profile.business_rules:
        passed = rule.get("passed")
        status = str(
            rule.get("status", "")
        ).lower()

        violation_count = rule.get(
            "violation_count",
            rule.get(
                "violations",
                rule.get("failed_count", 0),
            ),
        )

        try:
            normalized_violations = int(
                violation_count or 0
            )
        except (TypeError, ValueError):
            normalized_violations = 0

        if (
            passed is False
            or status in {"failed", "fail"}
            or normalized_violations > 0
        ):
            failed_rules.append(
                {
                    "column": rule.get("column"),
                    "rule": rule.get(
                        "rule",
                        rule.get("rule_name"),
                    ),
                    "description": rule.get(
                        "description"
                    ),
                    "status": status or None,
                    "passed": passed,
                    "violations": normalized_violations,
                    "severity": rule.get("severity"),
                }
            )

    return failed_rules


def _column_context(
    profile: DatasetProfile,
) -> list[dict[str, Any]]:
    """
    Build concise, privacy-safe column context.

    Raw top values are intentionally excluded because they may contain
    emails, names, identifiers, free text, or other sensitive values.
    """
    columns: list[dict[str, Any]] = []

    for column in profile.columns:
        columns.append(
            {
                "name": column.name,
                "type": column.inferred_type,
                "non_null_count": column.non_null_count,
                "missing_count": column.missing_count,
                "missing_ratio": column.missing_ratio,
                "unique_count": column.unique_count,
                "unique_ratio": column.unique_ratio,
                "outlier_count": column.outlier_count,
                "outlier_ratio": column.outlier_ratio,
                "statistics": column.statistics,
            }
        )

    return columns


def build_copilot_context(
    profile: DatasetProfile,
) -> dict[str, Any]:
    """
    Convert a DatasetProfile into structured context for the AI copilot.

    Raw preview rows and raw top values are excluded to reduce privacy
    risk, prompt size, and accidental disclosure of sensitive content.
    """
    return {
        "dataset": {
            "filename": profile.filename,
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "duplicate_rows": profile.duplicate_rows,
            "reliability_score": profile.reliability_score,
        },
        "quality_issues": [
            {
                "severity": issue.severity,
                "code": issue.code,
                "column": issue.column,
                "message": issue.message,
            }
            for issue in profile.issues
        ],
        "columns": _column_context(profile),
        "failed_business_rules": _failed_business_rules(
            profile
        ),
        "recommendations": list(
            profile.recommendations
        ),
        "ml_anomaly_count": len(
            profile.ml_anomalies
        ),
    }


def build_copilot_prompt(
    profile: DatasetProfile,
    question: str,
) -> str:
    """
    Build the final user prompt sent to an LLM provider.
    """
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError(
            "The copilot question cannot be empty."
        )

    context = build_copilot_context(
        profile
    )

    return (
        "You are SignalForge AI, a data-reliability copilot.\n\n"
        "Answer the user's question using only the supplied dataset "
        "profile. Do not invent records, causes, statistics, columns, "
        "or business facts that are not supported by the context.\n\n"
        "Guidelines:\n"
        "- Clearly distinguish detected facts from possible explanations.\n"
        "- Mention specific column names and metrics when available.\n"
        "- Prioritize practical remediation actions.\n"
        "- Use clear business-friendly language.\n"
        "- If the profile does not contain enough information, say so.\n"
        "- Do not claim that the dataset is safe for production without "
        "appropriate validation.\n"
        "- Keep the answer concise but useful.\n\n"
        "Dataset profile:\n"
        f"{json.dumps(context, indent=2, default=str)}\n\n"
        "User question:\n"
        f"{cleaned_question}"
    )