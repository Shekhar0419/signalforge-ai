import pandas as pd
import pytest

from app.core.config import Settings
from app.models.copilot import (
    CopilotRequest,
    CopilotResponse,
)
from app.services.copilot import (
    answer_copilot_question,
    generate_fallback_answer,
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


def test_copilot_request_trims_question() -> None:
    request = CopilotRequest(
        question="  Which columns need attention?  "
    )

    assert request.question == (
        "Which columns need attention?"
    )


def test_copilot_request_rejects_blank_question() -> None:
    with pytest.raises(
        ValueError,
    ):
        CopilotRequest(
            question="   "
        )


def test_answer_cleaning_priority() -> None:
    profile = _build_profile()

    answer = generate_fallback_answer(
        profile=profile,
        question=(
            "Which columns should I clean first?"
        ),
    )

    lowered_answer = answer.lower()

    assert "age" in lowered_answer
    assert "email" in lowered_answer
    assert "customer_id" in lowered_answer


def test_answer_reliability_question() -> None:
    profile = _build_profile()

    answer = generate_fallback_answer(
        profile=profile,
        question=(
            "Why is the reliability score low?"
        ),
    )

    assert "reliability score" in answer.lower()
    assert str(
        round(
            profile.reliability_score,
            1,
        )
    ) in answer


def test_answer_anomaly_question() -> None:
    profile = _build_profile()

    answer = generate_fallback_answer(
        profile=profile,
        question="Explain the anomalies.",
    )

    assert "isolation forest" in answer.lower()


def test_answer_ml_readiness_question() -> None:
    profile = _build_profile()

    answer = generate_fallback_answer(
        profile=profile,
        question=(
            "Can I use this dataset for machine learning?"
        ),
    )

    assert (
        "production-ready" in answer.lower()
        or "experimentation" in answer.lower()
    )


def test_answer_copilot_question_response() -> None:
    profile = _build_profile()

    response = answer_copilot_question(
        dataset_id="dataset-123",
        profile=profile,
        question=(
            "Which columns should I clean first?"
        ),
    )

    assert isinstance(
        response,
        CopilotResponse,
    )

    assert response.dataset_id == (
        "dataset-123"
    )

    assert response.provider == "fallback"
    assert response.model is None
    assert response.answer


def test_fallback_rejects_empty_question() -> None:
    profile = _build_profile()

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        generate_fallback_answer(
            profile=profile,
            question="   ",
        )