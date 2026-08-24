import { FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, createSummary, uploadDocument, type Summary } from "../services/api";
import { useAuth } from "../context/AuthContext";

const MODES: Summary["mode"][] = ["short", "medium", "long"];

export function DashboardPage() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const token = session?.access_token || "";
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<Summary["mode"]>("medium");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const statusHint = useMemo(() => {
    if (!file) return "";
    if (file.type.startsWith("image/")) return "This image will be processed with OCR.";
    return "Text PDFs are extracted directly; scanned PDFs fall back to OCR.";
  }, [file]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF or image first.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      setStatus("Uploading document...");
      const isImage = file.type.startsWith("image/");
      setStatus(isImage ? "Running OCR..." : "Extracting text...");
      const document = await uploadDocument(token, file);
      setStatus("Generating summary...");
      const summary = await createSummary(token, document.id, mode);
      setStatus("Saving summary...");
      setStatus("Completed.");
      void summary;
      navigate(`/documents/${document.id}?mode=${mode}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h1>Dashboard</h1>
      <p className="muted">Upload a PDF or image, choose a summary length, then generate.</p>
      <form className="stack" onSubmit={onSubmit}>
        <label className="upload-box">
          Upload PDF / Image
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
            disabled={busy}
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <span className="muted small">
            {file ? file.name : "PDF, PNG, JPG, or JPEG. Max 10 MB."}
          </span>
        </label>
        {statusHint ? <p className="muted small">{statusHint}</p> : null}

        <fieldset disabled={busy}>
          <legend>Summary length</legend>
          <div className="mode-row">
            {MODES.map((item) => (
              <label key={item} className={mode === item ? "chip selected" : "chip"}>
                <input
                  type="radio"
                  name="mode"
                  value={item}
                  checked={mode === item}
                  onChange={() => setMode(item)}
                />
                {item}
              </label>
            ))}
          </div>
        </fieldset>

        <button type="submit" disabled={busy}>
          {busy ? status || "Working..." : "Generate Summary"}
        </button>
      </form>
      {busy ? <p className="info">{status}</p> : null}
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
