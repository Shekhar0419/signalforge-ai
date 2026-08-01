from app.models.schemas import DatasetProfile


def generate_dataset_summary(profile: DatasetProfile) -> str:
    """
    Generate a human-readable summary of the dataset profile.
    This deterministic implementation acts as a fallback when
    no LLM provider is configured.
    """

    reliability = round(profile.reliability_score, 2)

    summary = [
        f"The uploaded dataset contains {profile.row_count} rows and {profile.column_count} columns.",
        f"The overall data reliability score is {reliability}%.",
    ]

    if profile.duplicate_rows:
        summary.append(
            f"{profile.duplicate_rows} duplicate rows were detected."
        )

    if profile.issues:
        summary.append(
            f"{len(profile.issues)} data quality issues were identified."
        )

    if profile.business_rules:
        failed_rules = sum(
            1
            for rule in profile.business_rules
            if not rule.get("passed", True)
        )

        if failed_rules:
            summary.append(
                f"{failed_rules} business rule checks failed."
            )

    if profile.ml_anomalies:
        summary.append(
            f"{len(profile.ml_anomalies)} potential anomalies were detected using Isolation Forest."
        )

    if profile.recommendations:
        summary.append("Recommended next steps:")

        for recommendation in profile.recommendations[:3]:
            summary.append(f"- {recommendation}")

    return "\n".join(summary)