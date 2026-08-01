import pandas as pd

from app.core.config import Settings
from app.services.ai_summary import generate_dataset_summary
from app.services.profiling import profile_dataframe


def test_generate_dataset_summary():
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 2],
            "age": [25, -5, 40],
            "salary": [50000, 51000, 1000000],
            "email": [
                "john@test.com",
                "bad-email",
                "alice@test.com",
            ],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    summary = generate_dataset_summary(profile)

    assert isinstance(summary, str)
    assert "rows" in summary
    assert "columns" in summary
    assert "reliability" in summary.lower()
    assert "Recommended next steps" in summary