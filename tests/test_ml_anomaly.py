import pandas as pd

from app.services.ml_anomaly import detect_ml_anomalies


def test_ml_anomaly_detection():

    df = pd.DataFrame(
        {
            "salary": [
                50000,
                51000,
                52000,
                53000,
                1000000,
            ],
            "age": [
                30,
                31,
                29,
                32,
                30,
            ],
        }
    )

    anomalies = detect_ml_anomalies(df)

    assert len(anomalies) >= 1

    assert anomalies[0]["row_index"] == 4