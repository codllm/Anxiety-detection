"""Data loading and schema validation for ECG-derived feature tables."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

TARGET = "anxiety_level"
GROUP = "subject_id"
IDENTIFIERS = [GROUP, "window_id"]
EXPECTED_LABELS = {"Low", "Medium", "High"}


def load_datasets(paths: Iterable[str | Path]) -> pd.DataFrame:
    paths = [Path(path) for path in paths]
    if not paths:
        raise ValueError("At least one CSV path is required.")

    frames = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        frame = pd.read_csv(path)
        if frame.empty:
            raise ValueError(f"Dataset is empty: {path}")
        frames.append(frame)

    data = pd.concat(frames, ignore_index=True)
    required = {TARGET, GROUP, *IDENTIFIERS}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    data[TARGET] = data[TARGET].astype("string").str.strip().str.title()
    unknown = sorted(set(data[TARGET].dropna()) - EXPECTED_LABELS)
    if unknown:
        raise ValueError(f"Unexpected labels in {TARGET}: {unknown}")
    if data[TARGET].isna().any():
        raise ValueError(f"{TARGET} contains missing labels.")
    if data[GROUP].isna().any():
        raise ValueError(f"{GROUP} contains missing values.")

    # The two supplied files can contain the same window. Keep one copy so
    # the second file does not silently double-weight overlapping records.
    before = len(data)
    data = data.drop_duplicates(subset=IDENTIFIERS, keep="first").reset_index(drop=True)
    if len(data) < before:
        print(f"Removed {before - len(data)} duplicate subject/window rows.")

    feature_columns = [column for column in data.columns if column not in {*IDENTIFIERS, TARGET}]
    if not feature_columns:
        raise ValueError("No feature columns remain after removing identifiers and target.")
    non_numeric = data[feature_columns].select_dtypes(exclude="number").columns.tolist()
    if non_numeric:
        raise ValueError(f"Feature columns must be numeric: {non_numeric}")
    if data[feature_columns].notna().sum().eq(0).any():
        empty_columns = data[feature_columns].columns[data[feature_columns].notna().sum().eq(0)].tolist()
        raise ValueError(f"Feature columns contain no usable values: {empty_columns}")
    return data


def feature_columns(data: pd.DataFrame) -> list[str]:
    return [column for column in data.columns if column not in {*IDENTIFIERS, TARGET}]
