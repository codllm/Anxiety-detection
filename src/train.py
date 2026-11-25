"""Train and evaluate grouped ECG/HRV anxiety-level models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data import GROUP, TARGET, load_datasets, feature_columns

LABEL_ORDER = ["Low", "Medium", "High"]


def build_models(seed: int) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            [("imputer", SimpleImputer(strategy="median")),
             ("scaler", StandardScaler()),
             ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed))]
        ),
        "random_forest": Pipeline(
            [("imputer", SimpleImputer(strategy="median")),
             ("model", RandomForestClassifier(n_estimators=400, class_weight="balanced", random_state=seed, n_jobs=-1))]
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", action="append", required=True, help="Input CSV path. Repeat for multiple files.")
    parser.add_argument("--output-dir", default="artifacts/model", help="Directory for model and reports.")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_datasets(args.data)
    columns = feature_columns(data)
    X, y, groups = data[columns], data[TARGET], data[GROUP]
    splitter = GroupShuffleSplit(n_splits=1, test_size=args.test_size, random_state=args.seed)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    groups_train = groups.iloc[train_idx]

    n_splits = min(5, groups_train.nunique())
    cv = GroupKFold(n_splits=n_splits)
    models = build_models(args.seed)
    cv_results = {}
    for name, model in models.items():
        scores = cross_val_score(model, X_train, y_train, groups=groups_train, cv=cv, scoring="f1_macro", n_jobs=1)
        cv_results[name] = {"fold_macro_f1": scores.round(6).tolist(), "mean_macro_f1": float(scores.mean())}

    best_name = max(cv_results, key=lambda name: cv_results[name]["mean_macro_f1"])
    best_model = models[best_name].fit(X_train, y_train)
    predictions = best_model.predict(X_test)
    report = classification_report(y_test, predictions, labels=LABEL_ORDER, output_dict=True, zero_division=0)
    matrix = confusion_matrix(y_test, predictions, labels=LABEL_ORDER)

    pd.DataFrame(matrix, index=LABEL_ORDER, columns=LABEL_ORDER).to_csv(output_dir / "confusion_matrix.csv")
    with (output_dir / "classification_report.json").open("w") as handle:
        json.dump(report, handle, indent=2)
    with (output_dir / "cv_results.json").open("w") as handle:
        json.dump(cv_results, handle, indent=2)

    metadata = {
        "target": TARGET,
        "group_column": GROUP,
        "feature_columns": columns,
        "labels": LABEL_ORDER,
        "selected_model": best_name,
        "rows": int(len(data)),
        "subjects": int(data[GROUP].nunique()),
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "test_subjects": int(groups.iloc[test_idx].nunique()),
        "test_macro_f1": float(f1_score(y_test, predictions, labels=LABEL_ORDER, average="macro")),
        "source_files": [str(Path(path).resolve()) for path in args.data],
        "note": "Prototype using engineered ECG/HRV features; not raw ECG and not a clinical diagnosis.",
    }
    with (output_dir / "metadata.json").open("w") as handle:
        json.dump(metadata, handle, indent=2)
    joblib.dump(best_model, output_dir / "model.joblib")

    print(json.dumps({"selected_model": best_name, "cv": cv_results, "test_macro_f1": metadata["test_macro_f1"], "output_dir": str(output_dir)}, indent=2))


if __name__ == "__main__":
    main()
