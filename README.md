# Document Summary Assistant

A full-stack, web-based document summarization application. Users can upload PDFs or images, extract text natively with PyMuPDF or via Tesseract OCR for scans/images, generate structured AI summaries (short, medium, long) with key points using Google Gemini, manage document history with isolated user accounts, and export formatted summary reports as PDFs.

The application is deployed in production with the **FastAPI backend on Render** and a **React/Vite frontend**, utilizing **Supabase** for PostgreSQL database, storage, and authentication with custom **Brevo SMTP** for passwordless Email OTP delivery.

---

## Features

- **Passwordless Email OTP Authentication**: Secure sign-in via Supabase Auth with custom SMTP email delivery powered by Brevo.
- **Multi-Format Upload Support**: Accepts PDF, PNG, JPG, and JPEG with file size, extension, MIME type, and binary magic-byte verification.
- **Native PDF & OCR Extraction**: Fast text extraction via PyMuPDF with automated fallback to Tesseract OCR for scanned PDFs and image files.
- **Configurable AI Summarization**: Google Gemini (`gemini-3.6-flash` by default) generates short, medium, or long summaries with structured key points.
- **Map-Reduce Text Chunking**: Automatically chunks and summarizes large documents in passes to respect token limits.
- **User History & Data Isolation**: PostgreSQL database with Row-Level Security (RLS) ensures users can only access their own documents and summaries.
- **Original Document & Storage Management**: Secure document storage in private Supabase Storage buckets with user-scoped access policies.
- **PDF Summary Export**: Generates clean, downloadable PDF summary reports via ReportLab.
- **In-App PDF Viewer & Modal Controls**: Preview uploaded PDFs directly in the browser and manage documents with confirmation dialogs.

---

## Production Architecture

```
                    ┌───────────────────────────────┐
                    │     React / Vite UI (SPA)     │
                    │   (Render Production Host)    │
                    └───────────────┬───────────────┘
                                    │
                              HTTPS / Bearer JWT
                                    │
                    ┌───────────────▼───────────────┐
                    │     FastAPI Backend Web       │
                    │       (Render Service)        │
                    └───────┬───────────────┬───────┘
                            │               │
             ┌──────────────┘               └──────────────┐
             ▼                                             ▼
     ┌───────────────┐                             ┌───────────────┐
     │ Google Gemini │                             │   Supabase    │
     │  AI Summary   │                             │ Auth + DB/RLS │
     │  (GenAI SDK)  │                             │   + Storage   │
     └───────────────┘                             └───────┬───────┘
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │    Brevo     │
                                                    │  Custom SMTP │
                                                    │  (Email OTP) │
                                                    └──────────────┘
```

### Data & Processing Lifecycle
1. **Upload & Validation**: Uploaded binaries are validated on the backend (magic bytes, size, MIME type) and written to a secure temporary file.
2. **Text Extraction**: PyMuPDF extracts digital text; if pages are scanned or image-based, Tesseract OCR performs optical character recognition.
3. **Storage & Database**: Extracted text and metadata are saved to Supabase PostgreSQL, and the binary file is saved to the private Supabase Storage bucket under the user's ID.
4. **Temporary File Cleanup**: Temporary local server files are deleted immediately after processing in a `finally` block.
5. **AI Summarization**: Untrusted text is delimited and passed to Google Gemini with JSON schema enforcement.
6. **Summary Export**: ReportLab builds styled PDF reports for download on demand.

---

## Tech Stack

| Layer | Component | Description |
| --- | --- | --- |
| **Frontend** | React 19, TypeScript, Vite | Single-page application with responsive UI, CSS styling, and React Router v6 |
| **Backend** | Python 3.12, FastAPI, Uvicorn | RESTful API with Pydantic validation, JWT authentication, and CORS middleware |
| **Hosting** | Render | Production cloud hosting for backend web service (Docker runtime) and frontend |
| **Authentication** | Supabase Auth | Passwordless Email OTP flow generating asymmetric JWT tokens |
| **Email / SMTP** | Brevo (formerly Sendinblue) | Custom SMTP delivery provider configured in Supabase Auth |
| **Database** | Supabase PostgreSQL | Managed PostgreSQL database with Row-Level Security (RLS) policies |
| **File Storage** | Supabase Storage | Private storage bucket (`documents`) with folder-based RLS |
| **AI / LLM** | Google Gemini API (`google-genai`) | Default `gemini-3.6-flash` (configurable) with map-reduce chunking |
| **Document Processing** | PyMuPDF (`fitz`) | High-speed native digital PDF text extraction |
| **OCR Engine** | Tesseract OCR (`pytesseract`, `Pillow`) | Optical character recognition for scanned PDFs and image formats |
| **PDF Generation** | ReportLab | Server-side generation of summary report PDFs |

---

## Authentication Flow

