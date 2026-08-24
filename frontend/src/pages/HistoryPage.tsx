import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError, deleteDocument, listDocuments, type DocumentRecord } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { ConfirmDeleteModal } from "../components/ConfirmDeleteModal";

function formatDate(value: string) {
  if (!value) return "n/a";
  const date = new Date(value);
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function HistoryPage() {
  const { session } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const token = session?.access_token || "";

  const [rows, setRows] = useState<DocumentRecord[]>([]);
  const [error, setError] = useState("");
  const [toast, setToast] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const [docToDelete, setDocToDelete] = useState<DocumentRecord | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  async function load() {
    if (!token) return;
    setError("");
    setLoading(true);
    try {
      const data = await listDocuments(token);
      setRows(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [token]);

  useEffect(() => {
    const state = location.state as { deletedMessage?: string } | null;
    if (state?.deletedMessage) {
      setToast(state.deletedMessage);
      // Clear location state so toast doesn't reappear on refresh
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location, navigate]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4000);
    return () => clearTimeout(timer);
  }, [toast]);

  function handleDeleteClick(doc: DocumentRecord) {
    setDocToDelete(doc);
    setError("");
  }

  async function handleConfirmDelete() {
    if (!docToDelete || !token) return;
    setIsDeleting(true);
    setError("");
    try {
      await deleteDocument(token, docToDelete.id);
      const deletedName = docToDelete.original_filename;
      setRows((current) => current.filter((row) => row.id !== docToDelete.id));
      setToast(`Deleted "${deletedName}" successfully.`);
      setDocToDelete(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete document.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <section className="card history-card">
      <div className="history-header">
        <div>
          <h1>History</h1>
          <p className="muted">Your uploaded documents and generated summaries.</p>
        </div>
      </div>

      {toast && (
        <div className="toast-banner success" role="status">
          <span>{toast}</span>
          <button
            type="button"
            className="toast-close-btn"
            onClick={() => setToast("")}
            aria-label="Close notification"
          >
            ×
          </button>
        </div>
      )}

      {error && <div className="toast-banner error">{error}</div>}

      {loading && (
        <div className="loading-state">
          <div className="spinner" aria-hidden="true" />
          <p>Loading history...</p>
        </div>
      )}

      {!loading && rows.length === 0 && (
        <div className="empty-history-state">
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#a8a29e"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <p>No documents yet.</p>
          <Link to="/" className="primary-link-btn">
            Upload your first document
          </Link>
        </div>
      )}

      {!loading && rows.length > 0 && (
        <ul className="history-list">
          {rows.map((row) => {
            const modes = (row.summaries || []).map((item) => item.mode);
            return (
              <li key={row.id} className="history-item">
                <div className="history-item-info">
                  <div className="history-item-title-row">
                    <strong className="history-filename">{row.original_filename}</strong>
                  </div>
                  <div className="history-meta-row">
                    <span className="meta-badge">{row.status}</span>
                    <span className="muted small">Uploaded: {formatDate(row.created_at)}</span>
                    {modes.length > 0 ? (
                      <span className="summary-tags">
                        Summaries:{" "}
                        {modes.map((m) => (
                          <span key={m} className="summary-mode-tag">
                            {m}
                          </span>
                        ))}
                      </span>
                    ) : (
                      <span className="muted small">No summaries yet</span>
                    )}
                  </div>
                </div>

                <div className="row-actions">
                  <Link to={`/documents/${row.id}`} className="open-btn">
                    Open
                  </Link>
                  <button
                    type="button"
                    className="danger-btn-outline"
                    onClick={() => handleDeleteClick(row)}
                    title="Delete document"
                  >
                    <svg
                      width="15"
                      height="15"
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
              </li>
            );
          })}
        </ul>
      )}

      {/* CONFIRM DELETE MODAL */}
      <ConfirmDeleteModal
        isOpen={!!docToDelete}
        filename={docToDelete?.original_filename || ""}
        isDeleting={isDeleting}
        onCancel={() => {
          if (!isDeleting) setDocToDelete(null);
        }}
        onConfirm={() => void handleConfirmDelete()}
      />
    </section>
  );
}
