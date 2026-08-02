import pandas as pd

from app.core.config import Settings
from app.services.cleaned_dataset import (
    build_cleaned_dataframe,
    dataframe_to_csv_bytes,
)
from app.services.profiling import (
    profile_dataframe,
)


def _build_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                3,
                4,
                4,
            ],
            "age": [
                25,
                None,
                35,
                42,
                42,
            ],
            "city": [
                "St. Louis",
                "Chicago",
                None,
                "Austin",
                "Austin",
            ],
            "salary": [
                50000,
                52000,
                51000,
                53000,
                53000,
            ],
        }
    )


def test_build_cleaned_dataframe() -> None:
    dataframe = _build_dataframe()

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    cleaned = build_cleaned_dataframe(
        dataframe=dataframe,
        profile=profile,
    )

    assert len(dataframe) == 5
    assert len(cleaned) == 4

    assert int(
        cleaned.duplicated().sum()
    ) == 0

    assert int(
        cleaned.isna().sum().sum()
    ) == 0


def test_original_dataframe_is_not_modified() -> None:
    dataframe = _build_dataframe()

    original_copy = dataframe.copy(
        deep=True,
    )

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    build_cleaned_dataframe(
        dataframe=dataframe,
        profile=profile,
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_copy,
    )


def test_numeric_missing_value_uses_median() -> None:
    dataframe = _build_dataframe()

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    cleaned = build_cleaned_dataframe(
        dataframe=dataframe,
        profile=profile,
    )

    assert cleaned["age"].isna().sum() == 0

    assert 35.0 in cleaned["age"].tolist()


def test_text_missing_value_uses_mode() -> None:
    dataframe = _build_dataframe()

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    cleaned = build_cleaned_dataframe(
        dataframe=dataframe,
        profile=profile,
    )

    assert cleaned["city"].isna().sum() == 0

    assert "Austin" in cleaned["city"].tolist()


def test_dataframe_to_csv_bytes() -> None:
    dataframe = _build_dataframe()

    profile = profile_dataframe(
        dataframe=dataframe,
        filename="customers.csv",
        settings=Settings(),
    )

    cleaned = build_cleaned_dataframe(
        dataframe=dataframe,
        profile=profile,
    )

    csv_bytes = dataframe_to_csv_bytes(
        cleaned,
    )

    assert isinstance(
        csv_bytes,
        bytes,
    )

    assert len(csv_bytes) > 0

    csv_text = csv_bytes.decode(
        "utf-8",
    )

    assert "customer_id,age,city,salary" in csv_text
    assert "St. Louis" in csv_text