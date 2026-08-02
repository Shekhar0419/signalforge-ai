from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy.orm import Session

from app.db.models import Dataset
from app.db.session import get_db
from app.services.versioning import (
    DatasetVersioningError,
    save_cleaned_dataset_version,
)

router = APIRouter(tags=["Versioning"])


def _get_ready_dataset(
    dataset_id: str,
    db: Session,
) -> Dataset:
    dataset = db.get(
        Dataset,
        dataset_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset analysis not found.",
        )

    if (
        dataset.analysis is None
        or dataset.status != "READY"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "The dataset is not ready for "
                "version creation."
            ),
        )

    return dataset


@router.post(
    "/datasets/{dataset_id}/save-cleaned-version",
    response_model=dict[str, Any],
)
def create_cleaned_dataset_version(
    dataset_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    source_dataset = _get_ready_dataset(
        dataset_id=dataset_id,
        db=db,
    )

    settings = request.app.state.settings

    try:
        saved = save_cleaned_dataset_version(
            source_dataset=source_dataset,
            settings=settings,
            db=db,
        )
    except DatasetVersioningError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The cleaned dataset version "
                "could not be saved."
            ),
        ) from exc

    return {
        "dataset_id": saved.dataset.id,
        "source_dataset_id": (
            saved.source_dataset_id
        ),
        "parent_dataset_id": (
            saved.dataset.parent_dataset_id
        ),
        "root_dataset_id": (
            saved.root_dataset_id
        ),
        "version_number": (
            saved.dataset.version_number
        ),
        "version_type": (
            saved.dataset.version_type
        ),
        "filename": (
            saved.dataset.original_filename
        ),
        "row_count": (
            saved.profile.row_count
        ),
        "column_count": (
            saved.profile.column_count
        ),
        "duplicate_rows": (
            saved.profile.duplicate_rows
        ),
        "reliability_score": (
            saved.profile.reliability_score
        ),
        "created_at": (
            saved.dataset.uploaded_at
        ),
    }