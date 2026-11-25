"""Streamlit frontend for ECG/HRV anxiety-level estimation."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "artifacts" / "model-three" / "model.joblib"
METADATA_PATH = ROOT / "artifacts" / "model-three" / "metadata.json"
sys.path.insert(0, str(ROOT / "src"))


st.set_page_config(page_title="ECG/HRV Anxiety Estimator", page_icon="❤", layout="wide")


@st.cache_resource
def load_model():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Trained model not found. Train the model first with src/train.py.")
    import json

    return joblib.load(MODEL_PATH), json.loads(METADATA_PATH.read_text())


def validate_features(data: pd.DataFrame, feature_columns: list[str]) -> list[str]:
    return sorted(set(feature_columns) - set(data.columns))


def predict(data: pd.DataFrame, model, metadata: dict) -> tuple[pd.DataFrame, object]:
    missing = validate_features(data, metadata["feature_columns"])
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
    predictions = model.predict(data[metadata["feature_columns"]])
    result = data.copy()
    result["predicted_anxiety_level"] = predictions
    if hasattr(model, "predict_proba"):
        result["prediction_confidence"] = model.predict_proba(data[metadata["feature_columns"]]).max(axis=1).round(6)
    return result, predictions


def show_download(result: pd.DataFrame, filename: str) -> None:
    st.download_button(
        "Download results CSV",
        result.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


st.title("ECG/HRV Anxiety-Level Estimator")
st.caption("Feature-based prototype. Upload ECG/HRV feature CSV data, not raw ECG waveform data.")

try:
    model, metadata = load_model()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

st.info(f"Loaded model: {metadata['selected_model']} | Features required: {len(metadata['feature_columns'])}")

left, right = st.columns(2, gap="large")

with left:
    st.header("Labeled data: check correctness")
    st.write("Upload a CSV containing the true `anxiety_level` column.")
    labeled_file = st.file_uploader("Upload labeled CSV", type="csv", key="labeled")
    if labeled_file is not None:
        labeled = pd.read_csv(labeled_file)
        if "anxiety_level" not in labeled.columns:
            st.error("This file does not contain the `anxiety_level` column.")
        else:
            try:
                labeled_result, labeled_predictions = predict(labeled, model, metadata)
                actual = labeled["anxiety_level"].astype("string").str.strip().str.title()
                labels = metadata["labels"]
                report = classification_report(actual, labeled_predictions, labels=labels, output_dict=True, zero_division=0)
                a, b, c = st.columns(3)
                a.metric("Accuracy", f"{accuracy_score(actual, labeled_predictions):.2%}")
                b.metric("Balanced accuracy", f"{balanced_accuracy_score(actual, labeled_predictions):.2%}")
                c.metric("Macro-F1", f"{f1_score(actual, labeled_predictions, labels=labels, average='macro'):.2%}")
                metrics = pd.DataFrame(report).T.loc[labels, ["precision", "recall", "f1-score"]]
                st.subheader("Per-class metrics")
                st.dataframe(metrics.style.format("{:.2%}"), use_container_width=True)
                st.subheader("Confusion matrix")
                matrix = pd.DataFrame(confusion_matrix(actual, labeled_predictions, labels=labels), index=labels, columns=labels)
                st.dataframe(matrix, use_container_width=True)
                show_download(labeled_result, "labeled_predictions.csv")
            except ValueError as error:
                st.error(str(error))

with right:
    st.header("Unlabeled data: predict anxiety level")
    st.write("Upload a CSV without `anxiety_level`. The model will estimate Low, Medium, or High.")
    unlabeled_file = st.file_uploader("Upload unlabeled CSV", type="csv", key="unlabeled")
    if unlabeled_file is not None:
        unlabeled = pd.read_csv(unlabeled_file)
        try:
            unlabeled_result, _ = predict(unlabeled, model, metadata)
            counts = unlabeled_result["predicted_anxiety_level"].value_counts().reindex(metadata["labels"], fill_value=0)
            a, b, c = st.columns(3)
            a.metric("Low", int(counts["Low"]))
            b.metric("Medium", int(counts["Medium"]))
            c.metric("High", int(counts["High"]))
            st.subheader("Prediction distribution")
            st.bar_chart(counts)
            if "prediction_confidence" in unlabeled_result:
                st.metric("Average confidence", f"{unlabeled_result['prediction_confidence'].mean():.2%}")
            st.dataframe(unlabeled_result.head(100), use_container_width=True)
            show_download(unlabeled_result, "unlabeled_predictions.csv")
        except ValueError as error:
            st.error(str(error))

st.divider()
st.warning("This tool estimates anxiety level from engineered ECG/HRV features. It is not a clinical diagnosis and cannot accept raw ECG waveforms directly.")
