import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  ApiError,
  createSummary,
  deleteDocument,
  downloadSummaryPdf,
  getDocument,
  type DocumentRecord,
  type Summary,
} from "../services/api";
import { useAuth } from "../context/AuthContext";
import { PdfViewer } from "../components/PdfViewer";
import { ConfirmDeleteModal } from "../components/ConfirmDeleteModal";

function formatUploadDate(isoString: string): string {
  if (!isoString) return "n/a";
  const date = new Date(isoString);
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function capitalize(text: string): string {
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function DocumentPage() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { session } = useAuth();
  const token = session?.access_token || "";

  const [doc, setDoc] = useState<DocumentRecord | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const preferred = (params.get("mode") as Summary["mode"] | null) || "medium";
  const [mode, setMode] = useState<Summary["mode"]>(preferred);

  async function load() {
    if (!id || !token) return;
    setError("");
    try {
      const data = await getDocument(token, id);
      setDoc(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load document.");
    }
  }

  useEffect(() => {
    void load();
  }, [id, token]);

  const activeSummary = useMemo(() => {
    return doc?.summaries?.find((item) => item.mode === mode) || null;
  }, [doc, mode]);

  async function onGenerate() {
    if (!id || !token) return;
    setBusy(true);
    setError("");
    try {
      setStatus("Generating summary...");
      await createSummary(token, id, mode);
      setStatus("Saving summary...");
      await load();
      setStatus("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Summarization failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onDownload() {
    if (!activeSummary || !doc || !token) return;
    setError("");
    try {
      await downloadSummaryPdf(
        token,
        activeSummary.id,
        `${doc.original_filename.replace(/\.[^.]+$/, "")}-${activeSummary.mode}.pdf`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "PDF download failed.");
    }
  }

  async function handleDeleteConfirm() {
    if (!id || !token) return;
    setIsDeleting(true);
    try {
      await deleteDocument(token, id);
      navigate("/history", {
        replace: true,
        state: { deletedMessage: `Deleted "${doc?.original_filename || "document"}" successfully.` },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete document.");
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  }

  if (error && !doc) {
    return (
      <section className="card">
        <p className="error">{error}</p>
        <button
          type="button"
          className="secondary"
          style={{ marginTop: "1rem" }}
          onClick={() => navigate("/history")}
        >
          Back to History
        </button>
      </section>
    );
  }

  if (!doc) {
    return (
      <section className="card">
        <p>Loading document details...</p>
      </section>
    );
  }

  return (
    <div className="document-details-stack">
      {/* 1. DOCUMENT HEADER */}
      <section className="card document-header-card">
        <div className="document-header-top">
          <div>
            <h1 className="document-title">{doc.original_filename}</h1>
            <p className="document-upload-date">
              Uploaded: {formatUploadDate(doc.created_at)}
            </p>
          </div>
          <div className="document-header-actions">
            <button
              type="button"
              className="danger-btn-outline"
              onClick={() => setShowDeleteModal(true)}
              title="Delete this document"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M3 6h18" />
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              </svg>
              <span>Delete</span>
            </button>
          </div>
        </div>
      </section>

      {/* 2. ORIGINAL PDF VIEWER */}
      <section className="card pdf-section-card">
        <PdfViewer
          token={token}
          documentId={doc.id}
          filename={doc.original_filename}
          contentType={doc.content_type || "application/pdf"}
        />
      </section>

      {/* 3. GENERATED SUMMARY SECTION */}
      <section className="card summary-section-card">
        <div className="summary-section-header">
          <h2>
            {activeSummary
              ? `Generated Summary [${capitalize(activeSummary.mode)}]`
              : "Generated Summary"}
          </h2>
        </div>

        <div className="summary-controls-row">
          <div className="mode-selection-group">
            <span className="mode-label">Summary length:</span>
            <div className="mode-row">
              {(["short", "medium", "long"] as const).map((item) => (
                <button
                  key={item}
                  type="button"
                  className={mode === item ? "chip selected" : "chip"}
                  onClick={() => setMode(item)}
                  disabled={busy}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            className="primary-btn"
            onClick={() => void onGenerate()}
            disabled={busy}
          >
            {busy ? status || "Generating..." : activeSummary ? "Regenerate Summary" : "Generate Summary"}
          </button>
        </div>

        {busy && <p className="info status-alert">{status || "Processing with Gemini..."}</p>}
        {error && <p className="error status-alert">{error}</p>}

        {activeSummary ? (
          <div className="summary-content-box">
            <p className="summary-body">{activeSummary.summary_text}</p>
            {activeSummary.key_points && activeSummary.key_points.length > 0 && (
              <div className="key-points-block">
                <h3>Key Points</h3>
                <ul className="key-points-list">
                  {activeSummary.key_points.map((point, index) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="summary-download-row">
              <button
                type="button"
                className="secondary"
                onClick={() => void onDownload()}
                title="Download Summary as PDF"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                  style={{ marginRight: "0.4rem", verticalAlign: "middle" }}
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Download Summary as PDF
              </button>
            </div>
          </div>
        ) : (
          <div className="empty-summary-box">
            <p className="muted">No summary generated yet.</p>
            <p className="muted small">
              Select a summary length and click <strong>Generate Summary</strong> above.
            </p>
          </div>
        )}
      </section>

      {/* CONFIRM DELETE MODAL */}
      <ConfirmDeleteModal
        isOpen={showDeleteModal}
        filename={doc.original_filename}
        isDeleting={isDeleting}
        onCancel={() => {
          if (!isDeleting) setShowDeleteModal(false);
        }}
        onConfirm={() => void handleDeleteConfirm()}
      />
    </div>
  );
}
