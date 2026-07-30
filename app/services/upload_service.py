from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.core.config import Settings


@dataclass
class StoredDataset:
    original_filename: str
    stored_filename: str
    storage_path: Path
    file_size_bytes: int
    dataframe: pd.DataFrame


def _safe_original_filename(filename: str | None) -> str:
    """
    Remove directory components supplied by a client.

    Example:
        ../../customers.csv -> customers.csv
    """
    safe_name = Path(filename or "uploaded.csv").name.strip()

    if not safe_name:
        return "uploaded.csv"

    return safe_name


def _validate_csv_filename(filename: str) -> None:
    if Path(filename).suffix.lower() != ".csv":
        raise HTTPException(
            status_code=415,
            detail="Only CSV files are supported.",
        )


def _validate_file_size(content: bytes, settings: Settings) -> None:
    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    maximum_bytes = settings.max_upload_mb * 1024 * 1024

    if len(content) > maximum_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.",
        )


def _parse_csv(content: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to parse CSV: {exc}",
        ) from exc


async def store_uploaded_csv(
    file: UploadFile,
    settings: Settings,
) -> StoredDataset:
    original_filename = _safe_original_filename(file.filename)

    _validate_csv_filename(original_filename)

    content = await file.read()
    _validate_file_size(content, settings)

    dataframe = _parse_csv(content)

    upload_directory = Path(settings.upload_directory)
    upload_directory.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4()}.csv"
    storage_path = upload_directory / stored_filename

    try:
        storage_path.write_bytes(content)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="The dataset could not be stored.",
        ) from exc

    return StoredDataset(
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=storage_path,
        file_size_bytes=len(content),
        dataframe=dataframe,
    )


def delete_stored_dataset(storage_path: Path) -> None:
    """
    Delete a stored file when later processing or persistence fails.
    """
    try:
        storage_path.unlink(missing_ok=True)
    except OSError:
        # File cleanup should not hide the original application error.
        pass