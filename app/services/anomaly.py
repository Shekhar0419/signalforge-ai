import pandas as pd


def iqr_outlier_mask(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()

    if len(valid) < 4:
        return pd.Series(False, index=series.index)

    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return pd.Series(False, index=series.index)

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return (numeric < lower) | (numeric > upper)
