from io import BytesIO


def _upload_dataset(
    client,
) -> str:
    csv_data = (
        "customer_id,age,salary,email\n"
        "1,25,50000,john@example.com\n"
        "2,-5,52000,bad-email\n"
        "2,35,51000,alice@example.com\n"
        "4,,53000,bob@example.com\n"
        "5,42,1000000,mary@example.com\n"
    )

    response = client.post(
        "/api/v1/datasets/profile",
        files={
            "file": (
                "customers.csv",
                BytesIO(csv_data.encode()),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    return response.json()["dataset_id"]


def test_dataset_copilot_endpoint(
    client,
) -> None:
    dataset_id = _upload_dataset(
        client
    )

    response = client.post(
        (
            f"/api/v1/datasets/"
            f"{dataset_id}/copilot"
        ),
        json={
            "question": (
                "Which columns should I clean first?"
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["dataset_id"] == dataset_id
    assert body["provider"] == "fallback"
    assert body["model"] is None

    assert body["question"] == (
        "Which columns should I clean first?"
    )

    assert body["answer"]

    lowered_answer = body["answer"].lower()

    assert "age" in lowered_answer
    assert "email" in lowered_answer


def test_dataset_copilot_reliability_question(
    client,
) -> None:
    dataset_id = _upload_dataset(
        client
    )

    response = client.post(
        (
            f"/api/v1/datasets/"
            f"{dataset_id}/copilot"
        ),
        json={
            "question": (
                "Why is the reliability score low?"
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "reliability score" in (
        body["answer"].lower()
    )


def test_dataset_copilot_rejects_blank_question(
    client,
) -> None:
    dataset_id = _upload_dataset(
        client
    )

    response = client.post(
        (
            f"/api/v1/datasets/"
            f"{dataset_id}/copilot"
        ),
        json={
            "question": "   "
        },
    )

    assert response.status_code == 422


def test_dataset_copilot_returns_404(
    client,
) -> None:
    response = client.post(
        (
            "/api/v1/datasets/"
            "missing-dataset/copilot"
        ),
        json={
            "question": (
                "Summarize this dataset."
            )
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Dataset analysis not found."
    )