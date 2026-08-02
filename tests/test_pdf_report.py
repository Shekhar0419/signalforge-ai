import pandas as pd

from app.core.config import Settings
from app.services.pdf_report import (
    build_dataset_pdf_report,
)
from app.services.profiling import (
    profile_dataframe,
)


def test_build_dataset_pdf_report() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                2,
                4,
            ],
            "age": [
                25,
                None,
                35,
                42,
            ],
            "salary": [
                50000,
                52000,
                51000,
                1000000,
            ],
        }
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    pdf_bytes = build_dataset_pdf_report(
        profile=profile,
        dataset_id="dataset-123",
        created_at=pd.Timestamp(
            "2026-08-01T12:00:00"
        ).to_pydatetime(),
    )

    assert isinstance(
        pdf_bytes,
        bytes,
    )

    assert pdf_bytes.startswith(
        b"%PDF"
    )

    assert len(pdf_bytes) > 1000