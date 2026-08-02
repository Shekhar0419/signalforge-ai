from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Dataset, DatasetAnalysis
from app.models.schemas import DatasetProfile
from app.services.cleaned_dataset import (
    build_cleaned_dataframe,
)
from app.services.profiling import (
    profile_dataframe,
)


@dataclass(frozen=True)
class SavedDatasetVersion:
    dataset: Dataset
    analysis: DatasetAnalysis
    profile: DatasetProfile
    source_dataset_id: str
    root_dataset_id: str


class DatasetVersioningError(RuntimeError):
    """Raised when a cleaned dataset version cannot be saved."""


def _resolve_storage_path(
    dataset: Dataset,
) -> Path:
    """
    Resolve and validate the original stored CSV path.
    """
    storage_path = Path(
        dataset.storage_path
    )

    if not storage_path.is_absolute():
        storage_path = (
            Path.cwd() / storage_path
        )

    storage_path = storage_path.resolve()

    if not storage_path.exists():
        raise DatasetVersioningError(
            "The source CSV file could not be found."
        )

    if not storage_path.is_file():
        raise DatasetVersioningError(
            "The source dataset path is not a valid file."
        )

    return storage_path


def _load_source_dataframe(
    dataset: Dataset,
) -> pd.DataFrame:
    """
    Load the stored source CSV into a dataframe.
    """
    storage_path = _resolve_storage_path(
        dataset
    )

    try:
        return pd.read_csv(
            storage_path
        )
    except pd.errors.EmptyDataError as exc:
        raise DatasetVersioningError(
            "The source CSV file does not contain readable data."
        ) from exc
    except pd.errors.ParserError as exc:
        raise DatasetVersioningError(
            "The source CSV file could not be parsed."
        ) from exc
    except UnicodeDecodeError as exc:
        raise DatasetVersioningError(
            "The source CSV encoding could not be read."
        ) from exc
    except OSError as exc:
        raise DatasetVersioningError(
            "The source CSV file could not be opened."
        ) from exc


def _load_source_profile(
    dataset: Dataset,
) -> DatasetProfile:
    """
    Validate and load the saved source profile.
    """
    if dataset.analysis is None:
        raise DatasetVersioningError(
            "The source dataset does not have an analysis."
        )

    try:
        return DatasetProfile.model_validate(
            dataset.analysis.profile_json
        )
    except Exception as exc:
        raise DatasetVersioningError(
            "The source dataset profile could not be loaded."
        ) from exc


def _get_root_dataset_id(
    dataset: Dataset,
) -> str:
    """
    Return the original/root dataset ID for this lineage.

    Cleaned versions are stored as children of the root dataset so that
    all versions can be queried as one family.
    """
    return (
        dataset.parent_dataset_id
        or dataset.id
    )


def _get_next_version_number(
    root_dataset_id: str,
    db: Session,
) -> int:
    """
    Find the highest version in the dataset lineage and return the next one.
    """
    current_max = db.scalar(
        select(
            func.max(
                Dataset.version_number
            )
        ).where(
            or_(
                Dataset.id
                == root_dataset_id,
                Dataset.parent_dataset_id
                == root_dataset_id,
            )
        )
    )

    return int(
        current_max or 1
    ) + 1


def _safe_filename_stem(
    filename: str,
) -> str:
    stem = Path(
        filename
    ).stem.strip()

    if not stem:
        stem = "dataset"

    safe_stem = "".join(
        character
        if (
            character.isalnum()
            or character in {
                "-",
                "_",
            }
        )
        else "_"
        for character in stem
    )

    return safe_stem


def _build_version_filenames(
    source_filename: str,
    version_number: int,
) -> tuple[str, str]:
    """
    Build the user-facing and internally stored filenames.
    """
    safe_stem = _safe_filename_stem(
        source_filename
    )

    original_filename = (
        f"{safe_stem}_v"
        f"{version_number}_cleaned.csv"
    )

    stored_filename = (
        f"{uuid4()}.csv"
    )

    return (
        original_filename,
        stored_filename,
    )


