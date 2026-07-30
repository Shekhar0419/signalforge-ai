from app.models.schemas import ColumnProfile


def calculate_reliability_score(
    row_count: int,
    duplicate_rows: int,
    columns: list[ColumnProfile],
) -> float:
    if row_count == 0 or not columns:
        return 0.0

    score = 100.0

    duplicate_ratio = duplicate_rows / row_count
    score -= min(duplicate_ratio * 30.0, 30.0)

    average_missing = sum(column.missing_ratio for column in columns) / len(columns)
    score -= min(average_missing * 40.0, 40.0)

    average_outliers = sum(column.outlier_ratio for column in columns) / len(columns)
    score -= min(average_outliers * 20.0, 20.0)

    constant_columns = sum(1 for column in columns if column.unique_count <= 1)
    score -= min(constant_columns * 2.0, 10.0)

    return round(max(score, 0.0), 2)
