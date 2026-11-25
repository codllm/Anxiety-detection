# ECG/HRV Anxiety-Level Estimation

This project trains a prototype model from the supplied ECG-derived feature datasets. It currently does **not** consume raw ECG waveforms: the CSV files contain features such as mean heart rate, RMSSD, SDNN, LF/HF ratio, and signal quality.

The output is an estimated `Low`, `Medium`, or `High` anxiety level for research/prototyping. It is not a clinical diagnosis.

## Quick start

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 src/train.py \
  --data /Users/nishantnikhil/Downloads/ecg_hrv_dataset.csv \
  --output-dir artifacts/model
```

To train using all supplied files, the loader de-duplicates identical `subject_id`/`window_id` rows when files contain overlapping records:

```bash
python3 src/train.py \
  --data /Users/nishantnikhil/Downloads/ecg_hrv_dataset.csv \
  --data /Users/nishantnikhil/Downloads/ecg_hrv_dataset_2.csv \
  --data /Users/nishantnikhil/Downloads/ecg_hrv_dataset_synthetic_10k.csv \
  --output-dir artifacts/model-three
```

Run a saved model on a new feature row:

```bash
python3 src/predict.py \
  --model artifacts/model/model.joblib \
  --input path/to/new_features.csv
```

The input CSV must contain the feature columns listed in `artifacts/model/metadata.json`. It may also contain `subject_id`, `window_id`, and `anxiety_level`; those columns are ignored by prediction.

## Evaluate on labeled test data

Use this command when the test CSV contains the true `anxiety_level` column. It prints accuracy, balanced accuracy, macro-F1, and precision/recall/F1 for each class:

```bash
python3 src/evaluate.py \
  --model artifacts/model-three/model.joblib \
  --data /Users/nishantnikhil/Downloads/ecg_hrv_prediction_labeled.csv \
  --output artifacts/model-three/ecg_hrv_prediction_labeled_results.csv
```

Do not use this evaluation command on an unlabeled CSV. Without true labels, accuracy and recall cannot be calculated.

## What the pipeline does

1. Validates the expected schema and label values.
2. Removes identifier and target columns from the features.
3. Imputes missing numeric values using training-fold medians.
4. Standardizes features inside the training pipeline.
5. Compares a class-weighted logistic regression and random forest using subject-grouped cross-validation.
6. Fits the better macro-F1 model on the training subjects.
7. Evaluates once on held-out subjects and writes macro F1, per-class metrics, a confusion matrix, and feature importance/coefficients.
8. Saves the fitted model and metadata for later inference.

The default split is a grouped 80/20 split by `subject_id`, followed by grouped 5-fold cross-validation on the training subjects. This avoids treating windows from the same person as independent people.

## Important limitation

These files contain engineered features, not raw ECG. The current model is therefore a feature-based baseline. When raw ECG becomes available, add a preprocessing stage for filtering, R-peak detection, RR intervals, and HRV extraction, then pass the resulting feature table through this same training/evaluation interface. Keep subject IDs so the grouped split remains valid.

Do not describe this prototype as diagnosing anxiety. ECG/HRV features can support anxiety-level estimation or screening research, but cannot establish a clinical diagnosis by themselves.
