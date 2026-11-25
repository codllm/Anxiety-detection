import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const labels = ["Low", "Medium", "High"];

function formatPercent(value) {
  return value == null ? "—" : `${(value * 100).toFixed(2)}%`;
}

function downloadCsv(csv, filename) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function FilePicker({ label, onChange }) {
  return (
    <label className="upload-box">
      <span>{label}</span>
      <input type="file" accept=".csv,text/csv" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
    </label>
  );
}

function Metric({ label, value }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function App() {
  const [labeledFile, setLabeledFile] = useState(null);
  const [unlabeledFile, setUnlabeledFile] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  async function send(path, file, setter) {
    if (!file) return;
    setLoading(path);
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const response = await fetch(path, { method: "POST", body: form });
      const raw = await response.text();
      let body;
      try {
        body = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error(`Backend returned an invalid response (${response.status}). Check that the API is running on port 8000.`);
      }
      if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
      setter(body);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  return (
    <main className="page-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">ECG / HRV MACHINE LEARNING</p>
          <h1>Anxiety-level estimator</h1>
          <p className="subtitle">Evaluate labeled data or estimate Low, Medium, and High anxiety from engineered ECG/HRV features.</p>
        </div>
        <div className="status-pill"><span /> Model ready</div>
      </header>

      <div className="notice">Upload ECG/HRV feature CSV data, not raw ECG waveforms. The model estimates anxiety level and is not a clinical diagnosis.</div>
      {error && <div className="error">{error}</div>}

      <section className="workspace-grid">
        <article className="panel">
          <div className="panel-heading"><span className="number">01</span><div><h2>Validate labeled data</h2><p>Use a CSV containing the true <code>anxiety_level</code>.</p></div></div>
          <FilePicker label={labeledFile ? labeledFile.name : "Choose labeled CSV"} onChange={setLabeledFile} />
          <button className="primary-button" disabled={!labeledFile || loading === "/api/evaluate"} onClick={() => send("/api/evaluate", labeledFile, setEvaluation)}>{loading === "/api/evaluate" ? "Evaluating..." : "Evaluate model"}</button>
          {evaluation && <>
            <div className="metrics-grid">
              <Metric label="Records" value={evaluation.rows} />
              <Metric label="Accuracy" value={formatPercent(evaluation.metrics.accuracy)} />
              <Metric label="Balanced accuracy" value={formatPercent(evaluation.metrics.balanced_accuracy)} />
              <Metric label="Macro-F1" value={formatPercent(evaluation.metrics.macro_f1)} />
            </div>
            {evaluation.rows < 30 && <div className="small-warning">This is a very small test file. A 100% score here is not a reliable overall accuracy estimate.</div>}
            <div className="result-counts"><span>Correct: <strong>{evaluation.metrics.correct}</strong></span><span>Incorrect: <strong>{evaluation.metrics.incorrect}</strong></span></div>
            <h3>Per-class performance</h3>
            <table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead><tbody>{labels.map((label) => <tr key={label}><td>{label}</td><td>{formatPercent(evaluation.per_class[label].precision)}</td><td>{formatPercent(evaluation.per_class[label].recall)}</td><td>{formatPercent(evaluation.per_class[label]["f1-score"])}</td></tr>)}</tbody></table>
            <h3>Actual vs predicted preview</h3>
            <div className="table-wrap"><table><thead><tr><th>Actual</th><th>Predicted</th><th>Result</th></tr></thead><tbody>{evaluation.preview.slice(0, 20).map((row, index) => <tr key={index}><td>{row.anxiety_level}</td><td>{row.predicted_anxiety_level}</td><td className={row.prediction_correct ? "correct-text" : "incorrect-text"}>{row.prediction_correct ? "Correct" : "Incorrect"}</td></tr>)}</tbody></table></div>
            <button className="download-button" onClick={() => downloadCsv(evaluation.csv, "labeled_predictions.csv")}>Download labeled results</button>
          </>}
        </article>

        <article className="panel">
          <div className="panel-heading"><span className="number">02</span><div><h2>Predict anxiety level</h2><p>Use a feature CSV without <code>anxiety_level</code>.</p></div></div>
          <FilePicker label={unlabeledFile ? unlabeledFile.name : "Choose unlabeled CSV"} onChange={setUnlabeledFile} />
          <button className="primary-button" disabled={!unlabeledFile || loading === "/api/predict"} onClick={() => send("/api/predict", unlabeledFile, setPrediction)}>{loading === "/api/predict" ? "Predicting..." : "Predict levels"}</button>
          {prediction && <>
            <div className="level-grid">{labels.map((label) => <div className={`level-card ${label.toLowerCase()}`} key={label}><span>{label}</span><strong>{prediction.counts[label]}</strong><small>records</small></div>)}</div>
            <div className="confidence"><span>Average confidence</span><strong>{formatPercent(prediction.average_confidence)}</strong></div>
            <h3>Predicted anxiety-level preview</h3>
            <div className="table-wrap"><table><thead><tr><th>Subject</th><th>Window</th><th>Level</th><th>Confidence</th></tr></thead><tbody>{prediction.preview.slice(0, 20).map((row, index) => <tr key={index}><td>{row.subject_id ?? "—"}</td><td>{row.window_id ?? "—"}</td><td><span className={`tag ${row.predicted_anxiety_level.toLowerCase()}`}>{row.predicted_anxiety_level}</span></td><td>{formatPercent(row.prediction_confidence)}</td></tr>)}</tbody></table></div>
            <button className="download-button" onClick={() => downloadCsv(prediction.csv, "unlabeled_predictions.csv")}>Download predictions</button>
          </>}
        </article>
      </section>
      <footer>Model: Logistic Regression · 21 ECG/HRV features · Subject-aware evaluation</footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
