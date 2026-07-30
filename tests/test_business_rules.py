import pandas as pd

from app.services.business_rules import (
    evaluate_business_rules,
)


def test_business_rules():

    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 2],
            "age": [20, -5, 30],
            "salary": [1000, 0, 3000],
            "email": [
                "john@test.com",
                "bad-email",
                "jane@test.com",
            ],
        }
    )

    rules = evaluate_business_rules(df)

    assert len(rules) == 4

    assert rules[0]["violations"] == 1
    assert rules[1]["violations"] == 1
    assert rules[2]["violations"] == 1
    assert rules[3]["violations"] == 1