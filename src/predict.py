"""Predict anxiety level from one or more ECG/HRV feature rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Path to model.joblib")
    parser.add_argument("--input", required=True, help="CSV containing feature rows")
    parser.add_argument("--output", help="Optional output CSV path")
    args = parser.parse_args()

    model_path = Path(args.model)
    metadata_path = model_path.with_name("metadata.json")
    metadata = json.loads(metadata_path.read_text())
    frame = pd.read_csv(args.input)
    missing = sorted(set(metadata["feature_columns"]) - set(frame.columns))
    if missing:
        raise ValueError(f"Input is missing feature columns: {missing}")

    result = frame.copy()
    model = joblib.load(model_path)
    result["predicted_anxiety_level"] = model.predict(frame[metadata["feature_columns"]])
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(frame[metadata["feature_columns"]])
        result["prediction_confidence"] = probabilities.max(axis=1).round(6)
    if args.output:
        result.to_csv(args.output, index=False)
    else:
        print(result.to_csv(index=False))


if __name__ == "__main__":
    main()
