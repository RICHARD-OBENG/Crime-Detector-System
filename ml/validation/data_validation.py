import pandas as pd
import numpy as np

MAX_MISSING_PCT = 0.3
MAX_CARDINALITY = 100
MAX_OUTLIER_RATE = 0.05


def validate_schema(crime_data: pd.DataFrame, expected_columns: list):
    missing_cols = set(expected_columns) - set(crime_data.columns)
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")


def validate_missingness(crime_data: pd.DataFrame):
    missing = crime_data.isna().mean()
    bad = missing[missing > MAX_MISSING_PCT]
    if not bad.empty:
        raise ValueError(f"Too much missing data: {bad.to_dict()}")


def validate_cardinality(crime_data: pd.DataFrame, categorical_cols: list):
    for col in categorical_cols:
        if crime_data[col].nunique() > MAX_CARDINALITY:
            raise ValueError(f"High cardinality in {col}")


def validate_outliers(crime_data: pd.DataFrame, numeric_cols: list):
    for col in numeric_cols:
        q1 = crime_data[col].quantile(0.25)
        q3 = crime_data[col].quantile(0.75)
        iqr = q3 - q1
        outlier_rate = (
            (crime_data[col] < q1 - 1.5 * iqr) |
            (crime_data[col] > q3 + 1.5 * iqr)
        ).mean()

        if outlier_rate > MAX_OUTLIER_RATE:
            raise ValueError(f"Too many outliers in {col}: {outlier_rate:.2%}")
