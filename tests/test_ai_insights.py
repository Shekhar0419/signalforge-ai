import json

import pandas as pd

from app.core.config import Settings
from app.services.ai_insights import (
    AIInsightResponse,
    build_insight_prompt,
    generate_fallback_insights,
)
from app.services.profiling import profile_dataframe


def _build_test_profile():
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

    return profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )


def test_generate_fallback_insights() -> None:
    profile = _build_test_profile()

    insights = generate_fallback_insights(
        profile
    )

    assert isinstance(
        insights,
        AIInsightResponse,
    )

    assert insights.provider == "fallback"

    assert "customers.csv" in (
        insights.executive_summary
    )

    assert "5 rows" in (
        insights.executive_summary
    )

    assert len(insights.root_causes) > 0
    assert len(insights.priority_actions) > 0
    assert insights.business_impact


def test_fallback_insights_explain_failed_rules() -> None:
    profile = _build_test_profile()

    insights = generate_fallback_insights(
        profile
    )

    combined_causes = " ".join(
        insights.root_causes
    ).lower()

    assert "customer_id" in combined_causes
    assert "age" in combined_causes
    assert "email" in combined_causes


def test_fallback_insights_include_anomaly_action() -> None:
    profile = _build_test_profile()

    insights = generate_fallback_insights(
        profile
    )

    combined_actions = " ".join(
        insights.priority_actions
    ).lower()

    if profile.ml_anomalies:
        assert "isolation forest" in combined_actions


def test_build_insight_prompt() -> None:
    profile = _build_test_profile()

    prompt = build_insight_prompt(
        profile
    )

    assert "AI data-reliability analyst" in prompt
    assert "executive_summary" in prompt
    assert "root_causes" in prompt
    assert "business_impact" in prompt
    assert "priority_actions" in prompt
    assert "customers.csv" in prompt

    json_start = prompt.index(
        "Dataset profile:\n"
    ) + len("Dataset profile:\n")

    profile_json = prompt[json_start:]

    parsed_context = json.loads(
        profile_json
    )

    assert parsed_context["row_count"] == 5
    assert parsed_context["column_count"] == 4
    assert "failed_business_rules" in parsed_context


def test_prompt_does_not_include_raw_records() -> None:
    profile = _build_test_profile()

    prompt = build_insight_prompt(
        profile
    )

    assert "john@test.com" not in prompt
    assert "alice@test.com" not in prompt
    assert "1000000" not in prompt