The application implements a passwordless **Email OTP (One-Time Password)** authentication flow:

```
User enters email in React UI
        ↓
Frontend calls supabase.auth.signInWithOtp({ email, options: { shouldCreateUser: true } })
        ↓
Supabase Auth generates 6-digit OTP token
        ↓
Supabase triggers Custom SMTP through Brevo
        ↓
Brevo delivers OTP email containing {{ .Token }} to user inbox
        ↓
User enters OTP code in application
        ↓
Frontend calls supabase.auth.verifyOtp({ email, token, type: 'email' })
        ↓
Supabase issues session with asymmetric JWT (access token)
        ↓
Frontend attaches Bearer JWT to FastAPI request headers
        ↓
FastAPI validates JWT via Supabase JWKS (ES256 / RS256 algorithms)
        ↓
FastAPI derives authenticated user ID from token 'sub' claim
        ↓
User-isolated database (PostgREST) and document operations executed
```

### Key Implementation Details
- **Frontend Methods**: Uses `supabase.auth.signInWithOtp()` to dispatch the code and `supabase.auth.verifyOtp()` to complete sign-in.
- **Backend Verification**: FastAPI validates JWTs using `PyJWKClient` pointing to Supabase's JWKS endpoint (`/auth/v1/.well-known/jwks.json`), validating issuer, audience (`authenticated`), and signature algorithm (`ES256`/`RS256`).
- **SMTP Security**: Brevo SMTP credentials and API keys are stored securely inside Supabase project settings—never exposed to the frontend or checked into the Git repository.

---

## Project Structure

```
├── .env.example              # Root environment template
├── Aptfile                   # Linux packages for buildpack deployments (tesseract-ocr)
├── docker-compose.yml        # Multi-container local orchestration (backend + frontend)
├── supabase/
│   └── schema.sql            # Database tables, RLS policies, triggers, storage bucket setup
├── docs/
│   └── ASSIGNMENT.md         # Assessment and functional write-up
├── backend/
│   ├── Dockerfile            # Python 3.12-slim container with Tesseract OCR pre-installed
│   ├── requirements.txt      # Python dependencies
│   ├── pytest.ini            # Pytest test suite configuration
│   ├── app/
│   │   ├── main.py           # FastAPI entry point, CORS, routers, exception handlers
│   │   ├── core/
│   │   │   ├── config.py     # Pydantic settings management (.env loader)
│   │   │   ├── auth.py       # Supabase JWKS JWT validation dependency
│   │   │   └── db.py         # PostgREST client passing user Bearer tokens for RLS
│   │   ├── api/
│   │   │   ├── health.py     # GET /api/health endpoint
│   │   │   ├── documents.py  # Document upload, listing, detail, file stream, delete
│   │   │   └── summaries.py  # Summary generation and ReportLab PDF export endpoints
│   │   ├── services/
│   │   │   ├── validate.py   # Upload validation (magic bytes, size, MIME)
│   │   │   ├── extract.py    # PyMuPDF digital text extraction
│   │   │   ├── ocr.py        # Tesseract OCR image and PDF processing
│   │   │   ├── document.py   # Extraction pipeline orchestration
│   │   │   ├── summarize.py  # Gemini API summarizer with map-reduce chunking
│   │   │   ├── storage.py    # Supabase Storage upload, download, and delete
│   │   │   └── pdf_export.py # ReportLab PDF summary generation
│   │   └── utils/
│   │       └── text.py       # Text normalization and chunking helpers
│   └── tests/                # Automated pytest suite (auth, validation, storage, PDF)
└── frontend/
    ├── package.json          # Node dependencies and build scripts
    ├── vite.config.ts        # Vite configuration
    ├── index.html            # HTML template
    └── src/
        ├── main.tsx          # React application root
        ├── App.tsx           # Router and application layout
        ├── index.css         # UI design system and responsive styles
        ├── context/
        │   └── AuthContext.tsx # Supabase Auth state, OTP sign-in/verification
        ├── services/
        │   ├── supabase.ts   # Supabase client initialization
        │   └── api.ts        # Authenticated backend API client
        ├── pages/
        │   ├── LoginPage.tsx # Email entry & OTP verification forms
        │   ├── DashboardPage.tsx # File upload and summary mode selection
        │   ├── DocumentPage.tsx  # Document view, summary regeneration, PDF download
        │   └── HistoryPage.tsx   # Document history listing with delete controls
        └── components/
            ├── Layout.tsx            # Navigation header, user email, logout
            ├── PdfViewer.tsx         # In-browser PDF renderer
            ├── ProtectedRoute.tsx    # Auth guard redirecting to /login
            └── ConfirmDeleteModal.tsx # Delete confirmation dialog
```

---

## Environment Variables

### Backend Variables (Render Environment / `backend/.env`)

These credentials contain private secrets and must **never** be exposed to the client or committed to version control.

