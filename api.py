"""Local API used by the React frontend."""

from __future__ import annotations

import io
import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "artifacts" / "model-three" / "model.joblib"
METADATA_PATH = ROOT / "artifacts" / "model-three" / "metadata.json"

app = FastAPI(title="ECG/HRV Anxiety API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_artifacts():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise HTTPException(status_code=500, detail="Trained model not found. Run the training command first.")
    return joblib.load(MODEL_PATH), json.loads(METADATA_PATH.read_text())


async def read_csv(file: UploadFile) -> pd.DataFrame:
    try:
        return pd.read_csv(io.BytesIO(await file.read()))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {exc}") from exc


def check_features(data: pd.DataFrame, metadata: dict) -> None:
    missing = sorted(set(metadata["feature_columns"]) - set(data.columns))
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required feature columns: {missing}")


def prediction_result(data: pd.DataFrame, model, metadata: dict) -> tuple[pd.DataFrame, list[str]]:
    check_features(data, metadata)
    predictions = model.predict(data[metadata["feature_columns"]])
    result = data.copy()
    result["predicted_anxiety_level"] = predictions
    if hasattr(model, "predict_proba"):
        result["prediction_confidence"] = model.predict_proba(data[metadata["feature_columns"]]).max(axis=1).round(6)
    return result, predictions


def json_preview(data: pd.DataFrame) -> list[dict]:
    """Convert pandas NaN values to JSON null values for FastAPI responses."""
    preview = data.head(100).astype(object).where(pd.notna(data.head(100)), None)
    return preview.to_dict(orient="records")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/predict")
async def predict(file: UploadFile = File(...)):
    model, metadata = load_artifacts()
    data = await read_csv(file)
    result, predictions = prediction_result(data, model, metadata)
    labels = metadata["labels"]
    counts = result["predicted_anxiety_level"].value_counts().reindex(labels, fill_value=0)
    return {
        "filename": file.filename,
        "rows": len(result),
        "counts": {label: int(counts[label]) for label in labels},
        "average_confidence": float(result["prediction_confidence"].mean()) if "prediction_confidence" in result else None,
        "preview": json_preview(result),
        "csv": result.to_csv(index=False),
    }


@app.post("/api/evaluate")
async def evaluate(file: UploadFile = File(...)):
    model, metadata = load_artifacts()
    data = await read_csv(file)
    if "anxiety_level" not in data.columns:
        raise HTTPException(status_code=400, detail="Labeled CSV must contain an anxiety_level column.")
    result, predictions = prediction_result(data, model, metadata)
    labels = metadata["labels"]
    actual = data["anxiety_level"].astype("string").str.strip().str.title()
    unknown_labels = sorted(set(actual.dropna()) - set(labels))
    if unknown_labels:
        raise HTTPException(status_code=400, detail=f"Unsupported anxiety labels: {unknown_labels}. Use only: {labels}")
    result["prediction_correct"] = actual.to_numpy() == predictions
    report = classification_report(actual, predictions, labels=labels, output_dict=True, zero_division=0)
    matrix = confusion_matrix(actual, predictions, labels=labels)
    return {
        "filename": file.filename,
        "rows": len(data),
        "metrics": {
            "accuracy": float(accuracy_score(actual, predictions)),
            "balanced_accuracy": float(balanced_accuracy_score(actual, predictions)),
            "macro_f1": float(f1_score(actual, predictions, labels=labels, average="macro")),
            "correct": int((actual.to_numpy() == predictions).sum()),
            "incorrect": int((actual.to_numpy() != predictions).sum()),
        },
        "per_class": {
            label: {metric: float(report[label][metric]) for metric in ["precision", "recall", "f1-score"]}
            for label in labels
        },
        "labels": labels,
        "confusion_matrix": matrix.tolist(),
        "preview": json_preview(result),
        "csv": result.to_csv(index=False),
    }
