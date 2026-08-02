from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.db.models import Dataset
from app.db.session import get_db
from app.services.version_compare import (
    VersionComparisonError,
    compare_dataset_versions,
)

router = APIRouter(
    tags=["Version Comparison"],
)


def _get_dataset_with_analysis(
    dataset_id: str,
    db: Session,
) -> Dataset:
    dataset = db.scalar(
        select(Dataset)
        .options(
            joinedload(
                Dataset.analysis,
            )
        )
        .where(
            Dataset.id == dataset_id,
        )
    )

    if (
        dataset is None
        or dataset.analysis is None
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Dataset analysis not found."
            ),
        )

    return dataset


@router.get(
    "/datasets/{first_dataset_id}/compare/{second_dataset_id}",
    response_model=dict,
)
def compare_versions(
    first_dataset_id: str,
    second_dataset_id: str,
    db: Session = Depends(get_db),
) -> dict:
    if (
        first_dataset_id
        == second_dataset_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Select two different dataset versions "
                "to compare."
            ),
        )

    first_dataset = (
        _get_dataset_with_analysis(
            dataset_id=first_dataset_id,
            db=db,
        )
    )

    second_dataset = (
        _get_dataset_with_analysis(
            dataset_id=second_dataset_id,
            db=db,
        )
    )

    try:
        return compare_dataset_versions(
            first_dataset=first_dataset,
            second_dataset=second_dataset,
        )
    except VersionComparisonError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The dataset versions could not "
                "be compared."
            ),
        ) from exc