| Variable | Required | Description | Example |
| --- | --- | --- | --- |
| `SUPABASE_URL` | Yes | Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | Yes | Supabase anonymous public API key | `eyJhbGciOi...` |
| `SUPABASE_JWT_SECRET` | Optional | Supabase JWT secret | `your-jwt-secret` |
| `SUPABASE_STORAGE_BUCKET` | No | Storage bucket name (default: `documents`) | `documents` |
| `GEMINI_API_KEY` | Yes | Google AI Studio Gemini API Key | `AIzaSy...` |
| `GEMINI_MODEL` | No | Gemini model identifier (default: `gemini-3.6-flash`) | `gemini-3.6-flash` |
| `MAX_UPLOAD_BYTES` | No | Maximum file size in bytes (default: `10485760` / 10MB) | `10485760` |
| `MAX_PDF_PAGES` | No | Max pages for PDF OCR extraction (default: `20`) | `20` |
| `MAX_EXTRACTED_CHARS` | No | Character limit for extracted text (default: `200000`) | `200000` |
| `CORS_ORIGINS` | Yes | Comma-separated list of allowed frontend origins | `http://localhost:5173,https://your-frontend.onrender.com` |

### Frontend Variables (Render Static Site / `frontend/.env`)

These variables are bundled into the client build and must contain **only public** identifiers.

| Variable | Required | Description | Example |
| --- | --- | --- | --- |
| `VITE_SUPABASE_URL` | Yes | Supabase project URL | `https://your-project.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Yes | Supabase anon public API key | `eyJhbGciOi...` |
| `VITE_API_BASE_URL` | Yes | URL pointing to the FastAPI backend | `https://your-backend.onrender.com` or `http://localhost:8000` |

---

## Cloud Services Setup

