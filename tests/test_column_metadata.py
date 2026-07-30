import pandas as pd
import pytest

from app.services.column_metadata import build_column_metadata


def test_build_column_metadata() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "age": [25, 30, None, 40],
            "city": ["Austin", "Dallas", "Austin", None],
            "active": [True, False, True, True],
        }
    )

    metadata = build_column_metadata(dataframe)

    assert len(metadata) == 4

    customer_id = metadata[0]
    assert customer_id["column_name"] == "customer_id"
    assert customer_id["logical_type"] == "numeric"
    assert customer_id["null_count"] == 0
    assert customer_id["unique_count"] == 4
    assert customer_id["unique_ratio"] == 1.0
    assert customer_id["min"] == 1
    assert customer_id["max"] == 4

    age = metadata[1]
    assert age["null_count"] == 1
    assert age["null_ratio"] == 0.25
    assert age["mean"] == pytest.approx(31.6667, rel=1e-4)
    assert age["median"] == 30.0

    city = metadata[2]
    assert city["logical_type"] == "text"
    assert city["unique_count"] == 2
    assert city["top_values"][0]["value"] == "Austin"
    assert city["top_values"][0]["count"] == 2

    active = metadata[3]
    assert active["logical_type"] == "boolean"