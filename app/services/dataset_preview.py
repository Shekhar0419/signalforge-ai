from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


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

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return value.item()
        except (AttributeError, ValueError):
            pass

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    return str(value)


def build_dataset_preview(
    dataframe: pd.DataFrame,
    maximum_rows: int = 20,
) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Return column names and a JSON-safe preview of the first rows.

    The original dataframe is not modified.
    """
    if maximum_rows <= 0:
        raise ValueError(
            "maximum_rows must be greater than zero."
        )

    columns = [
        str(column)
        for column in dataframe.columns
    ]

    preview_dataframe = dataframe.head(
        maximum_rows
    )

    rows: list[dict[str, Any]] = []

    for _, series in preview_dataframe.iterrows():
        row = {
            str(column): _json_safe(
                series[column]
            )
            for column in dataframe.columns
        }

        rows.append(row)

    return columns, rows