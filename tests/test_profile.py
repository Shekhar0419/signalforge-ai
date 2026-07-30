import pandas as pd

from app.core.config import Settings
from app.services.profiling import profile_dataframe


def test_profile_dataframe_basic_statistics() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "age": [25, 30, None, 40],
            "city": [
                "Austin",
                "Dallas",
                "Austin",
                None,
            ],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    assert profile.filename == "customers.csv"
    assert profile.row_count == 4
    assert profile.column_count == 3
    assert profile.duplicate_rows == 0

    assert len(profile.columns) == 3
    assert profile.reliability_score >= 0

    age_profile = next(
        column
        for column in profile.columns
        if column.name == "age"
    )

    assert age_profile.missing_count == 1
    assert age_profile.missing_ratio == 0.25
    assert age_profile.non_null_count == 3
    assert age_profile.statistics["min"] == 25.0
    assert age_profile.statistics["max"] == 40.0
    assert age_profile.statistics["median"] == 30.0


def test_profile_dataframe_detects_duplicate_rows() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 2],
            "name": ["Alice", "Bob", "Bob"],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="duplicates.csv",
        settings=Settings(),
    )

    assert profile.duplicate_rows == 1

    duplicate_issues = [
        issue
        for issue in profile.issues
        if issue.code == "DUPLICATE_ROWS"
    ]

    assert len(duplicate_issues) == 1
    assert duplicate_issues[0].severity == "warning"


def test_profile_dataframe_builds_column_metadata() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "salary": [50000, 51000, 52000, 53000],
            "active": [True, False, True, True],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="employees.csv",
        settings=Settings(),
    )

    assert len(profile.column_metadata) == 3

    customer_id_metadata = next(
        column
        for column in profile.column_metadata
        if column["column_name"] == "customer_id"
    )

    assert customer_id_metadata["logical_type"] == "numeric"
    assert customer_id_metadata["null_count"] == 0
    assert customer_id_metadata["unique_count"] == 4
    assert customer_id_metadata["unique_ratio"] == 1.0

    active_metadata = next(
        column
        for column in profile.column_metadata
        if column["column_name"] == "active"
    )

    assert active_metadata["logical_type"] == "boolean"


def test_complete_profile_pipeline() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 2, 4, 5],
            "age": [25, -10, 35, 40, 29],
            "salary": [
                50000,
                52000,
                51000,
                53000,
                1000000,
            ],
            "email": [
                "john@test.com",
                "bad-email",
                "alice@test.com",
                "bob@test.com",
                "mary@test.com",
            ],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    assert profile.filename == "customers.csv"
    assert profile.row_count == 5
    assert profile.column_count == 4
    assert len(profile.columns) == 4

    assert len(profile.column_metadata) == 4
    assert len(profile.business_rules) == 4
    assert len(profile.recommendations) > 0

    rules_by_column = {
        rule["column"]: rule
        for rule in profile.business_rules
    }

    assert rules_by_column["customer_id"]["passed"] is False
    assert rules_by_column["customer_id"]["violations"] == 1

    assert rules_by_column["age"]["passed"] is False
    assert rules_by_column["age"]["violations"] == 1

    assert rules_by_column["salary"]["passed"] is True
    assert rules_by_column["salary"]["violations"] == 0

    assert rules_by_column["email"]["passed"] is False
    assert rules_by_column["email"]["violations"] == 1

    assert any(
        "email" in recommendation.lower()
        for recommendation in profile.recommendations
    )

    assert isinstance(profile.ml_anomalies, list)
    assert len(profile.ml_anomalies) >= 1

    anomaly_rows = {
        anomaly["row_index"]
        for anomaly in profile.ml_anomalies
    }

    assert 4 in anomaly_rows


def test_profile_pipeline_handles_text_only_dataset() -> None:
    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "department": ["Engineering", "Sales", "Finance"],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="departments.csv",
        settings=Settings(),
    )

    assert profile.row_count == 3
    assert profile.column_count == 2
    assert len(profile.column_metadata) == 2
    assert profile.ml_anomalies == []