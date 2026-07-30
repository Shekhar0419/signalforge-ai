from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import Dataset, DatasetAnalysis
from app.db.session import get_db
from app.models.schemas import (
    DatasetProfile,
    DatasetProfileResponse,
    DatasetSummary,
)
from app.services.dataset_manager import process_stored_dataset
from app.services.upload_service import store_uploaded_csv

router = APIRouter(tags=["Datasets"])


@router.post(
    "/datasets/profile",
    response_model=DatasetProfileResponse,
)
async def profile_dataset(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DatasetProfileResponse:
    settings = request.app.state.settings

    stored_dataset = await store_uploaded_csv(
        file=file,
        settings=settings,
    )

    processed = process_stored_dataset(
        stored_dataset=stored_dataset,
        settings=settings,
        db=db,
    )

    return DatasetProfileResponse(
        dataset_id=processed.dataset.id,
        created_at=processed.dataset.uploaded_at,
        **processed.profile.model_dump(),
    )


@router.get(
    "/datasets",
    response_model=list[DatasetSummary],
)
def list_datasets(
    db: Session = Depends(get_db),
) -> list[DatasetSummary]:
    records = db.scalars(
        select(DatasetAnalysis).order_by(
            desc(DatasetAnalysis.created_at)
        )
    ).all()

    return [
        DatasetSummary(
            id=record.dataset_id,
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
) -> DatasetProfileResponse:
    dataset = db.get(Dataset, dataset_id)

    if dataset is None or dataset.analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset analysis not found.",
        )

    profile = DatasetProfile.model_validate(
        dataset.analysis.profile_json
    )

    return DatasetProfileResponse(
        dataset_id=dataset.id,
        created_at=dataset.uploaded_at,
        **profile.model_dump(),
    )