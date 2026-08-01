import pandas as pd
import pytest

from app.services.dataset_preview import (
    build_dataset_preview,
)


def test_build_dataset_preview() -> None:
    dataframe = pd.DataFrame(
        {
            "patient_id": [
                "P-001",
                "P-002",
                "P-003",
            ],
            "age": [
                42,
                None,
                65,
            ],
            "active": [
                True,
                False,
                True,
            ],
        }
    )

    columns, rows = build_dataset_preview(
        dataframe
    )

    assert columns == [
        "patient_id",
        "age",
        "active",
    ]

    assert len(rows) == 3

    assert rows[0] == {
        "patient_id": "P-001",
        "age": 42.0,
        "active": True,
    }

    assert rows[1]["patient_id"] == "P-002"
    assert rows[1]["age"] is None
    assert rows[1]["active"] is False


def test_preview_limits_number_of_rows() -> None:
    dataframe = pd.DataFrame(
        {
            "id": list(range(100)),
        }
    )

    _, rows = build_dataset_preview(
        dataframe,
        maximum_rows=20,
    )

    assert len(rows) == 20
    assert rows[0]["id"] == 0
    assert rows[-1]["id"] == 19


def test_preview_handles_empty_dataframe() -> None:
    dataframe = pd.DataFrame(
        columns=[
            "customer_id",
            "email",
        ]
    )

    columns, rows = build_dataset_preview(
        dataframe
    )

    assert columns == [
        "customer_id",
        "email",
    ]
    assert rows == []


def test_preview_rejects_invalid_row_limit() -> None:
    dataframe = pd.DataFrame(
        {
            "id": [1, 2, 3],
        }
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        build_dataset_preview(
            dataframe,
            maximum_rows=0,
        )