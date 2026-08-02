import pandas as pd

from app.core.config import Settings
from app.services.cleaning_plan import (
    build_cleaning_plan,
)
from app.services.profiling import (
    profile_dataframe,
)


def _build_profile():
    dataframe = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                2,
                4,
                5,
            ],
            "age": [
                25,
                -5,
                35,
                None,
                42,
            ],
            "salary": [
                50000,
                52000,
                51000,
                53000,
                1000000,
            ],
            "email": [
                "john@example.com",
                "bad-email",
                "alice@example.com",
                "bob@example.com",
                "mary@example.com",
            ],
        }
    )

    return profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )


def test_build_cleaning_plan() -> None:
    profile = _build_profile()

    plan = build_cleaning_plan(
        profile
    )

    assert plan["action_count"] > 0

    assert (
        plan["predicted_reliability_score"]
        >= plan["current_reliability_score"]
    )

    categories = {
        action["category"]
        for action in plan["actions"]
    }

    assert "business_rules" in categories
    assert "missing_values" in categories
    assert "outliers" in categories


def test_cleaning_plan_contains_code() -> None:
    profile = _build_profile()

    plan = build_cleaning_plan(
        profile
    )

    for action in plan["actions"]:
        assert action["pandas_code"]
        assert action["pyspark_code"]
        assert action["sql_code"]


def test_cleaning_plan_uses_priority_order() -> None:
    profile = _build_profile()

    plan = build_cleaning_plan(
        profile
    )

    priorities = [
        action["priority"]
        for action in plan["actions"]
    ]

    assert priorities == sorted(
        priorities
    )


def test_clean_profile_has_safe_plan() -> None:
    dataframe = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [10, 20, 30],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="clean.csv",
        settings=Settings(),
    )

    plan = build_cleaning_plan(
        profile
    )

    assert plan["predicted_reliability_score"] <= 100
    assert isinstance(
        plan["actions"],
        list,
    )