from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.models.schemas import DatasetProfile


@dataclass(frozen=True)
class CleaningAction:
    priority: int
    category: str
    column: str | None
    title: str
    reason: str
    pandas_code: str
    pyspark_code: str
    sql_code: str
    estimated_score_gain: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _quote_python_column(column: str) -> str:
    escaped = column.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _quote_sql_identifier(column: str) -> str:
    escaped = column.replace('"', '""')
    return f'"{escaped}"'


def _failed_business_rules(
    profile: DatasetProfile,
) -> list[dict[str, Any]]:
    failed_rules: list[dict[str, Any]] = []

    for rule in profile.business_rules:
        status = str(
            rule.get("status", "")
        ).lower()

        raw_violations = rule.get(
            "violation_count",
            rule.get(
                "violations",
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
            rule.get("passed") is False
            or status in {"failed", "fail"}
            or violation_count > 0
        ):
            failed_rules.append(
                {
                    **rule,
                    "normalized_violations": violation_count,
                }
            )

    return failed_rules


def _is_numeric_type(
    inferred_type: str,
) -> bool:
    normalized = inferred_type.lower()

    numeric_tokens = (
        "int",
        "float",
        "double",
        "decimal",
        "number",
        "numeric",
    )

    return any(
        token in normalized
        for token in numeric_tokens
    )


def _build_duplicate_action(
    profile: DatasetProfile,
) -> CleaningAction | None:
    if profile.duplicate_rows <= 0:
        return None

    return CleaningAction(
        priority=1,
        category="duplicates",
        column=None,
        title="Remove duplicate rows",
        reason=(
            f"{profile.duplicate_rows} duplicate row"
            f"{'s were' if profile.duplicate_rows != 1 else ' was'} detected."
        ),
        pandas_code=(
            "df = df.drop_duplicates().reset_index(drop=True)"
        ),
        pyspark_code=(
            "df = df.dropDuplicates()"
        ),
        sql_code=(
            "-- Replace source_table and destination_table.\n"
            "CREATE TABLE destination_table AS\n"
            "SELECT DISTINCT *\n"
            "FROM source_table;"
        ),
        estimated_score_gain=min(
            8.0,
            max(
                1.0,
                profile.duplicate_rows
                / max(profile.row_count, 1)
                * 100,
            ),
        ),
    )


def _build_missing_value_actions(
    profile: DatasetProfile,
) -> list[CleaningAction]:
    actions: list[CleaningAction] = []

    for column in profile.columns:
        if column.missing_count <= 0:
            continue

        python_column = _quote_python_column(
            column.name
        )

        sql_column = _quote_sql_identifier(
            column.name
        )

        if _is_numeric_type(
            column.inferred_type
        ):
            title = (
                f"Fill missing values in {column.name} "
                "with the median"
            )

            pandas_code = (
                f"df[{python_column}] = "
                f"df[{python_column}].fillna("
                f"df[{python_column}].median()"
                ")"
            )

            pyspark_code = (
                "from pyspark.ml.feature import Imputer\n\n"
                "imputer = Imputer(\n"
                f"    inputCols=[{python_column}],\n"
                f"    outputCols=[{python_column}],\n"
                '    strategy="median",\n'
                ")\n"
                "df = imputer.fit(df).transform(df)"
            )

            sql_code = (
                "-- Replace source_table and destination_table.\n"
                "CREATE TABLE destination_table AS\n"
                "SELECT\n"
                "    *,\n"
                f"    COALESCE({sql_column}, "
                f"PERCENTILE_CONT(0.5) WITHIN GROUP "
                f"(ORDER BY {sql_column}) OVER ()) "
                f"AS {sql_column}_clean\n"
                "FROM source_table;"
            )
        else:
            title = (
                f"Fill missing values in {column.name} "
                "with the most frequent value"
            )

            pandas_code = (
                f"mode_value = df[{python_column}].mode(dropna=True)\n"
                "if not mode_value.empty:\n"
                f"    df[{python_column}] = "
                f"df[{python_column}].fillna(mode_value.iloc[0])"
            )

            pyspark_code = (
                "mode_row = (\n"
                f"    df.groupBy({python_column})\n"
                "      .count()\n"
                "      .orderBy(\"count\", ascending=False)\n"
                "      .first()\n"
                ")\n"
                "if mode_row is not None:\n"
                f"    df = df.fillna({{{python_column}: mode_row[0]}})"
            )

            sql_code = (
                "-- Replace source_table and destination_table.\n"
                "WITH mode_value AS (\n"
                f"    SELECT {sql_column} AS value\n"
                "    FROM source_table\n"
                f"    WHERE {sql_column} IS NOT NULL\n"
                f"    GROUP BY {sql_column}\n"
                "    ORDER BY COUNT(*) DESC\n"
                "    FETCH FIRST 1 ROW ONLY\n"
                ")\n"
                "CREATE TABLE destination_table AS\n"
                "SELECT\n"
                "    *,\n"
                f"    COALESCE({sql_column}, "
                f"(SELECT value FROM mode_value)) "
                f"AS {sql_column}_clean\n"
                "FROM source_table;"
            )

        actions.append(
            CleaningAction(
                priority=2,
                category="missing_values",
                column=column.name,
                title=title,
                reason=(
                    f"{column.missing_count} missing value"
                    f"{'s' if column.missing_count != 1 else ''} "
                    f"were detected "
                    f"({column.missing_ratio:.1%})."
                ),
                pandas_code=pandas_code,
                pyspark_code=pyspark_code,
                sql_code=sql_code,
                estimated_score_gain=min(
                    10.0,
                    max(
                        0.5,
                        column.missing_ratio * 100,
                    ),
                ),
            )
        )

    return actions


def _build_business_rule_actions(
    profile: DatasetProfile,
) -> list[CleaningAction]:
    actions: list[CleaningAction] = []

    for rule in _failed_business_rules(
        profile
    ):
        column = rule.get("column")

        rule_name = (
            rule.get("rule")
            or rule.get("rule_name")
            or rule.get("description")
            or "validation rule"
        )

        violation_count = int(
            rule.get(
                "normalized_violations",
                0,
            )
        )

        if (
            isinstance(column, str)
            and column.strip()
        ):
            cleaned_column = column.strip()

            python_column = _quote_python_column(
                cleaned_column
            )

            sql_column = _quote_sql_identifier(
                cleaned_column
            )

            pandas_code = (
                f"# Review rows that violate: {rule_name}\n"
                f"invalid_rows = df[df[{python_column}].isna()]\n"
                "# Apply a domain-approved correction before dropping rows."
            )

            pyspark_code = (
                f"# Review rows that violate: {rule_name}\n"
                f"invalid_rows = df.filter("
                f"df[{python_column}].isNull()"
                ")\n"
                "# Apply a domain-approved correction before filtering rows."
            )

            sql_code = (
                f"-- Review rows that violate: {rule_name}\n"
                "SELECT *\n"
                "FROM source_table\n"
                f"WHERE {sql_column} IS NULL;"
            )
        else:
            cleaned_column = None

            pandas_code = (
                f"# Review records that violate: {rule_name}\n"
                "# Add a domain-specific boolean mask before modifying rows."
            )

            pyspark_code = (
                f"# Review records that violate: {rule_name}\n"
                "# Add a domain-specific Spark filter before modifying rows."
            )

            sql_code = (
                f"-- Review records that violate: {rule_name}\n"
                "-- Add the domain-specific WHERE condition here."
            )

        actions.append(
            CleaningAction(
                priority=1,
                category="business_rules",
                column=cleaned_column,
                title=(
                    f"Resolve failed rule: {rule_name}"
                ),
                reason=(
                    f"{violation_count} violation"
                    f"{'s were' if violation_count != 1 else ' was'} detected."
                ),
                pandas_code=pandas_code,
                pyspark_code=pyspark_code,
                sql_code=sql_code,
                estimated_score_gain=min(
                    8.0,
                    max(
                        1.0,
                        violation_count * 0.5,
                    ),
                ),
            )
        )

    return actions


def _build_outlier_actions(
    profile: DatasetProfile,
) -> list[CleaningAction]:
    actions: list[CleaningAction] = []

    for column in profile.columns:
        if column.outlier_count <= 0:
            continue

        python_column = _quote_python_column(
            column.name
        )

        sql_column = _quote_sql_identifier(
            column.name
        )

        actions.append(
            CleaningAction(
                priority=3,
                category="outliers",
                column=column.name,
                title=(
                    f"Review outliers in {column.name}"
                ),
                reason=(
                    f"{column.outlier_count} IQR outlier"
                    f"{'s were' if column.outlier_count != 1 else ' was'} "
                    f"detected ({column.outlier_ratio:.1%})."
                ),
                pandas_code=(
                    f"q1 = df[{python_column}].quantile(0.25)\n"
                    f"q3 = df[{python_column}].quantile(0.75)\n"
                    "iqr = q3 - q1\n"
                    "lower = q1 - 1.5 * iqr\n"
                    "upper = q3 + 1.5 * iqr\n"
                    f"outlier_mask = ~df[{python_column}].between("
                    "lower, upper, inclusive=\"both\")\n"
                    "outlier_rows = df[outlier_mask]\n"
                    "# Review before capping, transforming, or removing."
                ),
                pyspark_code=(
                    f"quantiles = df.approxQuantile("
                    f"{python_column}, [0.25, 0.75], 0.01)\n"
                    "q1, q3 = quantiles\n"
                    "iqr = q3 - q1\n"
                    "lower = q1 - 1.5 * iqr\n"
                    "upper = q3 + 1.5 * iqr\n"
                    f"outlier_rows = df.filter("
                    f"(df[{python_column}] < lower) | "
                    f"(df[{python_column}] > upper)"
                    ")\n"
                    "# Review before capping, transforming, or removing."
                ),
                sql_code=(
                    f"-- Review outliers in {sql_column} using "
                    "database-specific percentile functions.\n"
                    "WITH bounds AS (\n"
                    "    SELECT\n"
                    f"        PERCENTILE_CONT(0.25) WITHIN GROUP "
                    f"(ORDER BY {sql_column}) AS q1,\n"
                    f"        PERCENTILE_CONT(0.75) WITHIN GROUP "
                    f"(ORDER BY {sql_column}) AS q3\n"
                    "    FROM source_table\n"
                    ")\n"
                    "SELECT source_table.*\n"
                    "FROM source_table\n"
                    "CROSS JOIN bounds\n"
                    f"WHERE {sql_column} < q1 - 1.5 * (q3 - q1)\n"
                    f"   OR {sql_column} > q3 + 1.5 * (q3 - q1);"
                ),
                estimated_score_gain=min(
                    5.0,
                    max(
                        0.5,
                        column.outlier_ratio * 50,
                    ),
                ),
            )
        )

    return actions


def build_cleaning_plan(
    profile: DatasetProfile,
) -> dict[str, Any]:
    actions: list[CleaningAction] = []

    duplicate_action = _build_duplicate_action(
        profile
    )

    if duplicate_action is not None:
        actions.append(
            duplicate_action
        )

    actions.extend(
        _build_business_rule_actions(
            profile
        )
    )

    actions.extend(
        _build_missing_value_actions(
            profile
        )
    )

    actions.extend(
        _build_outlier_actions(
            profile
        )
    )

    actions = sorted(
        actions,
        key=lambda action: (
            action.priority,
            action.category,
            action.column or "",
        ),
    )

    current_score = (
        profile.reliability_score * 100
        if profile.reliability_score <= 1
        else profile.reliability_score
    )

    estimated_gain = sum(
        action.estimated_score_gain
        for action in actions
    )

    predicted_score = min(
        100.0,
        current_score + estimated_gain,
    )

    return {
        "current_reliability_score": round(
            current_score,
            2,
        ),
        "predicted_reliability_score": round(
            predicted_score,
            2,
        ),
        "estimated_score_gain": round(
            predicted_score - current_score,
            2,
        ),
        "action_count": len(actions),
        "actions": [
            action.to_dict()
            for action in actions
        ],
    }