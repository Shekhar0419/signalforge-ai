from __future__ import annotations

from typing import Any


def generate_recommendations(
    column_metadata: list[dict[str, Any]],
    business_rules: list[dict[str, Any]],
) -> list[str]:
    """
    Generate actionable recommendations from dataset quality signals.
    """

    recommendations: list[str] = []

    for column in column_metadata:

        name = column["column_name"]

        logical_type = column["logical_type"]

        null_ratio = column["null_ratio"]

        if null_ratio >= 0.20:

            if logical_type == "numeric":

                recommendations.append(
                    f"{name}: Fill missing values using the median."
                )

            else:

                recommendations.append(
                    f"{name}: Review and populate missing values."
                )

        if logical_type == "text":

            if column["unique_ratio"] > 0.95:

                recommendations.append(
                    f"{name}: Check for inconsistent text formatting."
                )

    for rule in business_rules:

        if not rule["passed"]:

            recommendations.append(
                f'{rule["column"]}: {rule["rule"]} ({rule["violations"]} violations).'
            )

    return recommendations