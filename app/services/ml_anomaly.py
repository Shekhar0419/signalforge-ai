from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_ml_anomalies(
    dataframe: pd.DataFrame,
    contamination: float = 0.05,
) -> list[dict[str, Any]]:
    """
    Detect anomalous rows using Isolation Forest.
    """

    numeric = dataframe.select_dtypes(include="number")

    if numeric.empty:
        return []

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
    )

    predictions = model.fit_predict(numeric)

    scores = model.decision_function(numeric)

    anomalies = []

    for index, prediction in enumerate(predictions):

        if prediction == -1:

            anomalies.append(
                {
                    "row_index": int(index),
                    "anomaly_score": float(scores[index]),
                }
            )

    return anomalies