from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.models.schemas import DatasetProfile
from app.services.profiling import profile_dataframe

router = APIRouter(tags=["Datasets"])


@router.post("/datasets/profile", response_model=DatasetProfile)
async def profile_dataset(
    request: Request,
    file: UploadFile = File(...),
) -> DatasetProfile:
    settings = request.app.state.settings
    filename = file.filename or "uploaded.csv"

    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV files are supported in Phase 1.")

    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_mb} MB limit.",
        )

    try:
        dataframe = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to parse CSV: {exc}") from exc

    return profile_dataframe(dataframe, filename, settings)
