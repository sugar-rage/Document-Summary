const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  token: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("Network failure. Check that the API is running.", 0);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload.detail === "string" ? payload.detail : "Request failed.";
    throw new ApiError(detail, response.status);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/pdf") || contentType.startsWith("image/")) {
    return (await response.blob()) as T;
  }

  const payload = await response.json().catch(() => ({}));
  return payload as T;
}

export type Summary = {
  id: string;
  document_id: string;
  mode: "short" | "medium" | "long";
  summary_text: string;
  key_points: string[];
  model: string;
  created_at: string;
};

export type DocumentRecord = {
  id: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  storage_path?: string | null;
  extraction_method: string | null;
  extracted_text?: string;
  page_count: number | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  summaries?: Summary[];
};

export function uploadDocument(token: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<DocumentRecord>("/api/documents", token, { method: "POST", body });
}

export function listDocuments(token: string) {
  return request<DocumentRecord[]>("/api/documents", token);
}

export function getDocument(token: string, id: string) {
  return request<DocumentRecord>(`/api/documents/${id}`, token);
}

export function getDocumentFileBlob(token: string, id: string) {
  return request<Blob>(`/api/documents/${id}/file`, token);
}

export function deleteDocument(token: string, id: string) {
  return request<{ ok: boolean }>(`/api/documents/${id}`, token, { method: "DELETE" });
}

export function createSummary(token: string, documentId: string, mode: Summary["mode"]) {
  return request<Summary>(`/api/documents/${documentId}/summaries`, token, {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
}

export async function downloadSummaryPdf(token: string, summaryId: string, filename: string) {
  const blob = await request<Blob>(`/api/summaries/${summaryId}/pdf`, token);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

