from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy.orm import Session

from app.db.models import Dataset
from app.db.session import get_db
from app.services.cleaning_execution import (
    preview_cleaning_execution,
)

router = APIRouter(tags=["Cleaning"])


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
                "cleaning preview."
            ),
        )

    return dataset


def _resolve_storage_path(
    dataset: Dataset,
) -> Path:
    storage_path = Path(
        dataset.storage_path
    )

    if not storage_path.is_absolute():
        storage_path = (
            Path.cwd() / storage_path
        )

    storage_path = storage_path.resolve()

    if not storage_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "The original uploaded CSV file "
                "could not be found."
            ),
        )

    if not storage_path.is_file():
        raise HTTPException(
            status_code=500,
            detail=(
                "The stored dataset path is not "
                "a valid file."
            ),
        )

    return storage_path


def _load_stored_dataframe(
    dataset: Dataset,
) -> pd.DataFrame:
    storage_path = _resolve_storage_path(
        dataset
    )

    try:
        return pd.read_csv(
            storage_path,
        )
    except pd.errors.EmptyDataError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "The stored CSV file does not "
                "contain readable data."
            ),
        ) from exc
    except pd.errors.ParserError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "The stored CSV file could not "
                "be parsed."
            ),
        ) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "The stored CSV file encoding "
                "could not be read."
            ),
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The stored CSV file could not "
                "be opened."
            ),
        ) from exc


@router.post(
    "/datasets/{dataset_id}/cleaning-preview",
    response_model=dict[str, Any],
)
def create_cleaning_preview(
    dataset_id: str,
    request: Request,
    preview_limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description=(
            "Maximum number of cleaned rows "
            "returned in the preview."
        ),
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Simulate safe cleaning operations without changing the original file.

    Automatically applied preview operations:
    - remove exact duplicate rows;
    - fill numeric missing values with the median;
    - fill non-numeric missing values with the mode.

    Business-rule violations and statistical outliers are retained and
    returned as manual-review actions.
    """
    dataset = _get_ready_dataset(
        dataset_id=dataset_id,
        db=db,
    )

    dataframe = _load_stored_dataframe(
        dataset
    )

    settings = (
        request.app.state.settings
    )

    try:
        preview = (
            preview_cleaning_execution(
                dataframe=dataframe,
                filename=(
                    dataset.original_filename
                ),
                settings=settings,
                preview_limit=preview_limit,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The cleaning preview could not "
                "be generated."
            ),
        ) from exc

    return {
        "dataset_id": dataset.id,
        "source_file": (
            dataset.original_filename
        ),
        "source_modified": False,
        **preview,
    }