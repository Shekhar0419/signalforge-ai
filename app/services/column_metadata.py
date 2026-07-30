from __future__ import annotations

from typing import Any

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


def _safe_value(value: Any) -> Any:
    """
    Convert pandas and NumPy values into JSON-safe Python values.
    """
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def _detect_column_type(series: pd.Series) -> str:
    """
    Return a readable logical datatype for a pandas Series.
    """
    if is_bool_dtype(series):
        return "boolean"

    if is_datetime64_any_dtype(series):
        return "datetime"

    if is_numeric_dtype(series):
        return "numeric"

    return "text"


def build_column_metadata(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Generate descriptive metadata for every column in a dataframe.
    """
    row_count = len(dataframe)
    metadata: list[dict[str, Any]] = []

    for column_name in dataframe.columns:
        series = dataframe[column_name]
        non_null_series = series.dropna()

        null_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        null_ratio = (
            round(null_count / row_count, 4)
            if row_count > 0
            else 0.0
        )

        unique_ratio = (
            round(unique_count / len(non_null_series), 4)
            if len(non_null_series) > 0
            else 0.0
        )

        column_data: dict[str, Any] = {
            "column_name": str(column_name),
            "pandas_dtype": str(series.dtype),
            "logical_type": _detect_column_type(series),
            "row_count": row_count,
            "non_null_count": int(series.notna().sum()),
            "null_count": null_count,
            "null_ratio": null_ratio,
            "unique_count": unique_count,
            "unique_ratio": unique_ratio,
            "memory_usage_bytes": int(
                series.memory_usage(deep=True)
            ),
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "standard_deviation": None,
            "top_values": [],
        }

        if not non_null_series.empty:
            try:
                column_data["min"] = _safe_value(
                    non_null_series.min()
                )
                column_data["max"] = _safe_value(
                    non_null_series.max()
                )
            except TypeError:
                pass

        if is_numeric_dtype(series) and not non_null_series.empty:
            column_data["mean"] = _safe_value(
                non_null_series.mean()
            )
            column_data["median"] = _safe_value(
                non_null_series.median()
            )
            column_data["standard_deviation"] = _safe_value(
                non_null_series.std()
            )

        value_counts = (
            series.astype("string")
            .fillna("<NULL>")
            .value_counts(dropna=False)
            .head(5)
        )

        column_data["top_values"] = [
            {
                "value": str(value),
                "count": int(count),
                "ratio": (
                    round(int(count) / row_count, 4)
                    if row_count > 0
                    else 0.0
                ),
            }
            for value, count in value_counts.items()
        ]

        metadata.append(column_data)

    return metadata