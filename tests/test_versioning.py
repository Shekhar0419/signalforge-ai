from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Dataset, DatasetAnalysis
from app.db.session import SessionLocal
from app.services.dataset_manager import (
    process_stored_dataset,
)
from app.services.upload_service import (
    StoredDataset,
)
from app.services.versioning import (
    DatasetVersioningError,
    save_cleaned_dataset_version,
)


@pytest.fixture
def db_session() -> Session:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def _create_stored_dataset(
    tmp_path: Path,
) -> StoredDataset:
    dataframe = pd.DataFrame(
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

    storage_path = (
        tmp_path
        / "source_customers.csv"
    )

    dataframe.to_csv(
        storage_path,
        index=False,
    )

    return StoredDataset(
        original_filename=(
            "customers.csv"
        ),
        stored_filename=(
            "source_customers.csv"
        ),
        storage_path=storage_path,
        file_size_bytes=(
            storage_path.stat().st_size
        ),
        dataframe=dataframe,
    )


def _create_source_dataset(
    db_session: Session,
    tmp_path: Path,
) -> Dataset:
    stored_dataset = (
        _create_stored_dataset(
            tmp_path
        )
    )

    processed = (
        process_stored_dataset(
            stored_dataset=(
                stored_dataset
            ),
            settings=Settings(),
            db=db_session,
        )
    )

    return processed.dataset


def test_save_cleaned_dataset_version(
    db_session: Session,
    tmp_path: Path,
) -> None:
    source_dataset = (
        _create_source_dataset(
            db_session,
            tmp_path,
        )
    )

    saved = (
        save_cleaned_dataset_version(
            source_dataset=(
                source_dataset
            ),
            settings=Settings(),
            db=db_session,
        )
    )

    assert (
        saved.source_dataset_id
        == source_dataset.id
    )

    assert (
        saved.root_dataset_id
        == source_dataset.id
    )

    assert (
        saved.dataset.parent_dataset_id
        == source_dataset.id
    )

    assert (
        saved.dataset.version_number
        == 2
    )

    assert (
        saved.dataset.version_type
        == "CLEANED"
    )

    assert (
        saved.dataset.status
        == "READY"
    )

    assert (
        saved.profile.duplicate_rows
        == 0
    )

    assert all(
        column.missing_count == 0
        for column in (
            saved.profile.columns
        )
    )

    cleaned_path = Path(
        saved.dataset.storage_path
    )

    assert cleaned_path.exists()
    assert cleaned_path.is_file()

    cleaned_dataframe = (
        pd.read_csv(
            cleaned_path
        )
    )

    assert len(
        cleaned_dataframe
    ) == 4

    assert int(
        cleaned_dataframe
        .duplicated()
        .sum()
    ) == 0

    assert int(
        cleaned_dataframe
        .isna()
        .sum()
        .sum()
    ) == 0


def test_saved_version_is_persisted(
    db_session: Session,
    tmp_path: Path,
) -> None:
    source_dataset = (
        _create_source_dataset(
            db_session,
            tmp_path,
        )
    )

    saved = (
        save_cleaned_dataset_version(
            source_dataset=(
                source_dataset
            ),
            settings=Settings(),
            db=db_session,
        )
    )

    stored_dataset = (
        db_session.get(
            Dataset,
            saved.dataset.id,
        )
    )

    stored_analysis = (
        db_session.scalar(
            select(
                DatasetAnalysis
            ).where(
                DatasetAnalysis.dataset_id
                == saved.dataset.id
            )
        )
    )

    assert stored_dataset is not None
    assert stored_analysis is not None

    assert (
        stored_dataset.version_number
        == 2
    )

    assert (
        stored_analysis.row_count
        == 4
    )


def test_multiple_versions_increment_number(
    db_session: Session,
    tmp_path: Path,
) -> None:
    source_dataset = (
        _create_source_dataset(
            db_session,
            tmp_path,
        )
    )

    version_two = (
        save_cleaned_dataset_version(
            source_dataset=(
                source_dataset
            ),
            settings=Settings(),
            db=db_session,
        )
    )

    version_three = (
        save_cleaned_dataset_version(
            source_dataset=(
                version_two.dataset
            ),
            settings=Settings(),
            db=db_session,
        )
    )

    assert (
        version_two.dataset.version_number
        == 2
    )

    assert (
        version_three.dataset.version_number
        == 3
    )

    assert (
        version_three.dataset.parent_dataset_id
        == source_dataset.id
    )

    assert (
        version_three.root_dataset_id
        == source_dataset.id
    )


def test_source_file_is_not_modified(
    db_session: Session,
    tmp_path: Path,
) -> None:
    source_dataset = (
        _create_source_dataset(
            db_session,
            tmp_path,
        )
    )

    source_path = Path(
        source_dataset.storage_path
    )

    before_bytes = (
        source_path.read_bytes()
    )

    save_cleaned_dataset_version(
        source_dataset=(
            source_dataset
        ),
        settings=Settings(),
        db=db_session,
    )

    after_bytes = (
        source_path.read_bytes()
    )

    assert before_bytes == after_bytes


def test_versioning_rejects_unready_dataset(
    db_session: Session,
    tmp_path: Path,
) -> None:
    source_dataset = (
        _create_source_dataset(
            db_session,
            tmp_path,
        )
    )

    source_dataset.status = (
        "PROCESSING"
    )

    db_session.add(
        source_dataset
    )

    db_session.commit()

    with pytest.raises(
        DatasetVersioningError,
        match="not ready",
    ):
        save_cleaned_dataset_version(
            source_dataset=(
                source_dataset
            ),
            settings=Settings(),
            db=db_session,
        )


def test_versioning_rejects_missing_source_file(
    db_session: Session,
    tmp_path: Path,
) -> None:
    source_dataset = (
        _create_source_dataset(
            db_session,
            tmp_path,
        )
    )

    source_path = Path(
        source_dataset.storage_path
    )

    source_path.unlink()

    with pytest.raises(
        DatasetVersioningError,
        match="could not be found",
    ):
        save_cleaned_dataset_version(
            source_dataset=(
                source_dataset
            ),
            settings=Settings(),
            db=db_session,
        )