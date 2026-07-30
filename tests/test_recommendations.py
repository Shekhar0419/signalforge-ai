from app.services.recommendations import (
    generate_recommendations,
)


def test_generate_recommendations():

    metadata = [
        {
            "column_name": "age",
            "logical_type": "numeric",
            "null_ratio": 0.30,
            "unique_ratio": 0.90,
        },
        {
            "column_name": "email",
            "logical_type": "text",
            "null_ratio": 0.05,
            "unique_ratio": 1.0,
        },
    ]

    rules = [
        {
            "column": "email",
            "rule": "Valid email format",
            "passed": False,
            "violations": 2,
        }
    ]

    recommendations = generate_recommendations(
        metadata,
        rules,
    )

    assert len(recommendations) >= 3

    assert any(
        "median" in recommendation.lower()
        for recommendation in recommendations
    )

    assert any(
        "email" in recommendation.lower()
        for recommendation in recommendations
    )