from io import BytesIO


def _upload_dataset(
    client,
) -> str:
    csv_content = (
        "customer_id,age,city,salary\n"
        "1,25,St. Louis,50000\n"
        "2,,Chicago,52000\n"
        "3,35,,51000\n"
        "4,42,Austin,53000\n"
        "4,42,Austin,53000\n"
        "6,31,Dallas,1000000\n"
    )

    response = client.post(
        "/api/v1/datasets/profile",
        files={
            "file": (
                "customers.csv",
                BytesIO(
                    csv_content.encode(
                        "utf-8"
                    )
                ),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    return response.json()[
        "dataset_id"
    ]


def test_cleaning_preview_endpoint(
    client,
) -> None:
    dataset_id = _upload_dataset(
        client
    )

    response = client.post(
        (
            f"/api/v1/datasets/"
            f"{dataset_id}/cleaning-preview"
        )
    )

    assert response.status_code == 200

    body = response.json()

    assert body["dataset_id"] == dataset_id
    assert body["source_modified"] is False

    assert (
        body["before"]["row_count"]
        == 6
    )

    assert (
        body["after"]["row_count"]
        == 5
    )

    assert (
        body["before"][
            "duplicate_rows"
        ]
        == 1
    )

    assert (
        body["after"][
            "duplicate_rows"
        ]
        == 0
    )

    assert (
        body["before"][
            "missing_values"
        ]
        == 2
    )

    assert (
        body["after"][
            "missing_values"
        ]
        == 0
    )

    assert (
        body["after"][
            "reliability_score"
        ]
        >= body["before"][
            "reliability_score"
        ]
    )

    assert body["preview_rows"]


def test_cleaning_preview_limit(
    client,
) -> None:
    dataset_id = _upload_dataset(
        client
    )

    response = client.post(
        (
            f"/api/v1/datasets/"
            f"{dataset_id}/cleaning-preview"
            "?preview_limit=2"
        )
    )

    assert response.status_code == 200

    assert len(
        response.json()[
            "preview_rows"
        ]
    ) == 2


def test_cleaning_preview_rejects_invalid_limit(
    client,
) -> None:
    dataset_id = _upload_dataset(
        client
    )

    response = client.post(
        (
            f"/api/v1/datasets/"
            f"{dataset_id}/cleaning-preview"
            "?preview_limit=0"
        )
    )

    assert response.status_code == 422


def test_cleaning_preview_returns_404(
    client,
) -> None:
    response = client.post(
        (
            "/api/v1/datasets/"
            "missing-dataset/"
            "cleaning-preview"
        )
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Dataset analysis not found."
    )