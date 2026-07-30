from io import BytesIO

def test_profile_history_and_detail(client):
    csv_data = "machine_id,temperature\nM1,71\nM2,72\nM2,72\n"
    response = client.post(
        "/api/v1/datasets/profile",
        files={"file": ("machines.csv", BytesIO(csv_data.encode()), "text/csv")},
    )
    assert response.status_code == 200
    dataset_id = response.json()["dataset_id"]

    history = client.get("/api/v1/datasets")
    assert history.status_code == 200
    assert history.json()[0]["id"] == dataset_id

    detail = client.get(f"/api/v1/datasets/{dataset_id}")
    assert detail.status_code == 200
    assert detail.json()["filename"] == "machines.csv"

def test_ready_database(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"
