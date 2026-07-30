from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import DatasetAnalysis
from app.db.session import get_db
from app.models.schemas import (
    DatasetProfile,
    DatasetProfileResponse,
    DatasetSummary,
)
from app.services.profiling import profile_dataframe
from app.services.upload_service import (
    delete_stored_dataset,
    store_uploaded_csv,
)

router = APIRouter(tags=["Datasets"])


@router.post(
    "/datasets/profile",
    response_model=DatasetProfileResponse,
)
async def profile_dataset(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    settings = request.app.state.settings

    stored_dataset = await store_uploaded_csv(
        file=file,
        settings=settings,
    )

    try:
        profile = profile_dataframe(
            dataframe=stored_dataset.dataframe,
            filename=stored_dataset.original_filename,
            settings=settings,
        )

        record = DatasetAnalysis(
            id=str(uuid4()),
            filename=stored_dataset.original_filename,
            file_size_bytes=stored_dataset.file_size_bytes,
            row_count=profile.row_count,
            column_count=profile.column_count,
            duplicate_rows=profile.duplicate_rows,
            reliability_score=profile.reliability_score,
            profile_json=profile.model_dump(mode="json"),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

    except Exception:
        db.rollback()
        delete_stored_dataset(stored_dataset.storage_path)
        raise

    return DatasetProfileResponse(
        dataset_id=record.id,
        created_at=record.created_at,
        **profile.model_dump(),
    )


@router.get(
    "/datasets",
    response_model=list[DatasetSummary],
)
def list_datasets(
    db: Session = Depends(get_db),
):
    records = db.scalars(
        select(DatasetAnalysis).order_by(
            desc(DatasetAnalysis.created_at)
        )
    ).all()

    return [
        DatasetSummary(
            id=record.id,
            filename=record.filename,
            row_count=record.row_count,
            column_count=record.column_count,
            reliability_score=record.reliability_score,
            created_at=record.created_at,
        )
        for record in records
    ]


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetProfileResponse,
)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    record = db.get(DatasetAnalysis, dataset_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset analysis not found.",
        )

    profile = DatasetProfile.model_validate(
        record.profile_json
    )

    return DatasetProfileResponse(
        dataset_id=record.id,
        created_at=record.created_at,
        **profile.model_dump(),
    )