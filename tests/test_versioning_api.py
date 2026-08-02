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


def test_save_cleaned_version_endpoint(
    client,
) -> None:
    source_dataset_id = (
        _upload_dataset(
            client
        )
    )

    response = client.post(
        (
            f"/api/v1/datasets/"
            f"{source_dataset_id}/"
            "save-cleaned-version"
        )
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["source_dataset_id"]
        == source_dataset_id
    )

    assert (
        body["parent_dataset_id"]
        == source_dataset_id
    )

    assert (
        body["root_dataset_id"]
        == source_dataset_id
    )

    assert (
        body["version_number"]
        == 2
    )

    assert (
        body["version_type"]
        == "CLEANED"
    )

    assert (
        body["duplicate_rows"]
        == 0
    )

    assert (
        body["row_count"]
        == 4
    )

    assert body["dataset_id"]
    assert body["filename"].endswith(
        "_v2_cleaned.csv"
    )


def test_saved_version_can_be_opened(
    client,
) -> None:
    source_dataset_id = (
        _upload_dataset(
            client
        )
    )

    save_response = client.post(
        (
            f"/api/v1/datasets/"
            f"{source_dataset_id}/"
            "save-cleaned-version"
        )
    )

    assert save_response.status_code == 200

    new_dataset_id = (
        save_response.json()[
            "dataset_id"
        ]
    )

    get_response = client.get(
        (
            f"/api/v1/datasets/"
            f"{new_dataset_id}"
        )
    )

    assert get_response.status_code == 200

    body = get_response.json()

    assert (
        body["dataset_id"]
        == new_dataset_id
    )

    assert (
        body["duplicate_rows"]
        == 0
    )


def test_multiple_saved_versions_increment(
    client,
) -> None:
    source_dataset_id = (
        _upload_dataset(
            client
        )
    )

    version_two = client.post(
        (
            f"/api/v1/datasets/"
            f"{source_dataset_id}/"
            "save-cleaned-version"
        )
    )

    assert version_two.status_code == 200

    version_two_id = (
        version_two.json()[
            "dataset_id"
        ]
    )

    version_three = client.post(
        (
            f"/api/v1/datasets/"
            f"{version_two_id}/"
            "save-cleaned-version"
        )
    )

    assert version_three.status_code == 200

    body = version_three.json()

    assert (
        body["version_number"]
        == 3
    )

    assert (
        body["parent_dataset_id"]
        == source_dataset_id
    )


def test_save_cleaned_version_returns_404(
    client,
) -> None:
    response = client.post(
        (
            "/api/v1/datasets/"
            "missing-dataset/"
            "save-cleaned-version"
        )
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Dataset analysis not found."
    )