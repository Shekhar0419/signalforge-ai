from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pandas as pd


EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def evaluate_business_rules(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Evaluate business rules against a dataframe.

    Rules are inferred from common column names.
    """

    results: list[dict[str, Any]] = []

    for column in dataframe.columns:

        name = column.lower()

        series = dataframe[column]

        # -----------------------
        # Age
        # -----------------------

        if "age" == name:

            invalid = int((series < 0).fillna(False).sum())

            results.append(
                {
                    "column": column,
                    "rule": "Age >= 0",
                    "passed": invalid == 0,
                    "violations": invalid,
                }
            )

        # -----------------------
        # Salary
        # -----------------------

        elif "salary" in name:

            invalid = int((series <= 0).fillna(False).sum())

            results.append(
                {
                    "column": column,
                    "rule": "Salary > 0",
                    "passed": invalid == 0,
                    "violations": invalid,
                }
            )

        # -----------------------
        # Email
        # -----------------------

        elif "email" in name:

            invalid = 0

            for value in series.dropna():

                if not EMAIL_REGEX.match(str(value)):

                    invalid += 1

            results.append(
                {
                    "column": column,
                    "rule": "Valid email format",
                    "passed": invalid == 0,
                    "violations": invalid,
                }
            )

        # -----------------------
        # ID
        # -----------------------

        elif name.endswith("id"):

            duplicates = int(series.duplicated().sum())

            results.append(
                {
                    "column": column,
                    "rule": "Unique values",
                    "passed": duplicates == 0,
                    "violations": duplicates,
                }
            )

        # -----------------------
        # Dates
        # -----------------------

        elif "date" in name:

            parsed = pd.to_datetime(
                series,
                errors="coerce",
            )

            future = int(
                (parsed > datetime.utcnow())
                .fillna(False)
                .sum()
            )

            results.append(
                {
                    "column": column,
                    "rule": "No future dates",
                    "passed": future == 0,
                    "violations": future,
                }
            )

    return results