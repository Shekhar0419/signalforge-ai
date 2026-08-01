import json

import pandas as pd
import pytest

from app.core.config import Settings
from app.services.copilot_context import (
    build_copilot_context,
    build_copilot_prompt,
)
from app.services.profiling import profile_dataframe


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


def test_build_copilot_context() -> None:
    profile = _build_profile()

    context = build_copilot_context(
        profile
    )

    assert context["dataset"]["filename"] == (
        "customers.csv"
    )

    assert context["dataset"]["row_count"] == 5
    assert context["dataset"]["column_count"] == 4

    assert isinstance(
        context["quality_issues"],
        list,
    )

    assert isinstance(
        context["columns"],
        list,
    )

    assert len(context["columns"]) == 4

    column_names = {
        column["name"]
        for column in context["columns"]
    }

    assert column_names == {
        "customer_id",
        "age",
        "salary",
        "email",
    }


def test_context_excludes_preview_rows() -> None:
    profile = _build_profile()

    context = build_copilot_context(
        profile
    )

    serialized = json.dumps(
        context,
        default=str,
    )

    assert "preview_rows" not in serialized
    assert "john@example.com" not in serialized
    assert "alice@example.com" not in serialized


def test_build_copilot_prompt() -> None:
    profile = _build_profile()

    prompt = build_copilot_prompt(
        profile=profile,
        question=(
            "Which columns should I clean first?"
        ),
    )

    assert (
        "You are SignalForge AI"
        in prompt
    )

    assert "customers.csv" in prompt
    assert "reliability_score" in prompt
    assert "Which columns should I clean first?" in prompt

    assert "john@example.com" not in prompt


def test_prompt_rejects_empty_question() -> None:
    profile = _build_profile()

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        build_copilot_prompt(
            profile=profile,
            question="   ",
        )