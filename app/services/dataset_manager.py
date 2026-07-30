from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Dataset, DatasetAnalysis
from app.models.schemas import DatasetProfile
from app.services.profiling import profile_dataframe
from app.services.upload_service import (
    StoredDataset,
    delete_stored_dataset,
)


@dataclass
class ProcessedDataset:
    dataset: Dataset
    analysis: DatasetAnalysis
    profile: DatasetProfile


def process_stored_dataset(
    stored_dataset: StoredDataset,
    settings: Settings,
    db: Session,
) -> ProcessedDataset:
    """
    Register, profile, score, and persist an uploaded dataset.

    The API route should only handle HTTP concerns. This service owns the
    application workflow and database transaction.
    """
    dataset = Dataset(
        id=str(uuid4()),
        original_filename=stored_dataset.original_filename,
        stored_filename=stored_dataset.stored_filename,
        storage_path=str(stored_dataset.storage_path),
        file_size_bytes=stored_dataset.file_size_bytes,
        status="PROCESSING",
    )

    try:
        db.add(dataset)
        db.flush()

        profile = profile_dataframe(
            dataframe=stored_dataset.dataframe,
            filename=stored_dataset.original_filename,
            settings=settings,
        )

        analysis = DatasetAnalysis(
            id=str(uuid4()),
            dataset_id=dataset.id,
            filename=stored_dataset.original_filename,
            file_size_bytes=stored_dataset.file_size_bytes,
            row_count=profile.row_count,
            column_count=profile.column_count,
            duplicate_rows=profile.duplicate_rows,
            reliability_score=profile.reliability_score,
            profile_json=profile.model_dump(mode="json"),
        )

        dataset.status = "READY"
        dataset.processed_at = datetime.now(timezone.utc)

        db.add(analysis)
        db.commit()

        db.refresh(dataset)
        db.refresh(analysis)

        return ProcessedDataset(
            dataset=dataset,
            analysis=analysis,
            profile=profile,
        )

    except Exception:
        db.rollback()
        delete_stored_dataset(stored_dataset.storage_path)
        raise