from __future__ import annotations

from io import BytesIO

import pandas as pd

from app.models.schemas import DatasetProfile


def build_cleaned_dataframe(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> pd.DataFrame:
    """
    Apply ONLY deterministic, safe cleaning steps.

    We intentionally do NOT repair:

    - business-rule failures
    - statistical outliers
    - ML anomalies

    because they require human review.
    """

    cleaned = dataframe.copy()

    # --------------------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------------------

    cleaned = cleaned.drop_duplicates()

    # --------------------------------------------------
    # Fill numeric missing values with median
    # --------------------------------------------------

    numeric_columns = cleaned.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        if cleaned[column].isna().any():

            cleaned[column] = cleaned[column].fillna(
                cleaned[column].median()
            )

    # --------------------------------------------------
    # Fill categorical values with mode
    # --------------------------------------------------

    categorical_columns = cleaned.select_dtypes(
        exclude="number"
    ).columns

    for column in categorical_columns:

        if cleaned[column].isna().any():

            mode = cleaned[column].mode()

            if not mode.empty:

                cleaned[column] = cleaned[column].fillna(
                    mode.iloc[0]
                )

    return cleaned


def dataframe_to_csv_bytes(
    dataframe: pd.DataFrame,
) -> bytes:

    buffer = BytesIO()

    dataframe.to_csv(
        buffer,
        index=False,
    )

    return buffer.getvalue()