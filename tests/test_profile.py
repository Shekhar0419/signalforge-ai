from io import BytesIO

from fastapi.testclient import TestClient
from app.main import app


def test_profile_csv() -> None:
    csv_data = (
        "machine_id,temperature,status\n"
        "M-1,71.2,running\n"
        "M-2,72.1,running\n"
        "M-3,,stopped\n"
        "M-3,,stopped\n"
        "M-4,150.0,running\n"
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/datasets/profile",
            files={"file": ("machines.csv", BytesIO(csv_data.encode()), "text/csv")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 5
    assert body["column_count"] == 3
    assert body["duplicate_rows"] == 1
    assert 0 <= body["reliability_score"] <= 100
    assert any(issue["code"] == "DUPLICATE_ROWS" for issue in body["issues"])