### 1. Supabase (Database, Auth, Storage)
1. Create a project at [supabase.com](https://supabase.com).
2. **Database & Storage Setup**: Go to the **SQL Editor** and run the contents of [`supabase/schema.sql`](supabase/schema.sql). This configures:
   - `public.documents` and `public.summaries` tables with RLS.
   - Private `documents` storage bucket with user-scoped isolation.
3. **API Keys**: From **Project Settings → API**, copy the `Project URL` and `anon public` key.

### 2. Brevo Custom SMTP (Email OTP)
1. Create an account on [brevo.com](https://www.brevo.com) and navigate to **Transactional → Settings → Configuration**.
2. Note your SMTP host (`smtp-relay.brevo.com`), port (`587`), SMTP login, and generated SMTP Master Password / API Key.
3. In the **Supabase Dashboard**, navigate to **Project Settings → Authentication → SMTP Settings**:
   - Enable **Custom SMTP**.
   - Set **Sender Email** to your verified sender email address.
   - Set **Sender Name** to `Document Summary Assistant`.
   - Set **Host** to `smtp-relay.brevo.com` and **Port** to `587`.
   - Enter your Brevo SMTP username and password.
4. In **Authentication → Email Templates → Magic Link / Confirmation**:
   - Update the subject and body to use the token template variable:
     ```html
     <h2>Your Login Code</h2>
     <p>Use the following one-time code to log in to Document Summary Assistant:</p>
     <p style="font-size: 24px; font-weight: bold; letter-spacing: 4px;">{{ .Token }}</p>
     <p>This code will expire shortly. If you did not request this code, please ignore this email.</p>
     ```

### 3. Google Gemini (Google AI Studio)
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com).
2. Set `GEMINI_API_KEY` and optionally `GEMINI_MODEL=gemini-3.6-flash`.

---

## Deployment on Render

The production application runs on Render:

### Backend Deployment (Web Service)
1. Create a **New Web Service** on Render and link your repository.
2. Select **Docker** as the runtime (Render will build using `backend/Dockerfile`).
3. Set the **Root Directory** to `backend` (or point Dockerfile Path to `backend/Dockerfile`).
4. Configure the environment variables under **Environment**:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL=gemini-3.6-flash`
   - `CORS_ORIGINS=https://your-frontend.onrender.com,http://localhost:5173`
5. The Dockerfile automatically installs `tesseract-ocr`, `tesseract-ocr-eng`, Python dependencies, and starts Uvicorn bound to `${PORT:-8000}`.

### Frontend Deployment (Static Site)
1. Create a **New Static Site** on Render and link the repository.
2. Set the **Root Directory** to `frontend`.
3. Build Command: `npm install && npm run build`
4. Publish Directory: `dist`
5. Configure Environment Variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_BASE_URL` (the live Render backend service URL)

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- Tesseract OCR (`eng` language pack) installed locally on system PATH

### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env   # Configure with your test Supabase and Gemini keys
uvicorn app.main:app --reload --port 8000 --timeout-keep-alive 300
```
Verify the backend is running at `http://localhost:8000/api/health`.

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env     # Ensure VITE_API_BASE_URL=http://localhost:8000
npm run dev
```
Open `http://localhost:5173` in your browser.

### 3. Docker Compose (Alternative Local Setup)
You can run the complete stack locally using Docker Compose:
```bash
docker-compose up --build
```
This builds the backend container with Tesseract pre-installed and launches the Vite development server.

---

## API Reference

All protected endpoints require an `Authorization: Bearer <JWT>` header containing a valid Supabase access token.

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/health` | No | Health check endpoint returning `{ "status": "ok" }` |
| `POST` | `/api/documents` | JWT | Uploads, validates, extracts/OCRs text, saves file to storage & returns metadata |
| `GET` | `/api/documents` | JWT | Lists all documents owned by the authenticated user |
| `GET` | `/api/documents/{id}` | JWT | Retrieves metadata, extracted text, and summaries for a document |
| `GET` | `/api/documents/{id}/file` | JWT | Streams the original uploaded PDF/image file from storage |
| `DELETE` | `/api/documents/{id}` | JWT | Deletes document record, associated summaries, and storage object |
| `POST` | `/api/documents/{id}/summaries` | JWT | Generates summary (`short`, `medium`, or `long`) via Google Gemini |
| `GET` | `/api/summaries/{id}/pdf` | JWT | Downloads a formatted ReportLab PDF summary report |

---

## Security Considerations

- **Asymmetric JWT Verification**: Validated on every protected endpoint via Supabase JWKS public keys (`ES256`/`RS256`), verifying signature, expiry, and audience.
- **Strict User Isolation**: Client-supplied user IDs are never trusted. All database and storage operations derive the user identity strictly from the validated token `sub` claim.
- **Row-Level Security (RLS)**: PostgreSQL enforces policies where `user_id = auth.uid()` for all tables and private storage buckets.
- **Magic-Byte Upload Validation**: Binary headers are checked (`%PDF`, `\x89PNG`, `\xff\xd8\xff`) to prevent spoofed file extensions.
- **Temporary File Lifecycle**: Temporary files written during extraction are strictly deleted in Python `finally` blocks.
- **Prompt Injection Defense**: Untrusted extracted document text is delimited in explicit boundary tags (`DOCUMENT_CONTENT_START`/`DOCUMENT_CONTENT_END`) and guided by strict system prompts with JSON schema response enforcement.
- **Zero Exposed Secrets**: No API keys, JWT secrets, or Brevo SMTP credentials are baked into frontend bundles or tracked in Git.

---

## Testing

### Automated Test Suite
Run the backend test suite:
```bash
cd backend
pytest
```
The suite verifies JWT authentication, upload validation rules, text normalization and chunking, ReportLab PDF generation, and storage operations.

### Manual Verification Checklist
- [ ] **OTP Login**: Enter an email, receive the 6-digit OTP delivered via Brevo SMTP.
- [ ] **OTP Verification**: Enter the code, verify successful JWT issuance and redirection to the dashboard.
- [ ] **Native PDF Upload**: Upload a standard PDF and verify fast PyMuPDF extraction.
- [ ] **Image / Scanned PDF OCR**: Upload an image or scanned document and verify Tesseract OCR processing.
- [ ] **Validation Rejection**: Test upload of invalid formats (e.g. `.txt`, `.exe`) and oversized files (> 10 MB) to confirm clear error responses.
- [ ] **Summary Modes**: Generate `short`, `medium`, and `long` summaries with key points.
- [ ] **PDF Summary Export**: Click "Download Summary as PDF" and verify the downloaded ReportLab PDF layout.
- [ ] **In-App PDF Viewing**: View the original uploaded PDF in the embedded viewer.
- [ ] **User History Isolation**: Log in as User A, create documents, log out, log in as User B, and verify User A's documents are completely invisible.
- [ ] **Document Deletion**: Delete a document and confirm its removal from history and storage.
- [ ] **Production Connectivity**: Confirm frontend on Render communicates over HTTPS with the Render backend API.

---

## Limitations & Operational Considerations

- **Render Free-Tier Cold Starts**: Web services on free hosting tiers may sleep when inactive, causing initial requests to take 30–50 seconds while spinning up.
- **Gemini Free-Tier Rate Limits**: Google AI Studio free tier enforces requests-per-minute (RPM) and requests-per-day (RPD) limits. The backend includes exponential backoff retries to mitigate transient HTTP 429 errors.
- **OCR Constraints**: OCR accuracy depends heavily on input image resolution, orientation, and scan quality. English (`eng`) is the default configured language pack.
- **Processing Limits**: Default configuration caps uploads at 10 MB and limits OCR page scanning to 20 pages to protect server memory.
- **Email Delivery Limits**: Free SMTP providers enforce daily sending quotas on OTP delivery.
