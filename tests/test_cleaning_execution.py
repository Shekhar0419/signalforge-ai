import pandas as pd
import pytest

from app.core.config import Settings
from app.services.cleaning_execution import (
    preview_cleaning_execution,
)


def _build_dataframe() -> pd.DataFrame:
    """
    Build test data containing:

    - one exact duplicate row;
    - two missing values;
    - one clear numeric outlier;
    - business-rule findings for manual review.
    """
    return pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                3,
                4,
                4,
                6,
            ],
            "age": [
                25,
                None,
                35,
                42,
                42,
                31,
            ],
            "city": [
                "St. Louis",
                "Chicago",
                None,
                "Austin",
                "Austin",
                "Dallas",
            ],
            "salary": [
                50000,
                52000,
                51000,
                53000,
                53000,
                1000000,
            ],
        }
    )


def test_preview_cleaning_execution() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    assert result["before"]["row_count"] == 6
    assert result["after"]["row_count"] == 5

    assert (
        result["before"]["duplicate_rows"]
        == 1
    )

    assert (
        result["after"]["duplicate_rows"]
        == 0
    )

    assert (
        result["before"]["missing_values"]
        == 2
    )

    assert (
        result["after"]["missing_values"]
        == 0
    )

    assert (
        result["after"]["reliability_score"]
        >= result["before"][
            "reliability_score"
        ]
    )

    assert (
        result["applied_action_count"]
        >= 3
    )


def test_original_dataframe_is_not_modified() -> None:
    dataframe = _build_dataframe()

    original_copy = dataframe.copy(
        deep=True
    )

    preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_copy,
    )


def test_cleaning_preview_contains_rows() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
        preview_limit=3,
    )

    assert len(
        result["preview_rows"]
    ) == 3

    assert result[
        "preview_columns"
    ] == [
        "customer_id",
        "age",
        "city",
        "salary",
    ]

    for row in result[
        "preview_rows"
    ]:
        assert row["age"] is not None
        assert row["city"] is not None


def test_outliers_require_manual_review() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    review_categories = {
        action["category"]
        for action in result[
            "review_actions"
        ]
    }

    assert "outliers" in review_categories


def test_business_rules_require_manual_review() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    review_categories = {
        action["category"]
        for action in result[
            "review_actions"
        ]
    }

    assert (
        "business_rules"
        in review_categories
    )


def test_applied_actions_include_duplicate_removal() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    duplicate_actions = [
        action
        for action in result[
            "applied_actions"
        ]
        if action["category"]
        == "duplicates"
    ]

    assert len(
        duplicate_actions
    ) == 1

    duplicate_action = (
        duplicate_actions[0]
    )

    assert (
        duplicate_action["status"]
        == "applied"
    )

    assert (
        duplicate_action[
            "rows_affected"
        ]
        == 1
    )


def test_applied_actions_include_missing_value_fills() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    missing_actions = [
        action
        for action in result[
            "applied_actions"
        ]
        if action["category"]
        == "missing_values"
    ]

    affected_columns = {
        action["column"]
        for action in missing_actions
    }

    assert "age" in affected_columns
    assert "city" in affected_columns

    for action in missing_actions:
        assert (
            action["status"]
            == "applied"
        )

        assert (
            action[
                "rows_affected"
            ]
            >= 1
        )


def test_cleaning_preview_returns_before_after_metrics() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    expected_metrics = {
        "row_count",
        "column_count",
        "duplicate_rows",
        "missing_values",
        "quality_issue_count",
        "reliability_score",
    }

    assert expected_metrics.issubset(
        result["before"].keys()
    )

    assert expected_metrics.issubset(
        result["after"].keys()
    )

    assert isinstance(
        result[
            "estimated_score_gain"
        ],
        float,
    )


def test_preview_limit_is_respected() -> None:
    dataframe = _build_dataframe()

    result = preview_cleaning_execution(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
        preview_limit=2,
    )

    assert len(
        result["preview_rows"]
    ) == 2


def test_invalid_preview_limit() -> None:
    dataframe = _build_dataframe()

    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        preview_cleaning_execution(
            dataframe=dataframe,
            filename="customers.csv",
            settings=Settings(),
            preview_limit=0,
        )