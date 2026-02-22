import { useEffect, useState } from "react";

const HISTORY_STORAGE_KEY = "crop-scan-history";

const insightCards = [
  {
    title: "Early alerts",
    subtitle: "Catch disease signals before visible spread.",
  },
  {
    title: "Farmer-first output",
    subtitle: "Concise diagnosis, confidence, and next action.",
  },
  {
    title: "Image based",
    subtitle: "Upload a single leaf photo for instant analysis.",
  },
];

export default function FarmerDashboard() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await fetch("/api/scans");
        const payload = await response.json();
        if (response.ok && Array.isArray(payload)) {
          setHistory(payload);
          localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(payload));
          return;
        }
      } catch {
        // fall through to local cache
      }

      try {
        const saved = localStorage.getItem(HISTORY_STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) {
            setHistory(parsed);
          }
        }
      } catch {
        setHistory([]);
      }
    };

    loadHistory();
  }, []);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setError("");
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please choose an image first.");
      return;
    }

    setIsUploading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("/api/predict", {
        method: "POST",
        body: formData,
      });

      const rawBody = await response.text();
      let data = {};

      if (rawBody) {
        try {
          data = JSON.parse(rawBody);
        } catch {
          throw new Error("Prediction service returned invalid JSON.");
        }
      }

      if (!response.ok) {
        const message = [
          data.error || data.detail || "Prediction request failed.",
          data.aiServiceUrl ? `URL: ${data.aiServiceUrl}` : "",
          data.details ? `Details: ${data.details}` : "",
        ]
          .filter(Boolean)
          .join(" | ");
        throw new Error(message);
      }

      if (!rawBody) {
        throw new Error("Prediction service returned an empty response.");
      }

      setResult(data);

      const scanPayload = {
        fileName: selectedFile.name,
        disease: data.disease,
        confidence: data.confidence,
        severity: data.severity,
        treatment: data.treatment,
      };

      try {
        const saveResponse = await fetch("/api/scans", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(scanPayload),
        });

        const savedScan = await saveResponse.json();
        if (!saveResponse.ok) {
          throw new Error(savedScan.error || "Unable to save scan history.");
        }

        setHistory((prev) => {
          const updated = [savedScan, ...prev.filter((item) => item.id !== savedScan.id)].slice(0, 12);
          localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
          return updated;
        });
      } catch {
        const fallbackEntry = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          createdAt: new Date().toISOString(),
          ...scanPayload,
        };
        setHistory((prev) => {
          const updated = [fallbackEntry, ...prev].slice(0, 12);
          localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
          return updated;
        });
      }
    } catch (uploadError) {
      setError(uploadError.message || "Unable to process request.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      const response = await fetch("/api/scans", { method: "DELETE" });
      if (!response.ok) {
        throw new Error("Unable to clear server history.");
      }
      setHistory([]);
      localStorage.removeItem(HISTORY_STORAGE_KEY);
    } catch (clearError) {
      setError(clearError.message || "Unable to clear history.");
    }
    setShowClearConfirm(false);
  };

  const handleExportHistoryCsv = () => {
    if (history.length === 0) return;

    const headers = ["timestamp", "file_name", "disease", "confidence", "severity"];
    const escapeCsv = (value) => `"${String(value ?? "").replace(/"/g, "\"\"")}"`;

    const rows = history.map((entry) => [
      new Date(entry.createdAt).toISOString(),
      entry.fileName,
      entry.disease,
      entry.confidence,
      entry.severity,
    ]);

    const csv = [headers, ...rows]
      .map((row) => row.map(escapeCsv).join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `crop-scan-history-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <main className="app-shell">
      <section className="dashboard" aria-label="Crop disease prediction dashboard">
        <div className="dashboard-grid">
          <div className="left-pane">
            <span className="badge">AI Crop Care</span>
            <h1 className="hero-title">Plant Health Studio</h1>
            <p className="hero-copy">
              Turn a single leaf image into a practical field recommendation. Designed
              for quick decision-making in real farm conditions.
            </p>

            <div className="info-cards">
              {insightCards.map((card) => (
                <article key={card.title} className="info-card">
                  <span className="dot" aria-hidden="true" />
                  <div>
                    <p className="info-title">{card.title}</p>
                    <p className="info-sub">{card.subtitle}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="right-pane">
            <h2 className="panel-title">Upload Leaf Image</h2>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="file-input"
            />

            {selectedFile && <p className="selected-file">Selected: {selectedFile.name}</p>}

            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="upload-btn"
            >
              {isUploading ? "Analyzing..." : "Run Disease Scan"}
            </button>

            {error && <p className="error">{error}</p>}

            {result && (
              <section className="result" aria-label="Prediction result">
                <h3>{result.disease}</h3>
                <div className="kv">
                  <div>
                    <span>Confidence</span>
                    <strong>{result.confidence}</strong>
                  </div>
                  <div>
                    <span>Severity</span>
                    <strong>{result.severity}</strong>
                  </div>
                  <div>
                    <span>Treatment</span>
                    <strong>{result.treatment}</strong>
                  </div>
                </div>

                {Array.isArray(result.treatmentSteps) && result.treatmentSteps.length > 0 && (
                  <div className="sub-section">
                    <h4>Treatment Plan</h4>
                    <ol className="steps-list">
                      {result.treatmentSteps.map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ol>
                  </div>
                )}

                {Array.isArray(result.topPredictions) && result.topPredictions.length > 0 && (
                  <div className="sub-section">
                    <h4>Top 3 Predictions</h4>
                    <div className="top-predictions">
                      {result.topPredictions.map((item) => (
                        <article key={`${item.disease}-${item.confidenceScore}`} className="pred-card">
                          <div className="pred-head">
                            <p>{item.disease}</p>
                            <span>{item.confidenceScore}% ({item.confidence})</span>
                          </div>
                          <div className="pred-meter" aria-hidden="true">
                            <div
                              className="pred-fill"
                              style={{ width: `${Math.max(0, Math.min(100, item.confidenceScore ?? 0))}%` }}
                            />
                          </div>
                        </article>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}

            {history.length > 0 && (
              <section className="history" aria-label="Recent scans">
                <div className="history-header">
                  <h3>Recent Scans</h3>
                  <div className="history-actions">
                    <button type="button" onClick={handleExportHistoryCsv} className="ghost-btn">
                      Export CSV
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowClearConfirm(true)}
                      className="ghost-btn danger"
                    >
                      Clear History
                    </button>
                  </div>
                </div>
                <div className="history-list">
                  {history.map((entry) => (
                    <article key={entry.id} className="history-item">
                      <p className="history-main">{entry.disease}</p>
                      <p className="history-sub">
                        {entry.fileName} | {entry.confidence} confidence | {entry.severity} severity
                      </p>
                      <time className="history-time">
                        {new Date(entry.createdAt).toLocaleString()}
                      </time>
                    </article>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      </section>

      {showClearConfirm && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Confirm clear history">
          <div className="modal-card">
            <h3>Clear scan history?</h3>
            <p>This will permanently remove all saved scan entries from this browser.</p>
            <div className="modal-actions">
              <button type="button" className="ghost-btn" onClick={() => setShowClearConfirm(false)}>
                Cancel
              </button>
              <button type="button" className="ghost-btn danger" onClick={handleClearHistory}>
                Yes, clear all
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
