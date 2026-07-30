from io import BytesIO
from uuid import uuid4
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import DatasetAnalysis
from app.db.session import get_db
from app.models.schemas import DatasetProfile, DatasetProfileResponse, DatasetSummary
from app.services.profiling import profile_dataframe

router = APIRouter(tags=["Datasets"])

@router.post("/datasets/profile", response_model=DatasetProfileResponse)
async def profile_dataset(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = request.app.state.settings
    filename = file.filename or "uploaded.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(415, "Only CSV files are supported.")
    content = await file.read()
    if not content:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "File exceeds upload limit.")
    try:
        dataframe = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise HTTPException(400, f"Unable to parse CSV: {exc}") from exc

    profile = profile_dataframe(dataframe, filename, settings)
    record = DatasetAnalysis(
        id=str(uuid4()),
        filename=filename,
        file_size_bytes=len(content),
        row_count=profile.row_count,
        column_count=profile.column_count,
        duplicate_rows=profile.duplicate_rows,
        reliability_score=profile.reliability_score,
        profile_json=profile.model_dump(mode="json"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return DatasetProfileResponse(dataset_id=record.id, created_at=record.created_at, **profile.model_dump())

@router.get("/datasets", response_model=list[DatasetSummary])
def list_datasets(db: Session = Depends(get_db)):
    records = db.scalars(select(DatasetAnalysis).order_by(desc(DatasetAnalysis.created_at))).all()
    return [
        DatasetSummary(
            id=r.id, filename=r.filename, row_count=r.row_count,
            column_count=r.column_count, reliability_score=r.reliability_score,
            created_at=r.created_at
        )
        for r in records
    ]

@router.get("/datasets/{dataset_id}", response_model=DatasetProfileResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    record = db.get(DatasetAnalysis, dataset_id)
    if record is None:
        raise HTTPException(404, "Dataset analysis not found.")
    profile = DatasetProfile.model_validate(record.profile_json)
    return DatasetProfileResponse(dataset_id=record.id, created_at=record.created_at, **profile.model_dump())
