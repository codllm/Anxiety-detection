"""Evaluate a saved model against a labeled ECG/HRV CSV."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Path to model.joblib")
    parser.add_argument("--data", required=True, help="Labeled CSV containing anxiety_level")
    parser.add_argument("--output", help="Optional path for predictions CSV")
    args = parser.parse_args()

    model_path = Path(args.model)
    metadata = json.loads(model_path.with_name("metadata.json").read_text())
    data = pd.read_csv(args.data)
    if "anxiety_level" not in data.columns:
        raise ValueError("The evaluation CSV must contain an anxiety_level column.")
    missing = sorted(set(metadata["feature_columns"]) - set(data.columns))
    if missing:
        raise ValueError(f"Evaluation CSV is missing feature columns: {missing}")

    model = joblib.load(model_path)
    labels = metadata["labels"]
    actual = data["anxiety_level"].astype("string").str.strip().str.title()
    predicted = pd.Series(model.predict(data[metadata["feature_columns"]]), index=data.index)
    report = classification_report(actual, predicted, labels=labels, zero_division=0, output_dict=True)
    matrix = confusion_matrix(actual, predicted, labels=labels)

    print(f"Records: {len(data)}")
    print(f"Accuracy: {accuracy_score(actual, predicted):.4f}")
    print(f"Balanced accuracy: {balanced_accuracy_score(actual, predicted):.4f}")
    print(f"Macro-F1: {f1_score(actual, predicted, labels=labels, average='macro'):.4f}")
    print("\nPer-class precision, recall, F1:")
    for label in labels:
        print(f"{label}: precision={report[label]['precision']:.4f}, recall={report[label]['recall']:.4f}, f1={report[label]['f1-score']:.4f}")
    print("\nConfusion matrix (rows=true, columns=predicted):")
    print(pd.DataFrame(matrix, index=labels, columns=labels).to_string())

    if args.output:
        result = data.copy()
        result["predicted_anxiety_level"] = predicted
        result.to_csv(args.output, index=False)
        print(f"\nSaved predictions: {args.output}")


if __name__ == "__main__":
    main()
