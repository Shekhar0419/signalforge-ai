from pathlib import Path

import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.models import Dataset
from app.db.session import get_db
from app.models.schemas import DatasetProfile
from app.services.cleaned_dataset import (
    build_cleaned_dataframe,
    dataframe_to_csv_bytes,
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
                "cleaned-file generation."
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


def _load_profile(
    dataset: Dataset,
) -> DatasetProfile:
    try:
        return DatasetProfile.model_validate(
            dataset.analysis.profile_json
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The stored dataset profile could not "
                "be loaded."
            ),
        ) from exc


def _build_cleaned_filename(
    original_filename: str,
) -> str:
    stem = Path(
        original_filename
    ).stem.strip()

    if not stem:
        stem = "dataset"

    safe_stem = "".join(
        character
        if (
            character.isalnum()
            or character in {"-", "_"}
        )
        else "_"
        for character in stem
    )

    return (
        f"{safe_stem}_cleaned.csv"
    )


@router.post(
    "/datasets/{dataset_id}/cleaned-file",
    response_class=Response,
    responses={
        200: {
            "content": {
                "text/csv": {}
            },
            "description": (
                "Download the safely cleaned CSV file."
            ),
        },
        404: {
            "description": (
                "Dataset analysis or source file not found."
            ),
        },
        409: {
            "description": (
                "Dataset is not ready."
            ),
        },
    },
)
def download_cleaned_file(
    dataset_id: str,
    db: Session = Depends(get_db),
) -> Response:
    dataset = _get_ready_dataset(
        dataset_id=dataset_id,
        db=db,
    )

    dataframe = _load_stored_dataframe(
        dataset
    )

    profile = _load_profile(
        dataset
    )

    try:
        cleaned = build_cleaned_dataframe(
            dataframe=dataframe,
            profile=profile,
        )

        csv_bytes = dataframe_to_csv_bytes(
            cleaned
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The cleaned CSV file could not "
                "be generated."
            ),
        ) from exc

    filename = _build_cleaned_filename(
        dataset.original_filename
    )

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
            "Cache-Control": "no-store",
        },
    )