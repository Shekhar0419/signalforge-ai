from pathlib import Path

import pandas as pd

from app.core.config import Settings
from app.db.session import SessionLocal
from app.services.dataset_manager import process_stored_dataset
from app.services.upload_service import StoredDataset


def test_process_stored_dataset(
    reset_database,
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "salary": [100, 200, 300],
        }
    )

    storage_path = tmp_path / "employees_uuid.csv"
    dataframe.to_csv(storage_path, index=False)

    stored_dataset = StoredDataset(
        original_filename="employees.csv",
        stored_filename="employees_uuid.csv",
        storage_path=storage_path,
        file_size_bytes=storage_path.stat().st_size,
        dataframe=dataframe,
    )

    settings = Settings()

    with SessionLocal() as db:
        processed = process_stored_dataset(
            stored_dataset=stored_dataset,
            settings=settings,
            db=db,
        )

        assert processed.dataset.original_filename == "employees.csv"
        assert processed.dataset.stored_filename == "employees_uuid.csv"
        assert processed.dataset.status == "READY"
        assert processed.dataset.processed_at is not None

        assert processed.analysis.dataset_id == processed.dataset.id
        assert processed.analysis.row_count == 3
        assert processed.analysis.column_count == 3

        assert processed.profile.row_count == 3
        assert processed.profile.column_count == 3