import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const labels = ["Low", "Medium", "High"];

function formatPercent(value) {
  return `${(value * 100).toFixed(2)}%`;
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
  const [file, setFile] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function evaluate() {
    if (!file) return;
    setLoading(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const response = await fetch("/api/evaluate", { method: "POST", body: form });
      const raw = await response.text();
      let body;
      try {
        body = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error(`Backend returned an invalid response (${response.status}). Check that the API is running on port 8000.`);
      }
      if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
      setEvaluation(body);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">ECG / HRV MACHINE LEARNING</p>
          <h1>Anxiety-level model evaluation</h1>
          <p className="subtitle">Upload labeled ECG/HRV feature data to verify the model's correctness and performance.</p>
        </div>
        <div className="status-pill"><span /> Model ready</div>
      </header>

      <div className="notice">Upload a CSV containing the true <code>anxiety_level</code> column. Valid labels are Low, Medium, and High.</div>
      {error && <div className="error">{error}</div>}

      <section className="single-panel panel">
        <div className="panel-heading"><span className="number">01</span><div><h2>Check model correctness</h2><p>Evaluate predictions against trusted labels.</p></div></div>
        <FilePicker label={file ? file.name : "Choose labeled CSV"} onChange={setFile} />
        <button className="primary-button" disabled={!file || loading} onClick={evaluate}>{loading ? "Evaluating..." : "Evaluate model"}</button>
        {evaluation && <>
          <div className="metrics-grid">
            <Metric label="Total records" value={evaluation.rows} />
            <Metric label="Accuracy" value={formatPercent(evaluation.metrics.accuracy)} />
            <Metric label="Balanced accuracy" value={formatPercent(evaluation.metrics.balanced_accuracy)} />
            <Metric label="Macro-F1" value={formatPercent(evaluation.metrics.macro_f1)} />
          </div>
          {evaluation.rows < 30 && <div className="small-warning">This is a very small test file ({evaluation.rows} rows). A 100% score here does not represent reliable overall model accuracy.</div>}
          <div className="result-counts"><span>Correct: <strong>{evaluation.metrics.correct}</strong></span><span>Incorrect: <strong>{evaluation.metrics.incorrect}</strong></span></div>
          <h3>Per-class performance</h3>
          <table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead><tbody>{labels.map((label) => <tr key={label}><td>{label}</td><td>{formatPercent(evaluation.per_class[label].precision)}</td><td>{formatPercent(evaluation.per_class[label].recall)}</td><td>{formatPercent(evaluation.per_class[label]["f1-score"])}</td></tr>)}</tbody></table>
          <h3>Confusion matrix</h3>
          <div className="matrix"><div /><div>Low</div><div>Medium</div><div>High</div>{evaluation.confusion_matrix.map((row, index) => <><div className="matrix-label" key={`label-${labels[index]}`}>{labels[index]}</div>{row.map((value, cellIndex) => <div className={cellIndex === index ? "correct-cell" : "matrix-cell"} key={`${index}-${cellIndex}`}>{value}</div>)}</>)}</div>
          <h3>Row-level result preview</h3>
          <div className="table-wrap"><table><thead><tr><th>Actual</th><th>Predicted</th><th>Result</th></tr></thead><tbody>{evaluation.preview.slice(0, 20).map((row, index) => <tr key={index}><td>{row.anxiety_level}</td><td>{row.predicted_anxiety_level}</td><td className={row.prediction_correct ? "correct-text" : "incorrect-text"}>{row.prediction_correct ? "Correct" : "Incorrect"}</td></tr>)}</tbody></table></div>
          <button className="download-button" onClick={() => downloadCsv(evaluation.csv, "labeled_predictions.csv")}>Download labeled results</button>
        </>}
      </section>
      <footer>Model: Logistic Regression · 21 ECG/HRV features · Subject-aware evaluation</footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
