import { useEffect, useState } from "react";
import { ApiError, getDocumentFileBlob } from "../services/api";

interface PdfViewerProps {
  token: string;
  documentId: string;
  filename: string;
  contentType: string;
}

export function PdfViewer({ token, documentId, filename, contentType }: PdfViewerProps) {
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    async function loadFile() {
      setLoading(true);
      setError("");
      try {
        const blob = await getDocumentFileBlob(token, documentId);
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setFileUrl(objectUrl);
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiError && err.status === 404) {
          setError("Original uploaded file is not available on the server.");
        } else {
          setError(
            err instanceof ApiError
              ? err.message
              : "Could not load the original document preview.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadFile();

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [token, documentId]);

  const isImage = contentType.startsWith("image/");

  return (
    <div className="pdf-viewer-wrapper">
      <div className="pdf-viewer-toolbar">
        <div className="pdf-viewer-title">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          <span>Original Document ({isImage ? "Image" : "PDF"})</span>
        </div>
        {fileUrl && (
          <div className="pdf-viewer-actions">
            <a
              href={fileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="pdf-action-link"
              title="Open in a new tab"
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
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
              <span>Open in new tab</span>
            </a>
          </div>
        )}
      </div>

      <div className="pdf-viewer-body">
        {loading && (
          <div className="pdf-viewer-state">
            <div className="spinner" aria-hidden="true" />
            <p>Loading original document...</p>
          </div>
        )}

        {!loading && error && (
          <div className="pdf-viewer-state error-state">
            <svg
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#b91c1c"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <p className="error">{error}</p>
            <p className="muted small">
              The original file binary is not stored for this document.
            </p>
          </div>
        )}

        {!loading && !error && fileUrl && (
          <>
            {isImage ? (
              <div className="image-viewer-scroll">
                <img
                  src={fileUrl}
                  alt={filename}
                  className="original-image-preview"
                />
              </div>
            ) : (
              <iframe
                src={`${fileUrl}#toolbar=1&navpanes=1&scrollbar=1`}
                className="pdf-iframe"
                title={`Original PDF: ${filename}`}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