def _write_cleaned_csv(
    dataframe: pd.DataFrame,
    source_storage_path: Path,
    stored_filename: str,
) -> Path:
    """
    Save the cleaned dataframe next to the source file.

    The original file is never overwritten.
    """
    storage_directory = (
        source_storage_path.parent
    )

    storage_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        storage_directory
        / stored_filename
    )

    try:
        dataframe.to_csv(
            destination,
            index=False,
        )
    except OSError as exc:
        raise DatasetVersioningError(
            "The cleaned CSV file could not be saved."
        ) from exc

    return destination.resolve()


def save_cleaned_dataset_version(
    source_dataset: Dataset,
    settings: Settings,
    db: Session,
) -> SavedDatasetVersion:
    """
    Create and persist a cleaned child version of an existing dataset.

    Safe automatic operations:
    - remove exact duplicate rows;
    - fill numeric missing values with the median;
    - fill non-numeric missing values with the mode.

    Business-rule violations, outliers, and ML anomalies are preserved
    because they require domain review.
    """
    if (
        source_dataset.status
        != "READY"
    ):
        raise DatasetVersioningError(
            "The source dataset is not ready."
        )

    source_profile = (
        _load_source_profile(
            source_dataset
        )
    )

    source_storage_path = (
        _resolve_storage_path(
            source_dataset
        )
    )

    source_dataframe = (
        _load_source_dataframe(
            source_dataset
        )
    )

    cleaned_dataframe = (
        build_cleaned_dataframe(
            dataframe=source_dataframe,
            profile=source_profile,
        )
    )

    root_dataset_id = (
        _get_root_dataset_id(
            source_dataset
        )
    )

    version_number = (
        _get_next_version_number(
            root_dataset_id=root_dataset_id,
            db=db,
        )
    )

    (
        cleaned_original_filename,
        cleaned_stored_filename,
    ) = _build_version_filenames(
        source_filename=(
            source_dataset.original_filename
        ),
        version_number=version_number,
    )

    cleaned_storage_path: Path | None = None

    try:
        cleaned_storage_path = (
            _write_cleaned_csv(
                dataframe=cleaned_dataframe,
                source_storage_path=(
                    source_storage_path
                ),
                stored_filename=(
                    cleaned_stored_filename
                ),
            )
        )

        file_size_bytes = (
            cleaned_storage_path.stat().st_size
        )

        profile = profile_dataframe(
            dataframe=cleaned_dataframe,
            filename=(
                cleaned_original_filename
            ),
            settings=settings,
        )

        new_dataset = Dataset(
            id=str(uuid4()),
            parent_dataset_id=(
                root_dataset_id
            ),
            version_number=(
                version_number
            ),
            version_type="CLEANED",
            original_filename=(
                cleaned_original_filename
            ),
            stored_filename=(
                cleaned_stored_filename
            ),
            storage_path=str(
                cleaned_storage_path
            ),
            file_size_bytes=(
                file_size_bytes
            ),
            status="READY",
            processed_at=datetime.now(
                timezone.utc
            ),
        )

        db.add(
            new_dataset
        )

        db.flush()

        new_analysis = DatasetAnalysis(
            id=str(uuid4()),
            dataset_id=(
                new_dataset.id
            ),
            filename=(
                cleaned_original_filename
            ),
            file_size_bytes=(
                file_size_bytes
            ),
            row_count=(
                profile.row_count
            ),
            column_count=(
                profile.column_count
            ),
            duplicate_rows=(
                profile.duplicate_rows
            ),
            reliability_score=(
                profile.reliability_score
            ),
            profile_json=(
                profile.model_dump(
                    mode="json"
                )
            ),
        )

        db.add(
            new_analysis
        )

        db.commit()

        db.refresh(
            new_dataset
        )

        db.refresh(
            new_analysis
        )

        return SavedDatasetVersion(
            dataset=new_dataset,
            analysis=new_analysis,
            profile=profile,
            source_dataset_id=(
                source_dataset.id
            ),
            root_dataset_id=(
                root_dataset_id
            ),
        )

    except Exception:
        db.rollback()

        if (
            cleaned_storage_path
            is not None
            and cleaned_storage_path.exists()
        ):
            try:
                cleaned_storage_path.unlink()
            except OSError:
                pass

        raise