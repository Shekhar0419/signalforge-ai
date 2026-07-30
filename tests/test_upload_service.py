from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_csv_is_saved_to_upload_directory(
    client: TestClient,
    tmp_path: Path,
) -> None:
    app.state.settings.upload_directory = str(tmp_path)

    csv_data = (
        "machine_id,temperature\n"
        "M-1,71.2\n"
        "M-2,72.1\n"
    )

    response = client.post(
        "/api/v1/datasets/profile",
        files={
            "file": (
                "machines.csv",
                BytesIO(csv_data.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    stored_files = list(tmp_path.glob("*.csv"))

    assert len(stored_files) == 1
    assert stored_files[0].read_text(encoding="utf-8") == csv_data


def test_rejects_non_csv_file(
    client: TestClient,
    tmp_path: Path,
) -> None:
    app.state.settings.upload_directory = str(tmp_path)

    response = client.post(
        "/api/v1/datasets/profile",
        files={
            "file": (
                "dataset.txt",
                BytesIO(b"sample text"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Only CSV files are supported."
    assert list(tmp_path.iterdir()) == []


def test_rejects_empty_csv(
    client: TestClient,
    tmp_path: Path,
) -> None:
    app.state.settings.upload_directory = str(tmp_path)

    response = client.post(
        "/api/v1/datasets/profile",
        files={
            "file": (
                "empty.csv",
                BytesIO(b""),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is empty."
    assert list(tmp_path.iterdir()) == []


def test_removes_path_components_from_filename(
    client: TestClient,
    tmp_path: Path,
) -> None:
    app.state.settings.upload_directory = str(tmp_path)

    response = client.post(
        "/api/v1/datasets/profile",
        files={
            "file": (
                "../../machines.csv",
                BytesIO(b"machine_id\nM-1\n"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "machines.csv"